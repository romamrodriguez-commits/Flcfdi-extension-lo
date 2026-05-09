# -*- coding: utf-8 -*-

from .listenersadmin import listener


DLG_NAME = 'dlgAsignar.xdl'
ICON_GUARDAR = 'save.png'
ICON_SALIR = 'close.png'
ICON_AGREGAR = 'add.png'
ICON_ELIMINAR = 'delete.png'


class Dlg(object):

    def __init__(self, caller, *values):
        self.caller = caller
        self.unogui = caller.unogui
        self.db = caller.db
        self.globales = caller.globales
        self.util = caller.util
        self.id_addenda = values[0]
        self.name_addenda = values[1]
        self.xml = None
        self.xml2 = None
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config()
        self.listener.asignar()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_GUARDAR)
        self.dm.cmdGuardar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SALIR)
        self.dm.cmdSalir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_AGREGAR)
        self.dm.cmdAsignarNodo.ImageURL = img_url
        self.dm.cmdAsignarPersonalizado.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ELIMINAR)
        self.dm.cmdEliminar.ImageURL = img_url
        self.dialog.Title = '%s - Asignar Campos en Addenda' % self.globales['APP_TITULO']

        properties = {}
        properties['Name'] = 'gridAtributos'
        properties['PositionX'] = 288
        properties['PositionY'] = 30
        properties['Width'] = 80
        properties['Height'] = 122
        properties['SelectionModel'] = 1
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Atributos', 'ColumnWidth': 65, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)

        properties = {}
        properties['Name'] = 'gridAsignaciones'
        properties['PositionX'] = 3
        properties['PositionY'] = 162
        properties['Width'] = 282
        properties['Height'] = 85
        properties['SelectionModel'] = 1
        columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'id_addenda', 'ColumnWidth': 0, 'HorizontalAlign': 0},
        {'Title': 'Nodo Origen', 'ColumnWidth': 100, 'HorizontalAlign': 0},
        {'Title': 'Nodo Destino', 'ColumnWidth': 160, 'HorizontalAlign': 0},
        {'Title': 'Origen', 'ColumnWidth': 0, 'HorizontalAlign': 0},
        {'Title': 'Destino', 'ColumnWidth': 0, 'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        data = self.db.select(('asignaciones',),
                                    where='id_addenda=%s' % self.id_addenda)
        if data:
            self.unogui.gridAddRows(oGrid, data)
        self.dm.lblAddenda.Tag = self.id_addenda
        self.dm.lblAddenda.Label = 'Addenda: %s' % self.name_addenda
        data = self.db.select(('addendas',), where='id=%s' % self.id_addenda)
        tree = self.dialog.getControl('treeAddenda')
        self.addenda_to_tree(tree, data[0][2])

        tree = self.dialog.getControl('treeFactura')
        self.xml_to_tree(tree)

        data = self.db.select(('campospersonalizados',), ('campo',), order='campo')
        data = [r[0] for r in data]
        if data:
            lst = self.dm.lstPersonalizados
            lst.StringItemList = tuple(data)
        else:
            self.dm.cmdAsignarPersonalizado.Enabled = False
        self.dm.cmdEliminar.Enabled = False
        return

    def execute(self):
        return self.dialog.execute()

    def addenda_to_tree(self, tree, xml):
        from facturalibre.modulos.pyXml import ASIGNARADDENDA

        edit = ASIGNARADDENDA()
        path = self.util.getPathTemp()
        self.util.save_file(path, xml)
        edit.parse(path)
        self.xml2 = edit
        tag = edit.doc.tag.split("}")[-1]
        tree_dm = self.unogui.addTreeDataModel(tree, tag)
        tree_dm.Root.DataValue = 1
        exp = getattr(tree, 'expandNode')
        self.make_tree(exp, tree_dm, tree_dm.Root, edit.doc, self.xml2)
        return

    def xml_to_tree(self, tree):
        from facturalibre.modulos.pyXml import ASIGNARADDENDA

        path = '%s/bin/factura.xml' % self.globales['EXT_PATH']
        #~ xml = self.util.load_file(self.util.urlToSystem(path))
        edit = ASIGNARADDENDA()
        edit.parse(self.util.urlToSystem(path))
        self.xml = edit
        tag = edit.doc.tag.split("}")[-1]
        tree_dm = self.unogui.addTreeDataModel(tree, tag)
        #~ tree_dm.Root.DataValue = edit.raizData
        exp = getattr(tree, 'expandNode')
        self.make_tree(exp, tree_dm, tree_dm.Root, edit.doc, self.xml)
        return

    def make_tree(self, exp, tree, padre, nodo, xml):
        if nodo is None:
            return
        if not nodo.getchildren():
            return
        for child in nodo:
            tag = child.tag.split("}")[-1]
            #~ name = xml.get_namespace(child.tag)
            hijo = tree.createNode(tag, False)
            hijo.DataValue = child.tag
            padre.appendChild(hijo)
            self.make_tree(exp, tree, hijo, child, xml)
        exp(padre)
        return
