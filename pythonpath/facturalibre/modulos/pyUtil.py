# -*- coding: utf-8 -*-

import uno
import traceback
import os
import sys
import tempfile
import subprocess
import urllib.request, urllib.error, urllib.parse
import ftplib
import datetime
import time
import smtplib
import re
import shutil
import zipfile
from socket import timeout
from threading import Thread
from functools import reduce
from xml.etree import ElementTree as ET
from smtplib import SMTPException, SMTPAuthenticationError
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Size
from com.sun.star.awt import Point
import pyqrcode
from com.sun.star.awt import KeyEvent
from com.sun.star.util import Date
#~ from facturalibre.modulos.pyPAC import SAT

#~ PAC_USE = 1
#~ if PAC_USE == 1:
    #~ from facturalibre.modulos.pyPAC import ECODEX as PAC
#~ elif PAC_USE == 2:
    #~ from facturalibre.modulos.pyPAC import FINKOK as PAC

PRE = '{http://www.sat.gob.mx/cfd/3}'
PREFIX = {
    '2.0': '{http://www.sat.gob.mx/cfd/2}',
    '2.2': '{http://www.sat.gob.mx/cfd/2}',
    '3.0': '{http://www.sat.gob.mx/cfd/3}',
    '3.2': '{http://www.sat.gob.mx/cfd/3}',
}
PRE2 = '{http://www.sat.gob.mx/TimbreFiscalDigital}'


class PACTimbres(Thread):
    def __init__(self, rfc, label, ce, new_server=True):
        self.rfc = rfc
        self.label = label
        self.ce = ce
        self.new_server = new_server
        Thread.__init__(self)

    def run(self):
        timbres = 0
        res, data = self.ce(self.rfc, self.new_server)
        if res:
            timbres = data['TimbresDisponibles']
            self.label.Label = 'Folios PAC: {}'.format(timbres)


