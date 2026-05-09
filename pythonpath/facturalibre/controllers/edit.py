# -*- coding: utf-8 -*-

from facturalibre.modulos.util import catch_exception


class EventosEditAdd(object):

    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog
        self.db = caller.db
        self.util = caller.util
        self.unogui = caller.unogui
        self.xml = caller.xml
        self.dm = self.dialog.getModel()
        self.current_node = None

    def cmdGuardar(self):
        try:
            msg = '¿Estás seguro de guardar los cambios en la addenda?\n\n' \
                'Si hiciste cambios en nodos o atributos de esta addenda y ' \
                'esta ya ha sido asignada a algún emisor, tienes que revisar ' \
                'la asignación de datos en estos campos'
            if self.unogui.createQuestion('FacturaLibre', msg):
                a = self.xml.tostring()

                self.db.update('addendas',
                                {'addenda': a},
                                'id=%s' % self.dm.lblAddenda.Tag)
                self.dialog.endDialog(1)
        except:
            print (traceback.format_exc())
        return

    def cmdSalir(self):
        self.dialog.endDialog(0)
        return

    def gridAtributos_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            self.dm.cmdEliminarAtributo.Enabled = True
            self.dm.cmdActualizarAtributo.Enabled = True
            row = grid.getCurrentRow()
            self.dm.txtAtributo.Tag = ''
            if row >= 0:
                self.dm.txtAtributo.Tag = grid_dm.getCellData(1, row)
        return

    def treeAddenda_selectionChanged(self, tree):
        try:
            sel = tree.getSelection()
            self._is_root(sel)
            s = self.get_cadena(tree.getSelection(), [])
            if s:
                self.dm.txtValor.Text = ''
                n = self._get_node(s, sel)
                if n.text is not None:
                    self.dm.txtValor.Text = n.text.strip()
                self.make_grid(n.attrib)
                self.current_node = n
        except:
            print(traceback.format_exc())
        return

    def _is_root(self, s):
        if s is not None:
            if s.DataValue:
                self.dm.cmdEliminarNodo.Enabled = False
                self.dm.cmdActualizarNodo.Enabled = False
            else:
                self.dm.cmdEliminarNodo.Enabled = True
                self.dm.cmdActualizarNodo.Enabled = True
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

    def make_grid(self, a):
        self.dm.cmdEliminarAtributo.Enabled = False
        self.dm.cmdActualizarAtributo.Enabled = False
        rows = []
        for k,v in list(a.items()):
            rows.append(('', k, v))
        self.unogui.gridAddRows(self.dm.gridAtributos, rows)
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

    def cmdAgregarNodo(self):
        txt = self.dialog.getControl('txtNodo')
        if self.unogui.validate(txt, 'Vacio'):
            message = 'El nombre del NODO no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txt.setFocus()
            return
        try:
            self.xml.add_node(self.current_node, txt.Text)
            self._tree_add_node(txt.Text)
        except:
            print(traceback.format_exc())
        else:
            txt.Text = ''
        return

    def cmdEliminarNodo(self):
        tree = self.dialog.getControl('treeAddenda')
        sel = tree.getSelection()
        message = '¿Estas seguro de eliminar el nodo: %s?' % sel.getDisplayValue()
        try:
            if self.unogui.createQuestion('FacturaLibre', message):
                self.xml.delete_node(self.current_node)
                self._tree_delete_node()
        except:
            print(traceback.format_exc())
        return

    def cmdActualizarNodo(self):
        txt = self.dialog.getControl('txtNodo')
        if self.unogui.validate(txt, 'Vacio'):
            message = 'El nombre del NODO a actualizar no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txt.setFocus()
            return
        tree = self.dialog.getControl('treeAddenda')
        sel = tree.getSelection()
        n = sel.getDisplayValue()
        message = '¿Estás seguro de actualizar el nodo: %s?' % n
        if self.unogui.createQuestion('FacturaLibre', message):
            n = txt.Text.replace(' ','')
            sel.setDisplayValue(n)
            self.current_node.tag = n
            txt.Text = ''
        return

    def cmdAgregarAtributo(self):
        txt1 = self.dialog.getControl('txtAtributo')
        if self.unogui.validate(txt1, 'Vacio'):
            message = 'El nombre del nuevo atributo no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txt1.setFocus()
            return
        txt2 = self.dialog.getControl('txtValorAtributo')
        if self.unogui.validate(txt2, 'Vacio'):
            message = 'El valor del nuevo atributo no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txt2.setFocus()
            return
        self.current_node.set(txt1.Text, txt2.Text)
        self.make_grid(self.current_node.attrib)
        txt1.Text = ''
        txt2.Text = ''
        return

    def cmdEliminarAtributo(self):
        a = self.dm.txtAtributo.Tag
        if not a:
            message = 'Selecciona el atributo a eliminar'
            self.unogui.createMsgBox({'Message': message})
            self.dialog.getControl('txtAtributo').setFocus()
            return
        message = '¿Estás seguro de eliminar el atributo: %s?' % a
        if self.unogui.createQuestion('FacturaLibre', message):
            del(self.current_node.attrib[a])
            self.make_grid(self.current_node.attrib)
            self.dm.txtAtributo.Tag = ''
            self.dm.txtAtributo.Text = ''
            self.dm.txtValorAtributo.Text = ''
        return

    def cmdActualizarAtributo(self):
        txt = self.dialog.getControl('txtValorAtributo')
        message = 'El valor del atributo a actualizar esta vacío. Asegurate ' \
            'de asignarle un valor por que no puede haber atributos vacios'
        self.unogui.createMsgBox({'Message': message})
        a = self.dm.txtAtributo.Tag
        message = '¿Estás seguro de actualizar el atributo: %s?' % a
        if self.unogui.createQuestion('FacturaLibre', message):
            self.current_node.set(a, txt.Text)
            self.make_grid(self.current_node.attrib)
            txt.Text = ''
        return

    def cmdActualizarValor(self):
        tree = self.dialog.getControl('treeAddenda')
        sel = tree.getSelection()
        n = sel.getDisplayValue()
        message = '¿Estás seguro de actualizar el valor del nodo: %s?' % n
        if self.unogui.createQuestion('FacturaLibre', message):
            self.current_node.text = self.dm.txtValor.Text.strip()
        return

    def _tree_add_node(self, name):
        tree = self.dialog.getControl('treeAddenda')
        tree_dm = self.dm.treeAddenda.DataModel
        hijo = tree_dm.createNode(name, False)
        padre = tree.getSelection()
        padre.appendChild(hijo)
        tree.expandNode(padre)
        return

    def _tree_delete_node(self):
        tree = self.dialog.getControl('treeAddenda')
        sel = tree.getSelection()
        parent = sel.getParent()
        parent.removeChildByIndex(parent.getIndex(sel))
        return
