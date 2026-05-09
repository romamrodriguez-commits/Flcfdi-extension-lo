# -*- coding: utf-8 -*-
import re
import traceback
import time
import logging
from xml.etree import ElementTree as ET
from .numlet import NumerosLetras
from .pyPdfCbb import CBBPDF
from .pyPdfCfd import CFD2PDF
from facturalibre.modulos import util
from facturalibre.settings import (
    LOG, TYPE_MSG, CURRENCY, CURRENCIES, PAYMENT_METHODS)


log = logging.getLogger(LOG['NAME'])


EXTENSION_PDF = '.pdf'
PRE = '{http://www.sat.gob.mx/cfd/3}'
TIMBRE = '{http://www.sat.gob.mx/TimbreFiscalDigital}'
NOMINA = '{http://www.sat.gob.mx/nomina}'
IMP_LOCAL = '{http://www.sat.gob.mx/implocal}'
IEDU = '{http://www.sat.gob.mx/iedu}'
PATH_TEMPLATE = '/bin/plantilla_factura.ods'
PATH_TEMPLATE2 = '/bin/plantilla_cotizacion.ods'
PATH_TEMPLATE3 = '/bin/acuse.ods'
PATH_TEMPLATE_NOMINA = '/bin/plantilla_recibo_nomina.ods'
PATH_COMPRA = '/bin/plantilla_compra.ods'
PATH_XSLTPROC = '/bin/xsltproc.exe'
PATH_XSLT = '/bin/timbre.xslt'
CANCELADA = 'Cancelada'
CANCELADO = 'Cancelado'
CELL_TYPE = 'ScCellObj'
CADENA = '||{version}|{UUID}|{FechaTimbrado}|{selloCFD}|{noCertificadoSAT}||'
LIMIT_MARGIN = 23000
CLEAN = "\{(\w.+)\}"


class PDFNomina(object):
    TIPO_REGIMEN = {
        '2': 'Sueldos y salarios',
        '3': 'Jubilados',
        '4': 'Pensionados',
        '5': 'Asimilados a salarios, Miembros de las Sociedades '
            'Cooperativas de Producción',
        '6': 'Asimilados a salarios, Integrantes de Sociedades y '
            'Asociaciones Civiles',
        '7': 'Asimilados a salarios, Miembros de consejos directivos, '
            'de vigilancia, consultivos, honorarios a administradores, '
            'comisarios y gerentes generales',
        '8': 'Asimilados a salarios, Actividad empresarial (comisionistas)',
        '9': 'Asimilados a salarios, Honorarios asimilados a salarios',
        '10': 'Asimilados a salarios, Ingresos acciones o títulos valor',
    }
    RIESGO_PUESTO = {
        '1': 'Clase I',
        '2': 'Clase II',
        '3': 'Clase III',
        '4': 'Clase IV',
        '5': 'Clase V'
    }

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.error = ''
        self.espejos = []
        self.format_s = caller.format_s
        self.plantilla = self.db.select_field('opciones', 'plantilla')
        self.properties = self.util.setPropertiesValues(
            ('Hidden', True, 'AsTemplate', True))
        if self.plantilla:
            data = self.util.getInfoPath(self.plantilla)
            self.plantilla = self.util.join(data[0], '%s_nomina.ods' % data[2])
            self.doc = self.unogui.openDoc(self.plantilla, self.properties)
            if not self.doc:
                msg = 'No fue posible abrir la plantilla:\n\n%s\n\nAsegurate ' \
                    'de que exista.' % self.plantilla
                self.error = msg
        else:
            self.plantilla = self.util.urlToSystem(
                self.globales['EXT_PATH'] + PATH_TEMPLATE_NOMINA)
            self.doc = self.unogui.openDoc(self.plantilla, self.properties)
            if not self.doc:
                msg = 'No fue posible abrir la plantilla predeterminada. ' \
                    'consulta a soporte técnico.'
                self.error = msg
        self.path_xslt = self.util.urlToSystem(
            self.globales['EXT_PATH'] + PATH_XSLT)
        self.hoja = None
        self.search = None
        self.sd = None
        self.rfc_emisor = ''
        self.rfc_receptor = ''
        self.show = False

    def generate_pdf(self, id_cfdi):
        self.hoja = self.doc.getSheets().getByIndex(0)
        self.search = self.hoja.getPrintAreas()
        if self.search:
            self.search = self.search[0]
        else:
            self.search = self.hoja.getRangeAddress()
        self.search = self.hoja.getCellRangeByPosition(
            self.search.StartColumn,
            self.search.StartRow,
            self.search.EndColumn,
            self.search.EndRow
        )
        self.sd = self.hoja.createSearchDescriptor()
        self.sd.SearchCaseSensitive = False
        data = self.db.select(
            ('nominacfdi',), ('xml', 'estatus'), 'id=%s' % id_cfdi)[0]
        #~ cadena = self.util.get_cadena(self.path_xslt, data[0])
        xml = ET.fromstring(data[0])
        self._comprobante(xml)
        self._emisor(xml)
        self._receptor(xml)
        self._concepto(xml)
        self._timbre(xml)
        self._nomina(xml)
        self._cancelado(data[1])
        self._clean()
        self._save_pdf(id_cfdi)
        return

    def _clean(self):
        self.sd.SearchRegularExpression = True
        self.sd.setSearchString(CLEAN)
        self.search.replaceAll(self.sd)
        return

    def _save_pdf(self, id_cfdi):
        data = self.db.select(
            ('nominacfdi',),
            ('xml',
                "strftime('%Y', fecha_timbrado)",
                "strftime('%m', fecha_timbrado)"),
            'id=%s' % id_cfdi)[0]
        #~ if self.editar:
            #~ template.Title = data[0].split('.')[0]
            #~ return
        properties = self.util.setPropertiesValues(
            ('FilterName', 'calc_pdf_Export'))
        format_s = self.db.get_option('file_name')
        name = self.util.get_name(data[0], format_s, self.globales['FILE_NAME'])
        path_pdf = self.util.getPathTemp('%s.pdf' % name)
        self.doc.storeToURL(self.util.systemToUrl(path_pdf), properties)
        if self.espejos:
            self.util.copy_pdf((data[1], data[2]), self.espejos, path_pdf)
        if self.show:
            self.util.execute(self.util.systemToUrl(path_pdf))
        self.doc.dispose()
        return

    def _nomina(self, xml):
        nomina = xml.find('%sComplemento' % PRE)
        nomina = nomina.find('%sNomina' % NOMINA)
        for k, v in nomina.attrib.items():
            if k == 'Banco':
                data = self.db.select(
                        ('bancos',), ('banco',), "clave=%s" % int(v))
                if data:
                    nv = '(%s) %s' % (v, data[0][0])
                else:
                    nv = '(%s) %s' % (v, '')
                self._set_cell('{nomina.%s}' % k, nv)
            elif k == 'TipoRegimen':
                nv = '(%s) %s' % (v, self.TIPO_REGIMEN[v])
                self._set_cell('{nomina.%s}' % k, nv)
            elif k == 'RiesgoPuesto':
                nv = '(%s) %s' % (v, self.RIESGO_PUESTO[v])
                self._set_cell('{nomina.%s}' % k, nv)
            else:
                self._set_cell('{nomina.%s}' % k, v)
        percepciones = nomina.find('%sPercepciones' % NOMINA)
        total = 0
        if percepciones is not None:
            for k, v in percepciones.attrib.items():
                total += float(v)
                v = '$ %s' % self.format_s.format(float(v))
                self._set_cell('{percepciones.%s}' % k, v)
        v = '$ %s' % self.format_s.format(total)
        self._set_cell('{total.percepciones}', v)
        if percepciones is not None:
            first = True
            for percepcion in percepciones.getchildren():
                ig = '$ %s' % self.format_s.format(
                    float(percepcion.attrib['ImporteGravado']))
                ie = '$ %s' % self.format_s.format(
                    float(percepcion.attrib['ImporteExento']))
                tp = percepcion.attrib['TipoPercepcion']
                concepto = percepcion.attrib['Concepto']
                if first:
                    first = False
                    cell_1 = self._set_cell('{percepcion.TipoPercepcion}', tp)
                    cell_2 = self._set_cell('{percepcion.Concepto}', concepto)
                    cell_3 = self._set_cell('{percepcion.ImporteGravado}', ig)
                    cell_4 = self._set_cell('{percepcion.ImporteExento}', ie)
                else:
                    cell_1 = self._set_cell(v=tp, cell=cell_1)
                    cell_2 = self._set_cell(v=concepto, cell=cell_2)
                    cell_3 = self._set_cell(v=ig, cell=cell_3)
                    cell_4 = self._set_cell(v=ie, cell=cell_4)
        deducciones = nomina.find('%sDeducciones' % NOMINA)
        if deducciones is None:
            return
        total = 0
        for k, v in deducciones.attrib.items():
            total += float(v)
            v = '$ %s' % self.format_s.format(float(v))
            self._set_cell('{deducciones.%s}' % k, v)
        v = '$ %s' % self.format_s.format(total)
        self._set_cell('{total.deducciones}', v)
        first = True
        for deduccion in deducciones.getchildren():
            ig = '$ %s' % self.format_s.format(
                float(deduccion.attrib['ImporteGravado']))
            ie = '$ %s' % self.format_s.format(
                float(deduccion.attrib['ImporteExento']))
            td = deduccion.attrib['TipoDeduccion']
            concepto = deduccion.attrib['Concepto']
            if first:
                first = False
                cell_1 = self._set_cell('{deduccion.TipoDeduccion}', td)
                cell_2 = self._set_cell('{deduccion.Concepto}', concepto)
                cell_3 = self._set_cell('{deduccion.ImporteGravado}', ig)
                cell_4 = self._set_cell('{deduccion.ImporteExento}', ie)
            else:
                cell_1 = self._set_cell(v=td, cell=cell_1)
                cell_2 = self._set_cell(v=concepto, cell=cell_2)
                cell_3 = self._set_cell(v=ig, cell=cell_3)
                cell_4 = self._set_cell(v=ie, cell=cell_4)
        return

    def _timbre(self, xml):
        timbre = xml.find('%sComplemento' % PRE)
        timbre = timbre.find('%sTimbreFiscalDigital' % TIMBRE)
        for k, v in timbre.attrib.items():
            self._set_cell('{timbre.%s}' % k, v)
        total_s = '%017.06f' % float(xml.attrib['total'])
        qr_data = '?re=%s&rr=%s&tt=%s&id=%s' % (
            self.rfc_emisor, self.rfc_receptor, total_s, timbre.attrib['UUID'])
        ruta_cbb = self.util.getCBB(qr_data)
        pd = self.hoja.getDrawPage()
        image = self.doc.createInstance(
                'com.sun.star.drawing.GraphicObjectShape')
        image.GraphicURL = self.util.systemToUrl(ruta_cbb)
        pd.add(image)
        self.util.size(image, 4500, 4500)
        self.sd.setSearchString('{timbre.cbb}')
        ranges = self.search.findAll(self.sd)
        if ranges:
            ranges = ranges.getRangeAddressesAsString().split(';')
            for r in ranges:
                for c in r.split(','):
                    cell = self.hoja.getCellRangeByName(c)
                    image.Anchor = cell
        cadena = CADENA.format(**timbre.attrib)
        self._set_cell('{timbre.cadenaoriginal}', cadena)
        return

    def _concepto(self, xml):
        conceptos = xml.find('%sConceptos' % PRE)
        for concepto in conceptos.getchildren():
            for k, v in concepto.attrib.items():
                self._set_cell('{concepto.%s}' % k, v)
        return

    def _receptor(self, xml):
        receptor = xml.find('%sReceptor' % PRE)
        self.rfc_receptor = receptor.attrib['rfc']
        for k, v in receptor.attrib.items():
            self._set_cell('{receptor.%s}' % k, v)
        domicilio = receptor.find('%sDomicilio' % PRE)
        for k, v in domicilio.attrib.items():
            self._set_cell('{receptor.%s}' % k, v)
        return

    def _emisor(self, xml):
        emisor = xml.find('%sEmisor' % PRE)
        self.rfc_emisor = emisor.attrib['rfc']
        for k, v in emisor.attrib.items():
            self._set_cell('{emisor.%s}' % k, v)
        domicilio = emisor.find('%sDomicilioFiscal' % PRE)
        for k, v in domicilio.attrib.items():
            self._set_cell('{emisor.%s}' % k, v)
        return

    def _comprobante(self, xml):
        for k, v in xml.attrib.items():
            if k == 'metodoDePago':
                continue
            if k == 'total' or k == 'descuento' or k == 'subTotal':
                v = '$ %s' % self.format_s.format(float(v))
            self._set_cell('{cfdi.%s}' % k, v)

        payment_methods = []
        if 'metodoDePago' in xml.attrib:
            values = xml.attrib['metodoDePago'].split(',')
            for k, v in PAYMENT_METHODS.items():
                if v in values:
                    tmp = '({}) {}'.format(v, k)
                    payment_methods.append(tmp)
        payment_methods = ', '.join(payment_methods)
        if not payment_methods:
            payment_methods = xml.attrib.get('metodoDePago', '')
        self._set_cell('{cfdi.%s}' % 'metodoDePago', payment_methods)

        data = self.db.select(
            ('monedas',), where="moneda='%s'" % xml.attrib['Moneda'])
        if data:
            data = data[0]
            currency = data[1].lower()
            if currency in CURRENCIES:
                currency = CURRENCIES[currency]
            enletras = NumerosLetras().NumerosLetras(
                float(xml.attrib['total']), currency, data[2], data[3])
        else:
            enletras = NumerosLetras().NumerosLetras(float(xml.attrib['total']))
        self._set_cell('{total.enletras}', enletras.upper())
        return

    def _set_cell(self, k='', v='', cell=None):
        #~ print (k, v)
        if k:
            self.sd.setSearchString(k)
            ranges = self.search.findAll(self.sd)
            if ranges:
                ranges = ranges.getRangeAddressesAsString().split(';')
                for r in ranges:
                    for c in r.split(','):
                        cell = self.hoja.getCellRangeByName(c)
                        if cell.getImplementationName() == CELL_TYPE:
                            pattern = re.compile(k, re.IGNORECASE)
                            value = pattern.sub(v, cell.getString())
                            cell.setString(value)
                return cell
        if cell:
            if cell.getImplementationName() == CELL_TYPE:
                ca = cell.getCellAddress()
                new_cell = self.hoja.getCellByPosition(ca.Column, ca.Row + 1)
                new_cell.setString(v)
                return new_cell

    def _cancelado(self, estatus):
        if estatus != CANCELADO:
            pd = self.hoja.getDrawPage()
            if pd.getCount():
                pd.remove(pd.getByIndex(0))
        return


