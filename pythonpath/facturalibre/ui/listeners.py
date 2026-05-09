# -*- coding: utf-8 -*-
from com.sun.star.awt import XItemListener
from com.sun.star.awt import XTextListener
from com.sun.star.awt.grid import XGridSelectionListener
from com.sun.star.view import XSelectionChangeListener
from facturalibre.controllers.configuracion import EventosConfiguracion
from facturalibre.controllers.tools import EventosTools
from facturalibre.controllers.clientes import EventosClientes
from facturalibre.controllers.cfdi import EventosCfdi
from facturalibre.controllers.admincfdi import EventosAdminCfdi
from facturalibre.controllers.reportes import EventosReportes
from facturalibre.controllers.repclitot import EventosRepCliTot
from facturalibre.controllers.repprod import EventosRepProd
from facturalibre.controllers.reportep import EventosReporteP
from facturalibre.controllers.repprotot import EventosRepProTot
from facturalibre.controllers.repprop import EventosRepProP
from facturalibre.controllers.admincompras import EventosAdminCompras
from facturalibre.controllers.importXML import EventosImportXML
from facturalibre.controllers.adminnomina import EventosAdminNomina

import unohelper
from com.sun.star.awt import XActionListener
from com.sun.star.awt import XFocusListener
from com.sun.star.awt import XKeyListener
from com.sun.star.awt import XMouseListener

from facturalibre.settings import COLORS
from facturalibre.controllers.niveles import NivelesEvents
from facturalibre.controllers.empleados import EmpleadosEvents
from facturalibre.controllers.input_box import InputBoxEvents
from facturalibre.controllers.productosadmin import ProductosAdminEvents
from facturalibre.controllers.producto import ProductoEvents
from facturalibre.controllers.complements import ComplementsEvents


class Listener(object):

    def __init__(self, dialog, db=None):
        self.dialog = dialog
        self.db = db

    def _add_listeners(self, listeners):
        for k, v in listeners.items():
            for control_name in v['controls']:
                control = self.dialog.getControl(control_name)
                getattr(control, k)(v['class'])

    def complements(self, caller):
        events = ComplementsEvents(self.dialog, caller)
        buttons = ('cmd_save', 'cmd_close',)
        trees = ('tree_complement',)
        texts = ('attribute_value',)
        grids = ('grid',)
        listbox = ('lst_values',)
        listeners = {
            'addActionListener': {
                'class': ButtonEvents(events), 'controls': buttons},
            'addSelectionChangeListener': {
                'class': TreeSelectionChangeEvents(events), 'controls': trees},
            'addFocusListener': {
                'class': FocusEvents(events), 'controls': texts},
            'addTextListener': {
                'class': TextEvents(events), 'controls': texts},
            'addSelectionListener': {
                'class': GridSelectionEvents(events), 'controls': grids},
            'addItemListener': {
                'class': ItemEvents(events), 'controls': listbox},
            'addMouseListener': {
                'class': MouseEvents(events), 'controls': grids},
        }
        self._add_listeners(listeners)
        return

    def producto(self, edit, id_producto):
        events = ProductoEvents(self.dialog, self.db, edit, id_producto)
        buttons = (
            'cmdSalir',
            'chkAutomatica',
            'chkInventario',
            'chkCuentaPredial',
            'cmdMostrarCategorias',
            'cmdAgregarCategoria',
            'cmdGuardar',
            'cmdLimpiarSeleccion',
        )
        texts = (
            'noIdentificacion',
            'categoria',
            'descripcion',
            'unidad',
            'valorUnitario',
            'cantidad',
            'total',
            'existencia',
            'codigobarras',
            'CuentaPredial',
        )
        trees = ('treeCategorias',)
        listeners = {
            'addActionListener': {
                'class': ButtonEvents(events), 'controls': buttons},
            'addFocusListener': {
                'class': FocusEvents(events), 'controls': texts},
            'addKeyListener': {
                'class': KeyEvents(events), 'controls': texts},
            'addMouseListener': {
                'class': MouseEvents(events), 'controls': trees},
        }
        self._add_listeners(listeners)
        return

    def productosadmin(self):
        events = ProductosAdminEvents(self.dialog, self.db)
        buttons = (
            'cmdNuevoProducto',
            'cmdEditarProducto',
            'cmdEliminarProducto',
            'cmdMostrarTodo',
            'cmdReporte',
            'cmdFiltrar1',
            'cmdSalir',
        )
        texts = ('txtFiltrarProducto',)
        grids = ('gridProductos',)
        listeners = {
            'addActionListener': {
                'class': ButtonEvents(events), 'controls': buttons},
            'addFocusListener': {
                'class': FocusEvents(events), 'controls': texts},
            'addKeyListener': {
                'class': KeyEvents(events), 'controls': texts},
            'addMouseListener': {
                'class': MouseEvents(events), 'controls': grids},
        }
        self._add_listeners(listeners)
        return

    def niveles(self):
        events = NivelesEvents(self.dialog, self.db)
        buttons = ('cmdAgregar', 'cmdEliminar')
        texts = ('txtNivel', 'txtAutorizacion')
        listeners = {
            'addActionListener': {
                'class': ButtonEvents(events), 'controls': buttons},
            'addFocusListener': {
                'class': FocusEvents(events), 'controls': texts},
        }
        self._add_listeners(listeners)
        return

    def empleados(self):
        events = EmpleadosEvents(self.dialog, self.db)
        buttons = (
            'new_employer',
            'edit_employer',
            'delete_employer',
            'show_all',
            'make_report',
            'close',
        )
        texts = ('filter_employers',)
        grids = ('grid_employers',)
        listeners = {
            'addActionListener': {
                'class': ButtonEvents(events), 'controls': buttons},
            'addFocusListener': {
                'class': FocusEvents(events), 'controls': texts},
            'addKeyListener': {
                'class': KeyEvents(events), 'controls': texts},
            'addMouseListener': {
                'class': MouseEvents(events), 'controls': grids},
        }
        self._add_listeners(listeners)
        return

    def input_box(self, caller):
        events = InputBoxEvents(self.dialog, caller)
        buttons = (
            'ok',
            'cancel',
        )
        texts = ('value',)
        listeners = {
            'addActionListener': {
                'class': ButtonEvents(events), 'controls': buttons},
            'addFocusListener': {
                'class': FocusEvents(events), 'controls': texts},
        }
        self._add_listeners(listeners)
        return


