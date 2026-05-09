# -*- coding: utf-8 -*-

import logging
from xml.etree import ElementTree as ET
from facturalibre.modulos.pyXml import CFDXML
from facturalibre.modulos.pyPdf import CFDPDF
from facturalibre.modulos.pyPdf import PDFAcuse
import facturalibre.ui.inputbox as inputbox
import facturalibre.ui.inputbox2 as inputbox2
import facturalibre.ui.campos as campos
from facturalibre.settings import DEBUG, LOG, KEY, TYPE_MSG, BUTTONS, \
    BUTTON_CLICK, ICONS, FORMAT, PRE, CLIENTES_COUNT, MOSTRAR_LIMITE, \
    SEND_MAIL, FILE_NAME
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class EventosAdminCfdi(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.globales = caller.globales
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.grid = self.dialog.getControl('gridFacturas')
        self.grid_dm = self.dm.gridFacturas.GridDataModel
        self.db = caller.db
        self.rfc = self.db.select_field('certificado', 'rfc')
        self.format_s = FORMAT.format(
            self.db.select_field('opciones', 'decimales'))
        self.enviar_correo = caller.enviar_correo
        self.value = ''
        self.img_url = '{}/icons/'.format(self.PATH_EXT)
        self.id_addenda = 0
        self.id_cfd = 0
        self.path_pem = caller.path_pem
        self.new_server = caller.new_server

    def cmdSinTimbrar(self):
        self.dm.chkDetalle.State = 0
        self.chkDetalle(self.dm.chkDetalle)
        where = 'version="3.2" and uuid="" and estatus<>"Validada"'
        self.__filtrar(where)
        return

    def msg_user(self, msg):
        self.dm.lblInfo.Label = msg
        return

    def cmdSalir(self):
        util.kill(self.path_pem)
        self.dialog.endExecute()
        return

    def cmdFiltrar1(self):
        where = ''
        lst = self.dialog.getControl('lstMes')
        year = self.dialog.getControl('lstAno')
        pos1 = lst.SelectedItemPos
        pos2 = year.SelectedItemPos
        if pos1 > 0 and pos2 > 0:
            filtro = '%02d%s' % (pos1, year.SelectedItem)
            where = " AND strftime('%m%Y',fecha_timbrado)='" + filtro + "'"
        elif pos1 == 0 and pos2 > 0:
            filtro = str(year.SelectedItem)
            where = " AND strftime('%Y',fecha_timbrado)='" + filtro + "'"
        elif pos1 > 0 and pos2 == 0:
            filtro = '%02d' % pos1
            where = " AND strftime('%m',fecha_timbrado)='" + filtro + "'"
        lst = self.dialog.getControl('lstEstatus')
        pos = lst.getSelectedItemPos()
        if pos > 0:
            where += " AND estatus='%s'" % lst.getSelectedItem()
        if self.dm.txtReceptor.Tag:
            where += " AND id_cliente=%s" % self.dm.txtReceptor.Tag
        self.__filtrar(where)
        return

    def cmdFiltrar2(self):
        where = ''
        if self.dm.txtCfd.Text:
            try:
                folio = int(self.dm.txtCfd.Text)
                where = " AND folio=%s" % folio
            except:
                where = " AND serie||folio='%s'" % self.dm.txtCfd.Text
            self.__filtrar(where)
        else:
            self.dialog.getControl('txtCfd').setFocus()
            message = 'Introduce el folio a buscar'
            self.msg_user(message)
        return

    def cmdFiltrar3(self):
        where = ''
        desde = self.dm.txtFolio1.Value
        if desde is None:
            self.dialog.getControl('txtFolio1').setFocus()
            message = 'Captura el folio inicial'
            self.msg_user(message)
            return
        hasta = self.dm.txtFolio2.Value
        if hasta is None:
            self.dialog.getControl('txtFolio2').setFocus()
            message = 'Captura el folio final'
            self.msg_user(message)
            return
        if desde > hasta:
            desde = self.dm.txtFolio2.Value
            hasta = self.dm.txtFolio1.Value
        where = " AND folio BETWEEN %s AND %s" % (int(desde), int(hasta))
        if self.dm.txtReceptor.Tag:
            where += " AND id_cliente=%s" % self.dm.txtReceptor.Tag
        self.__filtrar(where)
        return

    def cmdImprimir(self):
        avance =  self.dialog.getControl('pbCopia')
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        #~ sel = grid.SelectedRows
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        if len(sel) > MOSTRAR_LIMITE:
            message = 'Vas a imprimir %s documentos.\n\n¿Estás seguro de ' \
                'continuar?' % len(sel)
            if not self.unogui.createQuestion('Factura Libre', message):
                return
        avance.setRange(0, len(sel))
        facturas = []
        for row in sel:
            facturas.append(grid_dm.getCellData(0, row))
        if self.dm.chkDetalle.State:
            self.dialog.getControl('gridTotales').setVisible(False)
        else:
            grid.Model.Height = 170
        try:
            pdf = CFDPDF(self)
            pdf.show = False
            pdf.printer = True
            pdf.generate_pdf(facturas, '', avance)
        except Exception as e:
            log.error('PRINT: ', exc_info=True)
        finally:
            if self.dm.chkDetalle.State:
                self.dialog.getControl('gridTotales').setVisible(True)
            else:
                grid.Model.Height = 184
        self.msg_user('Impresión finalizada')
        return

    def cmdPdf(self):
        avance =  self.dialog.getControl('pbCopia')
        sel = util.clear_sel(self.grid.SelectedRows)
        editar = bool(self.dm.chkEditar.State)
        if not sel:
            msg = 'Selecciona primero una factura'
            self.msg_user(msg)
            return
        destino = ''
        if self.dm.chkGuardar.State:
            destino = self.unogui.getFolder(self.util.getPathUser())
            if not destino:
                return
            self.grid.Model.Height = 170
        elif editar:
            if len(sel) > 1:
                msg = 'Selecciona solo una factura para editar'
                self.msg_user(msg)
                return
        if len(sel) > MOSTRAR_LIMITE:
            msg = 'Vas a generar %s documentos PDF.\n\n¿Estás seguro de ' \
                'continuar?' % len(sel)
            if not self.unogui.createQuestion('Factura Libre', msg):
                return
        avance.setRange(0, len(sel))
        facturas = []
        for row in sel:
            facturas.append(self.grid_dm.getCellData(0, row))
        try:
            pdf = CFDPDF(self)
            pdf.editar = editar
            rutas = self.db.select(('rutasespejo',), ('ruta',))
            pdf.espejos = rutas
            if destino:
                pdf.show = False
                pdf.espejos = ((destino,),)
            if pdf.generate_pdf(facturas, destino, avance):
                if destino:
                    msg = 'Pdfs generados correctamente en: {}'.format(destino)
                    self.msg_user(msg)
        except Exception as e:
            log.error('AdminCFDI - PDF: ', exc_info=True)
        finally:
            self.grid.Model.Height = 180
            avance.setVisible(False)
        return

    def cmdLimpiarSeleccion(self):
        grid = self.dialog.getControl('gridFacturas')
        grid.deselectAllRows()
        self.dm.suma.Value = 0
        return

    def cmdSeleccionarTodo(self):
        grid = self.dialog.getControl('gridFacturas')
        grid.selectAllRows()
        return

    def cmdPagada(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        #~ sel = grid.SelectedRows
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        message = '¿Estás seguro de marcar como pagadas las facturas seleccionadas?'
        if not self.unogui.createQuestion('Factura Libre', message):
            return
        for row in sel:
            id_cfd = grid_dm.getCellData(0, row)
            if grid_dm.getCellData(4, row) == 'Cancelada':
                message = 'Esta factura esta cancelda'
                self.msg_user(message)
                continue
            if grid_dm.getCellData(4, row) == 'Pagada':
                message = 'Esta factura ya esta pagada'
                self.msg_user(message)
                continue

            uuid = self.db.select(
                ('cfdfacturas',), ('uuid',), 'id=%s' % id_cfd)[0][0]
            if not uuid:
                message = 'Esta factura (CFDI) esta sin timbrar, solo es ' \
                    'posible cambiar el estatus a documentos timbrados'
                self.unogui.createMsgBox({'Message': message})
                continue

            #~ Modificamos el saldo del cliente cuando se marca como pagada
            try:
                self._saldo(
                    grid_dm.getCellData(10, row), grid_dm.getCellData(8, row))
            except Exception as e:
                log.error('AdminCFDI Pagada: ', exc_info=True)
            rows = self.db.update(
                'cfdfacturas', {'estatus': 'Pagada'}, "id=%s" % id_cfd)
            if rows:
                grid_dm.updateCellData(4, row, 'Pagada')
        return

    def cmdCancelada(self):
        avance =  self.dialog.getControl('pbCopia')
        grid = self.dialog.getControl('gridFacturas')
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        if len(sel) > 1:
            message = 'Selecciona solo una factura para cancelar'
            self.msg_user(message)
            return
        grid_dm = grid.Model.GridDataModel
        if grid_dm.getCellData(4, sel[0]) == 'Cancelada':
            message = 'Esta factura ya esta cancelda'
            self.msg_user(message)
            self._recuperar_acuse(sel[0])
            return
        id_cfd = grid_dm.getCellData(0, sel[0])
        # If is CBB or CFD
        where = 'cfdfacturas.id=%s' % id_cfd
        data = self.db.select(
            ('cfdfacturas',),
            ('noAprobacion', 'noCertificado'),
            where)[0]
        cbb = ''
        if data[0] and data[1]:
            cbb = 'LA FACTURA ES DEL ESQUEMA CFD\n\n'
        elif data[0] and not data[1]:
            cbb = 'LA FACTURA ES DEL ESQUEMA CBB\n\n'
        message = '%sFolio: %s\nReceptor: %s' % (
                        cbb,
                        grid_dm.getCellData(1, sel[0]),
                        grid_dm.getCellData(9, sel[0]))
        message = '%s\n\n¿Estás seguro de marcar como CANCELADA la factura' \
                ' seleccionada?\n\nEsta accion no se puede deshacer' % message
        if not self.unogui.createQuestion('Factura Libre', message):
            return
        if cbb:
            rows = self.db.update(
                'cfdfacturas',
                {'estatus': 'Cancelada'},
                'id=%s AND estatus<>"Cancelada"' % id_cfd)
            if rows:
                grid_dm.updateCellData(4, sel[0], 'Cancelada')
                message = 'Factura cancelada correctamente.'
                self.msg_user(message)
            return
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, es necesaria' \
                        ' para enviar a cancelar con el PAC los CFDI'
            self.unogui.createMsgBox({'Message': message})
            return
        rfc = self.db.select_field('certificado', 'rfc')
        uuid = self.db.select(
            ('cfdfacturas',), ('uuid',), 'id=%s' % id_cfd)[0][0]
        if not uuid:
            message = 'Esta factura (CFDI) esta sin timbrar, solo es posible ' \
                'cancelar documentos timbrados'
            self.unogui.createMsgBox({'Message': message})
            return
        #~ res, msg = self.util.cancel_cfdi(rfc, uuid, self.new_server)
        ok, estatus = util.cancela_multiple(rfc, uuid, self.new_server, not self.new_server)
        rows = 0
        if not ok:
            msg = 'No fue posible cancelar, la respuesta del PAC es:\n\n{}'.format(estatus)
            self.unogui.createMsgBox({'Message': msg})
            return
        rows = self.db.update(
            'cfdfacturas',
            {'estatus': 'Cancelada'},
            'id=%s AND estatus<>"Cancelada"' % id_cfd)
        if rows:
            #~ Modificamos el saldo del cliente cuando se marca como pagada
            try:
                self._saldo(
                    grid_dm.getCellData(10, sel[0]),
                    grid_dm.getCellData(8, sel[0]))
            except Exception as e:
                log.error('AdminCFDI Cancel: ', exc_info=True)

            rutas = self.db.select(('rutasespejo',), ('ruta',))
            try:
                if rutas:
                    pdf = CFDPDF(self)
                    pdf.editar = False
                    pdf.show = False
                    pdf.espejos = rutas
                    pdf.generate_pdf([id_cfd], '', avance)
            except:
                pass
            grid_dm.updateCellData(4, sel[0], 'Cancelada')
            fields = ('cfddetalle.noIdentificacion', 'cantidad')
            where = 'id_cfd=%s AND cfddetalle.noIdentificacion=' \
                    'productos.noIdentificacion AND inventario=1' % id_cfd
            data = self.db.select(('cfddetalle', 'productos'), fields, where)
            message = '.'
            if data:
                message += 'La factura cancelada tiene productos' \
                    ' con control de inventario.\n\n¿Deseas reingresarlos' \
                    ' al sistema?'
                if self.unogui.createQuestion('Factura Libre', message):
                    for r in data:
                        self.db.update(
                            'productos',
                            {'existencia': 'existencia+%s' % r[1]},
                            'noIdentificacion=%s' % r[0],
                            True)
                    message = ' y artículos reingresados correctamente.'
            message = 'Factura (CFDI) cancelada correctamente%s' % message
            self.unogui.createMsgBox({'Message': message})
        return

    def _recuperar_acuse(self, row):
        id_cfdi = self.grid_dm.getCellData(0, row)
        data = self.db.select(
            ('cfdfacturas',), ('uuid', 'xml_acuse'), 'id={}'.format(id_cfdi))[0]
        acuse = data[1]
        if acuse.startswith('No se'):
            acuse = ''
        if acuse:
            self._show_acuse(acuse, id_cfdi)
            return
        if data[0]:
            msg = 'Esta factura esta cancelada.\n\n¿Deseas intentar ' \
                'recuperar el acuse del SAT?\n\nRecuerda que debes de ' \
                'esperar al menos tres días después de cancelada para ' \
                'recuperar el acuse de cancelación'
            if util.question(msg) == BUTTON_CLICK['NO']:
                return
            rfc = self.db.select_field('certificado', 'rfc')
            #~ xml = util.get_acuse(rfc, data[0], self.new_server)
            ok, xml = util.recuperar_acuse(rfc, data[0], self.new_server, not self.new_server)
            if ok:
                self.db.update('cfdfacturas',
                    {'xml_acuse': xml}, 'id={}'.format(id_cfdi))
                self._show_acuse(xml, id_cfdi)
            else:
                util.msgbox(xml, TYPE_MSG['WARNING'])
        return

    def _show_acuse(self, xml, id_cfdi):
        pdf = PDFAcuse(self)
        pdf.generate_pdf(xml, id_cfdi)
        return

    def __filtrar(self, where=''):
        try:
            if where[0:5] == ' AND ':
                where = where[5:]
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
                'uuid', 'version'), where, 'fecha_timbrado', other1=pre)
            data_format = []
            suma_cfd = 0
            for row in data:
                total = self.format_s.format(row[5])
                tipo_cambio = self.format_s.format(row[7])
                suma_cfd += row[8]
                mn = self.format_s.format(row[8])
                row_format = (row[0], row[1], row[2], row[3], row[4], total,
                    row[6], tipo_cambio, mn, row[9], row[10])
                data_format.append(row_format)
            self.unogui.gridAddRows(self.dm.gridFacturas, data_format)
            self.dm.suma.Value = suma_cfd
            if data:
                #~ grid = self.dialog.getControl('gridFacturas')
                grid_dm = self.dm.gridFacturas.GridDataModel
                colors = []
                for i,v in enumerate(data):
                    grid_dm.updateCellToolTip(1, i, v[11])
                    if v[11] or float(v[12]) < 3:
                        colors.append(self.util.rgb(255,255,255))
                    elif v[4] == 'Validada':
                        colors.append(self.util.rgb(186,255,200))
                    else:
                        colors.append(self.util.rgb(255,204,153))
                self.dm.gridFacturas.RowBackgroundColors = tuple(colors)
                message = '%s Facturas encontradas' % len(data)
            else:
                message = 'No se encontraron facturas con estos criterios de busqueda'
            self.msg_user(message)
        except Exception as e:
            log.error('AdminCFDI - Filter: ', exc_info=True)
        return

    def txtReceptor_focusLost(self, source):
        self.dialog.getControl('gridReceptores').setVisible(False)
        return

    def txtReceptor_keyPressed(self, event):
        if event.KeyCode != KEY['RETURN'] and event.KeyCode != KEY['TAB']:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(True)
            self.dm.txtReceptor.Tag = ''
            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                self.dm.txtReceptor.Tag = ''
                grid.setVisible(False)
                return
            where = "nombre LIKE '%" + cliente + "%' OR rfc LIKE '%" + cliente + "%'"
            receptores = self.db.select(('receptores',), ('id', 'rfc', 'nombre'), where, 'nombre')
            self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
        return

    def txtReceptor_keyReleased(self, event):
        if event.KeyCode == KEY['RETURN']:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(False)
            self.dm.txtReceptor.Tag = ''

            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                row_count = self.db.count('receptores')
                if row_count < CLIENTES_COUNT:
                    receptores = self.db.select(('receptores',), ('id', 'rfc', 'nombre'), 'activo=1', 'nombre')
                    self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
                    grid.setFocus()
                    grid.setVisible(True)
                    return
                else:
                    message = 'Captura la clave del cliente a buscar.'
                    #~ self.unogui.createMsgBox({'Message': message})
                    self.msg_user(message)
                    return
            try:
                id_cliente = int(cliente)
                receptor = self.db.select(('receptores',), where='id=%s AND activo=1' % id_cliente)
                if receptor:
                    receptor = receptor[0]
                    self.dm.txtReceptor.Tag = receptor[0]
                    self.dm.txtReceptor.Text = receptor[2]
                else:
                    message = 'No se encontró el receptor con la clave: %s' % id_cliente
                    #~ self.unogui.createMsgBox({'Message': message})
                    self.msg_user(message)
            except ValueError as e:
                message = 'Asegurate de capturar un valor entero para buscar por clave del cliente'
                #~ self.unogui.createMsgBox({'Message': message})
                self.msg_user(message)
        return

    def gridReceptores_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            receptor = self.db.select(('receptores',), ('id', 'nombre'),where='id=%s' % grid_dm.getCellData(0, row))[0]
            self.dm.txtReceptor.Tag = receptor[0]
            self.dm.txtReceptor.Text = receptor[1]
            grid.setVisible(False)
        return

    def gridFacturas_selectionChanged(self, grid):
        self.id_addenda = 0
        self.id_cfd = 0
        self.dm.cmdEnviar.Enabled = False
        self.dm.cmdAddenda.Enabled = False
        self.dm.cmdNotas.Enabled = False
        self.dm.cmdCamposPersonalizados.Enabled = False
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        self.__sum_cfd(sel)
        if len(sel) == 1:
            self.dm.cmdEnviar.Enabled = True
            self.dm.cmdNotas.Enabled = True
            self.dm.cmdCamposPersonalizados.Enabled = True
            self.id_cfd = grid_dm.getCellData(0, sel[0])
            self.__get_nota(self.id_cfd)
            if self.dm.chkDetalle.State:
                self.__get_detalle(self.id_cfd)
            data = self.db.select(('receptores', 'cfdfacturas'),
                ('id_addenda',),
                'cfdfacturas.id=%s AND id_cliente=receptores.id' % self.id_cfd)
            self.id_addenda = data[0][0]
            if self.id_addenda:
                data = self.db.select(('asignaciones', ),
                                    ('id',),
                                    'id_addenda=%s' % self.id_addenda)
                if data:
                    self.dm.cmdAddenda.Enabled = True
        return

    def __sum_cfd(self, sel):
        if not sel:
            return
        grid_dm = self.dm.gridFacturas.GridDataModel
        self.dm.gridDetalle.GridDataModel.removeAllRows()
        self.dm.gridTotales.GridDataModel.removeAllRows()
        total = 0
        for f in sel:
            value = grid_dm.getCellData(8, f).replace(',', '')
            total += float(value)
        self.dm.suma.Value = total
        return

    def __get_nota(self, id_cfd):
        data = self.db.select(('cfdfacturas',), ('notas',), 'id=%s' % id_cfd)[0]
        self.dm.cmdNotas.Tag = data[0]
        return

    def __get_detalle(self, id_cfd):
        grid_dm = self.dm.gridDetalle
        grid_dm.GridDataModel.removeAllRows()
        fields = (
            'id',
            'noIdentificacion',
            'unidad',
            'descripcion',
            'cantidad',
            'valorUnitario',
            'importe',
            'numero',
            'fecha',
            'aduana',
            'CuentaPredial')
        data = self.db.select(('cfddetalle',), fields, 'id_cfd=%s' % id_cfd)
        data_format = []
        for row in data:
            cantidad = self.format_s.format(row[4])
            pu = self.format_s.format(row[5])
            importe = self.format_s.format(row[6])
            row_format = (row[0], row[1], row[2], row[3], cantidad, pu, importe)
            data_format.append(row_format)
        self.unogui.gridAddRows(grid_dm, data_format)

        fields = (
            'subTotal',
            'descuento',
            'total',
            'motivoDescuento',
            'notas')
        data = self.db.select(('cfdfacturas',), fields, 'id=%s' % id_cfd)[0]
        fields = (
            'nombre',
            'tasa',
            'importe')
        taxes = self.db.select(('cfdimpuestos',), fields, 'id_cfd=%s' % id_cfd)

        columns = [{'Title': 'SubTotal', 'ColumnWidth': 60, 'HorizontalAlign': 2}]
        rows = [self.format_s.format(data[0])]
        if data[1]:
            columns.append({'Title': 'Descuento', 'ColumnWidth': 60, 'HorizontalAlign': 2})
            rows.append(self.format_s.format(data[1]))
        self.dm.cmdNotas.Tag = data[4]

        for tax in taxes:
            col = {}
            col['Title'] = '%s al %s' % (tax[0], tax[1])
            col['ColumnWidth'] = 60
            col['HorizontalAlign'] = 2
            columns.append(col)
            importe_s = self.format_s.format(tax[2])
            rows.append(importe_s)
        col = {'Title': 'TOTAL', 'ColumnWidth': 60, 'HorizontalAlign': 2}
        columns.append(col)
        total = self.format_s.format(data[2])
        rows.append(total)
        self.unogui.gridChangeColumn(self.dm.gridTotales, columns)
        self.unogui.gridAddRows(self.dm.gridTotales, (tuple(rows),))
        self.dm.gridTotales.GridDataModel.updateCellToolTip(1, 0, data[3])
        return

    def cmdNotas(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)[0]
        self.value = ''
        msg = 'Edición de notas de la factura: {}'.format(
            grid_dm.getCellData(1, sel))
        input_box = inputbox2.Dlg(self, (msg, self.dm.cmdNotas.Tag))
        res = input_box.execute()
        if res:
            id_cfd = grid_dm.getCellData(0, sel)
            self.db.update(
                'cfdfacturas', {'notas': self.value}, 'id={}'.format(id_cfd))
            self.dm.cmdNotas.Tag = self.value
        return

    def cmdReporte(self):
        try:
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            if not grid_dm.RowCount:
                message = 'No hay facturas a reportar'
                self.unogui.createMsgBox({'Message': message})
                return
            doc = self.util.newDoc()
            sheet = doc.getSheets().getByIndex(0)
            data, titles = self.grid_to_tuple(grid.Model)
            oRange = sheet.getCellRangeByPosition(0, 0, len(data[0])-1, 0)
            self.__format_title(oRange)
            oRange.setDataArray((titles,))
            oRange = sheet.getCellRangeByPosition(0, 1, len(data[0])-1, len(data))
            oRange.setDataArray(data)
            self.__format_columns(oRange, len(data[0]), len(data)-1)
        except Exception as e:
            log.error('AdminCFDI - Report: ', exc_info=True)
        return

    def __format_title(self, rango):
        rango.CharWeight = 150
        rango.VertJustify = 2
        rango.HoriJustify = 2
        return

    def __format_columns(self, rango, num_col, num_fil):
        col = rango.getCellRangeByPosition(1, 0, 1, num_fil)
        col.NumberFormat = 37
        col = rango.getCellRangeByPosition(4, 0, 4, num_fil)
        col.NumberFormat = 104
        if num_col > 6:
            col = rango.getCellRangeByPosition(6, 0, 7, num_fil)
            col.NumberFormat = 104
        return

    def grid_to_tuple(self, grid):
        grid_dm = grid.GridDataModel
        col_m = grid.ColumnModel
        col = grid_dm.ColumnCount
        fil = grid_dm.RowCount
        data = []
        titles = []
        for f in range(fil):
            row = []
            for c in range(1, col-1):
                column = col_m.getColumn(c)
                if not column.ColumnWidth:
                    continue
                if f == 0:
                    titles.append(column.Title)
                if c == 2:
                    #~ row.append(self.util.date_to_calc(grid_dm.getCellData(c, f)))
                    row.append(grid_dm.getCellData(c, f))
                elif c == 5 or c == 7 or c == 8:
                    value = grid_dm.getCellData(c, f).replace(',', '')
                    row.append(float(value))
                else:
                    row.append(grid_dm.getCellData(c, f))
            data.append(tuple(row))
        return tuple(data), tuple(titles)

    def cmdCorreo(self):
        mail_server = {}
        sel = self.util.clear_sel(self.grid.SelectedRows)
        if not sel:
            msg = 'Selecciona primero una factura'
            self.msg_user(msg)
            return
        send_mail = self.enviar_correo
        if send_mail == SEND_MAIL['ASK']:
            msg = 'Selecciona una opción para enviar estas facturas\n\n' \
                'SI = Usa el cliente de correo predeterminado\n' \
                'NO = Envía el correo directamente\n' \
                'CANCELAR = Salir sin enviar'
            send_mail = util.question(msg, BUTTONS['YES_NO_CANCEL'])
            if not send_mail:
                return
        else:
            msg = '¿Estás seguro de enviar por correo las facturas seleccionadas?'
            if not util.question(msg):
                return

        email_server = self.db.select(('correo',))
        if email_server:
            email_server = email_server[0]
        if send_mail == SEND_MAIL['SMTP'] and not email_server:
            msg = 'Se requiere configurar primero los datos del servidor de' \
                'de salida para enviar correo directamente\n\nNo se enviará ' \
                'ninguna factura'
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return
        elif send_mail == SEND_MAIL['SMTP']:
            server_ok = (email_server[1] and email_server[2]
                and email_server[3] and email_server[4])
            if not server_ok:
                msg = 'La configuracion del servidor de correo de salida ' \
                    'esta incompleta. No podras enviar correos directamente ' \
                    'hasta tener correcta esta configuracion'
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return
        if email_server:
            mail_server['server'] = email_server[1]
            mail_server['port'] = email_server[2]
            mail_server['user'] = email_server[3]
            mail_server['pass'] = email_server[4]
            mail_server['copy'] = email_server[5]
            mail_server['subject'] = email_server[6]
            mail_server['body'] = email_server[7]
            mail_server['ssl'] = email_server[8]
        paths = self.db.select(('rutasespejo',), ('ruta',))
        co1 = 0
        for row in sel:
            id_cfdi = self.grid_dm.getCellData(0, row)
            client = self.grid_dm.getCellData(9, row)
            where = 'id_cliente=(SELECT id_cliente FROM cfdfacturas ' \
                'WHERE id={})'.format(id_cfdi)
            mails_to = self.db.select(('correos',), ('correo',), where)
            to = [mail[0] for mail in mails_to]
            if send_mail == SEND_MAIL['SMTP'] and not to:
                msg = 'Cliente: {}, sin correo de envio'.format(client)
                log.info(msg)
                self.msg_user(msg)
                continue
            path_xml, path_pdf = self._get_paths_files(id_cfdi, paths)
            info = {
                'files': (path_xml, path_pdf),
                'mail_server': mail_server,
                'receivers': to
            }
            try:
                if send_mail == SEND_MAIL['USE_CLIENT']:
                    send = util.send_mail_client(info)
                elif send_mail == SEND_MAIL['SMTP']:
                    send, msg = util.send_mail(info)
                    if send:
                        co1 += 1
                    else:
                        log.error(msg)
            except:
                log.error('Mail: ', exc_info=True)
        self.msg_user('Proceso terminado...')
        if send_mail == SEND_MAIL['SMTP']:
            msg = 'Facturas seleccionadas = {}\n' \
                'Facturas enviadas = {}'.format(len(sel), co1)
            util.msgbox(msg)
        return

    def _get_paths_files(self, id_cfdi, paths):
        ext_xml = '.xml'
        ext_pdf = '.pdf'
        name = "serie || substr('000000' || folio, -6, 6) || '_' || rfc"
        where = 'cfdfacturas.id_cliente=receptores.id AND cfdfacturas.id={}'.format(id_cfdi)
        data = self.db.select(
            ('cfdfacturas', 'receptores'),
            ("strftime('%Y',fecha_timbrado)",
                "strftime('%m',fecha_timbrado)", name, 'xml'),
            where)[0]
        if paths:
            for path in paths:
                path_xml = self.util.join(path[0], data[0])
                path_xml = self.util.join(path_xml, data[1])
                path_xml = self.util.join(path_xml, data[2] + ext_xml)
                path_pdf = path_xml.replace(ext_xml, ext_pdf)
                if util.exists(path_xml) and util.exists(path_pdf):
                    return path_xml, path_pdf
        path_xml = util.get_path_temp(data[2] + ext_xml)
        util.save_file(path_xml, data[3])
        pdf = CFDPDF(self)
        pdf.show = False
        pdf.generate_pdf((id_cfdi,), '')
        path_pdf = pdf.path_pdf
        return path_xml, path_pdf

    def chkDetalle(self, source):
        grid = self.dialog.getControl('gridFacturas')
        h = 180
        if source.State:
            h = 75
        self.dialog.getControl('gridDetalle').setVisible(source.State)
        self.dialog.getControl('gridTotales').setVisible(source.State)
        grid.Model.Height = h
        return

    def chkGuardar(self, source):
        if source.State:
            self.dm.chkEditar.State = False
            self.dm.cmdPdf.ImageURL = self.img_url + ICONS['PDF']
        return

    def chkEditar(self, source):
        if source.State:
            self.dm.chkGuardar.State = False
            icon_url = self.img_url + ICONS['CALC']
        else:
            icon_url = self.img_url + ICONS['PDF']
        self.dm.cmdPdf.ImageURL = icon_url
        return

    def lstAno_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def lstMes_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def lstEstatus_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def txtCfd_keyPressed(self, event):
        if event.KeyCode == KEY['RETURN'] or event.KeyCode == KEY['TAB']:
            return
        folio = event.Source.Text.strip()
        if not folio:
            return
        #~ where = 'cfdfacturas.id_cliente=receptores.id'
        where = "serie||folio LIKE '%" + folio.upper() + "%'"
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
            'nombre'), where, 'fecha_timbrado', other1=pre)
        data_format = []
        suma_cfd = 0
        for row in data:
            total = self.format_s.format(row[5])
            tipo_cambio = self.format_s.format(row[7])
            suma_cfd += row[8]
            mn = self.format_s.format(row[8])
            row_format = (row[0], row[1], row[2], row[3], row[4], total,
                            row[6], tipo_cambio, mn, row[9])
            data_format.append(row_format)
        self.unogui.gridAddRows(self.dm.gridFacturas, data_format)
        return

    def txtCfd_keyRelease(self, event):
        pass

    def cmdCamposPersonalizados(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)[0]
        #~ sel = grid.SelectedRows[0]
        id_cfd = grid_dm.getCellData(0, sel)
        message = '%s - $%s - %s' % (
                            grid_dm.getCellData(1, sel),
                            grid_dm.getCellData(8, sel),
                            grid_dm.getCellData(9, sel))
        dlg = campos.Dlg(self, (id_cfd, message))
        dlg.execute()
        return

    def cmdReportes(self):
        #~ patron = re.compile('([^{}]*)}')
        patron = util.get_patron()
        lst = self.dialog.getControl('lstReportes')
        if not lst.SelectedItemPos:
            message = 'Selecciona un reporte a emitir'
            #~ self.unogui.createMsgBox({'Message': message})
            self.msg_user(message)
            return
        name = lst.SelectedItem
        sql = self.db.select(('reportes',),
                            ('sql',),
                            "nombre='%s'" % name)[0][0]
        sql = sql.replace("''", "'")
        parametros = patron.findall(sql)
        if parametros:
            for p in parametros:
                self.value = ''
                message = 'Captura el valor para el parámetro:\n\n%s =' % p
                input_box = inputbox.Dlg(self, (message, False))
                if not input_box.execute():
                    message = 'Son necesarios todos los parametros'
                    self.unogui.createMsgBox({'Message': message})
                    return
                sql = sql.replace('{%s}' % p, self.value)
        data = self.db.execute(sql)
        if not data:
            message = 'Este reporte no devolvio ningun dato'
            self.unogui.createMsgBox({'Message': message})
            return

        cols = {}
        for i, v in enumerate(data[0]):
            #~ if type(v) is datetime.datetime:
            if util.is_date(v):
                cols[i] = True
        if cols:
            data_array = []
            for r in data:
                line = []
                for i,v in enumerate(r):
                    if i in cols:
                        line.append(v.toordinal() - 693594)
                    else:
                        line.append(v)
                data_array.append(tuple(line))
            data = data_array
        doc = self.util.newDoc()
        sheet = doc.getSheets().getByIndex(0)
        oRange = sheet.getCellRangeByPosition(0, 0, len(data[0])-1, len(data)-1)
        oRange.setDataArray(tuple(data))
        self.__format_columns_date(oRange, cols, len(data)-1)
        return

    def __format_columns_date(self, rango, dates, num_fil):
        if dates:
            for c in list(dates.keys()):
                col = rango.getCellRangeByPosition(c, 0, c, num_fil)
                col.NumberFormat = 37
        return

    def cmdXml(self):
        export = 0
        try:
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            #~ sel = grid.SelectedRows
            sel = self.util.clear_sel(grid.SelectedRows)
            if not sel:
                message = 'Selecciona primero una factura'
                self.msg_user(message)
                return
            destino = ''
            if self.dm.chkGuardar.State:
                destino = self.unogui.getFolder(self.util.getPathUser())
                destino = destino.strip()
                if not destino:
                    return
            format_s = self.db.get_option('file_name')
            for row in sel:
                if row < 0: continue
                id_cfd = grid_dm.getCellData(0, row)
                factura = grid_dm.getCellData(1, row)
                # If is CBB or CFD
                data = self.db.select(
                    ('cfdfacturas',),
                        ('substr(version, 1, 1)',
                        'serie || folio',
                        "strftime('%Y',fecha_timbrado)",
                        "strftime('%m',fecha_timbrado)",
                        'xml', 'uuid', 'estatus'),
                    'id=%s' % id_cfd)[0]
                self.msg_user('Verificando factura: %s' % data[1])
                if data[0] == '1':
                    # Esquema CBB
                    message = 'La factura: %s es del esquema CBB, no cuenta ' \
                                'con XML' % data[1]
                    self.unogui.createMsgBox({'Message': message})
                    continue
                elif data[0] == '2':
                    # Esquema CFD
                    self._fac_cfd(id_cfd, data[4], data[1], destino)
                    continue
                if data[4] and data[5]:
                    if destino:
                        name = self.util.get_name(data[4], format_s, FILE_NAME)
                        copy_data = {
                            'year': data[2],
                            'month': data[3],
                            'xml': data[4],
                            'name': '%s.xml' % name
                        }
                        util.copy_xml(copy_data,((destino,),))
                        export += 1
                        self.msg_user('Guardando factura: %s' % data[1])
                    else:
                        self.__copiar_xml(id_cfd)
                        self._update_info_fac(id_cfd, row)
                        message = 'CFDI timbrado correctamente'
                        #~ self.unogui.createMsgBox({'Message': message})
                        self.msg_user(message)
                    continue
                else:
                    message = 'Parece que esta factura: %s no esta timbrada.' \
                        '\n\n¿Deseas verificarla con el PAC?' % data[1]
                    if data[6] == 'Guardada':
                        ok, xml = self.__generar_xml(id_cfd)
                        if not ok:
                            message = 'No se pudo generar el XMl de la ' \
                                'Factura: %s\n\nConsulta a soporte ' \
                                'técnico' % data[1]
                            self.unogui.createMsgBox({'Message': message})
                            continue
                    elif data[6] == 'Enviada':
                        ok, xml = self.__generar_xml(id_cfd)
                        message = 'La factura: %s fue enviada anteriormente con ' \
                            'el PAC, pero no parece estar timbrada. \n\n ¿Deseas ' \
                            'verificarla con el PAC' % data[1]
                    if not self.unogui.createQuestion('Factura Libre', message):
                        continue
                    if self._timbrada(data, id_cfd, row, destino):
                        continue
            #~ self.msg_user('Proceso terminado...')
            if destino and export:
                message = 'Documentos exportados correctamente'
                self.unogui.createMsgBox({'Message': message})
        except Exception as e:
            log.error('AdminCFDI - XML: ', exc_info=True)
        return

    def _fac_cfd(self, id_cfdi, xml, fac, destino):
        if xml:
            if destino:
                #~ self.__copiar_xml(id_cfdi)
                self.util.copy_xml(factura[2:], (destino,))
            else:
                self.__copiar_xml(id_cfdi)
                msg = 'La factura: %s es del esquema CFD, XML correcto' % fac
                self.unogui.createMsgBox({'Message': msg})
        else:
            msg = 'No se encontró el XML de la factura: %s\n\nConsulta ' \
                        'a soporte tecnico' % fac
            self.unogui.createMsgBox({'Message': msg})
        return

    def _enviar_timbrar(self, xml, id_cfd, row):
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, el CFDI ya ' \
                'ha sido generado y guardado en la base de datos, pero no se ' \
                'podrá timbrar hasta volver a tener conexión a internet, se ' \
                'recomienda esperar hasta resolver este problema'
            self.unogui.createMsgBox({'Message': message})
            return False
        rfc = self.db.select_field('certificado', 'rfc')
        if not xml:
            _,xml = self.__generar_xml(id_cfd)
        tmp = self.db.select(('cfdfacturas',), ('fecha',), 'id=%s' % id_cfd)[0][0]
        id_timbrado = self.util.get_epoch(tmp)
        #~ ok, data = self.util.timbrar(rfc, xml, id_timbrado, self.new_server)
        ok, data = util.timbra_xml(rfc, xml, id_timbrado, self.new_server, not self.new_server)
        if ok:
            self.db.update(
                'cfdfacturas',
                {'xml': data['xml'], 'uuid': data['uuid'],
                    'fecha_timbrado': data['fecha'], 'estatus': 'Por pagar'},
                'id=%s' % id_cfd)
            d = self.util.format_date(
                data['fecha'], '%d-%b-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S')
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            grid_dm.updateCellData(2, row, d)
            grid_dm.updateCellData(4, row, 'Por pagar')

            colors = list(self.dm.gridFacturas.RowBackgroundColors)
            colors[row] = self.util.rgb(255,255,255)
            self.dm.gridFacturas.RowBackgroundColors = tuple(colors)

            path_pdf = self.__create_pdf(id_cfd)
            self.__copiar_xml(id_cfd, path_pdf)
            return True
        else:
            self.unogui.createMsgBox({'Message': data})
            return False

    def __create_pdf(self, id_cfd, show=True):
        pdf = CFDPDF(self)
        pdf.show = show
        pdf.generate_pdf((id_cfd,))
        return pdf.path_pdf

    def __copiar_xml(self, id_cfd, path_pdf=''):
        data = self.db.select(
            ('cfdfacturas',),
            ("strftime('%Y',fecha_timbrado)",
                "strftime('%m',fecha_timbrado)", 'xml'),
            'id=%s' % id_cfd)[0]
        path_xml = ''
        rutas = self.db.select(('rutasespejo',), ('ruta',))
        if rutas:
            format_s = self.db.get_option('file_name')
            name = self.util.get_name(data[2], format_s, FILE_NAME)
            xml = self._special_case_addenda(data[2])
            data = {
                'year': data[0],
                'month': data[1],
                'xml': xml,
                'name': '%s.xml' % name
            }
            #~ path_xml = self.util.copy_xml(data, rutas, path_pdf)
            path_xml = util.copy_xml(data, rutas, path_pdf)
        return

    def _special_case_addenda(self, xml):
        new_data = xml
        if 'sanofi:sanofi' in xml:
            s1 = 'xmlns:sanofi="https://mexico.sanofi.com/schemas" '
            s2 = '<sanofi:sanofi version="1.0"'
            r1 = '<sanofi:sanofi xmlns:sanofi="https://mexico.sanofi.com/schemas" ' \
                'version="1.0"'
        elif '<AIG>' in xml:
            s1 = 'xmlns="http://www.azurian.com" '
            s2 = '<AIG>'
            r1 = '<AIG xmlns="http://www.azurian.com">'
        else:
            return new_data
        new_data = new_data.replace(s1, '', 1).replace(s2, r1, 1)
        return new_data

    def __generar_xml(self, id_cfd):
        cfd = CFDXML(self, id_cfd)
        xml = cfd.generate_xml()
        self.db.update('cfdfacturas', {'xml': xml}, 'id=%s' % id_cfd)
        return True, xml

    def _timbrada(self, data, id_cfd, row, destino=''):
        xml = data[4]
        if xml:
            xml = ET.fromstring(xml.encode('UTF-8'))
            timbre = xml.find('{}Complemento'.format(PRE[xml.attrib['version']]))
            if timbre is not None:
                timbre = timbre.find('{}TimbreFiscalDigital'.format(PRE['TIMBRE']))
                if timbre is not None:
                    uuid = timbre.attrib['UUID']
                    self.db.update('cfdfacturas',
                        {'uuid': uuid, 'estatus': 'Por pagar'}, 'id=%s' % id_cfd)
                    message = 'Factura verificada correctamente, ya puedes ' \
                        'exportarla de nuevo'
                    self.unogui.createMsgBox({'Message': message})
                    return True
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, se ' \
                'requiere para verificar la factura con el PAC.'
            self.unogui.createMsgBox({'Message': message})
            return False
        #~ xml = data[4]
        exists = False
        tmp = self.db.select(('cfdfacturas',), ('fecha',), 'id=%s' % id_cfd)[0][0]
        id_timbrado = self.util.get_epoch(tmp)
        #~ ok, res = self.util.status_xml(self.rfc, id_timbrado, self.new_server)
        ok, res = util.estatus_timbrado(self.rfc, id_timbrado, self.new_server, not self.new_server)
        if not ok:
            self.unogui.createMsgBox({'Message': res})
            return False
        #~ Recuperar
        if res['Codigo'] == '600' or res['Codigo'] == '602':
            return self._recuperar_xml(
                self.rfc, id_timbrado, res['Codigo'], row, id_cfd)
        elif res['Codigo'] == '605':
            if not xml:
                ok, xml = self.__generar_xml(id_cfd)
                if not ok:
                    message = 'No se pudo generar el XMl de la Factura: ' \
                        '%s\n\nConsulta a soporte técnico' % data[1]
                    self.unogui.createMsgBox({'Message': message})
                    return False

        #~ if data[6] == 'Enviada':
            #~ ok, res = self.util.status_xml(
                #~ self.rfc, id_timbrado, self.new_server)
            #~ if not ok:
                #~ self.unogui.createMsgBox({'Message': res})
                #~ return False
            #~ Recuperar
            #~ if res['Codigo'] == '600' or res['Codigo'] == '602':
                #~ return self._recuperar_xml(
                    #~ self.rfc, id_timbrado, res['Codigo'], row, id_cfd)
            #~ elif res['Codigo'] == '605':
                #~ if not xml:
                    #~ ok, xml = self.__generar_xml(id_cfd)
                    #~ if not ok:
                        #~ message = 'No se pudo generar el XMl de la ' \
                            #~ 'Factura: %s\n\nConsulta a soporte ' \
                            #~ 'técnico' % data[1]
                        #~ self.unogui.createMsgBox({'Message': message})
                        #~ return False
                #~ exists = False

        #~ if data[6] == 'Generada' or not exists:
        if not exists:
            #~ msg = 'La factura: %s no esta timbrada. \n\n¿Deseas enviarla a ' \
                #~ 'timbrar con el PAC?. \n\nIMPORTANTE: la fecha y hora serán ' \
                #~ 'actualizadas automáticamente.\n\n¿Deseas enviarla?' % data[1]
            msg = 'La factura: %s no esta timbrada.\n\n¿Deseas enviarla a ' \
                'timbrar con el PAC?.\n\nIMPORTANTE: La fecha de la factura ' \
                'debe estar dentro de las pasadas 72 horas, de lo contrario ' \
                'será rechazada.\n\n¿Deseas enviarla?' % data[1]
            if not self.unogui.createQuestion('Factura Libre', msg):
                return False
            ok, xml = self.__generar_xml(id_cfd)
            if self._enviar_timbrar(xml, id_cfd, row):
                message = 'La factura se timbro correctamente y se ha ' \
                    'guardado en la base de datos.'
                self.unogui.createMsgBox({'Message': message})
                return True
        return False

    def _recuperar_xml(self, rfc, id_timbrado, codigo, row, id_cfd):
        #~ ok, data = self.util.get_xml(rfc, id_timbrado, self.new_server)
        ok, data = util.obtener_timbrado(rfc, id_timbrado, self.new_server, not self.new_server)
        if ok:
            xml = ET.fromstring(data)
            fecha = xml.attrib['fecha'].replace('T',' ')
            timbre = xml.find('{}Complemento'.format(PRE[xml.attrib['version']]))
            timbre = timbre.find('{}TimbreFiscalDigital'.format(PRE['TIMBRE']))
            fecha = timbre.attrib['FechaTimbrado'].replace('T',' ')
            campos = {}
            campos['fecha_timbrado'] = fecha
            campos['xml'] = data
            campos['uuid'] = timbre.attrib['UUID']
            campos['estatus'] = 'Por pagar'
            #~ estatus = 'Por pagar'
            if codigo == '602':
                campos['estatus'] = 'Cancelada'
                #~ estatus = 'Cancelada'
            d = self.util.format_date(
                fecha, '%d-%b-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S')
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            grid_dm.updateCellData(2, row, d)
            grid_dm.updateCellData(4, row, campos['estatus'])
            self.db.update('cfdfacturas',  campos, 'id=%s' % id_cfd)
            path_pdf = self.__create_pdf(id_cfd)
            self.__copiar_xml(id_cfd, path_pdf)
            return True
        return False

    #~ def chkGuardar(self, source):
        #~ if source.State:
            #~ self.dm.chkEditar.State = False
        #~ return

    def cmdAddenda(self):
        from facturalibre.modulos.pyXml import AGREGARADDENDA

        data = self.db.select(('asignaciones', ),
                                ('origen2', 'destino2'),
                                'id_addenda=%s' % self.id_addenda)
        perso = self.db.select(('cfdpersonalizados', ),
                                ('campo', 'valor'),
                                'id_cfd=%s' % self.id_cfd)
        xml = self.db.select(('cfdfacturas',),
                                ('xml',),
                                'id=%s' % self.id_cfd)[0][0]
        addenda = self.db.select(('addendas',),
                                ('addenda', 'nombre'),
                                'id=%s' % self.id_addenda)[0]
        name_addenda = addenda[1]
        try:
            aa = AGREGARADDENDA(xml, addenda[0])
            if aa.msg:
                msg = '%s\n\n¿Estás seguro de reemplazarla?' % aa.msg
                if not self.unogui.createQuestion('Factura Libre', msg):
                    return
                aa.msg = ''
            xml = ''
            if aa.add_data(data, perso):
                xml = aa.tostring()
                #~ xml = self._special_case_addenda(xml, name_addenda)
                self.db.update('cfdfacturas',
                                {'xml': xml},
                                'id=%s' % self.id_cfd)
                self.__copiar_xml(self.id_cfd)
                msg = 'Addenda agregada correctamente a la ' \
                    'factura seleccionada'
            else:
                msg = aa.msg
            self.unogui.createMsgBox({'Message': msg})
        except Exception as e:
            log.error('AdminCFDI - Addenda', exc_info=True)
        return

    def _saldo(self, id_cliente, total, sumar=False):
        if isinstance(total, str):
            importe = float(total.replace(",", ""))
        else:
            importe = total
        if sumar:
            importe *= -1
        self.db.update(
            'receptores',
            {'saldoCliente': 'saldoCliente - ({})'.format(importe)},
            'id=%s' % id_cliente,
            True)
        return

    def cmdSat(self):
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, es necesaria' \
                        ' para enviar para consultar el estatus en el SAT'
            self.unogui.createMsgBox({'Message': message})
            return
        if DEBUG:
            msg = 'Estas usando el sistema de pruebas de Factura Libre. ' \
                'Cualquier consulta al SAT te devolverá el mensaje: No ' \
                'encontrado'
            self.unogui.createMsgBox({'Message': msg})

        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        #~ sel = grid.SelectedRows
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        if len(sel) > 1:
            message = 'Selecciona solo una factura'
            self.msg_user(message)
            return

        id_cfdi = grid_dm.getCellData(0, sel[0])
        fac = grid_dm.getCellData(1, sel[0])
        xml = self.db.select(
            ('cfdfacturas',), ('xml',), 'id=%s' % id_cfdi)[0][0]

        ok, msg = util.get_status_sat(xml)
        if not ok:
            util.msgbox(msg, TYPE_MSG['ERROR'])
            return

        msg = 'Factura (CFDI): {}\n\nEstatus en SAT: {}'.format(fac, msg)
        util.msgbox(msg)

        status = grid_dm.getCellData(4, sel[0])
        if status == 'Cancelada' and 'Vigente' in msg:
            msg = 'La tienes cancelada en el sistema, pero aparece vigente ' \
                'en el SAT. ¿Deseas enviar de nuevo a cancelar?'
            message = 'La Factura: %s\n\n%s' % (fac, msg)
            if not self.unogui.createQuestion('Factura Libre', message):
                return
            rfc = self.db.select_field('certificado', 'rfc')
            uuid = self.db.select(
                ('cfdfacturas',), ('uuid',), 'id=%s' % id_cfdi)[0][0]
            #~ res, msg = self.util.CancelaComprobante(rfc, uuid)
            #~ res, msg = self.util.cancel_cfdi(rfc, uuid, self.new_server, not self.new_server)
            ok, msg = util.cancela_multiple(rfc, uuid, self.new_server, not self.new_server)
            if not ok:
                #~ self.unogui.createMsgBox({'Message': est})
                util.msgbox(msg, TYPE_MSG['ERROR'])
                return

            msg = 'Solicitud de cancelación enviada correctamente, por favor, ' \
                'valida de nuevo ante el SAT en unos días'
            #~ self.unogui.createMsgBox({'Message': msg})
            util.msgbox(msg)

        elif status != 'Cancelada' and 'Cancelado' in msg:
            msg = 'El documento esta Cancelado en el SAT, pero no en el  ' \
                'sistema. Enviar de nuevo a cancelar debería resolver esta ' \
                'diferencia.'
            #~ self.unogui.createMsgBox({'Message': msg})
            util.msgbox(msg)
        return

    def _update_info_fac(self, id_cfdi, row):
        data = self.db.select(('cfdfacturas',), ('xml',), 'id=%s' % id_cfdi)[0]
        xml = ET.fromstring(data[0])
        timbre = xml.find('{}Complemento'.format(PRE[xml.attrib['version']]))
        timbre = timbre.find('{}TimbreFiscalDigital'.format(PRE['TIMBRE']))
        fecha = timbre.attrib['FechaTimbrado'].replace('T', ' ')
        campos = {}
        campos['fecha_timbrado'] = fecha
        fecha = self.util.format_date(
            fecha, '%d-%b-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S')
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        grid_dm.updateCellData(2, row, fecha)
        self.db.update('cfdfacturas', campos, 'id=%s' % id_cfdi)
        return

    def cmdRefacturar(self):
        self.dm.chkDetalle.State = 0
        self.chkDetalle(self.dm.chkDetalle)
        avance = self.dialog.getControl('pbCopia')
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        msg = 'Vas a refacturar {} documento(s).\n\n¿Estás seguro de ' \
            'continuar?'.format(len(sel))
        if util.question(msg) == BUTTON_CLICK['NO']:
            return
        grid.Model.Height = 170
        avance.setRange(0, len(sel))
        facturas = []
        for row in sel:
            id_cfdi = grid_dm.getCellData(0, row)
            facturas.append(id_cfdi)
        try:
            self._copy_cfdi(facturas, avance)
            self.cmdTimbrar()
        except Exception as e:
            log.error('AdminCFDI - Refac: ', exc_info=True)
        finally:
            grid.Model.Height = 180
            avance.setVisible(False)
        return

    def _copy_cfdi(self, facturas, pb):
        fields = (
            'id',
            'noCertificado',
            'LugarExpedicion',
            'Moneda',
            'NumCtaPago',
            'TipoCambio',
            'certificado',
            'condicionesDePago',
            'descuento',
            'donativo',
            'estatus',
            'folio',
            'formaDePago',
            'id_cliente',
            'id_folio',
            'metodoDePago',
            'motivoDescuento',
            'notas',
            'regimen',
            'serie',
            'subTotal',
            'tipoDeComprobante',
            'total',
            'totalImpuestosRetenidos',
            'totalImpuestosTrasladados',
            'version',
        )
        fields2 = (
            'id_cfd',
            'categoria',
            'cantidad',
            'unidad',
            'noIdentificacion',
            'descripcion',
            'valorUnitario',
            'importe',
            'numero',
            'fecha',
            'aduana',
            'CuentaPredial',
            'version',
            'alumno',
            'curp',
            'nivel',
            'autorizacion',
            'id_producto',
        )
        fields3 = (
            'id_cfd',
            'nombre',
            'tasa',
            'tipo',
            'importe',
        )
        fields4 = (
            'id_cfd',
            'leyenda',
        )
        fields5 = (
            'id_cfd',
            'campo',
            'valor',
        )
        fields6 = (
            'id_cfd',
            'id_producto',
            'nombre',
            'tasa',
            'tipo'
        )
        fac = ','.join(str(f) for f in facturas)
        where = 'id IN ({})'.format(fac)
        data = self.db.select(
            ('cfdfacturas',), (fields), where, 'fecha')
        i = 0
        #~ fac_ok = []
        for r in data:
            i += 1
            pb.setValue(i)
            id_cfdi = r[0]
            w = "noCertificado='{}'".format(r[1])
            cer = self.db.select(('certificado',), ('id',), w)[0]
            if not cer:
                continue

            new_data = dict(zip(fields, r))
            new_data['estatus'] = 'Generada'
            new_data['folio'] = self._get_folio(new_data['serie'])
            del new_data['id']
            init = util.now()
            new_id = self.db.insertrow('cfdfacturas', new_data)
            if not new_id:
                continue

            q = self.db.select(
                ('cfddetalle',), (fields2), where='id_cfd={}'.format(id_cfdi))
            new_data = []
            for r in q:
                tmp = list(r)
                tmp[0] = new_id
                des = self.db.get_description(tmp[17])
                if des:
                    tmp[5] = util.render(des)
                new_data.append(tuple(tmp))
            self.db.executemany('cfddetalle', fields2, tuple(new_data))

            q = self.db.select(
                ('cfdimpuestos',), (fields3), where='id_cfd={}'.format(id_cfdi))
            new_data = []
            for r in q:
                tmp = list(r)
                tmp[0] = new_id
                new_data.append(tuple(tmp))
            self.db.executemany('cfdimpuestos', fields3, tuple(new_data))

            q = self.db.select(
                ('cfdleyendas',), (fields4), where='id_cfd={}'.format(id_cfdi))
            new_data = []
            for r in q:
                tmp = list(r)
                tmp[0] = new_id
                new_data.append(tuple(tmp))
            self.db.executemany('cfdleyendas', fields4, tuple(new_data))

            q = self.db.select(
                ('cfdpersonalizados',),
                (fields5), where='id_cfd={}'.format(id_cfdi))
            new_data = []
            for r in q:
                tmp = list(r)
                tmp[0] = new_id
                new_data.append(tuple(tmp))
            self.db.executemany('cfdpersonalizados', fields5, tuple(new_data))

            q = self.db.select(
                ('detalleimpuestos',),
                (fields6), where='id_cfd={}'.format(id_cfdi))
            new_data = []
            for r in q:
                tmp = list(r)
                tmp[0] = new_id
                new_data.append(tuple(tmp))
            self.db.executemany('detalleimpuestos', fields6, tuple(new_data))
            dif = util.now() - init
            if not dif.total_seconds():
                util.sleep()
        return

    def _get_folio(self, serie):
        folio = self.db.select(
            ('cfdfacturas',),
            ('ifnull(max(folio)+1,1)',),
            "serie='%s'" % serie)[0][0]
        return folio

    def cmdTimbrar(self):
        if not self.util.hay_conexion():
            msg = 'Parece que no tienes conexión a Internet, es necesario' \
                ' para enviar a timbrar los documentos, intenta más tarde'
            self.unogui.createMsgBox({'Message': msg})
            return False
        try:
            res = self._send_timbrar()
            if res:
                today = self.util.strftime(self.util.today(), '%d%m%Y')
                where = "strftime('%d%m%Y', fecha_timbrado)='{}'".format(today)
                self.__filtrar(where)
        except Exception as e:
            log.error('AdminCFDI - Timbrar: ', exc_info=True)
        self.msg_user('Proceso terminado...')
        return

    def cmdEliminar(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona las facturas a eliminar'
            self.msg_user(message)
            return
        docs = []
        for row in sel:
            id_cfdi = grid_dm.getCellData(0, row)
            uuid = self.db.select(
                ('cfdfacturas',), ('uuid',), 'id=%s' % id_cfdi)[0][0]
            if not uuid:
                docs.append(id_cfdi)
        if not docs:
            msg = 'Las facturas seleccionadas están timbradas, no se pueden eliminar'
            self.msg_user(msg)
            return
        if len(docs) == 1:
            msg = 'Vas a eliminar 1 factura sin timbrar\n\n'
        else:
            msg = 'Vas a eliminar %s facturas sin timbrar\n\n' % len(sel)
        msg += '¿Estas seguro de eliminar estas facturas?\n\nESTA ACCION ' \
            'NO SE PUEDE DESHACER\n\nSolo se eliman facturas sin timbrar'
        res = util.msgbox(
            msg, type_msg=TYPE_MSG['QUERY'], buttons=BUTTONS['YES_NO'])
        if res == BUTTON_CLICK['YES']:
            for d in docs:
                msg = 'Eliminando la factura: %s' % d
                self.msg_user(msg)
                w = 'id_cfd=%s' % d
                self.db.delete('cfddetalle', w)
                self.db.delete('cfdimpuestos', w)
                self.db.delete('cfdleyendas', w)
                self.db.delete('cfdpersonalizados', w)
                self.db.delete('detalleimpuestos', w)
                self.db.delete('cfdfacturas', 'id=%s' % d)
            self.cmdSinTimbrar()
            self.msg_user('Documentos eliminados')
        return

    def cmdPorPagar(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona primero una factura'
            self.msg_user(message)
            return
        message = '¿Estás seguro de marcar como NO pagadas las facturas ' \
            'seleccionadas?\n\nSolo se marcaran las facturas timbradas'
        if not self.unogui.createQuestion('Factura Libre', message):
            return

        for row in sel:
            id_cfd = grid_dm.getCellData(0, row)
            if grid_dm.getCellData(4, row) == 'Cancelada':
                message = 'Esta factura esta cancelda'
                self.msg_user(message)
                continue
            if grid_dm.getCellData(4, row) == 'Por pagar':
                message = 'Esta factura ya tiene este estatus'
                self.msg_user(message)
                continue

            uuid = self.db.select(
                ('cfdfacturas',), ('uuid',), 'id=%s' % id_cfd)[0][0]
            if not uuid:
                message = 'Esta factura (CFDI) esta sin timbrar, solo es ' \
                    'posible cambiar el estatus a documentos timbrados'
                self.unogui.createMsgBox({'Message': message})
                continue
            try:
                self._saldo(
                    grid_dm.getCellData(10, row),
                    grid_dm.getCellData(8, row),
                    True)
            except Exception as e:
                log.error('AdminCFDI - PorPagar: ', exc_info=True)

            rows_update = self.db.update(
                'cfdfacturas',
                {'estatus': 'Por pagar'},
                "id=%s" % id_cfd)
            if rows_update:
                grid_dm.updateCellData(4, row, 'Por pagar')
        return

    def _send_timbrar(self):
        try:
            invoices = self.db.select(
                ('cfdfacturas',),
                ('id', 'serie || folio', 'xml', 'fecha'),
                'version="3.2" and uuid="" and estatus<>"Validada"',
                'fecha')
            if not invoices:
                msg = 'No se encontraron facturas por timbrar'
                self.unogui.createMsgBox({'Message': msg})
                return False
            msg = 'Se encontraron %s facturas por timbrar. Presiona SI ' \
                'para timbrarlos ahora, presiona NO para salir' % len(invoices)
            if not self.unogui.createQuestion('Factura Libre', msg):
                return False
            avance = self.dialog.getControl('pbCopia')
            avance.setVisible(True)
            avance.setRange(1, len(invoices))
            for i,v in enumerate(invoices):
                ok, data = self._send_xml(v)
                if not ok:
                    msg = 'Ocurrio el siguiente error al timbrar el documento %s:' \
                        '\n\n%s\n\nel proceso se interrumpira' % (v[1], data)
                    self.unogui.createMsgBox({'Message': msg})
                    self.util.debug(msg)
                    return False
                avance.setValue(i+1)
            avance.setVisible(False)
        except Exception as e:
            log.error('AdminCFDI - Send Timbrar: ', exc_info=True)
        return True

    def _send_xml(self, fac):
        id_cfdi = fac[0]
        id_timbrado = self.util.get_epoch(fac[3])
        if fac[2]:
            if self._validate_xml(id_cfdi, id_timbrado, fac[2]):
                return True, ''
        ok, xml = self._make_xml(id_cfdi)
        if not ok:
            return False, xml
        #~ ok, data = self.util.timbrar(
            #~ self.rfc, xml, id_timbrado, self.new_server)
        ok, data = util.timbra_xml(self.rfc, xml, id_timbrado, self.new_server, not self.new_server)
        if ok:
            new_data = {
                'xml': data['xml'],
                'uuid': data['uuid'],
                'fecha_timbrado': data['fecha'],
                'estatus': 'Por pagar'
            }
            self.db.update('cfdfacturas', new_data, 'id=%s' % id_cfdi)
            path_pdf = self.__create_pdf(id_cfdi, False)
            self.__copiar_xml(id_cfdi, path_pdf)
            try:
                new_data = self.db.select(
                    ('cfdfacturas',),
                    ('id_cliente', 'total*TipoCambio'),
                    'id={}'.format(id_cfdi))[0]
                self._saldo(new_data[0], round(new_data[1], 2), True)
            except Exception as e:
                log.error('Update saldo', exc_info=True)
            return True, ''
        else:
            return False, data

    def _make_xml(self, id_cfdi):
        try:
            cfd = CFDXML(self, id_cfdi)
            xml = cfd.generate_xml()
            self.db.update('cfdfacturas', {'xml': xml}, 'id=%s' % id_cfdi)
            return True, xml
        except Exception as e:
            log.error('Admin CFDI - XML: ', exc_info=True)
            msg = 'Error: {}'.format(id_cfdi)
            return False, msg

    def _validate_xml(self, id_cfdi, id_timbrado, xml):
        xml = ET.fromstring(xml.encode('UTF-8'))
        timbre = xml.find('{}Complemento'.format(PRE[xml.attrib['version']]))
        if timbre is not None:
            timbre = timbre.find('{}TimbreFiscalDigital'.format(PRE['TIMBRE']))
            if timbre is not None:
                uuid = timbre.attrib['UUID']
                self.db.update('cfdfacturas',
                    {'uuid': uuid, 'estatus': 'Timbrada'}, 'id=%s' % id_cfdi)
                return True
        #~ ok, res = self.util.status_xml(self.rfc, id_timbrado, self.new_server)
        ok, res = util.estatus_timbrado(self.rfc, id_timbrado, self.new_server, not self.new_server)
        if not ok:
            self.unogui.createMsgBox({'Message': res})
            return False
        if res['Codigo'] == '600' or res['Codigo'] == '602':
            return self._recuperar_xml2(
                self.rfc, id_timbrado, res['Codigo'], id_cfdi)
        return False

    def _recuperar_xml2(self, rfc, id_timbrado, codigo, id_cfdi):
        #~ ok, data = self.util.get_xml(rfc, id_timbrado, self.new_server)
        ok, data = util.obtener_timbrado(rfc, id_timbrado, self.new_server, not self.new_server)
        if ok:
            xml = ET.fromstring(data)
            fecha = xml.attrib['fecha'].replace('T',' ')
            timbre = xml.find('{}Complemento'.format(PRE[xml.attrib['version']]))
            timbre = timbre.find('{}TimbreFiscalDigital'.format(PRE['TIMBRE']))
            campos = {}
            campos['fecha_timbrado'] = fecha
            campos['xml'] = data
            campos['uuid'] = timbre.attrib['UUID']
            campos['estatus'] = 'Timbrado'
            if codigo == '602':
                campos['estatus'] = 'Cancelado'
            grid = self.dialog.getControl('gridFacturas')
            self.db.update('cfdfacturas', campos, 'id=%s' % id_cfdi)
            return True
        return False

    def cmdValidar(self):
        try:
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            sel = self.util.clear_sel(grid.SelectedRows)
            if not sel:
                msg = 'Selecciona al menos una factura.\n\nIMPORTANTE: solo ' \
                    'se pueden marcar como VALIDADAS, facturas NO timbradas.'
                self.msg_user(msg)
                return

            msg = '¿Estás seguro de marcar como VALIDADAS las facturas ' \
                'seleccionadas?\n\nSolo se marcaran las facturas NO timbradas'
            if not self.unogui.createQuestion('Factura Libre', msg):
                return
            i = 0
            for row in sel:
                id_cfd = grid_dm.getCellData(0, row)
                uuid = self.db.select(
                    ('cfdfacturas',), ('uuid',), 'id={}'.format(id_cfd))[0][0]
                if not uuid:
                    self.db.update(
                        'cfdfacturas',
                        {'estatus': 'Validada'},
                        'id={}'.format(id_cfd))
                    grid_dm.updateCellData(4, row, 'Validada')
                    i += 1
        except Exception as e:
            log.error('AdminCFDI - Validate: ', exc_info=True)
        self.msg_user('Actulizadas {} factura(s)'.format(i))
        return
