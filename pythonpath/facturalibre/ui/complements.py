# -*- coding: utf-8 -*-

from facturalibre.modulos.pyXml import XMLComplement
from facturalibre.settings import TITLE, ICONS
from facturalibre.modulos import util


class Complements(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.db = caller.db
        self.unogui = caller.unogui
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.getModel()
        self.xml = None
        self._config()

    def _config(self):
        from .listeners import Listener

        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmd_save.ImageURL = img_url.format(ICONS['OK'])
        self.dm.cmd_close.ImageURL = img_url.format(ICONS['CANCEL'])

        properties = {}
        properties['Name'] = 'grid'
        properties['PositionX'] = 180
        properties['PositionY'] = 56
        properties['Width'] = 165
        properties['Height'] = 165
        properties['SelectionModel'] = 1
        columns = (
            {'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 1},
            {'Title': 'Atributo', 'ColumnWidth': 70, 'HorizontalAlign': 2},
            {'Title': 'Valor', 'ColumnWidth': 80, 'HorizontalAlign': 0}
        )
        grid = util.create_grid(self.dialog, columns, properties)

        where = "code_name='{}'".format('ine')
        data = self.db.select(('complements',), where=where)[0]
        self.dm.label_complement.Label = data[1]
        tree = self.dialog.getControl('tree_complement')
        self.xml_to_tree(tree, data[3])

        listener = Listener(self.dialog)
        listener.complements(self)

        self.dialog.Title = '{} - Complementos'.format(TITLE)
        util.center_dialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()

    def xml_to_tree(self, tree, xml):
        edit = XMLComplement()
        path = util.get_path_temp()
        util.save_file(path, xml)
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