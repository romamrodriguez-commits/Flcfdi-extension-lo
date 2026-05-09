#!
# -*- coding: utf-8 -*-
from .listenersadmin import listener

DLG_NAME = 'dlgAddProducts.xdl'
ICON_IMPORT = 'import.png'
ICON_SALIR = 'close.png'

class Dlg(object):
    def __init__(self, caller, data=(), agregar=False):
        self.caller = caller
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.util = caller.util
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'],DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config(data, agregar)
        self.listener.add_products()

    def __config(self, data, agregar):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_IMPORT)
        self.dm.cmdAgregarProductos.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'],ICON_SALIR)
        self.dm.cmdSalir.ImageURL=img_url

        title='%s - Agregar productos en lote' % self.globales['APP_TITULO']
        self.dialog.Title = title
        self.dialog.getControl('fileProductos').setFocus()

        message = 'Todos los precios incluyen IVA: %s\n' % (
            'SI' if data[1] else 'NO')
        message += 'Permitir facturar productos sin existencia: %s\n' % (
            'SI' if data[2] else 'NO')
        message += 'Permitir cambiar el precio al facturar: %s\n' % (
            'SI' if data[5] else 'NO')
        message += 'Permitir agregar producto varias veces: %s' % (
            'SI' if agregar else 'NO')
        self.dm.lblInfo.Label = message
        return

    def execute(self):
        return self.dialog.execute()
