# -*- coding: utf-8 -*-

import logging
import facturalibre.ui.clientesadmin as clientesadmin
#~ import facturalibre.ui.producto as productosadmin
import facturalibre.ui.add_products as add_products
import facturalibre.ui.refacturar as refacturar
import facturalibre.ui.inputbox as inputbox
import facturalibre.ui.inputbox2 as inputbox2
from facturalibre.modulos.pyXml import CFDXML
from facturalibre.modulos.pyPdf import CFDPDF
import facturalibre.ui.campos as campos
from facturalibre.ui.complements import Complements

import facturalibre.ui.producto as producto
from facturalibre.modulos import util
from facturalibre.settings import (
    LOG, KEY, SEND_MAIL, CURRENCY, CURRENCIES, TYPE_MSG, PAYMENT_METHODS
)


log = logging.getLogger(LOG['NAME'])


KEY_RETURN = 1280
KEY_TAB = 1282
CLIENTES_COUNT = 101
BUSQUEDA_MIN = 1
EXENTO = 'EXENTO'


class EventosCfdi(object):

    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.opciones = caller.opciones
        self.db = caller.db
        self.db_detalle = caller.db_detalle
        self.db_detalle.decimales = caller.opciones[0]
        self.db_detalle.tax_round = self._tax_round()
        self.globales = caller.globales
        self.format_s = self.globales['FORMAT'] % caller.opciones[0]
        self.unogui = caller.unogui
        self.dialog = caller.dialog
        self.enviar_correo = caller.enviar_correo
        self.new_server = caller.new_server
        self.dm = self.dialog.getModel()
        self.producto = None
        self.impuestos = None
        self.notas = ''
        self.regimenfiscal = ''
        self.prefactura = False
        self.path_pem = caller.path_pem
        self.value = ''
        self.agregar_producto = bool(
            self.db.select_field('opciones2', 'opcion4'))
        self.new_products = ()
        self.estatus = ''
        self.alumno = {}
        self.edu_version = self.db.select_field('sat', 'eduversion')
        self.donativo = self.dialog.getControl('lblDonativo').isVisible()
        self.rfc_emisor = caller.rfc_emisor
        self.total_mn = 0
        self.complement = None
        self.lst_payment_method = self.dialog.getControl('lst_payment_method')

    def _tax_round(self):
        tax = {}
        data = self.db.select(('impuestos',), ('nombre', 'redondear'))
        if data:
            for t in data:
                tax[t[0]] = bool(t[1])
        return tax

    def cmdSalir(self):
        self.util.kill(self.path_pem)
        self.dialog.endDialog(1)
        return

    def cmdDetalleReceptor(self):
        self.unogui.createMsgBox({'Message':self.dm.cmdDetalleReceptor.Tag})
        return

    def cmdNuevoReceptor(self):
        dialog_admin = clientesadmin.Dlg(self.caller)
        id_cliente = dialog_admin.execute()
        if id_cliente:
            self.dm.txtReceptor.Enabled = True
            self.__get_detalle_cliente(id_cliente)
        return

    def txtReceptor_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(False)
            self.dm.cmdDetalleReceptor.Enabled = False
            self.dm.txtReceptor.Tag = ''

            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                row_count = self.db.count('receptores')
                if row_count < CLIENTES_COUNT:
                    receptores = self.db.select(
                        ('receptores',),
                        ('id', 'rfc', 'nombre'),
                        'activo=1',
                        'nombre')
                    self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
                    grid.setFocus()
                    grid.setVisible(True)
                    return
                else:
                    message = 'Captura la clave del cliente a buscar.'
                    self.unogui.createMsgBox({'Message': message})
                    return
            try:
                id_cliente = int(cliente)
                fields = (
                        'id',
                        'rfc',
                        'nombre',
                        'calle',
                        'noExterior',
                        'noInterior',
                        'colonia',
                        'codigoPostal',
                        'municipio',
                        'estado',
                        'pais',
                        'notas',
                        'metododepago',
                        'cuentadepago',
                        'condiciondepago')
                receptor = self.db.select(
                            ('receptores',),
                            fields,
                            'id=%s AND activo=1' % id_cliente)
                if receptor:
                    receptor = receptor[0]
                    self.dm.txtReceptor.Tag = receptor[0]
                    self.dm.txtReceptor.Text = receptor[2]
                    self.dm.cmdDetalleReceptor.Enabled = True
                    self.__get_detalle_cliente(receptor[0])
                else:
                    message = 'No se encontró en los receptores activos, uno ' \
                        'con la clave: %s' % id_cliente
                    self.unogui.createMsgBox({'Message': message})
            except ValueError as e:
                message = 'Asegurate de capturar un valor entero para buscar ' \
                    'por clave del cliente'
                self.unogui.createMsgBox({'Message': message})
        return

    def txtReceptor_keyPressed(self, event):
        cliente = event.Source.Text.strip().replace('|','')
        try:
            id_cliente = int(cliente)
        except:
            if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
                grid = self.dialog.getControl('gridReceptores')
                grid.setVisible(True)
                self.dm.cmdDetalleReceptor.Enabled = False
                self.dm.txtReceptor.Tag = ''
                if not cliente:
                    grid.setVisible(False)
                    return
                where = "activo=1 AND nombre LIKE '%" + \
                        cliente + "%' OR rfc LIKE '%" + cliente + "%'"
                receptores = self.db.select(('receptores',),
                                            ('id', 'rfc', 'nombre'),
                                            where, 'nombre')
                self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
        return

    def gridReceptores_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        count = grid_dm.RowCount
        if count:
            row = grid.CurrentRow
            if row < 0 or count==1:
                row = 0
            self.__get_detalle_cliente(grid_dm.getCellData(0, row))
            grid.setVisible(False)
        return

    def cmdMostrarFolios(self):
        grid = self.dialog.getControl('gridFolios')
        grid.setVisible(not grid.isVisible())
        if grid.isVisible():
            grid.setFocus()
        return

    def gridFolios_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        folio_actual = grid_dm.getCellData(3, row)
        if grid_dm.getCellData(1, row):
            self.dm.lblFolio.Label = '%s-%s' % (
                grid_dm.getCellData(1, row), folio_actual)
        else:
            self.dm.lblFolio.Label = grid_dm.getCellData(4, row)
        tipo = grid_dm.getCellData(4, row)
        if tipo == 'todos':
            self.dm.optIngreso.State = 1
            self.dm.optIngreso.Enabled = True
            self.dm.optEgreso.Enabled = True
            self.dm.optTraslado.Enabled = True
        elif tipo == 'ingreso':
            self.dm.optIngreso.State = 1
            self.dm.optIngreso.Enabled = True
            self.dm.optEgreso.Enabled = False
            self.dm.optTraslado.Enabled = False
        elif tipo == 'egreso':
            self.dm.optEgreso.State = 1
            self.dm.optEgreso.Enabled = True
            self.dm.optIngreso.Enabled = False
            self.dm.optTraslado.Enabled = False
        elif tipo == 'traslado':
            self.dm.optTraslado.State = 1
            self.dm.optTraslado.Enabled = True
            self.dm.optIngreso.Enabled = False
            self.dm.optEgreso.Enabled = False
        if grid_dm.RowCount == 1:
            self.dm.cmdMostrarFolios.Enabled = False
        visible = bool(grid_dm.getCellData(5, row))
        self.dialog.getControl('lblDonativo').setVisible(visible)
        self.donativo = visible
        grid.setVisible(False)
        return

    def cmdMostrarCategorias(self):
        tree = self.dialog.getControl('treeCategorias')
        tree.setVisible(not tree.isVisible())
        self.dialog.getControl('gridDetalle').setVisible(not tree.isVisible())
        if tree.isVisible():
            tree.setFocus()
        mostrar = not tree.isVisible()
        self.dialog.getControl('unidad').setVisible(mostrar)
        self.dialog.getControl('noIdentificacion').setVisible(mostrar)
        self.dialog.getControl('cantidad').setVisible(mostrar)
        self.dialog.getControl('lblUnidad').setVisible(mostrar)
        self.dialog.getControl('lblClave').setVisible(mostrar)
        self.dialog.getControl('lblCantidad').setVisible(mostrar)
        return

    def treeDobleClick(self, tree):
        sel = tree.Selection
        categoria = sel.DataValue
        if categoria == 0:
            self.dm.txtCategoria.Text = ''
            self.dm.txtCategoria.Tag = 0
        else:
            self.dm.txtCategoria.Tag = sel.DataValue
            cat=[]
            while sel.DataValue:
                cat.insert(0, sel.DisplayValue)
                sel = sel.getParent()
            self.dm.txtCategoria.Text = '|'.join(cat)
        productos = self.db.select(
            ('productos',),
            ('id', 'noIdentificacion', 'descripcion', 'unidad',
                'valorUnitario', 'existencia'),
            'id_categoria=%s' % categoria, 'descripcion')
        self.unogui.gridAddRows(self.dm.gridProductos, productos)
        if productos:
            self.dm.cmdMostrarProductos.Enabled = True
        else:
            self.dm.cmdMostrarProductos.Enabled = False
            self.dialog.getControl('gridDetalle').setVisible(True)
        self.dialog.getControl('cmdMostrarProductos').setFocus()
        tree.setVisible(False)
        return

    def treeCategorias_focusLost(self, tree):
        self.dialog.getControl('gridDetalle').setVisible(True)
        self.dialog.getControl('unidad').setVisible(True)
        self.dialog.getControl('noIdentificacion').setVisible(True)
        self.dialog.getControl('cantidad').setVisible(True)
        self.dialog.getControl('lblUnidad').setVisible(True)
        self.dialog.getControl('lblClave').setVisible(True)
        self.dialog.getControl('lblCantidad').setVisible(True)
        return

    def treeCategorias_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            self.treeDobleClick(event.Source)
        return

    def descripcion_keyPressed(self, event):
        if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
            grid = self.dialog.getControl('gridProductos')
            producto = event.Source.Text.strip().replace('|','')
            if not producto:
                grid.setVisible(False)
                return
            valorUnitario = 'valorUnitario'
            where = "noIdentificacion LIKE '%" + producto + "%' OR " \
                    "descripcion LIKE '%" + producto + "%'"
            if self.dm.txtCategoria.Tag != '0':
                where += " and id_categoria=%s" % self.dm.txtCategoria.Tag
            productos = self.db.select(('productos',),
                                        ('id',
                                        'noIdentificacion',
                                        'descripcion',
                                        'unidad',
                                        'valorUnitario',
                                        'existencia'),
                                        where,
                                        'descripcion')
            self.unogui.gridAddRows(self.dm.gridProductos, productos)
            if productos:
                grid.setVisible(True)
            else:
                grid.setVisible(False)
        return

    def descripcion_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            grid = self.dialog.getControl('gridProductos')
            grid.setVisible(False)
            self.dm.descripcion.Tag = 0
            producto = event.Source.Text.strip().replace('|','')
            if producto:
                productos = self.db.select(('productos',), where="codigobarras='%s'" % producto)
                if productos:
                    producto = productos[0]
                    self.__mostrar_producto(producto[0])
                    self.__actualizar_importe()
                    self.cmdAgregarProducto()
                    self.dm.cmdAgregarProducto.Enabled = True
                    return
                productos = self.db.select(('productos',), where="noIdentificacion='%s'" % producto)
                if productos:
                    producto = productos[0]
                    self.dm.descripcion.Tag = producto[0]
                    self.dm.descripcion.Text = producto[3]
                    self.__mostrar_producto(producto[0])
                    self.__actualizar_importe()
                    self.dm.cmdAgregarProducto.Enabled = True
                    return
                else:
                    message = 'No se encontró el producto o servicio con esta clave o codigo de barras'
                    self.unogui.createMsgBox({'Message':message})
                return
            else:
                message = 'Captura la clave del producto o servicio a buscar.'
                self.unogui.createMsgBox({'Message':message})
                return
        return

    def cmdMostrarProductos(self):
        grid = self.dialog.getControl('gridProductos')
        grid.deselectAllRows()
        grid_dm = grid.Model.GridDataModel
        if not grid_dm.RowCount:
            msg = 'Esta categoría no tiene productos asignados, selecciona otra'
            self.unogui.createMsgBox({'Message': msg})
            return
        grid.setVisible(not grid.isVisible())
        if grid.isVisible():
            grid.setFocus()
        return

    def cmdNuevoProducto(self):
        dlg = producto.Dlg(self.db)
        id_product = dlg.execute()
        if id_product:
            self.__mostrar_producto(id_product)
            self.dm.txtCategoria.Enabled = True
            self.dm.cmdMostrarCategorias.Enabled = True
            self.dm.descripcion.Enabled = True
            self.__actualizar_importe()
            self.dm.cmdAgregarProducto.Enabled = True
        return

    def gridProductos_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid.isVisible():
            if grid_dm.RowCount:
                row = grid.CurrentRow
                if row < 0:
                    row = 0
                self.__mostrar_producto(grid_dm.getCellData(0, row))
                self.__actualizar_importe()
                grid.setVisible(False)
                self.dm.cmdAgregarProducto.Enabled = True
        return

    def __mostrar_producto(self, id_producto):
        fields = (
            'productos.id',
            "CASE WHEN id_categoria THEN categoria ELSE '' END",
            'unidad',
            'noIdentificacion',
            'descripcion',
            'valorUnitario',
            'existencia',
            'inventario',
            'CuentaPredial')
        producto = self.db.select(
            ('productos',),
            fields,
            'productos.id=%s' % id_producto,
            other1='LEFT OUTER JOIN categorias ON productos.id_categoria = categorias.id')[0]
        self.dm.unidad.Text = producto[2]
        self.dm.noIdentificacion.Text = producto[3]
        self.dm.descripcion.Text = producto[4]
        self.dm.valorUnitario.Value = producto[5]
        fields = ('nombre', 'tasa', 'tipo')
        where = 'productosimpuestos.id_impuesto=impuestos.id AND ' \
            'productosimpuestos.id_producto=%s' % producto[0]
        impuestos = self.db.select(
            ('impuestos', 'productosimpuestos'), fields, where)
        self.producto = producto
        self.impuestos = impuestos
        return

    def chkMostrarAduana(self, source):
        controls = ('lblAduana', 'aduana', 'lblNumero', 'fecha', 'numero')
        self.unogui.setVisible(self.dialog, controls, source.State)
        if source.State:
            source.Model.Label = ''
            source.Model.Width = 15
            self.dialog.getControl('aduana').setFocus()
        else:
            source.Model.Label = 'Mostrar datos aduanales'
            self.dm.aduana.Text = ''
            self.dm.numero.Text = ''
            self.dm.fecha.Text = ''
            source.Model.Width = 100
        return

    def chkDescuento(self, source):
        self.dm.motivoDescuento.Enabled = source.State
        self.dm.descuento.Enabled = source.State
        if source.State:
            self.dialog.getControl('motivoDescuento').setFocus()
        else:
            self.dm.descuento.Value = 0
        self.__mostrar_totales()
        return

    def cantidad_textChanged(self):
        self.__actualizar_importe()
        return

    def valorUnitario_textChanged(self):
        self.__actualizar_importe()
        return

    def descuento_textChanged(self):
        self.__mostrar_totales()
        return

    def __actualizar_importe(self):
        self.dm.importe.Value = self.dm.cantidad.Value * self.dm.valorUnitario.Value
        return

    def cmdAgregarProducto(self):
        #~ try:
        if self.dm.chkDescuento.State:
            descuento = self.dm.descuento.Value
        else:
            descuento = 0
        if self._validar_agregar_producto():
            grid = self.dialog.getControl('gridDetalle')
            grid_dm = grid.Model.GridDataModel
            pos = grid_dm.RowCount + 1
            producto = {}
            producto['id'] = self.producto[0]
            producto['categoria'] = self.producto[1]
            producto['cantidad'] = self.dm.cantidad.Value
            if not self.agregar_producto:
                productos = self.db_detalle.exists_product(
                    producto['id'], producto['cantidad'], descuento)
                if productos:
                    self.__show_data(productos)
                    self.__mostrar_totales()
                    return
            producto['unidad'] = self.dm.unidad.Text
            producto['noIdentificacion'] = self.dm.noIdentificacion.Text
            des = util.render(self.producto[4])
            if self.alumno:
                if self.dialog.getControl('lstMes').SelectedItemPos > 0:
                    des += ' %s' % self.dialog.getControl('lstMes').SelectedItem
                if self.dm.fecha2.Text:
                    des += '\nDepósito del día ' + self.dm.fecha2.Text
                if not self.alumno['autorizacion']:
                    des += '\n%s\nCurp: %s\nNivel: %s' % (
                        self.alumno['alumno'],
                        self.alumno['curp'],
                        self.alumno['nivel'])
            producto['descripcion'] = des
            producto['valorUnitario'] = self.__calcular_precio(
                producto['id'], self.dm.valorUnitario.Value)
            producto['importe'] = round(
                producto['cantidad'] * producto['valorUnitario'],
                self.opciones[0])
            producto['numero'] = self.dm.numero.Text
            if self.dm.fecha.Date:
                producto['fecha'] = str(
                    self.util.getDateFromControl(self.dm.fecha.Date, True))
            producto['aduana'] = self.dm.aduana.Text
            producto['CuentaPredial'] = self.producto[8]
            producto['inventario'] = self.producto[7]
            if self.alumno:
                producto['version'] = self.edu_version
                producto['alumno'] = self.alumno['alumno']
                producto['curp'] = self.alumno['curp']
                producto['nivel'] = self.alumno['nivel']
                producto['autorizacion'] = self.alumno['autorizacion']
            producto['pos'] = pos
            where = 'productosimpuestos.id_impuesto=impuestos.id AND ' \
                'id_producto=%s' % producto['id']
            impuestos = self.db.select(
                ('impuestos','productosimpuestos'),
                ('nombre','tasa','tipo'), where)
            productos = self.db_detalle.insert_product(
                producto, impuestos, descuento)
            self.__show_data(productos)
            self.__mostrar_totales()
            self.dm.cantidad.Value = 1
            self.dm.cmdEliminarProducto.Enabled = True
            self.alumno = {}
            self.dm.txtAlumno.Text = ''
            self.dm.fecha2.Text = ''
        #~ except:
            #~ print (traceback.format_exc())
        return

    def __show_data(self, productos):
        data = []
        for row in productos:
            data.append((row[0], row[1], row[2], row[3], row[4],
                        self.format_s.format(row[5]),
                        self.format_s.format(row[6]),
                        row[7]))
        self.unogui.gridAddRows(self.dm.gridDetalle, data)
        enabled = bool(len(productos)-1)
        self.dm.cmdArriba.Enabled = enabled
        self.dm.cmdAbajo.Enabled = enabled
        return

    def __calcular_precio(self, id_producto, precio):
        if not self.opciones[1]:
            return precio
        imp = 'IVA'
        where = "productosimpuestos.id_impuesto=impuestos.id AND nombre='%s' " \
            "AND tipo='Traslado' AND CAST(tasa AS REAL)>0 AND id_producto=%s"
        impuesto = self.db.select(
            ('impuestos', 'productosimpuestos'),
            ('tasa',),
            where % (imp, id_producto))
        valor_unitario = precio
        if impuesto:
            impuesto = 1 + float(impuesto[0][0]) / 100
            valor_unitario = round(valor_unitario / impuesto, self.opciones[0])
        imp = 'IEPS'
        impuesto = self.db.select(
            ('impuestos', 'productosimpuestos'),
            ('tasa',),
            where % (imp, id_producto))
        if impuesto:
            impuesto = 1 + float(impuesto[0][0]) / 100
            valor_unitario = round(valor_unitario / impuesto, self.opciones[0])
        return valor_unitario

    def __mostrar_totales(self):
        if self.db_detalle.impuestos:
            if self.db_detalle.impuestos[0]['subtotal']:
                self.dm.descuento.ValueMax = self.db_detalle.impuestos[0]['subtotal']
        self.db_detalle.calcular_impuestos(self.dm.descuento.Value)
        if self.db_detalle.impuestos[0]['subtotal'] is None:
            col = ({'Title': 'SubTotal', 'ColumnWidth': 60, 'HorizontalAlign': 2},
                {'Title': 'Impuestos', 'ColumnWidth': 60, 'HorizontalAlign': 2},
                {'Title': 'TOTAL', 'ColumnWidth': 60, 'HorizontalAlign': 2})
            self.unogui.gridChangeColumn(self.dm.gridTotales, col)
            total = self.format_s.format(0)
            self.unogui.gridAddRows(self.dm.gridTotales, ((total, total, total),))
            return
        subtotal = self.db_detalle.impuestos[0]['subtotal']
        descuento = self.db_detalle.impuestos[0]['descuento']
        if self.db_detalle.impuestos[0]['totalTraslados'] is None:
            traslados = 0
        else:
            traslados = self.db_detalle.impuestos[0]['totalTraslados']
        if self.db_detalle.impuestos[0]['totalRetenciones'] is None:
            retenciones = 0
        else:
            retenciones = self.db_detalle.impuestos[0]['totalRetenciones']
        columns=[{'Title': 'SubTotal', 'ColumnWidth': 60, 'HorizontalAlign': 2}]
        rows = [self.format_s.format(subtotal)]
        if descuento:
            columns.append(
                {'Title': 'Descuento',
                'ColumnWidth': 60,
                'HorizontalAlign': 2})
            rows.append(self.format_s.format(descuento))
        for i in range(1,len(self.db_detalle.impuestos)):
            col = {}
            col['Title'] = self.db_detalle.impuestos[i]['titulo']
            col['ColumnWidth'] = 60
            col['HorizontalAlign'] = 2
            columns.append(col)
            importe_s = self.format_s.format(
                                    self.db_detalle.impuestos[i]['importe'])
            rows.append(importe_s)
        col = {'Title': 'TOTAL', 'ColumnWidth': 60, 'HorizontalAlign': 2}
        columns.append(col)
        total = self.format_s.format(self.db_detalle.impuestos[0]['total'])
        rows.append(total)
        self.unogui.gridChangeColumn(self.dm.gridTotales, columns)
        self.unogui.gridAddRows(self.dm.gridTotales, (tuple(rows),))
        return

    def _validar_agregar_producto(self):
        if not self.producto:
            message = 'Selecciona un producto o servicio'
            self.unogui.createMsgBox({'Message': message})
            return False
        if not self.dm.cantidad.Value:
            message = 'La cantidad no puede ser cero'
            self.unogui.createMsgBox({'Message': message})
            return False
        if not self.dm.valorUnitario.Value:
            message = 'El valor unitario es cero \n\n' \
                '¿Estás seguro de usar este valor?'
            if not self.unogui.createQuestion('Factura Libre', message):
                return False
        if self.dm.valorUnitario.Value < 0:
            message = 'El valor unitario es negativo \n\n' \
                '¿Estás seguro de usar este valor?'
            if not self.unogui.createQuestion('Factura Libre', message):
                return False
        if self.producto[7] and not self.opciones[2]:
            cant = self.db_detalle.exists_product_cant(self.producto[0])
            if (self.dm.cantidad.Value + cant) > self.producto[6]:
                message = 'No hay suficiente existencia de este producto'
                self.unogui.createMsgBox({'Message': message})
                return False
        if self.donativo:
            for i in self.impuestos:
                if i[1] != EXENTO:
                    message = 'Estas haciendo un recibo de donativo, pero ' \
                        'estas agregando un producto o servicio NO exento, ' \
                        'esto generalmente es incorrecto.\n\n¿Estás seguro ' \
                        'de agregar este producto o servicio?'
                    if not self.unogui.createQuestion('Factura Libre', message):
                        return False
                    break
        if self.dm.chkMostrarAduana.State:
            control = self.dialog.getControl('aduana')
            if self.unogui.validate(control,'Vacio'):
                message='El campo ADUANA no puede estar vacío'
                self.unogui.createMsgBox({'Message':message})
                control.setFocus()
                return False
            date = self.dm.fecha.Date
            if not date:
                message = 'El campo FECHA no puede estar vacío'
                self.unogui.createMsgBox({'Message': message})
                control.setFocus()
                return False
            control = self.dialog.getControl('numero')
            if self.unogui.validate(control, 'Vacio'):
                message='El campo NUMERO DE PEDIMENTO no puede estar vacío'
                self.unogui.createMsgBox({'Message': message})
                control.setFocus()
                return False

        if self.dialog.getControl('cmdMostrarAlumnos').isVisible():
            if not self.alumno:
                message = 'No has seleccionado el alumno.\n\n¿Estás seguro ' \
                    'de continuar sin agregar uno?'
                if not self.unogui.createQuestion('Factura Libre', message):
                    self.dialog.getControl('txtAlumno').setFocus()
                    return False
            lstMes = self.dialog.getControl('lstMes')
            if lstMes.SelectedItemPos == 0:
                message = 'No has seleccionado el mes de pago.\n\n¿Estás ' \
                    'seguro de continuar sin agregarlo?'
                if not self.unogui.createQuestion('Factura Libre', message):
                    lstMes.setFocus()
                    return False
            date = self.dm.fecha2.Date
            if not date or not self.dm.fecha2.Text:
                message = 'No has seleccionado la fecha de pago.\n\n¿Estás ' \
                    'seguro de continuar sin agregarlo?'
                if not self.unogui.createQuestion('Factura Libre', message):
                    self.dialog.getControl('fecha2').setFocus()
                    return False
            if date:
                date = self.util.getDateFromControl(date)
                if date > self.util.today():
                    message = 'La fecha de pago seleccionada, es una fecha ' \
                    'futura.\n\n¿Estás seguro de usar esta fecha?'
                    if not self.unogui.createQuestion('Factura Libre', message):
                        self.dialog.getControl('fecha2').setFocus()
                        return False
        return True

    def cmdEliminarProducto(self):
        grid = self.dialog.getControl('gridDetalle')
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        if row < 0:
            message = 'Selecciona el producto o servicio a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        if self.dm.chkDescuento.State:
            descuento = self.dm.descuento.Value
        else:
            descuento = 0
        productos = self.db_detalle.delete_product(grid_dm.getCellData(7, row))
        if not productos:
            self.dm.cmdEliminarProducto.Enabled = False
        self.unogui.gridAddRows(self.dm.gridDetalle, productos)
        self.__mostrar_totales()
        enabled = True
        if len(productos) <= 1:
            enabled = False
        self.dm.cmdArriba.Enabled = enabled
        self.dm.cmdAbajo.Enabled = enabled
        return

    def cmdGenerarCfdi(self):
        try:
            self.prefactura = False
            if self._validar_facturar():
                id_cfd = self.__guardar_datos()
                self.__generar_xml(id_cfd)
                self.__nueva_factura()
                if not self.__enviar_timbrar(id_cfd):
                    return
                path_pdf = self.__create_pdf(id_cfd)
                path_xml, data = self.__copiar_xml(id_cfd, path_pdf)
                self.__subir_ftp(data)
                if self.enviar_correo:
                    self.__enviar_correo(path_xml, path_pdf, id_cfd)
        except:
            log.error('CFDI', exc_info=True)
        return

    def _validar_facturar(self):
        if not self.dm.lblFolio.Label:
            message = 'Selecciona un rango de folios'
            self.unogui.createMsgBox({'Message': message})
            self.cmdMostrarFolios()
            return False
        if not self.dm.txtReceptor.Tag:
            message = 'Selecciona un receptor (cliente)'
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtReceptor').setFocus()
            return False
        grid = self.dialog.getControl('gridDetalle')
        grid_dm = grid.Model.GridDataModel
        if not grid_dm.RowCount:
            message = 'Agrega un producto o servicio para facturar'
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('descripcion').setFocus()
            return False

        #~ if not self.prefactura:
            #~ txtControl = self.dialog.getControl('metodoDePago')
            #~ if self.unogui.validate(txtControl,'Vacio'):
                #~ message='El campo Método de Pago no puede estar vacío'
                #~ self.unogui.createMsgBox({'Message':message})
                #~ txtControl.setFocus()
                #~ return False
        pm = self.lst_payment_method.getSelectedItems()
        if not pm:
            self.lst_payment_method.setFocus()
            msg = 'El campo Método de Pago no puede estar vacío'
            util.msgbox(msg, TYPE_MSG['ERROR'])
            return False

        if self.db_detalle.impuestos[0]['total'] < 0:
            message = 'Valor incorrecto, puedes tener precios negativos, ' \
                        'pero el TOTAL debe ser mayor o igual a cero'
            self.unogui.createMsgBox({'Message':message})
            return False

        lstControl = self.dialog.getControl('moneda')
        currency = lstControl.SelectedItem.lower()
        tipocambio = self.dialog.getControl('TipoCambio')
        if lstControl.SelectedItemPos == 0:
            if self.dm.TipoCambio.Value > 1:
                message = 'Valor incorrecto, el campo moneda es PESO pero ' \
                            'el tipo de cambio es mayor 1'
                self.unogui.createMsgBox({'Message':message})
                tipocambio.setFocus()
                return False
        elif lstControl.SelectedItemPos > 0:
            if currency in CURRENCIES:
                currency = CURRENCIES[currency]
            if self.dm.TipoCambio.Value == 1 and currency != CURRENCY:
                message = 'Valor incorrecto, el campo moneda no es PESO ' \
                    'pero el tipo de cambio es 1'
                self.unogui.createMsgBox({'Message':message})
                tipocambio.setFocus()
                return False

        if self.dm.chkDescuento.State:
            txtControl = self.dialog.getControl('motivoDescuento')
            if self.unogui.validate(txtControl, 'Vacio'):
                message = 'El campo Motivo de Descuento no puede estar vacío'
                self.unogui.createMsgBox({'Message':message})
                txtControl.setFocus()
                return False
            if self.dm.descuento.Value == 0:
                message = 'Valor incorrecto, el DESCUENTO tiene que ser mayor a cero'
                self.unogui.createMsgBox({'Message': message})
                self.dialog.getControl('descuento').setFocus()
                return False

        if self.dialog.getControl('cmdRegimenFiscal').isVisible():
            if not self.regimenfiscal:
                message = 'Selecciona el regimen fiscal para esta factura, ' \
                            'debes de seleccionar el regimen que cubra los ' \
                            'conceptos facturados en este CFDI'
                self.unogui.createMsgBox({'Message': message})
                return False

        if not self.prefactura:
            if not self._validate_inventario(grid_dm):
                return False

        cuenta = self.dialog.getControl('NumCtaPago')
        self.unogui.validate(cuenta, 'Vacio')
        if len(cuenta.Text) > 0 and len(cuenta.Text) < 4:
            cuenta.setFocus()
            message = 'La cuenta de pago debe ser de 4 digitos o más'
            self.unogui.createMsgBox({'Message': message})
            return False

        if self.dm.formaDePago.Text != self.globales['FORMA_PAGO']:
            msg = 'La forma de pago es:\n\n{}\n\n¿Estas seguro de usarla?'
            msg = msg.format(self.dm.formaDePago.Text)
            if not self.unogui.createQuestion('Factura Libre', msg):
                return False

        grid_dm = self.dm.gridCampos.GridDataModel
        fil = grid_dm.RowCount
        message = ''
        if fil:
            message = '\n\nTienes campos personalizados, no olvides capturarlos.\n'
        if self.prefactura:
            return True
        else:
            message = 'Todos los datos son correctos, ¿deseas generar este CFDI?%s' % message
        if self.unogui.createQuestion('Factura Libre', message):
            return True
        else:
            return False

    def _validate_inventario(self, grid_dm):
        if self.opciones[2]:
            return True
        for r in range(grid_dm.RowCount):
            clave = grid_dm.getCellData(1, r)
            des = grid_dm.getCellData(3, r)
            cant = grid_dm.getCellData(4, r)
            data = self.db.select(('productos',),
                                    ('inventario', 'existencia'),
                                    "noIdentificacion='%s'" % clave)
            if not data:
                message = 'El siguiente producto ya no esta en el inventario:' \
                    '\n\n(%s) %s\n\n¿Estás seguro de facturarlo?' % (clave, des)
                if not self.unogui.createQuestion('Factura Libre', message):
                    return False
            else:
                if data[0][0]:
                    if data[0][1] < cant:
                        message = 'No hay suficiente existencia (%s) del ' \
                                    'producto:\n\n%s\n\n' % (data[0][1], des)
                        self.unogui.createMsgBox({'Message': message})
                        return False
        return True

    def __guardar_datos(self):
        folios = self.dialog.getControl('gridFolios')
        folios_dm = folios.Model.GridDataModel
        row = folios.CurrentRow
        if row == -1:
            row = 0
        id_folio = folios_dm.getCellData(0, row)
        serie = folios_dm.getCellData(1, row)
        folio_actual = self.db.select(
            ('cfdfacturas',),
            ('ifnull(max(folio)+1,1)',),
            "serie='%s'" % serie)[0][0]
        if int(folios_dm.getCellData(2, row)) > folio_actual:
            folio_actual = int(folios_dm.getCellData(2, row))
        if self.dm.optIngreso.State:
            tipo_comprobante = 'ingreso'
        elif self.dm.optEgreso.State:
            tipo_comprobante = 'egreso'
        elif self.dm.optTraslado.State:
            tipo_comprobante = 'traslado'
        lugar_expedicion = self.db.select_field('expedidoen', 'municipio')
        if lugar_expedicion:
            lugar_expedicion += ', %s' % self.db.select_field('expedidoen', 'estado')
        else:
            lugar_expedicion = '%s, %s' % (self.db.select_field('emisor', 'municipio'), self.db.select_field('emisor', 'estado'))
        self.estatus = 'Por pagar'
        if self.dm.optEstatus2.State:
            self.estatus = 'Pagada'

        pm = self.lst_payment_method.getSelectedItems()
        payment_methods = ','.join(
            tuple({k: v for k, v in PAYMENT_METHODS.items() if k in pm}.values()))

        cfd = {}
        cfd['version'] = self.db.select_field('sat', 'xmlversion')
        cfd['serie'] = serie
        cfd['noAprobacion'] = ''
        cfd['anoAprobacion'] = ''
        cfd['folio'] = folio_actual
        #~ cfd['fecha'] = str(self.util.getDateFromControl(self.dm.txtFecha.Date, True))
        cfd['fecha'] = self.util.now(True, 3)
        cfd['fecha_timbrado'] = self.util.now(True)
        cfd['formaDePago'] = self.dm.formaDePago.Text
        cfd['noCertificado'] = self.db.select_field('certificado', 'noCertificado')
        cfd['certificado'] = self.db.select_field('certificado', 'certificado')
        cfd['condicionesDePago'] = self.dm.condicionesDePago.Text
        cfd['subTotal'] = self.db_detalle.impuestos[0]['subtotal']
        cfd['descuento'] = self.db_detalle.impuestos[0]['descuento']
        cfd['motivoDescuento'] = ''
        if self.dm.chkDescuento.State:
            cfd['motivoDescuento'] = self.dm.motivoDescuento.Text
        cfd['TipoCambio'] = self.dm.TipoCambio.Value
        cfd['Moneda'] = self.dialog.getControl('moneda').SelectedItem
        cfd['total'] = self.db_detalle.impuestos[0]['total']
        self.total_mn = round(cfd['TipoCambio'] * cfd['total'], self.opciones[0])
        cfd['tipoDeComprobante'] = tipo_comprobante
        cfd['metodoDePago'] = payment_methods
        cfd['LugarExpedicion'] = lugar_expedicion
        cfd['NumCtaPago'] = self.dm.NumCtaPago.Text
        if not self.db_detalle.impuestos[0]['totalRetenciones'] is None:
            cfd['totalImpuestosRetenidos'] = self.db_detalle.impuestos[0]['totalRetenciones']
        if not self.db_detalle.impuestos[0]['totalTraslados'] is None:
            cfd['totalImpuestosTrasladados'] = self.db_detalle.impuestos[0]['totalTraslados']
        cfd['id_cliente'] = self.dm.txtReceptor.Tag
        cfd['notas'] = self.notas
        cfd['estatus'] = 'Guardada'
        cfd['regimen'] = self.regimenfiscal
        cfd['donativo'] = self.donativo
        cfd['id_folio'] = id_folio
        id_cfd = self.db.insertrow('cfdfacturas', cfd)
        self.db_detalle.update_idcfd(id_cfd)

        productos, taxes = self.db_detalle.get_products()
        fields = (
            'id_cfd',
            'id_producto',
            'categoria',
            'cantidad',
            'unidad',
            'noIdentificacion',
            'descripcion',
            'valorUnitario',
            'importe',
            'numero',
            'fecha',
            'aduana',
            'CuentaPredial',
            'version',
            'alumno',
            'curp',
            'nivel',
            'autorizacion')
        self.db.executemany('cfddetalle', fields, productos)
        fields = ('id_cfd', 'id_producto', 'nombre','tasa', 'tipo')
        self.db.executemany('detalleimpuestos', fields, taxes)

        productos = self.db_detalle.get_products_update()
        for product in productos:
            self.db.update(
                'productos',
                {'existencia': 'existencia-%s' % product[1]},
                'id=%s' % product[0],
                True)

        for i in range(1, len(self.db_detalle.impuestos)):
            impuesto = self.db_detalle.impuestos[i]
            del impuesto['titulo']
            impuesto['id_cfd'] = id_cfd
            self.db.insertrow('cfdimpuestos', impuesto)

        if self.complement:
            values = {
                'id_cfdi': id_cfd,
                'code_name': 'ine',
                'nodes': util.dumps(self.complement),
            }
            self.db.insertrow('cfdi_complements', values)

        grid_dm = self.dm.gridCampos.GridDataModel
        fil = grid_dm.RowCount
        if fil:
            data = []
            for f in range(fil):
                if grid_dm.getCellData(2, f):
                    row = (id_cfd, grid_dm.getCellData(3, f), grid_dm.getCellData(2, f))
                    data.append(row)
            fields = ('id_cfd', 'campo', 'valor')
            self.db.executemany('cfdpersonalizados', fields, tuple(data))
        return id_cfd

    def __generar_xml(self, id_cfd):
        cfd = CFDXML(self, id_cfd)
        cfd.regimenfiscal = self.regimenfiscal
        #~ cfd.sat_ine = self.complement
        xml = cfd.generate_xml()
        self.db.update(
            'cfdfacturas',
            {'xml': xml, 'estatus': 'Generada'},
            'id=%s' % id_cfd)
        return

    def __enviar_timbrar(self, id_cfd):
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, el CFDI ya ' \
                'ha sido generado y guardado en la base de datos, pero no se ' \
                'podrá timbrar hasta volver a tener conexión a internet, se ' \
                'recomienda esperar hasta resolver este problema'
            self.unogui.createMsgBox({'Message': message})
            return False
        message = 'El documento se ha generado correctamente, presiona ' \
            'Aceptar para enviar a timbrar con el PAC'
        self.unogui.createMsgBox({'Message': message})
        rfc = self.db.select_field('certificado', 'rfc')

        data = self.db.select(('cfdfacturas',), ('xml', 'fecha'), 'id=%s' % id_cfd)[0]
        self.db.update('cfdfacturas', {'estatus': 'Enviada'}, 'id=%s' % id_cfd)
        id_timbrado = self.util.get_epoch(data[1])
        #~ ok, data = self.util.timbrar(rfc, data[0], id_timbrado, self.new_server)
        ok, data = util.timbra_xml(rfc, data[0], id_timbrado, self.new_server, not self.new_server)
        if ok:
            t = util.GetTimbres(self.rfc_emisor, self.dm.lblFoliosPac, self.new_server, not self.new_server)
            t.start()
            self.db.update(
                'cfdfacturas',
                {'xml': data['xml'],
                    'uuid': data['uuid'],
                    'fecha_timbrado': data['fecha'],
                    'estatus': self.estatus},
                'id=%s' % id_cfd)
            if self.dm.optEstatus1.State:
                self._saldo(self.dm.txtReceptor.Tag, self.total_mn, True)
            self.dm.txtReceptor.Tag = ''
            self.total_mn = 0
            self.dm.optEstatus1.State = True

            #~ message = 'El documento se timbro correctamente y se ha guardado' \
                #~ ' en la base de datos'
            #~ self.unogui.createMsgBox({'Message': message})
            return True
        else:
            self.unogui.createMsgBox({'Message': data})
            return False

    def __create_pdf(self, id_cfd):
        pdf = CFDPDF(self)
        pdf.generate_pdf((id_cfd,))
        return pdf.path_pdf

    def __copiar_xml(self, id_cfd, path_pdf):
        info = self.util.getInfoPath(path_pdf)
        rutas = self.db.select(('rutasespejo',), ('ruta',))
        #~ name_xml = "serie || substr('000000' || folio, -6, 6) || '_' || rfc || '.xml'"
        #~ where = 'cfdfacturas.id_cliente=receptores.id AND cfdfacturas.id=%s' % id_cfd
        data = self.db.select(
            ('cfdfacturas',),
            ("strftime('%Y',fecha_timbrado)", "strftime('%m',fecha_timbrado)", 'xml'),
            'id=%s' % id_cfd)[0]
        path_xml = ''
        if rutas:
            #~ rutas = [r[0] for r in rutas]
            data = {
                'year': data[0],
                'month': data[1],
                'xml': data[2],
                'name': '%s.xml' % info[2]
            }
            #~ path_xml = self.util.copy_xml(data, rutas, path_pdf)
            path_xml = util.copy_xml(data, rutas, path_pdf)
        #~ else:
            #~ path_xml = self.util.getPathTemp(name)
            #~ self.util.save_file(path_xml, data[2])
        return path_xml, data

    def __subir_ftp(self, data):
        ftp = self.db.select(
            ('opciones',), ('ftpservidor', 'ftpusuario', 'ftpcontrasena'))[0]
        if ftp[0] and ftp[1] and ftp[2]:
            self.util.send_ftp(ftp, data)
        return

    def __enviar_correo(self, path_xml, path_pdf, id_cfd):
        if self.enviar_correo == 1:
            message = '¿Deseas envíar, al correo del receptor, esta factura?' \
                '\n\nSI = Usa el cliente predeterminado\nNO = Envía el ' \
                'correo directamente\nCANCELAR = Salir sin enviar'
            enviar = self.unogui.createMsgBox(
                {'Type': 'querybox', 'Buttons': 4, 'Message': message})
            if not enviar:
                return
        else:
            enviar = self.enviar_correo
        config_server = self.db.select(('correo',))
        if config_server:
            config_server = config_server[0]
        if enviar == 3 and not config_server:
            message = 'Se requiere configurar primero los datos del servidor ' \
                'para enviar correo directamente\n\nNo se enviará ninguna factura'
            self.unogui.createMsgBox({'Message': message, 'Type': 'warningbox'})
            return
        elif enviar == 3:
            server = (config_server[1] and config_server[2] and
                        config_server[3] and config_server[4])
            if not server:
                message = 'La configuracion del servidor de correo esta ' \
                    'incompleta. No podras enviar correos directamente hasta ' \
                    'tener completa esta configuración'
                self.unogui.createMsgBox({'Message': message, 'Type': 'warningbox'})
                return

        data = self.db.select(
            ('correos',),
            ('correo',) ,
            'id_cliente=(SELECT id_cliente FROM cfdfacturas WHERE id=%s)' % id_cfd)
        to = [element[0] for element in data]
        if enviar == 3 and not to:
            message = 'El cliente no tiene configurada una cuenta de correo, ' \
                'no se enviará nada.'
            self.unogui.createMsgBox({'Message': message, 'Type': 'warningbox'})
            return

        if not path_xml:
            path_xml = path_pdf.replace('.pdf', '.xml')
            xml = self.db.select(('cfdfacturas',), ('xml', ), 'id=%s' % id_cfd)[0][0]
            self.util.save_file(path_xml, xml.encode('utf-8'))
        #~ res = self.util.enviar_correo((enviar, (path_xml, path_pdf), to, config_server))
        #~ path_xml, path_pdf = self._get_paths_files(id_cfdi, paths)
        if config_server:
            mail_server = {}
            mail_server['server'] = config_server[1]
            mail_server['port'] = config_server[2]
            mail_server['user'] = config_server[3]
            mail_server['pass'] = config_server[4]
            mail_server['copy'] = config_server[5]
            mail_server['subject'] = config_server[6]
            mail_server['body'] = config_server[7]
            mail_server['ssl'] = config_server[8]
        info = {
            'files': (path_xml, path_pdf),
            'mail_server': mail_server,
            'receivers': to
        }
        try:
            if enviar == SEND_MAIL['USE_CLIENT']:
                send = util.send_mail_client(info)
            elif enviar == SEND_MAIL['SMTP']:
                send, msg = util.send_mail(info)
                if send:
                    msg = 'Correo enviado al cliente correctamente'
                    util.msgbox(msg)
                else:
                    log.error(msg)
        except:
            log.error('Mail: ', exc_info=True)
        return

    def __nueva_factura(self):
        if not self.prefactura:
            folios = self.dialog.getControl('gridFolios')
            folios_dm = folios.Model.GridDataModel
            row = folios.CurrentRow
            if row == -1:
                row = 0
            serie = folios_dm.getCellData(1, row)
            folio_actual = self.db.select(
                ('cfdfacturas',),
                ('ifnull(max(folio)+1,1)',),
                "serie='%s'" % serie)[0][0]
            folios_dm.updateCellData(3, row, folio_actual)
            if serie:
                self.dm.lblFolio.Label = '%s-%s' % (serie,folio_actual)
            else:
                self.dm.lblFolio.Label = folio_actual
            self.prefactura = False

        grid_dm = self.dm.gridCampos.GridDataModel
        fil = grid_dm.RowCount
        if fil:
            for f in range(fil):
                grid_dm.updateCellData(2, f, '')

        #~ self.dm.txtReceptor.Tag = ''
        self.dm.txtReceptor.Text = ''
        self.dm.NumCtaPago.Text = ''
        self.dm.motivoDescuento.Text = ''
        self.notas = ''
        self.dm.chkDescuento.State = 0
        self.dm.motivoDescuento.Enabled = False
        self.dm.descuento.Enabled = False
        self.dm.descuento.Value = 0
        self.dm.lst_payment_method.SelectedItems = ()
        self.dm.condicionesDePago.Text = ''
        self.dm.cmdDetalleReceptor.Enabled = False
        self.unogui.gridAddRows(self.dm.gridDetalle, None)

        self.producto = None
        self.dm.unidad.Text = ''
        self.dm.noIdentificacion.Text = ''
        self.dm.descripcion.Text = ''
        self.dm.valorUnitario.Value = 0
        self.dm.cantidad.Value = 1
        self.dm.cmdAgregarProducto.Enabled = False
        self.__actualizar_importe()

        self.db_detalle.delete_all()
        self.__mostrar_totales()
        return

    def cmdNotas(self):
        self.value = ''
        message = 'Edición de notas'
        input_box = inputbox2.Dlg(self, (message, self.notas))
        res = input_box.execute()
        if res:
            self.notas = self.value
        return

    def cmdCamposPersonalizados(self):
        dlg = campos.Dlg(self, ('', ''))
        dlg.execute()
        return

    def gridCampos_DobleClick(self, grid):
        grid_dm = grid.Model.GridDataModel
        col = 2
        fil = grid.CurrentRow
        message = 'Introduce el nuevo valor\nValor Actual: %s' % grid_dm.getCellData(col, fil)
        self.value = ''
        input_box = inputbox.Dlg(self, (message, False))
        res = input_box.execute()
        if res:
            grid_dm.updateCellData(col, fil, self.value)
        return

    def notas_focusLost(self, source):
        source.setVisible(False)
        self.dm.gridDetalle.Enabled = True
        self.dm.gridTotales.Enabled = True
        self.dm.cmdCamposPersonalizados.Enabled = True
        self.dialog.getControl('cmdEliminarProducto').setVisible(True)
        self.dialog.getControl('chkDescuento').setVisible(True)
        self.dialog.getControl('motivoDescuento').setVisible(True)
        return

    def txtReceptor_focusLost(self, source):
        self.dialog.getControl('gridReceptores').setVisible(False)
        return

    def descripcion_focusLost(self, source):
        self.dialog.getControl('gridProductos').setVisible(False)
        return

    def cmdRegimenFiscal(self):
        regimenes = self.dialog.getControl('lstRegimenes')
        self.dialog.getControl('gridTotales').setVisible(regimenes.isVisible())
        self.dialog.getControl('chkDescuento').setVisible(regimenes.isVisible())
        self.dialog.getControl('motivoDescuento').setVisible(regimenes.isVisible())
        self.dm.cmdCamposPersonalizados.Enabled = regimenes.isVisible()
        self.dm.cmdNotas.Enabled = regimenes.isVisible()
        regimenes.setVisible(not regimenes.isVisible())
        if regimenes.isVisible():
            regimenes.setFocus()
        return

    def lstRegimenes(self, source):
        self.regimenfiscal = source.SelectedItem
        self.cmdRegimenFiscal()
        return

    def cmdPrefacturar(self):
        try:
            self.prefactura = True
            delete = True
            if self._validar_facturar():
                message = 'Todos los datos son correctos ¿Que deseas hacer?' \
                    '\n\nPresiona SI para guardar y generar\nPresiona NO ' \
                    'solo para generar'
                if self.unogui.createQuestion('Factura Libre', message):
                    delete = False
                id_cfd = self.__guardar_predatos('PRE-FACTURA')
                pdf = CFDPDF(self)
                pdf.generate_prepdf(id_cfd)
                if delete:
                    self.db.delete('prefacturas', 'id=%s' % id_cfd)
                    self.db.delete('predetalle', 'id_cfd=%s' % id_cfd)
                    self.db.delete('predetalleimpuestos', 'id_cfd=%s' % id_cfd)
                    self.db.delete('preimpuestos', 'id_cfd=%s' % id_cfd)
                    self.db.delete('prepersonalizados', 'id_cfd=%s' % id_cfd)
                self.__nueva_factura()
        except:
            log.error('PRE', exc_info=True)
        return

    def __guardar_predatos(self, serie):
        folio_actual = self.db.select(('prefacturas',),
                                ('ifnull(max(folio)+1,1)',),
                                "serie='%s'" % serie)[0][0]
        if self.dm.optIngreso.State:
            tipo_comprobante = 'ingreso'
        elif self.dm.optEgreso.State:
            tipo_comprobante = 'egreso'
        elif self.dm.optTraslado.State:
            tipo_comprobante = 'traslado'
        lugar_expedicion = self.db.select_field('expedidoen', 'municipio')
        if lugar_expedicion:
            lugar_expedicion += ', %s' % self.db.select_field('expedidoen', 'estado')
        else:
            lugar_expedicion = '%s, %s' % (self.db.select_field('emisor', 'municipio'), self.db.select_field('emisor', 'estado'))
        estatus = 1
        cfd = {}
        cfd['version'] = self.db.select_field('sat', 'xmlversion')
        cfd['serie'] = serie
        cfd['folio'] = folio_actual
        cfd['fecha'] = str(self.util.getDateFromControl(
            self.dm.txtFecha.Date, True))
        cfd['formaDePago'] = self.dm.formaDePago.Text
        #cfd['noCertificado'] = self.db.select_field('certificado', 'noCertificado')
        cfd['condicionesDePago'] = self.dm.condicionesDePago.Text
        cfd['subTotal'] = self.db_detalle.impuestos[0]['subtotal']
        cfd['descuento'] = self.db_detalle.impuestos[0]['descuento']
        cfd['motivoDescuento'] = self.dm.motivoDescuento.Text
        cfd['TipoCambio'] = self.dm.TipoCambio.Value
        cfd['Moneda'] = self.dialog.getControl('moneda').SelectedItem
        cfd['total'] = self.db_detalle.impuestos[0]['total']
        cfd['tipoDeComprobante'] = tipo_comprobante
        #~ cfd['metodoDePago'] =
        cfd['LugarExpedicion'] = lugar_expedicion
        cfd['NumCtaPago'] = self.dm.NumCtaPago.Text
        if not self.db_detalle.impuestos[0]['totalRetenciones'] is None:
            cfd['totalImpuestosRetenidos'] = self.db_detalle.impuestos[0]['totalRetenciones']
        if not self.db_detalle.impuestos[0]['totalTraslados'] is None:
            cfd['totalImpuestosTrasladados'] = self.db_detalle.impuestos[0]['totalTraslados']
        cfd['id_cliente'] = self.dm.txtReceptor.Tag
        cfd['notas'] = self.notas
        cfd['estatus'] = 'PRE'
        cfd['regimen'] = self.regimenfiscal

        #~ Gracias a http://fipasoft.mx/
        folios = self.dialog.getControl('gridFolios')
        folios_dm = folios.Model.GridDataModel
        row = folios.CurrentRow
        if row == -1:
            row = 0
        id_folio = folios_dm.getCellData(0, row)
        cfd['id_folio'] = id_folio
        #~
        id_cfd = self.db.insertrow('prefacturas', cfd)
        self.db_detalle.update_idcfd(id_cfd)

        productos, taxes = self.db_detalle.get_products()
        fields = (
            'id_cfd',
            'id_producto',
            'categoria',
            'cantidad',
            'unidad',
            'noIdentificacion',
            'descripcion',
            'valorUnitario',
            'importe',
            'numero',
            'fecha',
            'aduana',
            'CuentaPredial',
            'version',
            'alumno',
            'curp',
            'nivel',
            'autorizacion')
        self.db.executemany('predetalle', fields, productos)
        fields = ('id_cfd', 'id_producto', 'nombre','tasa', 'tipo')
        self.db.executemany('predetalleimpuestos', fields, taxes)

        for i in range(1, len(self.db_detalle.impuestos)):
            impuesto = self.db_detalle.impuestos[i]
            if 'titulo' in impuesto:
                del impuesto['titulo']
            impuesto['id_cfd'] = id_cfd
            self.db.insertrow('preimpuestos', impuesto)

        grid_dm = self.dm.gridCampos.GridDataModel
        fil = grid_dm.RowCount
        if fil:
            data = []
            for f in range(fil):
                if grid_dm.getCellData(2, f):
                    row = (id_cfd, grid_dm.getCellData(3, f), grid_dm.getCellData(2, f))
                    data.append(row)
            fields = ('id_cfd', 'campo', 'valor')
            self.db.executemany('prepersonalizados', fields, tuple(data))
        return id_cfd

    @util.catch_exception
    def gridDetalle_DobleClick(self, grid):
        #~ try:
        grid_dm = grid.Model.GridDataModel
        col = grid.CurrentColumn
        fil = grid.CurrentRow
        self.value = ''
        row_id = grid_dm.getCellData(7, fil)
        clave = grid_dm.getCellData(1, fil)
        if col == 2:
            msg = 'Introduce la nueva unidad.'
            input_box = inputbox.Dlg(self, (msg, False))
            res = input_box.execute()
            if res:
                if self.value:
                    self.db_detalle.update_unidad(row_id, self.value)
                    grid_dm.updateCellData(col, fil, self.value)
        elif col == 3:
            message = 'Introduce la nueva descripción.'
            input_box = inputbox2.Dlg(
                self, (message, grid_dm.getCellData(col, fil)))
            res = input_box.execute()
            if res:
                if self.value:
                    self.db_detalle.update_description(row_id, self.value)
                    grid_dm.updateCellData(col, fil, self.value)
        elif col == 4:
            message = 'Introduce la nueva cantidad.'
            input_box = inputbox.Dlg(self, (message, False))
            res = input_box.execute()
            if res:
                if self._validate_new_cant(clave):
                    new_cant = float(self.value)
                    precio = grid_dm.getCellData(5, fil)
                    if not isinstance(precio, float):
                        precio = float(precio.replace(',', ''))
                    importe = round(new_cant * precio, self.opciones[0])
                    data = self.db_detalle.update_value(row_id, new_cant, importe, False)
                    self.__show_data(data)
                    self.__mostrar_totales()
                    self.dm.cantidad.Value = 1
                    self.dm.cmdEliminarProducto.Enabled = True
        elif col == 5:
            if not self.opciones[5]:
                return
            message = 'Introduce el nuevo precio unitario.'
            input_box = inputbox.Dlg(self, (message, False))
            res = input_box.execute()
            if res:
                if self._validate_new_precio():
                    new_value = float(self.value)
                    cant = grid_dm.getCellData(4, fil)
                    if not isinstance(cant, float):
                        cant = float(cant.replace(',', ''))
                    importe = round(cant * new_value, self.opciones[0])
                    data = self.db_detalle.update_value(row_id, new_value, importe)
                    self.__show_data(data)
                    self.__mostrar_totales()
                    self.dm.cantidad.Value = 1
                    self.dm.cmdEliminarProducto.Enabled = True
        #~ except:
            #~ print(traceback.format_exc())
        return

    def _validate_new_precio(self):
        try:
            self.value = self.value.replace(',', '')
            new_value = float(self.value)
        except ValueError:
            message = 'El dato introducido no es un valor'
            self.unogui.createMsgBox({'Message': message})
            return False
        if not new_value:
            message = 'El nuevo valor unitario es cero \n\n¿Estás seguro de usar este valor?'
            if not self.unogui.createQuestion('Factura Libre', message):
                return False
        if new_value < 0:
            message = 'El nuevo valor unitario es negativo \n\n¿Estás seguro de usar este valor?'
            if not self.unogui.createQuestion('Factura Libre', message):
                return False
        return True

    def _validate_new_cant(self, clave):
        try:
            self.value = self.value.replace(',', '')
            new_cant = float(self.value)
        except ValueError:
            message = 'El dato introducido no es un número'
            self.unogui.createMsgBox({'Message': message})
            return False
        if not new_cant:
            message = 'La cantidad no puede ser cero'
            self.unogui.createMsgBox({'Message': message})
            return False
        data = self.db.select(('productos',),
                                ('inventario','existencia'),
                                "noIdentificacion='%s'" % clave)
        if not data:
            message = 'Este producto ya no esta en el inventario.\n\n' \
                        '¿Estás seguro de refacturarlo?'
            if self.unogui.createQuestion('Factura Libre', message):
                return True
            else:
                return False
        if data[0][0] and not self.opciones[2]:
            if data[0][1] < new_cant:
                message = 'No hay suficiente existencia de este producto.\n' \
                            '\nExistencia = %s' % data[0][1]
                self.unogui.createMsgBox({'Message': message})
                return False
        return True

    def cmdRefacturar(self):
        dialog_refacturar = refacturar.Dlg(self.caller)
        id_refacturar = dialog_refacturar.execute()
        if not id_refacturar:
            return
        #~ self.db_detalle.delete_all()
        if dialog_refacturar.prefactura:
            table = 'prefacturas'
            detalle = 'predetalle'
            t_impuestos = 'predetalleimpuestos'
            person = 'prepersonalizados'
        else:
            table = 'cfdfacturas'
            detalle = 'cfddetalle'
            t_impuestos = 'detalleimpuestos'
            person = 'cfdpersonalizados'
        fields = (
            'id_cliente',
            'tipoDeComprobante',
            'metodoDePago',
            'NumCtaPago',
            'condicionesDePago',
            'moneda',
            'TipoCambio',
            'motivoDescuento',
            'descuento',
            'formaDePago',
            'notas')
        data = self.db.select((table,), fields,'id=%s' % id_refacturar )[0]
        opt = {
            'ingreso': 'optIngreso',
            'egreso': 'optEgreso',
            'traslado': 'optTraslado'
        }
        if getattr(self.dm, opt[data[1]]).Enabled:
            self.dialog.getControl(opt[data[1]]).setState(True)
        #~ self.dm.metodoDePago.Text = data[2]
        self.dm.NumCtaPago.Text = data[3]
        self.dm.condicionesDePago.Text = data[4]
        self.dialog.getControl('moneda').selectItem(data[5], True)
        self.dm.TipoCambio.Value = data[6]
        self.dm.motivoDescuento.Text = data[7]
        descuento = data[8]
        if descuento:
            self.dm.motivoDescuento.Enabled = True
            self.dm.descuento.Enabled = True
            self.dm.descuento.Value = descuento
        self.dm.formaDePago.Text = data[9]
        self.notas = data[10]

        self.dm.txtReceptor.Text = data[0]
        event = self.util.getKeyEvent()
        event.KeyCode = KEY_RETURN
        event.Source = self.dm.txtReceptor
        self.txtReceptor_keyReleased(event)
        fields = (
            'id_producto',
            'categoria',
            'cantidad',
            'unidad',
            'noIdentificacion',
            'descripcion',
            'valorUnitario',
            'importe',
            'numero',
            'fecha',
            'aduana',
            'CuentaPredial')
        data = self.db.select((detalle,), fields, 'id_cfd=%s' % id_refacturar )
        pos = 0
        for product in data:
            pos += 1
            producto = {}
            producto['id'] = product[0]
            producto['categoria'] = product[1]
            producto['cantidad'] = product[2]
            producto['unidad'] = product[3]
            producto['noIdentificacion'] = product[4]
            producto['descripcion'] = product[5]
            producto['valorUnitario'] = product[6]
            producto['importe'] = round(producto['cantidad'] * producto['valorUnitario'], self.opciones[0])
            producto['numero'] = product[8]
            if producto['numero']:
                producto['fecha'] = product[9]
            producto['aduana'] = product[10]
            producto['CuentaPredial'] = product[11]
            inventario = self.db.select(('productos',),
                                        ('inventario',),
                                        "noIdentificacion='%s'" % product[4])
            producto['inventario'] = 0
            producto['pos'] = pos
            if inventario:
                producto['inventario'] = inventario[0][0]
            where = 'id_cfd=%s AND id_producto=%s' % (id_refacturar, producto['id'])
            impuestos = self.db.select(
                (t_impuestos,), ('nombre', 'tasa', 'tipo'), where)
            productos = self.db_detalle.insert_product(producto, impuestos, descuento)
        #~ self.unogui.gridAddRows(self.dm.gridDetalle, productos)
        self.__show_data(productos)
        self.__mostrar_totales()
        self.dm.cmdEliminarProducto.Enabled = True
        fields = ('campo', 'valor')
        data = self.db.select((person,), fields, 'id_cfd=%s' % id_refacturar )
        dic = {}
        for r in data:
            dic[r[0]] = r[1]
        grid_dm = self.dm.gridCampos.GridDataModel
        fil = grid_dm.RowCount
        for f in range(fil):
            v = grid_dm.getCellData(3, f).lower()
            if v in dic:
                grid_dm.updateCellData(2, f, dic[v])
        #~ self._validate_inventario(self.dm.gridDetalle.GridDataModel)
        return

    def __get_detalle_cliente(self, id_cliente):
        fields = (
                'id',
                'rfc',
                'nombre',
                'calle',
                'noExterior',
                'noInterior',
                'colonia',
                'codigoPostal',
                'municipio',
                'estado',
                'pais',
                'notas',
                'metododepago',
                'cuentadepago',
                'condiciondepago')
        receptor = self.db.select(
                    ('receptores',),
                    fields,
                    'id=%s' % id_cliente)[0]
        self.dm.txtReceptor.Tag = receptor[0]
        self.dm.txtReceptor.Text = receptor[2]
        self.dm.cmdDetalleReceptor.Enabled = True
        message = '(%s) RFC: %s\n%s\n%s %s %s\nCol. %s, C.P. %s\n%s, %s, %s\n\nNotas: %s' % (
                    receptor[0], receptor[1], receptor[2],
                    receptor[3], receptor[4], receptor[5],
                    receptor[6], receptor[7], receptor[8],
                    receptor[9], receptor[10], receptor[11])
        mails = self.db.sql('get_mails', 'id_cliente={}'.format(id_cliente))
        if mails:
            message += '\n\n{}'.format('\n'.join([r[0] for r in mails]))
        if receptor[12]:
            self.dialog.getControl('lst_payment_method').selectItem(receptor[12], True)
        self.dm.NumCtaPago.Text = receptor[13]
        self.dm.condicionesDePago.Text = receptor[14]
        self.dm.cmdDetalleReceptor.Tag = message

        grid = self.dialog.getControl('gridAlumnos')
        grid.deselectAllRows()
        data = self.db.select(
            ('alumnos', 'niveles'),
            ('alumnos.id','alumno', 'curp', 'nivel', 'autorizacion', 'id_cliente'),
            'alumnos.id_nivel=niveles.id AND id_cliente=%s' % id_cliente,
            order='alumno')
        self.unogui.gridAddRows(grid.Model, data)
        return

    def cmdCotizacion(self):
        try:
            self.prefactura = True
            delete = True
            if self._validar_facturar():
                message = 'Todos los datos son correctos ¿Que deseas hacer?' \
                    '\n\nPresiona SI para guardar y generar\nPresiona NO ' \
                    'solo para generar'
                if self.unogui.createQuestion('Factura Libre', message):
                    delete = False
                id_cfd = self.__guardar_predatos('COTIZACION')
                pdf = CFDPDF(self, True)
                pdf.generate_cotizacion(id_cfd, self.enviar_correo)
                if delete:
                    self.db.delete('prefacturas', 'id=%s' % id_cfd)
                    self.db.delete('predetalle', 'id_cfd=%s' % id_cfd)
                    self.db.delete('predetalleimpuestos', 'id_cfd=%s' % id_cfd)
                    self.db.delete('preimpuestos', 'id_cfd=%s' % id_cfd)
                    self.db.delete('prepersonalizados', 'id_cfd=%s' % id_cfd)
                self.__nueva_factura()
        except:
            print(traceback.format_exc())
        return

    def dialog_keyPressed(self, event):
        #~ print(event.KeyCode)
        return

    def dialog_keyReleased(self, event):
        #~ print(event.KeyCode)
        return

    def cmdArriba(self):
        grid = self.dialog.getControl('gridDetalle')
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        if row <= 0: return
        #~ if not row or row[0]==0: return
        #~ row = row[0]
        row_id = grid_dm.getCellData(7, row-1)
        self.db_detalle.update_pos(row_id, row)
        row_id = grid_dm.getCellData(7, row)
        productos = self.db_detalle.update_pos(row_id, row-1)
        self.__show_data(productos)
        grid.setFocus()
        grid.selectRow(row-1)
        return

    def cmdAbajo(self):
        grid = self.dialog.getControl('gridDetalle')
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        if row < 0 or row == grid_dm.RowCount-1: return
        #~ if not row or row[0]==grid_dm.RowCount-1: return
        #~ row = row[0]
        row_id = grid_dm.getCellData(7, row)
        self.db_detalle.update_pos(row_id, row+1)
        row_id = grid_dm.getCellData(7, row+1)
        productos = self.db_detalle.update_pos(row_id, row)
        self.__show_data(productos)
        grid.setFocus()
        grid.selectRow(row+1)
        return

    def cmdAgregarProductos(self):
        try:
            self.new_products = ()
            dlg = add_products.Dlg(self, self.opciones, self.agregar_producto)
            dlg.execute()
            if self.new_products:
                grid = self.dialog.getControl('gridDetalle')
                grid_dm = grid.Model.GridDataModel
                pos = grid_dm.RowCount + 1
                descuento = 0
                if self.dm.chkDescuento.State:
                    descuento = self.dm.descuento.Value
                for p in self.new_products:
                    if self.__add_new_product(p, pos, descuento):
                        pos += 1
                productos = self.db_detalle.get_products_show()
                if productos:
                    self.__show_data(productos)
                    self.__mostrar_totales()
                    self.dm.cantidad.Value = 1
                    self.dm.cmdEliminarProducto.Enabled = True
        except:
            print(traceback.format_exc())
        return

    def __add_new_product(self, data, pos, descuento):
        new_cant = self.__cast('float(%s)' % data[3], 0)
        if not new_cant:
            message = '%s - Cantidad cero' % data[0]
            self.util.debug(message)
            return False
        if isinstance(data[0], float):
            clave = str(int(data[0]))
        else:
            clave = data[0].strip()
        w = "noIdentificacion='%s'" % clave
        product = self.db.select(('productos',), where=w)
        if product:
            product = product[0]
            if self.opciones[5]:
                pu = self.__cast('float(%s)' % data[2], 0)
            else:
                pu = product[5]
            pu = self.__calcular_precio(product[0], pu)
            if product[7] and not self.opciones[2]:
                cant = self.db_detalle.exists_product_cant(product[0])
                if (new_cant + cant) > product[6]:
                    message = '%s - Sin existencia' % data[0]
                    self.util.debug(message)
                    return False
            new = {}
            new['id'] = product[0]
            new['cantidad'] = new_cant
            if not self.agregar_producto:
                productos = self.db_detalle.exists_product(
                    new['id'],
                    new['cantidad'],
                    descuento)
                if productos:
                    return False
            new['categoria'] = product[1]
            new['noIdentificacion'] = product[2]
            new['descripcion'] = product[3]
            new['unidad'] = product[4]
            new['valorUnitario'] = pu
            new['inventario'] = product[7]
            new['CuentaPredial'] = ''
            new['importe'] = round(new['cantidad'] * pu, self.opciones[0])
            new['pos'] = pos
            if data[4].strip() and data[5].strip() and data[6].strip():
                new['aduana'] = data[4].strip()
                new['fecha'] = '%s 00:00:00' % data[5].strip()
                new['numero'] = data[6].strip()
            where = 'productosimpuestos.id_impuesto=impuestos.id AND id_producto=%s' % new['id']
            imp = self.db.select(
                ('impuestos','productosimpuestos'),
                ('nombre','tasa','tipo'),
                where
            )
            productos = self.db_detalle.insert_product(new, imp, descuento)
        return True

    def __cast(self, value, default):
        try:
            return eval(value)
        except:
            return default

    def cmdMostrarAlumnos(self):
        grid = self.dialog.getControl('gridAlumnos')
        grid.deselectAllRows()
        grid_dm = grid.Model.GridDataModel
        if not grid_dm.RowCount:
            data = self.db.select(
                ('alumnos', 'niveles'),
                ('alumnos.id','alumno', 'curp', 'nivel', 'autorizacion',
                    'id_cliente'),
                'alumnos.id_nivel=niveles.id', order='alumno')
            if not data:
                message = 'No hay alumnos dados de alta'
                self.unogui.createMsgBox({'Message': message})
                return
            self.unogui.gridAddRows(grid.Model, data)
        grid.setVisible(not grid.isVisible())
        self.dialog.getControl('gridDetalle').setVisible(not grid.isVisible())
        self.dialog.getControl('gridTotales').setVisible(not grid.isVisible())
        if grid.isVisible():
            grid.setFocus()
        return

    def txtAlumno_keyPressed(self, event):
        if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
            grid = self.dialog.getControl('gridAlumnos')
            grid.setVisible(True)
            self.dm.txtAlumno.Tag = ''
            alumno = event.Source.Text.strip().replace('|','')
            if not alumno:
                grid.setVisible(False)
                self.dialog.getControl('gridDetalle').setVisible(True)
                self.dialog.getControl('gridTotales').setVisible(True)
                return
            where = "alumnos.id_nivel=niveles.id and alumno LIKE '%" + alumno + "%'"
            alumnos = self.db.select(
                ('alumnos', 'niveles'),
                ('alumnos.id','alumno', 'curp', 'nivel', 'autorizacion',
                    'id_cliente'), where, order='alumno')
            self.unogui.gridAddRows(self.dm.gridAlumnos, alumnos)
            self.dialog.getControl('gridDetalle').setVisible(False)
            self.dialog.getControl('gridTotales').setVisible(False)
        return

    def gridAlumnos_focusLost(self, obj):
        self.dialog.getControl('gridDetalle').setVisible(True)
        self.dialog.getControl('gridTotales').setVisible(True)
        return

    def gridAlumnos_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            #~ self.dm.txtAlumno.Tag = grid_dm.getCellData(0, row)
            self.dm.txtAlumno.Text = grid_dm.getCellData(1, row)
            self.alumno['alumno'] = grid_dm.getCellData(1, row)
            self.alumno['curp'] = grid_dm.getCellData(2, row)
            self.alumno['nivel'] = grid_dm.getCellData(3, row)
            self.alumno['autorizacion'] = grid_dm.getCellData(4, row)
            #~ nivel = self.dialog.getControl('lstNivel')
            #~ nivel.selectItem(self.alumno['nivel'], True)
            #~ nivel.Model.Tag = self.alumno['nivel']
            #~ alumno = grid_dm.getCellData(
                #~ 1, row) + '|' + grid_dm.getCellData(
                #~ 2, row) + '|' + grid_dm.getCellData(
                #~ 3, row) + '|' + grid_dm.getCellData(4, row)
            #~ self.dm.alumno.Tag = alumno
            id_cliente = grid_dm.getCellData(5, row)
            receptor = self.db.select(
                ('receptores',), where='id=%s AND activo=1' % id_cliente)
            if receptor:
                receptor = receptor[0]
                self.dm.txtReceptor.Tag = receptor[0]
                self.dm.txtReceptor.Text = receptor[2]
                self.dm.cmdDetalleReceptor.Enabled = True
                message = u'Clave: %s \nRFC: %s \nRazón Social: %s \n ' \
                    '%s %s %s \n Col. %s, %s \n %s, %s, %s \n' % (
                        receptor[0], receptor[1], receptor[2], receptor[3],
                        receptor[4], receptor[5], receptor[6], receptor[12],
                        receptor[9], receptor[10], receptor[11] )
                self.dm.cmdDetalleReceptor.Tag = message
        grid.setVisible(False)
        self.dialog.getControl('gridDetalle').setVisible(True)
        self.dialog.getControl('gridTotales').setVisible(True)
        self.dialog.getControl('txtAlumno').setFocus()
        return

    def _saldo(self, id_cliente, importe, sumar=False):
        if sumar:
            importe *= -1
        self.db.update(
            'receptores',
            {'saldoCliente': 'saldoCliente - ({})'.format(importe)},
            'id=%s' % id_cliente,
            True)
        return

    def cmdFormaPago(self):
        msg = 'Cambiar Forma de Pago\n\n{}'.format(self.dm.formaDePago.Text)
        input_box = inputbox.Dlg(self, (msg, False))
        res = input_box.execute()
        if res:
            new_value = self.value.strip()
            if new_value:
                self.dm.formaDePago.Text = new_value
        return

    @util.catch_exception
    def cmd_complements(self):
        dlg = Complements(self)
        dlg.execute()
        return
