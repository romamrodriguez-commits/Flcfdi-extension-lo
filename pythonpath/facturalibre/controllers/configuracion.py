# -*- coding: utf-8 -*-

import logging
import os
import sys
import facturalibre.ui.edit as editAdd
import facturalibre.ui.asignar as Asignar

import facturalibre.ui.input_box as input_box
from facturalibre.modulos import util
from facturalibre.settings import (
    LOG, DEBUG, BUTTON_CLICK, BUTTONS, TYPE_MSG, PAYMENT_METHODS)


log = logging.getLogger(LOG['NAME'])


FOLIOS_MIN = 49
LIMITE_IMPUESTO = 50
PATH_OPENSSL = '/bin/openssl.exe'
PATH_CER = 'pruebas.cer'
PATH_KEY = 'pruebas.key'
PASSWORD = '12345678a'
IS_FIEL = 'SSL server : No'
CER_SERIE_PRUEBA = '20001000000100005867'
ADDENDA_NODO = 'empresalibre-org'
ADDENDA_ATRIBUTO1 = 'http://empresalibre.org/cfd'
ADDENDA_ATRIBUTO2 = 'http://empresalibre.org/cfd/addenda.xsd'
SEPARADOR = '|'
EMPRESAS = 'Empresas'
PATHS = 'Rutas'
EXTENSION_PLANTILLA = '.ods'
KEY_RETURN = 1280


