# -*- coding: utf-8 -*-

from .listenersadmin import listener


DLG_NAME = 'dlgEdit.xdl'
ICON_GUARDAR = 'save.png'
ICON_SALIR = 'close.png'
ICON_AGREGAR = 'add.png'
ICON_ELIMINAR = 'delete.png'
ICON_ACTUALIZAR = 'refresh.png'


class Dlg(object):

    def __init__(self, caller, id_addenda):
        self.caller = caller
        self.unogui = caller.unogui
        self.db = caller.db
        self.globales = caller.globales
        self.util = caller.util
        self.id_addenda = id_addenda
        self.xml = None
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config()
        self.listener.edit_add()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_GUARDAR)
        self.dm.cmdGuardar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SALIR)
        self.dm.cmdSalir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_AGREGAR)
        self.dm.cmdAgregarNodo.ImageURL = img_url
        self.dm.cmdAgregarAtributo.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ELIMINAR)
        self.dm.cmdEliminarNodo.ImageURL = img_url
        self.dm.cmdEliminarAtributo.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ACTUALIZAR)
        self.dm.cmdActualizarNodo.ImageURL = img_url
        self.dm.cmdActualizarValor.ImageURL = img_url
        self.dm.cmdActualizarAtributo.ImageURL = img_url
        self.dialog.Title = '%s - Editar Addenda' % self.globales['APP_TITULO']

        properties = {}
        properties['Name'] = 'gridAtributos'
        properties['PositionX'] = 180
        properties['PositionY'] = 56
        properties['Width'] = 165
        properties['Height'] = 165
        properties['SelectionModel'] = 1
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Atributo', 'ColumnWidth': 70, 'HorizontalAlign': 2},
        {'Title': 'Valor', 'ColumnWidth': 80, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)

        data = self.db.select(('addendas',), where='id=%s' % self.id_addenda)
        self.dm.lblAddenda.Tag = self.id_addenda
        self.dm.lblAddenda.Label = data[0][1]
        tree = self.dialog.getControl('treeAddenda')
        self.xml_to_tree(tree, data[0][2])
        self.dm.cmdEliminarAtributo.Enabled = False
        self.dm.cmdActualizarAtributo.Enabled = False
        return

    def execute(self):
        return self.dialog.execute()

    def xml_to_tree(self, tree, xml):
        from facturalibre.modulos.pyXml import EDITADDENDA

        edit = EDITADDENDA()
        path = self.util.getPathTemp()
        self.util.save_file(path, xml)
        edit.parse(path)
        tag = edit.doc.tag.split("}")[-1]
        tree_dm = self.unogui.addTreeDataModel(tree, tag)
        tree_dm.Root.DataValue = 1
        exp = getattr(tree, 'expandNode')
        self.make_tree(exp, tree_dm, tree_dm.Root, edit.doc)
        self.xml = edit
        return

    def make_tree(self, exp, tree, padre, nodo):
        if nodo is None:
            return
        if not nodo.getchildren():
            return
        for child in nodo:
            tag = child.tag.split("}")[-1]
            hijo = tree.createNode(tag, False)
            hijo.DataValue = child.tag
            padre.appendChild(hijo)
            self.make_tree(exp, tree, hijo, child)
        exp(padre)
        return
