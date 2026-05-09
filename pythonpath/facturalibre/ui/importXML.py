#!
# -*- coding: utf-8 -*-
from .listeners import listener

DLG_NAME = 'dlgImportXML.xdl'


class Dlg(object):
    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.db = caller.db
        self.unogui = caller.unogui
        self.globales = caller.globales
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        if self.__config():
            self.listener.importXML()
            self.dialog.execute()
            self.dialog.dispose()

    def __config(self):
        properties = {}
        properties['Name'] = 'gridConceptos'
        properties['PositionX'] = 6
        properties['PositionY'] = 106
        properties['Width'] = 340
        properties['Height'] = 126
        properties['SelectionModel'] = 1
        columns = ({'Title': 'Cantidad', 'ColumnWidth': 30, 'HorizontalAlign': 1},
        {'Title': 'Unidad', 'ColumnWidth': 40, 'HorizontalAlign': 0},
        {'Title': u'Descripción', 'ColumnWidth':100, 'HorizontalAlign': 0},
        {'Title': 'Precio U.', 'ColumnWidth': 36, 'HorizontalAlign': 2},
        {'Title': 'Importe', 'ColumnWidth': 44, 'HorizontalAlign': 2},
        {'Title': u'Clave', 'ColumnWidth': 30, 'HorizontalAlign': 2},
        {'Title': 'Clave int', 'ColumnWidth': 30, 'HorizontalAlign': 2},
        {'Title': 'id_producto', 'ColumnWidth': 0, 'HorizontalAlign': 2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridConceptos').setVisible(True)

        return True
