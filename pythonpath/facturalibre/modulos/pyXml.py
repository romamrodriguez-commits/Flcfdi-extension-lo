# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET
import subprocess
import sys
import traceback
import re
from io import StringIO
import logging

from facturalibre.settings import LOG, FIELDS_CFDI, PRE, RFC_EXTRANJERO, WIN
from . import util


log = logging.getLogger(LOG['NAME'])


XSLTPROC = 'xsltproc%s'
OPENSSL = 'openssl%s'
XSLT = 'cadena%s.xslt'
ALGORITMO = '-sha1'


class CFDXML(object):

    def __init__(self, caller, id_cfd):
        self.PATH_BIN = util.join(
            util.path_to(util.get_path_extension(), False), 'bin')
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        #~ self.globales = caller.globales
        self.id_cfd = id_cfd
        self.comprobante = None
        self.xml = ''
        self.format_s = '{0:.%sf}' % self.db.select_field('opciones', 'decimales')
        self.prefijo = self.db.select_field('sat', 'prefijo')
        self.algoritmo = '-%s' % self.db.select_field('sat', 'algoritmo')
        self.escuela = False
        self.sat_donataria = {}
        self.sat_ine = {}
        self.regimenfiscal = ''
        self.otros_impuestos = False
        self.path_pem = caller.path_pem
        self.complemento = None

    def _call(self, arg):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        pipe = subprocess.Popen(arg, stdout=subprocess.PIPE, startupinfo=startupinfo)
        return

    def _sellar(self):
        ext = ''
        path_openssl = OPENSSL % ext
        path_xsltproc = XSLTPROC % ext
        if util.get_os() == WIN:
            ext = '.exe'
            path_openssl = util.join(self.PATH_BIN, OPENSSL % ext)
            path_xsltproc = util.join(self.PATH_BIN, XSLTPROC % ext)
        version = self.comprobante.attrib['version']
        path_xslt = util.join(self.PATH_BIN, XSLT % version)
        path_xml = util.get_path_temp()
        util.save_file(path_xml, ET.tostring(self.comprobante))
        args = '"{1}" "{2}" "{3}" | "{0}" dgst -sha1 -sign "{4}" | "{0}" enc ' \
            '-base64 -A'.format(
            path_openssl, path_xsltproc, path_xslt, path_xml, self.path_pem)
        sello = subprocess.check_output(args, shell=True).decode()
        if sello:
            self.comprobante.attrib['sello'] = sello
            return True
        else:
            print ('Sello NO generado')
            return False

    def generate_xml(self):
        self.__comprobante()
        self.__emisor()
        self.__receptor()
        self.__conceptos()
        self.__impuestos()
        self._complements()
        self.__otrosimpuestos()
        self._sellar()
        self.xml = ET.tostring(
            self.comprobante, encoding="unicode").replace('&#10;','&#13;')
        return self.xml

    def __comprobante(self):
        atributos = {}
        iedu_shema = ''
        donat_shema = ''

        donativo = self.db.select(
            ('cfdfacturas',), ('donativo',), 'id=%s' % self.id_cfd)[0][0]
        if donativo:
            data = self.db.select(
                ('sat',), ('donat1', 'donat2', 'dversion', 'dleyenda'))[0]
            atributos['xmlns:donat'] = data[0]
            donat_shema = ' %s' % data[1]
            self.sat_donataria['version'] = data[2]
            self.sat_donataria['leyenda'] = data[3]
            data = self.db.select(
                ('emisor',), ('tipo', 'noAutorizacion', 'fechaAutorizacion'))[0]
            self.sat_donataria['noAutorizacion'] = data[1]
            self.sat_donataria['fechaAutorizacion'] = data[2].split(' ')[0]
        sat = self.db.select(('sat',), ('xmlcfdi1', 'xmlcfdi2', 'xmlcfdi3'))[0]
        atributos['xmlns:cfdi'] = sat[0]
        atributos['xmlns:xsi'] = sat[1]
        self.escuela = bool(self.db.select_field('emisor', 'escuela'))
        if self.escuela:
            sat_iedu = self.db.select(('sat',), ('edu1', 'edu2'))[0]
            if sat_iedu:
                atributos['xmlns:iedu'] = sat_iedu[0]
                iedu_shema = ' %s' % sat_iedu[1]

        # Complement INE
        where = 'id_cfdi="{}" AND code_name="ine"'.format(self.id_cfd)
        ine = self.db.select(('cfdi_complements',), where=where)
        shema_ine = ''
        if ine and ine[0]:
            #~ where = 'code_name="ine"'
            #~ data = self.db.select(('complements',), where=where)
            shema_ine = ' http://www.sat.gob.mx/ine http://www.sat.gob.mx/sitio_internet/cfd/ine/ine10.xsd'
            atributos['xmlns:ine'] = 'http://www.sat.gob.mx/ine'
            self.sat_ine = util.loads(ine[0][3])
            self.sat_ine['Version'] = '1.0'

        where = "nombre!='IVA' AND nombre!='ISR' AND nombre!='IEPS' AND id_cfd=%s" % self.id_cfd
        otros_impuestos = self.db.select(('cfdimpuestos',), ('nombre',), where)
        implocal_shema = ''
        if otros_impuestos:
            atributos['xmlns:implocal'] = 'http://www.sat.gob.mx/implocal'
            implocal_shema = ' http://www.sat.gob.mx/implocal http://www.sat.gob.mx/sitio_internet/cfd/implocal/implocal.xsd'
            self.otros_impuestos = True

        atributos['xsi:schemaLocation'] = sat[2] + donat_shema + iedu_shema + implocal_shema + shema_ine
        fields = (
            'version',
            'serie',
            'folio',
            'fecha',
            'formaDePago',
            'noCertificado',
            'condicionesDePago',
            'subTotal',
            'descuento',
            'motivoDescuento',
            'TipoCambio',
            'Moneda',
            'total',
            'tipoDeComprobante',
            'metodoDePago',
            'LugarExpedicion',
            'NumCtaPago',
            'certificado'
        )
        data = self.db.select(('cfdfacturas',), fields, 'id=%s' % self.id_cfd)[0]

        for index, value in enumerate(fields):
            new_value = ''
            if index == 3:
                new_value = str(data[index]).replace(' ','T')
            elif index == 7 or index == 8 or index == 10 or index == 12:
                if index == 8 and not data[index]:
                    # Sin descuento
                    continue
                new_value = self.format_s.format(data[index])
            else:
                if isinstance(data[index], int):
                    new_value = str(data[index])
                else:
                    if data[index].strip():
                        new_value = str(data[index])
            if new_value:
                atributos[value] = new_value
        self.comprobante = ET.Element('cfdi:Comprobante', atributos)
        return

    def __emisor(self):
        atributos = {}
        fields = ('rfc', 'nombre')
        data = self.db.select(('emisor',), fields)[0]
        for index, value in enumerate(fields):
            if data[index]:
                atributos[value] = str(data[index])
        emisor = ET.SubElement(self.comprobante, 'cfdi:Emisor', atributos)

        atributos = {}
        fields = ('calle', 'noExterior', 'noInterior', 'colonia', 'referencia', 'municipio', 'estado', 'pais', 'codigoPostal')
        data = self.db.select(('emisor',), fields)[0]
        for index, value in enumerate(fields):
            if data[index]:
                if data[index].strip():
                    atributos[value] = str(data[index])
        ET.SubElement(emisor, 'cfdi:DomicilioFiscal', atributos)

        atributos = {}
        data = self.db.select(('expedidoen',), fields)
        if data:
            data = data[0]
            for index, value in enumerate(fields):
                if data[index]:
                    if data[index].strip():
                        atributos[value] = str(data[index])
            ET.SubElement(emisor, 'cfdi:ExpedidoEn', atributos)

        atributos = {}
        if self.regimenfiscal:
            atributos['Regimen'] = self.regimenfiscal
        else:
            atributos['Regimen'] = self.db.select(('cfdfacturas',), ('regimen',), 'id=%s' % self.id_cfd)[0][0]

        ET.SubElement(emisor, 'cfdi:RegimenFiscal', atributos)

        return

    def __receptor(self):
        id_receptor = data = self.db.select(('cfdfacturas',), ('id_cliente',), 'id=%s' % self.id_cfd)[0][0]
        atributos = {}
        fields = ('rfc', 'nombre')
        data = self.db.select(('receptores',), fields, 'id=%s' % id_receptor)[0]
        for index, value in enumerate(fields):
            if data[index]:
                atributos[value] = str(data[index])
        receptor = ET.SubElement(self.comprobante, 'cfdi:Receptor', atributos)

        atributos = {}
        fields = ('calle', 'noExterior', 'noInterior', 'colonia', 'referencia', 'municipio', 'estado', 'pais', 'codigoPostal')
        data = self.db.select(('receptores',), fields, 'id=%s' % id_receptor)[0]
        for index, value in enumerate(fields):
            if data[index]:
                if data[index].strip():
                    atributos[value] = str(data[index])
        ET.SubElement(receptor, 'cfdi:Domicilio', atributos)

        return

    def __conceptos(self):
        conceptos = ET.SubElement(self.comprobante, 'cfdi:Conceptos')
        fields = (
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
            'autorizacion')
        data = self.db.select(('cfddetalle',), fields, 'id_cfd=%s' % self.id_cfd)
        for row in data:
            atributos = {}
            atributos[fields[0]] = self.format_s.format(row[0])
            atributos[fields[1]] = str(row[1])
            atributos[fields[2]] = str(row[2])
            atributos[fields[3]] = str(row[3])
            atributos[fields[4]] = self.format_s.format(row[4])
            atributos[fields[5]] = self.format_s.format(row[5])
            concepto = ET.SubElement(conceptos, 'cfdi:Concepto', atributos)
            if row[6]:
                atributos = {}
                atributos[fields[6]] = str(row[6])
                atributos[fields[7]] = str(row[7])[0:10]
                atributos[fields[8]] = str(row[8])
                ET.SubElement(concepto, 'cfdi:InformacionAduanera', atributos)
            if row[9]:
                if row[9].strip():
                    ET.SubElement(
                        concepto, 'cfdi:CuentaPredial', {'numero': str(row[9])})
            if row[14].strip():
                complemento = ET.SubElement(concepto, 'cfdi:ComplementoConcepto')
                atributos = {}
                atributos[fields[10]] = row[10]
                atributos['nombreAlumno'] = row[11]
                atributos['CURP'] = row[12]
                atributos['nivelEducativo'] = row[13]
                atributos['autRVOE'] = row[14]
                ET.SubElement(complemento, 'iedu:instEducativas', atributos)
        return

    def __impuestos(self):
        atributos = {}
        totalImpuestosRetenidos = self.db.select(
            ('cfdfacturas',),
            ('totalImpuestosRetenidos',),
            'id=%s' % self.id_cfd)[0][0]
        if not totalImpuestosRetenidos is None:
            atributos['totalImpuestosRetenidos'] = self.format_s.format(totalImpuestosRetenidos)
        totalImpuestosTrasladados = self.db.select(('cfdfacturas',), ('totalImpuestosTrasladados',), 'id=%s' % self.id_cfd)[0][0]
        if not totalImpuestosTrasladados is None:
            atributos['totalImpuestosTrasladados'] = self.format_s.format(totalImpuestosTrasladados)
        impuestos = ET.SubElement(self.comprobante, 'cfdi:Impuestos', atributos)

        if not totalImpuestosRetenidos is None:
            where = "id_cfd=%s AND tipo='Retencion' AND (nombre='IVA' OR nombre='ISR')" % self.id_cfd
            data = self.db.select(('cfdimpuestos',), ('nombre', 'importe'), where)
            if data:
                retenciones = ET.SubElement(impuestos, 'cfdi:Retenciones')
                for row in data:
                    atributos = {}
                    atributos['impuesto'] = str(row[0])
                    atributos['importe'] = self.format_s.format(row[1])
                    ET.SubElement(retenciones, 'cfdi:Retencion', atributos)

        if not totalImpuestosTrasladados is None:
            #~ where = "id_cfd=%s AND tipo='Traslado' AND (nombre='IVA' OR nombre='ISR')" % self.id_cfd
            where = "id_cfd=%s AND tipo='Traslado' AND (nombre='IVA' OR nombre='IEPS')" % self.id_cfd
            data = self.db.select(('cfdimpuestos',), ('nombre', 'tasa', 'importe'), where)
            if data:
                traslados = ET.SubElement(impuestos, 'cfdi:Traslados')
                for row in data:
                    atributos = {}
                    atributos['impuesto'] = str(row[0])
                    atributos['tasa'] = str(row[1])
                    atributos['importe'] = self.format_s.format(row[2])
                    ET.SubElement(traslados, 'cfdi:Traslado', atributos)
        return

    def _complements(self):
        if self.sat_donataria:
            self.complemento = ET.SubElement(self.comprobante, 'cfdi:Complemento')
            ET.SubElement(self.complemento, 'donat:Donatarias', self.sat_donataria)
        if self.sat_ine:
            if self.complemento is None:
                self.complemento = ET.SubElement(self.comprobante, 'cfdi:Complemento')
            ET.SubElement(self.complemento, 'ine:INE', self.sat_ine)
        return

    def __otrosimpuestos(self):
        if self.otros_impuestos:
            total_retenciones = 0.00
            total_traslados = 0.00
            where = "id_cfd=%s AND tipo='%s' AND nombre!='IVA' AND nombre!='ISR'" % (self.id_cfd, 'Retencion')
            total = self.db.select(('cfdimpuestos',), ('SUM(importe)',), where)[0][0]
            if total:
                total_retenciones = total
            #~ where = "id_cfd=%s AND tipo='%s' AND nombre!='IVA' AND nombre!='ISR'" % (self.id_cfd, 'Traslado')
            where = "id_cfd=%s AND tipo='%s' AND nombre!='IVA' AND nombre!='IEPS'" % (self.id_cfd, 'Traslado')
            total = self.db.select(('cfdimpuestos',), ('SUM(importe)',), where)[0][0]
            if total:
                total_traslados = total

            if self.complemento is None:
                self.complemento = ET.SubElement(self.comprobante, 'cfdi:Complemento')

            atributos = {}
            atributos['version'] = '1.0'
            atributos['TotaldeRetenciones'] = self.format_s.format(total_retenciones)
            atributos['TotaldeTraslados'] = self.format_s.format(total_traslados)
            implocal = ET.SubElement(self.complemento, 'implocal:ImpuestosLocales', atributos)

            where = "id_cfd=%s AND tipo='%s' AND nombre!='IVA' AND nombre!='ISR'" % (self.id_cfd, 'Retencion')
            retenciones = self.db.select(('cfdimpuestos',), ('nombre', 'tasa', 'importe'), where)
            for retencion in retenciones:
                atributos = {}
                atributos['ImpLocRetenido'] = retencion[0]
                atributos['TasadeRetencion'] = retencion[1][1:]
                atributos['Importe'] = self.format_s.format(retencion[2])
                ET.SubElement(implocal, 'implocal:RetencionesLocales', atributos)
            where = "id_cfd=%s AND tipo='%s' AND nombre!='IVA' AND nombre!='ISR'" % (self.id_cfd, 'Traslado')
            traslados = self.db.select(('cfdimpuestos',), ('nombre', 'tasa', 'importe'), where)
            for traslado in traslados:
                atributos = {}
                atributos['ImpLocTrasladado'] = traslado[0]
                atributos['TasadeTraslado'] = traslado[1]
                atributos['Importe'] = self.format_s.format(traslado[2])
                ET.SubElement(implocal, 'implocal:TrasladosLocales', atributos)
        return


