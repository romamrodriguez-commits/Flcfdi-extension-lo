#!
# -*- coding: utf-8 -*-


class EventosCampos(object):

    def __init__(self, caller):
        self.caller = caller
        self.dialog = caller.dialog
        self.db = caller.db
        self.util = caller.util
        self.dm = self.dialog.getModel()

    def cmdAceptar(self):
        id_cfd = self.dm.lblInfo.Tag
        if id_cfd:
            grid_dm = self.dm.gridCampos.GridDataModel
            fil = grid_dm.RowCount
            for f in range(fil):
                value = grid_dm.getCellData(2, f)
                where = "id_cfd=%s and campo='%s'" % (id_cfd,
                                                grid_dm.getCellData(3, f))
                d = self.db.select(('cfdpersonalizados',), ('id',), where)
                if d:
                    values = {'valor': value}
                    self.db.update('cfdpersonalizados', values, where)
                    continue
                if value:
                    values = {'id_cfd': id_cfd,
                                'campo': grid_dm.getCellData(3, f),
                                'valor': value}
                    self.db.insertrow('cfdpersonalizados', values)
        else:
            grid_s = self.dm.gridCampos.GridDataModel
            grid_d = self.caller.caller.dm.gridCampos.GridDataModel
            fil = grid_s.RowCount
            for f in range(fil):
                grid_d.updateCellData(2, f, grid_s.getCellData(2, f))
        self.dialog.endDialog(1)
        return

    def cmdCancelar(self):
        self.dialog.endDialog(0)
        return

    def gridCampos_selectionChanged(self, grid):
        self.dm.txtEditar.Enabled = True
        grid_dm = grid.Model.GridDataModel
        row = grid.CurrentRow
        self.dm.lblCampo.Label = grid_dm.getCellData(1, row)
        self.dm.txtEditar.Text = grid_dm.getCellData(2, row)
        if 'fecha' in self.dm.lblCampo.Label.lower():
            self.dialog.getControl('datFecha').setVisible(True)
            #~ self.dialog.getControl('datFecha').setFocus()
        else:
            self.dialog.getControl('datFecha').setVisible(False)
            #~ self.dialog.getControl('txtEditar').setFocus()
        return

    def txtEditar_textChanged(self):
        row = self.dialog.getControl('gridCampos').CurrentRow
        grid_dm = self.dm.gridCampos.GridDataModel
        grid_dm.updateCellData(2, row, self.dm.txtEditar.Text)
        return

    def datFecha_textChanged(self):
        self.dm.txtEditar.Text = self.dm.datFecha.Text
        self.txtEditar_textChanged()
        return
