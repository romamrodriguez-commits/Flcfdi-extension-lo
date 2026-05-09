# -*- coding: utf-8 -*-

from .listeners import listener
from facturalibre.db.detalle import DBDetalle
from facturalibre.modulos import util
from facturalibre.settings import (
    TITLE, VERSION, COLORS, ICONS, DEFAULT_PAYMENT_METHOD)


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.db = caller.db
        self.opciones = ()
        self.options = self._get_options()
        self.path_pem = ''
        self.regimenfiscal = ''
        self.enviar_correo = 0
        self.folios = None
        self.rfc_emisor = ''
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.getModel()
        self.new_server = True
        if self._validar_cfdi():
            self.db_detalle = DBDetalle()
            self.listener = listener(self)
            self.__config()
            self._config()
            self.listener.cfdi()
            while not self.dialog.execute():
                pass
            self.dialog.dispose()

    def _config(self):
        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdFormaPago.ImageURL = img_url.format(ICONS['PAY'])
        self.dm.cmdDetalleReceptor.ImageURL = \
            img_url.format(ICONS['CLIENT_INFO'])
        self.dm.cmdNuevoReceptor.ImageURL = img_url.format(ICONS['NEW_CLIENT'])
        self.dm.cmdMostrarFolios.ImageURL = img_url.format(ICONS['FOLIO'])
        self.dm.cmdSalir.ImageURL = img_url.format(ICONS['CLOSE'])
        self.dm.cmdMostrarCategorias.ImageURL = img_url.format(ICONS['DOWN'])
        self.dm.cmdMostrarProductos.ImageURL = img_url.format(ICONS['SHOW'])
        self.dm.cmdMostrarAlumnos.ImageURL = img_url.format(ICONS['SHOW'])
        self.dm.cmdAgregarProductos.ImageURL = img_url.format(ICONS['IMPORT'])
        self.dm.cmdNuevoProducto.ImageURL = img_url.format(ICONS['PRODUCT_ADD'])
        self.dm.cmdAgregarProducto.ImageURL = img_url.format(ICONS['PAY'])
        self.dm.cmdEliminarProducto.ImageURL = img_url.format(ICONS['PRODUCT_DELETE'])
        self.dm.cmdGenerarCfdi.ImageURL = img_url.format(ICONS['XML'])
        self.dm.cmdNotas.ImageURL = img_url.format(ICONS['NOTE'])
        self.dm.cmdCamposPersonalizados.ImageURL = img_url.format(ICONS['FIELDS'])
        self.dm.cmdRefacturar.ImageURL = img_url.format(ICONS['REINVOICE'])
        self.dm.cmdPrefacturar.ImageURL = img_url.format(ICONS['PREINVOICE'])
        self.dm.cmdCotizacion.ImageURL = img_url.format(ICONS['COTIZA'])
        self.dm.cmdRegimenFiscal.ImageURL = img_url.format(ICONS['REGIMEN'])
        self.dm.cmdArriba.ImageURL = img_url.format(ICONS['UP'])
        self.dm.cmdAbajo.ImageURL = img_url.format(ICONS['DOWN'])
        self.dm.cmd_complements.ImageURL = img_url.format(ICONS['SETTINGS'])

        self.dm.lblVersion.Label = 'Factura Libre v{}'.format(VERSION)
        self.dm.lblInfo.Label = ''
        self.unogui.setVisible(self.dialog, 'cmdFormaPago', False)
        if 'forma_pago' in self.options:
            if self.options['forma_pago']:
                self.unogui.setVisible(self.dialog, 'cmdFormaPago')
                self.dm.NumCtaPago.Width = 78
        self.dm.cmdGenerarCfdi.Enabled = True
        visible = self.options.get('use_complements', False)
        self.dialog.getControl('cmd_complements').setVisible(visible)
        return

    def _get_options(self):
        rows = self.db.select(('options',))
        data = {r[1]: r[2] for r in rows}
        return data

    def __config(self):
        nombre = self.db.select_field('emisor', 'nombre')
        if nombre:
            self.dialog.Title = '{} - Generar CFDI - {}'.format(TITLE, nombre)
        else:
            self.dialog.Title = '{} - Generar CFDI'.format(TITLE)
        message = ''
        properties = {}
        properties['Name'] = 'gridReceptores'
        properties['PositionX'] = 5
        properties['PositionY'] = 19
        properties['Width'] = 295
        properties['Height'] = 225
        properties['SelectionModel'] = 1
        columns = ({'Title': 'Clave', 'ColumnWidth': 35, 'HorizontalAlign': 1},
        {'Title': 'RFC', 'ColumnWidth': 55, 'HorizontalAlign': 0},
        {'Title': 'Razón Social', 'ColumnWidth': 185, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridReceptores').setVisible(False)

        properties = {}
        properties['Name'] = 'gridFolios'
        properties['PositionX'] = 300
        properties['PositionY'] = 40
        properties['Width'] = 135
        properties['Height'] = 50
        properties['SelectionModel'] = 1
        columns = (
            {'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
            {'Title': 'Serie', 'ColumnWidth': 30, 'HorizontalAlign': 1},
            {'Title': 'Inicio', 'ColumnWidth': 30, 'HorizontalAlign': 1},
            {'Title': 'Actual', 'ColumnWidth': 30, 'HorizontalAlign': 1},
            {'Title': 'Tipo', 'ColumnWidth': 25, 'HorizontalAlign': 1},
            {'Title': 'D', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        )
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridFolios').setVisible(False)

        self.unogui.gridAddRows(self.dm.gridFolios, self.folios)
        folio_actual = self.folios[0][3]
        if self.folios[0][2] > folio_actual:
            folio_actual = self.folios[0][2]
        if self.folios[0][1]:
            self.dm.lblFolio.Label = '%s-%s' % (self.folios[0][1], folio_actual)
        else:
            self.dm.lblFolio.Label = self.folios[0][3]
        if self.folios[0][4] == 'ingreso':
            self.dm.optEgreso.Enabled = False
            self.dm.optTraslado.Enabled = False
        elif self.folios[0][4] == 'egreso':
            self.dm.optEgreso.State = 1
            self.dm.optIngreso.Enabled = False
            self.dm.optTraslado.Enabled = False
        elif self.folios[0][4] == 'traslado':
            self.dm.optTraslado.State = 1
            self.dm.optIngreso.Enabled = False
            self.dm.optEgreso.Enabled = False
        if len(self.folios) == 1:
            self.dm.cmdMostrarFolios.Enabled = False

        self.dm.txtFecha.Date = self.util.setUtilDate()
        self.dm.lblFecha.Label = self.util.now().strftime('%a, %d-%b-%Y')
        self.dialog.getControl('lblDonativo').setVisible(bool(self.folios[0][5]))
        tipo = self.db.select_field('emisor', 'tipo')
        if tipo == 3:
            self.new_server = False
            #~ self.dialog.getControl('lblDonativo').setVisible(False)
        self.opciones = self.db.select(('opciones',),
            ('decimales', 'opcion1', 'opcion2', 'opcion3', 'opcion4',
                'opcion5', 'opcion6', 'opcion7'))[0]
        self.enviar_correo = self.db.select_field('opciones2', 'opcion5')

        if self.opciones[1]:
            self.dm.lblValorUnitario.Label = 'Valor Unitario con IVA'
            self.dm.lblValorUnitario.FontWeight = 150
        if not self.opciones[3]:
            controls = ('lblMoneda', 'moneda', 'TipoCambio')
            self.unogui.setVisible(self.dialog, controls, False)
        if self.opciones[4]:
            self.dialog.getControl('lblFecha').setVisible(False)
        else:
            self.dialog.getControl('txtFecha').setVisible(False)
        if self.opciones[5]:
            self.dm.valorUnitario.BackgroundColor = COLORS['WHITE']
            self.dm.valorUnitario.ReadOnly = False
        else:
            self.dm.valorUnitario.Border = 0
        mostrar = bool(self.db.select_field('opciones2', 'opcion3'))
        self.dialog.getControl('chkMostrarAduana').setVisible(mostrar)

        self.dm.cantidad.DecimalAccuracy = self.opciones[0]
        self.dm.valorUnitario.DecimalAccuracy = self.opciones[0]
        self.dm.importe.DecimalAccuracy = self.opciones[0]
        self.dm.TipoCambio.DecimalAccuracy = self.opciones[0]

        data = self.db.select_field('receptores','id')
        if not data:
            message = 'El catálogo de clientes esta vacío, puedes agregar ' \
                'clientes directamente desde el siguiente cuadro de diálogo \n\n'
            self.dm.txtReceptor.Enabled = False

        tree = self.dialog.getControl('treeCategorias')
        tree.setVisible(False)
        select = getattr(self.db, 'select')
        self.unogui.query_to_tree(tree, 'categorias', select)

        properties = {}
        properties['Name'] = 'gridProductos'
        properties['PositionX'] = 5
        properties['PositionY'] = 34
        properties['Width'] = 300
        properties['Height'] = 165
        properties['Step'] = 0
        properties['SelectionModel'] = 1
        columns=({'Title':'id','ColumnWidth':0,'HorizontalAlign':1},
        {'Title': 'Clave','ColumnWidth':40,'HorizontalAlign':1},
        {'Title': 'Descripción','ColumnWidth':140,'HorizontalAlign':0},
        {'Title': 'Unidad','ColumnWidth':30,'HorizontalAlign':1},
        {'Title': 'P.U.','ColumnWidth':30,'HorizontalAlign':2},
        {'Title': 'Existencia','ColumnWidth':30,'HorizontalAlign':2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridProductos').setVisible(False)

        data = self.db.select_field('productos', 'id')
        if not data:
            message = '%sEl catálogo de productos y servicios esta vacío, ' \
                'puedes agregarlos directamente desde el siguiente cuadro de ' \
                'diálogo' % message
            self.dm.descripcion.Enabled = False
            self.dm.txtCategoria.Enabled = False
            self.dm.cmdMostrarCategorias.Enabled = False

        if message:
            self.unogui.createMsgBox({'Message': message})

        controls = ('lblAduana', 'aduana', 'lblNumero', 'fecha', 'numero')
        self.unogui.setVisible(self.dialog, controls, False)

        data = self.db.select(('aduanas',),('aduana',))
        combo = self.dialog.getControl('aduana')
        self.unogui.query_to_listbox(data, combo)
        data = self.db.select(('monedas',),('moneda',))
        combo = self.dialog.getControl('moneda')
        self.unogui.query_to_listbox(data, combo)
        combo.selectItemPos(0, True)

        #~ data = self.db.select(('metodosdepago',),('metododepago',))
        data = self.db.select(('payment_methods',),('method',), order='method')
        lst = self.dialog.getControl('lst_payment_method')
        self.unogui.query_to_listbox(data, lst)

        data = self.db.select(('condicionesdepago',),('condiciondepago',))
        combo = self.dialog.getControl('condicionesDePago')
        self.unogui.query_to_listbox(data, combo)

        properties = {}
        properties['Name'] = 'gridDetalle'
        properties['PositionX'] = 6
        properties['PositionY'] = 90
        properties['Width'] = 414
        properties['Height'] = 110
        properties['SelectionModel'] = 1
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
        {'Title': 'Clave', 'ColumnWidth': 40, 'HorizontalAlign': 0},
        {'Title': 'Unidad', 'ColumnWidth': 36, 'HorizontalAlign': 0},
        {'Title': 'Descripción', 'ColumnWidth': 170, 'HorizontalAlign': 0},
        {'Title': 'Cantidad', 'ColumnWidth': 33, 'HorizontalAlign': 2},
        {'Title': 'Valor Unitario', 'ColumnWidth': 44, 'HorizontalAlign': 2},
        {'Title': 'Importe', 'ColumnWidth': 56, 'HorizontalAlign': 2},
        {'Title': 'ROWID', 'ColumnWidth': 0, 'HorizontalAlign': 1})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)

        properties = {}
        properties['Name'] = 'gridTotales'
        properties['PositionX'] = 8
        properties['PositionY'] = 218
        properties['Width'] = 375
        properties['Height'] = 25
        properties['SelectionModel'] = 0
        properties['ShowRowHeader'] = False
        columns = ({'Title': 'SubTotal', 'ColumnWidth': 60, 'HorizontalAlign': 2},
        {'Title': 'Impuestos', 'ColumnWidth': 60, 'HorizontalAlign': 2},
        {'Title': 'TOTAL', 'ColumnWidth': 60, 'HorizontalAlign': 2})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)

        properties = {}
        properties['Name'] = 'gridCampos'
        properties['PositionX'] = 6
        properties['PositionY'] = 86
        properties['Width'] = 164
        properties['Height'] = 142
        properties['SelectionModel'] = 1
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Campo', 'ColumnWidth': 50, 'HorizontalAlign': 2},
        {'Title': 'Valor', 'ColumnWidth': 95, 'HorizontalAlign': 0},
        {'Title': 'Nodo', 'ColumnWidth': 0, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridCampos').setVisible(False)
        data = self.db.select(('campospersonalizados',),('campo', 'nodo'))
        if data:
            rows = []
            for row in data:
                rows.append(('', row[0], '', row[1]))
            self.unogui.gridAddRows(oGrid, rows)
        else:
            self.dialog.getControl('cmdCamposPersonalizados').setVisible(False)

        data = self.db.select(('regimenesfiscales',),('Regimen',))
        listbox = self.dialog.getControl('lstRegimenes')
        if data:
            self.unogui.query_to_listbox(data, listbox)
        if len(data) == 1:
            self.dialog.getControl('cmdRegimenFiscal').setVisible(False)
            self.regimenfiscal = listbox.getItem(0)
        self.dialog.getControl('lstRegimenes').setVisible(False)

        self.dm.cmdEliminarProducto.Enabled = False
        self.dm.cmdAgregarProducto.Enabled = False

        pem = self.util.getPathTemp()
        data = self.db.select_field('certificado', 'pem')
        self.util.save_file(pem, data)
        self.path_pem = pem

        visible = bool(self.db.select_field('emisor', 'escuela'))
        controls = ('lblAlumno', 'lblMes', 'lblFecha2', 'cmdMostrarAlumnos',
            'txtAlumno', 'lstMes', 'fecha2')
        for name in controls:
            self.dialog.getControl(name).setVisible(visible)
        if visible:
            visible = False
            controls = ('lblAduana', 'lblNumero', 'lblMoneda',
                'chkMostrarAduana', 'aduana', 'fecha', 'numero',
                'moneda', 'TipoCambio')
            for name in controls:
                self.dialog.getControl(name).setVisible(visible)

        properties = {}
        properties['Name'] = 'gridAlumnos'
        properties['PositionX'] = 6
        properties['PositionY'] = 87
        properties['Width'] = 375
        properties['Height'] = 155
        properties['SelectionModel'] = 1
        columns = (
            {'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
            {'Title': 'Alumno', 'ColumnWidth': 125, 'HorizontalAlign': 0},
            {'Title': 'CURP', 'ColumnWidth': 75, 'HorizontalAlign': 0},
            {'Title': 'Nivel', 'ColumnWidth': 50, 'HorizontalAlign': 0},
            {'Title': 'autorizacion', 'ColumnWidth': 0, 'HorizontalAlign': 0},
            {'Title': 'id_cliente', 'ColumnWidth': 0, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridAlumnos').setVisible(False)
        self.dm.gridAlumnos.RowHeaderWidth = 15
        self.dialog.getControl('lstMes').selectItemPos(self.util.today().month, True)

        self.unogui.centerDialog(self.dialog)
        self.dialog.getControl('txtReceptor').setFocus()

        return

    def _validar_cfdi(self):
        data = self.db.select_field('certificado', 'SUBSTR(final,1,10)')
        if not data:
            message = 'Aun no configuras los datos de tu certificado de ' \
                'sellos para facturar, es necesario realizar este paso primero.'
            self.unogui.createMsgBox({'Message': message})
            return False
        dias = self.util.get_date_from_string(data) - self.util.now()
        if dias.days < 1:
            message = 'Tu certificado de sellos a caducado, solicita otro ' \
                'ante el SAT y vuelve a cargarlo en el sismtea. No podras ' \
                'facturar hasta tener un certificado vigente'
            self.unogui.createMsgBox({'Message': message})
            return False
        if dias.days < 31:
            message = 'La vigencia de este certificado esta por terminar en ' \
                '%s días.\n\nSe recomienda solicitar un nuevo certificado en ' \
                'el SAT' % dias.days
            self.unogui.createMsgBox({'Message': message})

        data = self.db.select_field('folios', 'id')
        if not data:
            message = 'Aun no configuras los datos de los folios para ' \
                'facturar, es necesario realizar este paso primero.'
            self.unogui.createMsgBox({'Message': message})
            return False
        data = self.db.select_field('emisor', 'id')
        if not data:
            message = 'Aun no configuras los datos del emisor, es necesario ' \
            'realizar este paso primero.'
            self.unogui.createMsgBox({'Message': message})
            return False
        data = self.db.select_field('impuestos', 'id')
        if not data:
            message = 'No tienes impuestos datos de alta, es necesario tener ' \
            'al menos uno para poder facturar.'
            self.unogui.createMsgBox({'Message': message})
            return False
        limite_folios = self.db.select_field('opciones', 'minfolios')
        where = 'version="3.2" and uuid="" and estatus<>"Validada"'
        #~ data = self.db.select(('cfdfacturas',), ('id',), 'uuid="" AND version>1.1')
        data = self.db.select(('cfdfacturas',), ('id',), where)
        if data:
            message = 'Tienes facturas SIN TIMBRAR, se recomienda ' \
                'imperativamente NO CONTINUAR hasta verificar estas ' \
                'facturas, puedes ver su estatus en el Administrador de ' \
                'facturas.\n\n¿Deseas salir para verificar?'
            if self.unogui.createQuestion('Factura Libre', message):
                return False

        conexion = True
        if not self.util.hay_conexion():
            message = 'Parece que no tienes conexión a Internet, puedes ' \
                'generar CFDI, pero no se podrán timbrar hasta volver a ' \
                'tener conexión a internet, se recomienda esperar hasta ' \
                'resolver este problema'
            self.unogui.createMsgBox({'Message': message})
            conexion = False

        max_folio = 'CASE WHEN (select ifnull(max(folio)+1,1) from ' \
            'cfdfacturas where serie=folios.serie)=1 THEN inicio ELSE ' \
            '(select ifnull(max(folio)+1,1) from cfdfacturas where serie=folios.serie) END'
        folios = self.db.select(
            ('folios', 'tiposcfdi'),
            ('folios.id', 'serie', 'inicio', max_folio, 'tiposcfdi.tipo', 'donativo'),
            'folios.usarcon=tiposcfdi.id',
            'predeterminado DESC')
        if not folios:
            message = 'No tienes folios disponibles para facturar'
            self.unogui.createMsgBox({'Message': message})
            return False
        self.folios = folios
        self.rfc_emisor = self.db.select_field('certificado', 'rfc')
        if conexion:
            self.dm.lblFoliosPac.Label = 'Consultando...'
            new_server = self.db.select_field('emisor', 'tipo')
            if new_server == 3:
                new_server = False
            else:
                new_server = True
            #~ t = util.GetTimbres(self.rfc_emisor, self.dm.lblFoliosPac, new_server)
            #~ t.start()
            ok, timbres = util.get_timbres(self.rfc_emisor, new_server, not new_server)
            self.dm.lblFoliosPac.Label = 'Folios PAC: {}'.format(timbres)

        return True

