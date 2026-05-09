# -*- coding: utf-8 -*-

import logging
from facturalibre.modulos import util
from facturalibre.settings import LOG


log = logging.getLogger(LOG['NAME'])


class ComplementsEvents(object):

    def __init__(self, dialog, caller):
        self.dialog = dialog
        self.caller = caller
        self.unogui = caller.unogui
        self.xml = caller.xml
        self.dm = self.dialog.getModel()
        self.tree = self.dialog.getControl('tree_complement')
        self.grid = self.dialog.getControl('grid')
        self.lst_values = self.dialog.getControl('lst_values')
        self.gdm = self.dm.grid.GridDataModel
        self.make_grid()

    def cmd_save(self, event):
        data = {self.gdm.getCellData(1, i): self.gdm.getCellData(2, i) for i in range(3)}
        t = sum([bool(r) for r in data.values()])
        if t == 0 or t == 3:
            if t == 3:
                value = data['IdContabilidad']
                try:
                    value = int(value)
                except ValueError:
                    msg = 'El ID de Contabilidad debe ser un número'
                    self.unogui.createMsgBox({'Message': msg})
                    return
            else:
                data = {}
            self.caller.caller.complement = data
            self.dialog.endDialog(1)
        else:
            msg = 'Es necesario capturar los tres valores'
            self.unogui.createMsgBox({'Message': msg})
        return

    def cmd_close(self, event):
        self.dialog.endDialog(0)
        return

    def attribute_value_text_changed(self, event):
        row = self.grid.CurrentRow
        if row < 0:
            return
        self.gdm.updateCellData(2, row, self.dm.attribute_value.Text.strip())
        return

    def lst_values_selection_changed(self, event):
        row = self.grid.CurrentRow
        if row < 0:
            return
        self.gdm.updateCellData(2, row, self.lst_values.SelectedItem)
        return

    def grid_selection_changed(self, event):
        self.dm.attribute_value.Text = ''
        row = self.grid.CurrentRow
        if row < 0:
            return

        value = self.gdm.getCellData(1, row)
        if value == 'IdContabilidad':
            self.unogui.setVisible(self.dialog, 'attribute_value')
            self.unogui.setVisible(self.dialog, 'lst_values', False)
        else:
            self.unogui.setVisible(self.dialog, 'attribute_value', False)
            self.unogui.setVisible(self.dialog, 'lst_values')
            values = ('Ordinario', 'Precampaña', 'Campaña')
            if value == 'TipoComite':
                values = ('Ejecutivo Nacional', 'Ejecutivo Estatal')
            self.lst_values.Model.StringItemList = values
        return

    def grid_mouse_pressed(self, event):
        if event.ClickCount == 2:
            row = self.grid.CurrentRow
            self.gdm.updateCellData(2, row, '')
        return

    def tree_complement_selection_changed(self, event):
        #~ try:
            #~ sel = self.tree.getSelection()
            #~ self._is_root(sel)
            #~ s = self.get_cadena(self.tree.getSelection(), [])
            #~ if s:
                #~ self.dm.attribute_value.Text = ''
                #~ n = self._get_node(s, sel)
                #~ if n.text is not None:
                    #~ self.dm.attribute_value.Text = n.text.strip()
                #~ self.make_grid(n.attrib)
                #~ self.current_node = n
        #~ except Exception as e:
            #~ log.error(e, exc_info=True)
        return

    def _is_root(self, s):
        #~ if s is not None:
            #~ if s.DataValue:
                #~ self.dm.cmdEliminarNodo.Enabled = False
                #~ self.dm.cmdActualizarNodo.Enabled = False
            #~ else:
                #~ self.dm.cmdEliminarNodo.Enabled = True
                #~ self.dm.cmdActualizarNodo.Enabled = True
        return

    def _get_node(self, search, sel):
        search.reverse()
        search[0] = '.'
        s = '/'.join(search)
        l = self.xml.doc.findall(s)
        if len(l) == 1:
            n = l[0]
        else:
            parent = sel.getParent()
            index = parent.getIndex(sel)
            n = l[index]
        return n

    def make_grid(self, a={}):
        a = {'TipoProceso': '', 'TipoComite': '', 'IdContabilidad': ''}
        if self.caller.caller.complement:
            a = self.caller.caller.complement
        rows = []
        for k,v in list(a.items()):
            rows.append(('', k, v))
        self.unogui.gridAddRows(self.grid.Model, rows)
        return

    def get_cadena(self, node, t=[]):
        if node is None:
            return t
        #~ t.append(node.getDisplayValue())
        t.append(node.DataValue)
        if not node.getParent():
            return t
        padre = node.getParent()
        self.get_cadena(padre, t)
        return t
