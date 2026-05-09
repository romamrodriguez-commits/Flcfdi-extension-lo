#!
# -*- coding: utf-8 -*-

import traceback

KEY_RETURN = 1280
KEY_TAB = 1282

class EventosSeleccionar(object):
    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.unogui = caller.unogui
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()

    def cmdAceptar(self):
        txt = self.dialog.getControl('txtPrimero')
        self.caller.unogui.validate(txt, 'Vacio')
        self.caller.caller.codigo = txt.Text
        self.dialog.endDialog(1)
        return 
        
    def cmdCancelar(self):
        self.dialog.endDialog(0)
        return

    def txtPrimero_keyReleased(self, event):
        try:
            codigo = event.Source.Text.strip().replace('|','')
            if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
                grid = self.dialog.getControl('gridProductos')
                grid.setVisible(True)
                if not codigo:
                    grid.setVisible(False)
                    return
                where = "noIdentificacion LIKE '%" + \
                        codigo + "%' OR descripcion LIKE '%" + codigo + "%'"
                productos = self.db.select(('productos',),
                                            ('id', 'noIdentificacion', 'descripcion'),
                                            where, 'noIdentificacion')
                self.unogui.gridAddRows(self.dm.gridProductos, productos)
            return
        except:
            print (traceback.format_exc())

    def txtSegundo_keyReleased(self, event):
        try:
            codigo = event.Source.Text.strip().replace('|','')
            if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
                grid = self.dialog.getControl('gridProductos')
                grid.setVisible(True)
                if not codigo:
                    where = ''
                else:
                    where = "noIdentificacion LIKE '%" + \
                            codigo + "%' OR descripcion LIKE '%" + codigo + "%'"
                productos = self.db.select(('productos',),
                                            ('id', 'noIdentificacion', 'descripcion'),
                                            where, 'descripcion')
                self.unogui.gridAddRows(self.dm.gridProductos, productos)
            return
        except:
            print (traceback.format_exc())

    def gridProductos_selectionChanged(self, grid):
        try:
            grid_dm = grid.Model.GridDataModel
            if grid.isVisible():
                if grid_dm.RowCount:
                    row = grid.CurrentRow
                    self.dm.txtPrimero.Text = grid_dm.getCellData(1,row)
                    self.dm.txtSegundo.Text = grid_dm.getCellData(2,row)
            return
        except:
            print (traceback.format_exc())