def parse_and_get_ns(file):
    events = "start", "start-ns"
    root = None
    ns = {}
    for event, elem in ET.iterparse(file, events):
        if event == "start-ns":
            if elem[0] in ns and ns[elem[0]] != elem[1]:
                # NOTE: It is perfectly valid to have the same prefix refer
                #     to different URI namespaces in different parts of the
                #     document. This exception serves as a reminder that this
                #     solution is not robust.    Use at your own peril.
                raise KeyError("Duplicate prefix with different URI found.")
            #~ ns[elem[0]] = "{%s}" % elem[1]
            ns[elem[0]] = elem[1]
        elif event == "start":
            if root is None:
                root = elem
    return ET.ElementTree(root).getroot(), ns


class ADDENDA(object):

    def __init__(self):
        self.msg = ''
        self.xml = ''

    def parse(self, path):
        try:
            doc, ns = parse_and_get_ns(path)
            for key, value in ns.items():
                if value is None:
                    value = ''
                ET.register_namespace(key, value)
            if 'Addenda' in doc.tag:
                self.xml = ET.tostring(doc, encoding="unicode").replace("'",'"')
                return True
            else:
                self.msg = 'No se encontró el nodo Addenda'
                return False
        except:
            print (traceback.format_exc())
            self.msg = traceback.format_exc()
            return False


