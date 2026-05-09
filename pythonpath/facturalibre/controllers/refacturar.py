#!
# -*- coding: utf-8 -*-
import traceback

KEY_RETURN = 1280
KEY_TAB = 1282
CLIENTES_COUNT = 101
MOSTRAR_LIMITE = 10


class EventosRefacturar(object):
    def __init__(self, caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.globales = caller.globales
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.db = caller.db
        self.format_s = '{0:.%sf}' % self.db.select_field('opciones', 'decimales')
        self.prefacturas = False
        self.enviar_correo = caller.caller.enviar_correo

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def cmdFiltrar1(self):
        #AND strftime('%m%Y',fecha)=strftime('%m%Y','now')"
        where = ''
        lst = self.dialog.getControl('lstMes')
        pos = lst.SelectedItemPos
        if pos > 0:
            pos = '%02d' % pos
            where = " AND strftime('%m',fecha)='" + pos + "'"

        lst = self.dialog.getControl('lstEstatus')
        pos = lst.SelectedItemPos
        if pos > 0:
            where += " AND estatus=%s" % pos

        if self.dm.txtReceptor.Tag:
            where += " AND id_cliente=%s" % self.dm.txtReceptor.Tag

        self.__filtrar(where)
        return

    def cmdFiltrar2(self):
        where = ''
        if self.dm.txtCfd.Text:
            try:
                folio = int(self.dm.txtCfd.Text)
                where = " AND folio=%s" % folio
            except:
                where = " AND serie||folio='%s'" % self.dm.txtCfd.Text
            self.__filtrar(where)
        else:
            self.dialog.getControl('txtCfd').setFocus()
            message = 'Introduce el folio a buscar'
            self.unogui.createMsgBox({'Message': message})
        return

    #~ def cmdLimpiarSeleccion(self):
        #~ grid = self.dialog.getControl('gridFacturas')
        #~ grid.deselectAllRows()
        #~ return

    def __filtrar(self, where=''):
        if self.prefacturas:
            table = 'prefacturas'
            serie = 'folio'
        else:
            table = 'cfdfacturas'
            serie = 'serie || folio'
        if where:
            where = '%s.id_cliente=receptores.id %s' % (table, where)
        else:
            where = '%s.id_cliente=receptores.id' % table
        #~ estatus = "CASE WHEN estatus=1 THEN 'Por pagar' WHEN estatus=2 THEN 'Pagada' WHEN estatus=3 THEN 'Cancelada' END"
        #~ estatus = "CASE WHEN ser=1 THEN 'Por pagar' WHEN estatus=2 THEN 'Pagada' WHEN estatus=3 THEN 'Cancelada' END"
        estatus = 'serie'
        data = self.db.select((table, 'receptores'),
            ('%s.id' % table, serie, "strftime('%d-%m-%Y',fecha)", 'upper(substr(tipoDeComprobante,1,1))', estatus, 'total', 'upper(substr(Moneda,1,1))', 'TipoCambio', 'total*TipoCambio', 'nombre'), where)
        data_format = []
        for row in data:
            total = self.format_s.format(row[5])
            tipo_cambio = self.format_s.format(row[7])
            mn = self.format_s.format(row[8])
            row_format = (row[0], row[1], row[2], row[3], row[4], total, row[6], tipo_cambio, mn, row[9])
            data_format.append(row_format)
        self.unogui.gridAddRows(self.dm.gridFacturas, data_format)
        if not data:
            message = 'No se encontraron datos con estos criterios de busqueda'
            self.unogui.createMsgBox({'Message': message})
        #~ print 'Filtrado OK'
        return

    def txtReceptor_focusLost(self, source):
        self.dialog.getControl('gridReceptores').setVisible(False)
        return

    def txtReceptor_keyPressed(self, event):
        if event.KeyCode != KEY_RETURN and event.KeyCode != KEY_TAB:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(True)
            self.dm.txtReceptor.Tag = ''
            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                self.dm.txtReceptor.Tag = ''
                grid.setVisible(False)
                return
            where = "nombre LIKE '%" + cliente + "%' OR rfc LIKE '%" + cliente + "%'"
            receptores = self.db.select(('receptores',), ('id', 'rfc', 'nombre'), where, 'nombre')
            self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
        return

    def txtReceptor_keyReleased(self, event):
        if event.KeyCode == KEY_RETURN:
            grid = self.dialog.getControl('gridReceptores')
            grid.setVisible(False)
            self.dm.txtReceptor.Tag = ''

            cliente = event.Source.Text.strip().replace('|','')
            if not cliente:
                row_count = self.db.count('receptores')
                if row_count < CLIENTES_COUNT:
                    receptores = self.db.select(('receptores',), ('id', 'rfc', 'nombre'), 'activo=1', 'nombre')
                    self.unogui.gridAddRows(self.dm.gridReceptores, receptores)
                    grid.setFocus()
                    grid.setVisible(True)
                    return
                else:
                    message = 'Captura la clave del cliente a buscar.'
                    self.unogui.createMsgBox({'Message': message})
                    return
            try:
                id_cliente = int(cliente)
                receptor = self.db.select(('receptores',), where='id=%s AND activo=1' % id_cliente)
                if receptor:
                    receptor = receptor[0]
                    self.dm.txtReceptor.Tag = receptor[0]
                    self.dm.txtReceptor.Text = receptor[2]
                else:
                    message = 'No se encontró el receptor con la clave: %s' % id_cliente
                    self.unogui.createMsgBox({'Message': message})
            except ValueError as e:
                message = 'Asegurate de capturar un valor entero para buscar por clave del cliente'
                self.unogui.createMsgBox({'Message':message})
        return

    def gridReceptores_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            receptor = self.db.select(('receptores',), ('id', 'nombre'),where='id=%s' % grid_dm.getCellData(0, row))[0]
            self.dm.txtReceptor.Tag = receptor[0]
            self.dm.txtReceptor.Text = receptor[1]
            grid.setVisible(False)
            #self.dialog.getControl('descripcion').setFocus()
        return

    def chkPrefacturas(self, source):
        self.dm.cmdEliminar.Enabled = source.State
        self.dm.cmdPdf.Enabled = source.State
        self.prefacturas = bool(source.State)
        #~ if self.prefacturas:
            #~ self.unogui.gridAddRows(self.dm.gridFacturas, ())
        self.cmdFiltrar1()
        return

    def cmdEliminar(self):
        grid = self.dialog.getControl('gridFacturas')
        sel = grid.CurrentRow
        if sel < 0:
            message = 'Selecciona primero el documento a eliminar'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        id_cfd = grid_dm.getCellData(0, sel)
        message = '¿Estas seguro de borrar el documento seleccionado?' \
                    '\n\nESTA ACCION NO SE PUEDE DESHACER'
        if self.unogui.createQuestion('Factura Libre', message):
            self.db.delete('prefacturas', 'id=%s' % id_cfd)
            self.db.delete('predetalle', 'id_cfd=%s' % id_cfd)
            self.db.delete('preimpuestos', 'id_cfd=%s' % id_cfd)
            self.db.delete('prepersonalizados', 'id_cfd=%s' % id_cfd)
            grid_dm.removeRow(sel)
        return

    def cmdRefacturar(self):
        grid = self.dialog.getControl('gridFacturas')
        row = grid.CurrentRow
        if row < 0:
            message = 'Selecciona una factura'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        self.caller.prefactura = self.prefacturas
        self.dialog.endDialog(grid_dm.getCellData(0, row))
        return

    def cmdPdf(self):
        from facturalibre.modulos.pyPdf import CFDPDF

        grid = self.dialog.getControl('gridFacturas')
        sel = grid.CurrentRow
        if sel < 0:
            message = 'Selecciona primero un documento'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        id_cfd = grid_dm.getCellData(0, sel)
        cot = grid_dm.getCellData(4, sel)
        if cot == 'COTIZACION':
            pdf = CFDPDF(self, True)
            pdf.generate_cotizacion(id_cfd, self.enviar_correo)
        else:
            pdf = CFDPDF(self)
            pdf.generate_prepdf(id_cfd)
        return

    def txtCfd_keyReleased(self, event):
        try:
            if event.KeyCode == KEY_RETURN:
                self.cmdFiltrar2()
        except:
            print (traceback.format_exc())
