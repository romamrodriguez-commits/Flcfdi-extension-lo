# -*- coding: utf-8 -*-

import logging
from .listeners import Listener
from facturalibre.settings import TITLE, VERSION, LOG, ICONS
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self,caller):
        self.ctx = caller.ctx
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.db = caller.db
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.Model
        self.listener = Listener(self.dialog, self.db)
        self._config()
        self.listener.productosadmin()
        self.dialog.execute()
        self.dialog.dispose()

    def _config(self):
        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdMostrarTodo.ImageURL = img_url.format(ICONS['CLEAN'])
        self.dm.cmdEliminarProducto.ImageURL = img_url.format(ICONS['DELETE'])
        self.dm.cmdNuevoProducto.ImageURL = img_url.format(ICONS['ADD'])
        self.dm.cmdEditarProducto.ImageURL = img_url.format(ICONS['EDIT'])
        self.dm.cmdSalir.ImageURL = img_url.format(ICONS['CLOSE'])
        self.dm.cmdReporte.ImageURL = img_url.format(ICONS['REPORT'])
        self.dm.cmdFiltrar1.ImageURL = img_url.format(ICONS['ZERO'])
        decimals = self.db.select_field('opciones', 'decimales')

        title = '{} - Productos y Servicios '.format(TITLE)
        nombre = self.db.select_field('certificado', 'nombre')
        if nombre:
            title += '- {}'.format(nombre)
        self.dialog.Title = title
        properties = {}
        properties['Name'] = 'gridProductos'
        properties['PositionX'] = 6
        properties['PositionY'] = 27
        properties['Width'] = 388
        properties['Height'] = 232
        properties['Step'] = 5
        properties['SelectionModel'] = 1
        columns=(
            {'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
            {'Title': 'Categoria', 'ColumnWidth': 40, 'HorizontalAlign': 0},
            {'Title': 'Clave', 'ColumnWidth': 50, 'HorizontalAlign': 0},
            {'Title': 'Descripción', 'ColumnWidth': 160, 'HorizontalAlign': 0},
            {'Title': 'Unidad', 'ColumnWidth': 40, 'HorizontalAlign': 0},
            {'Title': 'Precio U.', 'ColumnWidth': 40, 'HorizontalAlign': 2},
            {'Title': 'Existencia', 'ColumnWidth': 30, 'HorizontalAlign': 2}
        )
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridProductos.RowHeaderWidth = 15
        products = self.db.sql('get_products')
        if products:
            data = [(
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                util.currency(r[5], decimals),
                r[6]) for r in products]
            util.data_to_grid(self.dm.gridProductos.GridDataModel, data)
            self.dm.cmdEditarProducto.Enabled = True
            self.dm.cmdEliminarProducto.Enabled = True
            self.dm.txtFiltrarProducto.Enabled = True
            if len(products) == 1:
                self.dm.lblInfo.Label = '1 Registro'
            else:
                self.dm.lblInfo.Label = '%s Registros' % len(products)
        else:
            self.dm.lblInfo.Label = 'Sin Registros'

        taxs = self.db.has_data('impuestos')
        if not taxs:
            msg = 'No hay impuestos dados de alta, necesitas al menos uno ' \
                'para poder agregar un producto o servicio'
            util.msgbox(msg)
        self.dm.cmdNuevoProducto.Enabled = taxs
        self.dm.cmdEditarProducto.Enabled = taxs
        self.dm.cmdReporte.Enabled = False
        util.center_dialog(self.dialog)
        self.dialog.getControl('txtFiltrarProducto').setFocus()
        return