class EDITADDENDA(object):

    def __init__(self):
        self.msg = ''
        self.doc = None
        self.raiz = ''
        self.parents = {}
        self.ns = None

    def parse(self, path):
        try:
            self.doc, self.ns = parse_and_get_ns(path)
            for key, value in self.ns.items():
                if value is None:
                    value = ''
                ET.register_namespace(key, value)
            self.raiz = self.doc.tag
            self.parents = dict((c, p) for p in self.doc.getiterator() for c in p)
        except:
            print (traceback.format_exc())
            self.msg = traceback.format_exc()

    def find_all(self, search):
        return

    def add_node(self, padre, name):
        hijo = ET.SubElement(padre, name)
        self.parents[hijo] = padre
        return

    def delete_node(self, node):
        p = self.parents[node]
        p.remove(node)
        del(self.parents[node])
        return

    def tostring(self):
        return ET.tostring(self.doc, encoding="unicode")


class ASIGNARADDENDA(object):

    def __init__(self):
        self.msg = ''
        self.doc = None
        self.ns = None

    def parse(self, path):
        try:
            self.doc, self.ns = parse_and_get_ns(path)
            for key, value in self.ns.items():
                if value is None:
                    value = ''
                ET.register_namespace(key, value)
                #~ if key in self.doc.tag:
                    #~ self.raizDisplay = '%s:%s' % (value, doc.tag[len(key)+2:])
        except:
            print(traceback.format_exc())
            self.message = sys.exc_info()[1]

    def get_namespace(self, tag):
        print (self.ns)
        print (tag)
        name = tag
        if self.pre in tag:
            value = self.parser.namespaces[self.pre[1:len(self.pre)-1]]
            name = '%s:%s' % (value, tag[len(self.pre):])
        return name

    def set_namespace(self, ns):
        value = '{%s}' % list(self.parser.namespaces.keys())[
                                    list(self.parser.namespaces.values()).index(ns)]
        return value


