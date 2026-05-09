#!
# -*- coding: utf-8 -*-
from .listeners import listener
from threading import Thread
from facturalibre.settings import TITLE, VERSION, LOG, DEBUG, ICONS
from facturalibre.modulos import util


#~ DLG_NAME = 'dlg_admincompras.xdl'
ICON_FILTER = 'filter.png'
ICON_EXIT = 'salir.png'
ICON_PDF = 'pdf.png'
ICON_LIMPIAR = 'icon02.png'
ICON_CANCELAR = 'cancelar.png'
ICON_PAY = 'pay.png'
ICON_TOPAY = 'porpagar.png'
ICON_XML = 'xml.png'
ICON_REPORT = 'report.png'
ICON_MAIL = 'mail.png'
ICON_SELECT = 'select.png'
ICON_NOTE = 'note.png'
ICON_FIELDS = 'fields.png'
ICON_PRINT = 'print.png'
ICON_SAT = 'sat.png'


class MyThread(Thread):
    def __init__(self, rfc, label):
        self.rfc = rfc
        self.label = label
        Thread.__init__(self)

    def run(self):
        try:
            pac = ECODEX(self.rfc)
            res = pac.ClienteEstatus()
            self.label.Label = 'Folios PAC: %s' % res['TimbresDisponibles']
        except:
            pass


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.db = caller.db
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = self.unogui.createDialogFromURL(path_dlg)
        self.dm = self.dialog.Model
        self.enviar_correo = 0
        self.monedas = self.db.select_field('opciones', 'opcion3')
        self.listener = listener(self)
        self.__config()
        self.listener.admincompras()
        self.dialog.execute()
        self.dialog.dispose()

    def __config(self):
        self.dm.lblFoliosPac.Label = 'Consultando...'
        self.dm.lblVersion.Label = 'Factura Libre v{}'.format(VERSION)
        self.dm.lblInfo.Label = ''
        t = MyThread(
            self.db.select_field('certificado', 'rfc'),
            self.dm.lblFoliosPac)
        t.start()
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_EXIT)
        self.dm.cmdSalir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_FILTER)
        self.dm.cmdFiltrar1.ImageURL = img_url
        self.dm.cmdFiltrar2.ImageURL = img_url
        self.dm.cmdFiltrar3.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_LIMPIAR)
        self.dm.cmdLimpiarSeleccion.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_PAY)
        self.dm.cmdPagada.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_TOPAY)
        self.dm.cmdPorPagar.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_CANCELAR)
        self.dm.cmdCancelada.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SELECT)
        self.dm.cmdSeleccionarTodo.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_PDF)
        self.dm.cmdPdf.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_XML)
        self.dm.cmdXml.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_PRINT)
        self.dm.cmdImprimir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SAT)
        self.dm.cmdSat.ImageURL = img_url

        #~ Ocultamos los controles que no se van a utilizar
        self.dialog.getControl('cmdNotas').setVisible(False)
        self.dialog.getControl('cmdCamposPersonalizados').setVisible(False)
        self.dialog.getControl('cmdAddenda').setVisible(False)
        self.dialog.getControl('cmdEnviar').setVisible(False)
        self.dialog.getControl('cmdSinTimbrar').setVisible(False)
        self.dialog.getControl('cmdRefacturar').setVisible(False)
        self.dialog.getControl('cmdPdf').setVisible(True)
        #~ self.dialog.getControl('cmdXml').setVisible(False)
        #~ self.dialog.getControl('cmdImprimir').setVisible(False)
        self.dialog.getControl('cmdCorreo').setVisible(False)
        self.dialog.getControl('cmdReporte').setVisible(False)
        self.dialog.getControl('cmdReportes').setVisible(False)
        self.dialog.getControl('chkGuardar').setVisible(False)
        self.dialog.getControl('chkEditar').setVisible(False)
        self.dialog.getControl('lblReceptor').Text = 'Emisor'

        self.dialog.getControl('lblDelFolio').setVisible(False)
        self.dialog.getControl('lblAlFolio').setVisible(False)
        self.dialog.getControl('txtFolio1').setVisible(False)
        self.dialog.getControl('txtFolio2').setVisible(False)
        self.dialog.getControl('cmdFiltrar3').setVisible(False)
        self.dialog.getControl('lstReportes').setVisible(False)
        self.dialog.getControl('cmdCancelada').setVisible(not DEBUG)

        nombre = self.db.select_field('certificado', 'nombre')
        if nombre:
            self.dialog.Title = '%s - Administrar CFDI de compras - %s' % (self.globales['APP_TITULO'], nombre)
        else:
            self.dialog.Title = '%s - Administrar CFDI de compras' % self.globales['APP_TITULO']

        properties = {}
        properties['Name'] = 'gridReceptores'
        properties['PositionX'] = 34
        properties['PositionY'] = 17
        properties['Width'] = 400
        properties['Height'] = 200
        properties['SelectionModel'] = 1
        columns = ({'Title': 'Clave', 'ColumnWidth': 25, 'HorizontalAlign': 1},
        {'Title': 'RFC', 'ColumnWidth': 50, 'HorizontalAlign': 0},
        {'Title': 'Razón Social', 'ColumnWidth': 180, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridReceptores').setVisible(False)

        properties = {}
        properties['Name'] = 'gridDetalle'
        properties['PositionX'] = 6
        properties['PositionY'] = 137
        properties['Width'] = 428
        properties['Height'] = 75
        properties['SelectionModel'] = 0
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Clave', 'ColumnWidth': 40, 'HorizontalAlign': 1},
        {'Title': 'Unidad', 'ColumnWidth': 35, 'HorizontalAlign': 1},
        {'Title': 'Descripcion', 'ColumnWidth': 170, 'HorizontalAlign': 0},
        {'Title': 'Cantidad', 'ColumnWidth': 35, 'HorizontalAlign': 2},
        {'Title': 'Valor Unitario', 'ColumnWidth': 45, 'HorizontalAlign': 2},
        {'Title': 'Importe', 'ColumnWidth': 60, 'HorizontalAlign': 2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridDetalle.RowHeaderWidth = 20
        self.dialog.getControl('gridDetalle').setVisible(False)

        properties = {}
        properties['Name'] = 'gridTotales'
        properties['PositionX'] = 6
        properties['PositionY'] = 216
        properties['Width'] = 428
        properties['Height'] = 25
        properties['SelectionModel'] = 0
        properties['ShowRowHeader'] = False
        columns = ({'Title': 'SubTotal', 'ColumnWidth': 60, 'HorizontalAlign': 2},
        {'Title': 'Impuestos', 'ColumnWidth': 60, 'HorizontalAlign': 2},
        {'Title': 'TOTAL', 'ColumnWidth': 60, 'HorizontalAlign': 2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridTotales').setVisible(False)

        total_w = 0
        moneda_w = 0
        tc_w = 0
        mn_w = 50
        receptor_w = 185
        if self.monedas:
            total_w = 40
            moneda_w = 10
            tc_w = 25
            mn_w = 45
            receptor_w = 115
        properties = {}
        properties['Name'] = 'gridFacturas'
        properties['PositionX'] = 6
        properties['PositionY'] = 42
        properties['Width'] = 428
        properties['Height'] = 190
        properties['SelectionModel'] = 2
        columns=({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
                {'Title': 'Factura', 'ColumnWidth': 40, 'HorizontalAlign': 0},
                {'Title': 'Fecha', 'ColumnWidth': 40, 'HorizontalAlign': 2},
                {'Title': 'T', 'ColumnWidth': 10, 'HorizontalAlign': 1},
                {'Title': 'Estatus', 'ColumnWidth': 35, 'HorizontalAlign': 0},
                {'Title': 'Total', 'ColumnWidth': total_w, 'HorizontalAlign': 2},
                {'Title': 'M', 'ColumnWidth': moneda_w, 'HorizontalAlign': 1},
                {'Title': 'T.C.', 'ColumnWidth': tc_w, 'HorizontalAlign': 2},
                {'Title': 'Total M.N.', 'ColumnWidth': mn_w, 'HorizontalAlign': 2},
                {'Title': 'Razón Social', 'ColumnWidth': receptor_w, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridFacturas.RowHeaderWidth = 20
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
        #~ where = "compras.id_proveedor=receptores.id AND strftime('%m%Y',fecha)=strftime('%m%Y','now','localtime')"
        where = "strftime('%m%Y',fecha)=strftime('%m%Y','now','localtime')"
        pre = "LEFT OUTER JOIN receptores ON compras.id_proveedor=receptores.id"
        data = self.db.select(('compras', ),
            ('compras.id',
            'serie || folio',
            fecha,
            'upper(substr(tipoDeComprobante,1,1))',
            'estatus',
            'total',
            'upper(substr(Moneda,1,1))',
            'TipoCambio',
            'total*TipoCambio',
            'nombre', 'id_proveedor'), where, 'fecha', other1=pre)
        if data:
            data_format = []
            format_s = self.globales['FORMAT'] % self.db.select_field('opciones', 'decimales')
            suma_cfd = 0
            for row in data:
                total = format_s.format(row[5])
                tipo_cambio = format_s.format(row[7])
                suma_cfd += row[8]
                mn = format_s.format(row[8])
                row_format = (row[0], row[1], row[2], row[3], row[4], total, row[6], tipo_cambio, mn, row[9], row[10])
                data_format.append(row_format)
            self.unogui.gridAddRows(oGrid, data_format)
            self.dm.suma.Value = suma_cfd

        date = self.util.today()
        mes = self.dialog.getControl('lstMes')
        mes.selectItemPos(date.month, True)
        fields = ('MIN(fecha)', 'MAX(fecha)')
        data = self.db.select(('compras',), fields)
        year = self.dialog.getControl('lstAno')
        if data[0][0]:
            years = list(range(int(data[0][0][:4]), int(data[0][1][:4])+1))
        else:
            years = [self.util.today().year,]
        year.addItems(tuple(years), 0)
        year.addItems(('Todos',), 0)
        year.selectItem(self.util.today().year, True)
        self.dialog.getControl('txtCfd').setFocus()
        self.unogui.centerDialog(self.dialog)
        return

