# -*- coding: utf-8 -*-
import uno
from .numlet import NumerosLetras

EXTENSION_PDF = '.pdf'
EXTENSION_CBB = '%s_cbb'
HIDDEN = 'Hidden'
AS_TEMPLATE = 'AsTemplate'
LEYENDA = """Número de aprobación SICOFI: %s
Este comprobante tendrá una vigencia de dos años contados a partir de la fecha
de aprobación de la asignación de folios, la cual es: %s"""


class CBBPDF(object):

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.util = caller.util
        self.unogui = caller.unogui
        self.globales = caller.globales
        self.format_s = caller.format_s
        template = caller.plantilla
        template = template.split('.')
        template[-2] = EXTENSION_CBB % template[-2]
        self.plantilla = '.'.join(template)
        self.hoja = None
        self.celdas = {}
        self.properties = None
        self.editar = caller.editar
        self.show = caller.show
        self.destino = caller.destino
        #~ self.path_pdf = ''

    def generate_pdf(self, factura):
        self.properties = self.util.setPropertiesValues(
                                (HIDDEN, not self.editar, AS_TEMPLATE, True))
        doc = self.unogui.openDoc(self.plantilla, self.properties)
        if not doc:
            message = 'No fue posible abrir la plantilla, consulte a soporte técnico'
            self.unogui.createMsgBox({'Message': message})
            return
        doc.dispose()
        celdas = self.db.select(('celdas',))
        for row in celdas:
            self.celdas[row[1].lower()] = row[2]
        self.__write_data(factura)
        return True

    def __write_data(self, id_cfd):
        template = self.unogui.openDoc(self.plantilla, self.properties)
        self.hoja = template.getSheets().getByIndex(0)
        self.__emisor(id_cfd)
        self.__receptor(id_cfd)
        self.__totales(id_cfd)
        self.__comprobante(id_cfd, template)
        self.__personalizados(id_cfd)
        self.__conceptos(id_cfd)
        self.__cancelada(id_cfd)
        self.__save_pdf(template, id_cfd)
        return

    def __save_pdf(self, template, id_cfd):
        name_pdf = "serie || substr('000000' || folio, -6, 6) || '_' || rfc || '.pdf'"
        where = '%s.id_cliente=receptores.id AND %s.id=%s' % (
                                                        'cfdfacturas',
                                                        'cfdfacturas',
                                                        id_cfd)
        data = self.db.select(('cfdfacturas', 'receptores'), (name_pdf,), where)[0]
        if self.editar:
            template.Title = data[0].split('.')[0]
            return
        properties = self.util.setPropertiesValues(('FilterName', 'calc_pdf_Export'))
        if self.destino:
            path_pdf = self.util.systemToUrl(self.util.join(self.destino, data[0]))
        else:
            path_pdf = self.util.systemToUrl(self.util.getPathTemp(data[0]))
            self.path_pdf = self.util.urlToSystem(path_pdf)
        template.storeToURL(path_pdf, properties)
        if self.show:
            self.util.execute(path_pdf)
        template.dispose()
        return

    def __emisor(self, id_cfd):
        emisor = self.db.select(('emisor',))[0]
        self.__write_cell(self.celdas['emisorrfc'], emisor[1])
        self.__write_cell(self.celdas['emisornombre'], emisor[2])
        address = emisor[3] + ' ' + emisor[4] + ' ' + emisor[5]
        self.__write_cell(self.celdas['emisordireccion1'], address)
        address = ''
        if emisor[6]:
            address = 'Col. ' + emisor[6]
        if emisor[12]:
            if address:
                address += ', C.P. ' + emisor[12]
            else:
                address = 'C.P. ' + emisor[12]
        if address:
            self.__write_cell(self.celdas['emisordireccion2'], address)
        address = ''
        if emisor[9]:
            address = emisor[9]
        if emisor[10]:
            if address:
                address += ', ' + emisor[10]
            else:
                address = emisor[10]
        if emisor[11]:
            if address:
                address += ', ' + emisor[11]
            else:
                address = emisor[11]
        if address:
            self.__write_cell(self.celdas['emisordireccion3'], address)
        self.__write_cell(self.celdas['emisortelefono'], emisor[13])
        self.__write_cell(self.celdas['donatariaautorizacion'], emisor[17])
        self.__write_cell(self.celdas['donatariafecha'], str(emisor[18]))
        leyenda = self.db.select_field('sat', 'dleyenda')
        self.__write_cell(self.celdas['donatarialeyenda'], leyenda)
        correo = self.db.select_field('emisor', 'correo')
        self.__write_cell(self.celdas['emisorcorreo'], correo)

        emisor = self.db.select(('expedidoen',))
        if emisor:
            emisor = emisor[0]
            address = emisor[1] + ' ' + emisor[2] + ' ' + emisor[3]
            self.__write_cell(self.celdas['expedidoendireccion1'], address)
            address = ''
            if emisor[4]:
                address = 'Col. ' + emisor[4]
            if emisor[10]:
                if address:
                    address += ', C.P. ' + emisor[10]
                else:
                    address = 'C.P. ' + emisor[10]
            if address:
                self.__write_cell(self.celdas['expedidoendireccion2'], address)
            address = ''
            if emisor[7]:
                address = emisor[7]
            if emisor[8]:
                if address:
                    address += ', ' + emisor[8]
                else:
                    address = emisor[8]
            if emisor[9]:
                if address:
                    address += ', ' + emisor[9]
                else:
                    address = emisor[9]
            if address:
                self.__write_cell(self.celdas['expedidoendireccion3'], address)
            self.__write_cell(self.celdas['expedidoentelefono'], emisor[11])

        return

    def __receptor(self, id_cfd):
        id_receptor = self.db.select(
                                    ('cfdfacturas',),
                                    ('id_cliente',),
                                    'id=%s' % id_cfd)[0][0]
        receptor = self.db.select(('receptores',), where='id=%s' % id_receptor)[0]
        self.__write_cell(self.celdas['receptorrfc'], receptor[1])
        self.__write_cell(self.celdas['receptornombre'], receptor[2])
        address = receptor[3] + ' ' + receptor[4] + ' ' + receptor[5]
        self.__write_cell(self.celdas['receptordireccion1'], address)
        address = ''
        if receptor[6]:
            address = 'Col. ' + receptor[6]
        if receptor[12]:
            if address:
                address += ', C.P. ' + receptor[12]
            else:
                address = 'C.P. ' + receptor[12]
        if address:
            self.__write_cell(self.celdas['receptordireccion2'], address)
        address = ''
        if receptor[9]:
            address = receptor[9]
        if receptor[10]:
            if address:
                address += ', ' + receptor[10]
            else:
                address = receptor[10]
        if receptor[11]:
            if address:
                address += ', ' + receptor[11]
            else:
                address = receptor[11]
        if address:
            self.__write_cell(self.celdas['receptordireccion3'], address)

        return

    def __totales(self, id_cfd):
        fields = (
                'subTotal',
                'motivoDescuento',
                'descuento',
                'totalImpuestosTrasladados',
                'totalImpuestosRetenidos',
                'total')
        factura = self.db.select(
                                ('cfdfacturas',),
                                fields,
                                'id=%s' % id_cfd)[0]
        self.__write_cell(self.celdas['subtotalimporte'], factura[0], value=True)
        self.__write_cell(self.celdas['motivodescuento'], factura[1])
        if factura[2]:
            self.__copy_cell(self.celdas['subtotaltitulo'])
            self.celdas['subtotaltitulo'] = self.__next_cell(self.celdas['subtotaltitulo'])
            self.__write_cell(self.celdas['subtotaltitulo'], 'Descuento')
            self.__copy_cell(self.celdas['subtotalimporte'])
            self.celdas['subtotalimporte'] = self.__next_cell(self.celdas['subtotalimporte'])
            self.__write_cell(self.celdas['subtotalimporte'], factura[2], value=True)
        if factura[3]:
            self.__write_cell(self.celdas['totalimpuestostrasladados'], factura[3], value=True)
            traslados = self.db.select(
                                ('cfdimpuestos',),
                                ('nombre', 'tasa', 'importe'),
                                "tipo='Traslado' AND id_cfd=%s" % id_cfd)
            for traslado in traslados:
                self.__copy_cell(self.celdas['subtotaltitulo'])
                self.celdas['subtotaltitulo'] = self.__next_cell(self.celdas['subtotaltitulo'])
                title = '%s %s%%' % (traslado[0], traslado[1])
                self.__write_cell(self.celdas['subtotaltitulo'], title)
                self.__copy_cell(self.celdas['subtotalimporte'])
                self.celdas['subtotalimporte'] = self.__next_cell(self.celdas['subtotalimporte'])
                self.__write_cell(self.celdas['subtotalimporte'], traslado[2], value=True)
        if factura[4]:
            self.__write_cell(self.celdas['totalimpuestosretenidos'], factura[4], value=True)
            retenciones = self.db.select(
                                (self.tables['impuestos'],),
                                ('nombre', 'tasa', 'importe'),
                                "tipo='Retencion' AND id_cfd=%s" % id_cfd)
            for retencion in retenciones:
                self.__copy_cell(self.celdas['subtotaltitulo'])
                self.celdas['subtotaltitulo'] = self.__next_cell(self.celdas['subtotaltitulo'])
                try:
                    impuesto = str(abs(float(retencion[1]))) + '%'
                except:
                    impuesto = retencion[1]
                title = 'Retención %s %s' % (retencion[0], impuesto)
                self.__write_cell(self.celdas['subtotaltitulo'], title)
                self.__copy_cell(self.celdas['subtotalimporte'])
                self.celdas['subtotalimporte'] = self.__next_cell(self.celdas['subtotalimporte'])
                self.__write_cell(self.celdas['subtotalimporte'], retencion[2], value=True)
        if factura[5]:
            self.__copy_cell(self.celdas['subtotaltitulo'])
            self.celdas['subtotaltitulo'] = self.__next_cell(self.celdas['subtotaltitulo'])
            self.__write_cell(self.celdas['subtotaltitulo'], 'TOTAL')
            self.__copy_cell(self.celdas['subtotalimporte'])
            self.celdas['subtotalimporte'] = self.__next_cell(self.celdas['subtotalimporte'])
            self.__write_cell(self.celdas['subtotalimporte'], factura[5], value=True)
        return

    def __comprobante(self, id_cfd, template):
        factura = self.db.select(('cfdfacturas',), where='id=%s' % id_cfd)[0]
        dias = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes',
                    'sábado', 'domingo')
        meses = ('0', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')
        fecha = ''
        if factura[19]:
            fecha = '%s, ' % factura[19]
        fecha += '%s, %s de %s de %s' % (
                                        dias[factura[6].weekday()],
                                        factura[6].day,
                                        meses[factura[6].month],
                                        factura[6].year)
        self.__write_cell(self.celdas['comprobantefecha'], fecha)
        fecha = factura[6].strftime('%H:%M:%S')
        self.__write_cell(self.celdas['comprobantehora'], fecha)
        folio = ''
        if factura[2]:
            folio = '%s-%s' % (factura[2], factura[5])
        else:
            folio = factura[5]
        self.__write_cell(self.celdas['comprobantefolio'], folio)
        #~ self.__write_cell(self.celdas['comprobanteaprobacionno'], factura[3])
        self.__write_cell(self.celdas['comprobantecertificadono'], factura[3])
        #~ self.__write_cell(self.celdas['comprobanteaprobacionfecha'], factura[4])
        self.__write_cell(self.celdas['comprobantecertificadosat'], factura[4])
        self.__write_cell(self.celdas['comprobantetipocomprobante'], factura[17])
        self.__write_cell(self.celdas['emisorregimen'], factura[33])
        self.__write_cell(self.celdas['comprobantemoneda'], factura[15])
        self.__write_cell(self.celdas['comprobantetipocambio'], factura[14])
        notas = ''
        if factura[7]:
            if self.celdas['comprobanteformadepago']:
                self.__write_cell(self.celdas['comprobanteformadepago'], factura[7])
            else:
                notas = 'Forma de Pago: %s' % factura[7]
        if factura[18]:
            if self.celdas['comprobantemetododepago']:
                self.__write_cell(self.celdas['comprobantemetododepago'], factura[18])
            else:
                if notas:
                    notas += '\nMétodo de Pago: %s' % factura[18]
                else:
                    notas = 'Método de Pago: %s' % factura[18]
        if factura[20]:
            if self.celdas['comprobantenumerocuentapago']:
                self.__write_cell(self.celdas['comprobantenumerocuentapago'], factura[20])
            else:
                if notas:
                    notas += '\nNúmero Cuenta de Pago: %s' % factura[20]
                else:
                    notas = 'Número Cuenta de Pago: %s' % factura[20]
        if factura[10]:
            if self.celdas['comprobantecondicionesdepago']:
                self.__write_cell(self.celdas['comprobantecondicionesdepago'], factura[10])
            else:
                if notas:
                    notas += '\nCondiciones de Pago: %s' % factura[10]
                else:
                    notas = 'Condiciones de Pago: %s' % factura[10]
        nota = factura[29]
        if nota:
            notas = 'Notas: \n' + nota + '\n\n' + notas
        if notas:
            self.__write_cell(self.celdas['comprobantenotas'], notas)

        #~ if self.celdas['comprobanteleyenda']:
        if self.celdas['comprobantesellosat']:
            #~ leyenda = self.db.select_field('sat', 'leyenda1')
            leyenda = LEYENDA % (factura[3], factura[4])
            self.__write_cell(self.celdas['comprobantesellosat'], leyenda)

        if self.celdas['totalenletras']:
            data = self.db.select(('monedas',), where="moneda='%s'" % factura[15])
            if data:
                data = data[0]
                enletras = NumerosLetras().NumerosLetras(
                                        factura[16], data[1], data[2], data[3])
            else:
                enletras = NumerosLetras().NumerosLetras(factura[16])
            self.__write_cell(self.celdas['totalenletras'], enletras.upper())
        if factura[9]:     # folio
            ruta_cbb = self.__getCBB(factura[9])
            pd = self.hoja.getDrawPage()
            image = template.createInstance('com.sun.star.drawing.GraphicObjectShape')
            image.GraphicURL = self.util.systemToUrl(ruta_cbb)
            pd.add(image)
            self.util.size(image, 3100, 3100)
            celda = self.hoja.getCellRangeByName(self.celdas['comprobantecbb'])
            image.Anchor = celda
        return

    def __getCBB(self, cbb):
        ruta = self.util.getPathTemp()
        #~ cbb = self.db.select(('folios',), ('cbb',), 'id=%s' % id_folio)
        if cbb:
            cbb = cbb.decode('base64')
            f = open(ruta, 'wb')
            f.write(cbb)
            f.close()
            return ruta

    def __personalizados(self, id_cfd):
        data = self.db.select(
                ('cfdpersonalizados', 'campospersonalizados'),
                ('celda1', 'valor'),
                '%s.campo=campospersonalizados.nodo and id_cfd=%s' % (
                    'cfdpersonalizados', id_cfd))
        if data:
            for row in data:
                self.__write_cell(row[0], row[1])
        return

    def __conceptos(self, id_cfd):
        conceptos = self.db.select(('cfddetalle',), where='id_cfd=%s' % id_cfd)
        row = self.__copy_rows(len(conceptos))
        for concepto in conceptos:
            self.__write_item(concepto, row)
            row += 1
        return

    def __write_item(self, concepto, row):
        cell = self.hoja.getCellByPosition(0, row)
        cell.setString(concepto[5])
        cell = self.hoja.getCellByPosition(21, row)
        cell.setString(concepto[4])
        cell = self.hoja.getCellByPosition(24, row)
        cell.setValue(concepto[3])
        cell = self.hoja.getCellByPosition(28, row)
        cell.setValue(concepto[7])
        cell = self.hoja.getCellByPosition(33, row)
        cell.setValue(concepto[8])
        text = concepto[6]
        if concepto[9]:
            text += '\nPedimento de Importación No. %s\n' % concepto[9]
            text += 'Aduana: %s, Fecha del pedimento: %s' % (
                        concepto[11], concepto[10])
        cuentapredial = concepto[12].strip()
        if cuentapredial:
            text += '\n\nCuenta Predial Número: %s' % cuentapredial
        cell = self.hoja.getCellByPosition(4, row)
        cell.setString(text)
        return

    def __write_cell(self, name, data, style='', value=False):
        #if not name or not data:
        if not name:
            return
        try:
            celda = self.hoja.getCellRangeByName(name)
        except:
            print('Error al asignar la celda: %s' % name)
            return
        if value:
            celda.setValue(float(data))
        else:
            celda.setString(data)
        if style:
            celda.CellStyle = style
        return

    def __next_cell(self, celda):
        if isinstance(celda, str):
            for i,v in enumerate(celda):
                if v.isdigit():
                    break
            row = int(celda[i:]) + 1
            return celda[:i] + str(row)
        return

    def __copy_cell(self, celda):
        origen = self.hoja.getCellRangeByName(celda)
        destino = self.hoja.getCellRangeByName(self.__next_cell(celda))
        self.hoja.copyRange( destino.getCellAddress(), origen.getRangeAddress() )
        return

    def __copy_rows(self, num):
        celda = self.hoja.getCellRangeByName(self.celdas['conceptos'])
        row = celda.getCellAddress().Row
        if num > 1:
            num -= 1
            self.hoja.getRows().insertByIndex(row+1, num)
            origen = celda.getRangeAddress()
            origen.EndColumn = 38
            destino = celda.getCellAddress()
            for i in range(num):
                destino.Row += 1
                self.hoja.copyRange(destino, origen)
        return row

    def __cancelada(self, id_cfd):
        cancelada = self.db.select(
                                ('cfdfacturas',),
                                ('estatus',),
                                'id=%s'%id_cfd)[0][0]
        if cancelada != 3:
            pd = self.hoja.getDrawPage()
            if pd.getCount():
                pd.remove(pd.getByIndex(0))
        return