class AGREGARADDENDA(object):

    def __init__(self, xml_doc, xml_addenda):
        self.msg = ''
        self.doc = None
        self.addenda = None
        self._parse(xml_doc, xml_addenda)

    def _parse(self, xml_doc, xml_addenda):
        #~ ET.register_namespace("cfdi", "http://www.sat.gob.mx/cfd/3")
        #~ ET.register_namespace("tfd", "http://www.sat.gob.mx/TimbreFiscalDigital")
        self.doc, name_space = parse_and_get_ns(StringIO(xml_doc))
        self.addenda, name_space_addenda = parse_and_get_ns(StringIO(xml_addenda))
        name_space.update(name_space_addenda)
        for key, value in name_space.items():
            if value is None:
                value = ''
            ET.register_namespace(key, value)

        node = self.doc.find('%sAddenda' % PRE['3.2'])
        if node is None:
            node = self.doc.find('Addenda')
        if node is not None:
            self.msg = 'Esta factura ya tiene Addenda'
        return

    def add_data(self, d, p):
        perso = self._get_dict(p)
        data = self._get_data(d, perso)
        if not data:
            return False
        for r in data:
            self._set_data(r)
        node = self.doc.find('%sAddenda' % PRE['3.2'])
        if node is None:
            node = self.doc.find('Addenda')
        if node is not None:
            self.doc.remove(node)
        self.doc.insert(len(self.doc.getchildren()), self.addenda)
        return True

    def _set_data(self, d):
        s = '+'
        v = d[0]
        t = d[1].split(s)
        node = self.addenda.find(t[0])
        if node is not None:
            if t[1]:
                if t[1] in node.attrib:
                    node.attrib[t[1]] += v
            else:
                if node.text:
                    node.text += v
                else:
                    node.text = v
        return

    def tostring(self):
        data = '<?xml version="1.0" encoding="utf-8"?>\n{}'.format(
            ET.tostring(self.doc, encoding="unicode"))
        return data

    def _get_dict(self, p):
        d = {}
        if p:
            for r in p:
                d[r[0]] = r[1]
        return d

    def _get_data(self, d, p):
        s = '+'
        data = []
        for r in d:
            t = r[0].split(s)
            v = self._get_value(t, p)
            if not v:
                self.msg = 'Falta el valor: %s' % r[0]
                return []
            data.append((v, r[1]))
        return data

    def _get_value(self, d, p):
        v = ''
        if d[0] == '.':
            if d[1] in self.doc.attrib:
                v = self.doc.attrib[d[1]]
        elif d[0].startswith('.'):
            node = self.doc.find(d[0])
            if node is not None:
                if d[1] in node.attrib:
                    v = node.attrib[d[1]]
        else:
            if d[0] in p:
                v = p[d[0]]
        return v


class CFDIXML(object):

    def __init__(self):
        pass

    def parse(self, path):
        try:
            xml = ET.parse(path)
            ET.register_namespace("cfdi","http://www.sat.gob.mx/cfd/3")
            ET.register_namespace("tfd","http://www.sat.gob.mx/TimbreFiscalDigital")
            return xml.getroot()
        except:
            return None

    def tostring(self, tree):
        return ET.tostring(tree, 'UTF-8')


