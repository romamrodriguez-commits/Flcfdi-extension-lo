# -*- coding: utf-8 -*-
import re
import traceback
import locale
import subprocess
from xml.etree import ElementTree as ET
from .numlet import NumerosLetras


EXTENSION_PDF = '.pdf'
PRE = '{http://www.sat.gob.mx/cfd/2}'
PATH_TEMPLATE = '/bin/plantilla_factura.ods'
PATH_XSLTPROC = '/bin/xsltproc.exe'
PATH_XSLT = '/bin/cadena22.xslt'

EXTENSION_CFD = '%s_cfd'
HIDDEN = 'Hidden'
AS_TEMPLATE = 'AsTemplate'
XSLTPROC = 'xsltproc%s'
XSLT = 'cadena%s.xslt'
CELL_TYPE = 'ScCellObj'
CANCELADA = 'Cancelada'
CLEAN = "\{(\w.+)\}"


class CFD2PDF(object):

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        self.unogui = caller.unogui
        self.globales = caller.globales
        self.format_s = caller.format_s
        self.hoja = None
        self.sd = None
        self.search = None
        self.celdas = {}
        if self.globales['OS'] == self.globales['WIN']:
            self.path_xsltproc = self.util.urlToSystem(
                self.globales['EXT_PATH'] + PATH_XSLTPROC)
        else:
            self.path_xsltproc = 'xsltproc'
        self.path_xslt = self.util.urlToSystem(
            self.globales['EXT_PATH'] + PATH_XSLT)
        self.destino = caller.destino
        self.path_pdf = ''
        self.show = caller.show
        self.editar = caller.editar
        self.rfc_emisor = ''
        self.rfc_receptor = ''
        self.moneda = ''
        template = caller.plantilla
        template = template.split('.')
        template[-2] = EXTENSION_CFD % template[-2]
        self.plantilla = '.'.join(template)
        self.template = None
        self.tree = None

    def generate_pdf(self, factura):
        #~ print (self.plantilla)
        self.properties = self.util.setPropertiesValues(
                                (HIDDEN, not self.editar, AS_TEMPLATE, True))
        self.template = self.unogui.openDoc(self.plantilla, self.properties)
        if not self.template:
            msg = 'No fue posible abrir la plantilla, consulte a soporte técnico'
            self.unogui.createMsgBox({'Message': msg})
            return
        #~ celdas = self.db.select(('celdascfd',))
        #~ for row in celdas:
            #~ self.celdas[row[1].lower()] = row[2]
        try:
            self._write_data(factura)
        except:
            print (traceback.format_exc())
        return

    def _write_data(self, id_cfd):
        self.hoja = self.template.getSheets().getByIndex(0)
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
        xml = self.db.select(('cfdfacturas',), ('xml',), 'id=%s'%id_cfd)[0][0]
        self.tree = ET.fromstring(xml)
        self._comprobante(self.tree)
        self._emisor(self.tree)
        self._receptor(self.tree)
        self._totales(self.tree)
        self._donataria(self.tree)
        self._conceptos(self.tree)
        self._cancelada(id_cfd)
        self._clean()
        self._save_pdf(id_cfd)
        return

    def _conceptos(self, xml):
        conceptos = xml.find('%sConceptos' % PRE)
        if conceptos is None:
            return
        first = True
        for c in conceptos.getchildren():
            key = ''
            if 'noIdentificacion' in c.attrib:
                key = c.attrib['noIdentificacion']
            description = self._get_description(c)
            unidad = ''
            if 'unidad' in c.attrib:
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
                cell_6 = self._set_cell('{importe}', importe, value=True)
            else:
                row = cell_2.getCellAddress().Row + 1
                self.hoja.getRows().insertByIndex(row, 1)
                self._copy_cell(cell_1)
                self._copy_cell(cell_2)
                self._copy_cell(cell_3)
                self._copy_cell(cell_4)
                self._copy_cell(cell_5)
                self._copy_cell(cell_6)
                cell_1 = self._set_cell(v=key, cell=cell_1)
                cell_2 = self._set_cell(v=description, cell=cell_2)
                cell_3 = self._set_cell(v=unidad, cell=cell_3)
                cell_4 = self._set_cell(v=cantidad, cell=cell_4, value=True)
                cell_5 = self._set_cell(v=precio, cell=cell_5, value=True)
                cell_6 = self._set_cell(v=importe, cell=cell_6, value=True)
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

    def _donataria(self, xml):
        complemento = xml.find('%sComplemento' % PRE)
        if complemento is None:
            return
        donataria = complemento.find('{http://www.sat.gob.mx/donat}Donatarias')
        if donataria is not None:
            for k, v in donataria.attrib.items():
                self._set_cell('{donataria.%s}' % k, v)
        return

    def _totales(self, xml):
        cell_title = self._set_cell('{subtotal.titulo}', 'Subtotal')
        value = xml.attrib['subTotal']
        cell_value = self._set_cell('{subtotal}', value, value=True)
        if 'descuento' in xml.attrib:
            self._copy_cell(cell_title)
            self._copy_cell(cell_value)
            cell_title = self._set_cell(v='Descuento', cell=cell_title)
            value = xml.attrib['descuento']
            cell_value = self._set_cell(v=value, cell=cell_value, value=True)
        imp = xml.find('%sImpuestos' % PRE)
        if imp is not None:
            node = imp.find('%sTraslados' % PRE)
            if node is not None:
                for t in node.getchildren():
                    self._copy_cell(cell_title)
                    self._copy_cell(cell_value)
                    title = '%s %s%%' % (t.attrib['impuesto'], t.attrib['tasa'])
                    value = t.attrib['importe']
                    cell_title = self._set_cell(v=title, cell=cell_title)
                    cell_value = self._set_cell(
                        v=value, cell=cell_value, value=True)
            node = imp.find('%sRetenciones' % PRE)
            if node is not None:
                for t in node.getchildren():
                    self._copy_cell(cell_title)
                    self._copy_cell(cell_value)
                    title = 'Retención %s' % t.attrib['impuesto']
                    value = t.attrib['importe']
                    cell_title = self._set_cell(v=title, cell=cell_title)
                    cell_value = self._set_cell(
                        v=value, cell=cell_value, value=True)

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
                    cell_value = self._set_cell(
                        v=value, cell=cell_value, value=True)

        if 'total' in xml.attrib:
            self._copy_cell(cell_title)
            self._copy_cell(cell_value)
            cell_title = self._set_cell(v='Total', cell=cell_title)
            value = xml.attrib['total']
            cell_value = self._set_cell(v=value, cell=cell_value, value=True)
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
        if not 'lugarExpedicion' in xml.attrib:
            lugar = ''
            if 'municipio' in domicilio.attrib:
                lugar = domicilio.attrib['municipio']
            if 'estado' in domicilio.attrib:
                lugar += ', %s' % domicilio.attrib['estado']
            self._set_cell('{cfdi.lugarExpedicion}', lugar)
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
        enletras = ''
        if 'Moneda' in xml.attrib:
            data = self.db.select(
                ('monedas',), where="moneda='%s'" % xml.attrib['Moneda'])
            if data:
                data = data[0]
                enletras = NumerosLetras().NumerosLetras(
                    float(xml.attrib['total']), data[1], data[2], data[3])
        if not enletras:
            enletras = NumerosLetras().NumerosLetras(float(xml.attrib['total']))
        self._set_cell('{cfdi.totalenletras}', enletras.upper())
        fecha = xml.attrib['fecha'].split('-')
        self.data = (fecha[0], fecha[1])
        fecha = xml.attrib['fecha'].split('T')
        self._set_cell('{cfdi.hora}', fecha[1])
        fecha = self.util.format_date(fecha[0], '%A, %d de %B del %Y')
        self._set_cell('{cfdi.fechaformato}', fecha)
        data = {
            'formaDePago': 'Forma de Pago: ',
            'metodoDePago': 'Método de Pago: ',
            'condicionesDePago': 'Condiciones de Pago: ',
            'NumCtaPago': 'Número de Cuenta de Pago: ',
        }
        cfdi_data = ''
        for k, v in data.items():
            if k in xml.attrib:
                cfdi_data += '%s %s\n' % (v, xml.attrib[k])
        if 'Moneda' in xml.attrib:
            moneda = xml.attrib['Moneda']
            cfdi_data += 'Moneda: %s\n' % (moneda)
            if not moneda.lower() in ('peso', 'mxn'):
                if 'TipoCambio' in xml.attrib:
                    tipo_cambio = xml.attrib['TipoCambio']
                    cfdi_data += 'Tipo de Cambio: %s\n' % (tipo_cambio)
        self._set_cell('{cfdi.datos}', cfdi_data)
        cadena = self._get_cadena()
        self._set_cell('{cfdi.cadena}', cadena)
        return

    def _get_cadena(self):
        ext = ''
        path_xsltproc = XSLTPROC % ext
        if self.globales['OS'] == self.globales['WIN']:
            ext = '.exe'
            path_xsltproc = self.util.join(self.globales['PATH'], XSLTPROC % ext)
        version = self.tree.attrib['version']
        path_xslt = self.util.join(self.globales['PATH'], XSLT % version)
        path_xml = self.util.getPathTemp()
        self.util.save_file(path_xml, ET.tostring(self.tree))
        args = '{0} "{1}" "{2}"'.format(path_xsltproc, path_xslt, path_xml)
        cadena = subprocess.check_output(args, shell=True).decode()
        return cadena

    def _save_pdf(self, id_cfd, show=True):
        name_pdf = "serie || substr('000000' || folio, -6, 6) || '_%s.pdf'" % self.rfc_receptor
        where = 'id=%s' % id_cfd
        data = self.db.select(('cfdfacturas',), (name_pdf,), where)[0]
        if self.editar:
            self.template.Title = data[0].split('.')[0]
            return
        properties = self.util.setPropertiesValues(('FilterName', 'calc_pdf_Export'))
        if self.destino:
            path_pdf = self.util.systemToUrl(self.util.join(self.destino, data[0]))
        else:
            path_pdf = self.util.systemToUrl(self.util.getPathTemp(data[0]))
            self.path_pdf = self.util.urlToSystem(path_pdf)
        self.template.storeToURL(path_pdf, properties)
        if show:
            self.util.execute(path_pdf)
        self.template.dispose()
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

    def __personalizados(self, id_cfd):
        data = self.db.select(
            ('cfdpersonalizados', 'campospersonalizados'),
            ('celda1', 'valor'),
            'cfdpersonalizados.campo=campospersonalizados.nodo and id_cfd=%s' % id_cfd)
        if data:
            for row in data:
                self.__write_cell(row[0], row[1])
        return

    def _cancelada(self, id_cfd):
        cancel = self.db.select(
            ('cfdfacturas',), ('estatus',), 'id=%s' % id_cfd)[0][0]
        if cancel != CANCELADA:
            pd = self.hoja.getDrawPage()
            if pd.getCount():
                pd.remove(pd.getByIndex(0))
        return
