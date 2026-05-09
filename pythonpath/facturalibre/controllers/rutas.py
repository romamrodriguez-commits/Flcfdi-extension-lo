#!
# -*- coding: utf-8 -*-


class EventosRutas(object):
    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()

    def cmdEntrar(self):
        grid = self.dialog.getControl('gridEmisores')
        if grid.CurrentRow == -1:
            message = 'Selecciona un emisor'
            self.caller.unogui.createMsgBox({'Message': message})
        else:
            self.dialog.endDialog(grid.CurrentRow)
        return

    def cmdSalir(self):
        self.dialog.endDialog(-1)
        return

