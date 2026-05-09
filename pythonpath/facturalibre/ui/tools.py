# -*- coding: utf-8 -*-
import logging
from .listeners import listener
from facturalibre.settings import LOG, ICONS, TITLE, ULM_WWW
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self._config()
        self.listener.tools()
        self.dialog.execute()
        self.dialog.dispose()

    def _config(self):
        path_icons = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdSalir.ImageURL = path_icons.format(ICONS['CLOSE'])

        nombre = self.db.select_field('emisor', 'nombre')
        self.dialog.Title = '{} - Utilidades - {}'.format(TITLE, nombre)

        properties = {}
        properties['Name'] = 'txtURL'
        properties['PositionX'] = 185
        properties['PositionY'] = 36
        properties['Width'] = 70
        properties['URL'] = ULM_WWW
        properties['Label'] = ULM_WWW
        properties['Step'] = 15
        url = util.create_control(self.dialog, 'FixedHyperlink', properties)
        properties.clear()
        properties['Name'] = 'txtURL2'
        properties['PositionX'] = 200
        properties['PositionY'] = 185
        properties['Width'] = 70
        properties['URL'] = 'http://universolibre.org'
        properties['Label'] = 'Donaciones'
        properties['Step'] = 15
        url = util.create_control(self.dialog, 'FixedHyperlink', properties)
        properties.clear()
        properties['Name'] = 'imgLogo'
        properties['ImageURL'] = path_icons.format(ICONS['LOGO'])
        img = util.change_control(self.dialog, properties)
        properties.clear()
        properties['Name'] = 'rmMapa'
        properties['Height'] = 250
        rm = util.create_control(self.dialog, 'Roadmap', properties)
        options = ('Importar datos', 'Actualizar datos', 'Importar productos')
        util.add_options_roadmap(rm, options)

        self.page1(path_icons)
        self.page2(path_icons)
        self.page3(path_icons)
        util.center_dialog(self.dialog)
        self.dialog.Model.Step = 15

    def page1(self, path_icons):
        self.dm.cmdSeleccionarDirectorio.ImageURL = \
            path_icons.format(ICONS['FOLDER'])
        self.dm.cmdImportarDatos.ImageURL = path_icons.format(ICONS['XML'])
        return

    def page2(self, path_icons):
        self.dm.cmdActualizarDatos.ImageURL = path_icons.format(ICONS['IMPORT'])
        return

    def page3(self, path_icons):
        self.dm.cmdImportarProductos.ImageURL = \
            path_icons.format(ICONS['IMPORT'])
        self.dm.optSumarExistencias.State = 1
        return