class PDFAcuse(object):

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.doc = None
        self.hoja = None
        self.plantilla = self.util.urlToSystem(
            self.globales['EXT_PATH'] + PATH_TEMPLATE3)
        self.properties = self.util.setPropertiesValues(
            ('Hidden', True, 'AsTemplate', True))

    def generate_pdf(self, xml, id_cfdi):
        self.doc = self.unogui.openDoc(self.plantilla, self.properties)
        if not self.doc:
            msg = 'No fue posible abrir la plantilla:\n%s\n\nAsegurate de ' \
                'que exista.' % self.plantilla
            self.unogui.createMsgBox({'Message': msg})
            return
        self.hoja = self.doc.getSheets().getByIndex(0)
        tree = ET.fromstring(xml)
        fecha = tree.attrib['Fecha'].split('.')[0].replace('T', ' ')
        rfc = tree.attrib['RfcEmisor']
        for elem in tree.iter():
            if '}UUID' in elem.tag:
                uuid = elem
            if 'SignatureValue' in elem.tag:
                sello = elem
        self._write_cell('E15', fecha)
        self._write_cell('E18', fecha)
        self._write_cell('E21', rfc)
        self._write_cell('A25', uuid.text)
        self._write_cell('A28', sello.text)
        self._save_pdf(id_cfdi)
        return

    def _write_cell(self, name, data):
        try:
            celda = self.hoja.getCellRangeByName(name)
        except:
            print('Error al asignar la celda: %s' % name)
            return
        celda.setString(data)
        return

    def _save_pdf(self, id_cfdi):
        name_pdf = "'Acuse_Cancelacion_' || serie || substr('000000' || folio"
        name_pdf += ", -6, 6) || '.pdf'"
        where = 'id=%s' % id_cfdi
        data = self.db.select(('cfdfacturas',), (name_pdf,), where)[0]
        properties = self.util.setPropertiesValues(
            ('FilterName', 'calc_pdf_Export'))
        path_pdf = self.util.systemToUrl(self.util.getPathTemp(data[0]))
        self.doc.storeToURL(path_pdf, properties)
        self.util.execute(path_pdf)
        self.doc.dispose()
        return


