#!
# -*- coding: utf-8 -*-

KEY_RETURN = 1280


class EventosAlumnos(object):

    def __init__(self, caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.db = caller.db
        self.dialog = caller.dialog
        self.dm = self.dialog.Model
        #~ self.niveles = caller.niveles

    def cmdAgregar(self):
        txtAlumno = self.dialog.getControl('txtAlumno')
        txtCurp = self.dialog.getControl('txtCurp')
        lstNivel = self.dialog.getControl('lstNivel')
        if self.unogui.validate(txtAlumno, 'Vacio'):
            message = u'El campo ALUMNO no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txtAlumno.setFocus()
            return
        if self.unogui.validate(txtCurp, 'Vacio'):
            message = u'El campo CURP no puede estar vacío'
            self.unogui.createMsgBox({'Message': message})
            txtCurp.setFocus()
            return
        if len(txtCurp.Text) != 18:
            message = u'El campo CURP tiene que ser de 18 caracteres'
            self.unogui.createMsgBox({'Message': message})
            txtCurp.setFocus()
            return
        patron = '[A-Z][A,E,I,O,U,X][A-Z]{2}[0-9]{2}[0-1][0-9][0-3]' \
            '[0-9][M,H][A-Z]{2}[B,C,D,F,G,H,J,K,L,M,N,Ñ,P,Q,R,S,T,V' \
            ',W,X,Y,Z]{3}[0-9,A-Z][0-9]'
        if not self.util.match(patron, txtCurp.Text):
            message = u'El CURP no es valido'
            self.unogui.createMsgBox({'Message': message})
            return
        if lstNivel.SelectedItemPos <= 0:
            message = u'Selecciona el nivel para este alumno'
            self.unogui.createMsgBox({'Message': message})
            lstNivel.setFocus()
            return

        row = (0, txtAlumno.Text, txtCurp.Text, lstNivel.SelectedItem)
        self.unogui.gridAddRow(self.dm.gridAlumnos, row)
        txtAlumno.Text = ''
        txtCurp.Text = ''
        self.dialog.getControl('lstNivel').selectItemPos(0, True)
        self.dm.cmdEliminar.Enabled = True
        txtAlumno.setFocus()
        return

    def cmdEliminar(self):
        grid = self.dialog.getControl('gridAlumnos')
        row = grid.CurrentRow
        if row < 0:
            message = u'Selecciona un alumno'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        message = u'¿Estás seguro de eliminar este alumno? \n\n %s' % \
            grid_dm.getCellData(1,row)
        if self.unogui.createQuestion('Factura Libre', message):
            grid_dm.removeRow(row)
            if not grid_dm.RowCount:
                self.dm.cmdEliminar.Enabled = False
        return

    def cmdCambiarNivel(self):
        grid = self.dialog.getControl('gridAlumnos')
        row = grid.CurrentRow
        if row < 0:
            message = u'Selecciona un alumno'
            self.unogui.createMsgBox({'Message': message})
            return
        grid_dm = grid.Model.GridDataModel
        lstNivel = self.dialog.getControl('lstNivel')
        if lstNivel.SelectedItemPos <= 0:
            message = u'Selecciona el nuevo nivel para este alumno'
            self.unogui.createMsgBox({'Message': message})
            lstNivel.setFocus()
            return
        grid_dm.updateCellData(3, row, lstNivel.SelectedItem)
        return

    def cmdGuardar(self):
        self.caller.caller.alumnos = self.__grid_to_list()
        self.dialog.endExecute()
        return

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def __grid_to_list(self):
        grid = self.dialog.getControl('gridAlumnos')
        grid_dm = grid.Model.GridDataModel
        col = grid_dm.ColumnCount
        fil = grid_dm.RowCount
        data = []
        for f in range(fil):
            row = []
            for c in range(col):
                if c == 0:
                    row.append(self.caller.id_cliente)
                #~ elif c == 3:
                    #~ nivel = grid_dm.getCellData(c, f)
                    #~ row.append(self.niveles[nivel])
                else:
                    row.append(grid_dm.getCellData(c, f))
            data.append(row)
        return data