# -*- coding: utf-8 -*-

from facturalibre.settings import TITLE, ICONS
from facturalibre.modulos import util


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller, msg):
        self.caller = caller
        self.msg = msg
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.getModel()
        self._config()

    def _config(self):
        from .listeners import Listener

        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.ok.ImageURL = img_url.format(ICONS['OK'])
        self.dm.cancel.ImageURL = img_url.format(ICONS['CANCEL'])
        self.dm.info.Label = self.msg
        self.dialog.Title = TITLE
        listener = Listener(self.dialog)
        listener.input_box(self.caller)
        util.center_dialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()
