# -*- coding: utf-8 -*-

import logging
import facturalibre.ui.producto as producto
from facturalibre.settings import LOG, KEY, FORMAT, DOUBLE_CLICK, \
    BUTTON_CLICK, TYPE_MSG
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class ProductosAdminEvents(object):

    def __init__(self, dialog, db):
        self.dialog = dialog
        self.db = db
        self._init_vars()

    def _init_vars(self):
        self.currency = FORMAT.format(
            self.db.select_field('opciones', 'decimales'))
        self.dm = self.dialog.getModel()
        self.grid = self.dialog.getControl('gridProductos')
        self.grid_dm = self.dm.gridProductos.GridDataModel
        self.decimals = self.db.select_field('opciones', 'decimales')
        self.filter_product = self.dialog.getControl('txtFiltrarProducto')
        return

    def cmdSalir(self, event):
        self.dialog.endExecute()
        return

    def gridProductos_mouse_pressed(self, event):
        if event.ClickCount == DOUBLE_CLICK:
            self.cmdEditarProducto(None)
        return

    def _info(self):
        rows = self.grid_dm.RowCount
        if rows == 0:
            info = 'Sin registros'
            self.dm.cmdEditarProducto.Enabled = False
            self.dm.cmdEliminarProducto.Enabled = False
            self.dm.txtFiltrarProducto.Enabled = False
        elif rows == 1:
            info = '1 Registro'
        elif rows > 1:
            info = '{} Registros'.format(rows)
        self.dm.lblInfo.Label = info
        return

    def cmdNuevoProducto(self, event):
        dlg = producto.Dlg(self.db)
        id_product = dlg.execute()
        if id_product:
            where = 'productos.id={}'.format(id_product)
            product = self.db.sql('get_products', where)
            data = [(
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                util.currency(r[5], self.decimals),
                r[6]) for r in product]
            util.grid_add_row(self.grid_dm, data[0])
            self.dm.cmdEditarProducto.Enabled = True
            self.dm.cmdEliminarProducto.Enabled = True
            self.dm.txtFiltrarProducto.Enabled = True
            self._info()
        return

    def cmdEditarProducto(self, event):
        row = self.grid.CurrentRow
        if row == -1:
            msg = 'Selecciona el producto o servicio a editar'
            util.msgbox(msg)
            return
        id_product = self.grid_dm.getCellData(0, row)
        dlg = producto.Dlg(self.db, True, id_product)
        id_product = dlg.execute()
        if id_product:
            where = 'productos.id={}'.format(id_product)
            product = self.db.sql('get_products', where)
            data = [(
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                util.currency(r[5], self.decimals),
                r[6]) for r in product]
            self.grid_dm.updateRowData((0, 1, 2, 3, 4, 5, 6), row, data[0])
        return

    def cmdEliminarProducto(self, event):
        row = self.grid.CurrentRow
        if row == -1:
            msg = 'Selecciona el producto o servicio a eliminar'
            util.msgbox(msg)
            return
        msg = '¿Estás seguro de eliminar el siguiente producto?\n\n' \
            'Clave = {}\n' \
            'Descripción = {}\n\n' \
            'ESTA ACCION NO SE PUEDE DESHACER'.format(
                self.grid_dm.getCellData(2, row),
                self.grid_dm.getCellData(3, row))
        if util.question(msg) == BUTTON_CLICK['NO']:
            return

        id_product = self.grid_dm.getCellData(0, row)
        self.db.delete(
            'productosimpuestos', 'id_producto={}'.format(id_product))
        self.db.delete('productos', 'id={}'.format(id_product))
        for i in range(row + 1, self.grid_dm.RowCount):
            self.grid_dm.updateRowHeading(i, i)
        self.grid_dm.removeRow(row)
        self._info()
        return

    def txtFiltrarProducto_key_released(self, event):
        if event.KeyCode == KEY['RETURN']:
            key = event.Source.Text.strip().replace('|', '')
            if not key:
                msg = 'Criterio de busqueda vacio'
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return
            where = "codigobarras='{0}' " \
                "OR noIdentificacion='{0}'".format(key)
            product = self.db.sql('get_products', where)
            if not product:
                self.filter_product.setFocus()
                msg = 'No se encontró un producto o servicio con este código ' \
                    'de barras o clave de identificación: {}'.format(key)
                util.msgbox(msg)
                return
            data = [(
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                util.currency(r[5], self.decimals),
                r[6]) for r in product]
            util.data_to_grid(self.grid_dm, data)
            self.dm.cmdMostrarTodo.Enabled = True
            self._info()
        return

    def txtFiltrarProducto_key_pressed(self, event):
        if event.KeyCode != KEY['RETURN']:
            product = event.Source.Text.strip().replace('|','')
            if not product:
                self.cmdMostrarTodo(None)
                return
            if len(product) == 1:
                return
            where = "noIdentificacion LIKE '%{0}%' " \
                "OR descripcion LIKE '%{0}%'".format(product)
            products = self.db.sql('get_products', where)
            data = [(
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                util.currency(r[5], self.decimals),
                r[6]) for r in products]
            util.data_to_grid(self.grid_dm, data)
            self.dm.cmdMostrarTodo.Enabled = True
            self._info()
        return

    def cmdMostrarTodo(self, event):
        products = self.db.sql('get_products')
        data = [(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            util.currency(r[5], self.decimals),
            r[6]) for r in products]
        util.data_to_grid(self.grid_dm, data)
        self.dm.txtFiltrarProducto.Text = ''
        self.dm.cmdMostrarTodo.Enabled = False
        self.filter_product.setFocus()
        self._info()
        return

    def cmdFiltrar1(self, event):
        where = 'inventario AND existencia<=0'
        products = self.db.sql('get_products', where)
        if not products:
            msg = 'No se encontraron productos con existencias menores a ' \
                'cero o no tienes productos con control de inventario'
            util.msgbox(msg)
            return
        data = [(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            util.currency(r[5], self.decimals),
            r[6]) for r in products]
        util.data_to_grid(self.grid_dm, data)
        self.dm.txtFiltrarProducto.Text = ''
        self.dm.cmdMostrarTodo.Enabled = True
        self.filter_product.setFocus()
        self._info()
        return

    #~ def cmdReporte(self):
        #~ grid = self.dialog.getControl('gridProductos')
        #~ grid_dm = grid.Model.GridDataModel
        #~ if not grid_dm.RowCount:
            #~ message = 'No hay productos a reportar'
            #~ self.unogui.createMsgBox({'Message': message})
            #~ return
        #~ oDoc = self.util.newDoc()
        #~ oHoja = oDoc.getSheets().getByIndex(0)
        #~ data = self.__grid_to_tuple(grid.Model)
        #~ oRango = oHoja.getCellRangeByPosition(0, 0, len(data[0])-1, 0)
        #~ oRango.setDataArray((('Categoría', 'Clave', 'Descripción', 'Unidad', 'Precio', 'Existencia'),))
        #~ self.__format_title(oRango)
        #~ oRango = oHoja.getCellRangeByPosition(0, 1, len(data[0])-1, len(data))
        #~ oRango.setDataArray(data)
        #~ self.__format_columns(oRango, len(data)-1)
        #~ return

    #~ def __format_title(self, rango):
        #~ rango.CharWeight = 150
        #~ rango.VertJustify = 2
        #~ rango.HoriJustify = 2
        #~ return

    #~ def __format_columns(self, rango, num_fil):
        #~ col = rango.getCellRangeByPosition(4, 0, 4, num_fil)
        #~ col.NumberFormat = 104
        #~ return

    #~ def __grid_to_tuple(self, grid):
        #~ grid_dm = grid.GridDataModel
        #~ col = grid_dm.ColumnCount
        #~ fil = grid_dm.RowCount
        #~ data = []
        #~ for f in range(fil):
            #~ row = []
            #~ for c in range(1, col):
                #~ if c == 5:
                    #~ value = grid_dm.getCellData(c, f).replace(',', '')
                    #~ row.append(float(value))
                #~ elif c == 6:
                    #~ value = grid_dm.getCellData(c, f)
                    #~ if value != '':
                        #~ row.append(float(value))
                    #~ else:
                        #~ row.append(value)
                #~ else:
                    #~ row.append(grid_dm.getCellData(c, f))
            #~ data.append(tuple(row))
        #~ return tuple(data)



