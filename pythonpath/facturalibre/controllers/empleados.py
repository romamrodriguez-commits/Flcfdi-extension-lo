# -*- coding: utf-8 -*-

import logging
import facturalibre.ui.input_box as input_box
from facturalibre.settings import LOG, KEY, TYPE_MSG, DOUBLE_CLICK
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class EmpleadosEvents(object):

    def __init__(self, dialog, db):
        self.dialog = dialog
        self.db = db
        self._init_vars()

    def _init_vars(self):
        self.dm = self.dialog.getModel()
        self.grid = self.dialog.getControl('grid_employers')
        self.grid_dm = self.dm.grid_employers.GridDataModel
        self.value = ''
        return

    def _update_info(self, rows):
        if rows == 0:
            info = 'Sin Registros'
        elif rows == 1:
            info = '1 Registro'
        else:
            info = '{} Registros'.format(rows)
        self.dm.info.Label = info
        return

    def new_employer(self, event):
        log.info('New')
        return

    def edit_employer(self, event):
        log.info('Edit')
        return

    def delete_employer(self, event):
        log.info('Delete')
        return

    def show_all(self, event):
        employers = self.db.select(
            ('empleados',), ('id','rfc', 'curp', 'nombre'), order='nombre')
        util.data_to_grid(self.grid_dm, employers)
        self.dm.filter_employers.Text = ''
        self.dm.show_all.Enabled = False
        self._update_info(len(employers))
        self.dialog.getControl('filter_employers').setFocus()
        return

    def make_report(self, event):
        log.info('Make Report')
        return

    def close(self, event):
        self.dialog.endExecute()
        return

    def filter_employers_focus_gained(self, event):
        sel = event.Source.getSelection()
        sel.Min = 0
        sel.Max = len(event.Source.Text)
        event.Source.setSelection(sel)
        return

    def filter_employers_focus_lost(self, event):
        pass

    def filter_employers_key_pressed(self, event):
        if event.KeyCode != KEY['RETURN']:
            employer = event.Source.Text.strip()
            if not employer:
                self.show_all(None)
                return
            where = "nombre LIKE '%{0}%' OR rfc LIKE '%{0}%'".format(employer)
            employers = self.db.select(
                ('empleados',), ('id','rfc', 'curp', 'nombre'), where, 'nombre')
            util.data_to_grid(self.grid_dm, employers)
            self._update_info(len(employers))
            self.dm.show_all.Enabled = True
        return

    def filter_employers_key_released(self, event):
        pass

    def grid_employers_mouse_pressed(self, event):
        if event.ClickCount == DOUBLE_CLICK:
            fil = self.grid.CurrentRow
            row_id = self.grid_dm.getCellData(0, fil)
            msg = 'Introduce el RFC correcto del empleado:\n\n{}'.format(
                self.grid_dm.getCellData(3, fil))
            box = input_box.Dlg(self, msg)
            while box.execute():
                ok, new_rfc = util.validate_rfc(self.value.upper())
                if ok:
                    if self._update_rfc(row_id, new_rfc):
                        self.grid_dm.updateCellData(1, fil, new_rfc)
                        msg = 'RFC actualizado correctamente'
                        util.msgbox(msg)
                        break
                else:
                    util.msgbox(new_rfc, TYPE_MSG['ERROR'])
        return

    def _update_rfc(self, employer_id, new_rfc):
        where = "rfc='{}'".format(new_rfc)
        rfc = self.db.select(('empleados',), ('id', 'nombre', 'rfc'), where)
        if rfc:
            if len(rfc) > 1:
                msg = 'CUIDADO: hay más de un empleado con este RFC'
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return False
            if rfc[0][0] != employer_id:
                msg = 'Este RFC es del empleado: {}'.format(rfc[0][1])
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return False
            if rfc[0][2] == new_rfc:
                return True
        where = 'id={}'.format(employer_id)
        return self.db.update('empleados', {'rfc': new_rfc}, where)

