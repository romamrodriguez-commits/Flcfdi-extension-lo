# -*- coding: utf-8 -*-

import traceback


class EventosAsignar(object):

    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.db = caller.db
        self.util = caller.util
        self.unogui = caller.unogui
        self.xml = caller.xml
        self.xml2 = caller.xml2
        #~ self.current_node = None
        self.code = False

    def cmdGuardar(self):
        grid = self.dialog.getControl('gridAsignaciones')
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            message = '¿Estás seguro de guardar los cambios en las ' \
                'asignaciones de esta Addenda?'
        else:
            message = 'No tienes asignaciones establecidas para esta Addenda ' \
                ', si guardas ahora, borraras cualquier asignación anterior' \
                '\n\n¿Estás seguro de continuar?'
        if self.unogui.createQuestion('FacturaLibre', message):
            try:
                fields = ('id_addenda', 'origen', 'destino', 'origen2', 'destino2')
                data = self.unogui.grid_to_tuple(grid.Model)
                self.db.delete('asignaciones', 'id_addenda=%s' % self.dm.lblAddenda.Tag)
                self.db.executemany('asignaciones', fields, data)
                self.dialog.endDialog(1)
            except:
                print(traceback.format_exc())
        return

    def cmdSalir(self):
        self.dialog.endDialog(0)
        return

    def gridAtributos_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount and not self.code:
            self.dm.chkValorNodo.State = 0
        return

    def gridAsignaciones_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            self.dm.cmdEliminar.Enabled = True
        return

    def treeFactura_selectionChanged(self, tree):
        try:
            sel = tree.getSelection()
            _,s = self._get_cadena(tree.getSelection(), [], [])
            if s:
                n = self._get_node(s, sel, self.xml)
                self._dict_to_list(n.attrib, self.dm.lstAtributosFactura)
        except:
            print(traceback.format_exc())
        return

    def treeAddenda_selectionChanged(self, tree):
        try:
            self.dm.chkValorNodo.State = 0
            sel = tree.getSelection()
            _,s = self._get_cadena(tree.getSelection(), [], [])
            if s:
                n = self._get_node(s, sel, self.xml2)
                if n.text:
                    if n.text.strip():
                        self.dm.lblValorNodo.Label = 'Nodo = %s' % n.text.strip()
                else:
                    self.dm.lblValorNodo.Label = 'Valor del nodo'
                self._make_grid(n.attrib)
        except:
            print(traceback.format_exc())
        return

    def chkValorNodo(self, chk):
        if chk.State:
            grid = self.dialog.getControl('gridAtributos')
            self.code = True
            grid.deselectAllRows()
            self.code = False
        return

    def _get_node(self, search, sel, xml):
        search.reverse()
        search[0] = '.'
        s = '/'.join(search)
        l = xml.doc.findall(s)
        if len(l) == 1:
            n = l[0]
        else:
            parent = sel.getParent()
            index = parent.getIndex(sel)
            n = l[index]
        return n

    def _make_grid(self, a):
        grid_dm = self.dm.gridAtributos.GridDataModel
        grid_dm.removeAllRows()
        co1 = 0
        for k,v in list(a.items()):
            row = (co1, k)
            self.unogui.gridAddRow(self.dm.gridAtributos, row)
            grid_dm.updateCellToolTip(1, co1, v)
            co1 += 1
        return

    def _get_cadena(self, node, t1=[], t2=[]):
        if node is None:
            return t1, t2
        t1.append(node.DisplayValue)
        t2.append(node.DataValue)
        if not node.getParent():
            return t1, t2
        padre = node.getParent()
        self._get_cadena(padre, t1, t2)
        return t1, t2

    def _dict_to_list(self, dic, lst):
        lst.StringItemList = tuple(sorted(dic.keys()))
        return

    def cmdAsignarNodo(self):
        try:
            lst = self.dialog.getControl('lstAtributosFactura')
            a1  = lst.getSelectedItem()
            if not a1:
                message = 'Selecciona un atributo de la factura'
                self.unogui.createMsgBox({'Message': message})
                return
            grid = self.dialog.getControl('gridAtributos')
            a2 = ''
            if not self.dm.chkValorNodo.State:
                #~ sel = grid.getSelection()
                row = grid.getCurrentRow()
                if row < 0:
                    message = 'Selecciona el nodo o atributo destino en la Addenda'
                    self.unogui.createMsgBox({'Message': message})
                    return
                grid_dm = grid.Model.GridDataModel
                a2 = grid_dm.getCellData(1, row)
            tree = self.dialog.getControl('treeFactura')
            sel = tree.getSelection()
            v1,s1 = self._get_cadena(sel, [], [])
            v1.reverse()
            v1[0] = '.'
            v1 = '/'.join(v1) + '+%s' % a1
            s1.reverse()
            s1[0] = '.'
            s1 = '/'.join(s1) + '+%s' % a1
            tree = self.dialog.getControl('treeAddenda')
            sel = tree.getSelection()
            v2,s2 = self._get_cadena(sel, [], [])
            v2.reverse()
            v2[0] = '.'
            v2 = '/'.join(v2) + '+%s' % a2
            s2.reverse()
            s2[0] = '.'
            s2 = '/'.join(s2) + '+%s' % a2

            row = ('', self.dm.lblAddenda.Tag, v1, v2, s1, s2)
            self.unogui.gridAddRow(self.dm.gridAsignaciones, row)
            self.dm.cmdEliminar.Enabled = True
        except:
            print (traceback.format_exc())
        return

    def cmdAsignarPersonalizado(self):
        lst = self.dialog.getControl('lstPersonalizados')
        a1  = lst.getSelectedItem()
        if not a1:
            message = 'Selecciona el campo personalizado a asignar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid = self.dialog.getControl('gridAtributos')
        a2 = ''
        if not self.dm.chkValorNodo.State:
            sel = grid.getSelection()
            if not sel:
                message = 'Selecciona el nodo o atributo destino en la Addenda'
                self.unogui.createMsgBox({'Message': message})
                return
            r = sel[0]
            grid_dm = grid.Model.GridDataModel
            a2 = grid_dm.getCellData(1, r)
        v1 = a1
        s1 = a1.replace(' ', '_').lower()
        tree = self.dialog.getControl('treeAddenda')
        sel = tree.getSelection()
        v2,s2 = self._get_cadena(sel, [], [])
        v2.reverse()
        v2[0] = '.'
        v2 = '/'.join(v2) + '+%s' % a2
        s2.reverse()
        s2[0] = '.'
        s2 = '/'.join(s2) + '+%s' % a2

        row = ('', self.dm.lblAddenda.Tag, v1, v2, s1, s2)
        self.unogui.gridAddRow(self.dm.gridAsignaciones, row)
        self.dm.cmdEliminar.Enabled = True
        return

    def cmdEliminar(self):
        grid = self.dialog.getControl('gridAsignaciones')
        #~ sel = grid.getSelection()
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        if row < 0:
            message = 'Selecciona una asignación a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        message = '¿Estás seguro de eliminar la asignación seleccionada?'
        if self.unogui.createQuestion('Factura Libre', message):
            grid_dm.removeRow(row)
        if not grid_dm.RowCount:
            self.dm.cmdEliminar.Enabled = False
        return
