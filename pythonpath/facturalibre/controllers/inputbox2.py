#!
# -*- coding: utf-8 -*-


class EventosInputBox2(object):
    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()

    def cmdAceptar(self):
        txt = self.dialog.getControl('txtValor')
        self.caller.unogui.validate(txt, 'Vacio')
        self.caller.caller.value = txt.Text
        self.dialog.endDialog(1)
        return

    def cmdCancelar(self):
        self.dialog.endDialog(0)
        return














