# -*- coding: utf-8 -*-

from facturalibre.settings import TYPE_MSG, NIVELES_IEDU, BUTTON_CLICK
from facturalibre.modulos import util


class NivelesEvents(object):

    def __init__(self, dialog, db):
        self.dialog = dialog
        self.db = db
        self._vars()

    def _vars(self):
        self.dm = self.dialog.getModel()
        self.nivel = self.dialog.getControl('txtNivel')
        self.auth = self.dialog.getControl('txtAutorizacion')
        self.grid = self.dialog.getControl('gridNiveles')
        self.grid_dm = self.dm.gridNiveles.GridDataModel
        return

    def cmdAgregar(self, event):
        if util.validate(self.nivel):
            msg = 'El campo NIVEL no puede estar vacío.'
            self.nivel.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return
        data = self.db.select(
            ('niveles',), ('nivel',), "nivel='{}'".format(self.nivel.Text))
        if data:
            msg = 'Este NIVEL ya se agrego a la lista'
            self.nivel.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return
        if not self.nivel.Text in NIVELES_IEDU:
            msg = 'El nivel capturado NO esta en la lista valida para el SAT:' \
                '\n\n{}\n\nSi capturas un valor que no sea de esta lista, NO ' \
                'puedes agregar el campo Autorizacion. ¿Deseas continuar?\n\n' \
                'Si respondes que Si el campo Autorizacion será borrado'.format(
                '\n'.join(NIVELES_IEDU))
            if util.question(msg) == BUTTON_CLICK['NO']:
                return
            self.auth.Text = ''
        if util.validate(self.auth):
            msg = 'El campo AUTORIZACION esta vacío.\n\n ¿Estás seguro de ' \
                'dejarlo así?\n\nRecuerda que es un dato obligatorio para ' \
                'los niveles incorporados'
            if util.question(msg) == BUTTON_CLICK['NO']:
                self.auth.setFocus()
                return ''
        new_nivel = {
            'nivel': self.nivel.Text,
            'autorizacion': self.auth.Text
        }
        self.db.insertrow('niveles', new_nivel)
        data = self.db.select(('niveles',), order='nivel')
        util.data_to_grid(self.grid_dm, data, True)
        self.nivel.Text = ''
        self.auth.Text = ''
        self.nivel.setFocus()
        return

    def cmdEliminar(self, event):
        row = self.grid.CurrentRow
        if row == -1:
            msg = 'Selecciona el nivel a eliminar'
            util.msgbox(msg)
            return
        id_nivel = self.grid_dm.getCellData(0, row)
        nivel = self.grid_dm.getCellData(1, row)
        alumno = self.db.select(
            ('alumnos',), ('id',), 'id_nivel={}'.format(id_nivel))
        if alumno:
            msg = 'Tienes alumnos usando este nivel, primero cambia de ' \
                'nivel a estos alumnos'
            util.msgbox(msg)
            return
        msg = '¿Estás seguro de eliminar el siguiente?\n\n{}\n\nEsta ' \
            'acción no se puede deshacer'.format(nivel)
        if util.question(msg) == BUTTON_CLICK['NO']:
            return
        self.db.delete('niveles', 'id={}'.format(id_nivel))
        data = self.db.select(('niveles',), order='nivel')
        util.data_to_grid(self.grid_dm, data, True)
        self.nivel.setFocus()
        return