class CFDPDF(object):
    #~ PATH_EXT = util.get_path_extension()

    def __init__(self, caller, cotizacion=False):

        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        self.unogui = caller.unogui
        self.globales = caller.globales
        #if self.globales['OS'] != 'darwin':
            #locale.setlocale(locale.LC_TIME, '')
        self.format_s = '{0:.%sf}' % self.db.select_field(
            'opciones', 'decimales')
        self.plantilla = self.db.select_field('opciones', 'plantilla')
        if not self.plantilla:
            self.plantilla = self.util.urlToSystem(
                self.globales['EXT_PATH'] + PATH_TEMPLATE)
        #~ self.plantilla2 = self.db.select_field('opciones', 'plantilla2')
        #~ if not self.plantilla2:
            #~ self.plantilla2 = self.util.urlToSystem(
                #~ self.globales['EXT_PATH'] + PATH_TEMPLATE2)
        self.hoja = None
        #~ self.celdas = {}
        self.properties = self.util.setPropertiesValues(
            ('Hidden', True, 'AsTemplate', True))
        if self.globales['OS'] == self.globales['WIN']:
            self.path_xsltproc = self.util.urlToSystem(
                self.globales['EXT_PATH'] + PATH_XSLTPROC)
        else:
            self.path_xsltproc = 'xsltproc'
        self.path_xslt = self.util.urlToSystem(
            self.globales['EXT_PATH'] + PATH_XSLT)
        self.destino = ''
        self.path_pdf = ''
        self.show = True
        self.editar = False
        self.rfc_emisor = ''
        self.rfc_receptor = ''
        self.moneda = ''
        self.cotizacion = cotizacion
        self.espejos = []
        self.data = ()
        self.printer = False
        self.sd = None
        self.search = None
        self.is_compra = False

    def generate_pdf(self, facturas, destino='', barra=None):
        self.destino = destino
        doc = util.doc_open(self.plantilla, self.properties)
        if not doc:
            msg = 'No fue posible abrir la plantilla:\n{}\n\nAsegurate de ' \
                'que exista.'.format(self.plantilla)
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return
        doc.dispose()
        for i, row in enumerate(facturas):
            if barra:
                barra.setValue(i + 1)
            self._write_data(row, self.show)
        return True

    def _write_data(self, id_cfd, show=True):
        source = ('cfdfacturas',)
        fields = ('xml', 'noAprobacion', 'noCertificado', 'uuid', 'id_folio')
        if self.is_compra:
            source = ('compras',)
            fields = ('xml', 'noCertificado', 'uuid', 'uuid')
        xml_s = self.db.select(source, fields, 'id={}'.format(id_cfd))[0]
        id_folio = False
        if not self.is_compra:
            id_folio = xml_s[4]
            if xml_s[1] and not xml_s[2]:
                cbb = CBBPDF(self)
                cbb.generate_pdf(id_cfd)
                return
        if not xml_s[0]:
            message = 'No se encontró el XML de este documento, verificalo ' \
                'con el icono XML o consulta a soporte técnico'
            self.unogui.createMsgBox({'Message': message})
            return
        if not self.is_compra:
            if xml_s[1] and xml_s[2]:
                # Esquema CFD
                cfd = CFD2PDF(self)
                cfd.generate_pdf(id_cfd)
                return
        if not self.is_compra:
            if not xml_s[3]:
                message = 'Parece que esta factura no esta timbrada, verificalo ' \
                    'con el icono XML y consulta a soporte técnico.'
                self.unogui.createMsgBox({'Message': message})
                return
        properties = self.util.setPropertiesValues(
            ('Hidden', not self.editar, 'AsTemplate', True))
        if id_folio:
            plantilla = self.db.select(
                ('folios',), ('plantilla',), 'id={}'.format(id_folio))
            if plantilla:
                plantilla = plantilla[0][0]
                if plantilla and util.exists(plantilla):
                    template = util.doc_open(plantilla, self.properties)
                else:
                    template = util.doc_open(self.plantilla, properties)
            else:
                template = util.doc_open(self.plantilla, properties)
        else:
            template = util.doc_open(self.plantilla, properties)
        if not template:
            return
        self.hoja = template.getSheets().getByIndex(0)
        self.search = self.hoja.getPrintAreas()
        if self.search:
            self.search = self.search[0]
        else:
            self.search = self.hoja.getRangeAddress()
        self.search = self.hoja.getCellRangeByPosition(
            self.search.StartColumn,
            self.search.StartRow,
            self.search.EndColumn,
            self.search.EndRow
        )
        self.sd = self.hoja.createSearchDescriptor()
        self.sd.SearchCaseSensitive = False
        self.sd.SearchRegularExpression = False
        xml_s = xml_s[0]
        ruta_xml = self.util.getPathTemp()
        self.util.save_file(ruta_xml, xml_s)
        xml = ET.fromstring(xml_s)
        self.moneda = xml.attrib['Moneda']
        self._comprobante(xml)
        self._emisor(xml)
        self._receptor(xml)
        self._donataria(xml)
        self._complement_ine(xml)
        self._totales(xml)
        self._conceptos(xml)
        self._not_in_xml(id_cfd)
        self._timbre(xml, template)
        self._clean()
        self._cancelada(id_cfd, template)
        self._compra()
        if self.printer:
            properties = self.util.setPropertiesValues(('CopyCount', 1))
            template.print(properties)
            print ('Impresion correcta')
        else:
            self._save_pdf(template, xml_s, show)
        return

    def _save_pdf(self, template, xml, show=True):
        format_s = self.db.get_option('file_name')
        name = self.util.get_name(xml, format_s, self.globales['FILE_NAME'])
        if self.editar:
            template.Title = name
            return
        properties = self.util.setPropertiesValues(
            ('FilterName', 'calc_pdf_Export'))
        path_pdf = self.util.systemToUrl(self.util.getPathTemp('%s.pdf' % name))
        self.path_pdf = self.util.urlToSystem(path_pdf)
        template.storeToURL(path_pdf, properties)
        if self.espejos:
            self.util.copy_pdf(self.data, self.espejos, self.path_pdf)
        if show:
            self.util.execute(path_pdf)
        template.dispose()
        return

    def _conceptos(self, xml):
        currency = xml.attrib['Moneda']
        conceptos = xml.find('%sConceptos' % PRE)
        if conceptos is None:
            return
        first = True
        for c in conceptos.getchildren():
            key = c.attrib['noIdentificacion']
            description = self._get_description(c)
            unidad = c.attrib['unidad']
            cantidad = c.attrib['cantidad']
            precio = c.attrib['valorUnitario']
            importe = c.attrib['importe']
            if first:
                first = False
                cell_1 = self._set_cell('{noIdentificacion}', key)
                cell_2 = self._set_cell('{descripcion}', description)
                cell_3 = self._set_cell('{unidad}', unidad)
                cell_4 = self._set_cell('{cantidad}', cantidad, value=True)
                cell_5 = self._set_cell('{valorUnitario}', precio, value=True)
                cell_5.CellStyle = currency + '1'
                cell_6 = self._set_cell('{importe}', importe, value=True)
                cell_6.CellStyle = currency + '2'
            else:
                row = cell_2.getCellAddress().Row + 1
                self.hoja.getRows().insertByIndex(row, 1)
                if cell_1:
                    self._copy_cell(cell_1)
                    cell_1 = self._set_cell(v=key, cell=cell_1)
                if cell_3:
                    self._copy_cell(cell_3)
                    cell_3 = self._set_cell(v=unidad, cell=cell_3)
                self._copy_cell(cell_2)
                self._copy_cell(cell_4)
                self._copy_cell(cell_5)
                self._copy_cell(cell_6)
                cell_2 = self._set_cell(v=description, cell=cell_2)
                cell_4 = self._set_cell(v=cantidad, cell=cell_4, value=True)
                cell_5 = self._set_cell(v=precio, cell=cell_5, value=True)
                cell_6 = self._set_cell(v=importe, cell=cell_6, value=True)
                cell_5.CellStyle = currency + '1'
                cell_6.CellStyle = currency + '2'
        return

    def _get_description(self, c):
        data = c.attrib['descripcion']
        n = c.find('%sInformacionAduanera' % PRE)
        if n is not None:
            data += '\nPedimento de Importación No. %s\n' % n.attrib['numero']
            data += 'Aduana: %s, Fecha del pedimento: %s' % (
                n.attrib['aduana'], n.attrib['fecha'])
        n = c.find('%sCuentaPredial' % PRE)
        if n is not None:
            data += '\n\nCuenta Predial Número: %s' % n.attrib['numero']
        n = c.find('%sComplementoConcepto' % PRE)
        if n is not None:
            iedu = n.find('%sinstEducativas' % IEDU)
            if iedu is not None:
                data += u'\n\nAlumno: %s\nCURP: %s' % (
                    iedu.attrib['nombreAlumno'], iedu.attrib['CURP'])
                data += u'\nAcuerdo de incorporación ante la SEP %s %s' % (
                    iedu.attrib['nivelEducativo'], iedu.attrib['autRVOE'])
        return data

    def _add_totales(self, xml):
        #~ Campos: {total}, {descuento},
        #~ {totalimpuestostrasladados}, {totalimpuestosretenidos},
        #~ {traslado_IMPUESTO_TASA} por ejemplo {traslado_iva_16}
        #~ {OTROS_IMPUESTOS_TASA} por ejemplo  {inspeccion_de_obra_0.5}
        ok = False
        if 'total' in xml.attrib:
            value = xml.attrib['total']
            cell_value = self._set_cell('{total}', value, value=True)
            ok = bool(cell_value)
        if 'descuento' in xml.attrib:
            value = xml.attrib['descuento']
            self._set_cell('{descuento}', value, value=True)
        imp = xml.find('{}Impuestos'.format(PRE))
        if imp is not None:
            for k, v in imp.attrib.items():
                self._set_cell('{{{}}}'.format(k), v, value=True)
            node = imp.find('{}Traslados'.format(PRE))
            if node is not None:
                for n in node.getchildren():
                    field = 'traslado_{}_{}'.format(
                        n.attrib['impuesto'], n.attrib['tasa'])
                    title = '{} {}%'.format(
                        n.attrib['impuesto'], n.attrib['tasa'])
                    value = n.attrib['importe']
                    self._set_cell('{{{}.titulo}}'.format(field), title)
                    self._set_cell('{{{}}}'.format(field), value, value=True)
            node = imp.find('{}Retenciones'.format(PRE))
            if node is not None:
                for n in node.getchildren():
                    field = 'retencion_{}'.format(n.attrib['impuesto'])
                    title = 'Retención {}'.format(n.attrib['impuesto'])
                    value = n.attrib['importe']
                    self._set_cell('{{{}.titulo}}'.format(field), title)
                    self._set_cell('{{{}}}'.format(field), value, value=True)
        com = xml.find('{}Complemento'.format(PRE))
        if com is not None:
            otros = com.find('{}ImpuestosLocales'.format(IMP_LOCAL))
            if otros is not None:
                for n in list(otros):
                    if n.tag == '{}RetencionesLocales'.format(IMP_LOCAL):
                        name = 'ImpLocRetenido'
                        tasa = 'TasadeRetencion'
                    else:
                        name = 'ImpLocTrasladado'
                        tasa = 'TasadeTraslado'
                    field = '{}_{}'.format(
                        n.attrib[name].replace(' ', '_'), n.attrib[tasa])
                    title = '{} {}%'.format(n.attrib[name], n.attrib[tasa])
                    value = n.attrib['Importe']
                    self._set_cell('{{{}.titulo}}'.format(field), title)
                    self._set_cell('{{{}}}'.format(field), value, value=True)
        return ok

    def _totales(self, xml):
        currency = xml.attrib['Moneda']

        cell_title = self._set_cell('{subtotal.titulo}', 'Subtotal')
        value = xml.attrib['subTotal']
        cell_value = self._set_cell('{subtotal}', value, value=True)
        cell_value.CellStyle = currency

        #~ Si encuentra el campo {total}, se asume que los totales e impuestos
        #~ están declarados de forma independiente cada uno
        if self._add_totales(xml):
            return
        #~ Si no se encuentra, copia las celdas hacia abajo de
        #~ {subtotal.titulo} y {subtotal}
        if 'descuento' in xml.attrib:
            self._copy_cell(cell_title)
            self._copy_cell(cell_value)
            cell_title = self._set_cell(v='Descuento', cell=cell_title)
            value = xml.attrib['descuento']
            cell_value = self._set_cell(v=value, cell=cell_value, value=True)
            cell_value.CellStyle = currency
        imp = xml.find('%sImpuestos' % PRE)
        if imp is not None:
            for k, v in imp.attrib.items():
                v = self.format_s.format(float(v))
                self._set_cell('{impuestos.%s}' % k, v, value=True)
            node = imp.find('%sTraslados' % PRE)
            if node is not None:
                for t in node.getchildren():
                    self._copy_cell(cell_title)
                    self._copy_cell(cell_value)
                    title = '%s %s%%' % (t.attrib['impuesto'], t.attrib['tasa'])
                    value = t.attrib['importe']
                    cell_title = self._set_cell(v=title, cell=cell_title)
                    cell_value = self._set_cell(v=value, cell=cell_value, value=True)
                    cell_value.CellStyle = currency
            node = imp.find('%sRetenciones' % PRE)
            if node is not None:
                for t in node.getchildren():
                    self._copy_cell(cell_title)
                    self._copy_cell(cell_value)
                    title = 'Retención %s' % t.attrib['impuesto']
                    value = t.attrib['importe']
                    cell_title = self._set_cell(v=title, cell=cell_title)
                    cell_value = self._set_cell(v=value, cell=cell_value, value=True)
                    cell_value.CellStyle = currency

        com = xml.find('%sComplemento' % PRE)
        if com is not None:
            otros = com.find('%sImpuestosLocales' % IMP_LOCAL)
            if otros is not None:
                for otro in list(otros):
                    if otro.tag == '%sRetencionesLocales' % IMP_LOCAL:
                        name = 'ImpLocRetenido'
                        tasa = 'TasadeRetencion'
                    else:
                        name = 'ImpLocTrasladado'
                        tasa = 'TasadeTraslado'
                    title = '%s %s %%' % (otro.attrib[name], otro.attrib[tasa])
                    value = otro.attrib['Importe']
                    self._copy_cell(cell_title)
                    self._copy_cell(cell_value)
                    cell_title = self._set_cell(v=title, cell=cell_title)
                    cell_value = self._set_cell(v=value, cell=cell_value, value=True)
                    cell_value.CellStyle = currency

        if 'total' in xml.attrib:
            self._copy_cell(cell_title)
            self._copy_cell(cell_value)
            cell_title = self._set_cell(v='Total', cell=cell_title)
            value = xml.attrib['total']
            cell_value = self._set_cell(v=value, cell=cell_value, value=True)
            cell_value.CellStyle = currency
        return

    def _donataria(self, xml):
        complemento = xml.find('%sComplemento' % PRE)
        if complemento is None:
            return
        donataria = complemento.find('{http://www.sat.gob.mx/donat}Donatarias')
        if donataria is not None:
            for k, v in donataria.attrib.items():
                self._set_cell('{donataria.%s}' % k, v)
        return

    def _complement_ine(self, xml):
        complemento = xml.find('%sComplemento' % PRE)
        if complemento is None:
            return
        ine = complemento.find('{http://www.sat.gob.mx/ine}INE')
        if ine is None:
            return

        for k, v in ine.attrib.items():
            self._set_cell('{ine.%s}' % k, v)
        return

    def _receptor(self, xml):
        receptor = xml.find('%sReceptor' % PRE)
        self.rfc_receptor = receptor.attrib['rfc']
        for k, v in receptor.attrib.items():
            self._set_cell('{receptor.%s}' % k, v)
        domicilio = receptor.find('%sDomicilio' % PRE)
        for k, v in domicilio.attrib.items():
            if k == 'codigoPostal':
                v = 'C.P. %s' % v
            self._set_cell('{receptor.%s}' % k, v)
        return

    def _emisor(self, xml):
        emisor = xml.find('%sEmisor' % PRE)
        self.rfc_emisor = emisor.attrib['rfc']
        for k, v in emisor.attrib.items():
            self._set_cell('{emisor.%s}' % k, v)
        domicilio = emisor.find('%sDomicilioFiscal' % PRE)
        for k, v in domicilio.attrib.items():
            if k == 'codigoPostal':
                v = 'C.P. %s' % v
            self._set_cell('{emisor.%s}' % k, v)
        domicilio = emisor.find('%sExpedidoEn' % PRE)
        if domicilio is not None:
            for k, v in domicilio.attrib.items():
                if k == 'codigoPostal':
                    v = 'C.P. %s' % v
                self._set_cell('{expedidoen.%s}' % k, v)
        regimen = emisor.find('%sRegimenFiscal' % PRE)
        if regimen is not None:
            for k, v in regimen.attrib.items():
                self._set_cell('{emisor.%s}' % k, v)
        return

    def _comprobante(self, xml):
        for k, v in xml.attrib.items():
            if k == 'total' or k == 'descuento' or k == 'subTotal':
                v = self.format_s.format(float(v))
            self._set_cell('{cfdi.%s}' % k, v)
        data = self.db.select(
            ('monedas',), where="moneda='%s'" % xml.attrib['Moneda'])
        if data:
            data = data[0]
            currency = data[1].lower()
            if currency in CURRENCIES:
                currency = CURRENCIES[currency]
            enletras = NumerosLetras().NumerosLetras(
                float(xml.attrib['total']), currency, data[2], data[3])
        else:
            enletras = NumerosLetras().NumerosLetras(float(xml.attrib['total']))
        self._set_cell('{cfdi.totalenletras}', enletras.upper())
        fecha = xml.attrib['fecha'].split('-')
        self.data = (fecha[0], fecha[1])
        fecha = xml.attrib['fecha'].split('T')
        self._set_cell('{cfdi.hora}', fecha[1])
        #fecha = self.util.format_date(fecha[0], '%A, %d de %B de %Y')
        fecha = self.util.format_date2(fecha[0])
        self._set_cell('{cfdi.fechaformato}', fecha)

        payment_methods = []
        if 'metodoDePago' in xml.attrib:
            values = xml.attrib['metodoDePago'].split(',')
            for k, v in PAYMENT_METHODS.items():
                if v in values:
                    tmp = '({}) {}'.format(v, k)
                    payment_methods.append(tmp)
        payment_methods = ', '.join(payment_methods)
        if not payment_methods:
            payment_methods = xml.attrib.get('metodoDePago', '')

        data = {
            'formaDePago': 'Forma de Pago: ',
            'metodoDePago': payment_methods,
            'condicionesDePago': 'Condiciones de Pago: ',
            'NumCtaPago': 'Número de Cuenta de Pago: ',
        }
        cfdi_data = ''
        for k, v in data.items():
            if k in xml.attrib:
                if k == 'metodoDePago':
                    cfdi_data += 'Método de Pago:  {}\n'.format(v)
                else:
                    cfdi_data += '%s %s\n' % (v, xml.attrib[k])
        if 'Moneda' in xml.attrib:
            moneda = xml.attrib['Moneda'].upper()
            cfdi_data += 'Moneda: %s\n' % (moneda)
            if not moneda.lower() in ('peso', 'mxn'):
                if 'TipoCambio' in xml.attrib:
                    tipo_cambio = xml.attrib['TipoCambio']
                    cfdi_data += 'Tipo de Cambio: %s\n' % (tipo_cambio)
        self._set_cell('{cfdi.datos}', cfdi_data)
        return

    def _timbre(self, xml, template):
        timbre = xml.find('%sComplemento' % PRE)
        timbre = timbre.find('%sTimbreFiscalDigital' % TIMBRE)
        for k, v in timbre.attrib.items():
            self._set_cell('{timbre.%s}' % k, v)
        total_s = '%017.06f' % float(xml.attrib['total'])
        qr_data = '?re=%s&rr=%s&tt=%s&id=%s' % (
            self.rfc_emisor, self.rfc_receptor, total_s, timbre.attrib['UUID'])
        ruta_cbb = self.util.getCBB(qr_data)
        pd = self.hoja.getDrawPage()
        self.sd.setSearchString('{timbre.cbb}')
        ranges = self.search.findAll(self.sd)
        if ranges:
            ranges = ranges.getRangeAddressesAsString().split(';')
            for r in ranges:
                for c in r.split(','):
                    cell = self.hoja.getCellRangeByName(c)
                    image = template.createInstance(
                        'com.sun.star.drawing.GraphicObjectShape')
                    image.GraphicURL = self.util.systemToUrl(ruta_cbb)
                    pd.add(image)
                    self.util.size(image, 3500, 3500)
                    image.Anchor = cell
                    pos = image.getPosition()
                    if pos.Y > LIMIT_MARGIN:
                        #~ self.util.msgbox('X: %s - Y: %s' % (pos.X, pos.Y))
                        self.hoja.getRows().getByIndex(
                            cell.getCellAddress(
                                ).Row - 2).IsStartOfNewPage = True
                    break
        cadena = CADENA.format(**timbre.attrib)
        self._set_cell('{timbre.cadenaoriginal}', cadena)
        return

    def _cancelada(self, id_cfd, template):
        cancelada = self.db.select(
            ('cfdfacturas',), ('estatus',), 'id=%s' % id_cfd)[0][0]
        if cancelada != CANCELADA:
            pd = self.hoja.getDrawPage()
            if pd.getCount():
                pd.remove(pd.getByIndex(0))
        return

    def _compra(self):
        if self.is_compra:
            pd = self.hoja.getDrawPage()
            if pd.getCount():
                pd.remove(pd.getByIndex(0))
        return

    def _set_cell(self, k='', v='', cell=None, value=False):
        if k:
            self.sd.setSearchString(k)
            ranges = self.search.findAll(self.sd)
            if ranges:
                ranges = ranges.getRangeAddressesAsString().split(';')
                for r in ranges:
                    for c in r.split(','):
                        cell = self.hoja.getCellRangeByName(c)
                        if cell.getImplementationName() == CELL_TYPE:
                            if value:
                                cell.setValue(float(v))
                            else:
                                pattern = re.compile(k, re.IGNORECASE)
                                value = pattern.sub(v, cell.getString())
                                cell.setString(value)
                return cell
        if cell:
            if cell.getImplementationName() == CELL_TYPE:
                ca = cell.getCellAddress()
                new_cell = self.hoja.getCellByPosition(ca.Column, ca.Row + 1)
                if value:
                    new_cell.setValue(float(v))
                else:
                    new_cell.setString(v)
                return new_cell

    def _next_cell(self, cell):
        col = cell.getCellAddress().Column
        row = cell.getCellAddress().Row + 1
        return self.hoja.getCellByPosition(col, row)

    def _copy_cell(self, cell):
        destino = self._next_cell(cell)
        self.hoja.copyRange(destino.getCellAddress(), cell.getRangeAddress())
        return destino

    def _clean(self):
        self.sd.SearchRegularExpression = True
        self.sd.setSearchString(CLEAN)
        self.search.replaceAll(self.sd)
        return

    def _not_in_xml(self, id_cfdi, table='cfd'):
        tmp = self.db.select(('emisor',), ('telefono', 'correo'))[0]
        emisor_telefono = tmp[0]
        emisor_correo = tmp[1]
        tmp = self.db.select(('expedidoen',), ('telefono',))
        expedidoen_telefono = ''
        if tmp:
            expedidoen_telefono = tmp[0][0]
        data = (
            ('{emisor.telefono}', emisor_telefono),
            ('{emisor.correo}', emisor_correo),
            ('{expedidoen.telefono}', expedidoen_telefono),
        )
        for row in data:
            self._set_cell(row[0], row[1])
        data = self.db.select(
            ('{}personalizados'.format(table),),
            ('campo', 'valor'),
            'id_cfd=%s' % id_cfdi)
        if data:
            for row in data:
                title = '{%s}' % row[0].replace(' ', '_')
                self._set_cell(title, row[1])
        data = self.db.select(
            ('{}facturas'.format(table),),
            ('id_cliente', 'notas'),
            'id=%s' % id_cfdi)[0]
        id_cliente = data[0]
        notas = data[1]
        self._set_cell('{cfdi.notas}', notas)
        data = self.db.select(
            ('telefonos',), ('telefono',), 'id_cliente=%s' % id_cliente)
        i = 0
        if data:
            for row in data:
                i += 1
                self._set_cell('{receptor.telefono_%s}' % i, row[0])
        data = self.db.select(
            ('correos',), ('correo',), 'id_cliente=%s' % id_cliente)
        i = 0
        if data:
            for row in data:
                i += 1
                self._set_cell('{receptor.correo_%s}' % i, row[0])
        data = self.db.select(
            ('contactos',), ('contacto',), 'id_cliente=%s' % id_cliente)
        i = 0
        if data:
            for row in data:
                i += 1
                self._set_cell('{receptor.contacto_%s}' % i, row[0])
        data = self.db.select(
            ('receptores',), ('notas',), 'id=%s' % id_cliente)[0][0]
        if data:
            self._set_cell('{receptor.notas}', data)
        return

    def generate_prepdf(self, id_cfd):
        id_folio = self.db.select(
            ('prefacturas',), ('id_folio',), 'id=%s'%id_cfd)[0][0]
        template = self.__get_template(False, id_folio)
        if not template:
            return
        self.hoja = template.getSheets().getByIndex(0)
        self.search = self.hoja.getPrintAreas()
        if self.search:
            self.search = self.search[0]
        else:
            self.search = self.hoja.getRangeAddress()
        self.search = self.hoja.getCellRangeByPosition(
            self.search.StartColumn,
            self.search.StartRow,
            self.search.EndColumn,
            self.search.EndRow
        )
        self.sd = self.hoja.createSearchDescriptor()
        self.sd.SearchCaseSensitive = False
        self.sd.SearchRegularExpression = False
        pd = self.hoja.getDrawPage()
        if pd.getCount():
            pd.remove(pd.getByIndex(0))
        self._preemisor()
        self._prereceptor(id_cfd)
        self._pretotales(id_cfd)
        self._precomprobante(id_cfd)
        self._preconceptos(id_cfd)
        self._not_in_xml(id_cfd, 'pre')
        self._clean()
        self.__save_prepdf(template, id_cfd)
        template.dispose()
        return

    def _preemisor(self):
        emisor = self.db.select(('emisor',))[0]
        self._set_cell('{emisor.rfc}', emisor[1])
        self._set_cell('{emisor.nombre}', emisor[2])
        self._set_cell('{emisor.calle}', emisor[3])
        self._set_cell('{emisor.noexterior}', emisor[4])
        self._set_cell('{emisor.nointerior}', emisor[5])
        self._set_cell('{emisor.colonia}', emisor[6])
        self._set_cell('{emisor.municipio}', emisor[9])
        self._set_cell('{emisor.estado}', emisor[10])
        self._set_cell('{emisor.pais}', emisor[11])
        self._set_cell('{emisor.codigopostal}', emisor[12])

        #~ domicilio = emisor.find('%sExpedidoEn' % PRE)
        #~ if domicilio is not None:
            #~ for k, v in domicilio.attrib.items():
                #~ if k == 'codigoPostal':
                    #~ v = 'C.P. %s' % v
                #~ self._set_cell('{expedidoen.%s}' % k, v)

        #~ self.__write_cell(self.celdas['donatariaautorizacion'], emisor[17])
        #~ self.__write_cell(self.celdas['donatariafecha'], emisor[18])
        #~ leyenda = self.db.select_field('sat', 'dleyenda')
        #~ self.__write_cell(self.celdas['donatarialeyenda'], leyenda)
        return

    def _prereceptor(self, id_cfdi):
        id_receptor = self.db.select(
            ('prefacturas',), ('id_cliente',), 'id=%s' % id_cfdi)[0][0]
        receptor = self.db.select(
            ('receptores',), where='id=%s' % id_receptor)[0]
        self._set_cell('{receptor.rfc}', receptor[1])
        self._set_cell('{receptor.nombre}', receptor[2])
        self._set_cell('{receptor.calle}', receptor[3])
        self._set_cell('{receptor.noexterior}', receptor[4])
        self._set_cell('{receptor.nointerior}', receptor[5])
        self._set_cell('{receptor.colonia}', receptor[6])
        self._set_cell('{receptor.municipio}', receptor[9])
        self._set_cell('{receptor.estado}', receptor[10])
        self._set_cell('{receptor.pais}', receptor[11])
        self._set_cell('{receptor.codigopostal}', receptor[12])
        return

    def _pretotales(self, id_cfd):
        factura = self.db.select(
            ('prefacturas',), ('id', 'subTotal', 'motivoDescuento', 'descuento',
            'totalImpuestosTrasladados', 'totalImpuestosRetenidos', 'total'),
            'id=%s' % id_cfd)[0]
        cell_title = self._set_cell('{subtotal.titulo}', 'Subtotal')
        cell_value = self._set_cell('{subtotal}', factura[1], value=True)
        self._set_cell('{cfdi.motivoDescuento}', factura[2])
        if factura[3]:
            self._copy_cell(cell_title)
            self._copy_cell(cell_value)
            cell_title = self._set_cell(v='Descuento', cell=cell_title)
            cell_value = self._set_cell(v=factura[3], cell=cell_value, value=True)
        if factura[4] is not None:
            self._set_cell(
                '{impuestos.totalimpuestostrasladados}', factura[4], value=True)
            traslados = self.db.select(
                ('preimpuestos',),
                ('nombre', 'tasa', 'importe'),
                "tipo='Traslado' AND id_cfd=%s" % id_cfd)
            for t in traslados:
                self._copy_cell(cell_title)
                self._copy_cell(cell_value)
                title = '{} {}%'.format(t[0], t[1])
                cell_title = self._set_cell(v=title, cell=cell_title)
                cell_value = self._set_cell(v=t[2], cell=cell_value, value=True)
        if factura[4] is not None:
            self._set_cell(
                '{impuestos.totalimpuestosretenidos}', factura[4], value=True)
            retenciones = self.db.select(
                ('preimpuestos',),
                ('nombre', 'tasa', 'importe'),
                "tipo='Retencion' AND id_cfd=%s" % id_cfd)
            for r in retenciones:
                self._copy_cell(cell_title)
                self._copy_cell(cell_value)
                title = '{} {}%'.format(r[0], r[1])
                cell_title = self._set_cell(v=title, cell=cell_title)
                cell_value = self._set_cell(v=r[2], cell=cell_value, value=True)
        self._copy_cell(cell_title)
        self._copy_cell(cell_value)
        cell_title = self._set_cell(v='Total', cell=cell_title)
        cell_value = self._set_cell(v=factura[6], cell=cell_value, value=True)
        return

    def _precomprobante(self, id_cfd):
        factura = self.db.select(('prefacturas',), where='id=%s' % id_cfd)[0]
        date_time = factura[6].split(' ')
        #~ date = self.util.format_date(date_time[0], '%A, %d de %B de %Y')
        date = self.util.format_date2(date_time[0])
        data = self.db.select(('monedas',), where="moneda='%s'" % factura[15])
        if data:
            data = data[0]
            currency = data[1].lower()
            if currency in CURRENCIES:
                currency = CURRENCIES[currency]
            en_letras = NumerosLetras().NumerosLetras(
                factura[16], currency, data[2], data[3])
        else:
            en_letras = NumerosLetras().NumerosLetras(factura[16])
        data = {
            7: 'Forma de Pago: {}\n'.format(factura[7]),
            10: 'Condiciones de Pago: {}\n'.format(factura[10]),
            15: 'Moneda: {}\n'.format(factura[15]),
            18: 'Método de Pago: {}\n'.format(factura[18]),
            20: 'Número de Cuenta de Pago: {}\n'.format(factura[20]),
        }
        cfdi_data = ''
        for k, v in data.items():
            if factura[k]:
                cfdi_data += data[k]
        if not factura[15].lower() in ('peso', 'mxn'):
            cfdi_data += 'Tipo de Cambio: {}\n'.format(factura[14])
        self._set_cell('{cfdi.serie}', factura[2])
        self._set_cell('{cfdi.folio}', str(factura[5]))
        self._set_cell('{cfdi.formadepago}', factura[7])
        self._set_cell('{cfdi.condicionesdepago}', factura[10])
        self._set_cell('{cfdi.fechaformato}', date)
        self._set_cell('{cfdi.hora}', date_time[1])
        self._set_cell('{cfdi.tipocambio}', factura[14])
        self._set_cell('{cfdi.moneda}', factura[15])
        self._set_cell('{cfdi.tipodecomprobante}', factura[17])
        self._set_cell('{cfdi.metododepago}', factura[18])
        self._set_cell('{cfdi.lugarexpedicion}', factura[19])
        self._set_cell('{cfdi.numctapago}', factura[20])
        self._set_cell('{emisor.regimen}', factura[33])
        self._set_cell('{cfdi.totalenletras}', en_letras.upper())
        self._set_cell('{cfdi.datos}', cfdi_data)
        return

    def _preconceptos(self, id_cfd):
        conceptos = self.db.select(('predetalle',), where='id_cfd=%s' % id_cfd)
        first = True
        for c in conceptos:
            key = c[5]
            description = self._get_predescription(c)
            unidad = c[4]
            cantidad = c[3]
            precio = c[7]
            importe = c[8]
            if first:
                first = False
                cell_1 = self._set_cell('{noIdentificacion}', key)
                cell_2 = self._set_cell('{descripcion}', description)
                cell_3 = self._set_cell('{unidad}', unidad)
                cell_4 = self._set_cell('{cantidad}', cantidad, value=True)
                cell_5 = self._set_cell('{valorUnitario}', precio, value=True)
                cell_6 = self._set_cell('{importe}', importe, value=True)
            else:
                row = cell_2.getCellAddress().Row + 1
                self.hoja.getRows().insertByIndex(row, 1)
                if cell_1:
                    self._copy_cell(cell_1)
                    cell_1 = self._set_cell(v=key, cell=cell_1)
                if cell_3:
                    self._copy_cell(cell_3)
                    cell_3 = self._set_cell(v=unidad, cell=cell_3)
                self._copy_cell(cell_2)
                self._copy_cell(cell_4)
                self._copy_cell(cell_5)
                self._copy_cell(cell_6)
                cell_2 = self._set_cell(v=description, cell=cell_2)
                cell_4 = self._set_cell(v=cantidad, cell=cell_4, value=True)
                cell_5 = self._set_cell(v=precio, cell=cell_5, value=True)
                cell_6 = self._set_cell(v=importe, cell=cell_6, value=True)
        return

    def _get_predescription(self, c):
        data = c[6]
        if c[9]:
            data += '\nPedimento de Importación No. %s\n' % c[9]
            data += 'Aduana: %s, Fecha del pedimento: %s' % (c[11], c[10])
        if c[12]:
            data += '\n\nCuenta Predial Número: %s' % c[12]
        if c[14]:
            data += u'\n\nAlumno: %s\nCURP: %s' % (c[14], c[15])
            data += u'\nAcuerdo de incorporación ante la SEP %s %s' % (
                c[16], c[17])
        return data

    def __get_template(self, cot=False, id_folio=False):
        if cot:
            data = self.util.getInfoPath(self.plantilla)
            path_template = self.util.join(data[0], '%s_cotizacion.ods' % data[2])
            message = '¿Deseas editar esta cotización?'
            if self.unogui.createQuestion('Factura Libre', message):
                self.editar = True
                self.properties = self.util.setPropertiesValues(
                                        ('Hidden', False, 'AsTemplate', True))
            doc = self.unogui.openDoc(path_template, self.properties)
        else:
            #~ Gracias a: http://fipasoft.mx/
            if id_folio:
                plantilla = self.db.select(('folios',), ('plantilla',), 'id=%s' % id_folio)
                if plantilla:
                    plantilla1 = plantilla[0][0]
                    if plantilla1:
                        doc = self.unogui.openDoc(plantilla1, self.properties)
                    else:
                        doc = self.unogui.openDoc(self.plantilla, self.properties)
                else:
                    doc = self.unogui.openDoc(self.plantilla, self.properties)
            else:
                doc = self.unogui.openDoc(self.plantilla, self.properties)

        if not doc:
            message = 'No fue posible abrir la plantilla, consulte a soporte técnico'
            self.unogui.createMsgBox({'Message': message})
            return None
        return doc

    def __save_prepdf(self, template, id_cfd, enviar=False):
        name_pdf = "serie || '-' ||substr('000000' || folio, -6, 6) || '_' || rfc || '.pdf'"
        where = 'prefacturas.id_cliente=receptores.id AND prefacturas.id=%s' % id_cfd
        data = self.db.select(('prefacturas', 'receptores'), (name_pdf,), where)[0]
        properties = self.util.setPropertiesValues(('FilterName', 'calc_pdf_Export'))
        path_pdf = self.util.systemToUrl(self.util.getPathTemp(data[0]))
        self.path_pdf = self.util.urlToSystem(path_pdf)
        template.storeToURL(path_pdf, properties)
        self.util.execute(path_pdf)
        if enviar == 2:
            self.util.enviar_correo((enviar, (self.path_pdf,), '', ''))
        return

    def generate_cotizacion(self, id_cfd, enviar=False):
        self.cotizacion = True
        template = self.__get_template(True, False)
        if not template:
            return
        self.hoja = template.getSheets().getByIndex(0)
        self.search = self.hoja.getPrintAreas()
        if self.search:
            self.search = self.search[0]
        else:
            self.search = self.hoja.getRangeAddress()
        self.search = self.hoja.getCellRangeByPosition(
            self.search.StartColumn,
            self.search.StartRow,
            self.search.EndColumn,
            self.search.EndRow
        )
        self.sd = self.hoja.createSearchDescriptor()
        self.sd.SearchCaseSensitive = False
        self.sd.SearchRegularExpression = False
        self._preemisor()
        self._prereceptor(id_cfd)
        self._pretotales(id_cfd)
        self._precomprobante(id_cfd)
        self._preconceptos(id_cfd)
        self._not_in_xml(id_cfd, 'pre')
        self._clean()
        if not self.editar:
            self.__save_prepdf(template, id_cfd, enviar)
            template.dispose()
        return


