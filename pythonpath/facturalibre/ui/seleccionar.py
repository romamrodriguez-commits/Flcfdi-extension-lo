#!
# -*- coding: utf-8 -*-
from .listenersadmin import listener
import traceback

DLG_NAME = 'dlgSeleccionar.xdl'
ICON_ACEPTAR = 'icon05.png'
ICON_CANCELAR = 'cancelar.png'


class Dlg(object):
    def __init__(self, caller, values):
        self.caller = caller
        self.unogui = caller.unogui
        self.globales = caller.globales
        self.db = caller.db
        self.unogui = caller.unogui
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'], DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config(values)
        self.listener.seleccionar()

    def __config(self, value):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_ACEPTAR)
        self.dm.cmdAceptar.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_CANCELAR)
        self.dm.cmdCancelar.ImageURL = img_url
        if isinstance(value, str) or isinstance(value, int):
            self.dialog.getControl('txtPrimero').Text = value
        self.dialog.Title = 'Seleccionar producto'
        
        properties = {}
        properties['Name'] = 'gridProductos'
        properties['PositionX'] = 6
        properties['PositionY'] = 20
        properties['Width'] = 218
        properties['Height'] = 174
        properties['Step'] = 3
        properties['SelectionModel'] = 1
        columns=({'Title':'id','ColumnWidth':0,'HorizontalAlign':1},
        {'Title': 'Clave','ColumnWidth':50,'HorizontalAlign':1},
        {'Title': 'Descripción','ColumnWidth':150,'HorizontalAlign':0})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        
        grid = self.dialog.getControl('gridProductos')
        grid.setVisible(True)
        if not value:
            where = ''
        else:
            where = "noIdentificacion LIKE '%" + \
                    value + "%' OR descripcion LIKE '%" + value + "%'"
        productos = self.db.select(('productos',),
                                    ('id', 'noIdentificacion', 'descripcion'),
                                    where, 'descripcion')
        self.unogui.gridAddRows(self.dm.gridProductos, productos)
        
        self.unogui.centerDialog(self.dialog)
        return

    def execute(self):
        return self.dialog.execute()