class Util(object):

    def __init__(self):
        self.ctx = uno.getComponentContext()
        self.sm = self.ctx.getServiceManager()
        self.desktop = self.sm.createInstanceWithContext(
                            'com.sun.star.frame.Desktop',
                            self.ctx)
        self.pc = self.getOS()
        self.ver = self.get_version()

    def get_ns(self, path_file):
        events = "start-ns",
        ns = {}
        for event, elem in ET.iterparse(path_file, events):
            if event == "start-ns":
                if elem[0] in ns and ns[elem[0]] != elem[1]:
                    # NOTE: It is perfectly valid to have the same prefix refer
                    #     to different URI namespaces in different parts of the
                    #     document. This exception serves as a reminder that this
                    #     solution is not robust.    Use at your own peril.
                    raise KeyError("Duplicate prefix with different URI found.")
                #~ ns[elem[0]] = "{%s}" % elem[1]
                ns[elem[0]] = elem[1]
        return ns

    def kill(self, path):
        try:
            os.remove(path)
        except:
            pass
        return

    def get_version(self):
        cp = self.sm.createInstance(
            'com.sun.star.configuration.ConfigurationProvider')
        arg = uno.createUnoStruct('com.sun.star.beans.PropertyValue')
        arg.Name = 'nodepath'
        arg.Value = '/org.openoffice.Setup/Product'
        node = cp.createInstanceWithArguments(
            'com.sun.star.configuration.ConfigurationAccess', (arg,))
        return float(node.getByName('ooSetupVersion'))

    def thisDocument(self):
        #~ desktop = self.sm.createInstanceWithContext('com.sun.star.frame.Desktop', self.ctx)
        return self.desktop.getCurrentComponent()

    def get_name(self, xml, format1, format2):
        tree = ET.fromstring(xml)
        data = tree.attrib.copy()
        del data['sello']
        del data['certificado']
        pre = PREFIX[data['version']]
        if not 'serie' in data:
            data['serie'] = ''
        data['fecha'] = data['fecha'].partition('T')[0]
        data['folio'] = int(data['folio'])
        node = tree.find('{}Emisor'.format(pre))
        data['emisor_rfc'] = node.attrib['rfc']
        data['emisor_nombre'] = node.attrib['nombre']
        node = tree.find('{}Receptor'.format(pre))
        data['receptor_rfc'] = node.attrib['rfc']
        data['receptor_nombre'] = node.attrib['nombre']
        if format1:
            try:
                name = format1.format(**data)
                name = name.replace("'", "").replace(" ", "_").replace(
                    ",", "").replace(".", "")
                return name
            except:
                return format2.format(**data)
        else:
            return format2.format(**data)

    def get_estatus(self, xml):
        data = {}
        tree = ET.fromstring(xml)
        version = tree.attrib['version']
        if float(version) < 3:
            msg = 'No es un CFDI. Su comprobante es un CFD y no se puede ' \
                'validar ante el SAT'
            return False, msg
        #~ print (version)
        node = tree.find('%sEmisor' % PRE)
        data['total'] = tree.attrib['total']
        data['rfc_emisor'] = node.attrib['rfc']
        node = tree.find('%sReceptor' % PRE)
        data['rfc_receptor'] = node.attrib['rfc']
        node = tree.find('%sComplemento' % PRE)
        node = node.find('%sTimbreFiscalDigital' % PRE2)
        data['uuid'] = node.attrib['UUID']
        sat = SAT()
        res = sat.get_estatus(data)
        if res:
            return True, sat.msg
        else:
            return False, sat.error

    def get_cadena(self, xslt, xml):
        from lxml import etree
        styledoc = etree.parse(xslt)
        transform = etree.XSLT(styledoc)
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        doc = etree.fromstring(xml.encode('utf-8'), parser=parser)
        result = str(transform(doc))
        return result

    def calc_to_date(self, value):
        if value:
            d = datetime.date.fromordinal(int(value) + 693594)
            return d
        return ''

    def get_active_doc(self):
        doc = self.desktop.getCurrentComponent()
        return doc

    def get_id_timbrado(self, serie, folio):
        data = {'A': 2, 'B': 3, 'C': 5, 'D': 7, 'E': 11, 'F': 13, 'G': 17,
            'H': 19, 'I': 23, 'J': 29, 'K': 31, 'L': 37, 'M': 41, 'N': 43,
            'O': 47, 'P': 53, 'Q': 59, 'R': 61, 'S': 67, 'T': 71, 'U': 73,
            'V': 79, 'W': 83, 'X': 89, 'Y': 97, 'Z': 101}
        r = reduce(lambda x, y: x*y, [data[l] for l in serie])
        return r + folio

    def get_epoch(self, date):
        f = '%Y-%m-%d %H:%M:%S'
        e = int(time.mktime(time.strptime(date, f)))
        return e

    def get_addenda(self, path):
        return

    def get_date_from_timestamp(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp)

    def get_date_from_string(self, date, time=False):
        if time:
            return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.datetime.strptime(date, '%Y-%m-%d')

    def setUtilDate(self, date=None):
        if not date:
            date = self.now()
        elif isinstance(date, str):
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        util_date = Date()
        util_date.Day = date.day
        util_date.Month = date.month
        util_date.Year = date.year
        return util_date

    def compress_files(self, path, source):
        z = zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED)
        for f in source:
            if self.exists(f):
                _,name,_,_ = self.getInfoPath(f)
                z.write(f, name)
        z.close()
        return

    def get_timbres(self, rfc, label, new_server=True):
        t = PACTimbres(rfc, label, getattr(self, 'client_status'), new_server)
        t.start()
        return

    def client_status(self, rfc, server=True):
        pac = PAC(rfc, server)
        data = pac.client_status()
        if data:
            return True, data
        else:
            return False, pac.error

    def timbrar(self, rfc, xml, id_cfd, new_server=True):
        pac = PAC(rfc, new_server)
        pac.xml_send = xml
        ok = pac.timbrar(id_cfd)
        if ok:
            timbrada = pac.xml
            timbrada = timbrada.replace("'", "''")
            xml = ET.fromstring(timbrada)
            timbre = xml.find('%sComplemento' % PRE)
            timbre = timbre.find('%sTimbreFiscalDigital' % PRE2)
            data = {
                'xml': timbrada,
                'uuid': timbre.attrib['UUID'],
                'fecha': timbre.attrib['FechaTimbrado'].replace('T',' '),
            }
            return True, data
        else:
            return False, pac.error

    def status_xml(self, rfc, id_original, new_server=True):
        pac = PAC(rfc, new_server)
        data = pac.status_xml(id_original)
        if data:
            return True, data
        else:
            return False, pac.error

    def cancel_cfdi(self, rfc, uuid, new_server=True):
        pac = PAC(rfc, new_server)
        if isinstance(uuid, list):
            list_uuid = uuid
        else:
            list_uuid = [uuid]
        cancel = pac.cancel_xml(list_uuid)
        if cancel:
            estatus = cancel[0]['ResultadoCancelacion']['Estatus']
            #~ print ('ESTATUS 1', estatus)
            if estatus == 'Cancelado':
                return True, ''
            #~ elif estatus == 'No Encontrado':
                #~ return self.cancel_cfdi(rfc, uuid, False)
                #~ return self.cancel_old_server(rfc, list_uuid)
            else:
                return False, estatus
        #~ else:
            #~ return False, pac.error
        else:
            return self.cancel_old_server(rfc, list_uuid)

    def cancel_old_server(self, rfc, list_uuid):
        pac = PAC(rfc, new=False, old_server=True)
        cancel = pac.cancel_xml(list_uuid)
        if cancel:
            estatus = cancel[0]['ResultadoCancelacion']['Estatus']
            if estatus == 'Cancelado':
                return True, ''
            else:
                return False, estatus
        else:
            return False, pac.error

    def cancel_cfdi_nomina(self, rfc, uuid, new_server=True):
        pac = PAC(rfc, new_server)
        if isinstance(uuid, list):
            list_uuid = uuid
        else:
            list_uuid = [uuid]
        cancel = pac.cancel_xml(list_uuid)
        if cancel:
            return True, cancel
        else:
            return False, pac.error

    def get_xml(self, rfc, id_original, new_server=True):
        pac = PAC(rfc, new_server)
        data = pac.get_xml(id_original)
        if data:
            return True, pac.xml
        else:
            return False, pac.error

    #~ def CancelaNomina(self, rfc, uuids):
        #~ pac = PAC(rfc)
        #~ res = pac.CancelacionesXML(uuids)
        #~ if res:
            #~ return True, res
        #~ else:
            #~ return False, pac.error

    def get_acuse(self, rfc, uuid, new_server=True):
        pac = PAC(rfc, new_server)
        res = pac.get_acuse(uuid)
        if res:
            return res, pac.xml
        else:
            return res, pac.error

    def getCBB(self, data):
        scale = 10
        path = self.getPathTemp('cbb.png')
        code = pyqrcode.QRCode(data, mode='binary')
        code.png(path, scale)
        return path

    def set_configvalue(self, nodepath, prop, value):
        cp = self.sm.createInstanceWithContext(
            'com.sun.star.configuration.ConfigurationProvider', self.ctx)
        node = PropertyValue()
        node.Name = 'nodepath'
        node.Value = nodepath
        try:
            config_writer = cp.createInstanceWithArguments(
                'com.sun.star.configuration.ConfigurationUpdateAccess', (node,))
            config_writer.setPropertyValue(prop, value)
            config_writer.commitChanges()
        except:
            raise

    def get_configvalue(self, nodepath, prop):
        cp = self.sm.createInstanceWithContext(
                'com.sun.star.configuration.ConfigurationProvider', self.ctx)
        node = PropertyValue()
        node.Name = 'nodepath'
        node.Value = nodepath
        try:
            cr = cp.createInstanceWithArguments(
                    'com.sun.star.configuration.ConfigurationAccess', (node,))
            if cr and (cr.hasByName(prop)):
                return cr.getPropertyValue(prop)
        except:
            return None

    def clear_sel(self, sel):
        #~ new = []
        #~ for f in sel:
            #~ if (f > -1):
                #~ new.append(f)
        #~ return tuple(new)
        return tuple([x for x in sel if x >-1])

    def getKeyEvent(self):
        return KeyEvent()

    def newDoc(self, doc=1):
        typeDoc = {1: 'private:factory/scalc'}
        oDoc = self.desktop.loadComponentFromURL(typeDoc[doc], '_blank', 0, ())
        return oDoc

    def position(self, obj, x, y):
        pos = Point()
        pos.X = x
        pos.Y = y
        obj.setPosition(pos)
        return

    def size(self, obj, width, height):
        tam = Size()
        tam.Width = width
        tam.Height = height
        obj.setSize(tam)
        return

    def rgb(self, r, g, b):
        return int('%02x%02x%02x' % (r, g, b), 16)

    def createInstance(self, service):
        return self.sm.createInstance(service)

    def execute(self, path):
        sys = self.sm.createInstance('com.sun.star.system.SystemShellExecute')
        sys.execute(path, '', 0)
        return

    def past_month(self):
        hoy = datetime.date.today()
        if hoy.month == 1:
            mes = 12
            ano = hoy.year - 1
        else:
            mes = hoy.month - 1
            ano = hoy.year
        ayer = datetime.date(ano, mes, 1)
        return ayer

    def format_date(self, date_string, template, f=''):
        #~ "%Y-%m-%dT%H:%M:%S"
        if not f:
            f = '%Y-%m-%d'
        if isinstance(date_string, str):
            date = datetime.datetime.strptime(date_string, f)
        else:
            date = date_string
        return date.strftime(template)

        #'%A, %d de %B de %Y'
    def format_date2(self, date_string):
        m = (
            '',
            'Enero',
            'Febrero',
            'Marzo',
            'Abril',
            'Mayo',
            'Junio',
            'Julio',
            'Agosto',
            'Septiembre',
            'Octubre',
            'Noviembre',
            'Diciembre'
        )
        d = (
            'Lunes',
            'Martes',
            'Miércoles',
            'Jueves',
            'Viernes',
            'Sábado',
            'Domingo'
        )
        date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return date.strftime('{}, %d de {} de %Y'.format(
            d[date.weekday()], m[date.month]))

    def date_to_calc(self, date_string, only_date=False):
        tmp = '%d/%m/%Y %H:%M:%S'
        if only_date:
            tmp = '%d/%m/%Y'
        l = datetime.datetime.strptime(date_string, tmp)
        l_calc = l.toordinal() - 693594
        return l_calc

    def monthfromdata(self, date_string, idioma='en'):
        #~ La fecha se toma de la consulta de datos de una base
        #~ Por lo que viene en formato aaaa-mm-dd hh:mm:ss
        month = int(date_string[5:7])
        en = ('January','February','March','April','May','June','July','August','September','October','November','December')
        de = ('Januar','Februar ','März ','April ','Mai ','Juni ','Juli ','August ','September ','Oktober ','November','Dezember')
        es = ('Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Setiembre','Octubre','Noviembre','Diciembre')
        it = ('Gennaio ','Febbraio ','Marzo ','Aprile ','Maggio ','Giugno ','Luglio ','Agosto ','Settembre','Ottobre','Novembre ','Dicembre')
        pt = ('Janeiro ','Fevereiro ','Março ','Abril ','Maio','Junho ','Julho ','Agosto ','Setembro ','Outubro ','Novembro ','Dezembro')
        fr = ('Janvier ','Février ','Mars ','Avril ','Mai ','Juin ','Juillet ','Août ','Septembre ','Octobre ','Novembre ','Décembre')
        lang_months = {'en':en, 'de':de, 'es':es, 'it':it, 'pt':pt}
        month_tuple = lang_months[idioma]
        return month_tuple[month - 1]

    def remove(self, path):
        if self.exists(path):
            os.remove(path)
        return

    def is_save(self, path):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return True
        else:
            return False

    def copy(self, source, path):
        shutil.copy(source, path)
        return

    #~ def copy_xml(self, data, paths, pdf=''):
        #~ new_path_xml = ''
        #~ for path in paths:
            #~ if not self.exists(path[0]):
                #~ continue
            #~ new_path = self.join(path[0], data['year'])
            #~ if not self.exists(new_path):
                #~ os.makedirs(new_path)
            #~ new_path = self.join(new_path, data['month'])
            #~ if not self.exists(new_path):
                #~ os.makedirs(new_path)
            #~ new_path_xml = self.join(new_path, data['name'])
            #~ xml = self.to_pretty(data['xml'])
            #~ self.save_file(new_path_xml, xml)
            #~ if pdf:
                #~ shutil.copy(pdf, new_path)
        #~ return new_path_xml

    def copy_pdf(self, data, paths, pdf=''):
        new_path = ''
        for path in paths:
            if not self.exists(path[0]):
                continue
            new_path = self.join(path[0], data[0])
            if not self.exists(new_path):
                os.makedirs(new_path)
            new_path = self.join(new_path, data[1])
            if not self.exists(new_path):
                os.makedirs(new_path)
            if pdf:
                try:
                    shutil.copy(pdf, new_path)
                except:
                    pass
        return

    def join(self, *paths):
        return os.path.join(*paths)

    def exists(self, path):
        return os.path.exists(path)

    def access(self, path):
        return os.access(path, os.W_OK)

    def get_paths_work(self, path):
        paths = ()
        if os.path.exists(path):
            data = self.load_file(path)
            paths = tuple(data.split('|'))
        return paths

    def match(self, pattern, text):
        return re.match(pattern, text)

    def enviar_correo(self, data):
        if data[0] == 2:
            return self.__enviar_correo_cliente(data)
        elif data[0] == 3:
            return self.__enviar_correo_smtp(data)

    def __enviar_correo_smtp(self, data):
        # id, servidor, puerto, usuario, contrasena, copia, asunto, cuerpo
        files = data[1]
        receivers = data[2]
        mail_server = data[3]
        sender = mail_server[3]
        subject = 'Enviamos su factura {serie}{folio}'
        if mail_server[6]:
            subject = mail_server[6]
        body = 'Le enviamos su archivo XML y PDF\n\nGracias'
        if mail_server[7]:
            body = mail_server[7]
        for f in files:
            if f.endswith('.xml'):
                break
        fields = self._make_fields(f)
        html = self._make_info(body, fields)
        subject = self._make_info(subject, fields, True)
        date_now = datetime.datetime.now().strftime("%m/%d/%Y %H:%M")
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = ', '.join(receivers)
        message['CC'] = mail_server[5]
        #~ message['Date'] = date_now
        message['Subject'] = subject
        message.attach(MIMEText(html, 'html'))
        for f in files:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload( open(f,"rb").read() )
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                "attachment; filename=%s" % os.path.basename(f))
            message.attach(part)

        if mail_server[5]:
            receivers += mail_server[5].split(',')
        try:
            smtpObj = smtplib.SMTP(mail_server[1], mail_server[2], timeout=10)
            if mail_server[8]:
                smtpObj.ehlo()
                smtpObj.starttls()
                smtpObj.ehlo()
            smtpObj.login(mail_server[3], mail_server[4])
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
        except Exception as e:
            print(e)
            return False
        else:
            return True

    def _make_fields(self, path):
        xml = ET.parse(path).getroot()
        data = xml.attrib.copy()
        del(data['certificado'])
        receptor = xml.find('%sReceptor' % PRE)
        data['receptor_nombre'] = receptor.attrib['nombre']
        data['receptor_rfc'] = receptor.attrib['rfc']
        return data

    def _make_info(self, data, fields, subject=False):
        if subject:
            return data.format(**fields)
        html = data.format(**fields).replace('\n', '<br/>')
        html = """
        <html>
          <head></head>
          <body>
            <p>%s
            </p>
          </body>
        </html>
        """.format(html)
        return html

    def __enviar_correo_cliente(self, data):
        if self.getOS() == 'win32':
            ssmail = self.sm.createInstance(
                        'com.sun.star.system.SimpleSystemMail')
        else:
            ssmail = self.sm.createInstance(
                        'com.sun.star.system.SimpleCommandMail')
        client = ssmail.querySimpleMailClient()
        mail = client.createSimpleMailMessage()
        ccmail = []
        if data[2]:
            mail.setRecipient(data[2][0])
            if len(data[2]) > 1:
                ccmail = data[2][1:]
        subject = 'Enviamos su factura'
        if data[3]:
            ccmail = data[3][5].split(',') + ccmail
            if data[3][6]:
                subject = data[3][6]
        mail.setCcRecipient(tuple(ccmail))
        attach = tuple([self.systemToUrl(path) for path in data[1]])
        mail.setAttachement(attach)

        for f in data[1]:
            if f.endswith('.xml'):
                break
        fields = self._make_fields(f)
        subject = self._make_info(subject, fields, True)

        mail.setSubject(subject)
        try:
            client.sendSimpleMailMessage(mail, 0)
        except:
            return False
        else:
            return True

    def sendmail(self, data, to=''):
        # servidor, puerto, usuario, contrasena, copia, asunto, cuerpo
        sender = data['usuario']
        if to:
            receivers = to
        else:
            receivers = [data['usuario']]
        try:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            message = MIMEMultipart()
            message['From'] = data['usuario']
            message['To'] = data['usuario']
            message['CC'] = data['copia']
            message['Date'] = date_now
            message['Subject'] = data['asunto']
            part = MIMEText(data['cuerpo'], _subtype='html', _charset='utf-8')
            message.attach(part)
            smtpObj = smtplib.SMTP(data['servidor'], data['puerto'], timeout=10)
            if data['starttls']:
                smtpObj.ehlo()
                smtpObj.starttls()
                smtpObj.ehlo()
                print ('OK')
            print (1, data['usuario'], data['contrasena'])
            smtpObj.login(data['usuario'], data['contrasena'])
            print (2, 'Connect')
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
        except SMTPAuthenticationError as e:
            #~ print (3, e)
            #~ if e[0] == 534
            return 535, 'Nombre de usuario o contraseña erroneo'
        except SMTPException as e:
            return 100, str(e)
        except Exception as e:
            return 200, str(e)
        else:
            return True, ''

    def getDateFromControl(self, date, with_time=False):
        if with_time:
            now = datetime.datetime.now()
            date = datetime.datetime(date.Year, date.Month, date.Day,
                                        now.hour, now.minute, now.second)
        else:
            date = datetime.date(date.Year, date.Month, date.Day)
        return date

    def load_file(self, path, binary=False):
        if not self.exists(path):
            return ''
        if binary:
            file_tmp = open(path, 'rb')
        else:
            file_tmp = open(path)
        data = file_tmp.read()
        file_tmp.close()
        return data

    def save_file(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            if isinstance(data, str):
                f.write(data)
            else:
                f.write(data.decode('utf-8'))
        return

    def cer_en_sat(self, ftpsat, folder, cer):
        ftp = ftplib.FTP(ftpsat)
        temp = self.getPathTemp()
        try:
            ftp.login('anonymous', '')
            ftp.cwd(folder)
            ftp.retrbinary('RETR %s' % cer, open(temp, 'wb').write)
            return True
        except:
            return False
        finally:
            ftp.close()
        return

    def ftptest(self, ftps, user, pas):
        try:
            ftp = ftplib.FTP(ftps, timeout=10)
            ftp.login(user, pas)
            ftp.close()
            return True
        except ftplib.all_errors as e:
            if str(e) == 'timed out':
                msg = 'Se agoto el tiempo de espera. Verifica la dirección del servidor y de tener conexión a Internet activa'
            else:
                code = str(e).split(None, 1)
                if isinstance(code, list):
                    code = int(code[0])
                if code == 530:
                    msg = 'El nombre de usuario o contraseña es incorrecto, verifica estos datos. CUIDADO, si haces demasiados intentos fallidos, tu proveedor podría bloquearte tu cuenta.'
                else:
                    msg = e
            return msg

    def send_ftp(self, ftp_data, data):
        try:
            #~ path, name = os.path.split(xml)
            #~ path, month = os.path.split(path)
            #~ path, year = os.path.split(path)
            ftp = ftplib.FTP(ftp_data[0], timeout=10)
            ftp.login(ftp_data[1], ftp_data[2])
            try:
                ftp.cwd(data['year'])
            except:
                ftp.mkd(data['year'])
                ftp.cwd(data['year'])
            try:
                ftp.cwd(data['month'])
            except:
                ftp.mkd(data['month'])
                ftp.cwd(data['month'])
            path_xml = self.getPathTemp(data['name'])
            self.save_file(path_xml, data['xml'])
            f = open(path_xml, 'rb')
            ftp.storbinary('STOR %s' % data['name'], f)
            f.close()
        except ftplib.all_errors as e:
            print(e)
        finally:
            ftp.close()
        return

    def hay_conexion(self):
        try:
            response = urllib.request.urlopen('http://google.com', timeout=5)
            return True
        except:
            return False

    def now(self, s=False, minutes=0):
        n = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        if s:
            return n.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return n.replace(microsecond=0)

    def today(self):
        now = datetime.datetime.now()
        date = datetime.date(now.year, now.month, now.day)
        return date

    def strptime(self, date_string, format_user, timestamp=False):
        tmp = datetime.datetime.strptime(date_string, format_user)
        if timestamp:
            tmp = tmp.timestamp()
        return tmp

    def strftime(self, date, format_s):
        return date.strftime(format_s)

    def verificar_programas(self):
        if self.pc == 'linux':
            try:
                #~ pipe = subprocess.Popen('openssl', stdout=subprocess.PIPE)
                pipe = subprocess.Popen('xsltproc', stdout=subprocess.PIPE)
                return True
            except:
                return False
        else:
            return True

    def call(self, arg):
        if self.pc == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            pipe = subprocess.Popen(arg, stdout=subprocess.PIPE, startupinfo=startupinfo)
        else:
            pipe = subprocess.Popen(arg, stdout=subprocess.PIPE)
        text = pipe.communicate()[0]
        return text.decode('utf-8')

    def getPathTemp(self, name=''):
        if name:
            temp = os.path.join(tempfile.gettempdir(), name)
        else:
            temp = tempfile.mkstemp()[1]
        return temp

    def check_extension(self, path, extension):
        data = self.getInfoPath(path)
        return data[3]==extension

    def getInfoPath(self, path):
        path, filename = os.path.split(path)
        name, extension = os.path.splitext(filename)
        data = [path, filename, name, extension]
        return data

    def getOS(self):
        return sys.platform

    def getPathExtension(self, extid):
        """Get extension directory url from the extension id."""
        pip_name = '/singletons/com.sun.star.deployment.PackageInformationProvider'
        if self.ctx.hasByName(pip_name):
            pip = self.ctx.getByName(pip_name)
            return pip.getPackageLocation(extid)
        return ''

    def getPathUser(self):
        path = self.sm.createInstance('com.sun.star.util.PathSettings')
        return self.urlToSystem(path.Work)

    def urlToSystem(self, path):
        return uno.fileUrlToSystemPath(path)

    def systemToUrl(self, path):
        return uno.systemPathToFileUrl(path)

    def setPropertiesValues(self, properties):
        properties_list = []
        l = len(properties)
        for i in range(0, l, 2):
            pv = PropertyValue()
            pv.Name = properties[i]
            pv.Value = properties[i+1]
            properties_list.append(pv)
        #if len(properties_list)==1:
        #    return pv
        #else:
        return tuple(properties_list)

    def msgbox(self,message):
        desktop = self.sm.createInstanceWithContext('com.sun.star.frame.Desktop', self.ctx )
        doc = desktop.getCurrentComponent()
        oToolkit = self.sm.createInstance('com.sun.star.awt.Toolkit')
        rec = uno.createUnoStruct('com.sun.star.awt.Rectangle')
        oParentWin = doc.getCurrentController().getFrame().getContainerWindow()
        title = 'Util Debug'
        if isinstance(message,str):
            message = str(message)
        else:
            message = str(message)
        if self.ver == 4.1:
            oMsgBox = oToolkit.createMessageBox(
                oParentWin, rec, 'infobox', 1, title, message)
        else:
            oMsgBox = oToolkit.createMessageBox(
                oParentWin, 'infobox', 1, title, message)
        return oMsgBox.execute()

    def debug(self, data, name_file='debug.log'):
        if not os.path.exists(os.path.dirname(name_file)):
            name_file = self.join(self.getPathUser(), os.path.basename(name_file))
        debug_file = open(name_file, 'a')
        debug_file.write(str(datetime.datetime.now()) + ' ' + str(data) + '\n')
        debug_file.close()
        return

    def mri(self,target):
        try:
            mri = self.sm.createInstanceWithContext('mytools.Mri',self.ctx)
            mri.inspect(target)
        except:
            self.msgbox('Parece que no esta instalada la extensión MRI')

    def chext(self, path, exten = ".xml", newext = '-registrado.xml'):
        if path[-4:] == exten:
            newname = path[0:-4:] + newext
            print (newname)
            os.rename(path, newname)
        if path[-4:] == exten.upper():
            newname = path[0:-4:] + newext
            print (newname)
            os.rename(path, newname)