class PDFCompra(object):

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.error = ''
        self.espejos = []
        self.format_s = caller.format_s
        self.properties = self.util.setPropertiesValues(
            ('Hidden', True, 'AsTemplate', True))
        self.plantilla = self.util.urlToSystem(
            self.globales['EXT_PATH'] + PATH_COMPRA)
        self.doc = self.unogui.openDoc(self.plantilla, self.properties)
        if not self.doc:
            msg = 'No fue posible abrir la plantilla predeterminada. ' \
                'consulta a soporte técnico.'
            self.error = msg
        self.hoja = None
        self.search = None
        self.sd = None
        self.rfc_emisor = ''
        self.rfc_receptor = ''
        self.show = False

    def generate_pdf(self, id_cfdi):
        self.hoja = self.doc.getSheets().getByIndex(0)
        self.search = self.hoja.getPrintAreas()
        if self.search:
            self.search = self.search[0]
        else:
            self.search = self.hoja.getRangeAddress()
        self.search = self.hoja.getCellRangeByPosition(
            self.search.StartColumn,
            self.search.StartRow,
            self.search.EndColumn,
            self.search.EndRow
        )
        self.sd = self.hoja.createSearchDescriptor()
        self.sd.SearchCaseSensitive = False
        data = self.db.select(
            ('compras',), ('xml', 'estatus'), 'id=%s' % id_cfdi)[0]
        xml = ET.fromstring(data[0])
        self._comprobante(xml)
        self._emisor(xml)
        self._receptor(xml)
        self._concepto(xml)
        self._cancelado(data[1])
        self._clean()
        self._save_pdf(id_cfdi)
        return

    def _clean(self):
        data = (
            '{nomina.RegistroPatronal}',
            '{emisor.noInterior}',
            '{nomina.CLABE}',
            '{deduccion.TipoDeduccion}',
            '{deduccion.Concepto}',
            '{deduccion.ImporteGravado}',
            '{deduccion.ImporteExento}',
            '{deducciones.TotalGravado}',
            '{deducciones.TotalExento}',
            '{total.deducciones}',
            '{nomina.NumSeguridadSocial}',
            '{nomina.Banco}',
            '{nomina.SalarioBaseCotApor}',
            '{nomina.SalarioDiarioIntegrado}',
            '{nomina.TipoJornada}',
            '{nomina.FechaInicioRelLaboral}',
            '{nomina.TipoContrato}',
        )
        for row in data:
            self._set_cell(row, '')
        return

    def _save_pdf(self, id_cfdi):
        name_pdf = "serie || substr('000000' || folio, -6, 6) || '_' || " \
            "replace(empleado, ' ', '_') || '.pdf'"
        data = self.db.select(
            ('nominacfdi',),
            (name_pdf,
                "strftime('%Y', fecha_timbrado)",
                "strftime('%m', fecha_timbrado)"),
            'id=%s' % id_cfdi)[0]
        #~ if self.editar:
            #~ template.Title = data[0].split('.')[0]
            #~ return
        properties = self.util.setPropertiesValues(
            ('FilterName', 'calc_pdf_Export'))
        #~ if self.destino:
            #~ path_pdf = self.util.systemToUrl(self.util.join(self.destino,
                                                            #~ self.data[0],
                                                            #~ self.data[1],
                                                            #~ data[0]))
        #~ else:
        path_pdf = self.util.getPathTemp(data[0])
        self.doc.storeToURL(self.util.systemToUrl(path_pdf), properties)
        if self.espejos:
            self.util.copy_pdf((data[1], data[2]), self.espejos, path_pdf)
        if self.show:
            self.util.execute(self.util.systemToUrl(path_pdf))
        self.doc.dispose()
        return

    def _nomina(self, xml):
        nomina = xml.find('%sComplemento' % PRE)
        nomina = nomina.find('%sNomina' % NOMINA)
        for k, v in nomina.attrib.items():
            if k == 'Banco':
                data = self.db.select(('bancos',), ('banco',), "clave=%s" % int(v))
                if data:
                    nv = '(%s) %s' % (v, data[0][0])
                else:
                    nv = '(%s) %s' % (v, '')
                self._set_cell('{nomina.%s}' % k, nv)
            elif k == 'TipoRegimen':
                nv = '(%s) %s' % (v, self.TIPO_REGIMEN[v])
                self._set_cell('{nomina.%s}' % k, nv)
            elif k == 'RiesgoPuesto':
                nv = '(%s) %s' % (v, self.RIESGO_PUESTO[v])
                self._set_cell('{nomina.%s}' % k, nv)
            else:
                self._set_cell('{nomina.%s}' % k, v)
        percepciones = nomina.find('%sPercepciones' % NOMINA)
        total = 0
        for k, v in percepciones.attrib.items():
            total += float(v)
            v = '$ %s' % self.format_s.format(float(v))
            self._set_cell('{percepciones.%s}' % k, v)
        v = '$ %s' % self.format_s.format(total)
        self._set_cell('{total.percepciones}', v)
        first = True
        for percepcion in percepciones.getchildren():
            ig = '$ %s' % self.format_s.format(
                float(percepcion.attrib['ImporteGravado']))
            ie = '$ %s' % self.format_s.format(
                float(percepcion.attrib['ImporteExento']))
            tp = percepcion.attrib['TipoPercepcion']
            concepto = percepcion.attrib['Concepto']
            if first:
                first = False
                cell_1 = self._set_cell('{percepcion.TipoPercepcion}', tp)
                cell_2 = self._set_cell('{percepcion.Concepto}', concepto)
                cell_3 = self._set_cell('{percepcion.ImporteGravado}', ig)
                cell_4 = self._set_cell('{percepcion.ImporteExento}', ie)
            else:
                cell_1 = self._set_cell(v=tp, cell=cell_1)
                cell_2 = self._set_cell(v=concepto, cell=cell_2)
                cell_3 = self._set_cell(v=ig, cell=cell_3)
                cell_4 = self._set_cell(v=ie, cell=cell_4)
        deducciones = nomina.find('%sDeducciones' % NOMINA)
        if deducciones is None: return
        total = 0
        for k, v in deducciones.attrib.items():
            total += float(v)
            v = '$ %s' % self.format_s.format(float(v))
            self._set_cell('{deducciones.%s}' % k, v)
        v = '$ %s' % self.format_s.format(total)
        self._set_cell('{total.deducciones}', v)
        first = True
        for deduccion in deducciones.getchildren():
            ig = '$ %s' % self.format_s.format(
                float(deduccion.attrib['ImporteGravado']))
            ie = '$ %s' % self.format_s.format(
                float(deduccion.attrib['ImporteExento']))
            td = deduccion.attrib['TipoDeduccion']
            concepto = deduccion.attrib['Concepto']
            if first:
                first = False
                cell_1 = self._set_cell('{deduccion.TipoDeduccion}', td)
                cell_2 = self._set_cell('{deduccion.Concepto}', concepto)
                cell_3 = self._set_cell('{deduccion.ImporteGravado}', ig)
                cell_4 = self._set_cell('{deduccion.ImporteExento}', ie)
            else:
                cell_1 = self._set_cell(v=td, cell=cell_1)
                cell_2 = self._set_cell(v=concepto, cell=cell_2)
                cell_3 = self._set_cell(v=ig, cell=cell_3)
                cell_4 = self._set_cell(v=ie, cell=cell_4)
        return

    def _timbre(self, xml, cadena):
        timbre = xml.find('%sComplemento' % PRE)
        timbre = timbre.find('%sTimbreFiscalDigital' % TIMBRE)
        for k, v in timbre.attrib.items():
            self._set_cell('{timbre.%s}' % k, v)
        total_s = '%017.06f' % float(xml.attrib['total'])
        qr_data = '?re=%s&rr=%s&tt=%s&id=%s' % (
            self.rfc_emisor, self.rfc_receptor, total_s, timbre.attrib['UUID'])
        ruta_cbb = self.util.getCBB(qr_data)
        pd = self.hoja.getDrawPage()
        image = self.doc.createInstance('com.sun.star.drawing.GraphicObjectShape')
        image.GraphicURL = self.util.systemToUrl(ruta_cbb)
        pd.add(image)
        self.util.size(image, 4500, 4500)
        self.sd.setSearchString('{timbre.cbb}')
        ranges = self.search.findAll(self.sd)
        if ranges:
            ranges = ranges.getRangeAddressesAsString().split(';')
            for r in ranges:
                for c in r.split(','):
                    cell = self.hoja.getCellRangeByName(c)
                    image.Anchor = cell
        self._set_cell('{timbre.cadenaoriginal}', cadena)
        return

    def _concepto(self, xml):
        conceptos = xml.find('%sConceptos' % PRE)
        for concepto in conceptos.getchildren():
            for k, v in concepto.attrib.items():
                self._set_cell('{concepto.%s}' % k, v)
        return

    def _receptor(self, xml):
        receptor = xml.find('%sReceptor' % PRE)
        self.rfc_receptor = receptor.attrib['rfc']
        for k, v in receptor.attrib.items():
            self._set_cell('{receptor.%s}' % k, v)
        domicilio = receptor.find('%sDomicilio' % PRE)
        for k, v in domicilio.attrib.items():
            self._set_cell('{receptor.%s}' % k, v)
        return

    def _emisor(self, xml):
        emisor = xml.find('%sEmisor' % PRE)
        self.rfc_emisor = emisor.attrib['rfc']
        for k, v in emisor.attrib.items():
            self._set_cell('{emisor.%s}' % k, v)
        domicilio = emisor.find('%sDomicilioFiscal' % PRE)
        for k, v in domicilio.attrib.items():
            self._set_cell('{emisor.%s}' % k, v)
        return

    def _comprobante(self, xml):
        for k, v in xml.attrib.items():
            if k == 'total' or k == 'descuento' or k == 'subTotal':
                v = '$ %s' % self.format_s.format(float(v))
            self._set_cell('{cfdi.%s}' % k, v)
        data = self.db.select(
            ('monedas',), where="moneda='%s'" % xml.attrib['Moneda'])
        if data:
            data = data[0]
            currency = data[1].lower()
            if currency in CURRENCIES:
                currency = CURRENCIES[currency]
            enletras = NumerosLetras().NumerosLetras(
                float(xml.attrib['total']), currency, data[2], data[3])
        else:
            enletras = NumerosLetras().NumerosLetras(float(xml.attrib['total']))
        self._set_cell('{total.enletras}', enletras.upper())
        return

    def _set_cell(self, k='', v='', cell=None):
        #~ print (k, v)
        if k:
            self.sd.setSearchString(k)
            ranges = self.search.findAll(self.sd)
            if ranges:
                ranges = ranges.getRangeAddressesAsString().split(';')
                for r in ranges:
                    for c in r.split(','):
                        cell = self.hoja.getCellRangeByName(c)
                        if cell.getImplementationName() == CELL_TYPE:
                            pattern = re.compile(k, re.IGNORECASE)
                            value = pattern.sub(v, cell.getString())
                            cell.setString(value)
                return cell
        if cell:
            if cell.getImplementationName() == CELL_TYPE:
                ca = cell.getCellAddress()
                new_cell = self.hoja.getCellByPosition(ca.Column, ca.Row + 1)
                new_cell.setString(v)
                return new_cell

    def _cancelado(self, estatus):
        if estatus != CANCELADO:
            pd = self.hoja.getDrawPage()
            if pd.getCount():
                pd.remove(pd.getByIndex(0))
        return