class ButtonEvents(unohelper.Base, XActionListener):

    def __init__(self, events):
        self.events = events

    def disposing(self, event):
        pass

    def actionPerformed(self, event):
        getattr(self.events, event.Source.Model.Name)(event)
        return


class FocusEvents(unohelper.Base, XFocusListener):

    def __init__(self, events):
        self.events = events

    def disposing(self, event):
        pass

    def focusGained(self, event):
        obj = event.Source.Model
        obj.Border = 0
        obj.BackgroundColor = COLORS['YELLOW']
        control_name = '{}_focus_gained'.format(obj.Name)
        getattr(self.events, control_name)(event)
        return

    def focusLost(self, event):
        obj = event.Source.Model
        obj.Border = 1
        obj.BackgroundColor = COLORS['WHITE']
        control_name = '{}_focus_lost'.format(obj.Name)
        getattr(self.events, control_name)(event)


class KeyEvents(unohelper.Base, XKeyListener):

    def __init__(self, events):
        self.events = events

    def disposing(self, event):
        pass

    def keyPressed(self, event):
        control_name = '{}_key_pressed'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)

    def keyReleased(self, event):
        control_name = '{}_key_released'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)


class MouseEvents(unohelper.Base, XMouseListener):

    def __init__(self, events):
        self.events = events

    def disposing(self, event):
        pass

    def mousePressed(self, event):
        control_name = '{}_mouse_pressed'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)
        return

    def mouseReleased(self, event):
        pass

    def mouseEntered(self, event):
        pass

    def mouseExited(self, event):
        pass


class TreeSelectionChangeEvents(unohelper.Base, XSelectionChangeListener):

    def __init__(self, events):
        self.events = events

    def selectionChanged(self, event):
        control_name = '{}_selection_changed'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)
        return


class TextEvents(unohelper.Base, XTextListener):

    def __init__(self, events):
        self.events = events

    def disposing(self, event):
        pass

    def textChanged(self, event):
        control_name = '{}_text_changed'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)
        return


class GridSelectionEvents(unohelper.Base, XGridSelectionListener):

    def __init__(self, events):
        self.events = events

    def selectionChanged(self, event):
        control_name = '{}_selection_changed'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)
        return


class ItemEvents(unohelper.Base, XItemListener):

    def __init__(self, events):
        self.events = events

    def disposing(self, eventObject):
        pass

    def itemStateChanged(self, event):
        control_name = '{}_selection_changed'.format(event.Source.Model.Name)
        getattr(self.events, control_name)(event)
        return


