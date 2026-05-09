# -*- coding: utf-8 -*-

# listeners
import unohelper
from com.sun.star.awt import XItemListener
from com.sun.star.awt import XActionListener
from com.sun.star.awt import XFocusListener
from com.sun.star.awt import XMouseListener
from com.sun.star.awt import XKeyListener
from com.sun.star.awt import XTextListener
from com.sun.star.view import XSelectionChangeListener
from com.sun.star.awt.grid import XGridSelectionListener
from facturalibre.controllers.clientesadmin import EventosClientesAdmin
#~ from facturalibre.controllers.producto import EventosProductosAdmin
from facturalibre.controllers.add_products import EventosAddProducts
from facturalibre.controllers.rutas import EventosRutas
from facturalibre.controllers.inputbox import EventosInputBox
from facturalibre.controllers.inputbox2 import EventosInputBox2
from facturalibre.controllers.seleccionar import EventosSeleccionar
from facturalibre.controllers.campos import EventosCampos
from facturalibre.controllers.edit import EventosEditAdd
from facturalibre.controllers.asignar import EventosAsignar
from facturalibre.controllers.refacturar import EventosRefacturar
from facturalibre.controllers.nomina import EventosNomina


AMARILLO = 16777164
BLANCO = 16777215


class listener(object):
    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog

    def __addActionListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addActionListener(the_listener)
        return

    def __addFocusListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addFocusListener(the_listener)
        return

    def __addMouseListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addMouseListener(the_listener)
        return

    def __addKeyListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addKeyListener(the_listener)
        return

    def __addSelectionListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addSelectionListener(the_listener)
        return

    def __addSelectionChangeListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addSelectionChangeListener(the_listener)
        return

    def __addItemListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addItemListener(the_listener)
        return

    def __addTextListener(self, control_name, the_listener):
        control = self.dialog.getControl(control_name)
        control.addTextListener(the_listener)
        return

    def nomina(self):
        eventos = EventosNomina(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdImportar', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)
        return

    def clientesadmin(self):
        eventos = EventosClientesAdmin(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGuardarSalir', the_listener)
        self.__addActionListener('cmdAgregarCorreo', the_listener)
        self.__addActionListener('cmdAgregarTelefono', the_listener)
        self.__addActionListener('cmdAgregarContacto', the_listener)
        self.__addActionListener('cmdBorrarCorreo', the_listener)
        self.__addActionListener('cmdBorrarTelefono', the_listener)
        self.__addActionListener('cmdBorrarContacto', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdAlumnos', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('id', the_listener)
        self.__addFocusListener('nombre', the_listener)
        self.__addFocusListener('rfc', the_listener)
        self.__addFocusListener('calle', the_listener)
        self.__addFocusListener('noExterior', the_listener)
        self.__addFocusListener('noInterior', the_listener)
        self.__addFocusListener('codigoPostal', the_listener)
        self.__addFocusListener('colonia', the_listener)
        self.__addFocusListener('municipio', the_listener)
        self.__addFocusListener('pais', the_listener)
        self.__addFocusListener('fechaalta', the_listener)
        self.__addFocusListener('notas', the_listener)
        self.__addFocusListener('txtCorreo', the_listener)
        self.__addFocusListener('txtTelefono', the_listener)
        self.__addFocusListener('txtContacto', the_listener)
        #~ self.__addFocusListener('metododepago', the_listener)
        self.__addFocusListener('cuentadepago', the_listener)
        self.__addFocusListener('condiciondepago', the_listener)

        the_listener = MouseListener(self.caller,eventos)
        self.__addMouseListener('lstCorreo',the_listener)
        self.__addMouseListener('lstTelefono',the_listener)
        self.__addMouseListener('lstContacto',the_listener)

        the_listener = OptionButtonListener(self.caller,eventos)
        self.__addActionListener('optFisica',the_listener)
        self.__addActionListener('optMoral',the_listener)
        self.__addActionListener('optExtranjero',the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('codigoPostal', the_listener)

        the_listener = GridSelectionListener(self.caller,eventos)
        self.__addSelectionListener('gridColonias', the_listener)
        the_listener = GridFocusListener(self.caller)
        self.__addFocusListener('gridColonias', the_listener)
        return None

    def productosadmin(self):
        eventos = EventosProductosAdmin(self.caller)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('noIdentificacion', the_listener)
        self.__addFocusListener('categoria', the_listener)
        self.__addFocusListener('descripcion', the_listener)
        self.__addFocusListener('unidad', the_listener)
        self.__addFocusListener('valorUnitario', the_listener)
        self.__addFocusListener('cantidad', the_listener)
        self.__addFocusListener('total', the_listener)
        self.__addFocusListener('existencia', the_listener)
        self.__addFocusListener('codigobarras', the_listener)
        self.__addFocusListener('CuentaPredial', the_listener)

        the_listener = CheckBoxListener(self.caller, eventos)
        self.__addActionListener('chkAutomatica', the_listener)
        self.__addActionListener('chkInventario', the_listener)
        self.__addActionListener('chkCuentaPredial', the_listener)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdMostrarCategorias', the_listener)
        self.__addActionListener('cmdAgregarCategoria', the_listener)
        self.__addActionListener('cmdGuardar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdLimpiarSeleccion', the_listener)

        the_listener = MouseListener(self.caller, eventos)
        self.__addMouseListener('treeCategorias', the_listener)

        the_listener = TextListener(self.caller, eventos)
        self.__addTextListener('cantidad', the_listener)
        self.__addTextListener('valorUnitario', the_listener)
        self.__addTextListener('total', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridImpuestos', the_listener)
        return None

    def rutas(self):
        eventos = EventosRutas(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdEntrar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        return None

    def inputbox(self):
        eventos = EventosInputBox(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAceptar', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)
        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtValor', the_listener)
        return

    def inputbox2(self):
        eventos = EventosInputBox2(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAceptar', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)
        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtValor',the_listener)
        return

    def campos(self):
        eventos = EventosCampos(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAceptar', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)
        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtEditar',the_listener)
        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridCampos', the_listener)
        the_listener = TextListener(self.caller, eventos)
        self.__addTextListener('txtEditar', the_listener)
        self.__addTextListener('datFecha', the_listener)
        return

    def edit_add(self):
        eventos = EventosEditAdd(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdGuardar', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdAgregarNodo', the_listener)
        self.__addActionListener('cmdEliminarNodo', the_listener)
        self.__addActionListener('cmdActualizarNodo', the_listener)
        self.__addActionListener('cmdAgregarAtributo', the_listener)
        self.__addActionListener('cmdEliminarAtributo', the_listener)
        self.__addActionListener('cmdActualizarAtributo', the_listener)
        self.__addActionListener('cmdActualizarValor', the_listener)
        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtNodo',the_listener)
        self.__addFocusListener('txtValor',the_listener)
        self.__addFocusListener('txtAtributo',the_listener)
        self.__addFocusListener('txtValorAtributo',the_listener)
        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridAtributos', the_listener)
        the_listener = TreeSelectionChangeListener(self.caller,eventos)
        self.__addSelectionChangeListener('treeAddenda',the_listener)
        return

    def asignar(self):
        eventos = EventosAsignar(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAsignarNodo', the_listener)
        self.__addActionListener('cmdAsignarPersonalizado', the_listener)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdGuardar', the_listener)
        self.__addActionListener('cmdEliminar', the_listener)
        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridAsignaciones', the_listener)
        self.__addSelectionListener('gridAtributos', the_listener)
        the_listener = TreeSelectionChangeListener(self.caller,eventos)
        self.__addSelectionChangeListener('treeFactura',the_listener)
        self.__addSelectionChangeListener('treeAddenda',the_listener)
        the_listener = CheckBoxListener(self.caller, eventos)
        self.__addActionListener('chkValorNodo', the_listener)
        return

    def refacturar(self):
        eventos = EventosRefacturar(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdFiltrar1', the_listener)
        self.__addActionListener('cmdFiltrar2', the_listener)
        self.__addActionListener('cmdRefacturar', the_listener)
        self.__addActionListener('cmdEliminar', the_listener)
        self.__addActionListener('cmdPdf', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtCfd',the_listener)
        self.__addFocusListener('txtReceptor', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtReceptor', the_listener)
        self.__addKeyListener('txtCfd', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridReceptores', the_listener)

        the_listener = CheckBoxListener(self.caller, eventos)
        self.__addActionListener('chkPrefacturas', the_listener)
        return

    def add_products(self):
        eventos = EventosAddProducts(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdAgregarProductos', the_listener)
        return

    def seleccionar(self):
        eventos = EventosSeleccionar(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAceptar', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtPrimero', the_listener)
        self.__addFocusListener('txtSegundo', the_listener)

        the_listener = KeyListener(self.caller, eventos)
        self.__addKeyListener('txtPrimero', the_listener)
        self.__addKeyListener('txtSegundo', the_listener)

        the_listener = GridSelectionListener(self.caller, eventos)
        self.__addSelectionListener('gridProductos', the_listener)
        return

    def niveles(self):
        eventos = EventosNiveles(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAgregar', the_listener)
        self.__addActionListener('cmdEliminar', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtNivel', the_listener)
        self.__addFocusListener('txtAutorizacion', the_listener)
        return


class ItemListener(unohelper.Base, XItemListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def itemStateChanged(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent)


class ButtonListener(unohelper.Base, XActionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def actionPerformed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        controls_add = (
            'cmdAgregarCorreo', 'cmdAgregarTelefono', 'cmdAgregarContacto')
        controls_del = (
            'cmdBorrarCorreo', 'cmdBorrarTelefono', 'cmdBorrarContacto')
        if control_name in controls_add:
            control_name = 'cmdAgregarCampo'
            getattr(self.eventos, control_name)(actionEvent.Source)
        elif control_name in controls_del:
            control_name = 'cmdEliminarCampo'
            getattr(self.eventos, control_name)(actionEvent.Source)
        else:
            getattr(self.eventos, control_name)()


class CheckBoxListener(unohelper.Base, XActionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def actionPerformed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent.Source)


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
        event_name['optExtranjero'] = 'optTipoContribuyente'
        getattr(self.eventos,event_name[control_name])(actionEvent.Source)


class FocusListener(unohelper.Base, XFocusListener):
    def __init__(self, caller):
        self.caller = caller
    def disposing(self, eventObject):
        pass
    def focusGained(self, actionEvent):
        actionEvent.Source.Model.Border = 0
        actionEvent.Source.Model.BackgroundColor = AMARILLO
        sel = actionEvent.Source.getSelection()
        sel.Min = 0
        sel.Max = len(actionEvent.Source.Text)
        actionEvent.Source.setSelection(sel)
    def focusLost(self, actionEvent):
        actionEvent.Source.Model.Border = 1
        actionEvent.Source.Model.BackgroundColor = BLANCO


class GridFocusListener(unohelper.Base, XFocusListener):
    def __init__(self, caller):
        self.caller = caller
    def disposing(self, eventObject):
        pass
    def focusGained(self, actionEvent):
        pass
    def focusLost(self, actionEvent):
        actionEvent.Source.setVisible(False)


class MouseListener(unohelper.Base, XMouseListener):
    def __init__(self, caller,eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def mousePressed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        event_name = {}
        event_name['lstCorreo'] = 'lstDobleClick'
        event_name['lstTelefono'] = 'lstDobleClick'
        event_name['lstContacto'] = 'lstDobleClick'
        event_name['treeCategorias'] = 'treeDobleClick'
        if actionEvent.ClickCount==2:
            getattr(self.eventos,event_name[control_name])(actionEvent.Source)
        else:
            pass
        pass
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


class GridSelectionListener(unohelper.Base, XGridSelectionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def selectionChanged(self, actionEvent):
        control_name = '%s_selectionChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos,control_name)(actionEvent.Source)
        return


class TextListener(unohelper.Base, XTextListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def textChanged(self, actionEvent):
        control_name = '%s_textChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)()


class TreeSelectionChangeListener(unohelper.Base, XSelectionChangeListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def selectionChanged(self, actionEvent):
        control_name = '%s_selectionChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos, control_name)(actionEvent.Source)
        return
