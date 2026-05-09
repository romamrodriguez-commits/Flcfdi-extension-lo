# -*- coding: utf-8 -*-

import datetime
import re
import locale
import logging
from xml.etree import ElementTree as ET
from facturalibre.modulos.pyXml import CFDXML
from facturalibre.modulos.pyXml import CFDIXMLNOMINA
from facturalibre.modulos.pyPdf import CFDPDF
from facturalibre.modulos.pyPdf import PDFNomina
import facturalibre.ui.inputbox as inputbox
import facturalibre.ui.inputbox2 as inputbox2
import facturalibre.ui.campos as campos
import facturalibre.ui.nomina as nomina
from facturalibre.settings import LOG, KEY
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


CLIENTES_COUNT = 101
MOSTRAR_LIMITE = 1
ICON_PDF = 'pdf.png'
ICON_ODS = 'calc.png'
PRE = '{http://www.sat.gob.mx/cfd/3}'
PRE2 = '{http://www.sat.gob.mx/TimbreFiscalDigital}'


class EventosAdminNomina(object):

    def __init__(self, caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.globales = caller.globales
        if self.globales['OS'] == self.globales['WIN']:
            locale.setlocale(locale.LC_TIME, '')
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.db = caller.db
        self.rfc_emisor = caller.rfc_emisor
        self.rfc = self.db.select_field('certificado', 'rfc')
        self.format_s = self.globales['FORMAT'] % self.db.select_field(
                                                'opciones', 'decimales')
        self.enviar_correo = caller.enviar_correo
        self.value = ''
        self.img_url = '%s/icons/' % self.globales['EXT_PATH']
        self.id_cfdi = 0
        self.regimenfiscal = self.db.select_field('regimenesfiscales', 'Regimen')
        self.rutas = self.db.select(('rutasespejo',), ('ruta',))
        self.path_pem = caller.path_pem
        self.new_server = caller.new_server

    def cmdImportar(self):
        try:
            nomina.Dlg(self)
            self._filtrar('uuid=""')
            return
        except Exception as e:
            log.error('Importar Nomina', exc_info=True)

    def cmdEnviar(self):
        if not self.util.hay_conexion():
            msg = 'Parece que no tienes conexión a Internet, es necesario' \
                ' para enviar a timbrar los documentos, intenta más tarde'
            self.unogui.createMsgBox({'Message': msg})
            return False
        try:
            res = self._send_timbrar()
            if res:
                msg = 'Los documentos se timbraron correctamente'
                self.unogui.createMsgBox({'Message': msg, 'Title': 'Nomina Libre'})
            self.msg_user('Proceso terminado...')
            t = util.GetTimbres(self.rfc_emisor, self.dm.lblFoliosPac, self.new_server, not self.new_server)
            t.start()
            self._update_nomina()
        except Exception as e:
            log.error('Enviar a timbrar Nomina', exc_info=True)
        return

    def cmdPdf(self):
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona al menos un recibo'
            self.msg_user(message)
            return
        if len(sel) > 1:
            msg = 'Vas a generar %s recibos de nomina en PDF. Solo ' \
                'se generaran los recibos de nomina timbrados\n\n' % len(sel)
            msg += '¿Estas seguro de continuar?'
            if not self.unogui.createQuestion('Nomina Libre', msg):
                return
        avance = self.dialog.getControl('pbInfo')
        avance.setVisible(True)
        avance.setRange(1, len(sel))
        try:
            for i,v in enumerate(sel):
                pdf = PDFNomina(self)
                if pdf.error:
                    self.unogui.createMsgBox(
                    {'Message': pdf.error, 'Title': 'Nomina Libre'})
                    continue
                if len(sel) == 1:
                    pdf.show = True
                pdf.espejos = self.rutas
                id_cfdi = grid_dm.getCellData(0, v)
                data = self.db.select(
                    ('nominacfdi',), ('uuid',), 'id=%s' % id_cfdi)[0]
                if data[0]:
                    pdf.generate_pdf(id_cfdi)
                avance.setValue(i+1)
            avance.setVisible(False)
            self.msg_user('Documentos generados...')
        except Exception as e:
            log.error('Generar PDF Nomina', exc_info=True)
        return

    def cmdCancelar(self):
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, es necesaria' \
                        ' para enviar a cancelar con el PAC'
            self.unogui.createMsgBox({'Message': message})
            return
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona los recibos a cancelar'
            self.msg_user(message)
            return
        docs = {}
        for row in sel:
            if grid_dm.getCellData(3, row) == 'Cancelado':
                continue
            id_cfdi = grid_dm.getCellData(0, row)
            uuid = self.db.select(
                ('nominacfdi',), ('uuid',), 'id=%s' % id_cfdi)[0][0]
            if uuid:
                docs[uuid] = row
        if not docs:
            msg = 'Los recibos seleccionados, ya están cancelados o están ' \
                'sin timbrar'
            self.msg_user(msg)
            return
        if len(docs) == 1:
            msg = 'Vas a cancelar 1 recibo\n\n'
        else:
            msg = 'Vas a cancelar %s recibos\n\n' % len(sel)
        msg += '¿Estas seguro de cancelar estos recibos?\n\n ESTA ACCION NO ' \
            'SE PUEDE DESHACER'
        if not self.unogui.createQuestion('Nomina Libre', msg):
            return
        try:
            #~ ok, msg = self.util.cancel_cfdi_nomina(
                #~ self.rfc, list(docs.keys()), self.new_server)
            ok, estatus = util.cancela_multiple(self.rfc, list(docs.keys()), self.new_server, not self.new_server)
            if not ok:
                self.unogui.createMsgBox({'Message': 'Error al cancelar'})
                return
            if 'EntityAlreadyExists' in estatus:
                if len(docs) == 1:
                    uuid = list(docs.keys())[0]
                    self.db.update(
                        'nominacfdi',
                        {'estatus': 'Cancelado'},
                        "uuid='%s'" % uuid)
                    grid_dm.updateCellData(3, docs[uuid], 'Cancelado')
                else:
                    msg = 'Uno de los documentos seleccionados ya esta cancelado, valida uno por uno'
                    self.unogui.createMsgBox({'Message': msg})
                return
            #~ print ('ESTATUS', type(estatus), estatus)
            #~ if not isinstance(estatus, list):
                #~ estatus = [estatus,]
            for row in estatus:
                #~ print ('ROW', row)
                if row['Estatus'] == 'Cancelado':
                    uuid = row['UUID'].upper()
                    self.db.update(
                        'nominacfdi',
                        {'estatus': 'Cancelado'},
                        "uuid='%s'" % uuid)
                    grid_dm.updateCellData(3, docs[uuid], 'Cancelado')
            if len(msg) == 1:
                msg = '1 recibo cancelado'
            else:
                msg = '%s recibos cancelados' % len(msg)
            self.msg_user(msg)
        except Exception as e:
            log.error('Cancelar Nomina', exc_info=True)
        return

    def cmdSinTimbrar(self):
        self.dm.gridFacturas.GridDataModel.removeAllRows()
        self.dm.chkDetalle.State = 0
        where = 'uuid=""'
        self._filtrar(where)
        return

    def chkDetalle(self, source):
        grid = self.dialog.getControl('gridFacturas')
        h = 180
        if source.State:
            h = 75
        self.dialog.getControl('gridDetalle').setVisible(source.State)
        self.dialog.getControl('gridTotales').setVisible(source.State)
        grid.Model.Height = h
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

    def lstFechaPago_itemStateChanged(self, source):
        if source.SelectedItem == 'Todos':
            self._filtrar('')
        else:
            date = source.SelectedItem
            date = self.util.format_date(date, '%Y-%m-%d', '%d-%b-%Y')
            self._filtrar('fecha_pago="%s"' % date)
        return

    def _filtrar(self, where=''):
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
            data = self.db.select(('nominacfdi', ),
                ('id',
                'folio',
                fecha,
                'estatus',
                fecha_pago,
                'total*tipo_cambio',
                'empleado'), where, 'fecha_timbrado')
            if data:
                data_format = []
                format_s = self.globales['FORMAT'] % self.db.select_field(
                    'opciones', 'decimales')
                suma_cfd = 0
                for row in data:
                    total = format_s.format(row[5])
                    row_format = (
                        row[0], row[1], row[2], row[3], row[4], total, row[6])
                    data_format.append(row_format)
                self.unogui.gridAddRows(self.dm.gridFacturas, data_format)
            if data:
                msg = '%s Recibos encontrados' % len(data)
            else:
                msg = 'No se encontraron recibos con estos criterios de busqueda'
            self.msg_user(msg)
        except Exception as e:
            log.error('FiltrarNomina', exc_info=True)
        return

    def _send_timbrar(self):
        invoices = self.db.select(
            ('nominacfdi',),
            ('id', 'serie || folio', 'xml', 'fecha'),
            'uuid=""',
            'fecha')
        if not invoices:
            msg = 'No se encontraron recibos de nomina por timbrar'
            self.unogui.createMsgBox({'Message': msg, 'Title': 'Nomina Libre'})
            return False
        msg = 'Se encontraron %s recibos de nomina por timbrar. Presiona SI ' \
            'para timbrarlos ahora, presiona NO para salir' % len(invoices)
        if not self.unogui.createQuestion('Nomina Libre', msg):
            return False
        avance = self.dialog.getControl('pbInfo')
        avance.setVisible(True)
        avance.setRange(0, len(invoices) - 1)
        for i,v in enumerate(invoices):
            ok, data = self._send_xml(v)
            if not ok:
                #~ if 'DUPLICIDAD EN HASH' in data:
                msg = 'Ocurrio el siguiente error al timbrar el documento %s:' \
                    '\n\n%s\n\nel proceso se interrumpira' % (v[1], data)
                self.unogui.createMsgBox({'Message': msg})
                self.util.debug(msg)
                return False
            avance.setValue(i)
        avance.setVisible(False)
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
        #~ ok, data = self.util.timbrar(self.rfc, xml, id_timbrado, self.new_server)
        ok, data = util.timbra_xml(self.rfc, xml, id_timbrado, self.new_server, not self.new_server)
        if ok:
            self.db.update(
                'nominacfdi',
                {'xml': data['xml'],
                    'uuid': data['uuid'],
                    'fecha_timbrado': data['fecha'],
                    'estatus': 'Timbrado'},
                'id=%s' % id_cfdi)
            if self.rutas:
                format_s = self.db.get_option('file_name')
                name = self.util.get_name(
                    data['xml'], format_s, self.globales['FILE_NAME'])
                copy_data = {
                    'year': data['fecha'][0:4],
                    'month': data['fecha'][5:7],
                    'xml': data['xml'],
                    'name': '%s.xml' % name
                }
                #~ self.util.copy_xml(copy_data, self.rutas)
                util.copy_xml(copy_data, self.rutas)
            return True, ''
        else:
            return False, data

    def _make_xml(self, id_cfdi):
        try:
            cfdi = CFDIXMLNOMINA(self, id_cfdi)
            cfdi.regimenfiscal = self.regimenfiscal
            xml = cfdi.generate_xml()
            self.db.update('nominacfdi', {'xml': xml}, 'id=%s' % id_cfdi)
            return True, xml
        except Exception as e:
            msg = 'Make XML: {}'.format(id_cfdi)
            log.error(msg, exc_info=True)
            return False, msg

    def _validate_xml(self, id_cfdi, id_timbrado, xml):
        xml = ET.fromstring(xml.encode('UTF-8'))
        timbre = xml.find('%sComplemento' % PRE)
        if timbre is not None:
            timbre = timbre.find('%sTimbreFiscalDigital' % PRE2)
            if timbre is not None:
                uuid = timbre.attrib['UUID']
                self.db.update('nominacfdi',
                    {'uuid': uuid, 'estatus': 'Timbrado'}, 'id=%s' % id_cfdi)
                return True
        #~ ok, res = self.util.status_xml(self.rfc, id_timbrado, self.new_server)
        ok, res = util.estatus_timbrado(self.rfc, id_timbrado, self.new_server, not self.new_server)
        if not ok:
            self.unogui.createMsgBox({'Message': res})
            return False
        if res['Codigo'] == '600' or res['Codigo'] == '602':
            return self._recuperar_xml(
                self.rfc, id_timbrado, res['Codigo'], id_cfdi)
        return False

    def _recuperar_xml(self, rfc, id_timbrado, codigo, id_cfdi):
        #~ ok, data = self.util.get_xml(rfc, id_timbrado, self.new_server)
        ok, data = util.obtener_timbrado(rfc, id_timbrado, self.new_server, not self.new_server)
        if ok:
            xml = ET.fromstring(data)
            fecha = xml.attrib['fecha'].replace('T',' ')
            timbre = xml.find('%sComplemento' % PRE)
            timbre = timbre.find('%sTimbreFiscalDigital' % PRE2)
            campos = {}
            campos['fecha_timbrado'] = fecha
            campos['xml'] = data
            campos['uuid'] = timbre.attrib['UUID']
            campos['estatus'] = 'Timbrado'
            if codigo == '602':
                campos['estatus'] = 'Cancelado'
            grid = self.dialog.getControl('gridFacturas')
            self.db.update('nominacfdi', campos, 'id=%s' % id_cfdi)
            if self.rutas:
                name_xml = "serie || substr('000000' || folio, -6, 6) || '_' || replace(empleado, ' ', '_') || '.xml'"
                data = self.db.select(
                    ('nominacfdi', ),
                    ("strftime('%Y',fecha_timbrado)",
                        "strftime('%m',fecha_timbrado)", name_xml, 'xml'),
                    'id=%s' % id_cfdi)[0]
                data = {
                    'year': data[0],
                    'month': data[1],
                    'name': data[2],
                    'xml': data[3],
                }
                #~ print ('DATA', data)
                self.util.copy_xml(data, self.rutas)
            return True
        return False

    def msg_user(self, msg):
        self.dm.lblInfo.Label = msg
        return

    def cmdSalir(self):
        self.util.kill(self.path_pem)
        self.dialog.endExecute()
        return

    def cmdDelete(self):
        try:
            grid = self.dialog.getControl('gridFacturas')
            grid_dm = grid.Model.GridDataModel
            sel = self.util.clear_sel(grid.SelectedRows)
            if not sel:
                message = 'Selecciona los recibos a eliminar'
                self.msg_user(message)
                return
            docs = []
            for row in sel:
                id_cfdi = grid_dm.getCellData(0, row)
                uuid = self.db.select(
                    ('nominacfdi',), ('uuid',), 'id=%s' % id_cfdi)[0][0]
                if not uuid:
                    docs.append(id_cfdi)
            if not docs:
                msg = 'Los recibos seleccionados están timbrados, no se pueden eliminar'
                self.msg_user(msg)
                return
            if len(docs) == 1:
                msg = 'Vas a eliminar 1 recibo\n\n'
            else:
                msg = 'Vas a eliminar %s recibos\n\n' % len(sel)
            msg += '¿Estas seguro de eliminar estos recibos?\n\nESTA ACCION ' \
                'NO SE PUEDE DESHACER\n\nSolo se eliman recibos sin timbrar'
            if not self.unogui.createQuestion('Nomina Libre', msg):
                return
            for d in docs:
                msg = 'Eliminando el recibo: %s' % d
                self.msg_user(msg)
                w = 'id_cfdi=%s' % d
                self.db.delete('nominapd', w)
                self.db.delete('nominaincapacidad', w)
                self.db.delete('nominaimpuestos', w)
                self.db.delete('nominahorasextra', w)
                self.db.delete('nominadetalle', w)
                self.db.delete('nominacfdi', 'id=%s' % d)

            self.cmdSinTimbrar()
            self.msg_user('Documentos eliminados')
        except Exception as e:
            log.error('DeleteNomina', exc_info=True)
        return

    def _update_nomina(self):
        data = self.db.select(
            ('nominacfdi',),
            ('DISTINCT(fecha_pago)',),
            order='fecha_pago')
        data = [self.util.format_date(r[0], '%d-%b-%Y') for r in data]
        fecha_pago = self.dialog.getControl('lstFechaPago')
        fecha_pago.removeItems(0, fecha_pago.getItemCount())
        if data:
            fecha_pago.addItems(tuple(data), 0)
        fecha_pago.addItems(('Todos',), 0)
        fecha_pago.selectItem('Todos', True)
        self.dm.gridFacturas.GridDataModel.removeAllRows()
        self.cmdSinTimbrar()
        return

    def cmdCopyXML(self):
        if not self.rutas:
            msg = 'No tienes establecida niguna ruta para guardar ' \
                'documentos, establece al menos una ruta'
            self.unogui.createMsgBox({'Message': message})
            return
        grid = self.dialog.getControl('gridFacturas')
        grid_dm = grid.Model.GridDataModel
        sel = self.util.clear_sel(grid.SelectedRows)
        if not sel:
            message = 'Selecciona al menos un recibo'
            self.msg_user(message)
            return
        if len(sel) > 1:
            msg = 'Vas a extrar %s recibos de nomina en XML. Solo ' \
                'se extraen los recibos de nomina timbrados\n\n' % len(sel)
            msg += '¿Estas seguro de continuar?'
            if not self.unogui.createQuestion('Nomina Libre', msg):
                return
        try:
            avance = self.dialog.getControl('pbInfo')
            avance.setVisible(True)
            avance.setRange(1, len(sel))
            espejos = self.db.select(('rutasespejo',), ('ruta',))
            format_s = self.db.get_option('file_name')
            for i,v in enumerate(sel):
                id_cfdi = grid_dm.getCellData(0, v)
                data = self.db.select(
                    ('nominacfdi',),
                    ("strftime('%Y',fecha_timbrado)",
                        "strftime('%m',fecha_timbrado)", 'xml'),
                    'id=%s' % id_cfdi)[0]
                name = self.util.get_name(
                    data[2], format_s, self.globales['FILE_NAME'])
                copy_data = {
                    'year': data[0],
                    'month': data[1],
                    'xml': data[2],
                    'name': '%s.xml' % name
                }
                #~ self.util.copy_xml(copy_data, self.rutas)
                util.copy_xml(copy_data, self.rutas)
                avance.setValue(i+1)
            avance.setVisible(False)
            self.msg_user('Documentos extraidos...')
        except Exception as e:
            log.error('CopyXML', exc_info=True)
        return

    def cmdFolio(self):
        folio = self.dm.txtFolio.Text.strip()
        if not folio:
            self.dialog.getControl('txtFolio').setFocus()
            message = 'Introduce el folio a buscar'
            self.msg_user(message)
            return
        try:
            folio = int(self.dm.txtFolio.Text)
        except:
            message = 'El folio debe ser un número entero'
            self.msg_user(message)
            self.dialog.getControl('txtFolio').setFocus()
            return
        where = " AND folio=%s" % folio
        self._filtrar(where)
        return

    def txtFolio_keyPressed(self, event):
        if event.KeyCode == KEY['RETURN'] or event.KeyCode == KEY['TAB']:
            return
        folio = event.Source.Text.strip()
        if not folio:
            self.unogui.gridAddRows(self.dm.gridFacturas, ())
            self.msg_user('Sin recibos')
            return
        where = "folio LIKE '%{0}%'".format(folio)
        self._filtrar(where)
        return

    def txtReceptor_keyPressed(self, event):
        if event.KeyCode == KEY['RETURN'] or event.KeyCode == KEY['TAB']:
            return
        grid = self.dialog.getControl('gridReceptores')
        cliente = event.Source.Text.strip().replace('|','')
        if not cliente:
            grid.setVisible(False)
            self.dm.txtReceptor.Tag = ''
            return
        where = "nombre LIKE '%" + cliente + "%'"
        receptores = self.db.select(
            ('empleados',), ('id', 'rfc', 'curp', 'nombre'), where, 'nombre')
        self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
        grid.setVisible(True)
        return

    def gridReceptores_selectionChanged(self, grid):
        self.dm.txtReceptor.Tag = ''
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            self.dm.txtReceptor.Tag = grid_dm.getCellData(2, row)
            self.dm.txtReceptor.Text = grid_dm.getCellData(3, row)
        grid.setVisible(False)
        self.cmdFiltrar1()
        return

    def lstAno_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def lstMes_itemStateChanged(self, source):
        self.cmdFiltrar1()
        return

    def cmdFiltrar1(self):
        where = ''
        month = self.dialog.getControl('lstMes')
        year = self.dialog.getControl('lstAno')
        pos1 = month.SelectedItemPos
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
        if self.dm.txtReceptor.Tag:
            where += " AND curp='%s'" % self.dm.txtReceptor.Tag
        self._filtrar(where)
        return