class listener(object):

    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog

    def __addItemListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addItemListener(the_listener)
        return

    def __addActionListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addActionListener(the_listener)
        return

    def __addFocusListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addFocusListener(the_listener)
        return

    def __addMouseListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addMouseListener(the_listener)
        return

    def __addKeyListener(self, control_name, the_listener):
        if control_name == 'dialog':
            self.dialog.addKeyListener(the_listener)
        else:
            control = self.dialog.getControl(control_name)
            control.addKeyListener(the_listener)
        return

    def __addTextListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addTextListener(the_listener)
        return

    def __addSelectionListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addSelectionListener(the_listener)
        return

    def __addSelectionChangeListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addSelectionChangeListener(the_listener)
        return

    def configuracion(self):
        eventos = EventosConfiguracion(self.caller)

        control = self.dialog.getControl('rmMapa')
        the_listener = RoadMapMessageListener(self.caller, eventos)
        control.addItemListener(the_listener)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        # Certificado
        self.__addActionListener('cmdVerificar', the_listener)
        self.__addActionListener('cmdVerificarSat', the_listener)
        self.__addActionListener('cmdGuardarCertificado', the_listener)
        self.__addActionListener('cmdCerTest', the_listener)
        # Folios
        self.__addActionListener('cmdAgregarFolios', the_listener)
        self.__addActionListener('cmdPredeterminar', the_listener)
        self.__addActionListener('cmdEliminarFolios', the_listener)
        # Emisor
        self.__addActionListener('cmdGuardarEmisor', the_listener)
        self.__addActionListener('cmdAgregarRegimen', the_listener)
        self.__addActionListener('cmdEliminarRegimen', the_listener)
        self.__addActionListener('cmdNiveles', the_listener)
        # Expedido
        self.__addActionListener('cmdGuardarExpedido', the_listener)
        self.__addActionListener('cmdLimpiarExpedido', the_listener)
        # Catalogos CFDI
        self.__addActionListener('cmdAgregarCondicionPago', the_listener)
        self.__addActionListener('cmdAgregarMetodoPago', the_listener)
        self.__addActionListener('cmdAgregarAduana', the_listener)
        self.__addActionListener('cmdGuardarCatalogosCfdi', the_listener)
        self.__addActionListener('cmdAgregarMoneda', the_listener)
        self.__addActionListener('cmdEliminarMoneda', the_listener)
        self.__addActionListener('cmdEliminarCondicionPago', the_listener)
        self.__addActionListener('cmdEliminarMetodoPago', the_listener)
        self.__addActionListener('cmdEliminarAduana', the_listener)
        # Catalogos Productos
        self.__addActionListener('cmdAgregarImpuesto', the_listener)
        self.__addActionListener('cmdEliminarImpuesto', the_listener)
        self.__addActionListener('cmdAgregarCategoria', the_listener)
        self.__addActionListener('cmdEliminarCategoria', the_listener)
        self.__addActionListener('cmdAgregarUnidad', the_listener)
        self.__addActionListener('cmdEliminarUnidad', the_listener)
        self.__addActionListener('cmdGuardarCatalogosProductos', the_listener)

        self.__addActionListener('cmdAgregarPersonalizado', the_listener)
        self.__addActionListener('cmdGuardarCamposPersonalizados', the_listener)
        self.__addActionListener('cmdCargarAddenda', the_listener)
        self.__addActionListener('cmdEliminarPersonalizado', the_listener)

        self.__addActionListener('cmdSeleccionarImpuesto', the_listener)
        self.__addActionListener('cmdAgregarDirectorio', the_listener)
        self.__addActionListener('cmdEliminarDirectorio', the_listener)
        self.__addActionListener('cmdProbarFtp', the_listener)
        self.__addActionListener('cmdGuardarOpciones', the_listener)

        self.__addActionListener('cmdCorreoProbar', the_listener)
        self.__addActionListener('cmdGuardarCorreo', the_listener)
        self.__addActionListener('cmdBorrarDatosCorreo', the_listener)

        self.__addActionListener('cmdAgregarRuta', the_listener)
        self.__addActionListener('cmdEliminarRuta', the_listener)
        self.__addActionListener('cmdGuardarRutas', the_listener)

        self.__addActionListener('cmdAgregarAddenda', the_listener)
        self.__addActionListener('cmdEliminarAddenda', the_listener)
        self.__addActionListener('cmdEditarAddenda', the_listener)
        self.__addActionListener('cmdAsignarCampos', the_listener)

        self.__addActionListener('cmdProbarSql', the_listener)
        self.__addActionListener('cmdAgregarReporte', the_listener)
        self.__addActionListener('cmdEliminarReporte', the_listener)

        the_listener = FocusListener(self.caller)
        # Folios
        self.__addFocusListener('txtContrasena',the_listener)
        self.__addFocusListener('txtSerie',the_listener)
        #self.__addFocusListener('txtAno',the_listener)
        #self.__addFocusListener('txtAprobacion',the_listener)
        self.__addFocusListener('txtInicio',the_listener)
        #self.__addFocusListener('txtFin',the_listener)
        # Emisor
        self.__addFocusListener('txtRfc',the_listener)
        self.__addFocusListener('txtNombre',the_listener)
        self.__addFocusListener('txtCalle',the_listener)
        self.__addFocusListener('txtNumExt',the_listener)
        self.__addFocusListener('txtNumInt',the_listener)
        self.__addFocusListener('txtColonia',the_listener)
        self.__addFocusListener('txtMunicipio',the_listener)
        self.__addFocusListener('txtCodigoPostal',the_listener)
        self.__addFocusListener('txtTelefono',the_listener)
        self.__addFocusListener('txtCorreo',the_listener)
        self.__addFocusListener('txtAutorizacionOng',the_listener)
        self.__addFocusListener('txtFechaOng',the_listener)
        self.__addFocusListener('txtRegimen',the_listener)

        # Expedido
        self.__addFocusListener('txtCalle2', the_listener)
        self.__addFocusListener('txtNumExt2', the_listener)
        self.__addFocusListener('txtNumInt2', the_listener)
        self.__addFocusListener('txtColonia2', the_listener)
        self.__addFocusListener('txtMunicipio2', the_listener)
        self.__addFocusListener('txtCodigoPostal2', the_listener)
        self.__addFocusListener('txtTelefono2', the_listener)

        self.__addFocusListener('txtCondicionPago',the_listener)
        self.__addFocusListener('txtMetodoPago',the_listener)
        self.__addFocusListener('txtAduana',the_listener)
        self.__addFocusListener('txtMoneda',the_listener)
        self.__addFocusListener('txtPrefijo',the_listener)
        self.__addFocusListener('txtSufijo',the_listener)
        self.__addFocusListener('txtTasa',the_listener)
        self.__addFocusListener('txtCategoria',the_listener)
        self.__addFocusListener('txtUnidad',the_listener)
        # Personalizados
        self.__addFocusListener('txtPersonalizado', the_listener)
        self.__addFocusListener('txtCelda1', the_listener)
        self.__addFocusListener('txtCelda2', the_listener)
        self.__addFocusListener('txtNodo', the_listener)
        self.__addFocusListener('txtAtributo1', the_listener)
        self.__addFocusListener('txtAtributo2', the_listener)

        # Opciones
        self.__addFocusListener('txtImpuestoPre',the_listener)
        self.__addFocusListener('txtDecimales',the_listener)
        self.__addFocusListener('txtMinFolios',the_listener)
        self.__addFocusListener('txtFtpServidor',the_listener)
        self.__addFocusListener('txtFtpUsuario',the_listener)
        self.__addFocusListener('txtFtpContrasena',the_listener)

        self.__addFocusListener('txtCorreoServidor',the_listener)
        self.__addFocusListener('txtCorreoPuerto',the_listener)
        self.__addFocusListener('txtCorreoUsuario',the_listener)
        self.__addFocusListener('txtCorreoContrasena',the_listener)
        self.__addFocusListener('txtCorreoCopia',the_listener)
        self.__addFocusListener('txtCorreoAsunto',the_listener)
        self.__addFocusListener('txtCorreoCuerpo',the_listener)

        self.__addFocusListener('txtAddendaRuta', the_listener)
        self.__addFocusListener('txtAddendaNombre', the_listener)

        self.__addFocusListener('txtNombreReporte', the_listener)
        self.__addFocusListener('txtSqlReporte', the_listener)

        the_listener = OptionButtonListener(self.caller, eventos)
        self.__addActionListener('optFisica', the_listener)
        self.__addActionListener('optMoral', the_listener)
        self.__addActionListener('optOng', the_listener)
        self.__addActionListener('optCorreo0', the_listener)
        self.__addActionListener('optCorreo1', the_listener)
        self.__addActionListener('optCorreo2', the_listener)
        self.__addActionListener('optCorreo3', the_listener)

        the_listener = MouseListener(self.caller, eventos)
        self.__addMouseListener('lstRegimen', the_listener)
        self.__addMouseListener('lstCondicionPago', the_listener)
        self.__addMouseListener('lstMetodoPago', the_listener)
        self.__addMouseListener('lstAduana', the_listener)
        self.__addMouseListener('lstUnidad', the_listener)
        #self.__addMouseListener('lstPersonalizado', the_listener)
        self.__addMouseListener('lstRutasEspejo', the_listener)
        #~ self.__addMouseListener('lstRutasTrabajo', the_listener)
        self.__addMouseListener('gridMonedas', the_listener)
        self.__addMouseListener('gridPersonalizados', the_listener)
        #~ self.__addMouseListener('gridCeldas', the_listener)

        the_listener = GridSelectionListener(self.caller,eventos)
        self.__addSelectionListener('gridMonedas',the_listener)
        self.__addSelectionListener('gridImpuestos',the_listener)
        self.__addSelectionListener('gridImpuestos2',the_listener)
        self.__addSelectionListener('gridColonias', the_listener)

        the_listener = TreeSelectionChangeListener(self.caller,eventos)
        self.__addSelectionChangeListener('treeCategorias',the_listener)

        the_listener = ItemListener(self.caller, eventos)
        self.__addItemListener('lstReportes', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtCodigoPostal', the_listener)
        #~ the_listener = GridSelectionListener(self.caller,eventos)
        #~ self.__addSelectionListener('gridColonias', the_listener)
        the_listener = GridFocusListener(self.caller)
        self.__addFocusListener('gridColonias', the_listener)

        the_listener = CheckBoxListener(self.caller, eventos)
        self.__addActionListener('chkEscuela', the_listener)
        return None

    def clientes(self):
        eventos = EventosClientes(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdNuevoCliente', the_listener)
        self.__addActionListener('cmdEditarCliente', the_listener)
        self.__addActionListener('cmdEliminarCliente', the_listener)
        self.__addActionListener('cmdMostrarTodo', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdReporte', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtFiltrarCliente', the_listener)
        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtFiltrarCliente', the_listener)

        the_listener = MouseListener(self.caller, eventos)
        self.__addMouseListener('gridReceptores', the_listener)
        return None

    def productosadmin(self):
        eventos = EventosProductos(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdNuevoProducto', the_listener)
        self.__addActionListener('cmdEditarProducto', the_listener)
        self.__addActionListener('cmdEliminarProducto', the_listener)
        self.__addActionListener('cmdMostrarTodo', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdReporte', the_listener)
        self.__addActionListener('cmdFiltrar1', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtFiltrarProducto', the_listener)
        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtFiltrarProducto', the_listener)

        the_listener = MouseListener(self.caller, eventos)
        self.__addMouseListener('gridProductos', the_listener)

        return None

    def cfdi(self):
        eventos = EventosCfdi(self.caller)
        eventos.regimenfiscal = self.caller.regimenfiscal

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir',the_listener)
        self.__addActionListener('cmdDetalleReceptor',the_listener)
        self.__addActionListener('cmdNuevoReceptor',the_listener)
        self.__addActionListener('cmdMostrarFolios',the_listener)
        self.__addActionListener('cmdMostrarCategorias',the_listener)
        self.__addActionListener('cmdNuevoProducto',the_listener)
        self.__addActionListener('cmdMostrarProductos',the_listener)
        self.__addActionListener('cmdAgregarProducto',the_listener)
        self.__addActionListener('cmdAgregarProductos',the_listener)
        self.__addActionListener('cmdEliminarProducto',the_listener)
        self.__addActionListener('cmdGenerarCfdi',the_listener)
        self.__addActionListener('cmdPrefacturar',the_listener)
        self.__addActionListener('cmdRefacturar',the_listener)
        self.__addActionListener('cmdNotas',the_listener)
        self.__addActionListener('cmdCamposPersonalizados',the_listener)
        self.__addActionListener('cmdRegimenFiscal',the_listener)
        self.__addActionListener('cmdCotizacion',the_listener)
        self.__addActionListener('cmdArriba',the_listener)
        self.__addActionListener('cmdAbajo',the_listener)
        self.__addActionListener('cmdMostrarAlumnos', the_listener)
        self.__addActionListener('cmdFormaPago', the_listener)
        self.__addActionListener('cmd_complements', the_listener)

        the_listener = FocusListener(self.caller, eventos)
        self.__addFocusListener('txtReceptor', the_listener)
        self.__addFocusListener('txtCategoria', the_listener)
        self.__addFocusListener('descripcion', the_listener)
        self.__addFocusListener('cantidad', the_listener)
        self.__addFocusListener('aduana', the_listener)
        self.__addFocusListener('fecha', the_listener)
        self.__addFocusListener('numero', the_listener)
        self.__addFocusListener('TipoCambio', the_listener)
        #~ self.__addFocusListener('metodoDePago', the_listener)
        self.__addFocusListener('condicionesDePago', the_listener)
        self.__addFocusListener('motivoDescuento', the_listener)
        self.__addFocusListener('descuento', the_listener)
        self.__addFocusListener('NumCtaPago', the_listener)
        self.__addFocusListener('txtAlumno', the_listener)
        self.__addFocusListener('fecha2', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtReceptor', the_listener)
        self.__addKeyListener('descripcion', the_listener)
        self.__addKeyListener('dialog', the_listener)
        self.__addKeyListener('treeCategorias', the_listener)
        self.__addKeyListener('txtAlumno', the_listener)

        the_listener = TextListener(self.caller, eventos)
        self.__addTextListener('cantidad', the_listener)
        self.__addTextListener('valorUnitario', the_listener)
        self.__addTextListener('descuento', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridReceptores', the_listener)
        self.__addSelectionListener('gridFolios', the_listener)
        self.__addSelectionListener('gridProductos', the_listener)
        self.__addSelectionListener('gridAlumnos', the_listener)

        the_listener = GridFocusListener(self.caller, eventos)
        self.__addFocusListener('gridReceptores', the_listener)
        self.__addFocusListener('gridFolios', the_listener)
        self.__addFocusListener('gridProductos', the_listener)
        self.__addFocusListener('gridAlumnos', the_listener)
        self.__addFocusListener('treeCategorias', the_listener)

        the_listener = MouseListener(self.caller,eventos)
        self.__addMouseListener('treeCategorias', the_listener)
        self.__addMouseListener('gridCampos', the_listener)
        self.__addMouseListener('gridDetalle', the_listener)
        self.__addMouseListener('lstRegimenes', the_listener)

        the_listener = CheckBoxListener(self.caller,eventos)
        self.__addActionListener('chkMostrarAduana',the_listener)
        self.__addActionListener('chkDescuento',the_listener)
        return None

    def admincfdi(self):
        eventos = EventosAdminCfdi(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdFiltrar1', the_listener)
        self.__addActionListener('cmdFiltrar2', the_listener)
        self.__addActionListener('cmdFiltrar3', the_listener)
        self.__addActionListener('cmdPdf', the_listener)
        self.__addActionListener('cmdXml', the_listener)
        self.__addActionListener('cmdLimpiarSeleccion', the_listener)
        self.__addActionListener('cmdSeleccionarTodo', the_listener)
        self.__addActionListener('cmdPagada', the_listener)
        self.__addActionListener('cmdCancelada', the_listener)
        self.__addActionListener('cmdSat', the_listener)
        self.__addActionListener('cmdReporte', the_listener)
        self.__addActionListener('cmdCorreo', the_listener)
        self.__addActionListener('cmdNotas', the_listener)
        self.__addActionListener('cmdCamposPersonalizados', the_listener)
        self.__addActionListener('cmdReportes', the_listener)
        self.__addActionListener('cmdAddenda', the_listener)
        self.__addActionListener('cmdEnviar', the_listener)
        self.__addActionListener('cmdImprimir', the_listener)
        self.__addActionListener('cmdSinTimbrar', the_listener)
        self.__addActionListener('cmdRefacturar', the_listener)
        self.__addActionListener('cmdTimbrar', the_listener)
        self.__addActionListener('cmdEliminar', the_listener)
        self.__addActionListener('cmdPorPagar', the_listener)
        self.__addActionListener('cmdValidar', the_listener)

        the_listener = FocusListener(self.caller, eventos)
        self.__addFocusListener('txtReceptor', the_listener)
        self.__addFocusListener('txtCfd', the_listener)
        self.__addFocusListener('txtFolio1', the_listener)
        self.__addFocusListener('txtFolio2', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtReceptor', the_listener)
        self.__addKeyListener('txtCfd', the_listener)

        the_listener = CheckBoxListener(self.caller, eventos)
        self.__addActionListener('chkDetalle', the_listener)
        self.__addActionListener('chkGuardar', the_listener)
        self.__addActionListener('chkEditar', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridReceptores', the_listener)
        self.__addSelectionListener('gridFacturas', the_listener)

        the_listener = ItemListener(self.caller, eventos)
        self.__addItemListener('lstAno', the_listener)
        self.__addItemListener('lstMes', the_listener)
        self.__addItemListener('lstEstatus', the_listener)
        return

    def tools(self):
        eventos = EventosTools(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdSeleccionarDirectorio', the_listener)
        self.__addActionListener('cmdImportarDatos', the_listener)
        self.__addActionListener('cmdActualizarDatos', the_listener)
        self.__addActionListener('cmdImportarProductos', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtDirectorio', the_listener)

        control = self.dialog.getControl('rmMapa')
        the_listener = RoadMapMessageListenerTools(self.caller, eventos)
        control.addItemListener(the_listener)
        return

    def reportes(self):
        eventos = EventosReportes(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGenerar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return

    def repclitot(self):
        eventos = EventosRepCliTot(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGenerar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return

    def repprod(self):
        eventos = EventosRepProd(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGenerar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return

    def reportep(self):
        eventos = EventosReporteP(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGenerar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return

    def repprotot(self):
        eventos = EventosRepProTot(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGenerar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return

    def repprop(self):
        eventos = EventosRepProP(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGenerar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return

    def admincompras(self):
        eventos = EventosAdminCompras(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdFiltrar1', the_listener)
        self.__addActionListener('cmdFiltrar2', the_listener)
        self.__addActionListener('cmdFiltrar3', the_listener)
        self.__addActionListener('cmdPdf', the_listener)
        self.__addActionListener('cmdXml', the_listener)
        self.__addActionListener('cmdLimpiarSeleccion', the_listener)
        self.__addActionListener('cmdSeleccionarTodo', the_listener)
        self.__addActionListener('cmdPagada', the_listener)
        self.__addActionListener('cmdCancelada', the_listener)
        self.__addActionListener('cmdSat', the_listener)
        self.__addActionListener('cmdReporte', the_listener)
        #~ self.__addActionListener('cmdReporteSat', the_listener)
        self.__addActionListener('cmdCorreo', the_listener)
        self.__addActionListener('cmdNotas', the_listener)
        self.__addActionListener('cmdCamposPersonalizados', the_listener)
        self.__addActionListener('cmdReportes', the_listener)
        self.__addActionListener('cmdAddenda', the_listener)
        self.__addActionListener('cmdEnviar', the_listener)
        self.__addActionListener('cmdImprimir', the_listener)

        the_listener = FocusListener(self.caller, eventos)
        self.__addFocusListener('txtReceptor', the_listener)
        self.__addFocusListener('txtCfd', the_listener)
        self.__addFocusListener('txtFolio1', the_listener)
        self.__addFocusListener('txtFolio2', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtReceptor', the_listener)
        self.__addKeyListener('txtCfd', the_listener)

        the_listener = CheckBoxListener(self.caller, eventos)
        self.__addActionListener('chkDetalle', the_listener)
        self.__addActionListener('chkGuardar', the_listener)
        self.__addActionListener('chkEditar', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridReceptores', the_listener)
        self.__addSelectionListener('gridFacturas', the_listener)

        the_listener = ItemListener(self.caller, eventos)
        self.__addItemListener('lstAno', the_listener)
        self.__addItemListener('lstMes', the_listener)
        self.__addItemListener('lstEstatus', the_listener)
        return

    def importXML(self):
        eventos = EventosImportXML(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdImportar', the_listener)
        self.__addActionListener('cmdGuardar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)

        the_listener = MouseListener(self.caller, eventos)
        self.__addMouseListener('gridConceptos', the_listener)
        return

    def adminnomina(self):
        eventos = EventosAdminNomina(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdImportar', the_listener)
        self.__addActionListener('cmdEnviar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdSinTimbrar', the_listener)
        self.__addActionListener('cmdLimpiarSeleccion', the_listener)
        self.__addActionListener('cmdSeleccionarTodo', the_listener)
        self.__addActionListener('cmdPdf', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)
        self.__addActionListener('cmdDelete', the_listener)
        self.__addActionListener('cmdCopyXML', the_listener)
        self.__addActionListener('cmdFolio', the_listener)
        self.__addActionListener('cmdFiltrar1', the_listener)

        the_listener = FocusListener(self.caller, eventos)
        self.__addFocusListener('txtReceptor', the_listener)
        self.__addFocusListener('txtFolio', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtReceptor', the_listener)
        self.__addKeyListener('txtFolio', the_listener)

        the_listener = ItemListener(self.caller, eventos)
        self.__addItemListener('lstFechaPago', the_listener)
        self.__addItemListener('lstAno', the_listener)
        self.__addItemListener('lstMes', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridReceptores', the_listener)
        return


class ItemListener(unohelper.Base, XItemListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def itemStateChanged(self, ItemEvent):
        control_name = '%s_itemStateChanged' % ItemEvent.Source.Model.Name
        getattr(self.eventos, control_name)(ItemEvent.Source)
        return


class RoadMapMessageListenerTools(unohelper.Base, XItemListener):

    def __init__(self, caller, events):
        self.caller = caller
        self.events = events

    def disposing(self, event):
        pass

    def itemStateChanged(self, ItemEvent):
        self.events._config(ItemEvent.ItemId + 1)
        return


class RoadMapMessageListener(unohelper.Base, XItemListener):
    """call SDK"""
    def __init__(self, caller,eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def itemStateChanged(self, ItemEvent):
        self.caller.dialog.Model.Step = ItemEvent.ItemId + 1
        self.eventos.ConfigOptions(ItemEvent.ItemId)
        #~ if ItemEvent.ItemId == 2:
            #~ if not self.caller.dialog.getControl('optOng').State:
                #~ self.caller.dialog.getControl('lblAutorizacionOng').Visible = False
                #~ self.caller.dialog.getControl('txtAutorizacionOng').Visible = False
                #~ self.caller.dialog.getControl('lblFechaOng').Visible = False
                #~ self.caller.dialog.getControl('txtFechaOng').Visible = False
            #~ if not self.caller.dialog.getControl('txtRfc').Text:
                #~ message = 'Aun no configuras el certificado de sellos, no ' \
                        #~ 'podrás guardar los datos del emisor hasta haber ' \
                        #~ 'capturado primero el certificado de sellos'
                #~ self.caller.unogui.createMsgBox({'Message': message})
        #~ elif ItemEvent.ItemId == 7 or ItemEvent.ItemId == 9:
            #~ self.eventos.ConfigOptions(ItemEvent.ItemId)
        return


class ButtonListener(unohelper.Base, XActionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def actionPerformed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        controls1 = ('cmdAgregarRegimen',
                    'cmdAgregarCondicionPago',
                    'cmdAgregarMetodoPago',
                    'cmdAgregarAduana',
                    'cmdAgregarUnidad')
        controls2 = ('cmdEliminarRegimen',
                    'cmdEliminarCondicionPago',
                    'cmdEliminarMetodoPago',
                    'cmdEliminarAduana',
                    'cmdEliminarUnidad',
                    'cmdEliminarDirectorio')
        if control_name in controls1:
            control_name = 'cmdAgregarCampo'
            getattr(self.eventos, control_name)(actionEvent.Source)
        elif control_name in controls2:
            control_name = 'cmdEliminarCampo'
            getattr(self.eventos, control_name)(actionEvent.Source)
        else:
            getattr(self.eventos, control_name)()


class OptionButtonListener(unohelper.Base, XActionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def actionPerformed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        event_name = {}
        event_name['optFisica'] = 'optTipoContribuyente'
        event_name['optMoral'] = 'optTipoContribuyente'
        event_name['optOng'] = 'optTipoContribuyente'
        event_name['optCorreo0'] = 'optCorreo'
        event_name['optCorreo1'] = 'optCorreo'
        event_name['optCorreo2'] = 'optCorreo'
        event_name['optCorreo3'] = 'optCorreo'
        getattr(self.eventos, event_name[control_name])(actionEvent.Source)


class FocusListener(unohelper.Base, XFocusListener):
    def __init__(self, caller, eventos=None):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def focusGained(self, actionEvent):
        actionEvent.Source.Model.Border = 0
        actionEvent.Source.Model.BackgroundColor = COLORS['YELLOW']
        sel = actionEvent.Source.getSelection()
        sel.Min = 0
        sel.Max = len(actionEvent.Source.Text)
        actionEvent.Source.setSelection(sel)
    def focusLost(self, actionEvent):
        actionEvent.Source.Model.Border = 1
        actionEvent.Source.Model.BackgroundColor = COLORS['WHITE']
        control_name = actionEvent.Source.Model.Name
        if control_name == 'txtReceptor' or control_name == 'descripcion':
            control_name = '%s_focusLost' % actionEvent.Source.Model.Name
            getattr(self.eventos, control_name)(actionEvent.Source)


class GridFocusListener(unohelper.Base, XFocusListener):
    def __init__(self, caller, eventos=None):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def focusGained(self, actionEvent):
        pass
    def focusLost(self, actionEvent):
        actionEvent.Source.setVisible(False)
        control_name = actionEvent.Source.Model.Name
        if  control_name=='treeCategorias' or control_name=='gridAlumnos':
            control_name = '%s_focusLost' % control_name
            getattr(self.eventos, control_name)(actionEvent.Source)


class MouseListener(unohelper.Base, XMouseListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def mousePressed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        event_name = {}
        event_name['lstRegimen'] = 'lstDobleClick'
        event_name['lstCondicionPago'] = 'lstDobleClick'
        event_name['lstMetodoPago'] = 'lstDobleClick'
        event_name['lstAduana'] = 'lstDobleClick'
        event_name['lstUnidad'] = 'lstDobleClick'
        #event_name['lstPersonalizado'] = 'lstDobleClick'
        event_name['lstRutasEspejo'] = 'lstDobleClick'
        event_name['lstRutasTrabajo'] = 'lstRutasTrabajo_DobleClick'
        event_name['gridProductos'] = 'gridProductos_DobleClick'
        event_name['gridReceptores'] = 'gridReceptores_DobleClick'
        event_name['gridMonedas'] = 'gridMonedas_DobleClick'
        event_name['gridPersonalizados'] = 'gridPersonalizados_DobleClick'
        #~ event_name['gridCeldas'] = 'gridCeldas_DobleClick'
        event_name['gridCampos'] = 'gridCampos_DobleClick'
        event_name['gridDetalle'] = 'gridDetalle_DobleClick'
        event_name['gridConceptos'] = 'gridConceptos_DobleClick'
        event_name['treeCategorias'] = 'treeDobleClick'
        if actionEvent.ClickCount == 2:
            getattr(self.eventos, event_name[control_name])(actionEvent.Source)
        else:
            getattr(self.eventos, control_name)(actionEvent.Source)
    def mouseReleased(self, actionEvent):
        pass
    def mouseEntered(self, actionEvent):
        pass
    def mouseExited(self, actionEvent):
        pass


class KeyListener(unohelper.Base, XKeyListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def keyPressed(self, actionEvent):
        control_name = '%s_keyPressed' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent)
    def keyReleased(self, actionEvent):
        control_name = '%s_keyReleased' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent)


class TextListener(unohelper.Base, XTextListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def textChanged(self, actionEvent):
        control_name = '%s_textChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)()


class GridSelectionListener(unohelper.Base, XGridSelectionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def selectionChanged(self, actionEvent):
        control_name = '%s_selectionChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent.Source)
        return


class TreeSelectionChangeListener(unohelper.Base, XSelectionChangeListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def selectionChanged(self, actionEvent):
        control_name = '%s_selectionChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent.Source)
        return


class CheckBoxListener(unohelper.Base, XActionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def actionPerformed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent.Source)