class CFDIXMLNOMINA(object):
    #~ PATH_BIN = util.join(util.get_path_extension(), 'bin')

    def __init__(self, caller, id_cfdi):
        self.PATH_BIN = util.join(
            util.path_to(util.get_path_extension(), False), 'bin')
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        #~ self.globales = caller.globales
        self.id_cfdi = id_cfdi
        self.tree = None
        self.xml = ''
        self.format_s = '{0:.%sf}' % self.db.select_field('opciones', 'decimales')
        self.prefijo = self.db.select_field('nominasat', 'prefijo')
        self.regimenfiscal = ''
        self.path_pem = caller.path_pem

    def generate_xml(self):
        self._comprobante()
        self._emisor()
        self._receptor()
        self._conceptos()
        self._impuestos()
        self._nomina()
        self._sellar()
        self.xml = ET.tostring(self.tree, encoding='unicode')
        return self.xml

    def _sellar(self):
        ext = ''
        path_openssl = OPENSSL % ext
        path_xsltproc = XSLTPROC % ext
        if util.get_os() == WIN:
            ext = '.exe'
            path_openssl = util.join(self.PATH_BIN, OPENSSL % ext)
            path_xsltproc = util.join(self.PATH_BIN, XSLTPROC % ext)
        version = self.tree.attrib['version']
        path_xslt = util.join(self.PATH_BIN, XSLT % version)
        path_xml = util.get_path_temp()
        self.util.save_file(path_xml, ET.tostring(self.tree))
        values = (
            path_openssl,
            path_xsltproc,
            path_xslt,
            path_xml,
            self.path_pem
        )
        args = '"{1}" "{2}" "{3}" | "{0}" dgst -sha1 -sign "{4}" | "{0}" enc ' \
            '-base64 -A'.format(*values)
            #~ path_openssl, path_xsltproc, path_xslt, path_xml, self.path_pem)
        sello = subprocess.check_output(args, shell=True).decode()
        self.tree.attrib['sello'] = sello
        return

    def _comprobante(self):
        atributos = {}
        sat = self.db.select(
            ('nominasat',), ('xmlcfdi1', 'xmlcfdi2', 'nomina', 'xmlcfdi3'))[0]
        atributos['xmlns:cfdi'] = sat[0]
        atributos['xmlns:xsi'] = sat[1]
        atributos['xmlns:nomina'] = sat[2]
        atributos['xsi:schemaLocation'] = sat[3]
        fields = {
            'version': 'version',
            'serie': 'serie',
            'folio': 'folio',
            'fecha': 'fecha',
            'forma_pago': 'formaDePago',
            'no_certificado': 'noCertificado',
            'subtotal': 'subTotal',
            'descuento': 'descuento',
            'motivo_descuento': 'motivoDescuento',
            'tipo_cambio': 'TipoCambio',
            'moneda': 'Moneda',
            'total': 'total',
            'tipo_comprobante': 'tipoDeComprobante',
            'metodo_pago': 'metodoDePago',
            'lugar_expedicion': 'LugarExpedicion',
        }
        k = tuple(fields.keys())
        data = self.db.select(('nominacfdi',), k, 'id=%s' % self.id_cfdi)[0]
        for i,v in enumerate(k):
            if v == 'fecha':
                new_value = str(data[i]).replace(' ','T')
            elif v == 'subtotal' or v == 'descuento' \
                or v == 'tipo_cambio' or v == 'total':
                new_value = self.format_s.format(data[i])
            elif v == 'no_certificado':
                no_certificado = data[i]
                new_value = str(data[i])
            else:
                new_value = str(data[i])
            atributos[fields[v]] = new_value
        data = self.db.select(
            ('certificado',),
            ('certificado',),
            "noCertificado='%s'" % no_certificado)[0][0]
        atributos['certificado'] = data
        self.tree = ET.Element('cfdi:Comprobante', atributos)
        return

    def _emisor(self):
        atributos = {}
        fields = ('rfc', 'nombre')
        data = self.db.select(('emisor',), fields)[0]
        for index, value in enumerate(fields):
            if data[index]:
                atributos[value] = str(data[index])
        emisor = ET.SubElement(self.tree, 'cfdi:Emisor', atributos)

        atributos = {}
        fields = ('calle', 'noExterior', 'noInterior', 'colonia', \
            'referencia', 'municipio', 'estado', 'pais', 'codigoPostal')
        data = self.db.select(('emisor',), fields)[0]
        for index, value in enumerate(fields):
            if data[index]:
                if data[index].strip():
                    atributos[value] = str(data[index])
        ET.SubElement(emisor, 'cfdi:DomicilioFiscal', atributos)

        atributos = {}
        data = self.db.select(('expedidoen',), fields)
        if data:
            data = data[0]
            for index, value in enumerate(fields):
                if data[index]:
                    if data[index].strip():
                        atributos[value] = str(data[index])
            ET.SubElement(emisor, 'cfdi:ExpedidoEn', atributos)

        atributos = {}
        atributos['Regimen'] = self.regimenfiscal
        ET.SubElement(emisor, 'cfdi:RegimenFiscal', atributos)
        return

    def _receptor(self):
        id_empleado = self.db.select(
            ('nominacfdi',), ('no_empleado',), 'id=%s' % self.id_cfdi)[0][0]
        atributos = {}
        fields = ('rfc', 'nombre')
        data = self.db.select(
            ('empleados',), fields, 'id=%s' % id_empleado)[0]
        for index, value in enumerate(fields):
            if data[index]:
                atributos[value] = str(data[index])
        receptor = ET.SubElement(self.tree, 'cfdi:Receptor', atributos)

        atributos = {}
        fields = ('pais',)
        data = self.db.select(
            ('empleados',), fields, 'id=%s' % id_empleado)[0]
        for index, value in enumerate(fields):
            if data[index]:
                if data[index].strip():
                    atributos[value] = str(data[index])
        ET.SubElement(receptor, 'cfdi:Domicilio', atributos)

        return

    def _conceptos(self):
        conceptos = ET.SubElement(self.tree, 'cfdi:Conceptos')
        fields = (
            'cantidad',
            'unidad',
            'descripcion',
            'valor_unitario',
            'importe')
        data = self.db.select(
            ('nominadetalle',), fields, 'id_cfdi=%s' % self.id_cfdi)
        for row in data:
            atributos = {}
            atributos['cantidad'] = self.format_s.format(row[0])
            atributos['unidad'] = str(row[1])
            atributos['descripcion'] = str(row[2])
            atributos['valorUnitario'] = str(row[3])
            atributos['importe'] = self.format_s.format(row[4])
            concepto = ET.SubElement(conceptos, 'cfdi:Concepto', atributos)
        return

    def _impuestos(self):
        atributos = {}
        total_retenido = self.db.select(
            ('nominacfdi',),
            ('total_retenido',),
            'id=%s' % self.id_cfdi)[0][0]
        if not total_retenido is None:
            atributos['totalImpuestosRetenidos'] = \
                self.format_s.format(total_retenido)
        total_traslado = self.db.select(
            ('nominacfdi',),
            ('total_traslado',),
            'id=%s' % self.id_cfdi)[0][0]
        if not total_traslado is None:
            atributos['totalImpuestosTrasladados'] = \
                self.format_s.format(total_traslado)
        impuestos = ET.SubElement(self.tree, 'cfdi:Impuestos', atributos)

        if not total_retenido is None:
            where = "id_cfdi=%s AND tipo='Retencion' AND (nombre='IVA' OR nombre='ISR')" % self.id_cfdi
            data = self.db.select(('nominaimpuestos',), ('nombre', 'importe'), where)
            if data:
                retenciones = ET.SubElement(impuestos, 'cfdi:Retenciones')
                for row in data:
                    atributos = {}
                    atributos['impuesto'] = str(row[0])
                    atributos['importe'] = self.format_s.format(row[1])
                    ET.SubElement(retenciones, 'cfdi:Retencion', atributos)

        if not total_traslado is None:
            where = "id_cfdi=%s AND tipo='Traslado' AND (nombre='IVA' OR nombre='IEPS')" % self.id_cfdi
            data = self.db.select(('nominaimpuestos',), ('nombre', 'tasa', 'importe'), where)
            if data:
                traslados = ET.SubElement(impuestos, 'cfdi:Traslados')
                for row in data:
                    atributos = {}
                    atributos['impuesto'] = str(row[0])
                    atributos['tasa'] = str(row[1])
                    atributos['importe'] = self.format_s.format(row[2])
                    ET.SubElement(traslados, 'cfdi:Traslado', atributos)
        return

    def _nomina(self):
        atributos = {}
        complemento = ET.SubElement(self.tree, 'cfdi:Complemento')
        fields = {
            'version_nomina': 'Version',
            'registro_patronal': 'RegistroPatronal',
            'no_empleado': 'NumEmpleado',
            'curp': 'CURP',
            'tipo_regimen': 'TipoRegimen',
            'imss': 'NumSeguridadSocial',
            'fecha_pago': 'FechaPago',
            'fecha_inicial': 'FechaInicialPago',
            'fecha_final': 'FechaFinalPago',
            'dias_pagados': 'NumDiasPagados',
            'periodicidad': 'PeriodicidadPago',
            'departamento': 'Departamento',
            'clabe': 'CLABE',
            'banco': 'Banco',
            'fecha_ingreso': 'FechaInicioRelLaboral',
            'antiguedad': 'Antiguedad',
            'puesto': 'Puesto',
            'tipo_contrato': 'TipoContrato',
            'tipo_jornada': 'TipoJornada',
            'salario_base': 'SalarioBaseCotApor',
            'salario_diario': 'SalarioDiarioIntegrado',
            'riesgo_puesto': 'RiesgoPuesto'
        }
        k = tuple(fields.keys())
        data = self.db.select(('nominacfdi',), k, 'id=%s' % self.id_cfdi)[0]
        for i, v in enumerate(k):
            new_value = ''
            if v == 'salario_base' or v == 'salario_diario':
                if data[i]:
                    new_value = self.format_s.format(data[i])
            elif v == 'dias_pagados':
                new_value = self.format_s.format(data[i])
            elif v == 'banco':
                if data[i]:
                    new_value = '{:03}'.format(data[i])
            elif v == 'riesgo_puesto':
                if data[i]:
                    new_value = str(data[i])
            else:
                new_value = str(data[i])
            if new_value:
                atributos[fields[v]] = new_value
        nomina = ET.SubElement(complemento, 'nomina:Nomina', atributos)
        self._detalle_nomina(nomina)
        return

    def _detalle_nomina(self, nomina):
        atributos = {}
        data = self.db.select(
            ('nominapd',),
            ('SUM(gravado)', 'SUM(exento)'),
            'id_cfdi=%s AND percepcion=1' % self.id_cfdi)[0]
        if data[0] is not None:
            atributos['TotalGravado'] = self.format_s.format(data[0])
        if data[1] is not None:
            atributos['TotalExento'] = self.format_s.format(data[1])
        if data[0] or data[1]:
            percepciones = ET.SubElement(nomina, 'nomina:Percepciones', atributos)
            data = self.db.select(
                ('nominapd',),
                ('clave_sat', 'clave', 'concepto', 'gravado', 'exento'),
                'id_cfdi=%s AND percepcion=1' % self.id_cfdi)
            for row in data:
                atributos = {}
                atributos['TipoPercepcion'] = '{:03}'.format(int(row[0]))
                atributos['Clave'] = '{:03}'.format(int(row[1]))
                atributos['Concepto'] = row[2]
                if row[3]:
                    atributos['ImporteGravado'] = self.format_s.format(row[3])
                else:
                    atributos['ImporteGravado'] = self.format_s.format(0.0)
                if row[4]:
                    atributos['ImporteExento'] = self.format_s.format(row[4])
                else:
                    atributos['ImporteExento'] = self.format_s.format(0.0)
                ET.SubElement(percepciones, 'nomina:Percepcion', atributos)

        atributos = {}
        data = self.db.select(
            ('nominapd',),
            ('SUM(gravado)', 'SUM(exento)'),
            'id_cfdi=%s AND percepcion=0' % self.id_cfdi)[0]
        if data[0] or data[1]:
            if data[0]:
                atributos['TotalGravado'] = self.format_s.format(data[0])
            else:
                atributos['TotalGravado'] = self.format_s.format(0.0)
            if data[1]:
                atributos['TotalExento'] = self.format_s.format(data[1])
            else:
                atributos['TotalExento'] = self.format_s.format(0.0)
            deducciones = ET.SubElement(nomina, 'nomina:Deducciones', atributos)
            data = self.db.select(
                ('nominapd',),
                ('clave_sat', 'clave', 'concepto', 'gravado', 'exento'),
                'id_cfdi=%s AND percepcion=0' % self.id_cfdi)
            for row in data:
                atributos = {}
                atributos['TipoDeduccion'] = '{:03}'.format(int(row[0]))
                atributos['Clave'] = '{:03}'.format(int(row[1]))
                atributos['Concepto'] = row[2]
                if row[3]:
                    atributos['ImporteGravado'] = self.format_s.format(row[3])
                else:
                    atributos['ImporteGravado'] = self.format_s.format(0.0)
                if row[4]:
                    atributos['ImporteExento'] = self.format_s.format(row[4])
                else:
                    atributos['ImporteExento'] = self.format_s.format(0.0)
                ET.SubElement(deducciones, 'nomina:Deduccion', atributos)

        data = self.db.select(
            ('nominaincapacidad',),
            ('dias', 'tipo_sat', 'descuento'),
            'id_cfdi=%s' % self.id_cfdi)
        if data:
            inc = ET.SubElement(nomina, 'nomina:Incapacidades')
            for row in data:
                atributos = {
                    'DiasIncapacidad': str(row[0]),
                    'TipoIncapacidad': str(row[1]),
                    'Descuento': self.format_s.format(row[2])
                }
                ET.SubElement(inc, 'nomina:Incapacidad', atributos)
        data = self.db.select(
            ('nominahorasextra',),
            ('dias', 'tipo', 'horas', 'importe'),
            'id_cfdi=%s' % self.id_cfdi)
        if data:
            he = ET.SubElement(nomina, 'nomina:HorasExtras')
            for row in data:
                atributos = {
                    'Dias': str(row[0]),
                    'TipoHoras': row[1],
                    'HorasExtra': str(row[2]),
                    'ImportePagado': self.format_s.format(row[3])
                }
                ET.SubElement(he, 'nomina:HorasExtra', atributos)
        return


