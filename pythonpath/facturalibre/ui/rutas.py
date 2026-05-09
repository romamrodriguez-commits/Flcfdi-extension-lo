#!
# -*- coding: utf-8 -*-
from .listenersadmin import listener

DLG_NAME = 'dlgRutas.xdl'
ICON_ENTRAR = 'entrar.png'
ICON_SALIR = 'salir.png'


class Dlg(object):
    def __init__(self, caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.globales = caller.globales
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config()
        self.listener.rutas()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ENTRAR)
        self.dm.cmdEntrar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SALIR)
        self.dm.cmdSalir.ImageURL = img_url
        self.dialog.Title = '%s - Acceso ' % self.globales['APP_TITULO']

        properties = {}
        properties['Name'] = 'gridEmisores'
        properties['PositionX'] = 15
        properties['PositionY'] = 25
        properties['Width'] = 195
        properties['Height'] = 85
        columns = ({'Title': 'id','ColumnWidth': 0, 'HorizontalAlign': 1},
                {'Title': 'Emisores','ColumnWidth': 170, 'HorizontalAlign': 0})
        grid = self.unogui.createGrid(self.dialog, columns, properties)
        grid_dm = grid.GridDataModel
        for i,v in enumerate(self.caller.emisores):
            row = (i, v)
            self.unogui.gridAddRow(self.dm.gridEmisores, row)
            grid_dm.updateCellToolTip(1, i, self.caller.work_paths[i])

        self.unogui.centerDialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()