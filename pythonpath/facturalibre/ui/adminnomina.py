# -*- coding: utf-8 -*-

import logging
from .listeners import listener
import traceback
import locale
from facturalibre.settings import TITLE, VERSION, LOG, ICONS
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])

DLG_NAME = 'dlgAdminNomina.xdl'
ICON_FILTER = 'filter.png'
ICON_EXIT = 'close.png'
ICON_PDF = 'pdf.png'
ICON_LIMPIAR = 'clean.png'
ICON_CANCELAR = 'cancel.png'
ICON_PAY = 'pay.png'
ICON_XML = 'xml.png'
ICON_REPORT = 'report.png'
ICON_REINVOICE = 'reinvoice.png'
ICON_MAIL = 'mail.png'
ICON_SELECT = 'select.png'
ICON_NOTE = 'note.png'
ICON_FIELDS = 'fields.png'
ICON_ADDENDA = 'addenda.png'
ICON_FTP = 'ftpcon.png'
ICON_PRINT = 'print.png'
ICON_SIN_TIMBRAR = 'sintimbrar.png'
ICON_IMPORT = 'import.png'
ICON_DELETE = 'delete.png'
ICON_PATH = '%s/icons/%s'


class Dlg(object):

    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        if self.globales['OS'] == self.globales['WIN']:
            locale.setlocale(locale.LC_TIME, '')
        self.unogui = caller.unogui
        self.db = caller.db
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.enviar_correo = 0
        self.path_pem = ''
        self.monedas = self.db.select_field('opciones', 'opcion3')
        self.rfc_emisor = ''
        self.listener = listener(self)
        self.new_server = True
        self._config()
        self.listener.adminnomina()
        self.dialog.execute()
        self.dialog.dispose()

    def _config(self):
        self.dm.lblFoliosPac.Label = 'Sin conexión'
        self.dm.lblVersion.Label = 'Nomina Libre v{}'.format(VERSION)
        self.dm.lblInfo.Label = ''
        if self.util.hay_conexion():
            tipo = self.db.select_field('emisor', 'tipo')
            if tipo == 3:
                self.new_server = False
            self.dm.lblFoliosPac.Label = 'Consultando...'
            self.rfc_emisor = self.db.select_field('certificado', 'rfc')
            t = util.GetTimbres(self.rfc_emisor, self.dm.lblFoliosPac, self.new_server, not self.new_server)
            t.start()
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_EXIT)
        self.dm.cmdSalir.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_FILTER)
        self.dm.cmdFiltrar1.ImageURL = img_url
        self.dm.cmdFolio.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_REPORT)
        self.dm.cmdReportes.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'],ICON_LIMPIAR)
        self.dm.cmdLimpiarSeleccion.ImageURL=img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_SIN_TIMBRAR)
        self.dm.cmdSinTimbrar.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_SELECT)
        self.dm.cmdSeleccionarTodo.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_IMPORT)
        self.dm.cmdImportar.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_XML)
        self.dm.cmdEnviar.ImageURL = img_url
        self.dm.cmdCopyXML.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_PDF)
        self.dm.cmdPdf.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_CANCELAR)
        self.dm.cmdCancelar.ImageURL = img_url
        img_url = ICON_PATH % (self.globales['EXT_PATH'], ICON_DELETE)
        self.dm.cmdDelete.ImageURL = img_url

        nombre = self.db.select_field('certificado', 'nombre')
        self.dialog.Title = 'Administrar Nomina CFDI - %s' % nombre

        pem = self.util.getPathTemp()
        data = self.db.select_field('certificado', 'pem')
        self.util.save_file(pem, data)
        self.path_pem = pem

        properties = {}
        properties['Name'] = 'gridReceptores'
        properties['PositionX'] = 105
        properties['PositionY'] = 17
        properties['Width'] = 330
        properties['Height'] = 200
        properties['SelectionModel'] = 1
        columns = ({'Title': 'Clave', 'ColumnWidth': 30, 'HorizontalAlign': 1},
        {'Title': 'RFC', 'ColumnWidth': 50, 'HorizontalAlign': 0},
        {'Title': 'CURP', 'ColumnWidth': 75, 'HorizontalAlign': 0},
        {'Title': 'Nombre del empleado', 'ColumnWidth': 160, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridReceptores').setVisible(False)

        #~ total_w = 0
        #~ moneda_w = 0
        #~ tc_w = 0
        #~ mn_w = 50
        #~ receptor_w = 165
        #~ if self.monedas:
            #~ total_w = 40
            #~ moneda_w = 10
            #~ tc_w = 25
            #~ mn_w = 45
            #~ receptor_w = 90
        properties = {}
        properties['Name'] = 'gridFacturas'
        properties['PositionX'] = 5
        properties['PositionY'] = 45
        properties['Width'] = 428
        properties['Height'] = 190
        properties['SelectionModel'] = 2
        columns=({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
                {'Title': 'Recibo', 'ColumnWidth': 40, 'HorizontalAlign': 0},
                {'Title': 'Fecha y Hora', 'ColumnWidth': 65, 'HorizontalAlign': 2},
                {'Title': 'Estatus', 'ColumnWidth': 40, 'HorizontalAlign': 0},
                {'Title': 'Fecha pago', 'ColumnWidth': 50, 'HorizontalAlign': 2},
                {'Title': 'Total M.N.', 'ColumnWidth': 50, 'HorizontalAlign': 2},
                {'Title': 'Empleado', 'ColumnWidth': 150, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridFacturas.RowHeaderWidth = 20

        fecha = """CASE strftime('%m', fecha_timbrado)
            WHEN '01' THEN strftime('%d-Ene-%Y %H:%M:%S', fecha_timbrado)
            WHEN '02' THEN strftime('%d-Feb-%Y %H:%M:%S', fecha_timbrado)
            WHEN '03' THEN strftime('%d-Mar-%Y %H:%M:%S', fecha_timbrado)
            WHEN '04' THEN strftime('%d-Abr-%Y %H:%M:%S', fecha_timbrado)
            WHEN '05' THEN strftime('%d-May-%Y %H:%M:%S', fecha_timbrado)
            WHEN '06' THEN strftime('%d-Jun-%Y %H:%M:%S', fecha_timbrado)
            WHEN '07' THEN strftime('%d-Jul-%Y %H:%M:%S', fecha_timbrado)
            WHEN '08' THEN strftime('%d-Ago-%Y %H:%M:%S', fecha_timbrado)
            WHEN '09' THEN strftime('%d-Sep-%Y %H:%M:%S', fecha_timbrado)
            WHEN '10' THEN strftime('%d-Oct-%Y %H:%M:%S', fecha_timbrado)
            WHEN '11' THEN strftime('%d-Nov-%Y %H:%M:%S', fecha_timbrado)
            WHEN '12' THEN strftime('%d-Dic-%Y %H:%M:%S', fecha_timbrado) END"""
        fecha_pago = """CASE strftime('%m', fecha_pago)
            WHEN '01' THEN strftime('%d-Ene-%Y', fecha_pago)
            WHEN '02' THEN strftime('%d-Feb-%Y', fecha_pago)
            WHEN '03' THEN strftime('%d-Mar-%Y', fecha_pago)
            WHEN '04' THEN strftime('%d-Abr-%Y', fecha_pago)
            WHEN '05' THEN strftime('%d-May-%Y', fecha_pago)
            WHEN '06' THEN strftime('%d-Jun-%Y', fecha_pago)
            WHEN '07' THEN strftime('%d-Jul-%Y', fecha_pago)
            WHEN '08' THEN strftime('%d-Ago-%Y', fecha_pago)
            WHEN '09' THEN strftime('%d-Sep-%Y', fecha_pago)
            WHEN '10' THEN strftime('%d-Oct-%Y', fecha_pago)
            WHEN '11' THEN strftime('%d-Nov-%Y', fecha_pago)
            WHEN '12' THEN strftime('%d-Dic-%Y', fecha_pago) END"""
        where = "strftime('%m%Y',fecha_timbrado)=strftime('%m%Y','now','localtime')"
        data = self.db.select(('nominacfdi', ),
            ('id',
            'folio',
            fecha,
            'estatus',
            fecha_pago,
            'total*tipo_cambio',
            'empleado'), 'uuid=""', 'fecha_timbrado')
        if data:
            data_format = []
            format_s = self.globales['FORMAT'] % self.db.select_field('opciones', 'decimales')
            suma_cfd = 0
            for row in data:
                if row[5] is None:
                    msg = 'El total del recibo %s de %s, es nulo, esto ' \
                        'generalmente es un error de importación, elimina ' \
                        'este recibo y corrigue el error en la plantilla o ' \
                        'consulta a soporte técnico' % (row[1], row[6])
                    self.unogui.createMsgBox({'Message': msg})
                    total = format_s.format(0)
                else:
                    total = format_s.format(row[5])
                row_format = (row[0], row[1], row[2], row[3], row[4], total, row[6])
                data_format.append(row_format)
            self.unogui.gridAddRows(oGrid, data_format)
            msg = '%s Recibos de nomina sin timbrar' % len(data)
        else:
            msg = 'No tienes recibos de nomina sin timbrar'
        self.dm.lblInfo.Label = msg
        data = self.db.select(
            ('nominacfdi',),
            ('DISTINCT(fecha_pago)',),
            order='fecha_pago')
        data = [self.util.format_date(r[0], '%d-%b-%Y') for r in data]
        fecha_pago = self.dialog.getControl('lstFechaPago')
        if data:
            fecha_pago.addItems(tuple(data), 0)
        fecha_pago.addItems(('Todos',), 0)
        fecha_pago.selectItem('Todos', True)

        data = self.db.select(('reportes',), order='nombre')
        if data:
            reports = self.dialog.getControl('lstReportes')
            for r in data:
                reports.addItem(r[1], reports.getItemCount())
            reports.addItem('Selecciona un reporte', 0)
            reports.selectItemPos(0, True)
        else:
            self.dialog.getControl('cmdReportes').setVisible(False)
            self.dialog.getControl('lstReportes').setVisible(False)

        fields = ('MIN(fecha_timbrado)', 'MAX(fecha_timbrado)')
        data = self.db.select(('cfdfacturas',), fields)
        mes = self.dialog.getControl('lstMes')
        year = self.dialog.getControl('lstAno')
        if data[0][0]:
            years = list(range(int(data[0][0][:4]), int(data[0][1][:4])+1))
        else:
            years = [self.util.today().year,]
        year.addItems(tuple(years), 0)
        year.addItems(('Todos',), 0)
        date = self.util.today()
        year.selectItem(date.year, True)
        mes.selectItemPos(date.month, True)

        self.unogui.centerDialog(self.dialog)
        return

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_PDF)
        self.dm.cmdPdf.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_PAY)
        self.dm.cmdPagada.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_CANCELAR)
        self.dm.cmdCancelada.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_XML)
        self.dm.cmdXml.ImageURL = img_url

        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_MAIL)
        self.dm.cmdCorreo.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_NOTE)
        self.dm.cmdNotas.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_FIELDS)
        self.dm.cmdCamposPersonalizados.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ADDENDA)
        self.dm.cmdAddenda.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_FTP)
        self.dm.cmdEnviar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_PRINT)
        self.dm.cmdImprimir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_REINVOICE)
        self.dm.cmdRefacturar.ImageURL = img_url
        self.dialog.getControl('cmdNotas').setEnable(False)
        self.dialog.getControl('cmdCamposPersonalizados').setEnable(False)
        self.dialog.getControl('cmdAddenda').setEnable(False)
        self.dialog.getControl('cmdEnviar').setEnable(False)
        self.dialog.getControl('cmdEnviar').setVisible(False)

        data = self.db.select_field('asignaciones', 'id')
        if not data:
            self.dialog.getControl('cmdAddenda').setVisible(False)





        properties = {}
        properties['Name'] = 'gridDetalle'
        properties['PositionX'] = 5
        properties['PositionY'] = 137
        properties['Width'] = 428
        properties['Height'] = 75
        properties['SelectionModel'] = 0
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Clave', 'ColumnWidth': 50, 'HorizontalAlign': 1},
        {'Title': 'Unidad', 'ColumnWidth': 30, 'HorizontalAlign': 1},
        {'Title': 'Descripcion', 'ColumnWidth': 160, 'HorizontalAlign': 0},
        {'Title': 'Cantidad', 'ColumnWidth': 30, 'HorizontalAlign': 2},
        {'Title': 'Valor Unitario', 'ColumnWidth': 40, 'HorizontalAlign': 2},
        {'Title': 'Importe', 'ColumnWidth': 50, 'HorizontalAlign': 2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridDetalle.RowHeaderWidth = 20
        self.dialog.getControl('gridDetalle').setVisible(False)

        properties = {}
        properties['Name'] = 'gridTotales'
        properties['PositionX'] = 5
        properties['PositionY'] = 216
        properties['Width'] = 428
        properties['Height'] = 25
        properties['SelectionModel'] = 0
        properties['ShowRowHeader'] = False
        columns = ({'Title': 'SubTotal', 'ColumnWidth': 70, 'HorizontalAlign': 2},
        {'Title': 'Impuestos', 'ColumnWidth': 70, 'HorizontalAlign': 2},
        {'Title': 'TOTAL', 'ColumnWidth': 70, 'HorizontalAlign': 2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridTotales').setVisible(False)

        total_w = 0
        moneda_w = 0
        tc_w = 0
        mn_w = 50
        receptor_w = 165
        if self.monedas:
            total_w = 40
            moneda_w = 10
            tc_w = 25
            mn_w = 45
            receptor_w = 90
        properties = {}
        properties['Name'] = 'gridFacturas'
        properties['PositionX'] = 5
        properties['PositionY'] = 60
        properties['Width'] = 428
        properties['Height'] = 180
        properties['SelectionModel'] = 2
        columns=({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
                {'Title': 'Factura', 'ColumnWidth': 40, 'HorizontalAlign': 0},
                {'Title': 'Fecha y Hora', 'ColumnWidth': 65, 'HorizontalAlign': 2},
                {'Title': 'T', 'ColumnWidth': 10, 'HorizontalAlign': 1},
                {'Title': 'Estatus', 'ColumnWidth': 32, 'HorizontalAlign': 0},
                {'Title': 'Total', 'ColumnWidth': total_w, 'HorizontalAlign': 2},
                {'Title': 'M', 'ColumnWidth': moneda_w, 'HorizontalAlign': 1},
                {'Title': 'T.C.', 'ColumnWidth': tc_w, 'HorizontalAlign': 2},
                {'Title': 'Total M.N.', 'ColumnWidth': mn_w, 'HorizontalAlign': 2},
                {'Title': 'Razón Social', 'ColumnWidth': receptor_w, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridFacturas.RowHeaderWidth = 20
        fecha = """CASE strftime('%m', fecha_timbrado)
            WHEN '01' THEN strftime('%d-Ene-%Y %H:%M:%S', fecha_timbrado)
            WHEN '02' THEN strftime('%d-Feb-%Y %H:%M:%S', fecha_timbrado)
            WHEN '03' THEN strftime('%d-Mar-%Y %H:%M:%S', fecha_timbrado)
            WHEN '04' THEN strftime('%d-Abr-%Y %H:%M:%S', fecha_timbrado)
            WHEN '05' THEN strftime('%d-May-%Y %H:%M:%S', fecha_timbrado)
            WHEN '06' THEN strftime('%d-Jun-%Y %H:%M:%S', fecha_timbrado)
            WHEN '07' THEN strftime('%d-Jul-%Y %H:%M:%S', fecha_timbrado)
            WHEN '08' THEN strftime('%d-Ago-%Y %H:%M:%S', fecha_timbrado)
            WHEN '09' THEN strftime('%d-Sep-%Y %H:%M:%S', fecha_timbrado)
            WHEN '10' THEN strftime('%d-Oct-%Y %H:%M:%S', fecha_timbrado)
            WHEN '11' THEN strftime('%d-Nov-%Y %H:%M:%S', fecha_timbrado)
            WHEN '12' THEN strftime('%d-Dic-%Y %H:%M:%S', fecha_timbrado) END"""
        where = "strftime('%m%Y',fecha_timbrado)=strftime('%m%Y','now','localtime')"
        pre = "LEFT OUTER JOIN receptores ON cfdfacturas.id_cliente=receptores.id"
        data = self.db.select(('cfdfacturas', ),
            ('cfdfacturas.id',
            'serie || folio',
            fecha,
            'upper(substr(tipoDeComprobante,1,1))',
            'estatus',
            'total',
            'upper(substr(Moneda,1,1))',
            'TipoCambio',
            'total*TipoCambio',
            'nombre', 'id_cliente'), where, 'fecha_timbrado', other1=pre)
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
        self.enviar_correo = self.db.select_field('opciones2', 'opcion5')
        if not self.enviar_correo:
            self.dialog.getControl('cmdCorreo').setVisible(False)
        editar = bool(self.db.select_field('opciones2', 'opcion6'))
        self.dialog.getControl('chkEditar').setVisible(editar)
        date = self.util.today()
        mes = self.dialog.getControl('lstMes')
        mes.selectItemPos(date.month, True)
        fields = ('MIN(fecha_timbrado)', 'MAX(fecha_timbrado)')
        data = self.db.select(('cfdfacturas',), fields)
        year = self.dialog.getControl('lstAno')
        if data[0][0]:
            years = list(range(int(data[0][0][:4]), int(data[0][1][:4])+1))
        else:
            years = [self.util.today().year,]
        year.addItems(tuple(years), 0)
        year.addItems(('Todos',), 0)
        year.selectItem(self.util.today().year, True)
        data = self.db.select(('campospersonalizados',),('campo', 'nodo'))
        if not data:
            self.dialog.getControl('cmdCamposPersonalizados').setVisible(False)

        return

