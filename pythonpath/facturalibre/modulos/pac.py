import sys
import logging
#~ import random
import hashlib
import datetime
import time
from xml.sax.saxutils import escape
#~ from xml.dom import minidom
from requests import Request, Session, exceptions
try:
    import facturalibre.modulos.xml2dict as xml2dict
    from facturalibre.settings import DEBUG, PRE, PAC
except ImportError:
    import xml2dict
    DEBUG = True
    PRE = {
        '2.0': '{http://www.sat.gob.mx/cfd/2}',
        '2.2': '{http://www.sat.gob.mx/cfd/2}',
        '3.0': '{http://www.sat.gob.mx/cfd/3}',
        '3.2': '{http://www.sat.gob.mx/cfd/3}',
        'TIMBRE': '{http://www.sat.gob.mx/TimbreFiscalDigital}',
    }


TIMEOUT = 10


def get_epoch(date=None):
    if date is None:
        date = datetime.datetime.now()
    if isinstance(date, str):
        f = '%Y-%m-%d %H:%M:%S'
        e = int(time.mktime(time.strptime(date, f)))
    else:
        e = int(time.mktime(date.timetuple()))
    return e


class SAT(object):
    _webservice = 'https://consultaqr.facturaelectronica.sat.gob.mx/' \
        'consultacfdiservice.svc'
    _soap = """<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope
        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <soap:Header/>
        <soap:Body>
        <Consulta xmlns="http://tempuri.org/">
            <expresionImpresa><![CDATA[?re={emisor_rfc}&rr={receptor_rfc}&tt={total}&id={uuid}]]></expresionImpresa>
        </Consulta>
        </soap:Body>
    </soap:Envelope>"""

    def __init__(self):
        self.error = ''
        self.msg = ''

    def _check_fault(self, res):
        FAULT = 's:Fault'
        self.error = ''
        res = res['s:Envelope']['s:Body']
        if FAULT in res:
            if res[FAULT]['faultcode'] == 'a:InternalServiceFault':
                self.error = 'Error de comunicación con el SAT, valida otra factura primero'
                return True, ''
            self.error = 'Código de Error: {}\n\n{}'.format(
                res[FAULT]['faultcode'], res[FAULT]['faultstring'])
            return True, ''
        return False, res

    def get_estatus(self, data):
        data['emisor_rfc'] = escape(data['emisor_rfc'])
        data['receptor_rfc'] = escape(data['receptor_rfc'])
        data = self._soap.format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"http://tempuri.org/IConsultaCFDIService/Consulta"',
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        s.verify = False
        req = Request('POST', self._webservice, data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=5)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return False
            self.msg = res['ConsultaResponse']['ConsultaResult']['a:Estado']
            return True
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
        except Exception as e:
            print (e)
        return False


