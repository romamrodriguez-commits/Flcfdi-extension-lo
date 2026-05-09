# -*- coding: utf-8 -*-

import traceback
try:
    import sqlite3 as sqlite
    DRIVER = True
except ImportError:
    import apsw as sqlite
    DRIVER = False


class DBDetalle(object):
    FIELDS = (
            'id',
            'noIdentificacion',
            'unidad',
            'descripcion',
            'cantidad',
            'valorUnitario',
            'importe',
            'ROWID')
    def __init__(self, sqlite=None):
        self.decimales = 2
        self.con = self.__Connection()
        self.__create_tables()
        self.impuestos = []
        self.tax_round = {}

    def __del_(self):
        self.con.close()

    def __Connection(self):
        con = sqlite.Connection(':memory:')
        return con

    def __create_tables(self):
        sql = """
            CREATE TABLE IF NOT EXISTS detalle(
                id INTEGER,
                id_cfd INTEGER DEFAULT 0,
                categoria TEXT COLLATE NOCASE,
                cantidad FLOAT,
                unidad TEXT,
                noIdentificacion TEXT COLLATE NOCASE,
                descripcion TEXT COLLATE NOCASE,
                valorUnitario FLOAT,
                importe FLOAT,
                numero TEXT,
                fecha TIMESTAMP,
                aduana TEXT,
                CuentaPredial TEXT,
                inventario INTEGER DEFAULT 0,
                version TEXT DEFAULT '',
                alumno TEXT DEFAULT '',
                curp TEXT DEFAULT '',
                nivel TEXT DEFAULT '',
                autorizacion TEXT DEFAULT '',
                pos INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS impuestos(
                id_cfd INTEGER,
                id_producto INTEGER,
                nombre TEXT,
                tasa TEXT,
                tipo TEXT,
                importe FLOAT,
                row_id INTEGER DEFAULT 0);
            """
        cursor = self.con.cursor()
        if DRIVER:
            cursor.executescript(sql)
        else:
            cursor.execute(sql)
        cursor.close()
        return

    def insert_product(self, values, impuestos, descuento):
        cursor = self.con.cursor()
        questions = '?,' * (len(values) - 1) + '?'
        fields = ','.join(list(values.keys()))
        sql = 'INSERT INTO %s(%s) values(%s)' % ('detalle', fields, questions)
        cursor.execute(sql, list(values.values()))
        if DRIVER:
            self.con.commit()
            row_id = cursor.lastrowid
        else:
            row_id = self.con.last_insert_rowid()
        new_row = {}
        for nombre, tasa, tipo in impuestos:
            new_row['id_producto'] = values['id']
            new_row['nombre'] = nombre
            new_row['tasa'] = tasa
            new_row['tipo'] = tipo
            new_row['importe'] = values['importe']
            new_row['row_id'] = row_id
            #~ new_row['redondear'] = redondear
            questions = '?,' * (len(new_row) - 1) + '?'
            fields = ','.join(list(new_row.keys()))
            sql = 'INSERT INTO %s(%s) values(%s)' % ('impuestos', fields, questions)
            cursor.execute(sql, list(new_row.values()))
        data = self.__select(('detalle',), self.FIELDS, order='pos')
        cursor.close()
        return data

    def exists_product(self, id_producto, cantidad, descuento):
        data = self.__select(('detalle',), ('cantidad', 'valorUnitario'), 'id=%s'%id_producto)
        if data:
            new_values = {}
            new_values['cantidad'] = cantidad + data[0][0]
            new_values['importe'] = round(new_values['cantidad'] * data[0][1], self.decimales)
            self.__update('detalle', new_values, 'id=%s'%id_producto)
            del new_values['cantidad']
            self.__update('impuestos', new_values, 'id_producto=%s'%id_producto)
            data = self.__select(('detalle',), self.FIELDS, order='pos')
        return data

    def exists_product_cant(self, id_producto):
        data = self.__select(('detalle',), ('cantidad',), 'id=%s'%id_producto)
        if data:
            return data[0][0]
        else:
            return 0

    def delete_product(self, row_id):
        self.__delete('detalle', 'ROWID=%s' % row_id)
        self.__delete('impuestos', 'row_id=%s' % row_id)
        data = self.__select(('detalle',), self.FIELDS, order='pos')
        return data

    def update_idcfd(self, id_cfd):
        self.__update('detalle', {'id_cfd': id_cfd})
        self.__update('impuestos', {'id_cfd': id_cfd})
        return

    def get_products_show(self):
        data = self.__select(('detalle',), self.FIELDS, order='pos')
        return data

    def get_products(self):
        fields = (
            'id_cfd',
            'id',
            'categoria',
            'cantidad',
            'unidad',
            'noIdentificacion',
            'descripcion',
            'valorUnitario',
            'importe',
            'numero',
            'fecha',
            'aduana',
            'CuentaPredial',
            'version',
            'alumno',
            'curp',
            'nivel',
            'autorizacion')
        data = self.__select(('detalle',), fields, order='pos')
        fields = 'id_cfd, id_producto, nombre, tasa, tipo'
        sql = 'SELECT %s FROM impuestos GROUP BY id_producto,nombre,tasa,tipo' % fields
        cursor = self.con.cursor()
        cursor.execute(sql)
        taxes = cursor.fetchall()
        cursor.close()
        return data, taxes

    def get_products_update(self):
        fields = ('id', 'cantidad')
        data = self.__select(('detalle',), fields, 'inventario=1')
        return data

    def delete_all(self):
        self.__delete('detalle')
        self.__delete('impuestos')
        return

    def calcular_impuestos(self, descuento):
        totales = {}
        impuestos = []
        cursor = self.con.cursor()
        sql = 'SELECT id FROM detalle LIMIT 1'
        if not cursor.execute(sql).fetchall():
            totales['subtotal'] = None
            impuestos.insert(0, totales)
            self.impuestos = impuestos
            return
        sql = 'SELECT SUM(importe) FROM detalle'
        cursor.execute(sql)
        subtotal = cursor.fetchall()[0][0]

        fields = 'nombre, tasa, tipo, SUM(importe)'
        sql = 'SELECT %s FROM impuestos ' \
                'WHERE nombre="IEPS" AND tipo="Traslado" ' \
                'GROUP BY nombre, tasa, tipo' % fields
        cursor.execute(sql)
        data = cursor.fetchall()
        ieps_importe = 0
        for i in data:
            tasa = float(i[1]) / 100.0
            ieps_importe += round((i[3]) * tasa, self.decimales)

        fields = 'nombre, tasa, tipo, SUM(importe)'
        sql = 'SELECT %s FROM impuestos ' \
            'WHERE nombre="IVA" AND tipo="Traslado" ' \
            'AND tasa!="EXENTO" AND tasa>0' % fields
        cursor.execute(sql)
        data = cursor.fetchall()
        iva_tasa = None
        iva_importe = 0
        if data[0][0]:
            iva_tasa = float(data[0][1]) / 100.0
            iva_importe = abs(round((
                data[0][3]+ieps_importe-descuento) * iva_tasa, self.decimales))

        fields = 'nombre, tasa, tipo, SUM(importe)'
        sql = 'SELECT %s FROM impuestos GROUP BY nombre, tasa, tipo ORDER BY tipo DESC' % fields
        cursor.execute(sql)
        data = cursor.fetchall()

        impuesto_iva = 0
        total_traslados = None
        total_retenciones = None
        total_traslados_otros = 0
        total_retenciones_otros = 0
        for nombre, tasa, tipo, importe in data:
            #~ print (nombre, tasa, tipo, importe)
            importe -= descuento
            impuesto = {}
            impuesto['nombre'] = nombre
            impuesto['tasa'] = tasa
            impuesto['tipo'] = tipo
            if tasa == 'EXENTO':
                continue
            if nombre == 'IVA' and tipo == 'Traslado' and tasa != '0':
                impuesto['importe'] = iva_importe
            else:
                try:
                    tasa_f = float(tasa) / 100
                    impuesto['importe'] = abs(round(importe * tasa_f, self.decimales))
                except ValueError:
                    base_impuesto = 0
                    if iva_tasa:
                        base_impuesto = abs(round(importe * iva_tasa, self.decimales))
                    tasa_f = '%s*%s' % (base_impuesto, tasa)
                    impuesto['importe'] = abs(round(eval(tasa_f), self.decimales))
            # Round special
            if nombre in self.tax_round:
                if self.tax_round[nombre]:
                    impuesto['importe'] = round(impuesto['importe'])
            if tipo == 'Retencion':
                impuesto['titulo'] = '%s %s %s%%' % (tipo, nombre, tasa)
                if nombre=='IVA' or nombre=='ISR':
                    if total_retenciones is None:
                        total_retenciones = 0
                    total_retenciones += impuesto['importe']
                else:
                    total_retenciones_otros += impuesto['importe']
            else:
                impuesto['titulo'] = '%s al %s%%' % (nombre, tasa)
                if total_traslados is None:
                    total_traslados = 0
                if nombre == 'IVA' or nombre == 'IEPS':
                    total_traslados += impuesto['importe']  #- descuento_iva
                else:
                    total_traslados_otros += impuesto['importe']
            impuestos.append(impuesto)
        cursor.close()
        totales['subtotal'] = subtotal
        totales['descuento'] = descuento
        totales['totalTraslados'] = total_traslados
        totales['totalRetenciones'] = total_retenciones
        totales['total'] = subtotal - descuento
        if total_traslados:
            totales['total'] += total_traslados
        totales['total'] += total_traslados_otros
        if total_retenciones:
            totales['total'] -= total_retenciones
        totales['total'] -= total_retenciones_otros
        impuestos.insert(0, totales)
        self.impuestos = impuestos
        return

    def __select(self, tables_names, fields=(), where='', order=''):
        cursor = self.con.cursor()
        tables=','.join(tables_names)
        if fields:
            fields2=','.join(fields)
        else:
            fields2='*'
        sql='SELECT %s FROM %s' % (fields2, tables)
        if where:
            sql+=' WHERE %s' % where
        if order:
            sql+=' ORDER BY %s' % order
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        return data

    def __update(self, table_name, values={}, where=''):
        cursor = self.con.cursor()
        new_values=[]
        for key,value in list(values.items()):
            if isinstance(value,str) or isinstance(value,str):
                new_values.append("%s='%s'" % (key,value))
            else:
                new_values.append("%s=%s" % (key,value))
        sql="UPDATE %s SET %s" % (table_name,','.join(new_values))
        if where:
            sql+=' WHERE %s' % where
        cursor.execute(sql)
        #~ self.con.commit()
        return

    def __delete(self, table_name, where=''):
        cursor = self.con.cursor()
        sql='DELETE FROM %s' % table_name
        if where:
            sql+=' WHERE %s' % where
        cursor.execute(sql)
        #~ self.con.commit()
        return

    def update_unidad(self, id_producto, new_unit):
        self.__update('detalle', {'unidad': new_unit}, 'ROWID=%s' % id_producto)
        return

    def update_description(self, id_producto, description):
        self.__update('detalle', {'descripcion': description}, 'ROWID=%s' % id_producto)
        return

    def update_value(self, id_producto, value, importe, precio=True):
        if precio:
            self.__update('detalle',
                            {'valorUnitario': value, 'importe': importe},
                            'ROWID=%s' % id_producto)
        else:
            self.__update('detalle',
                            {'cantidad': value, 'importe': importe},
                            'ROWID=%s' % id_producto)
        self.__update('impuestos', {'importe': importe}, 'row_id=%s' % id_producto)
        data = self.__select(('detalle',), self.FIELDS, order='pos')
        return data

    def update_pos(self, id_producto, new_pos):
        self.__update('detalle',
                        {'pos': new_pos},
                        'ROWID=%s' % id_producto)

        data = self.__select(('detalle',), self.FIELDS, order='pos')
        return data
