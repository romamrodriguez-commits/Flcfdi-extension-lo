# -*- coding: utf-8 -*-

from .listenersadmin import listener


DLG_NAME = 'dlgCampos.xdl'
ICON_ACEPTAR = 'ok.png'
ICON_CANCELAR = 'cancel.png'


class Dlg(object):

    def __init__(self, caller, values):
        self.caller = caller
        self.unogui = caller.unogui
        self.db = caller.db
        self.globales = caller.globales
        self.util = caller.util
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config(values)
        self.listener.campos()

    def __config(self, values):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ACEPTAR)
        self.dm.cmdAceptar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_CANCELAR)
        self.dm.cmdCancelar.ImageURL = img_url
        self.dm.lblInfo.Tag = values[0]
        self.dm.lblInfo.Label = values[1]
        self.dialog.Title = '%s - Campos Personalizados' % self.globales['APP_TITULO']

        properties = {}
        properties['Name'] = 'gridCampos'
        properties['PositionX'] = 4
        properties['PositionY'] = 30
        properties['Width'] = 190
        properties['Height'] = 120
        properties['SelectionModel'] = 1
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Campo', 'ColumnWidth': 50, 'HorizontalAlign': 2},
        {'Title': 'Valor', 'ColumnWidth': 95, 'HorizontalAlign': 0},
        {'Title': 'Nodo', 'ColumnWidth': 0, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        if values[0]:
            data = self.db.select(('campospersonalizados',), ('campo', 'nodo'))
            campos = self.db.select(('cfdpersonalizados',), ('campo', 'valor'), 'id_cfd=%s' % values[0])
            d = {}
            for c in campos:
                d[c[0]] = c[1]
            if data:
                rows = []
                for row in data:
                    value = ''
                    if row[1] in d:
                        value = d[row[1]]
                    rows.append(('', row[0], value, row[1]))
                self.unogui.gridAddRows(oGrid, rows)
        else:
            grid_dm = self.caller.dm.gridCampos.GridDataModel
            fil = grid_dm.RowCount
            rows = []
            for f in range(fil):
                row = ('', grid_dm.getCellData(1, f),
                                grid_dm.getCellData(2, f), '')
                rows.append(row)
            self.unogui.gridAddRows(oGrid, rows)
        self.dm.txtEditar.Enabled = False
        self.dialog.getControl('datFecha').setVisible(False)
        #~ self.unogui.centerDialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()