class Ecodex(object):
    #~ _ID_TEST = '2b3a8764-d586-4543-9b7e-82834443f219'
    #~ _ID_COM = ''
    #~ _ID_ONG = ''
    _WSDL = 'http://servicios{}.ecodex.com.mx:4040/Servicio{}.svc'
    #~ _WSDL = 'https://servicios{}.ecodex.com.mx:4043/Servicio{}.svc'
    _REST = {
        'obtener_token': 'http://api.ecodex.com.mx/token',
        'obtener_clave': 'http://api.ecodex.com.mx/api/Certificados/Clave',
        'get_documento': 'http://api.ecodex.com.mx/api/Documentos/',
    }
    if DEBUG:
        _WSDL = 'http://pruebas{}.ecodex.com.mx:2044/Servicio{}.svc'
        _REST = {
            'obtener_token': 'http://pruebasapi.ecodex.com.mx/token',
            'obtener_clave': 'http://pruebasapi.ecodex.com.mx/api/Certificados/Clave',
            'get_documento': 'http://pruebasapi.ecodex.com.mx/api/Documentos/',
        }

    _ACTIONS = {
        'obtener_token': 'http://Ecodex.WS.Model/2011/CFDI/Seguridad/ObtenerToken',
        'estatus_cuenta': 'http://Ecodex.WS.Model/2011/CFDI/ServicioClientes/EstatusCuenta',
        'estatus_timbrado': 'http://Ecodex.WS.Model/2011/CFDI/Timbrado/EstatusTimbrado',
        'obtener_timbrado': 'http://Ecodex.WS.Model/2011/CFDI/Timbrado/ObtenerTimbrado',
        'timbra_xml': 'http://Ecodex.WS.Model/2011/CFDI/Timbrado/TimbraXML',
        'cancela_multiple': 'http://Ecodex.WS.Model/2011/CFDI/Cancelaciones/CancelaMultiple',
        'recuperar_acuse': 'http://Ecodex.WS.Model/2011/CFDI/Cancelaciones/RecuperarAcuses',
    }
    _SOAPENV =  """<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope
            xmlns:cfdi="http://Ecodex.WS.Model/2011/CFDI"
            xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
            <soapenv:Header/>
            <soapenv:Body>
                {}
            </soapenv:Body>
        </soapenv:Envelope>
        """
    _SOAP = {
        'obtener_token': _SOAPENV.format("""
            <cfdi:SolicitudObtenerToken>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
            </cfdi:SolicitudObtenerToken>"""),
        'estatus_cuenta': _SOAPENV.format("""
            <cfdi:SolicitudEstatusCuenta>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:Token>{user_token}</cfdi:Token>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
            </cfdi:SolicitudEstatusCuenta>"""),
        'estatus_timbrado': _SOAPENV.format("""
            <cfdi:SolicitudEstatusTimbrado>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:Token>{user_token}</cfdi:Token>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
                <cfdi:TransaccionOriginal>{transaccion_original}</cfdi:TransaccionOriginal>
                <cfdi:UUID>{uuid}</cfdi:UUID>
            </cfdi:SolicitudEstatusTimbrado>"""),
        'obtener_timbrado': _SOAPENV.format("""
            <cfdi:SolicitudObtenerTimbrado>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:Token>{user_token}</cfdi:Token>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
                <cfdi:TransaccionOriginal>{transaccion_original}</cfdi:TransaccionOriginal>
                <cfdi:UUID>{uuid}</cfdi:UUID>
            </cfdi:SolicitudObtenerTimbrado>"""),
        'timbra_xml': _SOAPENV.format("""
            <cfdi:SolicitudTimbraXML>
                <cfdi:ComprobanteXML>
                    <DatosXML xmlns="http://Ecodex.WS.Model/2011/CFDI">{xml}</DatosXML>
                </cfdi:ComprobanteXML>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:Token>{user_token}</cfdi:Token>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
            </cfdi:SolicitudTimbraXML>"""),
        'cancela_multiple': _SOAPENV.format("""
            <cfdi:SolicitudCancelaMultiple>
                <cfdi:ListaCancelar>{uuids}</cfdi:ListaCancelar>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:Token>{user_token}</cfdi:Token>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
            </cfdi:SolicitudCancelaMultiple>"""),
        'recuperar_acuse': _SOAPENV.format("""
            <cfdi:SolicitudAcuse>
                <cfdi:RFC>{rfc}</cfdi:RFC>
                <cfdi:Token>{user_token}</cfdi:Token>
                <cfdi:TransaccionID>{transaccion_id}</cfdi:TransaccionID>
                <cfdi:UUID>{uuid}</cfdi:UUID>
            </cfdi:SolicitudAcuse>"""),
    }

    def __init__(self, rfc, new_server=True, ong=False):
        self.rfc = rfc
        self.error = ''
        self.WS = {}
        self.ID_INTEGRADOR = PAC['id_com']
        self._config(new_server, ong)

    def _config(self, new_server, ong):
        web_services = {
            'seguridad': 'Seguridad',
            'clientes': 'Clientes',
            'timbrado': 'Timbrado',
            'cancelacion': 'Cancelacion',
        }
        nominas = ''
        if new_server and not DEBUG:
            nominas = 'nominas'
        for k, v in web_services.items():
            self.WS[k] = self._WSDL.format(nominas, v)
        if ong:
            self.ID_INTEGRADOR = PAC['id_ong']
        if DEBUG:
            self.ID_INTEGRADOR = PAC['id_test']

    #~ def _decode_cfdi(self, xml):
        #~ cfdi = minidom.parseString(xml)
        #~ return cfdi.toprettyxml(encoding='UTF-8').decode()

    def _check_fault(self, res):
        self.error = ''
        FAULT = 's:Fault'
        fault = res['s:Envelope']['s:Body']
        if FAULT in fault:
            self.error = 'Código de Error: {}\n\n{}'.format(
                fault[FAULT]['faultcode'], fault[FAULT]['faultstring']['#text'])
            #~ print ('CHECK FAULT', self.error)
            return True, ''
        return False, fault

    def _get_token(self, transaccion_id):
        method = 'obtener_token'
        data = {
            'rfc': self.rfc,
            'transaccion_id': transaccion_id
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['seguridad'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            token = res['RespuestaObtenerToken']['Token']
            s = '{}|{}'.format(self.ID_INTEGRADOR, token)
            user_token = hashlib.sha1(s.encode()).hexdigest()
            return user_token
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except exceptions.RequestException as e:
            print ('TOKEN', e)
        return ''

    def estatus_cuenta(self):
        #~ transaccion_id = random.randint(1, 1000000000)
        transaccion_id = get_epoch()
        user_token = self._get_token(transaccion_id)
        if not user_token:
            return ''

        method = 'estatus_cuenta'
        data = {
            'rfc': self.rfc,
            'user_token': user_token,
            'transaccion_id': transaccion_id
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['clientes'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            return res['RespuestaEstatusCuenta']['Estatus']
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print ('Estatus Cuenta', e)
            return ''

    def estatus_timbrado(self, id_original=0, uuid=''):
        #~ transaccion_id = random.randint(1, 1000000000)
        transaccion_id = get_epoch()
        user_token = self._get_token(transaccion_id)
        if not user_token:
            return ''
        if uuid:
            id_original = 0
        method = 'estatus_timbrado'
        data = {
            'rfc': self.rfc,
            'user_token': user_token,
            'transaccion_id': transaccion_id,
            'transaccion_original': id_original,
            'uuid': uuid,
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['timbrado'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            return res['RespuestaEstatusTimbrado']['Estatus']
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print ('Estatus Timbrado', e)
            return ''

    def obtener_timbrado(self, id_original=0, uuid=''):
        #~ transaccion_id = random.randint(1, 1000000000)
        transaccion_id = get_epoch()
        user_token = self._get_token(transaccion_id)
        if not user_token:
            return ''
        if uuid:
            id_original = 0
        method = 'obtener_timbrado'
        data = {
            'rfc': self.rfc,
            'user_token': user_token,
            'transaccion_id': transaccion_id,
            'transaccion_original': id_original,
            'uuid': uuid,
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['timbrado'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            cfdi = res['RespuestaObtenerTimbrado']['ComprobanteXML']['DatosXML']
            #~ return self._decode_cfdi(cfdi)
            return cfdi
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print ('Obtener Timbrado', e)
            return ''

    def timbra_xml(self, xml, id_original=0):
        #~ print ('ID Original', id_original)
        user_token = self._get_token(id_original)
        if not user_token:
            return ''
        method = 'timbra_xml'
        data = {
            'xml': escape(xml.encode('ascii', 'xmlcharrefreplace').decode('utf-8')),
            'rfc': self.rfc,
            'user_token': user_token,
            'transaccion_id': id_original,
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['timbrado'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            cfdi = res['RespuestaTimbraXML']['ComprobanteXML']['DatosXML']
            #~ return self._decode_cfdi(cfdi)
            return cfdi
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print ('Timbra XML', e)
        return ''

    def cancela_multiple(self, uuid):
        transaccion_id = get_epoch()
        user_token = self._get_token(transaccion_id)
        if not user_token:
            return ''
        guid = '<guid xmlns="http://Ecodex.WS.Model/2011/CFDI">{}</guid>'
        if isinstance(uuid, str):
            uuids = guid.format(uuid)
        else:
            uuids = ''.join([guid.format(u) for u in uuid])
        method = 'cancela_multiple'
        data = {
            'uuids': uuids,
            'rfc': self.rfc,
            'user_token': user_token,
            'transaccion_id': transaccion_id,
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['cancelacion'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            res = res['RespuestaCancelaMultiple']['Resultado']['ResultadoCancelacion']
            if not isinstance(res, list):
                res = [res]
            return res
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
        except Exception as e:
            print ('Cancelacion', e)
        return

    def recuperar_acuse(self, uuid):
        transaccion_id = get_epoch()
        user_token = self._get_token(transaccion_id)
        if not user_token:
            return ''
        method = 'recuperar_acuse'
        data = {
            'uuid': uuid,
            'rfc': self.rfc,
            'user_token': user_token,
            'transaccion_id': transaccion_id,
        }
        data = self._SOAP[method].format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"{}"'.format(self._ACTIONS[method]),
            'Content-length': len(data),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        s = Session()
        req = Request('POST', self.WS['cancelacion'], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            res = xml2dict.parse(response.text)
            ok, res = self._check_fault(res)
            if ok:
                return ''
            return res['RespuestaRecuperarAcuse']['AcuseXML'].replace("'", '"')
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print ('Recuperar Acuse', e)
        return

    def _get_token_rest(self):
        method = 'obtener_token'
        data = {
            'rfc': self.rfc,
            'integrador': self.ID_INTEGRADOR,
            'grant_type': 'authorization_token',
        }
        headers = {'Content-type': 'application/json'}
        s = Session()
        req = Request('POST', self._REST[method], data=data, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            return response.json()['access_token']
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print (e)
        return

    def obtener_clave(self):
        method = 'obtener_clave'
        token = self._get_token_rest()
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer {}'.format(token)
        }
        s = Session()
        req = Request('GET', self._REST[method], headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            return response.json()
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print (e)
        return

    def get_doc_rest(self, hash_original):
        method = 'get_documento'
        token = self._get_token_rest()
        url = self._REST[method] + hash_original
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer {}'.format(token),
        }
        s = Session()
        req = Request('GET', url, headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            return response.json()
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print (e)
        return

    def get_docs_rest(self, hash_original):
        method = 'get_documento'
        token = self._get_token_rest()
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer {}'.format(token),
        }
        s = Session()
        req = Request('GET', self._REST[method], headers=headers)
        prepped = req.prepare()
        try:
            response = s.send(prepped, timeout=TIMEOUT)
            return response.json()
        except exceptions.Timeout:
            self.error = 'Tiempo de espera agotado'
            print (self.error)
        except Exception as e:
            print (e)
        return


if __name__ == '__main__':
    pac = Ecodex('AAA010101AAA')




