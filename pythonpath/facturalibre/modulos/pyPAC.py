#!/usr/bin/python
# -*- coding: utf-8 -*-
#~ '****************************************************************************
#~ '    CLASE PARA CONSUMIR LOS SERVICIOS DEL EXCELENTE PAC ECODEX
#~ '
#~ '    Copyright (C) 2012 Mauricio Baeza Servin
#~ '    Este programa es software libre. Puede redistribuirlo y/o modificarlo
#~ '    bajo los términos de la Licencia Pública General de GNU según es
#~ '    publicada por la Free Software Foundation, bien de la versión 3 de dicha
#~ '    Licencia o bien (según su elección) de cualquier versión posterior.
#~ '
#~ '    Este programa se distribuye con la esperanza de que sea útil, pero SIN
#~ '    NINGUNA GARANTÍA, incluso sin la garantía MERCANTIL implícita o sin
#~ '    garantizar la CONVENIENCIA PARA UN PROPÓSITO PARTICULAR.
#~ '    Véase la Licencia Pública General de GNU para más detalles.
#~ '
#~ '    Debería haber recibido una copia de la Licencia Pública General junto
#~ '    con este programa. Si no ha sido así, escriba a la Free Software
#~ '    Foundation, Inc., en 675 Mass Ave, Cambridge, MA 02139, EEUU.
#~ '
#~ '    Mauricio Baeza - correopublico ARROBA mauriciobaeza.org
#~ '    20-Agosto-2013 - Actualización a la version 2 de los WebServices Ecodex
#~ '
#~ '****************************************************************************

""" Class for webservices PAC ECODEX v2 for Python 3"""

import logging
import hashlib
import random
import base64
import os
from pysimplesoap.client import SoapClient, SoapFault
from facturalibre.settings import DEBUG, LOG, PAC


log = logging.getLogger(LOG['NAME'])


class SAT(object):
    _service_estatus = 'https://consultaqr.facturaelectronica.sat.gob.mx/' \
        'consultacfdiservice.svc?wsdl'

    def __init__(self):
        self.error = ''
        self.msg = ''

    def get_estatus(self, data):
        try:
            client = SoapClient(wsdl=self._service_estatus)
            fac = '?re={rfc_emisor}&rr={rfc_receptor}&tt={total}&id={uuid}'
            fac = fac.format(**data)
            res = client.Consulta(fac)
            if 'ConsultaResult' in res:
                msg = 'Estatus: {Estado}\nCódigo de Estatus: {CodigoEstatus}'
                self.msg = msg.format(**res['ConsultaResult'])
                return True
            return False
        except SoapFault as sf:
            self.error = sf.faultstring
            return False


