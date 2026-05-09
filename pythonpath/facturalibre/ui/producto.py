# -*- coding: utf-8 -*-

import logging
from facturalibre.settings import TITLE, LOG, ICONS
from facturalibre.modulos import util
from facturalibre.ui.pyUnoGui import UnoGui


log = logging.getLogger(LOG['NAME'])


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, db, edit=False, id_producto=0):
        #~ self.caller = caller
        #~ self.globales = caller.globales
        #~ self.unogui = caller.unogui
        #~ self.util = caller.util
        self.unogui = UnoGui()
        self.db = db
        self.edit = edit
        self.id_producto = id_producto
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.Model
        self._config()

    def _config(self):
        from .listeners import Listener

        img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.dm.cmdMostrarCategorias.ImageURL = img_url.format(ICONS['DOWN'])
        self.dm.cmdAgregarCategoria.ImageURL = img_url.format(ICONS['ADD'])
        self.dm.cmdLimpiarSeleccion.ImageURL = img_url.format(ICONS['CLEAN'])
        self.dm.cmdGuardar.ImageURL = img_url.format(ICONS['SAVE'])
        self.dm.cmdSalir.ImageURL = img_url.format(ICONS['CLOSE'])

        #~ Ocultamos la calculadora de impuesto hasta nuevo aviso
        self.dialog.getControl('Label6').setVisible(False)
        self.dialog.getControl('cantidad').setVisible(False)
        self.dialog.getControl('Label8').setVisible(False)
        self.dialog.getControl('total').setVisible(False)

        tree = self.dialog.getControl('treeCategorias')
        tree.setVisible(False)
        select = getattr(self.db, 'select')
        self.unogui.query_to_tree(tree, 'categorias', select)
        #~ parents = self.db.select(
            #~ ('categorias',), ('DISTINCT id_padre',), order='id_padre')
        #~ util.query_to_tree(tree, parents)

        data = self.db.select(('unidades',), ('unidad',))
        combo = self.dialog.getControl('unidad')
        #~ self.unogui.query_to_listbox(data, combo)
        util.query_to_listbox(data, combo)

        self.decimales = self.db.select_field('opciones', 'decimales')
        self.dm.valorUnitario.DecimalAccuracy = self.decimales
        self.dm.cantidad.DecimalAccuracy = self.decimales
        self.dm.total.DecimalAccuracy = self.decimales
        incluye_iva = bool(self.db.select_field('opciones', 'opcion1'))
        self.dialog.getControl('lblIva').setVisible(incluye_iva)
        mostrar = bool(self.db.select_field('opciones2', 'opcion1'))
        self.dialog.getControl('lblcodigobarras').setVisible(mostrar)
        self.dialog.getControl('codigobarras').setVisible(mostrar)
        mostrar = bool(self.db.select_field('opciones2', 'opcion2'))
        self.dialog.getControl('lblCuentaPredial').setVisible(mostrar)
        self.dialog.getControl('chkCuentaPredial').setVisible(mostrar)
        self.dialog.getControl('CuentaPredial').setVisible(mostrar)

        properties = {}
        properties['Name'] = 'gridImpuestos'
        properties['PositionX'] = 54
        properties['PositionY'] = 125
        properties['Width'] = 150
        properties['Height'] = 60
        properties['Step'] = 0
        properties['SelectionModel'] = 2
        columns=({'Title':'id','ColumnWidth':0,'HorizontalAlign':1},
        {'Title':'Impuesto','ColumnWidth':35,'HorizontalAlign':1},
        {'Title':'Tasa','ColumnWidth':40,'HorizontalAlign':1},
        {'Title':'Tipo','ColumnWidth':45,'HorizontalAlign':1})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)

        data = self.db.select(('impuestos',))
        if data:
            self.unogui.gridAddRows(oGrid, data)
        #~ Ocultamos la calculadora de impuestos hasta nuevo aviso
            #~ properties = {}
            #~ properties['Name'] = 'gridTotales'
            #~ properties['PositionX'] = 233
            #~ properties['PositionY'] = 115
            #~ properties['Width'] = 110
            #~ properties['Height'] = 60
            #~ properties['Step'] = 0
            #~ properties['SelectionModel'] = 0
            #~ columns = ({'Title': 'id', 'ColumnWidth': 0, 'HorizontalAlign': 2},
            #~ {'Title': 'Impuesto', 'ColumnWidth': 39, 'HorizontalAlign': 2},
            #~ {'Title': 'Importe', 'ColumnWidth': 53, 'HorizontalAlign': 2})
            #~ oGrid = self.unogui.createGrid(self.dialog, columns, properties)
            #~ data2 = []
            #~ for row in data:
                #~ data2.append((row[0], '%s %s' % (row[1], row[2]), '0.00'))
            #~ self.unogui.gridAddRows(oGrid, data2)

        if self.edit:
            title = '{} - Editar Producto o Servicio '.format(TITLE)
            producto = self.db.select(
                ('productos',), where='id={}'.format(self.id_producto))[0]
            self.dm.id.Label = self.id_producto
            self.dm.categoria.Tag = producto[1]
            id_categoria = producto[1]
            self.dm.noIdentificacion.Text = producto[2]
            self.dm.noIdentificacion.Tag = producto[2]
            self.dm.descripcion.Text = producto[3]
            self.dm.unidad.Text = producto[4]
            self.dm.valorUnitario.Value = producto[5]
            self.dm.existencia.Value = producto[6]
            self.dm.chkInventario.State = producto[7]
            self.dm.codigobarras.Text = producto[8]
            self.dm.CuentaPredial.Text = producto[9]
            impuestos = self.db.select(
                ('productosimpuestos',),
                ('id_impuesto',),
                'id_producto={}'.format(self.id_producto))
            if impuestos:
                self._selectRows(
                    self.dialog.getControl('gridImpuestos'), impuestos)
            self._getCategorias(id_categoria)
        else:
            title = '{} - Nuevo Producto o Servicio '.format(TITLE)
            self.dm.id.Label = '<Nuevo>'
            data = self.db.select(
                ('productos',),
                ('MAX(CAST(noIdentificacion AS UNSIGNED))+1',))[0][0]
            if not data:
                data = 1
            self.dm.noIdentificacion.Text = str(data)
            id_unidad = self.db.select_field('opciones','id_unidad')
            if id_unidad:
                unidad = self.db.select(
                    ('unidades',), ('unidad',), 'id={}'.format(id_unidad))
                if unidad:
                    self.dm.unidad.Text = unidad[0][0]
            id_impuesto = self.db.select_field('opciones','id_impuesto')
            if id_impuesto:
                self.unogui.selectRow(
                    self.dialog.getControl('gridImpuestos'),id_impuesto)

        self.dm.existencia.Enabled=self.dm.chkInventario.State

        self.dialog.Title = title
        self.dialog.getControl('categoria').setFocus()

        listener = Listener(self.dialog, self.db)
        listener.producto(self.edit, self.id_producto)
        return

    def execute(self):
        return self.dialog.execute()

    def _selectRows(self,grid,query):
        grid_dm = grid.Model.GridDataModel
        impuestos = []
        for row in query:
            impuestos.append(row[0])
        for row in range(grid_dm.RowCount):
            if grid_dm.getCellData(0,row) in impuestos:
                grid.selectRow(row)
        return

    def _getCategorias(self, id_categoria):
        if not id_categoria:
            return
        cat = []
        continuar = True
        while continuar:
            data = self.db.select(('categorias',),('categoria','id_padre',),'id=%s'%id_categoria)[0]
            cat.insert(0,data[0])
            if data[1]:
                id_categoria=data[1]
            else:
                continuar = False
        self.dm.categoria.Text='|'.join(cat)
        return
