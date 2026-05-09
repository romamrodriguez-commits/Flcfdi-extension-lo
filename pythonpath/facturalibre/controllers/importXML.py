#!
# -*- coding: utf-8 -*-

import traceback
try:
    from facturalibre.modulos.pyXml import CFDIXML
    import facturalibre.ui.seleccionar as seleccion
except:
    print (traceback.format_exc())

KEY_RETURN = 1280
PRE = {
        '2.0': '{http://www.sat.gob.mx/cfd/2}',
        '2.2': '{http://www.sat.gob.mx/cfd/2}',
        '3.0': '{http://www.sat.gob.mx/cfd/3}',
        '3.2': '{http://www.sat.gob.mx/cfd/3}'
    }

class EventosImportXML(object):
    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.unogui = caller.unogui
        self.globales = caller.globales
        self.db = caller.db
        self.dialog = caller.dialog
        self.PRE = ''
        self.value = ''
        self.codigo = ''
        self.version = ''
        self.xml = None
        self.dm = self.dialog.getModel()
        self.notas = ''
        self.id_prov = 0
        self.cfdiXML = CFDIXML()

    def cmdSalir(self):
        self.dialog.endExecute()
        return
        

    def cmdImportar(self):
        try:
            #Verificamos que ya exista una ruta hacia un archivo
            if not self.dm.txtArchivo.Text.strip():
                mensaje = 'Debe escribir la ruta hacia un archivo'
                self.unogui.createMsgBox({'Message': mensaje})
            else:
                #~ Nos aseguramos de que el archivo si sea un XML
                self.xml = self.cfdiXML.parse(self.dm.txtArchivo.Text.strip())
                if self.xml is None:
                    mensaje = u'Hubo un error al intentar abrir el archivo, asegurese ' \
                                u'de que es un documento válido'
                    self.unogui.createMsgBox({'Message': mensaje})
                else:
                    #~ Verificamos que el XML sea un CFD
                    if not 'Comprobante' in self.xml.tag:
                        mensaje = u'El archivo no es un documento CFD o CFDI'
                        self.unogui.createMsgBox({'Message': mensaje})
                    else:
                        self.alcuadro()
                        return
        except:
            print (traceback.format_exc())

    def cmdGuardar(self):
        try:
            fecha =  self.dialog.getControl('fecha').Text
            campos = ('id',)
            tablas = ('compras', )
            condicion = "fecha='%s' AND id_proveedor=%s" % (fecha, str(self.id_prov))
            data = self.db.select(tablas, campos, where=condicion)
            if not data:
                self.__guardar_datos()
                if self.dm.optEstatus1.State:
                    self.__saldos()
                self.dm.lblInfo.Label = u'Información guardada en la base de datos'
                self.__cambiarnombre()
                self.__limpiaformulario()
            else:
                self.dm.lblInfo.Label = u'Esta factura ya había sido guardada'
        except:
            print (traceback.format_exc())
        return

    def alcuadro(self):
        #~ Obtenemos la versión del XML
        self.version = self.xml.attrib['version']
        self.PRE = PRE[self.version]
        #~ Verificamos que el receptor corresponda con la empresa
        if not self.__receptor():
            mensaje = u'Este documento no fue emitido para esta empresa.'
            self.unogui.createMsgBox({'Message': mensaje})
            return

        #~ No aseguramos que el CFDI tenga conceptos
        self.__comprobante()
        self.__emisor()
        self.__impuestos()
        self.id_prov = self.__proveedor(self.dialog.getControl('emisorrfc').Text)
        if not self.__conceptos():
            mensaje = u'Este documento no tiene conceptos.'
            self.unogui.createMsgBox({'Message': mensaje})
            self.__limpiaformulario()
        else:
            archi = open(self.dm.txtArchivo.Text.strip(),'r')
            lineas = archi.readlines()
            archi.close()
            el_xml = ""
            for li in lineas:
                el_xml = el_xml + li
            self.dm.xml.Text = el_xml
            self.dm.lblInfo.Label = u'Datos del documento CFDI importados'

    def __comprobante(self):
        #~ Obtenemos la serie y el folio
        folio = ''
        if 'serie' in self.xml.attrib:
            folio = '%s-' % self.xml.attrib['serie']
        if 'folio' in self.xml.attrib:
            folio += self.xml.attrib['folio']
        self.dialog.getControl('txtFolio').Text = folio
        
        for v in list(self.xml.keys()):
            try:
                self.dialog.getControl(v).Text = self.xml.attrib[v]
            except:
                pass

        dias = ('domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado')
        meses = ('0', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
        fecha = ''
        fecha_l = self.xml.attrib['fecha'].split('T')
        dia = self.util.format_date(fecha_l[0], '%w')
        fecha_l[0] = fecha_l[0].split('-')
        fecha += '%s, %s de %s de %s' % (dias[int(dia)], fecha_l[0][2], meses[int(fecha_l[0][1])], fecha_l[0][0])
        self.dialog.getControl('txtFecha').Text = fecha
        return

    def __emisor(self):
        emisor = self.xml.find('%sEmisor' % self.PRE)
        if emisor is None:
            mensaje = u'El documento no cuenta con Emisor.\nNo es un CFDI válido.'
            self.unogui.createMsgBox({'Message': mensaje})
            return
        for v in list(emisor.keys()):
            try:
                self.dialog.getControl('emisor%s' % v).Text = emisor.attrib[v]
            except:
                pass

        domicilio = emisor.find('%sDomicilioFiscal' % self.PRE)
        if domicilio is not None:
            for v in list(domicilio.keys()):
                try:
                    self.dialog.getControl(v).Text = domicilio.attrib[v]
                except:
                    pass
        return

    def __receptor(self):
        if self.globales['DEBUG']:
            return True
        receptor = self.xml.find('%sReceptor' % self.PRE)
        if receptor is None:
            return False
        mirfc = self.db.select_field('emisor', 'rfc')
        if mirfc == receptor.attrib['rfc']:
            return True
        else:
            return False

    def __impuestos(self):
        impuestos = self.xml.find('%sImpuestos' % self.PRE)
        for v in list(impuestos.keys()):
            try:
                self.dialog.getControl(v).Text = impuestos.attrib[v]
            except:
                pass
        return

    def __donataria(self):
        complemento = self.xml.find('%sComplemento' % PRE)
        if complemento is None or not self.celdas['donatariaautorizacion']:
            return
        donataria = complemento.find('{http://www.sat.gob.mx/donat}Donatarias')
        if donataria is not None:
            self.__write_cell(self.celdas['donatariaautorizacion'], donataria.attrib['noAutorizacion'])
            self.__write_cell(self.celdas['donatariafecha'], donataria.attrib['fechaAutorizacion'])
            self.__write_cell(self.celdas['donatarialeyenda'], donataria.attrib['leyenda'])
        return

    def __personalizados(self, id_cfd):
        data = self.db.select(('cfdpersonalizados', 'campospersonalizados'), ('celda1', 'valor'), 'cfdpersonalizados.campo=campospersonalizados.nodo and id_cfd=%s' % id_cfd)
        if data:
            for row in data:
                self.__write_cell(row[0], row[1])
        return

    def __conceptos(self):
        #~ Revisamos que exista una sección de conceptos
        conceptos = self.xml.find('%sConceptos' % self.PRE)
        if conceptos is None:
            return False

        #~ Vaciamos los datos de los conceptos a el grid
        data = []
        for concepto in conceptos.getchildren():
            try:
                unidad = concepto.attrib['unidad']
            except:
                unidad = ''
            try:
                noIdentificacion = concepto.attrib['noIdentificacion']
            except:
                noIdentificacion = ''
            try:
                clave_interna, id_producto = self.__claveInterna(noIdentificacion)
                data.append((concepto.attrib['cantidad'],
                            unidad,
                            concepto.attrib['descripcion'],
                            concepto.attrib['valorUnitario'],
                            concepto.attrib['importe'],
                            noIdentificacion, clave_interna, id_producto))
            except:
                print (traceback.format_exc())
        self.unogui.gridAddRows(self.dm.gridConceptos, data)
        return True

    def __guardar_datos(self):
        compra = {}
        #~ Obtenemos el id del proveedor
        compra['id_proveedor'] = self.id_prov
        campos = ('serie', 'folio', 'fecha', 'formaDePago', 'subTotal',
                    'descuento', 'motivoDescuento', 'TipoCambio',
                    'Moneda', 'total', 'metodoDePago', 'NumCtaPago',
                    'LugarExpedicion', 'totalImpuestosRetenidos',
                    'totalImpuestosTrasladados', 'tipoDeComprobante',
                    'uuid', 'noCertificado')
        for campo in campos:
            compra[campo] = self.dialog.getControl(campo).Text
        compra['notas'] = self.notas
        compra['xml'] = self.dm.xml.Text
        compra['version'] = self.version
        if self.dm.optEstatus2.State:
            estatus = 'Pagada'
        else:
            estatus = 'Por pagar'
            
        compra['estatus'] = estatus
        id_compra = self.db.insertrow('compras', compra)
        try:
            #~ Vaciamos el contenido del grid a la base de datos
            grid = self.dm.gridConceptos
            grid_dm = grid.GridDataModel
            fil = grid_dm.RowCount
            concepto = {}
            for f in range(fil):
                #~ if f > 0:
                concepto['id_compra'] = id_compra
                concepto['cantidad'] = grid_dm.getCellData(0, f)
                concepto['unidad'] = grid_dm.getCellData(1, f)
                concepto['descripcion'] = grid_dm.getCellData(2, f)
                concepto['valorUnitario'] = grid_dm.getCellData(3, f)
                concepto['importe'] = grid_dm.getCellData(4, f)
                concepto['noIdentificacion'] = grid_dm.getCellData(5, f)
                concepto['id_producto'] = grid_dm.getCellData(7, f)
                self.db.insertrow('compradetalle', concepto)
                print ('id_Producto=%s' % grid_dm.getCellData(7, f))
                print (type(grid_dm.getCellData(7, f)))
                self.__claves(grid_dm.getCellData(5, f), grid_dm.getCellData(6, f), grid_dm.getCellData(7, f))
                self.__inventario(grid_dm.getCellData(7, f), grid_dm.getCellData(0, f), grid_dm.getCellData(1, f))
            return
        
        except:
            print (traceback.format_exc())

    def __proveedor(self, rfc):
        campos = ('id',)
        tablas = ('receptores', )
        condicion = "rfc='%s'" % rfc
        data = self.db.select(tablas, campos, where=condicion)
        if not data:
            datos = {}
            campos = ('calle', 'colonia', 'municipio', 'codigoPostal',
                        'estado', 'pais', 'noExterior', 'noInterior',)
            for campo in campos:
                datos[campo] = self.dialog.getControl(campo).Text
            datos['rfc'] = self.dialog.getControl('emisorrfc').Text
            datos['nombre'] = self.dialog.getControl('emisornombre').Text
            datos['escliente'] = 0
            datos['esproveedor'] = 1
            datos['activo'] = 1
            datos['fechaalta'] = str(self.util.now())
            datos['notas'] = ''
            id_reg = self.db.insertrow('receptores', datos)
        else:
            id_prov = data[0]
            id_reg = int(id_prov[0])
        return id_reg

    def __limpiaformulario(self):
        print ('Dentro de __limpiaformulario')
        campos = ('serie', 'folio', 'fecha', 'formaDePago', 'subTotal',
                    'descuento', 'motivoDescuento', 'TipoCambio',
                    'Moneda', 'total', 'metodoDePago', 'NumCtaPago',
                    'LugarExpedicion', 'calle', 'colonia',
                    'municipio', 'codigoPostal', 'txtFecha',
                    'estado', 'pais', 'noExterior', 'noInterior',
                    'emisorrfc', 'emisornombre', 'txtFolio',
                    'txtArchivo', 'localidad', 'tipoDeComprobante')
        for campo in campos:
            self.dialog.getControl(campo).Text = ''
        self.dialog.getControl('totalImpuestosRetenidos').Text = '0.00'
        self.dialog.getControl('totalImpuestosTrasladados').Text = '0.00'
        grid = self.dm.gridConceptos
        grid.GridDataModel.removeAllRows()
        self.id_prov = 0
        return

    def __claveInterna(self, noIdentificacion):
        if noIdentificacion.strip():
            condicion = "noIdentificacion='%s' AND id_proveedor=%s" % (noIdentificacion.strip(), self.id_prov)
            data = self.db.select(('claves',), ('clave','id_producto'), where=condicion)
            if data:
                return data[0][0], data[0][1]
            else:
                return '', 0
        return '', 0

    def __claves(self, noIdentificacion, clave, id_producto):
        if clave.strip() and noIdentificacion.strip():
            clave_interna, id_prod = self.__claveInterna(noIdentificacion)
            if not clave_interna:
                datos = {}
                datos['id_proveedor'] = self.id_prov
                datos['id_producto'] = id_producto
                datos['noIdentificacion'] = noIdentificacion
                datos['clave'] = clave
                self.db.insertrow('claves', datos)

    def gridConceptos_DobleClick(self, grid):
        try:
            grid_dm = grid.Model.GridDataModel
            col = grid.CurrentColumn
            fil = grid.CurrentRow
            clave = ''
            id_producto = ''
            row_id = grid_dm.getCellData(7, fil)
            clave = grid_dm.getCellData(1, fil)
            if col == 6:
                input_box = seleccion.Dlg(self, grid_dm.getCellData(col, fil))
                res = input_box.execute()
                if res:
                    condicion = "noIdentificacion='%s'" % self.codigo
                    data = self.db.select(('productos',), ('id',), where=condicion)
                    if data:
                        grid_dm.updateCellData(6, fil, self.codigo)
                        grid_dm.updateCellData(7, fil, data[0][0])
        except:
            print(traceback.format_exc())
        return

    def __id_prod(self, clave):
        if not clave.strip():
            condicion = "noIdentificacion='%s'" % clave
            data = self.db.select(('productos',), ('id',), where=condicion)
            if data:
                return data[0](0)
            else:
                return 0
        else:
            return 0

    def __inventario(self, id_producto, cantidad, unidad):
        if id_producto:
            condicion = "id='%s'" % id_producto
            actual = self.db.select(('productos',), ('existencia',), where=condicion)
            cuantos = actual[0][0]
            self.db.update('productos', {'existencia': '%s' % str(cuantos + float(cantidad))}, 'id=%s' % id_producto, True)
        return

    def __saldos(self):
        condicion = 'id=%s' % self.id_prov
        saldo = self.db.select(('receptores',), ('saldoProveedor',), where = condicion)
        nuevoSaldo = saldo[0][0] + float(self.dialog.getControl('total').Text.replace(",", ""))
        self.db.update('receptores', {'saldoProveedor':nuevoSaldo}, condicion)
        return

    def __cambiarnombre(self):
        origin = self.dm.txtArchivo.Text
        self.util.chext(origin)
        return
