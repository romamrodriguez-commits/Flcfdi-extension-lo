# -*- coding: utf-8 -*-

import logging
from facturalibre.settings import LOG, BUTTON_CLICK, TYPE_MSG
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class ProductoEvents(object):

    def __init__(self, dialog, db, edit, id_producto):
        self.dialog = dialog
        self.db = db
        self.edit = edit
        self.id_producto = id_producto
        self._init_vars()

    def _init_vars(self):
        self.dm = self.dialog.getModel()
        self.clave = self.dialog.getControl('noIdentificacion')
        self.existencia = self.dialog.getControl('existencia')
        self.predial = self.dialog.getControl('CuentaPredial')
        self.tree = self.dialog.getControl('treeCategorias')
        self.descripcion = self.dialog.getControl('descripcion')
        self.categoria = self.dialog.getControl('categoria')
        self.grid = self.dialog.getControl('gridImpuestos')
        self.grid_dm = self.grid.Model.GridDataModel
        self.unidad = self.dialog.getControl('unidad')
        self.price = self.dialog.getControl('valorUnitario')
        self.code_bar = self.dialog.getControl('codigobarras')
        return

    def cmdLimpiarSeleccion(self, event):
        self.grid.deselectAllRows()
        return

    def cmdSalir(self, event):
        self.dialog.endExecute()
        return

    def chkAutomatica(self, event):
        source = event.Source
        new = False
        if source.State:
            if self.edit:
                msg = 'Presiona SI para usar la misma clave,\npresiona NO ' \
                    'para asignar una nueva clave'
                if util.question(msg) == BUTTON_CLICK['YES']:
                    data = self.dm.noIdentificacion.Tag
                else:
                    new = True
            else:
                new = True
            if new:
                data = self.db.select(
                    ('productos',),
                    ('MAX(CAST(noIdentificacion AS UNSIGNED))+1',))[0][0]
            if not data:
                data = 1
            self.dm.noIdentificacion.Text = str(data)
            self.dm.noIdentificacion.ReadOnly = True
            self.dialog.getControl('categoria').setFocus()
        else:
            self.dm.noIdentificacion.Text = ''
            self.dm.noIdentificacion.ReadOnly = False
            self.clave.setFocus()
        return

    def chkInventario(self, event):
        source = event.Source
        self.dm.existencia.Enabled = source.State
        if source.State:
            self.existencia.setFocus()
        return

    def chkCuentaPredial(self, event):
        source = event.Source
        self.dm.CuentaPredial.Enabled = source.State
        if source.State:
            self.predial.setFocus()
        return

    def cmdMostrarCategorias(self, event):
        visible = self.tree.isVisible()
        self.tree.setVisible(not visible)
        util.set_visible(
            self.dialog, ('descripcion', 'unidad', 'valorUnitario'), visible)
        self.dm.cmdAgregarCategoria.Enabled = not visible
        self.dm.categoria.ReadOnly = visible
        return

    def treeCategorias_mouse_pressed(self, event):
        if event.ClickCount == 2:
            sel = self.tree.Selection
            if sel.DataValue == 0:
                self.dm.categoria.Text = ''
                self.dm.categoria.Tag = '0'
            else:
                cat = []
                self.dm.categoria.Tag = sel.DataValue
                while sel.DataValue:
                    cat.insert(0, sel.DisplayValue)
                    sel = sel.getParent()
                self.dm.categoria.Text = '|'.join(cat)
            self.cmdMostrarCategorias(None)
            self.descripcion.setFocus()
        return

    def cmdAgregarCategoria(self, event):
        if util.validate(self.categoria):
            msg = 'El campo CATEGORIA no puede estar vacío.'
            self.categoria.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return
        new_cat = self.categoria.Text
        sel = self.tree.Selection
        value = sel.DataValue
        query = self.db.select(
            ('categorias',),
            ('id',),
            "categoria='{}' and id_padre={}".format(new_cat, value))
        if query:
            msg = 'Ya existe esta categoría'
            self.categoria.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return
        tree_dm = self.tree.Model.DataModel
        new_row = self.db.insertrow(
            'categorias', {'categoria': new_cat, 'id_padre': value})
        hijo = tree_dm.createNode(new_cat, False)
        hijo.DataValue = new_row
        sel.appendChild(hijo)
        self.tree.expandNode(sel)
        self.categoria.Text = ''
        self.categoria.setFocus()
        return

    def cmdGuardar(self, event):
        try:
            if self._validar_datos():
                producto = {}
                producto['id_categoria'] = int(self.dm.categoria.Tag)
                producto['noIdentificacion'] = self.dm.noIdentificacion.Text
                producto['descripcion'] = self.dm.descripcion.Text
                producto['unidad'] = self.dm.unidad.Text
                producto['valorUnitario'] = self.dm.valorUnitario.Value
                producto['existencia'] = self.dm.existencia.Value
                producto['inventario'] = self.dm.chkInventario.State
                producto['codigobarras'] = self.dm.codigobarras.Text
                producto['CuentaPredial'] = self.dm.CuentaPredial.Text
                if self.edit:
                    id_producto = self.id_producto
                    self.db.update(
                        'productos', producto, 'id={}'.format(id_producto))
                    self.db.delete(
                        'productosimpuestos',
                        'id_producto={}'.format(id_producto))
                else:
                    id_producto = self.db.insertrow('productos', producto)
                self._unidad(self.dm.unidad.Text)
                sel = util.clear_sel(self.grid.SelectedRows)
                data = []
                for r in sel:
                    if r > -1:
                        row = [id_producto, self.grid_dm.getCellData(0, r)]
                        data.append(tuple(row))
                self.db.executemany(
                    'productosimpuestos',
                    ('id_producto', 'id_impuesto'),
                    tuple(data))
                self.dialog.endDialog(id_producto)
        except:
            log.error('TEST', exc_info=True)
        return

    def _unidad(self, unidad):
        test = self.db.select(
            ('unidades',), ('id',), "unidad='{}'".format(unidad))
        if not test:
            self.db.insertrow('unidades', {'unidad': unidad})
        return

    def _validar_datos(self):
        if util.validate(self.clave):
            msg = 'La Clave no puede estar vacía'
            self.clave.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return False
        if self.edit:
            data = self.db.select(
                ('productos',),
                ('id',),
                "noIdentificacion='{}' and id<>{}".format(
                    self.clave.Text, self.id_producto))
        else:
            data = self.db.select(
                ('productos',),
                ('id',),
                "noIdentificacion='{}'".format(self.clave.Text))
        if data:
            msg = 'Esta clave ya esta en uso'
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return False

        if not self.dm.categoria.Text:
            msg = 'La categoría no es necesaria, pero ayuda a organizar ' \
                'este catálogo y en las consultas \n\n ¿Estás seguro de ' \
                'dejarla vacía?'
            if util.question(msg) == BUTTON_CLICK['NO']:
                self.categoria.setFocus()
                return False

        if util.validate(self.descripcion):
            msg = 'La Descripcion no puede estar vacía'
            self.descripcion.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return False

        if self.edit:
            data = self.db.select(
                ('productos',),
                ('id',),
                "descripcion='{}' and id<>{}".format(
                    self.descripcion.Text, self.id_producto))
        else:
            data = self.db.select(
                ('productos',),
                ('id',),
                "descripcion='{}'".format(self.descripcion.Text))
        if data:
            msg = 'La descripción de este producto o servicio ya esta dada ' \
                'de alta.\n\n ¿Estás seguro de usarla nuevamente?'
            if util.question(msg) == BUTTON_CLICK['NO']:
                self.descripcion.setFocus()
                return False

        if util.validate(self.unidad):
            msg = 'La Unidad no puede estar vacía'
            self.unidad.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return False

        unit = self.db.select(
            ('unidades',), ('unidad',), "unidad='{}'".format(self.unidad.Text))
        if not unit:
            msg = 'La Unidad: {}, no existe en la base de datos, al guardar, ' \
                'esta será agregada automáticamente\n\n ¿Estás de ' \
                'acuerdo?'.format(self.unidad.Text)
            if util.question(msg) == BUTTON_CLICK['NO']:
                self.unidad.setFocus()
                return False

        if util.validate(self.price):
            msg = 'El Valor Unitario no puede estar vacío'
            self.price.setFocus()
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return False

        if not self.price.Value:
            msg = 'El Valor Unitario es cero\n\n¿Estás seguro de usar este valor?'
            if util.question(msg) == BUTTON_CLICK['NO']:
                sefl.price.setFocus()
                return False
        elif self.price.Value < 0:
            msg = 'El Valor Unitario es negativo\n\n¿Estás seguro de usar ' \
                'este valor?'
            if util.question(msg) == BUTTON_CLICK['NO']:
                self.price.setFocus()
                return False

        sel = util.clear_sel(self.grid.SelectedRows)
        if not sel:
            msg = 'Selecciona al menos un impuesto a aplicar'
            util.msgbox(msg, TYPE_MSG['WARNING'])
            self.grid.setFocus()
            return False

        if self.dm.chkInventario.State:
            if self.existencia.Value < 1:
                msg = 'La Existencia es igual o menor a cero\n\n¿Estás ' \
                    'seguro de usar este valor?'
                if util.question(msg) == BUTTON_CLICK['NO']:
                    self.existencia.setFocus()
                    return False

        util.validate(self.code_bar)

        if self.dm.CuentaPredial.Enabled:
            if util.validate(self.predial):
                msg = 'La Cuenta Predial no puede estar vacía'
                self.predial.setFocus()
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return False
        return True




