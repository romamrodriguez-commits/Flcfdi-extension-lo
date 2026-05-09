# -*- coding: utf-8 -*-
import traceback
import facturalibre.ui.clientesadmin as clientesadmin
import facturalibre.ui.inputbox2 as inputbox2

from facturalibre.modulos import util


KEY_RETURN = 1280


class EventosClientes(object):

    def __init__(self,caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.globales = caller.globales
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.db = caller.db
        self.value = ''

    @util.catch_exception
    def cmdNuevoCliente(self):
        dialog_admin = clientesadmin.Dlg(self.caller)
        id_cliente = dialog_admin.execute()
        if id_cliente:
            data = self.db.select(('receptores',), ('id','rfc', 'nombre'), order='nombre')
            self.unogui.gridAddRows(self.dm.gridReceptores,data)
            self.dm.cmdEditarCliente.Enabled = True
            self.dm.cmdEliminarCliente.Enabled = True
            self.dm.txtFiltrarCliente.Enabled = True
            self._registros(len(data))
        return

    def cmdEditarCliente(self):
        grid = self.dialog.getControl('gridReceptores')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona primero un receptor (cliente)'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        id_cliente = grid_dm.getCellData(0, row)
        dialog_admin = clientesadmin.Dlg(self.caller, True, id_cliente)
        id_cliente = dialog_admin.execute()
        if id_cliente:
            receptor = self.db.select(
                ('receptores',),('rfc', 'nombre', 'notas'), 'id=%s' % id_cliente)[0]
            grid_dm.updateCellData(1, row, receptor[0])
            grid_dm.updateCellData(2, row, receptor[1])
            grid_dm.updateCellData(3, row, receptor[2])
        return

    def cmdEliminarCliente(self):
        grid = self.dialog.getControl('gridReceptores')
        row = grid.CurrentRow
        if row == -1:
            message = 'Selecciona primero un receptor (cliente)'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        message = '¿Estás seguro de eliminar el siguiente receptor? \n Clave = %s \n RFC = %s \n Razón Social = %s \n\n ESTA ACCION NO SE PUEDE DESHACER \n\n También puedes solo desactivarlo' % (grid_dm.getCellData(0,row),grid_dm.getCellData(1,row),grid_dm.getCellData(2,row))
        if self.unogui.createQuestion('Factura Libre', message):
            self.db.delete('receptores','id=%s' % grid_dm.getCellData(0, row))
            grid_dm.removeRow(row)
            grid.deselectAllRows()
            if not grid_dm.RowCount:
                self.dm.cmdEditarCliente.Enabled=False
                self.dm.cmdEliminarCliente.Enabled=False
                self.dm.txtFiltrarCliente.Enabled=False
            self._registros(grid_dm.RowCount)
        return

    def txtFiltrarCliente_keyPressed(self, event):
        if event.KeyCode != KEY_RETURN:
            cliente = event.Source.Text.strip().replace('|', '')
            if not cliente:
                self.cmdMostrarTodo()
                return
            where = "nombre LIKE '%{0}%' OR rfc LIKE '%{0}%'".format(cliente)
            clientes = self.db.select(
                    ('receptores',), ('id', 'rfc', 'nombre'), where, 'nombre')
            self.unogui.gridAddRows(self.dm.gridReceptores, clientes)
            self._registros(len(clientes))
            self.dm.cmdMostrarTodo.Enabled = True
        return

    def txtFiltrarCliente_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            cliente=event.Source.Text.strip().replace('|','')
            if not cliente:
                message = 'Criterio de busqueda vacio.'
                self.unogui.createMsgBox({'Message': message})
                return
            try:
                id_cliente = int(cliente)
                clientes = self.db.select(('receptores',),
                                ('id', 'rfc', 'nombre'), 'id=%s' % id_cliente)
                if clientes:
                    self.unogui.gridAddRows(self.dm.gridReceptores, clientes)
                    self._registros(len(clientes))
                    self.dm.txtFiltrarCliente.Text = ''
                    self.dm.cmdMostrarTodo.Enabled = True
                else:
                    message = 'No se encontró un receptor con la clave: %s' % id_cliente
                    self.unogui.createMsgBox({'Message': message})
            except ValueError as e:
                message = 'Asegurate de capturar un valor entero para buscar por clave del cliente'
                self.unogui.createMsgBox({'Message': message})
        return

    def cmdMostrarTodo(self):
        data = self.db.select(
                ('receptores',),
                ('id', 'rfc', 'nombre'),
                order='nombre')
        self.unogui.gridAddRows(self.dm.gridReceptores, data)
        self.dialog.getControl('txtFiltrarCliente').setFocus()
        self.dm.txtFiltrarCliente.Text = ''
        self.dm.cmdMostrarTodo.Enabled = False
        self._registros(len(data))
        return

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def _registros(self, filas):
        if filas == 0:
            self.dm.lblInfo.Label = 'Sin Registros'
        elif filas == 1:
            self.dm.lblInfo.Label = '1 Registro'
        else:
            self.dm.lblInfo.Label = '%s Registros' % filas
        return

    def gridReceptores_DobleClick(self, source):
        grid = self.dialog.getControl('gridReceptores')
        col = grid.CurrentColumn
        if col == 3:
            row = grid.CurrentRow
            grid_dm = grid.Model.GridDataModel
            id_cliente = grid_dm.getCellData(0, row)
            self.value = ''
            msg = 'Edición de notas del cliente: {}'.format(grid_dm.getCellData(2, row))
            input_box = inputbox2.Dlg(self, (msg, grid_dm.getCellData(3, row)))
            res = input_box.execute()
            if res:
                self.db.update(
                    'receptores', {'notas': self.value}, 'id={}'.format(id_cliente))
                grid_dm.updateCellData(3, row, self.value)
            return
        self.cmdEditarCliente()
        return

    def cmdReporte(self):
        fields = ('id',
                'rfc',
                'nombre')
        data = self.db.select(('receptores',), fields, order='nombre')
        oDoc = self.util.newDoc()
        oHoja = oDoc.getSheets().getByIndex(0)
        oRango = oHoja.getCellRangeByPosition(0, 0, len(data[0])-1, 0)
        oRango.setDataArray((('Clave', 'RFC', 'Razón Social'),))
        self.__format_title(oRango)
        oRango = oHoja.getCellRangeByPosition(0, 1, len(data[0])-1, len(data))
        oRango.setDataArray(tuple(data))
        return

    def __format_title(self, rango):
        rango.CharWeight = 150
        rango.VertJustify = 2
        rango.HoriJustify = 2
        return
