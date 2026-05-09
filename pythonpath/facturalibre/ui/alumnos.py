#!
# -*- coding: utf-8 -*-
from .listenersalumnos import listener

DLG_NAME = 'dlgAlumnos.xdl'
ICON_GUARDAR='save.png'
ICON_SALIR = 'close.png'
ICON_AGREGAR = 'add.png'
ICON_ELIMINAR = 'delete.png'
ICON_CAMBIAR = 'refresh.png'


class Dlg(object):

    def __init__(self, caller):
        self.caller = caller
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.util = caller.util
        self.db = caller.db
        self.id_cliente = caller.id_cliente
        self.alumnos = caller.alumnos
        #~ self.niveles = {}
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config()
        self.listener.alumnos()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_GUARDAR)
        self.dm.cmdGuardar.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SALIR)
        self.dm.cmdSalir.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_AGREGAR)
        self.dm.cmdAgregar.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ELIMINAR)
        self.dm.cmdEliminar.ImageURL=img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_CAMBIAR)
        self.dm.cmdCambiarNivel.ImageURL=img_url

        self.dm.lblClave.Label = 'Nuevo'
        if self.id_cliente:
            self.dm.lblClave.Label = self.id_cliente
        self.dm.lblCliente.Label = self.caller.dm.nombre.Text

        data = self.db.select(('niveles',), ('nivel',))
        listbox = self.dialog.getControl('lstNivel')
        self.unogui.query_to_listbox(data, listbox)
        listbox.addItem('Selecciona un nivel', 0)
        listbox.selectItemPos(0, True)

        properties = {}
        properties['Name'] = 'gridAlumnos'
        properties['PositionX'] = 8
        properties['PositionY'] = 82
        properties['Width'] = 333
        properties['Height'] = 175
        properties['Step'] = 0
        properties['SelectionModel'] = 1
        columns=({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
        {'Title': u'Alumno', 'ColumnWidth': 150, 'HorizontalAlign': 0},
        {'Title': u'CURP', 'ColumnWidth':90,'HorizontalAlign': 0},
        {'Title': u'Nivel', 'ColumnWidth':60,'HorizontalAlign': 0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dm.gridAlumnos.RowHeaderWidth = 15
        if self.alumnos:
            self.unogui.gridAddRows(oGrid, self.alumnos)
        else:
            self.dm.cmdEliminar.Enabled = False
        self.unogui.centerDialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()