class ECODEX(object):
    PREFIX_NS = 'cfdi'
    PREFIX_SOAP = 'soapenv'
    CACHE = False
    TIMEOUT = 25
    TRACE = False
    # Reemplazar por el ID de integrador que te asigne ECODEX
    _rfc_integrador = 'BASM740115RW0'
    _id_integrador = PAC['id_com']
    _id_alta_emisor = ''
    #~ _url = 'https://servicios{}.ecodex.com.mx:4043/Servicio{}.svc?wsdl'
    _url = 'http://servicios{}.ecodex.com.mx:4040/Servicio{}.svc?wsdl'
    _url_up = 'https://integradex{}.ecodex.com.mx/Certificados/Upload?UUID={{}}'
    if DEBUG:
        _rfc_integrador = 'BBB010101001'
        _id_integrador = PAC['id_test']
        _id_alta_emisor = ''
        _url = 'https://pruebas{}.ecodex.com.mx:2045/Servicio{}.svc?wsdl'
        #~ _url = 'http://pruebas{}.ecodex.com.mx:2044/Servicio{}.svc?wsdl'
    _service_seguridad = ''
    _service_comprobantes = ''
    _service_timbrado = ''
    _service_repositorio = ''
    _service_clientes = ''
    _service_cancelacion = ''

    def __init__(self, rfc, new=True, solo_timbrar=True, old_server=False):
        self.rfc = rfc.strip()
        self.solo_timbrar = solo_timbrar
        self.error = None
        self.xml_send = ''
        self.xml = ''
        self.qr = None
        self._config_urls(new, old_server)

    def _config_urls(self, new, old_server):
        services = (
            'Seguridad',
            'Comprobantes',
            'Timbrado',
            'Repositorio',
            'Clientes',
            'Cancelacion'
        )
        nom = ''
        if new and not DEBUG:
            nom = 'nominas'
        elif not new and not DEBUG and not old_server:
            self._rfc_integrador = 'ULM0902275G1'
            self._id_integrador = PAC['id_ong']
            self._id_alta_emisor = ''
        self._url_up = self._url_up.format(nom)
        for s in services:
            setattr(
                self,
                '_service_{}'.format(s.lower()), self._url.format(nom, s))
        return

    def _get_token(self, id_transaccion=0, new_emisor=False):
        try:
            client = SoapClient(
                wsdl=self._service_seguridad,
                ns=self.PREFIX_NS,
                soap_ns=self.PREFIX_SOAP,
                timeout=self.TIMEOUT,
                trace=self.TRACE,
                cache=self.CACHE,
            )
            if new_emisor:
                rfc = self._rfc_integrador
            else:
                rfc = self.rfc
            retval = client.ObtenerToken(TransaccionID=id_transaccion, RFC=rfc)
            if new_emisor:
                s = '{}|{}|{}'.format(
                    self._id_integrador,
                    self._id_alta_emisor,
                    retval['Token']
                )
            else:
                s = '{}|{}'.format(self._id_integrador, retval['Token'])
            token_usuario = hashlib.sha1(s.encode()).hexdigest()
            return token_usuario
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            return False
        except AttributeError as e:
            msg = 'Get token: {}'.format(str(e))
            if DEBUG:
                msg = 'Token: Servicio de pruebas no disponible, intenta más tarde'
            self.error = msg
            log.error(msg)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Token: ', exc_info=True)
            return False

    def client_status(self):
        id_transaccion = random.randint(1, 1000000000)
        try:
            token = self._get_token(id_transaccion)
            if not token:
                return False
            client = SoapClient(
                wsdl = self._service_clientes,
                ns = self.PREFIX_NS,
                soap_ns = self.PREFIX_SOAP,
                timeout=self.TIMEOUT,
                trace=self.TRACE,
                cache=self.CACHE,
            )
            retval = client.EstatusCuenta(
                RFC = self.rfc,
                Token = token,
                TransaccionID = id_transaccion,
            )
            return retval['Estatus']
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Cliente: ', exc_info=True)
            return False

    def timbrar(self, id_cfdi=0):
        if id_cfdi:
            id_transaccion = id_cfdi
        else:
            id_transaccion = random.randint(1, 1000000000)
        token = self._get_token(id_transaccion)
        if not token:
            return False
        client = None
        try:
            log.info('Transaccion ID: {}'.format(id_transaccion))
            servicio = self._service_comprobantes
            metodo = 'SellaTimbraXML'
            if self.solo_timbrar:
                servicio = self._service_timbrado
                metodo = 'TimbraXML'
            xml = self.xml_send.encode("ascii", "xmlcharrefreplace")
            xml = xml.decode('utf-8')
            client = SoapClient(
                wsdl=servicio,
                ns=self.PREFIX_NS,
                soap_ns=self.PREFIX_SOAP,
                timeout=self.TIMEOUT,
                trace=self.TRACE,
            )
            retval = getattr(client, metodo)(
                ComprobanteXML={'DatosXML': xml},
                RFC=self.rfc,
                Token=token,
                TransaccionID=id_transaccion
            )
            self.xml = retval['ComprobanteXML']['DatosXML']
            return True
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            #~ log.debug(client.xml_request)
            #~ log.debug(client.xml_response)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Timbrado: ', exc_info=True)
            return False

    def status_xml(self, id_original=0, uuid=''):
        if not uuid and not id_original:
            self.error = 'Se requiere el UUID o el ID de la transacción original'
            return False
        if uuid:
            id_original = 0
        id_transaccion = random.randint(1, 1000000000)
        token = self._get_token(id_transaccion)
        if not token:
            return False
        try:
            servicio = self._service_repositorio
            metodo = 'EstatusComprobante'
            if self.solo_timbrar:
                servicio = self._service_timbrado
                metodo = 'EstatusTimbrado'
            client = SoapClient(
                wsdl=servicio,
                ns=self.PREFIX_NS,
                soap_ns=self.PREFIX_SOAP)
            retval = getattr(client, metodo)(
                RFC = self.rfc,
                Token = token,
                TransaccionID = id_transaccion,
                TransaccionOriginal = id_original,
                UUID=uuid
            )
            return retval['Estatus']
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Estatus XML: ', exc_info=True)
            return False

    def cancel_xml(self, uuids, id_cfdi=0):
        if id_cfdi:
            id_transaccion = id_cfdi
        else:
            id_transaccion = random.randint(1, 1000000000)
        token = self._get_token(id_transaccion)
        if not token:
            return False
        try:
            lista = []
            for u in uuids:
                lista.append({'guid': u})
            client = SoapClient(
                wsdl = self._service_cancelacion,
                ns = self.PREFIX_NS,
                soap_ns = self.PREFIX_SOAP
            )
            retval = client.CancelaMultiple(
                ListaCancelar = lista,
                RFC = self.rfc,
                Token = token,
                TransaccionID = id_transaccion
            )
            log.info(retval['Resultado'])
            return retval['Resultado']
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Cancel XML: ', exc_info=True)
            return False

    def get_acuse(self, uuid):
        id_transaccion = random.randint(1, 1000000000)
        token = self._get_token(id_transaccion)
        if not token:
            return False
        try:
            client = SoapClient(
                wsdl = self._service_cancelacion,
                ns = self.PREFIX_NS,
                soap_ns = self.PREFIX_SOAP
            )
            retval = client.RecuperarAcuses(
                RFC = self.rfc,
                Token = token,
                TransaccionID = id_transaccion,
                UUID = uuid
            )
            self.xml = retval['AcuseXML'].replace("'", '"')
            if self.xml.startswith('No se'):
                self.error = self.xml
                return False
            else:
                return True
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Acuse: ', exc_info=True)
            return False

    def get_xml(self, id_original=0, uuid=''):
        if not uuid and not id_original:
            self.error = 'Se requiere el UUID o el ID de la transacción original'
            return False
        if uuid:
            id_original = 0
        id_transaccion = random.randint(1, 1000000000)
        token = self._get_token(id_transaccion)
        if not token:
            return False
        try:
            servicio = self._service_repositorio
            metodo = 'ObtenerComprobante'
            if self.solo_timbrar:
                servicio = self._service_timbrado
                metodo = 'ObtenerTimbrado'
            client = SoapClient(wsdl=servicio, ns='cfdi', soap_ns='soapenv')
            retval = getattr(client, metodo)(
                RFC = self.rfc,
                Token = token,
                TransaccionID = id_transaccion,
                TransaccionOriginal = id_original,
                UUID=uuid
            )
            self.xml = retval['ComprobanteXML']['DatosXML']
            return True
        except SoapFault as sf:
            self.error = sf.faultstring
            log.debug(self.error)
            return False
        except Exception as e:
            self.error = 'Se agoto el tiempo de espera'
            log.error('Get XML: ', exc_info=True)
            return False

    # Solo temporal
    #~ def _cancel_tmp(self, uuids):
        #~ if DEBUG:
            #~ return False, 'Documento no cancelado, consulta a soporte técnico'
        #~ wsdl = 'https://servicios.ecodex.com.mx:4043/Servicio{}.svc?wsdl'
        #~ self._servicio_seguridad = wsdl.format('Seguridad')
        #~ self._servicio_cancelacion = wsdl.format('Cancelacion')
        #~ res = self.CancelacionesXML(uuids)
        #~ if res:
            #~ estatus = res[0]['ResultadoCancelacion']['Estatus']
            #~ if estatus == 'Cancelado':
                #~ return True, ''
            #~ else:
                #~ return False, estatus
        #~ else:
            #~ return False, 'Documento no cancelado, consulta a soporte técnico'

    #~ def _cancelacionesOtrosXML(self, rfc_receptor, uuid, id_cfdi=0):
        #~ if id_cfdi:
            #~ id_transaccion = id_cfdi
        #~ else:
            #~ id_transaccion = random.randint(1, 1000000000)
        #~ token = self._getToken(id_transaccion)
        #~ if not token:
            #~ return False
        #~ try:
            #~ client = SoapClient(
                #~ wsdl = self._servicio_cancelacion,
                #~ ns = PREFIX_NS,
                #~ soap_ns = PREFIX_SOAP
            #~ )
            #~ retval = client.CancelaOtros(
                #~ RFCEmisor = self.rfc,
                #~ RFCReceptor = rfc_receptor,
                #~ Token = token,
                #~ TransaccionID = id_transaccion,
                #~ UUID = uuid
            #~ )
            #~ return retval['Resultado']
        #~ except SoapFault as sf:
            #~ self.error = sf
            #~ return False

    # Va a desaparecer
    #~ def _cancelarXML(self, uuid, id_cfdi=0):
        #~ if id_cfdi:
            #~ id_transaccion = id_cfdi
        #~ else:
            #~ id_transaccion = random.randint(1, 1000000000)
        #~ token = self._getToken(id_transaccion)
        #~ if not token:
            #~ return False
        #~ try:
            #~ servicio = self._servicio_repositorio
            #~ metodo = 'CancelaComprobante'
            #~ if self.solo_timbrar:
                #~ servicio = self._servicio_timbrado
                #~ metodo = 'CancelaTimbrado'
            #~ client = SoapClient(wsdl=servicio, ns='cfdi', soap_ns='soapenv')
            #~ retval = getattr(client, metodo)(
                #~ RFC = self.rfc,
                #~ Token = token,
                #~ TransaccionID = id_transaccion,
                #~ UUID=uuid
            #~ )
        #~ except SoapFault as sf:
            #~ self.error = sf
            #~ return False
        #~ else:
            #~ return retval['Cancelada']

    #~ def ObtenerQR(self, uuid='', path=''):
        #~ if not uuid:
            #~ self.error = 'Se requiere el UUID para recupear su QR'
            #~ return False
        #~ id_transaccion = random.randint(1, 1000000000)
        #~ token = self._getToken(id_transaccion)
        #~ if not token:
            #~ return False
        #~ try:
            #~ servicio = self._servicio_repositorio
            #~ metodo = 'ObtenerQR'
            #~ if self.solo_timbrar:
                #~ servicio = self._servicio_timbrado
                #~ metodo = 'ObtenerQRTimbrado'
            #~ client = SoapClient(wsdl=servicio, ns=PREFIX_NS, soap_ns=PREFIX_SOAP)
            #~ retval = getattr(client, metodo)(
                #~ RFC = self.rfc,
                #~ Token = token,
                #~ TransaccionID = id_transaccion,
                #~ UUID = uuid
            #~ )
        #~ except SoapFault as sf:
            #~ self.error = sf.faultcode, sf.faultstring, sf.message
            #~ return False
        #~ else:
            #~ self.qr = base64.decodestring(retval['QR']['Imagen'])
            #~ if path:
                #~ path = os.path.join(path, '%s.bmp' % uuid)
                #~ f = open(path, 'wb')
                #~ f.write(self.qr)
                #~ f.close()
            #~ return True

    #~ def ClienteRegistrar(self, data={}):
        #~ id_transaccion = random.randint(1, 1000000000)
        #~ try:
            #~ token = self._getToken(id_transaccion, True)
            #~ if not token:
                #~ return False
            #~ client = SoapClient(
                #~ wsdl = self._servicio_clientes,
                #~ ns = PREFIX_NS,
                #~ soap_ns = PREFIX_SOAP
            #~ )
            #~ retval = client.Registrar(
                #~ Emisor = {
                    #~ 'RFC': data['rfc'],
                    #~ 'RazonSocial': data['razonsocial'],
                    #~ 'CorreoElectronico': data['correo']},
                #~ RfcIntegrador = self._rfc_integrador,
                #~ Token = token,
                #~ TransaccionID = id_transaccion
            #~ )
            #~ return retval
        #~ except SoapFault as sf:
            #~ self.error = sf.faultstring
            #~ return False


