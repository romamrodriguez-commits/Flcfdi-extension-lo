# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET
from facturalibre.modulos.pyXml import CFDXML
from facturalibre.modulos.pyPdf import CFDPDF
import facturalibre.ui.inputbox as inputbox
import facturalibre.ui.inputbox2 as inputbox2
import facturalibre.ui.campos as campos
import datetime
import re
import traceback


KEY_RETURN = 1280
KEY_TAB = 1282
CLIENTES_COUNT = 101
MOSTRAR_LIMITE = 2
ICON_PDF = 'pdf.png'
ICON_ODS = 'calc.png'
PRE = '{http://www.sat.gob.mx/cfd/3}'
PRE2 = '{http://www.sat.gob.mx/TimbreFiscalDigital}'


class EventosAdminCompras(object):

    def __init__(self, caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.globales = caller.globales
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.db = caller.db
        self.rfc = self.db.select_field('certificado', 'rfc')
        self.format_s = self.globales['FORMAT'] % self.db.select_field(
                                                'opciones', 'decimales')
        self.enviar_correo = caller.enviar_correo
        self.value = ''
        self.img_url = '%s/icons/' % self.globales['EXT_PATH']
        self.id_addenda = 0
        self.id_cfd = 0
        self.value = ''

    def msg_user(self, msg):
        self.dm.lblInfo.Label = msg

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def cmdFiltrar1(self):
        where = ''
        lst = self.dialog.getControl('lstMes')
        year = self.dialog.getControl('lstAno')
        pos1 = lst.SelectedItemPos
        pos2 = year.SelectedItemPos
        if pos1 > 0 and pos2 > 0:
            filtro = '%02d%s' % (pos1, year.SelectedItem)
            where = " AND strftime('%m%Y',fecha)='" + filtro + "'"
        elif pos1 == 0 and pos2 > 0:
            filtro = str(year.SelectedItem)
            where = " AND strftime('%Y',fecha)='" + filtro + "'"
        elif pos1 > 0 and pos2 == 0:
            filtro = '%02d' % pos1
            where = " AND strftime('%m',fecha)='" + filtro + "'"
        lst = self.dialog.getControl('lstEstatus')
        pos = lst.getSelectedItemPos()
        if pos > 0:
            where += " AND estatus='%s'" % lst.getSelectedItem()

        if self.dm.txtReceptor.Tag:
            where += " AND id_proveedor=%s" % self.dm.txtReceptor.Tag

        self.__filtrar(where)
        return

    def cmdFiltrar2(self):
        where = ''
        if self.dm.txtCfd.Text:
            try:
                folio = int(self.dm.txtCfd.Text)
                where = " AND folio=%s" % folio
            except:
                where = " AND serie||folio='%s'" % self.dm.txtCfd.Text
            self.__filtrar(where)
        else:
            self.dialog.getControl('txtCfd').setFocus()
            message = 'Introduce el folio a buscar'
            self.msg_user(message)
        return

    def cmdFiltrar3(self):
        where = ''
        desde = self.dm.txtFolio1.Value
        if desde is None:
            self.dialog.getControl('txtFolio1').setFocus()
            message = 'Captura el folio inicial'
            self.msg_user(message)
            return
        hasta = self.dm.txtFolio2.Value
        if hasta is None:
            self.dialog.getControl('txtFolio2').setFocus()
            message = 'Captura el folio final'
            self.msg_user(message)
            return
        if desde > hasta:
            desde = self.dm.txtFolio2.Value
            hasta = self.dm.txtFolio1.Value
        where = " AND folio BETWEEN %s AND %s" % (int(desde), int(hasta))
        self.__filtrar(where)
        return

    def cmdImprimir(self):
        avance =  self.dialog.getControl('pbCopia')
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = grid.Selection
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        if len(sel) > MOSTRAR_LIMITE:
            message = 'Vas a imprimir %s documentos.\n\n¿Estás seguro de continuar?' % len(sel)
            if not self.unogui.createQuestion('Factura Libre', message):
                return
        avance.setRange(0, len(sel))
        facturas = []
        for row in sel:
            facturas.append(grid_dm.getCellData(0, row))
        if self.dm.chkDetalle.State:
            self.dialog.getControl('gridTotales').setVisible(False)
        else:
            grid.Model.Height = 170
        try:
            pdf = CFDPDF(self)
            pdf.show = False
            pdf.printer = True
            pdf.generate_pdf(facturas, '', avance)
        except:
            print((traceback.format_exc()))
        finally:
            if self.dm.chkDetalle.State:
                self.dialog.getControl('gridTotales').setVisible(True)
            else:
                grid.Model.Height = 184
        return

    def cmdPdf(self):
        avance =  self.dialog.getControl('pbCopia')
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = grid.SelectedRows
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        destino = ''
        if len(sel) > MOSTRAR_LIMITE:
            message = 'Vas a generar %s documentos PDF.\n\n¿Estás seguro de ' \
                'continuar?' % len(sel)
            if not self.unogui.createQuestion('Factura Libre', message):
                return
        avance.setRange(0, len(sel))
        avance.setVisible(True)
        facturas = []
        for row in sel:
            facturas.append(grid_dm.getCellData(0, row))
            #~ print (grid_dm.getCellData(0, row))
        try:
            pdf = CFDPDF(self)
            #~ pdf.editar = editar
            if destino:
                pdf.show = False
            rutas = self.db.select(('rutasespejo',), ('ruta',))
            pdf.espejos = rutas
            pdf.is_compra = True
            if pdf.generate_pdf(facturas, destino, avance):
                if destino:
                    message = 'Pdfs generados correctamente en: %s' % destino
                    self.msg_user(message)
        except:
            print((traceback.format_exc()))
        finally:
            grid.Model.Height = 184
            avance.setVisible(False)
        return

    def cmdLimpiarSeleccion(self):
        grid = self.dialog.getControl('gridFacturas')
        grid.deselectAllRows()
        self.dm.suma.Value = 0
        return

    def cmdSeleccionarTodo(self):
        grid = self.dialog.getControl('gridFacturas')
        grid.selectAllRows()
        return

    def cmdPagada(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = grid.SelectedRows
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        message = '¿Estás seguro de marcar como pagadas las facturas seleccionadas?'
        if not self.unogui.createQuestion('Factura Libre', message):
            return
        for row in sel:
            id_cfd = grid_dm.getCellData(0, row)
            if grid_dm.getCellData(4, row) == 'Cancelada':
                message = 'Esta factura esta cancelda'
                self.msg_user(message)
                continue
            if grid_dm.getCellData(4, row) == 'Pagada':
                continue

            #~ Modificamos el saldo del proveedor cuando se marca como pagada
            self.__saldo(grid_dm.getCellData(10, row), grid_dm.getCellData(5, row))
            try:
                rows = self.db.update('compras', {'estatus': 'Pagada'}, "id=%s AND estatus='Por pagar'" % id_cfd)
            except:
                print(traceback.format_exc())
            if rows:
                grid_dm.updateCellData(4, row, 'Pagada')
        return

    def cmdCancelada(self):
        grid = self.dialog.getControl('gridFacturas')
        sel = grid.SelectedRows
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        if len(sel) > 1:
            message = 'Selecciona solo una factura para cancelar'
            self.msg_user(message)
            return
        grid_dm = grid.Model.GridDataModel
        if grid_dm.getCellData(4, sel[0]) == 'Cancelada':
            message = 'Esta factura ya esta cancelda'
            self.msg_user(message)
            return
        id_cfd = grid_dm.getCellData(0, sel[0])
        where = 'compras.id=%s' % id_cfd
        data = self.db.select(
            ('compras',),
            ('noAprobacion', 'noCertificado'),
            where)[0]
        message = 'Folio: %s\nEmisor: %s' % (
                        grid_dm.getCellData(1, sel[0]),
                        grid_dm.getCellData(9, sel[0]))
        message = '%s\n\n¿Estás seguro de marcar como CANCELADA la factura' \
                ' seleccionada?\n\nEsta accion no se puede deshacer' % message
        if not self.unogui.createQuestion('Factura Libre', message):
            return

        if grid_dm.getCellData(4, row) == 'Por pagar':
            #~ Modificamos el saldo del proveedor cuando se marca como Por pagar
            try:
                self.__saldo(grid_dm.getCellData(10, row), grid_dm.getCellData(5, row))
            except:
                print(traceback.format_exc())
        try:
            rows = self.db.update(
                'compras', {'estatus': 'Cancelada'}, 'id=%s' % id_cfd)
        except:
            print(traceback.format_exc())
        if rows:
            grid_dm.updateCellData(4, sel[0], 'Cancelada')
            message = 'Factura cancelada correctamente.'
            self.msg_user(message)
        rows = 0
        #~ Regresar inventario
        #~ rows = self.db.update('compras', {'estatus': 3}, 'id=%s AND estatus<>3' % id_cfd)
        #~ if rows:
            #~ grid_dm.updateCellData(4, sel[0], 'Cancelada')
            #~ fields = ('compradetalle.noIdentificacion', 'cantidad')
            #~ where = 'id_cfd=%s AND cfddetalle.noIdentificacion=' \
                    #~ 'productos.noIdentificacion AND inventario=1' % id_cfd
            #~ data = self.db.select(('cfddetalle', 'productos'), fields, where)
            #~ message = '.'
            #~ if data:
                #~ message += 'La factura cancelada tiene productos' \
                    #~ ' con control de inventario.\n\n¿Deseas reingresarlos' \
                    #~ ' al sistema?'
                #~ if self.unogui.createQuestion('Factura Libre', message):
                    #~ for r in data:
                        #~ self.db.update(
                            #~ 'productos',
                            #~ {'existencia': 'existencia+%s' % r[1]},
                            #~ 'noIdentificacion=%s' % r[0],
                            #~ True)
                    #~ message = ' y artículos reingresados correctamente.'
            #~ message = 'Factura (CFDI) cancelada correctamente%s' % message
            #~ self.unogui.createMsgBox({'Message': message})
        return

    def __filtrar(self, where=''):
        import traceback
        try:
            if where:
                where = 'compras.id_proveedor=receptores.id %s' % where
            else:
                where = 'compras.id_proveedor=receptores.id'
            #~ estatus = """CASE WHEN estatus=1 THEN 'Por pagar'
                #~ WHEN estatus=2 THEN 'Pagada'
                #~ WHEN estatus=3 THEN 'Cancelada' END"""
            fecha = """CASE strftime('%m', fecha)
                WHEN '01' THEN strftime('%d-Ene-%Y', fecha)
                WHEN '02' THEN strftime('%d-Feb-%Y', fecha)
                WHEN '03' THEN strftime('%d-Mar-%Y', fecha)
                WHEN '04' THEN strftime('%d-Abr-%Y', fecha)
                WHEN '05' THEN strftime('%d-May-%Y', fecha)
                WHEN '06' THEN strftime('%d-Jun-%Y', fecha)
                WHEN '07' THEN strftime('%d-Jul-%Y', fecha)
                WHEN '08' THEN strftime('%d-Ago-%Y', fecha)
                WHEN '09' THEN strftime('%d-Sep-%Y', fecha)
                WHEN '10' THEN strftime('%d-Oct-%Y', fecha)
                WHEN '11' THEN strftime('%d-Nov-%Y', fecha)
                WHEN '12' THEN strftime('%d-Dic-%Y', fecha) END"""
            data = self.db.select(('compras', 'receptores'),
                ('compras.id','serie || folio', fecha,
                    'upper(substr(tipoDeComprobante,1,1))', 'estatus', 'total',
                    'upper(substr(Moneda,1,1))', 'TipoCambio',
                    'total*TipoCambio', 'nombre', 'id_proveedor'),
                where, 'fecha')
            data_format = []
            suma_cfd = 0
            for row in data:
                total = self.format_s.format(row[5])
                tipo_cambio = row[7]
                suma_cfd += row[8]
                mn = self.format_s.format(row[8])
                row_format = (row[0], row[1], row[2], row[3], row[4], total, row[6], tipo_cambio, mn, row[9], row[10])
                data_format.append(row_format)
            self.unogui.gridAddRows(self.dm.gridFacturas, data_format)
            self.dm.suma.Value = suma_cfd
            if data:
                message = '%s Facturas encontradas' % len(data)
            else:
                message = 'No se encontraron facturas con estos criterios de busqueda'
                #~ self.unogui.createMsgBox({'Message': message})
            self.msg_user(message)
        except:
            print(traceback.format_exc())
        return

    def txtReceptor_focusLost(self, source):
        self.dialog.getControl('gridReceptores').setVisible(False)
        return

    def txtReceptor_keyPressed(self, event):
        if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(True)
            self.dm.txtReceptor.Tag = ''
            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                self.dm.txtReceptor.Tag = ''
                grid.setVisible(False)
                return
            where = "(nombre LIKE '%" + cliente + "%' OR rfc LIKE '%" + cliente + "%') AND esproveedor=1"
            receptores = self.db.select(('receptores',), ('id', 'rfc', 'nombre'), where, 'nombre')
            self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
        return

    def txtReceptor_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(False)
            self.dm.txtReceptor.Tag = ''

            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                row_count = self.db.count('receptores')
                if row_count < CLIENTES_COUNT:
                    receptores = self.db.select(('receptores',), ('id', 'rfc', 'nombre'), 'activo=1', 'nombre')
                    condicion = 'esproveedor=1'
                    self.unogui.gridAddRows(self.dm.gridReceptores, receptores, where=condicion)
                    grid.setFocus()
                    grid.setVisible(True)
                    return
                else:
                    message = 'Captura la clave del proveedor a buscar.'
                    self.msg_user(message)
                    return
            try:
                id_proveedor = int(cliente)
                receptor = self.db.select(('receptores',), where='id=%s AND activo=1 AND esproveedor=1' % id_proveedor)
                if receptor:
                    receptor = receptor[0]
                    self.dm.txtReceptor.Tag = receptor[0]
                    self.dm.txtReceptor.Text = receptor[2]
                else:
                    message = 'No se encontró el proveedor con la clave: %s' % id_proveedor
                    self.msg_user(message)
            except ValueError as e:
                message = 'Asegurate de capturar un valor entero para buscar por clave del proveedor'
                self.msg_user(message)
        return

    def gridReceptores_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            receptor = self.db.select(('receptores',), ('id', 'nombre'),where='id=%s' % grid_dm.getCellData(0, row))[0]
            self.dm.txtReceptor.Tag = receptor[0]
            self.dm.txtReceptor.Text = receptor[1]
            grid.setVisible(False)
        return

    def gridFacturas_selectionChanged(self, grid):
        self.id_addenda = 0
        self.id_cfd = 0
        self.dm.cmdEnviar.Enabled = False
        self.dm.cmdNotas.Enabled = False
        grid_dm = grid.Model.GridDataModel
        try:
            sel = self.util.clear_sel(grid.SelectedRows)
        except:
            print (traceback.format_exc())
        self.__sum_cfd(sel)
        if len(sel) == 1:
            self.dm.cmdEnviar.Enabled = True
            self.dm.cmdNotas.Enabled = True
            self.dm.cmdCamposPersonalizados.Enabled = True
            self.id_cfd = grid_dm.getCellData(0, sel[0])
            self.__get_nota(self.id_cfd)
            if self.dm.chkDetalle.State:
                try:
                    self.__get_detalle(self.id_cfd)
                except:
                    print (traceback.format_exc())
        return

    def __sum_cfd(self, sel):
        if not sel:
            return
        grid_dm = self.dm.gridFacturas.GridDataModel
        self.dm.gridDetalle.GridDataModel.removeAllRows()
        self.dm.gridTotales.GridDataModel.removeAllRows()
        total = 0
        for f in sel:
            value = grid_dm.getCellData(8, f).replace(',', '')
            total += float(value)
        self.dm.suma.Value = total
        return

    def __get_nota(self, id_cfd):
        data = self.db.select(('compras',), ('notas',), 'id=%s' % id_cfd)[0]
        self.dm.cmdNotas.Tag = data[0]
        return

    def __get_detalle(self, id_cfd):
        grid_dm = self.dm.gridDetalle
        grid_dm.GridDataModel.removeAllRows()
        fields = (
            'id',
            'noIdentificacion',
            'unidad',
            'descripcion',
            'cantidad',
            'valorUnitario',
            'importe')
        data = self.db.select(('compradetalle',), fields, 'id_compra=%s' % id_cfd)
        data_format = []
        for row in data:
            #~ print (row[0])
            cantidad = self.format_s.format(row[4])
            pu = self.format_s.format(row[5])
            importe = self.format_s.format(row[6])
            row_format = (row[0], row[1], row[2], row[3], cantidad, pu, importe)
            data_format.append(row_format)
        self.unogui.gridAddRows(grid_dm, data_format)

        fields = (
            'subTotal',
            'descuento',
            'total',
            'motivoDescuento',
            'notas')
        data = self.db.select(('compras',), fields, 'id=%s' % id_cfd)[0]

        columns = [{'Title': 'SubTotal', 'ColumnWidth': 60, 'HorizontalAlign': 2}]
        rows = [self.format_s.format(data[0])]
        if data[1]:
            columns.append({'Title': 'Descuento', 'ColumnWidth': 60, 'HorizontalAlign': 2})
            rows.append(self.format_s.format(data[1]))
        self.dm.cmdNotas.Tag = data[4]

        col = {'Title': 'TOTAL', 'ColumnWidth': 60, 'HorizontalAlign': 2}
        columns.append(col)
        total = self.format_s.format(data[2])
        rows.append(total)
        self.unogui.gridChangeColumn(self.dm.gridTotales, columns)
        self.unogui.gridAddRows(self.dm.gridTotales, (tuple(rows),))
        self.dm.gridTotales.GridDataModel.updateCellToolTip(1, 0, data[3])
        return

    def cmdNotas(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = grid.Selection[0]
        self.value = ''
        message = 'Edición de notas de la factura: %s' % grid_dm.getCellData(1, sel)
        input_box = inputbox2.Dlg(self, (message, self.dm.cmdNotas.Tag))
        res = input_box.execute()
        if res:
            id_cfd = grid_dm.getCellData(0, sel)
            self.db.update('compras', {'notas': self.value}, 'id=%s' % id_cfd)
            self.dm.cmdNotas.Tag = self.value
        return

    def cmdReporte(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        if not grid_dm.RowCount:
            message = 'No hay facturas a reportar'
            self.unogui.createMsgBox({'Message': message})
            return
        doc = self.util.newDoc()
        sheet = doc.getSheets().getByIndex(0)
        data, titles = self.grid_to_tuple(grid.Model)
        oRange = sheet.getCellRangeByPosition(0, 0, len(data[0])-1, 0)
        self.__format_title(oRange)
        oRange.setDataArray((titles,))
        oRange = sheet.getCellRangeByPosition(0, 1, len(data[0])-1, len(data))
        oRange.setDataArray(data)
        self.__format_columns(oRange, len(data[0]), len(data)-1)
        return

    def __format_title(self, rango):
        rango.CharWeight = 150
        rango.VertJustify = 2
        rango.HoriJustify = 2
        return

    def __format_columns(self, rango, num_col, num_fil):
        col = rango.getCellRangeByPosition(1, 0, 1, num_fil)
        col.NumberFormat = 37
        col = rango.getCellRangeByPosition(4, 0, 4, num_fil)
        col.NumberFormat = 104
        if num_col > 6:
            col = rango.getCellRangeByPosition(6, 0, 7, num_fil)
            col.NumberFormat = 104
        return

    def grid_to_tuple(self, grid):
        grid_dm = grid.GridDataModel
        col_m = grid.ColumnModel
        col = grid_dm.ColumnCount
        fil = grid_dm.RowCount
        data = []
        titles = []
        for f in range(fil):
            row = []
            for c in range(1, col):
                column = col_m.getColumn(c)
                if not column.ColumnWidth:
                    continue
                if f == 0:
                    titles.append(column.Title)
                if c == 2:
                    row.append(self.util.date_to_calc(grid_dm.getCellData(c, f)))
                elif c == 5 or c == 7 or c == 8:
                    value = grid_dm.getCellData(c, f).replace(',', '')
                    row.append(float(value))
                else:
                    row.append(grid_dm.getCellData(c, f))
            data.append(tuple(row))
        return tuple(data), tuple(titles)

        rutas = self.db.select(('rutasespejo',), ('ruta',))
        if self.dm.txtReceptor.Tag:
            data = self.db.select(('correos',), ('correo',), 'id_proveedor=%s' %
                                     self.dm.txtReceptor.Tag)
            to = [element[0] for element in data]
            if enviar == 3 and not to:
                message = 'Este cliente no tiene correo electrónico capturado, no es posible enviarle correos directamente'
                self.unogui.createMsgBox({'Message': message, 'Type': 'warningbox'})
                return
            paths = []
            for row in sel:
                id_cfd = grid_dm.getCellData(0, row)
                path_xml, path_pdf = self.__getPath(id_cfd, rutas)
                paths.append(path_xml)
                paths.append(path_pdf)
            self.util.enviar_correo((enviar, tuple(paths), to, config_server))
        else:
            co1 = 0
            for row in sel:
                id_cfd = grid_dm.getCellData(0, row)
                data = self.db.select(('correos',), ('correo',),
                    'id_proveedor=(SELECT id_proveedor FROM compras WHERE id=%s)'
                    % id_cfd)
                to = [element[0] for element in data]
                if enviar == 3 and not to:
                    continue
                path_xml, path_pdf = self.__getPath(id_cfd, rutas)
                if self.util.enviar_correo((enviar, (path_xml, path_pdf), to,
                            config_server)):
                    co1 += 1
            if enviar == 3:
                message = 'Facturas seleccionadas = %s\nFacturas enviadas = %s' % (len(sel), co1)
                self.unogui.createMsgBox({'Message': message})
        return

    def __getPath(self, id_cfd, rutas):
        ext_xml = '.xml'
        ext_pdf = '.pdf'
        name = "serie || substr('000000' || folio, -6, 6) || '_' || rfc"
        where = 'compras.id_proveedor=receptores.id AND compras.id=%s' % id_cfd
        data = self.db.select(('compras', 'receptores'),
                                    ("strftime('%Y',fecha)",
                                    "strftime('%m',fecha)",
                                    name,
                                    'xml'),
                                where)[0]
        if rutas:
            for path in rutas:
                path_xml = self.util.join(path[0], data[0])
                path_xml = self.util.join(path_xml, data[1])
                path_xml = self.util.join(path_xml, data[2] + ext_xml)
                path_pdf = path_xml.replace(ext_xml, ext_pdf)
                if self.util.exists(path_xml) and self.util.exists(path_pdf):
                    return path_xml, path_pdf
        path_xml = self.util.getPathTemp(data[2] + ext_xml)
        self.util.save_file(path_xml, data[3].encode('utf-8'))
        pdf = CFDPDF(self)
        pdf.show = False
        pdf.generate_pdf((id_cfd,), '')
        path_pdf = pdf.path_pdf
        return path_xml, path_pdf

    def chkDetalle(self, source):
        grid = self.dialog.getControl('gridFacturas')
        h = 180
        if source.State:
            h = 75
        self.dialog.getControl('gridDetalle').setVisible(source.State)
        self.dialog.getControl('gridTotales').setVisible(source.State)
        grid.Model.Height = h
        return

    def chkGuardar(self, source):
        if source.State:
            self.dm.chkEditar.State = False
            self.dm.cmdPdf.ImageURL = self.img_url + ICON_PDF
        return

    def chkEditar(self, source):
        if source.State:
            self.dm.chkGuardar.State = False
            icon_url = self.img_url + ICON_ODS
        else:
            icon_url = self.img_url + ICON_PDF
        self.dm.cmdPdf.ImageURL = icon_url
        return

    def lstAno_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def lstMes_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def lstEstatus_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def txtCfd_keyPressed(self, event):
        if event.KeyCode == KEY_RETURN or event.KeyCode == KEY_TAB:
            return
        folio = event.Source.Text.strip()
        if not folio:
            return
        where = 'compras.id_proveedor=receptores.id'
        where += " and folio LIKE '%" + folio + "%'"
        #~ estatus = "CASE WHEN estatus=1 THEN 'Por pagar' WHEN estatus=2 THEN " \
                    #~ "'Pagada' WHEN estatus=3 THEN 'Cancelada' END"
        data = self.db.select(
                            ('compras', 'receptores'),
                            ('compras.id',
                                'serie || folio',
                                "strftime('%d-%m-%Y',fecha)",
                                'upper(substr(tipoDeComprobante,1,1))',
                                'estatus',
                                'total',
                                'upper(substr(Moneda,1,1))',
                                'TipoCambio',
                                'total*TipoCambio',
                                'nombre'),
                            where)
        data_format = []
        suma_cfd = 0
        for row in data:
            total = self.format_s.format(row[5])
            tipo_cambio = self.format_s.format(row[7])
            suma_cfd += row[8]
            mn = self.format_s.format(row[8])
            row_format = (row[0], row[1], row[2], row[3], row[4], total,
                            row[6], tipo_cambio, mn, row[9])
            data_format.append(row_format)
        self.unogui.gridAddRows(self.dm.gridFacturas, data_format)
        return

    def txtCfd_keyRelease(self, event):
        pass

    def cmdCamposPersonalizados(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = grid.Selection[0]
        id_cfd = grid_dm.getCellData(0, sel)
        message = '%s - $%s - %s' % (
                            grid_dm.getCellData(1, sel),
                            grid_dm.getCellData(8, sel),
                            grid_dm.getCellData(9, sel))
        dlg = campos.Dlg(self, (id_cfd, message))
        dlg.execute()
        return

    def cmdReportes(self):
        patron = re.compile('([^{}]*)}')
        lst = self.dialog.getControl('lstReportes')
        if not lst.SelectedItemPos:
            message = 'Selecciona un reporte a emitir'
            #~ self.unogui.createMsgBox({'Message': message})
            self.msg_user(message)
            return
        name = lst.SelectedItem
        sql = self.db.select(('reportes',),
                            ('sql',),
                            "nombre='%s'" % name)[0][0]
        sql = sql.replace("''", "'")
        parametros = patron.findall(sql)
        if parametros:
            for p in parametros:
                self.value = ''
                message = 'Captura el valor para el parámetro:\n\n%s =' % p
                input_box = inputbox.Dlg(self, (message, False))
                if not input_box.execute():
                    message = 'Son necesarios todos los parametros'
                    self.unogui.createMsgBox({'Message': message})
                    return
                sql = sql.replace('{%s}' % p, self.value)
        data = self.db.execute(sql)
        if not data:
            message = 'Este reporte no devolvio ningun dato'
            self.unogui.createMsgBox({'Message': message})
            return

        cols = {}
        for i,v in enumerate(data[0]):
            if type(v) is datetime.datetime:
                cols[i] = True
        if cols:
            data_array = []
            for r in data:
                line = []
                for i,v in enumerate(r):
                    if i in cols:
                        line.append(v.toordinal() - 693594)
                    else:
                        line.append(v)
                data_array.append(tuple(line))
            data = data_array
        doc = self.util.newDoc()
        sheet = doc.getSheets().getByIndex(0)
        oRange = sheet.getCellRangeByPosition(0, 0, len(data[0])-1, len(data)-1)
        oRange.setDataArray(tuple(data))
        self.__format_columns_date(oRange, cols, len(data)-1)
        return

    def __format_columns_date(self, rango, dates, num_fil):
        if dates:
            for c in list(dates.keys()):
                col = rango.getCellRangeByPosition(c, 0, c, num_fil)
                col.NumberFormat = 37
        return

    def cmdXml(self):
        export = 0
        try:
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            sel = grid.SelectedRows
            if not sel:
                message = 'Selecciona primero una factura'
                self.msg_user(message)
                return
            destino = ''
            destino = self.unogui.getFolder(self.util.getPathUser())
            destino = destino.strip()
            if not destino:
                return
            for row in sel:
                if row < 0: continue
                id_cfd = grid_dm.getCellData(0, row)
                factura = grid_dm.getCellData(1, row)
                # If is CBB or CFD
                name_xml = "serie || substr('000000' || folio, -6, 6) || '_' || rfc || '.xml'"
                where = 'compras.id_proveedor=receptores.id AND compras.id=%s' % id_cfd
                data = self.db.select(
                    ('compras', 'receptores'),
                    ('substr(version, 1, 1)', 'serie || folio',
                        "strftime('%Y',fecha)", "strftime('%m',fecha)",
                        name_xml, 'xml', 'estatus'),
                    where)[0]
                self.msg_user('Verificando factura: %s' % data[1])
                if data[0] == '2':
                    # Esquema CFD
                    self._fac_cfd(data, destino)
                    continue
                if destino:
                    self.util.copy_xml(data[2:],(destino,))
                    export += 1
                    self.msg_user('Guardando factura: %s' % data[1])
            self.msg_user('Proceso terminado...')
            if destino and export:
                message = 'Documentos exportados correctamente'
                self.unogui.createMsgBox({'Message': message})
        except:
            print (traceback.format_exc())
        return

    def _fac_cfd(self, factura, destino):
        if factura[5]:
            if destino:
                self.util.copy_xml(factura[2:], (destino,))
            else:
                message = 'La factura: %s es del esquema CFD, XML correcto' % factura[1]
                self.unogui.createMsgBox({'Message': message})
        else:
            message = 'No se encontró el XML de la factura: %s\n\nConsulta' \
                        'a soporte tecnico' % factura[1]
            self.unogui.createMsgBox({'Message': message})
        return

    def __create_pdf(self, id_cfd):
        pdf = CFDPDF(self)
        pdf.generate_pdf((id_cfd,))
        return pdf.path_pdf

    def __copiar_xml(self, id_cfd, path_pdf=''):
        rutas = self.db.select(('rutasespejo',), ('ruta',))
        path_xml = ''
        if rutas:
            name_xml = "serie || substr('000000' || folio, -6, 6) || '_' || rfc || '.xml'"
            where = 'compras.id_proveedor=receptores.id AND compras.id=%s' % id_cfd
            data = self.db.select(('compras', 'receptores'), ("strftime('%Y',fecha)", "strftime('%m',fecha)", name_xml, 'xml'), where)[0]
            path_xml = self.util.copy_xml(data, rutas, path_pdf)
        return

    def __generar_xml(self, id_cfd):
        cfd = CFDXML(self, id_cfd)
        xml = cfd.generate_xml()
        self.db.update('compras', {'xml': xml, 'estatus': 'Generada'}, 'id=%s' % id_cfd)
        return True

    def _timbrada(self, data, id_cfd, row, destino=''):
        xml = data[5]
        if xml:
            xml = ET.fromstring(xml.encode('UTF-8'))
            timbre = xml.find('%sComplemento' % PRE)
            if timbre is not None:
                timbre = timbre.find('%sTimbreFiscalDigital' % PRE2)
                if timbre is not None:
                    uuid = timbre.attrib['UUID']
                    self.db.update('compras',
                        {'uuid': uuid, 'estatus': 'Por pagar'}, 'id=%s' % id_cfd)
                    message = 'Factura verificada correctamente, ya puedes ' \
                        'exportarla de nuevo'
                    self.unogui.createMsgBox({'Message': message})
                    return True
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, se ' \
                'requiere para verificar la factura con el PAC.'
            self.unogui.createMsgBox({'Message': message})
            return False
        exists = True
        if data[7] == 'Enviada':
            ok, res = self.util.EstatusXML(self.rfc, id_cfd)
            if not ok:
                self.unogui.createMsgBox({'Message': res})
                return False
            #~ Recuperar
            if res['Codigo'] == '600' or res['Codigo'] == '602':
                return self._recuperar_xml(self.rfc, id_cfd)
            elif res['Codigo'] == '605':
                if not xml:
                    if not self.__generar_xml(id_cfd):
                        message = 'No se pudo generar el XMl de la ' \
                            'Factura: %s\n\nConsulta a soporte ' \
                            'técnico' % data[1]
                        self.unogui.createMsgBox({'Message': message})
                        return False
                    xml = self.db.select(
                            ('compras',), ('xml',), 'id=%s' % id_cfd)[0][0]
                exists = False
        if data[7] == 'Generada' or not exists:
            message = 'La factura: %s no esta timbrada. \n\n¿Deseas enviarla ' \
                'a timbrar con el PAC?. \n\nIMPORTANTE: la fecha y hora serán ' \
                'actualizadas automáticamente.\n\n¿Deseas enviarla?' % data[1]
            if not self.unogui.createQuestion('Factura Libre', message):
                return False
            if self._enviar_timbrar(xml, id_cfd, row):
                message = 'La factura se timbro correctamente y se ha ' \
                    'guardado en la base de datos, ya puedes exportarla ' \
                    'de nuevo'
                self.unogui.createMsgBox({'Message': message})
                return True
        return False

    def chkGuardar(self, source):
        if source.State:
            self.dm.chkEditar.State = False
        return

    def chkEditar(self, source):
        if source.State:
            self.dm.chkGuardar.State = False
        return

    def cmdAddenda(self):
        from facturalibre.modulos.pyXml import AGREGARADDENDA

        data = self.db.select(('asignaciones', ),
                                ('origen2', 'destino2'),
                                'id_addenda=%s' % self.id_addenda)
        perso = self.db.select(('cfdpersonalizados', ),
                                ('campo', 'valor'),
                                'id_cfd=%s' % self.id_cfd)
        xml = self.db.select(('compras',),
                                ('xml',),
                                'id=%s' % self.id_cfd)[0][0]
        addenda = self.db.select(('addendas',),
                                ('addenda',),
                                'id=%s' % self.id_addenda)[0][0]
        try:
            aa = AGREGARADDENDA(self.globales['PRE'])
            path1 = self.util.getPathTemp()
            path2 = self.util.getPathTemp()
            self.util.save_file(path1, xml)
            self.util.save_file(path2, addenda)
            aa.parse(path1, path2)
            if aa.message:
                message = '%s\n\n¿Estás seguro de reemplazarla?' % aa.message
                if not self.unogui.createQuestion('Factura Libre', message):
                    return
                aa.message = ''
            xml = ''
            if aa.add_data(data, perso):
                xml = aa.tostring()
                self.db.update('compras',
                                {'xml': xml},
                                'id=%s' % self.id_cfd)
                message = 'Addenda agregada correctamente a la ' \
                            'factura seleccionada'
            else:
                message = aa.message
            self.unogui.createMsgBox({'Message': message})
        except:
            print(traceback.format_exc())
        return

    #~ Solo Quimica Universo
    def cmdEnviar(self):
        try:
            clientes = (1,5)
            name_xml = "serie || substr('000000' || folio, -6, 6) || '.xml'"
            data = self.db.select(('compras', ),
                                    ('id_proveedor', name_xml, 'xml'),
                                    'id=%s' % self.id_cfd)[0]
            if not data[0] in clientes:
                self.dm.cmdEnviar.Enabled = False
                return
            if not 'Addenda' in data[2]:
                message = 'Agrega la Addenda antes de intentar enviarla'
                self.unogui.createMsgBox({'Message': message})
                return
            message = '¿Estás seguro de subir esta factura al servidor?'
            if self.unogui.createQuestion('Factura Libre', message):
                if self._send_ftp(data[1], data[2]):
                    message = 'Factura subida correctamente'
                else:
                    message = 'No fue posible subir la factura ' \
                            'consulta a soporte tecnico'
                self.unogui.createMsgBox({'Message': message})
        except:
            print(traceback.format_exc())
        return

    def _send_ftp(self, name, xml):
        import ftplib

        folders = ('colgate', 'cfdi')
        server = 'ftp.quimicauniverso.com'
        user = ''
        pas = ''
        try:
            path = self.util.getPathTemp()
            self.util.save_file(path, xml)
            ftp = ftplib.FTP(server, timeout=10)
            ftp.login(user, pas)
            for f in folders:
                try:
                    ftp.cwd(f)
                except:
                    ftp.mkd(f)
                    ftp.cwd(f)
            f = open(path, 'rb')
            ftp.storbinary('STOR %s' % name, f)
            f.close()
            return True
        except ftplib.all_errors as e:
            print(e)
        finally:
            ftp.close()
        return False

    def __saldo(self, id_proveedor, total):
        condicion = 'id=%s' % id_proveedor
        saldo = self.db.select(('receptores',), ('saldoProveedor',), where = condicion)
        nuevoSaldo = saldo[0][0] - float(total.replace(",", ""))
        self.db.update('receptores', {'saldoProveedor':nuevoSaldo}, condicion)
        return

    def cmdSat(self):
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, es necesaria' \
                        ' para enviar para consultar el estatus en el SAT'
            self.unogui.createMsgBox({'Message': message})
            return
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = grid.SelectedRows
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        if len(sel) > 1:
            message = 'Selecciona solo una factura'
            self.msg_user(message)
            return
        id_cfdi = grid_dm.getCellData(0, sel[0])
        fac = grid_dm.getCellData(1, sel[0])
        xml = self.db.select(
            ('compras',), ('xml',), 'id=%s' % id_cfdi)[0][0]
        #~ print (xml)
        try:
            res, msg = self.util.get_estatus(xml)
        except:
            print(traceback.format_exc())

        msg = 'Factura: %s\n\n%s' % (fac, msg)
        self.unogui.createMsgBox({'Message': msg})
        return