#~ class EventosProductosAdmin(object):
    #~ def __init__(self,caller):
        #~ self.caller = caller
        #~ self.unogui = caller.unogui
        #~ self.util = caller.util
        #~ self.globales = caller.globales
        #~ self.db = caller.db
        #~ self.dialog = caller.dialog
        #~ self.decimales = caller.decimales
        #~ self.dm = self.dialog.getModel()
        #~ self.format_s = self.globales['FORMAT'] % self.decimales
#~
    #~ def valorUnitario_textChanged(self):
        #~ self._update_total()
        #~ return
#~
    #~ def cantidad_textChanged(self):
        #~ self._update_total()
        #~ return
#~
    #~ def total_textChanged(self):
        #~ self.dm.cantidad.Value = self.dm.total.Value
        #~ print(self.dm.total.Value)
        #~ return
#~
    #~ def _update_total(self):
        #~ p = round(self.dm.valorUnitario.Value, self.decimales)
        #~ c = round(self.dm.cantidad.Value, self.decimales)
        #~ s = round(p * c, self.decimales)
        #~ grid = self.dialog.getControl('gridImpuestos')
        #~ grid_dm = grid.Model.GridDataModel
        #~ totales = self.dialog.getControl('gridTotales').Model.GridDataModel
        #~ sel = self.util.clear_sel(grid.getSelection())
        #~ if sel:
            #~ total = s
            #~ iva = 0
            #~ for f in range(totales.RowCount):
                #~ if not (f in sel):
                    #~ totales.updateCellData(2, f, '0.00')
                    #~ continue
                #~ tax = (grid_dm.getCellData(0, f),
                        #~ grid_dm.getCellData(1, f),
                        #~ grid_dm.getCellData(2, f),
                        #~ grid_dm.getCellData(3, f))
                #~ if tax[2] == self.globales['IMPUESTO_EXENTO']:
                    #~ continue
                #~ try:
                    #~ tasa = float(tax[2]) / 100.0
                    #~ importe = round(s * tasa, self.decimales)
                    #~ if tax[1] == 'IVA' and tasa > 0:
                        #~ iva = importe
                #~ except:
                    #~ tasa = '%s*%s' % (iva, tax[2])
                    #~ importe = round(eval(tasa), self.decimales)
                #~ total += importe
                #~ totales.updateCellData(2, f, self.format_s.format(importe))
            #~ self.dm.total.Value = total
        #~ return
#~
    #~ def gridImpuestos_selectionChanged(self, grid):
        #~ self._update_total()
        #~ return
#~
#~


