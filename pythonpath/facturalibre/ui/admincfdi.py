# -*- coding: utf-8 -*-

import logging
from .listeners import listener
from facturalibre.settings import TITLE, VERSION, LOG, DEBUG, ICONS, FORMAT
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.unogui = caller.unogui
        self.globales = caller.globales
        self.db = caller.db
        self.path_pem = ''
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.getModel()
        self.enviar_correo = 0
        self.monedas = self.db.select_field('opciones', 'opcion3')
        self.listener = listener(self)
        self.new_server = True
        self._config()
        self.listener.admincfdi()
        self.dialog.execute()
        self.dialog.dispose()

    def _config(self):
        tipo = self.db.select_field('emisor', 'tipo')
        if tipo == 3:
            self.new_server = False
        self.dm.lblFoliosPac.Label = 'Sin conexión'
        self.dm.lblVersion.Label = '{} v{}'.format(TITLE, VERSION)
        self.dm.lblInfo.Label = ''
        if self.util.hay_conexion():
            self.dm.lblFoliosPac.Label = 'Consultando...'
            rfc = self.db.select_field('certificado', 'rfc')
            #~ self.util.get_timbres(rfc, self.dm.lblFoliosPac, self.new_server)
            ok, timbres = util.get_timbres(rfc, self.new_server, not self.new_server)
            self.dm.lblFoliosPac.Label = 'Folios PAC: {}'.format(timbres)
        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdSalir.ImageURL = img_url.format(ICONS['CLOSE'])
        self.dm.cmdPdf.ImageURL = img_url.format(ICONS['PDF'])
        self.dm.cmdSat.ImageURL = img_url.format(ICONS['SAT'])
        self.dm.cmdFiltrar1.ImageURL = img_url.format(ICONS['FILTER'])
        self.dm.cmdFiltrar2.ImageURL = img_url.format(ICONS['FILTER'])
        self.dm.cmdFiltrar3.ImageURL = img_url.format(ICONS['FILTER'])
        self.dm.cmdLimpiarSeleccion.ImageURL = img_url.format(ICONS['CLEAN'])
        self.dm.cmdPagada.ImageURL = img_url.format(ICONS['PAY'])
        self.dm.cmdPorPagar.ImageURL = img_url.format(ICONS['TOPAY'])
        self.dm.cmdCancelada.ImageURL = img_url.format(ICONS['CANCEL'])
        self.dm.cmdXml.ImageURL = img_url.format(ICONS['XML'])
        self.dm.cmdReporte.ImageURL = img_url.format(ICONS['REPORT'])
        self.dm.cmdReportes.ImageURL = img_url.format(ICONS['REPORT'])
        self.dm.cmdCorreo.ImageURL = img_url.format(ICONS['MAIL'])
        self.dm.cmdSeleccionarTodo.ImageURL = img_url.format(ICONS['SELECT'])
        self.dm.cmdNotas.ImageURL = img_url.format(ICONS['NOTE'])
        self.dm.cmdCamposPersonalizados.ImageURL = img_url.format(ICONS['FIELDS'])
        self.dm.cmdAddenda.ImageURL = img_url.format(ICONS['ADDENDA'])
        self.dm.cmdEnviar.ImageURL = img_url.format(ICONS['FTP'])
        self.dm.cmdImprimir.ImageURL = img_url.format(ICONS['PRINT'])
        self.dm.cmdSinTimbrar.ImageURL = img_url.format(ICONS['SIN_TIMBRAR'])
        self.dm.cmdRefacturar.ImageURL = img_url.format(ICONS['REINVOICE'])
        self.dm.cmdEliminar.ImageURL = img_url.format(ICONS['DELETE'])
        self.dm.cmdTimbrar.ImageURL = img_url.format(ICONS['XML3'])
        self.dm.cmdValidar.ImageURL = img_url.format(ICONS['OK'])

        self.dialog.getControl('cmdNotas').setEnable(False)
        self.dialog.getControl('cmdCamposPersonalizados').setEnable(False)
        self.dialog.getControl('cmdAddenda').setEnable(False)
        self.dialog.getControl('cmdEnviar').setEnable(False)
        self.dialog.getControl('cmdEnviar').setVisible(False)
        #~ self.dialog.getControl('cmdSat').setEnable(not DEBUG)

        pem = self.util.getPathTemp()
        data = self.db.select_field('certificado', 'pem')
        self.util.save_file(pem, data)
        self.path_pem = pem

        data = self.db.select_field('asignaciones', 'id')
        if not data:
            self.dialog.getControl('cmdAddenda').setVisible(False)

        nombre = self.db.select_field('certificado', 'nombre')
        if nombre:
            self.dialog.Title = '{} - Administrar CFD - {}'.format(TITLE, nombre)
        else:
            self.dialog.Title = '{} - Administrar CFD'.format(TITLE)

        self.dialog.getControl('cmdRefacturar').setEnable(False)
        data = self.db.select_field('certificado', 'final')
        if data:
            dif = self.util.get_date_from_string(data, True) - self.util.now()
            if dif.total_seconds() > 0:
                self.dialog.getControl('cmdRefacturar').setEnable(True)

        properties = {}
        properties['Name'] = 'gridReceptores'
        properties['PositionX'] = 100
        properties['PositionY'] = 17
        properties['Width'] = 322
        properties['Height'] = 200
        properties['SelectionModel'] = 1
        columns = ({'Title': 'Clave', 'ColumnWidth': 50, 'HorizontalAlign': 1},
        {'Title': 'RFC', 'ColumnWidth': 50, 'HorizontalAlign': 0},
        {'Title': 'Razón Social', 'ColumnWidth': 200, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridReceptores').setVisible(False)

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
            'nombre',
            'id_cliente',
            'uuid',
            'version'), where, 'fecha_timbrado', other1=pre)
        if data:
            data_format = []
            format_s = FORMAT.format(
                self.db.select_field('opciones', 'decimales'))
            suma_cfd = 0
            for row in data:
                total = format_s.format(row[5])
                tipo_cambio = format_s.format(row[7])
                suma_cfd += row[8]
                mn = format_s.format(row[8])
                row_format = (row[0], row[1], row[2], row[3], row[4], total,
                    row[6], tipo_cambio, mn, row[9], row[10])
                data_format.append(row_format)
            self.unogui.gridAddRows(oGrid, data_format)
            self.dm.suma.Value = suma_cfd

            grid_dm = self.dm.gridFacturas.GridDataModel
            colors = []
            for i, v in enumerate(data):
                grid_dm.updateCellToolTip(1, i, v[11])
                if v[11] or float(v[12]) < 3:
                    colors.append(self.util.rgb(255,255,255))
                elif v[4] == 'Validada':
                    colors.append(self.util.rgb(186,255,200))
                else:
                    colors.append(self.util.rgb(255,204,153))
            self.dm.gridFacturas.RowBackgroundColors = tuple(colors)

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

        self.dialog.getControl('txtCfd').setFocus()
        self.unogui.centerDialog(self.dialog)
        return

