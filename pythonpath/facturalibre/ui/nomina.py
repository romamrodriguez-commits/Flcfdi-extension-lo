from .listenersadmin import listener

DLG_NAME = 'dlgNomina.xdl'
ICON_EXIT = 'salir.png'
ICON_IMPORT = 'import.png'

class Dlg(object):

    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.db = caller.db
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        nombre = self.db.select_field('certificado', 'nombre')
        self.dialog.Title = 'Importar Nomina - %s' % nombre
        self.listener = listener(self)
        self.__config()
        self.listener.nomina()
        self.dialog.execute()
        self.dialog.dispose()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_EXIT)
        self.dm.cmdCancelar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_IMPORT)
        self.dm.cmdImportar.ImageURL = img_url
        self.dialog.getControl('cmdEnviar').setVisible(False)


        return
