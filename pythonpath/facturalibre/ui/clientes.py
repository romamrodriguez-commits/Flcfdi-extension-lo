# -*- coding: utf-8 -*-

import logging
from .listeners import listener
from facturalibre.settings import TITLE, LOG, ICONS
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
        self.dm = self.dialog.getModel()
        self.listener = listener(self)
        self._config()
        self.listener.clientes()
        self.dialog.execute()
        self.dialog.dispose()

    def _config(self):
        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdMostrarTodo.ImageURL = img_url.format(ICONS['CLEAN'])
        self.dm.cmdEliminarCliente.ImageURL = img_url.format(ICONS['DELETE'])
        self.dm.cmdNuevoCliente.ImageURL = img_url.format(ICONS['NEW_CLIENT'])
        self.dm.cmdEditarCliente.ImageURL = img_url.format(ICONS['EDIT'])
        self.dm.cmdSalir.ImageURL = img_url.format(ICONS['CLOSE'])
        self.dm.cmdReporte.ImageURL = img_url.format(ICONS['REPORT'])

        nombre = self.db.select_field('emisor', 'nombre')
        title = '{} - Receptores (Clientes) '.format(TITLE)
        if nombre:
            title += '- {}'.format(nombre)
        self.dialog.Title = title

        properties = {}
        properties['Name'] = 'gridReceptores'
        properties['PositionX'] = 5
        properties['PositionY'] = 27
        properties['Width'] = 390
        properties['Height'] = 232
        properties['Step'] = 0
        properties['SelectionModel'] = 1
        columns=(
            {'Title': 'Clave', 'ColumnWidth': 40, 'HorizontalAlign': 2},
            {'Title': 'RFC', 'ColumnWidth': 60, 'HorizontalAlign': 0},
            {'Title': 'Razón Social', 'ColumnWidth': 200, 'HorizontalAlign': 0},
            {'Title': 'Notas', 'ColumnWidth': 60, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridReceptores.RowHeaderWidth = 15
        data = self.db.select(
            ('receptores',), ('id','rfc', 'nombre', 'notas'), order='nombre')
        if data:
            self.unogui.gridAddRows(oGrid, data)
            self.dm.cmdEditarCliente.Enabled = True
            self.dm.cmdEliminarCliente.Enabled = True
            self.dm.txtFiltrarCliente.Enabled = True
            if len(data) == 1:
                self.dm.lblInfo.Label = '1 Registro'
            else:
                self.dm.lblInfo.Label = '%s Registros' % len(data)
        else:
            self.dm.lblInfo.Label = 'Sin Registros'
        self.dialog.getControl('txtFiltrarCliente').setFocus()
        self.unogui.centerDialog(self.dialog)
        return