class FINKOK(object):
    if DEBUG:
        _user = 'pruebasfinkok@correolibre.org'
        _pass = '4MV7mbs'
        _servicio_timbrado = 'http://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl'
        _servicio_cancelacion = 'http://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl'
    else:
        _user = ''
        _pass = ''
        _servicio_timbrado = ''
        _servicio_cancelacion = ''
    ERRORES = {
        '302': 'Sello inválido',
        '307': 'El CFDI ya esta timbrado',
        '705': 'Estructura inválida del XML',
    }

    def __init__(self, rfc=''):
        self.rfc = rfc
        self.error = None
        self.xml_send = ''
        self.xml = ''

    def ClienteEstatus(self):
        return False

    def TimbrarXML(self, id_cfdi=0):
        try:
            servicio = self._servicio_timbrado
            metodo = 'stamp'
            client = SoapClient(wsdl=servicio, soap_ns=PREFIX_SOAP)
            retval = getattr(client, metodo)(
                # for python 2  base64.encodestring(self.xml_send)
                #~ xml = base64.encodestring(self.xml_send).decode('utf-8'),
                xml = base64.encodestring(
                    self.xml_send.encode('utf-8')).decode('utf-8'),
                username = self._user,
                password = self._pass
            )
        except SoapFault as sf:
            self.error = sf.faultstring
            return False
        else:
            if retval['stampResult']['xml']:
                print (1, retval['stampResult']['UUID'])
                #~ print (2, retval['stampResult']['CodEstatus'])
                self.xml = retval['stampResult']['xml']      #.encode('utf-8') # for python 2
                return True
            else:
                error = retval['stampResult']['Incidencias'][0]['Incidencia']
                msg = error
                if error['CodigoError'] in self.ERRORES:
                    msg = self.ERRORES[error['CodigoError']]
                self.error = {
                    'CodigoError': error['CodigoError'],
                    'MensajeIncidencia': msg,
                }
                return False

    def ObtenerXML(self):
        try:
            servicio = self._servicio_timbrado
            metodo = 'stamped'
            client = SoapClient(wsdl=servicio, soap_ns=PREFIX_SOAP)
            retval = getattr(client, metodo)(
                xml = base64.encodestring(self.xml_send).decode('utf-8'),
                username = self._user,
                password = self._pass
            )
        except SoapFault as sf:
            self.error = (sf.faultstring,)
            return False
        else:
            if retval['stampedResult']['xml']:
                self.xml = retval['stampedResult']['xml']      #.encode('utf-8') # for python 2
                return True
            else:
                self.error = retval
                return False

    def EstatusXML(self, uuid):
        try:
            servicio = self._servicio_timbrado
            metodo = 'query_pending'
            client = SoapClient(wsdl=servicio, soap_ns=PREFIX_SOAP)
            retval = getattr(client, metodo)(
                uuid = uuid,
                username = self._user,
                password = self._pass
            )
        except SoapFault as sf:
            self.error = sf.faultstring
            return False
        else:
            return retval['query_pendingResult']

    def CancelacionesXML(self, uuids, cer, key):
        try:
            #~ tmp = {'uuids': {'string': uuids}}
            servicio = self._servicio_cancelacion
            metodo = 'cancel'
            client = SoapClient(wsdl=servicio, soap_ns=PREFIX_SOAP)
            retval = getattr(client, metodo)(
                UUIDS = {'uuids': {'string': uuids}},
                username = self._user,
                password = self._pass,
                taxpayer_id = self.rfc,
                #~ cer = open(cer, 'rb').read().decode(),
                cer = base64.b64encode(open(cer, 'rb').read()).decode(),
                key = base64.b64encode(open(key, 'rb').read()).decode()
            )
            #~ print (1, client.xml_request.decode())
        except SoapFault as sf:
            self.error = sf.faultstring
            return False
        else:
            return retval

