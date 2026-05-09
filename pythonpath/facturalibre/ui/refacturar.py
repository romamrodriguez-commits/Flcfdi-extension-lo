#!
# -*- coding: utf-8 -*-
from .listenersadmin import listener

DLG_NAME = 'dlgRefacturar.xdl'
ICON_FILTER = 'filter.png'
ICON_EXIT = 'close.png'
ICON_ELIMINAR = 'delete.png'
ICON_REFACTURAR = 'reinvoice.png'
ICON_PDF = 'pdf.png'


class Dlg(object):
    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.db = caller.db
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.prefactura = False
        self.listener = listener(self)
        self.__config()
        self.listener.refacturar()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_EXIT)
        self.dm.cmdSalir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_REFACTURAR)
        self.dm.cmdRefacturar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_ELIMINAR)
        self.dm.cmdEliminar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_FILTER)
        self.dm.cmdFiltrar1.ImageURL = img_url
        self.dm.cmdFiltrar2.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_PDF)
        self.dm.cmdPdf.ImageURL = img_url
        nombre = self.db.select_field('emisor', 'nombre')
        if nombre:
            self.dialog.Title = '%s - Refacturar CFD - %s' % (self.globales['APP_TITULO'], nombre)
        else:
            self.dialog.Title = '%s - Refacturar CFD' % self.globales['APP_TITULO']

        properties = {}
        properties['Name'] = 'gridReceptores'
        properties['PositionX'] = 3
        properties['PositionY'] = 17
        properties['Width'] = 300
        properties['Height'] = 200
        properties['SelectionModel'] = 1
        columns = ({'Title': 'Clave', 'ColumnWidth': 25, 'HorizontalAlign': 1},
        {'Title': 'RFC', 'ColumnWidth': 50, 'HorizontalAlign': 0},
        {'Title': 'Razón Social', 'ColumnWidth': 180, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridReceptores').setVisible(False)

        properties = {}
        properties['Name'] = 'gridFacturas'
        properties['PositionX'] = 2
        properties['PositionY'] = 42
        properties['Width'] = 365
        properties['Height'] = 184
        properties['SelectionModel'] = 1
        columns=({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
                {'Title': 'Factura', 'ColumnWidth': 25, 'HorizontalAlign': 0},
                {'Title': 'Fecha', 'ColumnWidth': 40, 'HorizontalAlign': 2},
                {'Title': 'T', 'ColumnWidth': 10, 'HorizontalAlign': 1},
                {'Title': 'Tipo', 'ColumnWidth': 30, 'HorizontalAlign': 0},
                {'Title': 'Total', 'ColumnWidth': 40, 'HorizontalAlign': 2},
                {'Title': 'M', 'ColumnWidth': 10, 'HorizontalAlign': 1},
                {'Title': 'T.C.', 'ColumnWidth': 25, 'HorizontalAlign': 2},
                {'Title': 'Total M.N.', 'ColumnWidth': 45, 'HorizontalAlign': 2},
                {'Title': 'Razón Social', 'ColumnWidth':115, 'HorizontalAlign':0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        #~ estatus = "CASE WHEN estatus=1 THEN 'Por pagar' WHEN estatus=2 THEN 'Pagada' WHEN estatus=3 THEN 'Cancelada' END"
        estatus = 'serie'
        #~ where = "cfdfacturas.id_cliente=receptores.id AND strftime('%m%Y',fecha)=strftime('%m%Y','now','localtime')"
        where = "strftime('%m%Y',fecha)=strftime('%m%Y','now','localtime')"
        pre = "LEFT OUTER JOIN receptores ON cfdfacturas.id_cliente=receptores.id"
        data = self.db.select(('cfdfacturas', ),
            ('cfdfacturas.id',
            'serie || folio',
            "strftime('%d-%m-%Y',fecha)",
            'upper(substr(tipoDeComprobante,1,1))',
            estatus,
            'total',
            'upper(substr(Moneda,1,1))',
            'TipoCambio',
            'total*TipoCambio',
            'nombre'), where, other1=pre)
        if data:
            data_format = []
            format_s = '{0:.%sf}' % self.db.select_field('opciones', 'decimales')
            for row in data:
                total = format_s.format(row[5])
                tipo_cambio = format_s.format(row[7])
                mn = format_s.format(row[8])
                row_format = (row[0], row[1], row[2], row[3], row[4], total, row[6], tipo_cambio, mn, row[9])
                data_format.append(row_format)
            self.unogui.gridAddRows(oGrid, data_format)
        date = self.util.today()
        mes = self.dialog.getControl('lstMes')
        mes.selectItemPos(date.month, True)
        self.dm.cmdPdf.Enabled = False
        self.dialog.getControl('txtCfd').setFocus()
        #~ self.unogui.centerDialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()