class ImportXML(object):

    def __init__(self, db, emisor, save_client=False, save_products=False):
        self.db = db
        self.emisor = emisor
        self.save_client = save_client
        self.save_products = save_products

    def _parse(self, path_xml):
        try:
            xml = ET.parse(path_xml).getroot()
        except:
            xml = None
        return xml

    def save(self, path_xml):
        data = {}
        xml = self._parse(path_xml)
        if xml is None:
            log.debug('No se pudo parsear el documento: {}'.format(path_xml))
            return False
        ver = xml.attrib['version']
        node = xml.find('{}Emisor'.format(PRE[ver]))
        if node is None:
            log.debug('El documento no tiene el nodo requerido ' \
                'Emisor: {}'.format(path_xml))
            return False
        if node.attrib['rfc'] != self.emisor:
            log.debug('El emisor no corresponde en la factura: {}'.format(
                path_xml))
            return False
        timbre = xml.find('{}Complemento/{}TimbreFiscalDigital'.format(
            PRE[ver], PRE['TIMBRE']))
        if timbre is None:
            log.debug('La factura no esta timbrada: {}'.format(path_xml))
            return False
        data['uuid'] = timbre.attrib['UUID']
        if self._exists(data['uuid']):
            return False
        data['fecha_timbrado'] = timbre.attrib['FechaTimbrado'].replace('T',' ')
        data['id_cliente'] = self._save_client(xml, ver)
        data['estatus'] = 'Importada'
        data['xml'] = util.load_file(path_xml)
        for f in FIELDS_CFDI['CFDI']:
            if f in xml.attrib:
                if f == 'fecha':
                    data[f] = xml.attrib[f].replace('T', ' ')
                else:
                    data[f] = xml.attrib[f]
            else:
                if f == 'TipoCambio':
                    data[f] = 1
                elif f == 'Moneda':
                    data[f] = 'peso'
                else:
                    data[f] = ''

        node = xml.find('{}Impuestos'.format(PRE[ver]))
        if node is not None:
            if 'totalImpuestosRetenidos' in node.attrib:
                data['totalImpuestosRetenidos'] = \
                    node.attrib['totalImpuestosRetenidos']
            if 'totalImpuestosTrasladados' in node.attrib:
                data['totalImpuestosTrasladados'] = \
                    node.attrib['totalImpuestosTrasladados']
        data['regimen'] = ''
        node = xml.find('{}Emisor/{}RegimenFiscal'.format(PRE[ver], PRE[ver]))
        if node is not None:
            if 'Regimen' in node.attrib:
                data['regimen'] = node.attrib['Regimen']

        concepts = xml.find('{}Conceptos'.format(PRE[ver]))
        if concepts is None:
            log.info(
                'La factura no tiene el nodo Conceptos: {}'.format(path_xml))
            return False
        products = self._get_products(ver, concepts)
        if not products:
            log.info('La factura no tiene Conceptos: {}'.format(path_xml))
            return False

        id_cfd = self.db.insertrow('cfdfacturas', data)

        node = xml.find('{}Impuestos'.format(PRE[ver]))
        if node is not None:
            tax = node.find('{}Traslados'.format(PRE[ver]))
            if tax is not None:
                for t in list(tax):
                    data = {}
                    data['id_cfd'] = id_cfd
                    data['nombre'] = t.attrib['impuesto']
                    data['tasa'] = t.attrib['tasa']
                    data['tipo'] = 'Traslado'
                    data['importe'] = float(t.attrib['importe'])
                    self.db.insertrow('cfdimpuestos', data, False)
            tax = node.find('{}Retenciones'.format(PRE[ver]))
            if tax is not None:
                for t in list(tax):
                    data = {}
                    data['id_cfd'] = id_cfd
                    data['nombre'] = t.attrib['impuesto']
                    data['tipo'] = 'Retencion'
                    data['importe'] = float(t.attrib['importe'])
                    self.db.insertrow('cfdimpuestos', data, False)

        for p in products:
            p[0] = id_cfd
        self.db.executemany('cfddetalle', FIELDS_CFDI['DETAILS'], products)
        log.info('Factura importada correctamente: {}'.format(path_xml))
        return True

    def _exists(self, uuid):
        q = self.db.select(('cfdfacturas',), ('id',), "uuid='{}'".format(uuid))
        if q:
            log.debug('La factura ya esta en la base de datos: {}'.format(uuid))
            return True
        else:
            return False

    def _save_client(self, xml, ver):
        id_customer = 0
        node = xml.find('{}Receptor'.format(PRE[ver]))
        if node is None:
            return id_customer
        where = "rfc='{}'".format(node.attrib['rfc'])
        q = self.db.select(('receptores',), ('id',), where)
        if q:
            return q[0][0]
        if self.save_client:
            data = {}
            data['nombre'] = ''
            if 'nombre' in node.attrib:
                data['nombre'] = node.attrib['nombre']
            data['rfc'] = node.attrib['rfc']
            if data['rfc'] == RFC_EXTRANJERO:
                data['extranjero'] = 1
            node = node.find('{}Domicilio'.format(PRE[ver]))
            if node is None:
                log = 'El documento no tiene el nodo necesario Domicilio: ' \
                    '{}'.format(path_xml)
                log.debug(log)
                return id_customer
            for f in FIELDS_CFDI['CUSTOMER']:
                if f in node.attrib:
                    data[f] = node.attrib[f]
                else:
                    data[f] = ''
            data['fechaalta'] = util.now(True)
            data['notas'] = ''
            id_customer = self.db.insertrow('receptores', data)
        return id_customer

    def _get_products(self, ver, concepts):
        data = []
        for l in list(concepts):
            unit = ''
            code = ''
            number = ''
            date = ''
            aduana = ''
            cuenta_predial = ''
            if 'unidad' in l.attrib:
                unit = l.attrib['unidad']
            if 'noIdentificacion' in l.attrib:
                code = l.attrib['noIdentificacion']
            tmp = l.find('{}sInformacionAduanera'.format(PRE[ver]))
            if tmp is not None:
                number = tmp.attrib['numero']
                date = tmp.attrib['fecha']
                aduana = tmp.attrib['aduana']
            tmp = l.find('{}CuentaPredial'.format(PRE[ver]))
            if tmp is not None:
                cuenta_predial = tmp.attrib['numero']
            line = [0, 0, '',
                    l.attrib['cantidad'],
                    unit,
                    code,
                    l.attrib['descripcion'],
                    l.attrib['valorUnitario'],
                    l.attrib['importe'],
                    number,
                    date,
                    aduana,
                    cuenta_predial]
            if self.save_products:
                if code:
                    where = "noIdentificacion='{}'".format(code)
                else:
                    where = "descripcion='{}'".format(l.attrib['descripcion'])
                q = self.db.select(('productos',), where=where)
                if not q:
                    row = {}
                    row['id_categoria'] = 0
                    row['noIdentificacion'] = code
                    row['descripcion'] = l.attrib['descripcion']
                    row['unidad'] = unit
                    row['valorUnitario'] = l.attrib['valorUnitario']
                    row['CuentaPredial'] = cuenta_predial
                    self.db.insertrow('productos', row)
            data.append(line)
        return data


class XMLComplement(object):

    def __init__(self):
        self.msg = ''
        self.doc = None
        self.raiz = ''
        self.parents = {}
        self.ns = None

    def parse(self, path):
        try:
            self.doc, self.ns = parse_and_get_ns(path)
            for key, value in self.ns.items():
                if value is None:
                    value = ''
                ET.register_namespace(key, value)
            self.raiz = self.doc.tag
            self.parents = dict((c, p) for p in self.doc.getiterator() for c in p)
        except Exception as e:
            log.error(e, exc_info=True)
            self.msg = str(e)
        return

    def add_node(self, padre, name):
        hijo = ET.SubElement(padre, name)
        self.parents[hijo] = padre
        return

    def delete_node(self, node):
        p = self.parents[node]
        p.remove(node)
        del(self.parents[node])
        return
