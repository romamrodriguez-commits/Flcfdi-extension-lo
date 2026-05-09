#!
# -*- coding: utf-8 -*-
from .listeners import listener

DLG_NAME = 'dlgRepTotales.xdl'


class Dlg(object):
    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.db = caller.db
        self.unogui = caller.unogui
        self.globales = caller.globales
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.listener.repclitot()
        if self.__config():
            self.dialog.execute()
            self.dialog.dispose()

    def __config(self):
        self.dm.txtFechaIni.Date = self.util.setUtilDate()
        self.dm.txtFechaFin.Date = self.util.setUtilDate()

        #~ Consultamos la base de datos para asegurar que hay facturas para consultar
        data=self.db.select(('cfdfacturas',),('id',))
        if not data:
            self.util.msgbox("No hay facturas para reportar")
            self.dialog.getControl('cmdGenerar').Enable = False
            return False
        self.dm.optFacturas.State = True
        return True
