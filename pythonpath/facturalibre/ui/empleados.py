# -*- coding: utf-8 -*-

import logging
from .listeners import Listener
from facturalibre.settings import TITLE, LOG, ICONS
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, db):
        self.db = db
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.getModel()
        self.listener = Listener(self.dialog, self.db)
        self._config()
        self.listener.empleados()
        self.dialog.execute()
        self.dialog.dispose()

    def _config(self):
        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.new_employer.ImageURL = img_url.format(ICONS['NEW_EMPLOYER'])
        self.dm.edit_employer.ImageURL = img_url.format(ICONS['EDIT'])
        self.dm.delete_employer.ImageURL = img_url.format(ICONS['DELETE'])
        self.dm.show_all.ImageURL = img_url.format(ICONS['CLEAN'])
        self.dm.make_report.ImageURL = img_url.format(ICONS['REPORT'])
        self.dm.close.ImageURL = img_url.format(ICONS['CLOSE'])
        name = self.db.select_field('certificado', 'nombre')
        self.dialog.Title = '{} - Empleados - {}'.format(TITLE, name)

        properties = {}
        properties['Name'] = 'grid_employers'
        properties['PositionX'] = 5
        properties['PositionY'] = 27
        properties['Width'] = 390
        properties['Height'] = 232
        properties['Step'] = 0
        properties['SelectionModel'] = 1
        columns=(
            {'Title': 'No', 'ColumnWidth': 20, 'HorizontalAlign': 2},
            {'Title': 'RFC', 'ColumnWidth': 50, 'HorizontalAlign': 0},
            {'Title': 'CURP', 'ColumnWidth': 70, 'HorizontalAlign': 0},
            {'Title': 'Nombre', 'ColumnWidth': 200, 'HorizontalAlign': 0}
        )
        grid = util.create_grid(self.dialog, columns, properties)
        self.dm.grid_employers.RowHeaderWidth = 15
        data = self.db.select(
            ('empleados',), ('id','rfc', 'curp', 'nombre'), order='nombre')
        # Delete
        self.dm.new_employer.Enabled = False
        self.dm.make_report.Enabled = False
        if data:
            util.data_to_grid(self.dm.grid_employers.GridDataModel, data)
            #~ self.dm.edit_employer.Enabled = True
            #~ self.dm.delete_employer.Enabled = True
            self.dm.filter_employers.Enabled = True
            if len(data) == 1:
                info = '1 Registro'
            else:
                info = '{} Registros'.format(len(data))
        else:
            info = 'Sin registros'
        self.dm.info.Label = info
        util.center_dialog(self.dialog)
        self.dialog.getControl('filter_employers').setFocus()
        return

