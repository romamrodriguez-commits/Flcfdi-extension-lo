#!
# -*- coding: utf-8 -*-

import traceback

KEY_RETURN = 1280

class EventosRepProP(object):
    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.unogui = caller.unogui
        self.db = caller.db
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()

    def cmdGenerar(self):
        print ('EventosRepProP')
        #Verificamos cual es el orden que se quiere para el resultado
        if self.dm.optFecha.State:
            ordenar = 'compras.fecha'
        else:
            ordenar = 'compradetalle.descripcion'

        FechaIni = str(self.util.getDateFromControl(self.dm.txtFechaIni.Date))
        FechaFin = str(self.util.getDateFromControl(self.dm.txtFechaFin.Date))

        condicion = " compras.fecha>='" + FechaIni + " 00:00:00' AND compras.fecha<='" + FechaFin + " 23:59:59'"
        
        #Se revisa si el resultado se quiere desglozado por producto
        if self.dm.chkDesglozado.State:
            campos = ('compras.fecha, compras.serie || compras.folio, compras.estatus, compradetalle.descripcion, receptores.nombre, compradetalle.unidad, compradetalle.cantidad, compradetalle.valorUnitario, compradetalle.importe',)
            tablas = ('compradetalle', )
            otro = 'INNER JOIN compras ON compras.id = compradetalle.id_compra INNER JOIN receptores ON receptores.id = compras.id_proveedor'
            titulos = ('Fecha', 'Factura', 'Estado', 'Descripción', 'Cliente', 'Subtotal', 'Descuento', 'Impuestos', 'Total')
            Periodo = 'Reporte de ventas de productos por cliente del %s al %s' % (FechaIni, FechaFin)
        else:
            campos = ('compras.fecha, compras.serie || compras.folio, compras.estatus, compradetalle.descripcion, compradetalle.unidad, compradetalle.cantidad, compradetalle.valorUnitario, compradetalle.importe',)
            tablas = ('compradetalle',)
            otro = 'INNER JOIN compras ON compradetalle.id_compra=compras.id'
            titulos = ('Fecha', 'Factura', 'Estado', 'Descripcion', 'Unidad', 'Cantidad', 'Precio unitario', 'Importe')
            Periodo = 'Reporte de ventas por producto del %s al %s' % (FechaIni, FechaFin)

        eltipo = self.dialog.getControl('lstTipo').SelectedItem
        if eltipo == 'Ingresos':
            condicion += " AND compras.tipoDeComprobante='ingreso'"
            Periodo += ' (Ingresos)'
        elif eltipo == 'Egresos':
            condicion += " AND compras.tipoDeComprobante='egreso'"
            Periodo += ' (Egresos)'
        else:
            campos += ('compras.tipoDeComprobante',)
            titulos += ('Tipo',)

        #Cuidamos si se quiere tener las facturas canceladas
        if self.dm.chkCancelados.State:
            condicion += " AND NOT compras.estatus='Cancelada' "

        #Se ve si el resultado es para un solo producto o para todos
        if len(self.dialog.getControl('lstClientes').SelectedItem) > 0 and self.dialog.getControl('lstClientes').SelectedItem != 'Todos':
            condicion += " AND compradetalle.descripcion='" + self.dialog.getControl('lstClientes').SelectedItem + "'"
            
        #~ self.util.msgbox(condicion)
        data = self.db.select(tablas,campos,where=condicion,order=ordenar,other1=otro)
        if not data:
            message = 'No hay facturas a reportar'
            self.util.msgbox(message)
            return

        #Generamos un nuevo documento donde dejar el resultado de la consulta
        oDoc = self.util.newDoc()
        oHoja = oDoc.getSheets().getByIndex(0)

        #Aplicamos formatos
        oRango = oHoja.getCellRangeByPosition(0, 0, 1, 0)
        oRango.CharWeight = 150
        oRango.CharHeight = 18
        oRango = oHoja.getCellRangeByPosition(0, 1, 0, 1)
        oRango.CharWeight = 150
        oRango.CharHeight = 14
        cf = len(data[0]) - 1
        lf = len(data) + 3
        oRango = oHoja.getCellRangeByPosition(0, 3, cf, 3)
        oRango.HoriJustify = 2
        oRango.VertJustify = 2
        oRango.CharWeight = 150
        oRango.IsTextWrapped = True
        oFilas = oHoja.getRows()
        oFilas.getByIndex(3).OptimalHeight = True
        oRango = oHoja.getCellRangeByPosition(0, 4, cf, lf)
        oRango.VertJustify = 2
        oRango = oHoja.getCellRangeByPosition(0, 4, 0, lf)
        oRango.NumberFormat = 37
        oRango = oHoja.getCellRangeByPosition(0, 4, cf, lf)
        oRango.IsTextWrapped = True
        oRango = oHoja.getCellRangeByPosition(3, 4, cf, lf)
        oRango.NumberFormat = 4
        oColumnas = oHoja.getColumns()
        oColumnas.getByName("A").Width = 3240
        oColumnas.getByName("D").Width = 8000
        if self.dm.chkDesglozado.State:
            oColumnas.getByName("E").Width = 8000

        #Colocamos los titulos
        datae = self.db.select_field('emisor','nombre')
        oHoja.getCellByPosition(0,0).String = "Empresa:"
        oHoja.getCellByPosition(1, 0).String = datae
        oHoja.getCellByPosition(0,1).String = Periodo
        
        oRango = oHoja.getCellRangeByPosition(0, 3, len(data[0]) - 1, 3)
        oRango.setDataArray((titulos,))

        #Cambia la columna fecha a un número valido para Calc y cambia el código del estatus por un texto
        data_ok = []
        for row in data:
            fecha_str = row[0]
            fecha = self.util.date_to_calc(self.util.format_date(fecha_str[0:10], '%d/%m/%Y'), True)
            data_ok.append((fecha, ) + row[1:])

        #Despliega los datos
        oRango = oHoja.getCellRangeByPosition(0, 4, cf, lf)
        oRango.setDataArray(tuple(data_ok))
        return

    def cmdSalir(self):
        self.dialog.endExecute()
        return
