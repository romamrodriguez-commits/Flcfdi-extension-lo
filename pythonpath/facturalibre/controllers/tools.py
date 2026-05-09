# -*- coding: utf-8 -*-
import logging

from facturalibre.settings import LOG, EXT, BUTTON_CLICK
from facturalibre.modulos import util
from facturalibre.modulos.pyXml import ImportXML


log = logging.getLogger(LOG['NAME'])


class EventosTools(object):

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.emisor = ''

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def _config(self, item=0):
        self.dm.Step = item
        self.emisor = self.db.select_field('emisor', 'rfc')
        if item == 1:
            if not self.emisor:
                self.dm.Step = 15
                msg = 'Configura primero los datos del emisor ' \
                    'antes de usar esta herramienta'
                util.msgbox(msg)
                return
        if item > 3:
            util.msgbox('Puedes cooperar para estas herramientas')
        return

    def cmdSeleccionarDirectorio(self):
        folder = util.get_folder(util.get_path_user())
        if not folder:
            return
        if not util.is_readable(folder):
            msg = 'No tienes derechos de lectura en el ' \
                'directorio:\n\n{}'.format(folder)
            util.msgbox(msg)
            return
        self.dm.txtDirectorio.Text = folder
        return

    def cmdImportarDatos(self):
        folder = self._validate()
        if not folder:
            return
        files = util.get_files(folder, EXT['XML'])
        if not files:
            msg = 'No se encontraron archivos XML en el ' \
                'directorio:\n\n{}'.format(folder)
            util.msgbox(msg)
            return
        msg = 'Se encontraron {} archivos XML.'.format(len(files))
        clientes = self.dm.chkImportarClientes.State
        if clientes:
            msg += '\nSe importaran también los clientes'
        productos = self.dm.chkImportarProductos.State
        if productos:
            msg += '\nSe importaran también los productos'
        msg += '\n\n¿Estas seguro de importalos?'
        if util.question(msg) == BUTTON_CLICK['NO']:
            return
        if self.dm.chkCopia1.State:
            self.db.backup()
        try:
            msg = self._import_xml(files, clientes, productos)
            util.msgbox(msg)
        except Exception as e:
            log.error('INIT: ', exc_info=True)
        return

    def _validate(self):
        if not self.emisor:
            log = 'El emisor no esta configurado'
            util.msgbox(msg)
            return
        txt = self.dialog.getControl('txtDirectorio')
        folder = txt.Text.strip()
        if not folder:
            msg = 'Debes de seleccionar un directorio'
            txt.setFocus()
            util.msgbox(msg)
            return
        if not util.is_dir(folder):
            msg = 'La ruta seleccionada no es un directorio'
            txt.setFocus()
            util.msgbox(msg)
            return
        if not util.is_readable(folder):
            msg = 'No tienes derechos de lectura en el ' \
                'directorio:\n\n{}'.format(folder)
            txt.setFocus()
            util.msgbox(msg)
            return
        return folder

    def _import_xml(self, files, clientes=False, productos=False):
        total = len(files)
        c1 = 0
        pb = self.dialog.getControl('pbImport')
        lbl = self.dialog.getControl('lblInfo')
        pb.setVisible(True)
        lbl.setVisible(True)
        pb.setRange(1, total)

        #~ l = []
        #~ for i,f in enumerate(files):
            #~ pb.setValue(i)
            #~ doc = ET.parse(f)
            #~ root = doc.getroot()
            #~ l.append((int(root.attrib['folio']), f))
        #~ l = sorted(l, key=lambda s: s[0])

        import_xml = ImportXML(self.db, self.emisor, clientes, productos)
        for i, f in enumerate(files):
            pb.setValue(i)
            if import_xml.save(f):
                c1 += 1
        pb.setVisible(False)
        msg = 'Total de documentos encontrados: {}\n' \
            'Total de documentos importados: {}\n\n'.format(total, c1)
        msg += 'Si importaste productos, es IMPORTANTE establezcas sus ' \
            'impuestos ANTES de intentar usarlos en alguna factura.'
        return msg

    def cmdActualizarDatos(self):
        self.dm.txtResultado.Text = ''
        plantilla = self.dialog.getControl('txtUpdate')
        if util.validate(plantilla, 'Vacio'):
            plantilla.setFocus()
            msg = 'Establece la ruta del archivo ODS de Calc'
            util.msgbox(msg)
            return
        if not util.exists(plantilla.Text):
            msg = 'No se encontró el archivo ODS en la ruta establecida'
            util.msgbox(msg)
            return
        _, _, _, extension = util.path_info(plantilla.Text)
        if extension[1:] != EXT['ODS']:
            msg = 'El archivo no es un archivo ODS de Calc'
            util.msgbox(msg)
            return
        if self.dm.chkCopia2.State:
            self.db.backup()
        data = (
            ('Hidden', True),
            ('AsTemplate', True),
        )
        properties = util.set_properties(data)
        doc = util.doc_open(plantilla.Text, properties)
        for s in range(doc.getSheets().getCount()):
            self._update_data(doc.getSheets().getByIndex(s))
        doc.dispose()
        self.dm.txtResultado.Text += 'Proceso terminado...'
        return

    def _update_data(self, sheet):
        name = sheet.getName()
        msg = 'Intentando actualizar la tabla: {} ...\n'.format(name)
        self.dm.txtResultado.Text += msg

        try:
            r = self.db.select_field(name.lower(), 'id')
        except:
            msg = 'La tabla: {}, no existe en la base de datos.\n'.format(name)
            self.dm.txtResultado.Text += msg
            return

        f = self._get_fields(sheet)
        if not f[0]:
            msg = 'La tabla: {}, esta vacía.\n'.format(name)
            self.dm.txtResultado.Text += msg
            return
        if len(f) < 2:
            msg = 'Hacen falta campos en la tabla: {}\n'.format(name)
            self.dm.txtResultado.Text += msg
            return
        requerido = 'id'
        if name == 'cfdfacturas':
            requerido = 'seriefolio'
        if f[0].lower() != requerido:
            msg = 'El primer campo en la tabla {} debe ser: {}\n'.format(
                name, requerido.upper())
            self.dm.txtResultado.Text += msg
            return
        d = self._get_data(sheet)
        if not d:
            msg = 'La tabla: {}, no tiene datos para actualizar.\n'.format(name)
            self.dm.txtResultado.Text += msg
            return
        w = 'id={}'
        if name == 'cfdfacturas':
            w = "serie||folio='{}'"
        u = 0
        for r in d:
            d = {}
            for i, v in enumerate(f):
                if i == 0:
                    if name == 'cfdfacturas':
                        where = w.format(r[i])
                    else:
                        where = w.format(int(r[i]))
                else:
                    d[v] = r[i]
            if self.db.update(name, d, where):
                u += 1
            else:
                self.dm.txtResultado.Text += self.db.error + '\n'
        if u == 0:
            msg = 'Tabla: {}, hubo errores al actualizar...\n'.format(name)
        else:
            msg = 'Tabla: {}, {} registros actualizados...\n'.format(name, u)
        self.dm.txtResultado.Text += msg
        return

    def _get_data(self, sheet):
        cell = sheet.getCellByPosition(0,0)
        c = sheet.createCursorByRange(cell)
        c.collapseToCurrentRegion()
        if c.getRows().getCount() == 1:
            return None
        cells = sheet.getCellRangeByPosition(0, 1,
            c.getRangeAddress().EndColumn, c.getRangeAddress().EndRow)
        return cells.getDataArray()

    def _get_fields(self, sheet):
        cell = sheet.getCellByPosition(0,0)
        c = sheet.createCursorByRange(cell)
        c.collapseToCurrentRegion()
        cells = sheet.getCellRangeByPosition(
            0, 0, c.getRangeAddress().EndColumn, 0)
        d = cells.getDataArray()
        return d[0]

    def cmdImportarProductos(self):
        plantilla = self.dialog.getControl('fileProductos')
        if util.validate(plantilla, 'Vacio'):
            plantilla.setFocus()
            msg = 'Establece la ruta del archivo ODS de Calc con los ' \
                'productos a importar'
            util.msgbox(msg)
            return
        if not util.exists(plantilla.Text):
            msg = 'No se encontró el archivo ODS en la ruta establecida'
            util.msgbox(msg)
            return
        _, _, _, extension = util.path_info(plantilla.Text)
        if extension[1:] != EXT['ODS']:
            msg = 'El archivo no es un archivo ODS de Calc'
            util.msgbox(msg)
            return
        data = (
            ('Hidden', True),
            ('AsTemplate', True),
        )
        properties = util.set_properties(data)
        doc = util.doc_open(plantilla.Text, properties)
        sheet = doc.getSheets().getByIndex(0)
        self._import_products(sheet)
        doc.dispose()
        return

    def _import_products(self, sheet):
        data = self._get_data(sheet)
        if not data:
            msg = 'El archivo no contiene datos a importar'
            util.msgbox(msg)
            return
        rows_count = len(data)
        msg = 'Se encontraron {} productos a importar\n\n' \
            '¿Estás seguro de importarlos?'.format(rows_count)
        if util.question(msg) == BUTTON_CLICK['NO']:
            return
        if self.dm.chkCopiaDB3.State:
            self.db.backup()
        pb = self.dialog.getControl('pbImportar3')
        lbl = self.dialog.getControl('lblInfo3').Model
        pb.setRange(1, rows_count)
        for i,v in enumerate(data):
            r = i + 1
            lbl.Label = 'Importanto {} de {} productos'.format(r, rows_count)
            pb.setValue(r)
            self._import_product(v)
        lbl.Label = 'Importación terminada...'
        return

    def _import_product(self, data):
        if isinstance(data[1], float):
            clave = str(int(data[1]))
        else:
            clave = data[1].strip()
        w = "noIdentificacion='{}'".format(clave)
        product = self.db.select(('productos',), where=w)
        if product:
            product = product[0]
            new_data = {}
            if self.dm.chkActualizarPrecio.State:
                new_data['valorUnitario'] = \
                    self._cast('float({})'.format(data[4]), 0)
            exists = self._cast('float({})'.format(data[5]), 0)
            if self.dm.optActualizarExistencia.State:
                new_data['existencia'] = exists
            else:
                new_data['existencia'] = exists + product[6]
            self.db.update('productos', new_data, 'id={}'.format(product[0]))
            return
        product = {}
        product['id_categoria'] = self._cast('int({})'.format(data[0]), 0)
        product['noIdentificacion'] = clave
        product['descripcion'] = data[2].strip()
        product['unidad'] = data[3].strip()
        product['valorUnitario'] = self._cast('float({})'.format(data[4]), 0)
        product['existencia'] = self._cast('float({})'.format(data[5]), 0)
        product['inventario'] = self._cast('int({})'.format(data[6]), 0)
        product['codigobarras'] = data[7].strip()
        product['CuentaPredial'] = ''
        id_product = self.db.insertrow('productos', product)
        imp = data[8:]
        if imp:
            fields = ('id_producto', 'id_impuesto')
            values = []
            for i in imp:
                values.append((id_product, self._cast('int({})'.format(i), 0)))
            self.db.executemany('productosimpuestos', fields, tuple(values))
        return

    def _cast(self, value, default):
        try:
            return eval(value)
        except:
            return default