class EventosConfiguracion(object):

    def __init__(self, caller):
        self.caller = caller
        self.globales = caller.globales
        self.options2 = caller.options
        self.util = caller.util
        self.unogui = caller.unogui
        self.db = caller.db
        self.dialog = caller.dialog
        self.opcion_correo = caller.opcion_correo
        self.dm = self.dialog.getModel()
        self.cer = {}
        self.emisor = {}
        self.options = {}
        self.cat = {}
        self.value = ''
        if self.globales['OS'] == self.globales['WIN']:
            self.path_openssl = self.util.urlToSystem(
                                    self.globales['EXT_PATH'] + PATH_OPENSSL)
        else:
            self.path_openssl = 'openssl'
        self.path_ext = self.util.urlToSystem(self.globales['EXT_PATH'])
        self.emisores = self.util.get_configvalue(
                            self.globales['NODE'], EMPRESAS).split(SEPARADOR)
        self.work_paths = self.util.get_configvalue(
                            self.globales['NODE'], PATHS).split(SEPARADOR)

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def cmdCerTest(self):
        self.dm.txtRutaCer.Text = PATH_CER
        self.dm.txtRutaKey.Text = PATH_KEY
        self.dm.txtContrasena.Text = PASSWORD
        return

    def cmdGuardarCertificado(self):
        self.db.delete('certificado')
        data = {
            'rfc': self.cer['rfc'],
            'nombre': self.cer['nombre'],
            'cer': self.db.load_file(self.cer['cer']),
            'key': self.db.load_file(self.cer['key']),
            'pem': self.cer['pem'],
            'noCertificado': self.cer['noCertificado'],
            'certificado': self.cer['certificado'],
            'inicio': str(self.cer['inicio']),
            'final': str(self.cer['final'])
        }
        if self.db.insertrow('certificado', data):
            columns = ({'Title': '',
                            'ColumnWidth': 90,
                            'HorizontalAlign': 2},
                        {'Title': 'Datos del certificado guardados',
                            'ColumnWidth': 150,
                            'HorizontalAlign': 0})
            self.unogui.gridChangeColumn(self.dm.gridCertificado, columns)
            rows = (('Razón Social: ', self.cer['nombre']),
                    ('RFC: ', self.cer['rfc']),
                    ('Serie: ', self.cer['noCertificado']),
                    ('Desde: ', self.cer['inicio'].strftime('%d-%b-%Y')),
                    ('Hasta: ', self.cer['final'].strftime('%d-%b-%Y')))
            self.unogui.gridAddRows(self.dm.gridCertificado, rows)
            data = self.db.select(('emisor',))
            if data:
                data = {'rfc': self.cer['rfc'], 'nombre': self.cer['nombre']}
                self.db.update('emisor', data)
            self.dialog.Title = '%s - Configuración - %s' % (
                                self.globales['APP_TITULO'], self.cer['nombre'])
            self._save_emisor(self.cer['nombre'])
            self.dm.cmdGuardarCertificado.Enabled = False
            self.dm.cmdVerificarSat.Enabled = False
            self.dm.txtRutaCer.Text = ''
            self.dm.txtRutaCer.Tag = ''
            self.dm.txtRutaKey.Text = ''
            self.dm.txtRutaKey.Tag = ''
            self.dm.txtContrasena.Text = ''
            self.dm.txtRfc.Text = self.cer['rfc']
            self.dm.txtNombre.Text = self.cer['nombre']
            self.dm.cmdGuardarEmisor.Enabled = True
        else:
            message = 'No fue posible guardar el certificado, ' \
                        'consulte a soporte tecnico'
            self.unogui.createMsgBox({'Message': message})
        return

    def cmdVerificarSat(self):
        message = 'Esta opción valida que el número de serie del certificado ' \
                'de sellos este dado de alta directamente en el SAT, se ' \
                'requiere acceso a Internet para esto. \n\n ¿Deseas continuar?'
        if not self.unogui.createQuestion('Factura Libre', message):
            return
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, verifica esto primero'
            self.unogui.createMsgBox({'Message': message})
            return
        serie = self.cer['noCertificado']
        ftpsat = self.db.select_field('sat', 'ftpsat')
        dirsat = self.db.select_field('sat', 'dirsat')
        url_cer = os.path.join(dirsat, serie[0:6], serie[6:12], serie[12:14],
                                serie[14:16], serie[16:18])
        res = self.util.cer_en_sat(ftpsat, url_cer, serie + '.cer')
        if res:
            message = 'El certificado de sello con número de serie: %s se ' \
                    'encontró en el SAT \n\n Ya puedes guardar y usar este ' \
                    'certificado' % serie
        else:
            message = 'El certificado de sello con número de serie: %s \n ' \
                    'NO se encontró en el SAT esto puede deberse a alguna de ' \
                    'las siguientes causas\n\n 1.- Estas usando el certificado ' \
                    'de pruebas de este sistema \n 2.- Solicitaste este ' \
                    'certificado al SAT en las pasadas 72 horas \n 3.- Estas ' \
                    'usando tu FIEL (CUIDADO NO ES CORRECTO)' % serie
        self.unogui.createMsgBox({'Message': message})
        return

    def cmdVerificar(self):
        try:
            count = self.db.count('certificado')
            if count:
                message = 'Ya tienes un certificado guardado \n\n ' \
                        '¿Estás seguro de volver a validar?'
                res = self.unogui.createMsgBox({'Message': message,
                                                'Type': 'querybox', 'Buttons': 3})
                if res == 3:
                    return
            self.dm.cmdGuardarCertificado.Enabled = False
            self.dm.cmdVerificarSat.Enabled = False
            self.cer.clear()
            message = self._validar_datos_certificado()
            if isinstance(message, str):
                self.unogui.createMsgBox({'Message': message})
            else:
                self.dm.cmdGuardarCertificado.Enabled = True
                self.dm.cmdVerificarSat.Enabled = True
                self._mostrar_datos()
        except:
            print (traceback.format_exc())
        return

    def _mostrar_datos(self):
        columns=({'Title': '','ColumnWidth': 0},
        {'Title': 'Resumen de validación', 'ColumnWidth': 240, 'HorizontalAlign': 0})
        self.unogui.gridChangeColumn(self.dm.gridCertificado, columns)
        rows = (('', 'La contraseña de la llave privada es correcta'),
        ('', 'Se encontró el certificado'),
        ('', 'El certificado y la llave privada son pareja'),
        ('', 'El certificado esta vigente del %s al %s' % (self.cer['inicio'].strftime('%d-%b-%Y'), self.cer['final'].strftime('%d-%b-%Y'))),
        ('', 'El certificado esta a nombre de: %s' % self.cer['nombre']),
        ('', 'El certificado tiene el RFC: %s' % self.cer['rfc']),
        ('', 'La serie del certificado es: %s' % self.cer['noCertificado']))
        self.unogui.gridAddRows(self.dm.gridCertificado, rows)
        return

    def _validar_datos_certificado(self):
        message = ''

        txtRutaCer = self.dialog.getControl('txtRutaCer')
        if txtRutaCer.Text == PATH_CER:
            ruta_cer = self.path_ext + '/bin/%s' % PATH_CER
        else:
            ruta_cer = txtRutaCer.Text
        if self.unogui.validate(txtRutaCer, 'Vacio'):
            message = 'Selecciona la ruta del certificado, archivo CER'
        elif not os.path.exists(ruta_cer):
            message = 'La ruta del archivo CER especificada, NO existe'
        elif not self.util.check_extension(ruta_cer, '.cer'):
            message = 'La ruta especifica no es un archivo CER'
        if message:
            txtRutaCer.setFocus()
            return message
        self.cer['cer'] = ruta_cer

        txtRutaKey = self.dialog.getControl('txtRutaKey')
        if txtRutaKey.Text == PATH_KEY:
            ruta_key = self.path_ext + '/bin/%s' % PATH_KEY
        else:
            ruta_key = txtRutaKey.Text
        if self.unogui.validate(txtRutaKey, 'Vacio'):
            message = 'Selecciona la ruta de la llave privada, archivo KEY'
        elif not os.path.exists(ruta_key):
            message = 'La ruta del archivo KEY especificada, NO existe'
        elif not self.util.check_extension(ruta_key, '.key'):
            message = 'La ruta especifica no es un archivo KEY'
        if message:
            txtRutaKey.setFocus()
            return message
        self.cer['key'] = ruta_key

        txtContra = self.dialog.getControl('txtContrasena')
        if self.unogui.validate(txtContra, 'Vacio'):
            message = 'Captura al contraseña de la llave privada (no se guarda)'
            txtContra.setFocus()
            return message

        self._obtener_pem(self.cer['key'], txtContra.Text)
        if 'pem' not in self.cer:
            message = 'La contraseña de la llave privada es incorrecta'
            txtContra.setFocus()
            return message

        self._obtener_datos_cer(self.cer['cer'])

        if self.cer['noCertificado'] == CER_SERIE_PRUEBA:
            message = 'Estas usando el certificado de pruebas que acompaña ' \
                    'a Factura Libre, toma en cuenta que es solo para fines ' \
                    'demostrativos y que con este certificado se generan XML ' \
                    'técnicamente válidos, pero fiscalmente INVALIDOS \n\n' \
                    'Presiona ACEPTAR para continuar'
            self.unogui.createMsgBox({'Message': message})
        else:
            if self._is_fiel(self.cer['cer']):
                message = 'Al parecer este certificado corresponde a una ' \
                        'FIEL, tienes que seleccionar un certificado de ' \
                        'sellos para poder facturar, usar la FIEL es un error ' \
                        'mayusculo, asegurate de que estos sean correctos.\n\n' \
                        '¿Estás seguro de continuar con estos archivos?'
                if not self.unogui.createQuestion('Factura Libre', message):
                    txtRutaCer.setFocus()
                    message = 'Busca y selecciona los certificados correctos'
                    return message

        if not self._sonpareja(self.cer['pem'], self.cer['cer']):
            message = 'El archivo CER y KEY no son pareja'
            txtRutaCer.setFocus()
            return message

        now = self.util.now()
        message = '\n\nDesde: %s\nHasta: %s\n\nFecha actual: %s' \
                    % (self.cer['inicio'].strftime('%d-%b-%Y'),
                        self.cer['final'].strftime('%d-%b-%Y'),
                        now.strftime('%d-%b-%Y'))
        if self.cer['inicio'] > now:
            message = 'Aun no empieza la vigencia de este certificado %s' % message
            txtRutaCer.setFocus()
            return message
        if self.cer['final'] < now:
            message = 'La vigencia de este certificado a terminado %s' % message
            txtRutaCer.setFocus()
            return message
        dias = self.cer['final'] - now
        if dias.days < 31:
            message = 'La vigencia de este certificado esta por terminar en ' \
                    '%s días.\n\nSe recomienda solicitar un nuevo certificado ' \
                    'en el SAT' % dias.days
            self.unogui.createMsgBox({'Message': message})

        self._obtener_cer_base64(self.cer['cer'])
        if not self.cer['certificado']:
            message = 'No fue posible convertir el certificado a Base64, ' \
                    'consulta a soporte tecnico'
            txtRutaCer.setFocus()
            return message
        self.cer['pem'] = self.util.load_file(self.cer['pem'])

        #   SOLO CFDI
        #~ if self.util.hay_conexion() and not DEBUG:
        if self.util.hay_conexion():
            #~ ok, res = self.util.client_status(self.cer['rfc'])
            #~ 'Folios PAC: {}'.format(util.get_timbres(rfc))
            ok, timbres = util.get_timbres(self.cer['rfc'])
            if not ok:
                #~ ok, res = self.util.client_status(self.cer['rfc'], False)
                ok, timbres = util.get_timbres(self.cer['rfc'], False)
            if ok:
                self.dm.lblPac.Label = 'Folios PAC: {}'.format(timbres)
                message = 'El RFC: %s\n\nSe encuentra registrado y activo ' \
                    'correctamente en el PAC, puedes timbrar con este RFC.' \
                    % self.cer['rfc']
                if self.cer['noCertificado'] == CER_SERIE_PRUEBA:
                    message = 'El RFC: %s\n\nSe encuentra registrado ' \
                        ' y activo correctamente en el sistema de ' \
                        'PRUEBAS del PAC, puedes generar y timbrar ' \
                        'con este RFC, pero recuerda que todos los ' \
                        'documentos generado son con fines demostrativos ' \
                        'y \n\nNO SON VALIDOS FISCALMENTE' % self.cer['rfc']
            else:
                message = 'Ocurrio el siguiente error al contactar al PAC: ' \
                    '\n\n%s\n\nPuedes continuar, pero no podrás timbrar hasta' \
                    ' resolver este problema' % timbres
            if message:
                self.unogui.createMsgBox({'Message': message})
        #~ elif DEBUG:
            #~ msg = 'Estas usando el sistema de pruebas, NO se verifico tu ' \
                #~ 'alta con el PAC. \n\nIMPORTANTE: si quieres hacer pruebas ' \
                #~ 'de timbrado, tienes que usar forzosamente los certificados ' \
                #~ 'de pruebas del sistema, NO puede usar tus certificados reales'
            #~ self.unogui.createMsgBox({'Message': msg})
        return True

    def _is_fiel(self, cer):
        argumentos = [self.path_openssl, 'x509', '-inform', 'DER', '-in', cer, '-noout', '-purpose']
        data = self.util.call(argumentos).split('\n')[3]
        if data == IS_FIEL:
            return True
        return False

    def _obtener_pem(self,ruta_key,contra):
        ruta_pem = self.util.getPathTemp()
        argumentos = [self.path_openssl, 'pkcs8', '-inform', 'DER', '-in', ruta_key, '-passin', "pass:%s" % (contra), '-out', ruta_pem]
        self.util.call(argumentos)
        if os.path.exists(ruta_pem) and os.path.getsize(ruta_pem) > 0:
            self.cer['pem'] = ruta_pem
        return

    def _sonpareja(self,pem,cer):
        argumentos = [self.path_openssl, 'rsa', '-in', pem, '-noout', '-modulus']
        key_modulus = self.util.call(argumentos)
        argumentos = [self.path_openssl, 'x509', '-inform', 'DER', '-in', cer, '-noout', '-modulus']
        cer_modulus = self.util.call(argumentos)
        return key_modulus == cer_modulus

    def _obtener_datos_cer(self,cer):
        argumentos = [self.path_openssl, 'x509', '-inform', 'DER', '-in', cer, '-noout', '-startdate']
        data_tmp = self.util.call(argumentos)
        months = {'notBefore=Jan': '01', 'notBefore=Apr': '04', 'notBefore=Aug': '08', 'notBefore=Dec': '12'}
        date_l = data_tmp.strip().split(' ')
        if  date_l[0] in months:
            template = '%m %d %H:%M:%S %Y GMT'
            date_l[0] = months[date_l[0]]
            data_tmp = ' '.join(date_l)
        else:
            data_tmp = data_tmp.strip()
            template = 'notBefore=%b %d %H:%M:%S %Y GMT'
        self.cer['inicio'] = self.util.strptime(data_tmp, template)

        argumentos = [self.path_openssl, 'x509', '-inform', 'DER', '-in', cer, '-noout', '-enddate']
        data_tmp = self.util.call(argumentos)
        months = {'notAfter=Jan': '01', 'notAfter=Apr': '04', 'notAfter=Aug': '08', 'notAfter=Dec': '12'}
        date_l = data_tmp.strip().split(' ')
        if  date_l[0] in months:
            template = '%m %d %H:%M:%S %Y GMT'
            date_l[0] = months[date_l[0]]
            data_tmp = ' '.join(date_l)
        else:
            data_tmp = data_tmp.strip()
            template = 'notAfter=%b %d %H:%M:%S %Y GMT'
        self.cer['final'] = self.util.strptime(data_tmp, template)

        argumentos = [self.path_openssl, 'x509', '-inform', 'DER', '-in', cer, '-noout', '-subject']
        data_tmp = self.util.call(argumentos)
        data_tmp = data_tmp.split('=')
        self.cer['nombre'] = data_tmp[2].split('/')[0].strip()
        self.cer['rfc'] = data_tmp[5].split('/')[0].strip()
        argumentos = [self.path_openssl, 'x509', '-inform', 'DER', '-in', cer, '-noout', '-serial']
        data_tmp = self.util.call(argumentos)
        serial_tmp = data_tmp.split('=')[1].split('\n')[0]
        self.cer['noCertificado'] = serial_tmp[1::2]
        return

    def _obtener_cer_base64(self,cer):
        argumentos = [self.path_openssl, 'enc', '-base64', '-in', cer]
        data_tmp = self.util.call(argumentos)
        if data_tmp:
            self.cer['certificado'] = data_tmp.replace('\n','')
        return

    def cmdAgregarFolios(self):
        #~ try:
        message = self._validar_datos_folios()
        if isinstance(message, str):
            self.unogui.createMsgBox({'Message': message})
            return
        if self.db.insertrow('folios', message):
            data = self.db.select(
                ('folios', 'tiposcfdi'),
                ('folios.id', 'serie', 'inicio', 'tipo',
                    "case when predeterminado then 'SI' else '' end",
                    'plantilla',
                    "case when donativo then 'SI' else '' end"),
                'folios.usarcon=tiposcfdi.id')
            self.unogui.gridAddRows(self.dm.gridFolios, data)
            self.dm.cmdEliminarFolios.Enabled=True
            self.dm.cmdPredeterminar.Enabled=True
            self.dialog.getControl('lstUsarCon').selectItemPos(0,True)
            self.dialog.getControl('txtSerie').Text=''
            self.dialog.getControl('txtInicio').Text=''
            self.dialog.getControl('txtPlantillaFolios').Text=''
            self.dialog.getControl('txtSerie').setFocus()
        else:
            message='No fue posible guardar el nuevo rango de folios, ' \
                'consulte a soporte tecnico'
            self.unogui.createMsgBox({'Message': message})
        #~ except:
            #~ print (traceback.format_exc())
        return

    def cmdPredeterminar(self):
        grid = self.dialog.getControl('gridFolios')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona un rango de folios'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        pre = grid_dm.getCellData(4, row)
        if pre:
            message = 'El rango de folios ya es el predeterminado'
            self.unogui.createMsgBox({'Message': message})
            return
        self.db.update('folios',{'predeterminado': 0})
        self.db.update('folios',
                        {'predeterminado': 1},
                        "id=%s" % grid_dm.getCellData(0, row))
        data = self.db.select(
                ('folios', 'tiposcfdi'),
                ('folios.id', 'serie', 'inicio',
                    'folios.usarcon=tiposcfdi.id',
                    "case when predeterminado then 'SI' else '' end",
                    'plantilla',
                    "case when donativo then 'SI' else '' end"),
                'folios.usarcon=tiposcfdi.id')
        self.unogui.gridAddRows(self.dm.gridFolios, data)
        return

    def cmdEliminarFolios(self):
        grid = self.dialog.getControl('gridFolios')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona un rango de folios'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        message = '¿Estás seguro de eliminar el siguiente rango de folios? ' \
            '\n\n Serie = %s \n Inicio = %s \n\nSi el rango de folios tiene ' \
            'una plantilla asignada, se usará la plantilla predeterminada. ' \
            '\n\nESTA ACCION NO SE PUEDE DESHACER' % (
                grid_dm.getCellData(1,row),
                grid_dm.getCellData(2,row))
        if self.unogui.createQuestion('Factura Libre', message):
            self.db.delete('folios', 'id=%s' % grid_dm.getCellData(0, row))
            data = self.db.select(
                    ('folios', 'tiposcfdi'),
                    ('folios.id', 'serie', 'inicio', 'tipo',
                        "case when predeterminado then 'SI' else '' end",
                        'plantilla',
                        "case when donativo then 'SI' else '' end"),
                    'folios.usarcon=tiposcfdi.id')
            if data:
                self.unogui.gridAddRows(self.dm.gridFolios, data)
            else:
                self.dm.gridFolios.GridDataModel.removeAllRows()
                self.dm.cmdEliminarFolios.Enabled = False
                self.dm.cmdPredeterminar.Enabled = False
            return
        return

    def _validar_datos_folios(self):
        message = ''
        txtControl = self.dialog.getControl('txtSerie')
        if self.unogui.validate(txtControl, 'Vacio'):
            message = 'La serie esta vacía, puedes dejarla vacía, pero se ' \
                'recomienda asignar una. ¿Qué deseas hacer? \n\n SI = ' \
                'dejarla vacía \n No = regresar y asignar una'
            if not self.unogui.createQuestion('Factura Libre', message):
                txtControl.setFocus()
                return ''
        serie = txtControl.Text.strip('_')

        txtControl = self.dialog.getControl('txtInicio')
        if self.unogui.validate(txtControl, 'Vacio'):
            message = 'El campo INICIO no puede estar vacío'
            txtControl.setFocus()
            return message

        inicio = int(txtControl.Text.strip('_'))
        if inicio == 0:
            message = 'El campo FOLIO INICIAL no puede ser cero'
            txtControl.setFocus()
            return message
        if inicio > 1:
            message = 'El campo FOLIO INICIAL es mayor a uno. \n\n ¿Estás ' \
                'seguro de usar este valor?'
            if not self.unogui.createQuestion('Factura Libre', message):
                txtControl.setFocus()
                return ''
        data = self.db.select(('cfdfacturas',),('max(folio)',), "serie='%s'" % serie)[0][0]
        if data:
            if (inicio - data) > 1:
                message = 'El FOLIO INICIAL, es mayor al ultimo folio que es: ' \
                    '%s\n\nSi aceptas este valor, vas a dejar folios huerfanos,' \
                    'en el esquema CFDI esto se permite pero no se recomienda' \
                    '\n\n¿Estás seguro de usar este valor?' % data
                if not self.unogui.createQuestion('Factura Libre', message):
                    txtControl.setFocus()
                    return ''
        lstControl = self.dialog.getControl('lstUsarCon')
        usarcon = lstControl.SelectedItemPos
        if usarcon <= 0:
            message = 'Selecciona el tipo de comprobantes (USAR CON) con que ' \
                'se usará esta serie'
            lstControl.setFocus()
            return message
        where = "serie='%s' and inicio=%s" % (serie, inicio)
        data = self.db.select(('folios',), ('id',), where)
        if data:
            message = 'Este rango de folios ya está dado de alta'
            txtControl.setFocus()
            return message
        message = ''
        txtPlantilla = self.dialog.getControl('txtPlantillaFolios')
        if not self.unogui.validate(txtPlantilla, 'Vacio'):
            if not os.path.exists(txtPlantilla.Text):
                message = u'La ruta del archivo ODS especificada, NO existe'
            elif not self.util.check_extension(txtPlantilla.Text, '.ods'):
                message = u'La extensión del archivo seleccionado, no es ODS'
        if message:
            txtPlantilla.setFocus()
            return message
        data = {}
        data['serie'] = serie
        data['inicio'] = inicio
        data['usarcon'] = usarcon
        if self.dm.gridFolios.GridDataModel.RowCount:
            data['predeterminado'] = False
        else:
            data['predeterminado'] = True
        data['plantilla'] = txtPlantilla.Text
        data['donativo'] = self.dm.chkDonativo.State
        return data

    def cmdGuardarEmisor(self):
        try:
            message = self._validar_datos_emisor()
            if isinstance(message, str):
                self.unogui.createMsgBox({'Message': message})
            else:
                self.db.delete('emisor')
                if self.db.insertrow('emisor', self.emisor):
                    self._save_emisor(self.emisor['nombre'])
                    self.db.delete('regimenesfiscales')
                    data = self.unogui.list_to_tuple(
                        self.dm.lstRegimen.StringItemList)
                    self.db.executemany('regimenesfiscales', ('Regimen',), data)
                    message = 'Datos del emisor guardados correctamente'
                    self.unogui.createMsgBox({'Message': message})
                    self.dialog.Title = '%s - Configuración - %s' % (
                                self.globales['APP_TITULO'], self.emisor['nombre'])
                else:
                    message = 'No fue posible guardar los datos del emisor, ' \
                        'consulte a soporte tecnico'
                    self.unogui.createMsgBox({'Message': message})
        except:
            print (traceback.format_exc())
        return

    def optTipoContribuyente(self, source):
        self.emisor['tipo'] = int(source.Model.Tag)
        if self.emisor['tipo'] == 3:
            visible = True
        else:
            visible = False
            self.dm.txtAutorizacionOng.Text = ''
            #~ self.dm.txtFechaOng.Date = None
        controls = (
            'lblAutorizacionOng',
            'txtAutorizacionOng',
            'lblFechaOng',
            'txtFechaOng',
            )
        self.unogui.setVisible(self.dialog, controls, visible)
        return

    def optCorreo(self, source):
        self.opcion_correo = int(source.Model.Tag)
        self.db.update('opciones2', {'opcion5': self.opcion_correo})
        return

    def lstDobleClick(self, source):
        if source.ItemCount:
            name = source.Model.Name
            if name == 'lstMetodoPago':
                return self._remove_payment_method(source)
            source.removeItems(source.SelectedItemPos, 1)
        return

    def cmdEliminarCampo(self, source):
        lst = self.dialog.getControl(source.Model.Tag)
        if lst.SelectedItemPos < 0:
            message = 'Selecciona el elemento a eliminar'
            self.unogui.createMsgBox({'Message': message})
        else:
            self.lstDobleClick(lst)
        return

    def _validar_datos_emisor(self):
        message = ''
        txtControl = self.dialog.getControl('txtRfc')
        if self.unogui.validate(txtControl,'Vacio'):
            message = 'El campo RFC esta vacío, este valor se extrae ' \
                    'directamente de tu certificado, agrega primero tu ' \
                    'certificado de sello para obtener este valor'
            txtControl.setFocus()
            return message
        self.emisor['rfc'] = txtControl.Text

        if 'tipo' not in self.emisor:
            if self.dialog.getControl('optFisica').State:
                self.emisor['tipo'] = 1
            elif self.dialog.getControl('optMoral').State:
                self.emisor['tipo'] = 2
            elif self.dialog.getControl('optOng').State:
                self.emisor['tipo'] = 3
            else:
                message = 'Tienes que seleccionar el Tipo de Contribuyente'
                return message

        txtControl = self.dialog.getControl('txtNombre')
        if self.unogui.validate(txtControl,'Vacio'):
            message = 'El campo RAZON SOCIAL no puede estar vacío'
            txtControl.setFocus()
            return message
        self.emisor['nombre'] = txtControl.Text

        txtControl = self.dialog.getControl('txtCalle')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo CALLE no puede estar vacío'
            txtControl.setFocus()
            return message
        self.emisor['calle'] = txtControl.Text

        txtControl = self.dialog.getControl('txtNumExt')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo NUMERO EXTERIOR no puede estar vacío, puedes usar SN'
            txtControl.setFocus()
            return message
        self.emisor['noExterior'] = txtControl.Text

        txtControl = self.dialog.getControl('txtNumInt')
        txtControl.Text=txtControl.Text.strip().replace('|','')
        self.emisor['noInterior'] = txtControl.Text

        txtControl = self.dialog.getControl('txtColonia')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo COLONIA no puede estar vacío.'
            txtControl.setFocus()
            return message
        self.emisor['colonia'] = txtControl.Text

        txtControl = self.dialog.getControl('txtMunicipio')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo MUNICIPIO o DELEGACION no puede estar vacío.'
            txtControl.setFocus()
            return message
        self.emisor['municipio'] = txtControl.Text

        lstControl = self.dialog.getControl('lstEstados')
        estado = lstControl.SelectedItemPos
        if estado<=0:
            message='Selecciona el estado de la dirección fiscal del emisor'
            lstControl.setFocus()
            return message
        self.emisor['estado'] = lstControl.SelectedItem

        txtControl = self.dialog.getControl('txtCodigoPostal')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo CODIGO POSTAL no puede estar vacío.'
            txtControl.setFocus()
            return message
        cp=txtControl.Text.strip('_')
        if len(cp)<5:
            message='El campo CODIGO POSTAL esta incompleto.'
            txtControl.setFocus()
            return message
        self.emisor['codigoPostal'] = cp

        txtControl = self.dialog.getControl('txtAutorizacionOng')
        txtControl2 = self.dialog.getControl('txtFechaOng')
        if self.dialog.getControl('optOng').State:
            if self.unogui.validate(txtControl,'Vacio'):
                message = 'El campo No DE AUTORIZACION no puede estar vacío'
                txtControl.setFocus()
                return message
            if txtControl2.Date == 0:
                message = 'El campo FECHA DE AUTORIZACION no puede estar vacío'
                txtControl2.setFocus()
                return message
            else:
                self.emisor['fechaAutorizacion'] = self.util.getDateFromControl(txtControl2.Date)
                if self.emisor['fechaAutorizacion'] > self.util.today():
                    message = 'El campo FECHA DE AUTORIZACION es incorrecto, es una fecha futura'
                    return message
            self.emisor['fechaAutorizacion'] = str(self.util.getDateFromControl(txtControl2.Date, True))
        self.emisor['noAutorizacion'] = txtControl.Text

        lstControl = self.dm.lstRegimen
        if not lstControl.ItemCount:
            message='Agrega al menos un regimen fiscal'
            self.dialog.getControl('txtRegimen').setFocus()
            return message

        txtControl = self.dialog.getControl('txtTelefono')
        self.unogui.validate(txtControl,'Vacio')
        self.emisor['telefono'] = txtControl.Text

        txtControl = self.dialog.getControl('txtCorreo')
        if not self.unogui.validate(txtControl,'Vacio'):
            if not self.unogui.validate(txtControl,'Correo'):
                message='La dirección de correo electrónico no es valida'
                txtControl.setFocus()
                return message

        self.emisor['correo'] = txtControl.Text
        self.emisor['pais'] = self.globales['PAIS']
        self.emisor['escuela'] = self.dm.chkEscuela.State
        self.emisor['registro'] = self.dm.txtRegistroPatronal.Text
        return True

    def cmdGuardarExpedido(self):
        self.emisor.clear()
        message = self._validar_datos_expedidoen()
        if isinstance(message,str):
            self.unogui.createMsgBox({'Message':message})
        else:
            self.db.delete('expedidoen')
            if self.db.insertrow('expedidoen', self.emisor):
                message = 'Datos del emisor EXPEDIDO EN guardados correctamente'
                self.unogui.createMsgBox({'Message': message})
            else:
                message = 'No fue posible guardar los datos EXPEDIDO EN, consulte a soporte tecnico'
                self.unogui.createMsgBox({'Message': message})
        return

    def cmdLimpiarExpedido(self):
        message='Esta opción, vacía todos los campos, de esta pantalla y de la base de datos. \n\n ¿Estás seguro de continuar?'
        if self.unogui.createQuestion('Factura Libre', message):
            self.db.delete('expedidoen')
            self.dm.txtCalle2.Text = ''
            self.dm.txtNumExt2.Text = ''
            self.dm.txtNumInt2.Text = ''
            self.dm.txtColonia2.Text = ''
            self.dm.txtMunicipio2.Text = ''
            self.dm.txtCodigoPostal2.Text = ''
            self.dm.txtTelefono2.Text = ''
            self.dialog.getControl('lstEstados2').selectItemPos(0,True)
            self.dialog.getControl('txtCalle2').setFocus()
        return

    def _validar_datos_expedidoen(self):
        message=''
        txtControl = self.dialog.getControl('txtCalle2')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo CALLE no puede estar vacío'
            txtControl.setFocus()
            return message
        self.emisor['calle'] = txtControl.Text

        txtControl = self.dialog.getControl('txtNumExt2')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo NUMERO EXTERIOR no puede estar vacío, puedes usar SN'
            txtControl.setFocus()
            return message
        self.emisor['noExterior'] = txtControl.Text

        txtControl = self.dialog.getControl('txtNumInt2')
        txtControl.Text=txtControl.Text.strip().replace('|','')
        self.emisor['noInterior'] = txtControl.Text

        txtControl = self.dialog.getControl('txtColonia2')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo COLONIA no puede estar vacío.'
            txtControl.setFocus()
            return message
        self.emisor['colonia'] = txtControl.Text

        txtControl = self.dialog.getControl('txtMunicipio2')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo MUNICIPIO o DELEGACION no puede estar vacío.'
            txtControl.setFocus()
            return message
        self.emisor['municipio'] = txtControl.Text

        lstControl = self.dialog.getControl('lstEstados2')
        estado = lstControl.SelectedItemPos
        if estado<=0:
            message='Selecciona el estado de expedición'
            lstControl.setFocus()
            return message
        self.emisor['estado'] = lstControl.SelectedItem

        txtControl = self.dialog.getControl('txtCodigoPostal2')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo CODIGO POSTAL no puede estar vacío.'
            txtControl.setFocus()
            return message
        cp=txtControl.Text.strip('_')
        if len(cp)<5:
            message='El campo CODIGO POSTAL esta incompleto.'
            txtControl.setFocus()
            return message
        self.emisor['codigoPostal'] = cp

        txtControl = self.dialog.getControl('txtTelefono2')
        self.unogui.validate(txtControl, 'Vacio')
            #~ message='El campo TELEFONO esta vacío.\n\n ¿Estás seguro de dejarlo así?'
            #~ if not self.unogui.createQuestion('Factura Libre',message):
                #~ txtControl.setFocus()
                #~ return ''
        self.emisor['telefono'] = txtControl.Text
        self.emisor['pais'] = self.globales['PAIS']
        return True

    def cmdAgregarCampo(self, source):
        name = source.Model.Tag

        controls = {}
        controls['Regimen'] = 'El campo REGIMEN FISCAL no puede estar vacío'
        controls['CondicionPago'] = 'El campo CONDICION DE PAGO no puede estar vacío'
        controls['MetodoPago'] = 'El campo MÉTODO DE PAGO no puede estar vacío'
        controls['Aduana'] = 'El campo ADUANA no puede estar vacío'
        controls['Unidad'] = 'El campo UNIDAD no puede estar vacío'
        #controls['Personalizado'] = u'El CAMPO PERSONALIZADO no puede estar vacío'

        txtControl = self.dialog.getControl('txt%s' % name)
        if self.unogui.validate(txtControl,'Vacio'):
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message': controls[name]})
            return

        field = txtControl.Text.strip()
        listbox = self.dialog.getControl('lst%s' % name)
        data = listbox.getItems()
        if self.unogui.string_in_tuple(field, data):
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message': 'Este valor ya esta en la lista'})
            return

        if name == 'MetodoPago':
            return self._add_payment_method(listbox, txtControl)

        listbox.addItem(field, 0)
        txtControl.Text = ''
        return

    def _add_payment_method(self, lst, txt):
        value = txt.Text.strip()

        if not value in PAYMENT_METHODS:
            msg = 'El método de pago no esta en el catalogo del SAT'
            util.msgbox(msg, TYPE_MSG['ERROR'])
            return

        code = PAYMENT_METHODS[value]
        data = {'method': value, 'code': code}
        self.db.insertrow('payment_methods', data)
        lst.addItem(value, 0)
        txt.Text = ''
        return

    def _remove_payment_method(self, lst):
        msg = '¿Estás seguro de eliminar el método de pago seleccionado?'
        if util.question(msg) == BUTTON_CLICK['NO']:
            return
        where = "method='{}'".format(lst.SelectedItem)
        self.db.delete('payment_methods', where)
        lst.removeItems(lst.SelectedItemPos, 1)
        return

    def cmdAgregarMoneda(self):
        txtMoneda = self.dialog.getControl('txtMoneda')
        if self.unogui.validate(txtMoneda,'Vacio'):
            message='El campo MONEDA no puede estar vacío.'
            txtMoneda.setFocus()
            self.unogui.createMsgBox({'Message':message})
            return
        data = self.db.select(('monedas',),('moneda',),"moneda='%s'" % txtMoneda.Text.lower())
        if data:
            message = 'Esta MONEDA ya se agrego'
            txtMoneda.setFocus()
            self.unogui.createMsgBox({'Message':message})
            return

        txtPrefijo = self.dialog.getControl('txtPrefijo')
        if self.unogui.validate(txtPrefijo,'Vacio'):
            message='El campo PREFIJO esta vacío.\n\n ¿Estás seguro de dejarlo así?'
            if not self.unogui.createQuestion('Factura Libre',message):
                txtPrefijo.setFocus()
                return ''

        txtSufijo = self.dialog.getControl('txtSufijo')
        if self.unogui.validate(txtSufijo,'Vacio'):
            message='El campo SUFIJO esta vacío.\n\n ¿Estás seguro de dejarlo así?'
            if not self.unogui.createQuestion('Factura Libre',message):
                txtSufijo.setFocus()
                return ''
        row = (0, txtMoneda.Text, txtPrefijo.Text, txtSufijo.Text)
        self.unogui.gridAddRow(self.dm.gridMonedas, row)
        txtMoneda.Text = ''
        txtPrefijo.Text = ''
        txtSufijo.Text = ''
        txtMoneda.setFocus()
        return

    def gridMonedas_DobleClick(self, grid):
        if grid.CurrentColumn > 1:
            grid_dm = grid.Model.GridDataModel
            col = grid.CurrentColumn
            fil = grid.CurrentRow
            msg = 'Introduce el nuevo valor.\n\nValor Actual: {}'.format(
                grid_dm.getCellData(col, fil))
            self.value = ''
            box = input_box.Dlg(self, msg)
            res = box.execute()
            if res:
                if not self.value:
                    msg = 'El nuevo valor esta vacío.\n\n¿Estás seguro de dejarlo así?'
                    if not self.unogui.createQuestion('Factura Libre', msg):
                        return
                grid_dm.updateCellData(col, fil, self.value)
        return

    def gridPersonalizados_DobleClick(self, grid):
        if grid.CurrentColumn > 0:
            grid_dm = grid.Model.GridDataModel
            col = grid.CurrentColumn
            fil = grid.CurrentRow
            msg = 'Introduce el nuevo valor.\n\nValor Actual: {}'.format(
                grid_dm.getCellData(col, fil))
            self.value = ''
            box = input_box.Dlg(self, msg)
            res = box.execute()
            if res:
                if self.value:
                    if col == 1:
                        grid_dm.updateCellData(col, fil, self.value)
                        grid_dm.updateCellData(
                            4, fil, self.value.replace(' ','').lower())
                    elif col > 1:
                        grid_dm.updateCellData(col, fil, self.value.upper())
                elif not self.value and col > 1:
                    msg = 'El nuevo valor esta vacío.\n\n¿Estás seguro de dejarlo así?'
                    if self.unogui.createQuestion('Factura Libre', msg):
                        grid_dm.updateCellData(col, fil, self.value)
        return

    #~ def gridCeldas_DobleClick(self, grid):
        #~ grid_dm = grid.Model.GridDataModel
        #~ col = grid.CurrentColumn
        #~ if col == 1:
            #~ return
        #~ fil = grid.CurrentRow
        #~ msg = 'Introduce el nuevo valor.\n\nValor Actual: {}'.format(
            #~ grid_dm.getCellData(col, fil))
        #~ self.value = ''
        #~ box = input_box.Dlg(self, msg)
        #~ res = box.execute()
        #~ if res:
            #~ if self.value:
                #~ grid_dm.updateCellData(col, fil, self.value.upper())
            #~ else:
                #~ msg = 'El nuevo valor esta vacío.\n\n¿Estás seguro de dejarlo así?'
                #~ if self.unogui.createQuestion('Factura Libre', msg):
                    #~ grid_dm.updateCellData(col, fil, '')
        #~ return

    def cmdEliminarMoneda(self):
        grid = self.dialog.getControl('gridMonedas')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona la moneda a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        moneda = grid_dm.getCellData(1,row)
        message = '¿Estás seguro de eliminar la siguiente moneda: %s?' % (moneda)
        if self.unogui.createQuestion('Factura Libre',message):
            self.dm.gridMonedas.GridDataModel.removeRow(row)
        return

    def cmdGuardarCatalogosCfdi(self):
        self.db.delete('condicionesdepago')
        data = self.dm.lstCondicionPago.StringItemList
        if data:
            self.db.executemany(
                'condicionesdepago',
                ('condiciondepago',),
                self.unogui.list_to_tuple(data))
        self.db.delete('metodosdepago')

        #~ data = self.dm.lstMetodoPago.StringItemList
        #~ if data:
            #~ self.db.executemany(
                #~ 'metodosdepago',
                #~ ('metododepago',),
                #~ self.unogui.list_to_tuple(data))

        self.db.delete('aduanas')
        data=self.dm.lstAduana.StringItemList
        if data:
            self.db.executemany(
                'aduanas',
                ('aduana',),
                self.unogui.list_to_tuple(data))
        data = self.unogui.grid_to_tuple(self.dm.gridMonedas)
        self.db.delete('monedas')
        self.db.executemany('monedas', ('moneda', 'prefijo', 'sufijo'), data)

        message = 'Datos actualizados correctamente'
        self.unogui.createMsgBox({'Message': message})
        return

    def gridMonedas_selectionChanged(self,grid):
        row = grid.CurrentRow
        if row==0:
            self.dm.cmdEliminarMoneda.Enabled=False
        else:
            self.dm.cmdEliminarMoneda.Enabled=True
        return

    def cmdAgregarImpuesto(self):
        message = self._validar_datos_impuesto()
        if isinstance(message, str):
            self.unogui.createMsgBox({'Message': message})
        else:
            impuesto = {
                'nombre': message[1], 'tasa': message[2], 'tipo': message[3]}
            self.db.insertrow('impuestos', impuesto)
            data = self.db.select(('impuestos',), order='nombre')
            self.unogui.gridAddRows(self.dm.gridImpuestos, data, True)
            self.dm.cmdEliminarImpuesto.Enabled = True
            self.dialog.getControl('lstImpuestos').selectItemPos(0, True)
            self.dm.txtTasa.Text = ''
        return

    def cmdEliminarImpuesto(self):
        grid = self.dialog.getControl('gridImpuestos')
        row = grid.CurrentRow
        if row==-1:
            message = 'Selecciona un impuesto'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        message = '¿Estás seguro de eliminar el siguiente impuesto? \n\n ' \
            'Impuesto = %s \n Tasa = %s \n Tipo = %s \n\n ESTA ACCION NO SE ' \
            'PUEDE DESHACER' % (
                grid_dm.getCellData(1,row),
                grid_dm.getCellData(2,row),
                grid_dm.getCellData(3,row))
        if self.unogui.createQuestion('Factura Libre', message):
            self.db.delete('impuestos', 'id=%s' % grid_dm.getCellData(0,row))
            self.dm.gridImpuestos.GridDataModel.removeRow(row)
            if not grid_dm.RowCount:
                self.dm.cmdEliminarImpuesto.Enabled = False
                message = 'Haz eliminado todos los impuestos, no podrás ' \
                    'agregar productos o servicios sin tener al menos un impuesto'
                self.unogui.createMsgBox({'Message': message})
        return

    def gridImpuestos_selectionChanged(self, grid):
        row = grid.CurrentRow
        if row == -1:
            return
        id_impuesto = grid.Model.GridDataModel.getCellData(0, row)
        data = self.db.select(
            ('productosimpuestos',), ('id',), 'id_impuesto=%s'%id_impuesto)
        if data:
            self.dm.cmdEliminarImpuesto.Enabled = False
        else:
            self.dm.cmdEliminarImpuesto.Enabled = True
        return

    def cmdAgregarCategoria(self):
        tree = self.dialog.getControl('treeCategorias')
        txtControl = self.dialog.getControl('txtCategoria')
        if self.unogui.validate(txtControl, 'Vacio'):
            message='El campo CATEGORIA no puede estar vacío.'
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message':message})
            return
        categoria = txtControl.Text
        sel = tree.Selection
        value = sel.DataValue
        query = self.db.select(
            ('categorias',),
            ('id',),
            "categoria='%s' and id_padre=%s" % (categoria,value))
        if query:
            message = 'Ya existe esta categoría'
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message': message})
            return
        tree_dm = tree.Model.DataModel
        new_row = self.db.insertrow(
            'categorias', {'categoria': categoria, 'id_padre': value})
        hijo = tree_dm.createNode('%s - %s' % (new_row, categoria), False)
        hijo.DataValue = new_row
        sel.appendChild(hijo)
        tree.expandNode(sel)
        txtControl.Text = ''
        txtControl.setFocus()
        return

    def cmdEliminarCategoria(self):
        tree=self.dialog.getControl('treeCategorias')
        sel=tree.Selection
        message='¿Estás seguro de eliminar la siguiente categoría: %s?' % sel.DisplayValue
        if not self.unogui.createQuestion('Factura Libre',message):
            self.dialog.getControl('txtCategoria').setFocus()
            return
        self.db.delete('categorias','id=%s' % sel.DataValue)
        parent=sel.getParent()
        parent.removeChildByIndex(parent.getIndex(sel))
        return

    def treeCategorias_selectionChanged(self,tree):
        id_categoria=tree.Selection.DataValue
        if id_categoria==0:
            self.dm.cmdEliminarCategoria.Enabled=False
        else:
            data = self.db.select(('productos',),('id',),'id_categoria=%s'%id_categoria)
            if data:
                self.dm.cmdEliminarCategoria.Enabled=False
            else:
                self.dm.cmdEliminarCategoria.Enabled=True
        return

    def _validar_datos_impuesto(self):
        message=''
        data=[0]
        lstControl = self.dialog.getControl('lstImpuestos')
        impuesto = lstControl.SelectedItemPos
        if impuesto<=0:
            message='Selecciona el tipo de impuesto'
            lstControl.setFocus()
            return message
        data.append(lstControl.SelectedItem)

        txtControl = self.dialog.getControl('txtTasa')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo TASA no puede estar vacío.'
            txtControl.setFocus()
            return message
        tasa = txtControl.Text
        tasa_temp = str(tasa).upper().strip()
        if tasa_temp == '0.0':
            tasa_temp = '0'
        where = "nombre='%s' and tasa='%s'" % (data[1], tasa_temp)
        query = self.db.select(('impuestos',),('id',),where)
        if query:
            message='Este impuesto ya está dado de alta'
            txtControl.setFocus()
            return message

        if data[1]==self.globales['IMPUESTO_IVA'] and tasa_temp==self.globales['IMPUESTO_EXENTO']:
            data.append(tasa_temp)
            data.append('Traslado')
            return tuple(data)

        if data[1]!=self.globales['IMPUESTO_IVA'] and tasa_temp==self.globales['IMPUESTO_EXENTO']:
            message='Solo el impuesto IVA puede ser exento'
            txtControl.setFocus()
            return message

        #~ if tasa_temp[0:1] == self.globales['SIGNO_MENOS']:
            #~ if (data[1]<>self.globales['IMPUESTO_IVA'] and data[1]<>self.globales['IMPUESTO_ISR']):
                #~ message=u'Solo los impuestos IVA o ISR pueden ser retenciones'
                #~ txtControl.setFocus()
                #~ return message

        try:
            tasa_f = float(tasa_temp)
            if tasa_f == 0:
                tasa_temp = '0'
        except:
            message = 'Parece que el valor de la tasa no es un número \n\n ¿Deseas agregarla de todos modos?'
            if self.unogui.createQuestion('Factura Libre',message):
                data.append(tasa_temp)
                if tasa_temp[0:1]==self.globales['SIGNO_MENOS']:
                    data.append('Retencion')
                else:
                    data.append('Traslado')
                return tuple(data)
            else:
                txtControl.setFocus()
                return ''

        if abs(tasa_f)>self.globales['LIMITE_IMPUESTO']:
            message='El valor de la tasa es incorrecto'
            txtControl.setFocus()
            return message
        elif abs(tasa_f)>LIMITE_IMPUESTO:
            message='Parece que el valor de la tasa es muy alto \n\n ¿Deseas agregarla de todos modos?'
            if not self.unogui.createQuestion('Factura Libre',message):
                txtControl.setFocus()
                return ''

        data.append(tasa_temp)
        if tasa_temp[0:1]==self.globales['SIGNO_MENOS']:
            data.append('Retencion')
        else:
            data.append('Traslado')

        return tuple(data)

    def cmdGuardarCatalogosProductos(self):
        self.db.delete('unidades')
        data = self.dm.lstUnidad.StringItemList
        if data:
            self.db.executemany(
                'unidades', ('unidad',), self.unogui.list_to_tuple(data))

        message = 'Datos actualizados correctamente'
        self.unogui.createMsgBox({'Message': message})

        if not self.dm.gridImpuestos.GridDataModel.RowCount:
            message = 'El catálogo de impuestos esta vacío, no podrás agregar ' \
                'productos o servicios sin tener al menos un impuesto'
            self.unogui.createMsgBox({'Message': message})
        return

    def cmdGuardarCamposPersonalizados(self):
        nodo = self.dialog.getControl('txtNodo')
        self.unogui.validate(nodo,'Vacio')
        atributo1 = self.dialog.getControl('txtAtributo1')
        self.unogui.validate(atributo1,'Vacio')
        atributo2 = self.dialog.getControl('txtAtributo2')
        self.unogui.validate(atributo2,'Vacio')
        if not nodo.Text and not atributo1.Text and not atributo2.Text:
            message = 'No tienes los campos necesarios para la addenda ' \
                        'personalizada, si los dejas vacíos, no podrás ' \
                        'agregar las notas y los campos personalizados a tu ' \
                        'documento XML \n\n¿Estás seguro de dejar vacíos estos campos?'
            if not self.unogui.createQuestion('Factura Libre', message):
                nodo.setFocus()
                return
        co1 = 0
        if nodo.Text:
            co1 += 1
        if atributo1.Text:
            co1 += 1
        if atributo2.Text:
            co1 += 1
        if co1 > 0 and co1 < 3:
            message = 'Debes de capturar los tres campos de la Addenda Personalizada'
            self.unogui.createMsgBox({'Message': message})
            return
        data = {'nodo': nodo.Text, 'atributo1': atributo1.Text, 'atributo2': atributo2.Text}
        self.db.update('addendapersonalizada', data)

        data = self.unogui.grid_to_tuple(self.dm.gridPersonalizados)
        self.db.delete('campospersonalizados')
        self.db.executemany('campospersonalizados',
                            ('campo', 'nodo'),
                            data)
        #~ data = self.unogui.grid_to_tuple(self.dm.gridCeldas)
        #~ self.db.delete('celdas')
        #~ self.db.executemany('celdas', ('campo', 'celda1', 'celda2'), data)

        message = 'Datos actualizados correctamente'
        self.unogui.createMsgBox({'Message': message})
        return

    def cmdCargarAddenda(self):
        self.dm.txtNodo.Text = ADDENDA_NODO
        self.dm.txtAtributo1.Text = ADDENDA_ATRIBUTO1
        self.dm.txtAtributo2.Text = ADDENDA_ATRIBUTO2
        return

    def cmdSeleccionarImpuesto(self):
        grid=self.dialog.getControl('gridImpuestos2')
        grid.setVisible(not grid.isVisible())
        #~ grid.setFocus()
        return

    def gridImpuestos2_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        self.options['id_impuesto'] = grid_dm.getCellData(0,row)
        self.dm.txtImpuestoPre.Text = '%s | %s ' % (
            grid_dm.getCellData(1,row), grid_dm.getCellData(2,row))
        grid.deselectAllRows()
        grid.setVisible(False)
        return

    def cmdAgregarDirectorio(self):
        folder = self.unogui.getFolder(self.globales['PATH_USER'])
        folder = folder.strip()
        if not folder:
            return
        if not os.access(folder, os.W_OK):
            message = 'No tienes derechos de escritura en el directorio: \n\n %s' % folder
            self.unogui.createMsgBox({'Message': message})
            return
        listbox = self.dialog.getControl('lstRutasEspejo')
        data=listbox.getItems()
        if self.unogui.string_in_tuple(folder,data):
            self.unogui.createMsgBox({'Message':'Esta ruta ya esta en la lista'})
            return
        listbox = self.dialog.getControl('lstRutasEspejo')
        listbox.addItem(folder,0)
        return

    def cmdProbarFtp(self):
        txtControl = self.dialog.getControl('txtFtpServidor')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo SERVIDOR no puede estar vacío.'
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message':message})
            return
        ftp=txtControl.Text

        txtControl = self.dialog.getControl('txtFtpUsuario')
        if self.unogui.validate(txtControl,'Vacio'):
            message='El campo USUARIO no puede estar vacío.'
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message':message})
            return
        user=txtControl.Text

        txtControl = self.dialog.getControl('txtFtpContrasena')
        if self.unogui.validate(txtControl, 'Vacio'):
            message = 'El campo CONTRASEÑA no puede estar vacío.'
            txtControl.setFocus()
            self.unogui.createMsgBox({'Message': message})
            return
        password = txtControl.Text

        message = self.util.ftptest(ftp, user, password)
        if isinstance(message,bool):
            message = 'Conexión al servidor FTP exitosa, ya puedes guardar estos datos'
            #self.dm.txtFtpContrasena.Text=''
        self.unogui.createMsgBox({'Message':message})
        return

    def cmdGuardarOpciones(self):
        self.options['id_estado'] = self.dialog.getControl('lstEstadoPre').SelectedItemPos
        self.options['id_unidad'] = self.dialog.getControl('lstUnidadPre').SelectedItemPos
        self.options['decimales'] = int(self.dm.txtDecimales.Value)
        self.options['minfolios'] = int(self.dm.txtMinFolios.Value)
        self.options['ftpservidor'] = self.dm.txtFtpServidor.Text
        self.options['ftpusuario'] = self.dm.txtFtpUsuario.Text
        self.options['ftpcontrasena'] = self.dm.txtFtpContrasena.Text
        self.options['plantilla'] = self.dm.txtPlantilla1.Text
        self.options['plantilla2'] = self.dm.txtPlantilla2.Text

        self.options['opcion1'] = self.dm.chkOpcion1.State
        self.options['opcion2'] = self.dm.chkOpcion2.State
        self.options['opcion3'] = self.dm.chkOpcion3.State
        #~ self.options['opcion4'] = self.dm.chkOpcion4.State
        self.options['opcion5'] = self.dm.chkOpcion5.State
        self.options['opcion6'] = self.dm.chkOpcion6.State
        self.options['opcion7'] = self.dm.chkOpcion7.State

        self.db.delete('rutasespejo')
        data = self.dm.lstRutasEspejo.StringItemList
        if data:
            self.db.executemany(
                'rutasespejo', ('ruta',), self.unogui.list_to_tuple(data))
        self.db.delete('opciones')
        if self.db.insertrow('opciones', self.options):
            self.db.delete('opciones2')
            options = {}
            options['opcion1'] = self.dm.chkOpcion_1.State
            options['opcion2'] = self.dm.chkOpcion_2.State
            options['opcion3'] = self.dm.chkOpcion_3.State
            options['opcion4'] = self.dm.chkOpcion_4.State
            options['opcion5'] = self.opcion_correo
            options['opcion6'] = self.dm.chkOpcion_6.State
            if self.db.insertrow('opciones2', options):
                message = 'Opciones guardadas correctamente'
                self.unogui.createMsgBox({'Message':message})
            else:
                message = 'No fue posible guardar lass opciones, consulte a soporte tecnico'
                self.unogui.createMsgBox({'Message':message})
        else:
            message='No fue posible guardar lass opciones, consulte a soporte tecnico'
            self.unogui.createMsgBox({'Message':message})

        values = {
            'file_name': self.dm.txtFileName.Text.strip(),
            'forma_pago': self.dm.chkFormaPago.State,
            'use_complements': self.dm.use_complements.State,
        }
        self._save_options(values)
        return

    def _save_options(self, values):
        for k, v in values.items():
            data = {
                'where': "campo='{}'".format(k),
                'campo': k,
                'valor': v,
            }
            self.db.update_or_insert('options', data)
        return

    def ConfigOptions(self, item=0):
        visible = bool(self.dm.optOng.State)
        if item == 0:
            self.dialog.getControl('cmdCerTest').setVisible(DEBUG)
        elif item == 1:
            controls = (
                'lblAutorizacionOng',
                'txtAutorizacionOng',
                'lblFechaOng',
                'txtFechaOng',
                )
            self.unogui.setVisible(self.dialog, controls, visible)
            if self.dm.txtRfc.Text:
                self.dm.cmdGuardarEmisor.Enabled = True
            else:
                self.dm.cmdGuardarEmisor.Enabled = False
                message = 'Aun no configuras el certificado de sellos, no ' \
                        'podrás guardar los datos del emisor hasta haber ' \
                        'capturado primero el certificado de sellos'
                self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('gridColonias').setVisible(False)
            visible = bool(self.dm.chkEscuela.State)
            self.unogui.setVisible(self.dialog, ('cmdNiveles',), visible)
        elif item == 3:
            controls = (
                'lblDonativo',
                'chkDonativo',
                )
            self.unogui.setVisible(self.dialog, controls, visible)
        elif item == 7:
            data = self.db.select(('unidades',),('unidad',))
            listbox = self.dialog.getControl('lstUnidadPre')
            self.unogui.query_to_listbox(data,listbox)
            listbox.addItem(' ',0)

            grid = self.dm.gridImpuestos2
            data=self.db.select(('impuestos',))
            if data:
                self.dialog.getControl('gridImpuestos2').deselectAllRows()
                self.unogui.gridAddRows(grid,data)
                self.dm.cmdSeleccionarImpuesto.Enabled=True
            self.dialog.getControl('gridImpuestos2').setVisible(False)

            options = self.db.select(('opciones',))[0]
            self.dialog.getControl('lstEstadoPre').selectItemPos(options[1], True)
            self.dialog.getControl('lstUnidadPre').selectItemPos(options[2], True)
            if options[3]:
                query = self.db.select(
                    ('impuestos',),
                    ("nombre || ' | ' || tasa",),
                    'id=%s' % options[3] )
                if query:
                    self.dm.txtImpuestoPre.Text = query[0][0]

            self.options['id_impuesto'] = options[3]
            self.dm.txtDecimales.Value = options[4]
            self.dm.txtMinFolios.Value = options[5]
            self.dm.txtFtpServidor.Text = options[6]
            self.dm.txtFtpUsuario.Text = options[7]
            self.dm.txtFtpContrasena.Text = options[8]
            # plantilla 9
            fields = ('id', 'opcion1', 'opcion2', 'opcion3', 'opcion4',
                        'opcion5', 'opcion6', 'opcion7')
            options = self.db.select(('opciones',), fields )[0]
            self.dm.chkOpcion1.State = options[1]
            self.dm.chkOpcion2.State = options[2]
            self.dm.chkOpcion3.State = options[3]
            #~ self.dm.chkOpcion4.State = options[4]
            self.dm.chkOpcion5.State = options[5]
            self.dm.chkOpcion6.State = options[6]
            self.dm.chkOpcion7.State = options[7]

            options = self.db.select(('opciones2',))[0]
            self.dm.chkOpcion_1.State = options[1]
            self.dm.chkOpcion_2.State = options[2]
            self.dm.chkOpcion_3.State = options[3]
            self.dm.chkOpcion_4.State = options[4]
            self.dm.chkOpcion_6.State = options[6]
            #~ self.dm.txtFileName.Text = self.db.get_option('file_name')
            self.dm.txtFileName.Text = self.options2['file_name']
            self.dm.chkFormaPago.State = self.options2['forma_pago']
            self.dm.use_complements.State = self.options2.get('use_complements', False)

        elif item == 9:
            self.emisores = self.util.get_configvalue(
                            self.globales['NODE'], EMPRESAS).split(SEPARADOR)
            self.work_paths = self.util.get_configvalue(
                            self.globales['NODE'], PATHS).split(SEPARADOR)
            data = []
            for i, v in enumerate(self.work_paths):
                data.append((i, self.emisores[i], v))
            self.unogui.gridAddRows(self.dm.gridRutas, tuple(data))
        return

    def cmdCorreoProbar(self):
        ok, server = self._validar_datos_correo()
        if not ok:
            if server:
                util.msgbox(server, TYPE_MSG['WARNING'])
            return
        if not util.is_connect():
            msg = 'Parece que no tienes conexión a Internet, \n\n ' \
                '¿Quieres omitir la prueba y activar el botón de comando ' \
                'para guardar los datos? \n\n Haz esto, solo si estas ' \
                'seguro de que todos los datos introducidos son correctos'
            if util.question(msg) == BUTTON_CLICK['YES']:
                self.dm.cmdGuardarCorreo.Enabled = True
                return
        info = {
            'files': (),
            'mail_server': server,
            'receivers': [server['user']]
        }
        try:
            send, msg = util.send_mail(info)
            if send:
                msg = 'Correo de prueba enviado correctamente, verifica su ' \
                    'recepción correcta. Ya puedes guardar estos datos'
                util.msgbox(msg)
            else:
                self.dialog.getControl('txtCorreoUsuario').setFocus()
                util.msgbox(msg, TYPE_MSG['ERROR'])
            self.dm.cmdGuardarCorreo.Enabled = send
        except Exception as e:
            log.error('MAIL: ', exc_info=True)
        return

    def cmdGuardarCorreo(self):
        ok, server = self._validar_datos_correo()
        if not ok:
            if server:
                util.msgbox(server, TYPE_MSG['WARNING'])
            return
        msg = '¿Estas seguro de guardar esta configuración de correo?'
        if util.question(msg) == BUTTON_CLICK['NO']:
            return
        mail = {}
        mail['servidor'] = server['server']
        mail['puerto'] = int(server['port'])
        mail['usuario']= server['user']
        mail['contrasena'] = server['pass']
        mail['copia'] = server['copy']
        mail['asunto'] = server['subject']
        mail['cuerpo'] = server['body']
        mail['starttls'] = server['ssl']
        self.db.delete('correo')
        if self.db.insertrow('correo', mail):
            msg = 'Datos del servidor de correo guardados correctamente'
            util.msgbox(msg)
            self.dm.cmdBorrarDatosCorreo.Enabled = True
        else:
            msg = 'No fue posible guardar los datos del servidor de ' \
                'correo, consulte a soporte tecnico'
            util.msgbox(msg, TYPE_MSG['WARNING'])
        return

    def cmdBorrarDatosCorreo(self):
        msg = 'Esta opción, vacía todos los campos, de esta pantalla y de ' \
            'la base de datos. \n\n ¿Estás seguro de continuar?'
        if util.question(msg) == BUTTON_CLICK['YES']:
            self.db.delete('correo')
            self.dm.txtCorreoServidor.Text = ''
            self.dm.txtCorreoPuerto.Value = 26
            self.dm.txtCorreoUsuario.Text = ''
            self.dm.txtCorreoContrasena.Text = ''
            self.dm.txtCorreoCopia.Text = ''
            self.dm.txtCorreoAsunto.Text = ''
            self.dm.txtCorreoCuerpo.Text = ''
            self.dm.cmdBorrarDatosCorreo.Enabled = False
            self.dm.chkSeguridad.State = False
            self.dm.cmdGuardarCorreo.Enabled = False
            msg = 'Datos borrados correctamente'
            util.msgbox(msg)
        return

    def _validar_datos_correo(self):
        message = ''
        mail = {}
        txtControl = self.dialog.getControl('txtCorreoServidor')
        if self.unogui.validate(txtControl,'Vacio'):
            msg = 'El campo SERVIDOR no puede estar vacío.'
            txtControl.setFocus()
            return False, msg
        mail['server']=txtControl.Text

        txtControl = self.dialog.getControl('txtCorreoPuerto')
        if self.unogui.validate(txtControl,'Vacio'):
            msg = 'El campo PUERTO no puede estar vacío.'
            txtControl.setFocus()
            return False, msg
        mail['port']=int(txtControl.Value)

        txtControl = self.dialog.getControl('txtCorreoUsuario')
        if self.unogui.validate(txtControl,'Vacio'):
            msg = 'El campo USUARIO no puede estar vacío.'
            txtControl.setFocus()
            return False, msg
        if not self.unogui.validate(txtControl,'Correo'):
            msg ='El campo USUARIO de un servidor de correo, generalmente ' \
                'es una cuenta de correo.\n\n¿Estás seguro de usar este ' \
                'valor?: {}'.format(txtControl.Text)
            if util.question(msg) == BUTTON_CLICK['NO']:
                txtControl.setFocus()
                return False, ''
        mail['user'] = txtControl.Text

        txtControl = self.dialog.getControl('txtCorreoContrasena')
        if self.unogui.validate(txtControl,'Vacio'):
            msg = 'El campo CONTRASEÑA no puede estar vacío.'
            txtControl.setFocus()
            return False, msg
        mail['pass'] = txtControl.Text

        txtControl = self.dialog.getControl('txtCorreoCopia')
        if self.unogui.validate(txtControl,'Vacio'):
            msg = 'El campo COPIA DE CORREO esta vacío.\n\n¿Estas seguro de ' \
                'dejarlo así?'
            if util.question(msg) == BUTTON_CLICK['NO']:
                txtControl.setFocus()
                return False, ''
        mail['copy'] = txtControl.Text

        txtControl = self.dialog.getControl('txtCorreoAsunto')
        if self.unogui.validate(txtControl,'Vacio'):
            msg ='El campo ASUNTO(Subject) no puede estar vacío.'
            txtControl.setFocus()
            return False, msg
        mail['subject'] = txtControl.Text

        txtControl = self.dialog.getControl('txtCorreoCuerpo')
        if not txtControl.Text.strip():
            msg = 'El campo CUERPO no puede estar vacío.'
            txtControl.setFocus()
            return False, msg
        mail['body'] = txtControl.Text.strip()
        mail['ssl'] = self.dm.chkSeguridad.State
        return True, mail

    def cmdAgregarRuta(self):
        folder = self.unogui.getFolder(self.globales['PATH_USER'])
        if not folder:
            return
        if not os.access(folder, os.W_OK):
            message = 'No tienes derechos de escritura en el ' \
                        'directorio: \n\n %s' % folder
            self.unogui.createMsgBox({'Message': message})
            return
        if folder in self.work_paths:
            message = 'La ruta: \n%s \n\nya esta en la lista' % folder
            self.unogui.createMsgBox({'Message': message})
            return



        emisor = self._verify_db(folder)
        row = (0, emisor, folder)
        self.unogui.gridAddRow(self.dm.gridRutas, row)
        return

    def cmdEliminarRuta(self):
        grid = self.dialog.getControl('gridRutas')
        row = grid.CurrentRow
        if row < 0:
            message = 'Selecciona la ruta a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        path = grid_dm.getCellData(2, row)
        path_db = self.util.join(path, self.globales['DB_NAME'])
        msg = ''
        if path_db == self.db.path_db:
            msg = 'Esta ruta es tu actual ruta de trabajo'
        message = 'Estas intentado quitar la siguiente ruta de trabajo:' \
                '\n\n%s\n\nDespués de guardar los cambios, ya no tendrás ' \
                'acceso a esta base de datos. %s\n\n¿Estás seguro de quitar ' \
                'esta ruta de trabajo?' % (path, msg)
        if not self.unogui.createQuestion('Factura Libre', message):
            return
        grid_dm.removeRow(row)
        if grid_dm.RowCount == 0:
            message = 'Haz quitado todas las rutas de trabajo, despúes de ' \
                    'guardar y salir, se te solicitará una nueva ruta de ' \
                    'trabajo, asegurate de que esto es lo que quieres.'
            self.unogui.createMsgBox({'Message': message})
        return

    def cmdGuardarRutas(self):
        plantilla = self.dialog.getControl('txtPlantilla1')
        if self.unogui.validate(plantilla, 'Vacio'):
            message = 'Si no estableces la ruta de la plantilla para generar ' \
                    'los archivos PDF de tus facturas, se usará la plantilla ' \
                    'predeterminada de Factura Libre.\n\n¿Estás seguro de dejarla vacía?'
            if not self.unogui.createQuestion('Factura Libre', message):
                plantilla.setFocus()
                return
        else:
            if not self.util.exists(plantilla.Text):
                message = 'No se encontró una plantilla en la ruta establecida'
                self.unogui.createMsgBox({'Message': message})
                return
            _,_,_,extension = self.util.getInfoPath(plantilla.Text)
            if extension != EXTENSION_PLANTILLA:
                message = 'La plantilla no es un archivo ODS de Calc'
                self.unogui.createMsgBox({'Message': message})
                return
        self.db.update('opciones', {'plantilla': plantilla.Text})

        #~ plantilla = self.dialog.getControl('txtPlantilla2')
        #~ if self.unogui.validate(plantilla, 'Vacio'):
            #~ message = 'Si no estableces la ruta de la plantilla para generar ' \
                    #~ 'las cotizaciones, se usará la plantilla predeterminada ' \
                    #~ 'de Factura Libre.\n\n¿Estás seguro de dejarla vacía?'
            #~ if not self.unogui.createQuestion('Factura Libre', message):
                #~ plantilla.setFocus()
                #~ return
        #~ else:
            #~ if not self.util.exists(plantilla.Text):
                #~ message = 'No se encontró una plantilla en la ruta establecida'
                #~ self.unogui.createMsgBox({'Message': message})
                #~ return
            #~ _,_,_,extension = self.util.getInfoPath(plantilla.Text)
            #~ if extension != EXTENSION_PLANTILLA:
                #~ message = 'La plantilla no es un archivo ODS de Calc'
                #~ self.unogui.createMsgBox({'Message': message})
                #~ return
        #~ self.db.update('opciones', {'plantilla2': plantilla.Text})

        grid = self.dialog.getControl('gridRutas')
        grid_dm = grid.Model.GridDataModel
        message = ''
        if grid_dm.RowCount:
            self.emisores = []
            self.work_paths = []
            for f in range(grid_dm.RowCount):
                self.emisores.append(grid_dm.getCellData(1, f))
                self.work_paths.append(grid_dm.getCellData(2, f))
            self._save_config(SEPARADOR.join(self.emisores),
                                SEPARADOR.join(self.work_paths),
                                '')
            message = 'Rutas de trabajo guardadas correctamente'
        else:
            message = 'No existen rutas de trabajo, después de guardar y ' \
                    'reiniciar el sistema, se te solicitará una nueva ruta ' \
                    'de trabajo.\n\n¿Estás seguro de borrar todas las rutas de trabajo?'
            if self.unogui.createQuestion('Factura Libre', message):
                self._save_config('', '', '')
                message = 'Se han quitado todas las rutas de trabajo correctamente'
        if message:
            self.unogui.createMsgBox({'Message': message})
        return

    def cmdAgregarPersonalizado(self):
        txtCampo = self.dialog.getControl('txtPersonalizado')
        #~ txtCelda1 = self.dialog.getControl('txtCelda1')
        #~ txtCelda2 = self.dialog.getControl('txtCelda2')
        if self.unogui.validate(txtCampo, 'Vacio'):
            message = 'El CAMPO PERSONZALIZADO no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txtCampo.setFocus()
            return
        #~ if self.unogui.validate(txtCelda1, 'Vacio'):
            #~ message = 'Si dejas la celda vacía, este campo no será agregado ' \
                        #~ 'a la representación impresa del documento (PDF)\n' \
                        #~ '\n¿Estás seguro de dejarlo así?'
            #~ if not self.unogui.createQuestion('Factura Libre', message):
                #~ txtCelda1.setFocus()
                #~ return
        row = (0,
                txtCampo.Text,
                txtCampo.Text.replace(' ', '_').lower())
        self.unogui.gridAddRow(self.dm.gridPersonalizados, row)
        txtCampo.Text = ''
        #~ txtCelda1.Text = ''
        #~ txtCelda2.Text = ''
        txtCampo.setFocus()
        return

    def cmdEliminarPersonalizado(self):
        grid = self.dialog.getControl('gridPersonalizados')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona el campo personalizado a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        campo = grid_dm.getCellData(1, row)
        message = '¿Estás seguro de eliminar el siguiente campo: %s?' % campo
        if self.unogui.createQuestion('Factura Libre', message):
            grid_dm.removeRow(row)
        return

    def cmdAgregarAddenda(self):
        try:
            nombre = self.dialog.getControl('txtAddendaNombre')
            ruta = self.dialog.getControl('txtAddendaRuta')
            if self.unogui.validate(nombre, 'Vacio'):
                message = 'El NOMBRE no puede estar vacío'
                self.unogui.createMsgBox({'Message': message})
                nombre.setFocus()
                return
            name = nombre.Text
            if self.unogui.validate(ruta, 'Vacio'):
                message = 'La ruta de la addenda esta vacía.\n\n' \
                        '¿Deseas agregar una nueva estructura de addenda vacía?'
                if not self.unogui.createQuestion('Factura Libre', message):
                    return
            d = self.db.select(('addendas',), where="nombre='%s'" % name)
            if d:
                message = 'Este nombre ya existe, selecciona otro'
                self.unogui.createMsgBox({'Message': message})
                nombre.setFocus()
                return
            path = ruta.Text
            if path:
                a = self._get_addenda(path)
                if not a:
                    return
            else:
                a = '<Addenda />'
            data = {'nombre': name, 'addenda': a}
            self.db.insertrow('addendas', data)
            data = self.db.select(('addendas',), ('id', 'nombre'))
            self.unogui.gridAddRows(self.dm.gridAddendas, data)
            self.dm.cmdEliminarAddenda.Enabled = True
            self.dm.cmdEditarAddenda.Enabled = True
            self.dm.cmdAsignarCampos.Enabled = True
        except:
            print (traceback.format_exc())
        return

    def cmdEliminarAddenda(self):
        grid = self.dialog.getControl('gridAddendas')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona la Addenda a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        id_addenda = grid_dm.getCellData(0, row)
        w = 'id_addenda=%s' % id_addenda
        d = self.db.select(('receptores',), ('id',), w)
        message = ''
        if d:
            message = '\n\nTienes receptores usando esta Addenda.'
        message = '¿Estás seguro de eliminar la siguiente Addenda: %s \n\n' \
                'ESTA ACCION NO SE PUEDE DESHACER %s' % (
                                    grid_dm.getCellData(1, row),
                                    message)
        if self.unogui.createQuestion('Factura Libre', message):
            self.db.update('receptores', {'id_addenda': 0}, w)
            self.db.delete('addendas', 'id=%s' % id_addenda)
            self.db.delete('asignaciones', 'id_addenda=%s' % id_addenda)
            grid_dm.removeRow(row)
            if not grid_dm.RowCount:
                self.dm.cmdEliminarAddenda.Enabled = False
                self.dm.cmdEditarAddenda.Enabled = False
                self.dm.cmdAsignarCampos.Enabled = False
        return

    def cmdEditarAddenda(self):
        grid = self.dialog.getControl('gridAddendas')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona la Addenda a editar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        id_addenda = grid_dm.getCellData(0, row)
        try:
            edit = editAdd.Dlg(self, id_addenda)
            edit.execute()
        except:
            print(traceback.format_exc())
        return

    def cmdAsignarCampos(self):
        grid = self.dialog.getControl('gridAddendas')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona la Addenda a asignar campos'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        id_addenda = grid_dm.getCellData(0, row)
        name_addenda = grid_dm.getCellData(1, row)
        try:
            edit = Asignar.Dlg(self, id_addenda, name_addenda)
            edit.execute()
        except:
            print(traceback.format_exc())
        return

    def _verify_db(self, path):
        return self.db.get_emisor(path)

    def _save_emisor(self, name):
        if len(self.work_paths) == 1:
            self.util.set_configvalue(self.globales['NODE'], EMPRESAS, name)
        else:
            i = self.work_paths.index(self.globales['CURRENT_PATH'])
            self.emisores[i] = name
            self.util.set_configvalue(self.globales['NODE'],
                                        EMPRESAS,
                                        SEPARADOR.join(self.emisores))
        return

    def _save_config(self, *values):
        self.util.set_configvalue(self.globales['NODE'], EMPRESAS, values[0])
        self.util.set_configvalue(self.globales['NODE'], PATHS, values[1])
        self.util.set_configvalue(self.globales['NODE'], 'Actual', values[2])
        return

    def lstReportes_itemStateChanged(self, lst):
        r = lst.SelectedItem
        w = "nombre='%s'" % r
        q = self.db.select(('reportes',), where=w)
        if q:
            self.dm.txtNombreReporte.Text = q[0][1]
            self.dm.txtSqlReporte.Text = q[0][2].replace("''", "'")
        self.dm.cmdEliminarReporte.Enabled = True
        return

    def cmdProbarSql(self):
        message = ''
        sql = self.dm.txtSqlReporte.Text.strip()
        if not sql:
            message = 'Introduce una instrucción SQL'
        elif not sql.upper().startswith('SELECT '):
            message = 'La instrucción SQL debe ser SELECT'
        if message:
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtSqlReporte').setFocus()
            return
        try:
            data = self.db.execute(sql)
            message = 'La instrucción SQL es correcta'
            self.unogui.createMsgBox({'Message': message})
        except:
            #~ print(traceback.format_exc())
            message = 'Ocurrio el siguiente error:\n\n%s' % sys.exc_info()[1]
            self.unogui.createMsgBox({'Message': message, 'Type': 'errorbox'})
        return

    def cmdAgregarReporte(self):
        message = ''
        name = self.dm.txtNombreReporte.Text.strip()
        sql = self.dm.txtSqlReporte.Text.strip()
        if not name:
            message = 'El campo Nombre no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtNombreReporte').setFocus()
            return
        if not sql:
            message = 'Introduce una instrucción SQL'
        elif not sql.upper().startswith('SELECT '):
            message = 'La instrucción SQL debe ser SELECT'
        if message:
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtSqlReporte').setFocus()
            return
        data = self.db.select(('reportes',), where="nombre='%s'" % name)
        if data:
            message = 'Este nombre de reporte ya esta dado de alta'
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtNombreReporte').setFocus()
            return
        sql2 = sql.replace("'","''")
        data = self.db.select(('reportes',), where="sql='%s'" % sql2)
        if data:
            message = 'Esta instrucción SQL, ya esta dada de alta ' \
                'en el reporte:\n\n%s' % data[0][1]
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtSqlReporte').setFocus()
            return
        try:
            data = self.db.execute(sql)
        except:
            message = 'Ocurrio el siguiente error:\n\n%s' % sys.exc_info()[1]
            self.unogui.createMsgBox({'Message': message, 'Type': 'errorbox'})
            return
        data = {'nombre': name, 'sql': sql2}
        self.db.insertrow('reportes', data)
        lst = self.dialog.getControl('lstReportes')
        lst.addItem(name, lst.ItemCount)
        self.dm.txtNombreReporte.Text = ''
        self.dm.txtSqlReporte.Text = ''
        return

    def cmdEliminarReporte(self):
        lst = self.dialog.getControl('lstReportes')
        v = lst.SelectedItem
        if not v:
            self.dm.cmdEliminarReporte.Enabled = False
            return
        message = '¿Estás seguro de eliminar el siguiente reporte?' \
                    '\n\n%s\n\n ESTA ACCION NO SE PUEDE DESHACER' % v
        if self.unogui.createQuestion('Factura Libre', message):
            lst.removeItems(lst.SelectedItemPos, 1)
            self.db.delete('reportes', "nombre='%s'" % v)
            if not lst.ItemCount:
                self.dm.cmdEliminarReporte.Enabled = False
        return

    def _get_addenda(self, path):
        from facturalibre.modulos.pyXml import ADDENDA

        a = ADDENDA()
        if a.parse(path):
            return a.xml
        else:
            self.unogui.createMsgBox({'Message': a.msg, 'Type': 'errorbox'})
            return

    def txtCodigoPostal_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            cp = event.Source.Text.strip('_')
            if len(cp) != 5:
                message = 'El Código Postal esta incompleto'
                self.unogui.createMsgBox({'Message': message})
                return
            data = self.db.get_cp_data(cp)
            if not data:
                message = 'El Código Postal: %s, no se encontró en la base ' \
                    'de datos, asegurate de que este correcto' % cp
                self.unogui.createMsgBox({'Message': message})
                return
            self.dm.txtMunicipio.Text = data[0][1]
            self.dialog.getControl('lstEstados').selectItem(data[0][2], True)
            if len(data) == 1:
                self.dm.txtColonia.Text = data[0][0]
            else:
                self.dm.txtColonia.Text = ''
                grid = self.dialog.getControl('gridColonias')
                self.unogui.gridAddRows(self.dm.gridColonias, data)
                grid.setVisible(True)
                grid.setFocus()
        return

    def gridColonias_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            self.dm.txtColonia.Text = grid_dm.getCellData(0, row)
            grid.setVisible(False)
        return

    def chkEscuela(self, source):
        visible = bool(source.State)
        self.unogui.setVisible(self.dialog, ('cmdNiveles',), visible)
        return

    def cmdNiveles(self):
        try:
            import facturalibre.ui.niveles as Niveles

            niveles = Niveles.Dlg(self.db)
            niveles.execute()
        except:
            log.error('NIVELES', exc_info=True)
        return
