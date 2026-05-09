# -*- coding: utf-8 -*-

# listeners
import unohelper
from com.sun.star.awt import XActionListener
from com.sun.star.awt import XFocusListener
from com.sun.star.awt.grid import XGridSelectionListener
from facturalibre.controllers.alumnos import EventosAlumnos


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

    def __addSelectionListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addSelectionListener(the_listener)
        return

    def __addSelectionChangeListener(self,control_name,the_listener):
        control = self.dialog.getControl(control_name)
        control.addSelectionChangeListener(the_listener)
        return

    def alumnos(self):
        eventos = EventosAlumnos(self.caller)

        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdSalir', the_listener)
        self.__addActionListener('cmdAgregar', the_listener)
        self.__addActionListener('cmdEliminar', the_listener)
        self.__addActionListener('cmdGuardar', the_listener)
        self.__addActionListener('cmdCambiarNivel', the_listener)

        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtAlumno',the_listener)
        self.__addFocusListener('txtCurp',the_listener)
        return None

    def inputbox(self):
        eventos = EventosInputBox(self.caller)
        the_listener = ButtonListener(self.caller, eventos)
        self.__addActionListener('cmdAceptar', the_listener)
        self.__addActionListener('cmdCancelar', the_listener)
        the_listener = FocusListener(self.caller)
        self.__addFocusListener('txtValor',the_listener)
        return


class ButtonListener(unohelper.Base, XActionListener):
    def __init__(self, caller, eventos):
        self.caller = caller
        self.eventos = eventos
    def disposing(self, eventObject):
        pass
    def actionPerformed(self, actionEvent):
        control_name = actionEvent.Source.Model.Name
        controls=('cmdAgregarCorreo','cmdAgregarTelefono','cmdAgregarContacto')
        if control_name in controls:
            control_name='cmdAgregarCampo'
            getattr(self.eventos,control_name)(actionEvent.Source)
        else:
            getattr(self.eventos,control_name)()


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


class GridSelectionListener(unohelper.Base, XGridSelectionListener):
    def __init__(self, caller,eventos):
        self.caller = caller
        self.eventos = eventos
    def selectionChanged(self, actionEvent):
        control_name = '%s_selectionChanged' % actionEvent.Source.Model.Name
        getattr(self.eventos,control_name)(actionEvent.Source)
        return
