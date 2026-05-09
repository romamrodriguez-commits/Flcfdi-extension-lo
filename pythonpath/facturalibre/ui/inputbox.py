#!
# -*- coding: utf-8 -*-
from .listenersadmin import listener

DLG_NAME = 'dlgInput.xdl'
ICON_ACEPTAR = 'ok.png'
ICON_CANCELAR = 'cancel.png'


class Dlg(object):
    def __init__(self, caller, values):
        self.caller = caller
        self.unogui = caller.unogui
        self.globales = caller.globales
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config(values)
        self.listener.inputbox()

    def __config(self, values):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ACEPTAR)
        self.dm.cmdAceptar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_CANCELAR)
        self.dm.cmdCancelar.ImageURL = img_url
        self.dm.lblInfo.Label = values[0]
        self.dm.txtValor.MultiLine = values[1]
        if values[1]:
            self.dm.txtValor.Height = 36
        self.dialog.Title = '%s' % self.globales['APP_TITULO']
        self.unogui.centerDialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()
