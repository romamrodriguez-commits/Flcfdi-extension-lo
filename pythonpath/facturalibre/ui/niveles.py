# -*- coding: utf-8 -*-
import traceback
from .listeners import Listener
from facturalibre.settings import TITLE, ICONS
from facturalibre.modulos import util


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, db):
        self.db = db
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.Model
        self.listener = Listener(self.dialog, self.db)
        self._config()
        self.listener.niveles()

    def _config(self):
        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdAgregar.ImageURL = img_url.format(ICONS['ADD'])
        self.dm.cmdEliminar.ImageURL = img_url.format(ICONS['DELETE'])
        self.dialog.Title = '{} - Niveles'.format(TITLE)

        properties = {}
        properties['Name'] = 'gridNiveles'
        properties['PositionX'] = 5
        properties['PositionY'] = 60
        properties['Width'] = 160
        properties['Height'] = 70
        properties['SelectionModel'] = 1
        columns = ({
            'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
            {'Title': 'Nivel', 'ColumnWidth': 70, 'HorizontalAlign': 0},
            {'Title': 'Autorización', 'ColumnWidth': 70, 'HorizontalAlign': 0}
        )
        grid = util.create_grid(self.dialog, columns, properties)
        data = self.db.select(('niveles',), order='nivel')
        util.data_to_grid(self.dm.gridNiveles.GridDataModel, data, True)
        return

    def execute(self):
        try:
            return self.dialog.execute()
        except:
            print (traceback.format_exc())

