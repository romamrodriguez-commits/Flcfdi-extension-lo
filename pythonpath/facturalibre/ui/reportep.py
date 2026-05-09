#!
# -*- coding: utf-8 -*-
from .listeners import listener

DLG_NAME = 'dlgRepClientes.xdl'


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
        self.listener.reportep()
        self.__config()
        self.dialog.execute()
        self.dialog.dispose()

    def __config(self):
        self.dm.txtFechaIni.Date = self.util.setUtilDate()
        self.dm.txtFechaFin.Date = self.util.setUtilDate()
        self.dialog.Title = 'Reporte de proveedores'
        listbox = self.dialog.getControl('lstClientes')
        data=self.db.select(('receptores',),('nombre',),where='esproveedor=1',order='nombre')
        data_ok = [('Todos',)] + data
        if data:
            self.unogui.query_to_listbox(data_ok, listbox)
        else:
            self.util.msgbox("No hay proveedores para reportar")
            self.dialog.getControl('cmdGenerar').Enable = False
        self.dm.optCliente.State = True
        self.dialog.getControl('cmdGenerar').setFocus()

        return
