#!
# -*- coding: utf-8 -*-

import traceback

KEY_RETURN = 1280

class EventosRepProTot(object):
    def __init__(self, caller):
        self.caller = caller
        self.util = caller.util
        self.unogui = caller.unogui
        self.db = caller.db
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()

    def cmdGenerar(self):
        print ('EventosRepProTot')
        FechaIni = str(self.util.getDateFromControl(self.dm.txtFechaIni.Date))
        FechaFin = str(self.util.getDateFromControl(self.dm.txtFechaFin.Date))

        condicion = " compras.fecha>='" + FechaIni + " 00:00:00' AND compras.fecha<='" + FechaFin + " 23:59:59'"
        
        #Verificamos como se quiere agrupar
        if self.dm.optFacturas.State:
            campos = ('receptores.nombre, compras.estatus, SUM(compras.subtotal), SUM(compras.descuento), SUM(compras.totalImpuestosTrasladados), SUM(compras.total)',)
            tablas = ('compras', )
            otro = 'INNER JOIN receptores ON compras.id_proveedor = receptores.id'
            condicion += " AND compras.TipoDeComprobante='ingreso' AND NOT compras.estatus='Cancelada' "
            ordenar = 'receptores.nombre'
            agrupar = 'receptores.nombre, compras.estatus'
            titulos = ('Cliente', 'Estado', 'Subtotal', 'Descuento', 'Impuestos', 'Total')
            Periodo = 'Reporte de compras totales por proveedor del %s al %s' % (FechaIni, FechaFin)
            
        if self.dm.optNotas.State:
            campos = ('receptores.nombre, compras.estatus, SUM(compras.subtotal), SUM(compras.descuento), SUM(compras.totalImpuestosTrasladados), SUM(compras.total)',)
            tablas = ('compras', )
            otro = 'INNER JOIN receptores ON compras.id_proveedor = receptores.id'
            condicion += " AND compras.TipoDeComprobante='egreso' AND NOT compras.estatus='Cancelada' "
            ordenar = 'receptores.nombre'
            agrupar = 'receptores.nombre, compras.estatus'
            titulos = ('Cliente', 'Estado', 'Subtotal', 'Descuento', 'Impuestos', 'Total')
            Periodo = 'Reporte del total de notas de crédito por proveedor del %s al %s' % (FechaIni, FechaFin)

        if self.dm.optProductos.State:
            campos = ('productos.descripcion, compradetalle.categoria, compradetalle.unidad, SUM(compradetalle.cantidad), SUM(compradetalle.importe)',)
            tablas = ('compradetalle', )
            otro = 'INNER JOIN compras ON compradetalle.id_cfd=compras.id INNER JOIN productos ON productos.id=compradetalle.id_producto'
            condicion += " AND compras.TipoDeComprobante='ingreso' AND NOT compras.estatus='Cancelada' "
            ordenar = 'compradetalle.descripcion'
            agrupar = 'compradetalle.id_producto'
            titulos = ('Producto', 'Categoría', 'Unidad', 'Cantidad', 'Importe')
            Periodo = 'Reporte de compras de productos del %s al %s' % (FechaIni, FechaFin)

        if self.dm.optTipo.State:
            campos = ('compras.tipoDeComprobante, compras.estatus, SUM(compras.subtotal), SUM(compras.descuento), SUM(compras.totalImpuestosTrasladados), SUM(compras.total)',)
            tablas = ('compras', )
            otro = ''
            condicion += ''
            ordenar = 'compras.tipoDeComprobante'
            agrupar = 'compras.tipoDeComprobante, compras.estatus'
            titulos = ('Tipo', 'Estado', 'Subtotal', 'Descuento', 'Impuestos', 'Total')
            Periodo = 'Reporte del total de movimientos por proveedor del %s al %s' % (FechaIni, FechaFin)

        if self.dm.optMes.State:
            campos = ("compras.fecha, compras.estatus, SUM(compras.subtotal), SUM(compras.descuento), SUM(compras.totalImpuestosTrasladados), SUM(compras.total)",)
            tablas = ('compras', )
            otro = ''
            condicion += " AND compras.TipoDeComprobante='ingreso' AND NOT compras.estatus='Cancelada' "
            ordenar = 'compras.fecha'
            agrupar = "strftime('%Y-%m',compras.fecha), compras.estatus"
            titulos = ('Mes', 'Estado', 'Subtotal', 'Descuento', 'Impuestos', 'Total')
            Periodo = 'Reporte del total de compras por mes del %s al %s' % (FechaIni, FechaFin)

        if self.dm.optDia.State:
            campos = ("compras.fecha, compras.estatus, SUM(compras.subtotal), SUM(compras.descuento), SUM(compras.totalImpuestosTrasladados), SUM(compras.total)",)
            tablas = ('compras', )
            otro = ''
            condicion += " AND compras.TipoDeComprobante='ingreso' AND NOT compras.estatus='Cancelada' "
            ordenar = 'compras.fecha'
            agrupar = "strftime('%d-%m-%Y',compras.fecha), compras.estatus"
            titulos = ('Fecha', 'Estado', 'Subtotal', 'Descuento', 'Impuestos', 'Total')
            Periodo = 'Reporte del total de compras por día del %s al %s' % (FechaIni, FechaFin)

        data = self.db.select(tablas, campos, where=condicion, order=ordenar, other1=otro, groupby=agrupar)
        if not data:
            message = 'No hay datos a reportar'
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
        oRango = oHoja.getCellRangeByPosition(0, 4, 0, lf)
        oRango.IsTextWrapped = True
        oRango = oHoja.getCellRangeByPosition(1, 4, cf, lf)
        oRango.NumberFormat = 4
        oColumnas = oHoja.getColumns()
    
        #Si se quiere un reporte de facturas o notas, se pone el nombre del cliente en la primer columna.
        if self.dm.optFacturas.State or self.dm.optNotas.State or self.dm.optProductos.State:
            oColumnas.getByName("A").Width = 8000
        else:
            oColumnas.getByName("A").Width = 3240
    
        #Colocamos los titulos
        datae = self.db.select_field('emisor','nombre')
        oHoja.getCellByPosition(0,0).String = "Empresa:"
        oHoja.getCellByPosition(1, 0).String = datae
        oHoja.getCellByPosition(0,1).String = Periodo
        
        oRango = oHoja.getCellRangeByPosition(0, 3, len(data[0]) - 1, 3)
        oRango.setDataArray((titulos,))
        
        #Cambia las columnas para que tengan validez
        data_ok = []
        if self.dm.optMes.State:
            for row in data:
                fecha = row[0]
                mes_ano = fecha[5:7] + '-' + fecha[0:4]
                data_ok.append((mes_ano, ) + row[1:])
                
        if self.dm.optDia.State:
            for row in data:
                fecha_str = row[0]
                fecha = self.util.date_to_calc(self.util.format_date(fecha_str[0:10], '%d/%m/%Y'), True)
                data_ok.append((fecha, ) + row[1:])

        if self.dm.optFacturas.State or self.dm.optNotas.State or self.dm.optProductos.State:
            data_ok = data

        if self.dm.optTipo.State:
            for row in data:
                if row[0] == 'ingreso':
                    tipo = 'Ingreso'
                else:
                    tipo = 'Egreso'
                data_ok.append((tipo, ) + row[1:])
        
        #Despliega los datos
        oRango = oHoja.getCellRangeByPosition(0, 4, cf, lf)
        oRango.setDataArray(tuple(data_ok))
        return

    def cmdSalir(self):
        self.dialog.endExecute()
        return
