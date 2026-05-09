# -*- coding: utf-8 -*-

from .values import Config
from .modulos.pyUtil import Util  # Delete in 2
from .ui.pyUnoGui import UnoGui

from .ui import Dialog
from .ui import rutas
from .db import DBConfig
from .settings import NODE, SPLIT, TYPE_MSG, TITLE, DB_NAME, NODE_EMPRESAS, \
    NODE_PATHS
from .modulos import util


class CFDI(object):

    def __init__(self, ctx, option=''):
        self.ctx = ctx
        self.util = Util()
        self.unogui = UnoGui(self.ctx)
        self.globales = self._globales()
        self.emisores = util.get_config_value(NODE, NODE_EMPRESAS).split(SPLIT)
        self.work_paths = util.get_config_value(NODE, NODE_PATHS).split(SPLIT)
        self.guardar = False
        self.path = ''
        self.option = option
        self.validate = self._validate()
        if self.validate:
            self.db = self._makedb()
            if not self.db:
                self.validate = False

    def _globales(self):
        C = Config(self.util)
        return C.__dict__

    def _validate(self):
        ok, msg = util.check_app()
        if not ok:
            util.msgbox(msg, TYPE_MSG['ERROR'])
            return False
        if self.option == 'close':
            if self.globales['CURRENT_PATH']:
                self.util.set_configvalue(self.globales['NODE'], 'Actual', '')
                msg = 'Empresa cerrada correctamente'
            else:
                msg = 'No hay ninguna empresa abierta'
            util.msgbox(msg)
            return False
        if self.globales['CURRENT_PATH']:
            self.path = self._validate_path(self.globales['CURRENT_PATH'])
        else:
            self.path = self._validate_path(self._get_path())
        if self.path and self.guardar:
            self._save_config(self.path)
        return bool(self.path)

    def _validate_path(self, path=''):
        if not path:
            if self.guardar:
                msg = 'No seleccionaste ningún directorio'
                util.msgbox(msg, TYPE_MSG['ERROR'])
            return False
        if not util.path_exists(path):
            msg = 'No se encontró la ruta de trabajo:\n\n{}\n\nAsegurate de ' \
                'que exista o no haya sido borrada o cambiada. Presiona SI ' \
                'para borrar esta ruta del sistema, presiona NO para ' \
                'salir'.format(path)
            if self.unogui.createQuestion(TITLE, msg):
                self._save_config()
                msg = 'La configuración ha sido restaurada, vuelve a ' \
                    'ingresar para seleccionar un nuevo directorio de trabajo.'
                util.msgbox(msg)
            return False
        if not self.util.access(path):
            msg = 'No tienes derechos de escritura en el directorio:' \
                '\n\n{}'.format(path)
            util.msgbox(msg, TYPE_MSG['ERROR'])
            return False
        return path

    def _get_path(self):
        folder = ''
        index = 0
        if not self.work_paths[index]:
            msg = 'Es la primera vez que accedes al sistema, es necesario ' \
                'seleccionar un directorio de trabajo.\n\nPresiona SI para ' \
                'seleccionar uno ahora, presiona NO para salir, no podrás ' \
                'trabajar hasta haber seleccionado un directorio de trabajo.'
            if not self.unogui.createQuestion(TITLE, msg):
                return folder
            folder = self.unogui.getFolder(self.globales['PATH_USER'])
            self.guardar = True
            return folder

        if len(self.work_paths) == 1:
            folder = self.work_paths[index]
            return folder

        dialog_rutas = rutas.Dlg(self)
        index = dialog_rutas.execute()
        if index > -1:
            folder = self.work_paths[index]
            self.util.set_configvalue(NODE, 'Actual', folder)
            self.globales['CURRENT_PATH'] = folder
        return folder

    def _save_config(self, path=''):
        self.util.set_configvalue(NODE, NODE_EMPRESAS, '')
        self.util.set_configvalue(NODE, NODE_PATHS, path)
        self.util.set_configvalue(NODE, 'Actual', path)
        return

    def _makedb(self):
        path_db = util.join(self.path, DB_NAME)
        existe = util.path_exists(path_db)
        if not existe:
            msg = 'La base de datos no existe en la ruta de trabajo\n\n{}\n\n' \
                'Presiona SI para crearla, esto solo tomará unos segundos, ' \
                'no podras trabajar hasta crear la base de datos.\n\n' \
                'Presiona CANCELAR si deseas borrar esta ruta de trabajo ' \
                'para seleccionar otra'.format(self.path)
            res = self.unogui.createMsgBox(
                {'Type': 'querybox', 'Buttons': 4, 'Message': msg})
            if not res:
                self._save_config()
                msg = 'La configuración ha sido restaurada, vuelve a ' \
                    'ingresar para seleccionar un nuevo directorio de trabajo.'
                util.msgbox(msg)
                return False
            elif res == 3:
                return False

        DB = DBConfig(path_db)
        self.util.set_configvalue(NODE, 'Actual', self.path)

        if existe:
            if self.guardar:
                emisor = DB.select_field('emisor', 'nombre')
                if emisor:
                    self.util.set_configvalue(NODE, NODE_EMPRESAS, emisor)
                msg = 'Se establecio correctamente la ruta de trabajo y se ' \
                    'conecto correctamente a la base de datos, ya puedes ' \
                    'acceder al sistema.'
                util.msgbox(msg)
        else:
            msg = 'La base de datos se creo correctamente,\nya puedes ' \
                'acceder al sistema.'
            util.msgbox(msg)
        return DB

    def show(self):
        return Dialog(self, self.option)

