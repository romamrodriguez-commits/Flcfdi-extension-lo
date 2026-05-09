# -*- coding: utf-8 -*-

import logging
from facturalibre.settings import LOG, DB_CP, DB_NAME, VERSION, PAYMENT_METHODS
from facturalibre.modulos import util
import sqlite3 as sqlite


buffer = memoryview
log = logging.getLogger(LOG['NAME'])


class DBConfig(object):

    def __init__(self, path_db):
        self.path_db = path_db
        self.path_cp, _, name, _ = util.path_info(__file__)
        self.path_cp = util.join(self.path_cp, DB_CP)
        exists = util.exists(self.path_db)
        self.con = sqlite.Connection(self.path_db)
        self.error = ''
        if exists:
            self._validate_cfdi()
        self._create_tables()
        self._create_tables_nomina()

    def backup(self):
        path, _, _, _ = util.path_info(self.path_db)
        today = util.now()
        name = today.strftime('facturalibre_%d_%m_%Y_%H_%M_%S.zip')
        path = util.join(path, name)
        util.files_to_zip(path, (self.path_db,))
        log.info('BK to: {}'.format(path))
        return

    def _validate_cfdi(self):
        version = self.get_option('fldb_version')
        if version == VERSION:
            return

        self._states()
        self._table_complements()
        self._validate_complements()
        self._table_payment_methods()
        self._update_version_db()

        try:
            data = self.select_field('impuestos', 'redondear')
        except:
            sql = "ALTER TABLE impuestos ADD COLUMN redondear INTEGER DEFAULT 0"
            self.execute(sql)
        rows = self.select(('tiposimpuestos',), ('tipo',), "tipo='ICIC'")
        if not rows:
            sql = "INSERT INTO tiposimpuestos (tipo) VALUES ('ICIC')"
            self.execute(sql)
        try:
            data = self.select_field('cfdfacturas', 'fecha_timbrado')
        except:
            sql = "ALTER TABLE cfdfacturas ADD COLUMN fecha_timbrado TIMESTAMP"
            self.execute(sql)
            sql = "UPDATE cfdfacturas SET fecha_timbrado=fecha"
            self.execute(sql)
        try:
            data = self.select_field('cfdfacturas', 'xml_acuse')
        except:
            sql = "ALTER TABLE cfdfacturas ADD COLUMN xml_acuse TEXT DEFAULT ''"
            self.execute(sql)
        try:
            data = self.select_field('cuentasbanco', 'saldo')
        except:
            sql = "ALTER TABLE cuentasbanco ADD COLUMN saldo FLOAT DEFAULT 0"
            self.execute(sql)
            sql = "UPDATE cuentasbanco SET saldo=0"
            self.execute(sql)
        try:
            data = self.select_field('emisor', 'registro')
        except:
            sql = "ALTER TABLE emisor ADD COLUMN registro TEXT DEFAULT ''"
            self.execute(sql)
        try:
            data = self.select_field('prefacturas', 'id_folio')
        except:
            sql = 'ALTER TABLE prefacturas ADD COLUMN id_folio INTEGER ' \
                'NOT NULL DEFAULT -1'
            self.execute(sql)
        return

    def _create_tables(self):
        sql = """
            CREATE TABLE IF NOT EXISTS certificado(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cer,
                key,
                pem TEXT DEFAULT '',
                certificado TEXT DEFAULT '',
                noCertificado TEXT DEFAULT '',
                inicio TIMESTAMP,
                final TIMESTAMP,
                nombre TEXT COLLATE NOCASE DEFAULT '',
                rfc TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS tiposcfdi(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS tipocontribuyente(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS estados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estado TEXT COLLATE NOCASE DEFAULT '',
                clave TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS emisor(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfc TEXT COLLATE NOCASE DEFAULT '',
                nombre TEXT COLLATE NOCASE DEFAULT '',
                calle TEXT COLLATE NOCASE DEFAULT '',
                noExterior TEXT COLLATE NOCASE DEFAULT '',
                noInterior TEXT COLLATE NOCASE DEFAULT '',
                colonia TEXT COLLATE NOCASE DEFAULT '',
                localidad  TEXT COLLATE NOCASE DEFAULT '',
                referencia  TEXT COLLATE NOCASE DEFAULT '',
                municipio TEXT COLLATE NOCASE DEFAULT '',
                estado TEXT COLLATE NOCASE DEFAULT '',
                pais TEXT COLLATE NOCASE DEFAULT '',
                codigoPostal TEXT DEFAULT '',
                telefono TEXT COLLATE NOCASE DEFAULT '',
                correo TEXT COLLATE NOCASE DEFAULT '',
                web TEXT COLLATE NOCASE DEFAULT '',
                tipo INTEGER DEFAULT 0,
                noAutorizacion TEXT DEFAULT '',
                fechaAutorizacion TIMESTAMP,
                escuela INTEGER DEFAULT 0,
                registro TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS expedidoen(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calle TEXT COLLATE NOCASE DEFAULT '',
                noExterior TEXT COLLATE NOCASE DEFAULT '',
                noInterior TEXT COLLATE NOCASE DEFAULT '',
                colonia TEXT COLLATE NOCASE DEFAULT '',
                localidad TEXT COLLATE NOCASE DEFAULT '',
                referencia TEXT COLLATE NOCASE DEFAULT '',
                municipio TEXT COLLATE NOCASE DEFAULT '',
                estado TEXT COLLATE NOCASE DEFAULT '',
                pais TEXT COLLATE NOCASE DEFAULT '',
                codigoPostal TEXT DEFAULT '',
                telefono TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS regimenesfiscales(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Regimen TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS folios(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serie TEXT COLLATE NOCASE DEFAULT '',
                inicio INTEGER DEFAULT 0,
                usarcon INTEGER DEFAULT 0,
                predeterminado INTEGER DEFAULT 0,
                plantilla TEXT DEFAULT '',
                donativo INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS unidades(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unidad TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS categorias(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT COLLATE NOCASE DEFAULT '',
                id_padre INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS condicionesdepago(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                condiciondepago TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS metodosdepago(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metododepago TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS aduanas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aduana TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS monedas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                moneda TEXT COLLATE NOCASE DEFAULT '',
                prefijo TEXT COLLATE NOCASE DEFAULT '',
                sufijo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS tiposimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS impuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT COLLATE NOCASE DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS campospersonalizados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campo TEXT COLLATE NOCASE DEFAULT '',
                celda1 TEXT COLLATE NOCASE DEFAULT '',
                celda2 TEXT COLLATE NOCASE DEFAULT '',
                nodo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS addendapersonalizada(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nodo TEXT COLLATE NOCASE DEFAULT '',
                atributo1 TEXT COLLATE NOCASE DEFAULT '',
                atributo2 TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS estatuspersonalizados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estatus TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS rutasespejo(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS correo(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servidor TEXT DEFAULT '',
                puerto INTEGER  DEFAULT 26,
                usuario TEXT DEFAULT '',
                contrasena TEXT DEFAULT '',
                copia TEXT DEFAULT '',
                asunto TEXT DEFAULT '',
                cuerpo TEXT DEFAULT '',
                starttls INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS options(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campo TEXT COLLATE NOCASE,
                valor);
            CREATE TABLE IF NOT EXISTS opciones(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_estado INTEGER DEFAULT 0,
                id_unidad INTEGER DEFAULT 0,
                id_impuesto INTEGER DEFAULT 0,
                decimales INTEGER DEFAULT 2,
                minfolios INTEGER DEFAULT 100,
                ftpservidor TEXT DEFAULT '',
                ftpusuario TEXT DEFAULT '',
                ftpcontrasena TEXT DEFAULT '',
                plantilla TEXT DEFAULT '',
                plantilla2 TEXT DEFAULT '',
                opcion1 INTEGER DEFAULT 0,
                opcion2 INTEGER DEFAULT 0,
                opcion3 INTEGER DEFAULT 0,
                opcion4 INTEGER DEFAULT 0,
                opcion5 INTEGER DEFAULT 0,
                opcion6 INTEGER DEFAULT 0,
                opcion7 INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS opciones2(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opcion1 INTEGER DEFAULT 0,
                opcion2 INTEGER DEFAULT 0,
                opcion3 INTEGER DEFAULT 0,
                opcion4 INTEGER DEFAULT 0,
                opcion5 INTEGER DEFAULT 0,
                opcion6 INTEGER DEFAULT 0,
                opcion7 INTEGER DEFAULT 0,
                opcion8 INTEGER DEFAULT 0,
                opcion9 INTEGER DEFAULT 0,
                opcion10 INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS sat(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ftpsat TEXT DEFAULT '',
                dirsat TEXT DEFAULT '',
                xmlcfdi1 TEXT DEFAULT '',
                xmlcfdi2 TEXT DEFAULT '',
                xmlcfdi3 TEXT DEFAULT '',
                xmlversion TEXT DEFAULT '',
                donat1 TEXT DEFAULT '',
                donat2 TEXT DEFAULT '',
                dversion TEXT DEFAULT '',
                dleyenda TEXT DEFAULT '',
                edu1 TEXT DEFAULT '',
                edu2 TEXT DEFAULT '',
                eduversion TEXT DEFAULT '',
                prefijo TEXT DEFAULT '',
                algoritmo TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS receptores(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfc TEXT COLLATE NOCASE DEFAULT '',
                nombre TEXT COLLATE NOCASE DEFAULT '',
                calle TEXT COLLATE NOCASE DEFAULT '',
                noExterior TEXT COLLATE NOCASE DEFAULT '',
                noInterior TEXT COLLATE NOCASE DEFAULT '',
                colonia TEXT COLLATE NOCASE DEFAULT '',
                localidad TEXT COLLATE NOCASE DEFAULT '',
                referencia TEXT COLLATE NOCASE DEFAULT '',
                municipio TEXT COLLATE NOCASE DEFAULT '',
                estado TEXT COLLATE NOCASE DEFAULT '',
                pais TEXT COLLATE NOCASE DEFAULT '',
                codigoPostal TEXT DEFAULT '',
                extranjero INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                fechaalta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notas TEXT COLLATE NOCASE DEFAULT '',
                metododepago TEXT COLLATE NOCASE DEFAULT '',
                cuentadepago TEXT COLLATE NOCASE DEFAULT '',
                condiciondepago TEXT COLLATE NOCASE DEFAULT '',
                id_addenda INTEGER DEFAULT 0,
                cuentaCliente TEXT COLLATE NOCASE DEFAULT '',
                cuentaProveedor TEXT COLLATE NOCASE DEFAULT '',
                saldoCliente FLOAT DEFAULT 0,
                saldoProveedor FLOAT DEFAULT 0,
                esCliente INTEGER DEFAULT 0,
                esProveedor INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS correos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER DEFAULT 0,
                correo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS telefonos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER DEFAULT 0,
                telefono TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS contactos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER DEFAULT 0,
                contacto TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS productos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_categoria INTEGER DEFAULT 0,
                noIdentificacion TEXT COLLATE NOCASE DEFAULT '',
                descripcion TEXT COLLATE NOCASE DEFAULT '',
                unidad TEXT COLLATE NOCASE DEFAULT '',
                valorUnitario FLOAT DEFAULT 0,
                existencia FLOAT DEFAULT 0,
                inventario INTEGER DEFAULT 0,
                codigobarras TEXT DEFAULT '',
                CuentaPredial TEXT DEFAULT '',
                precio_compra FLOAT DEFAULT 0,
                minimo FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS productosimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_producto INTEGER DEFAULT 0,
                id_impuesto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS cfdfacturas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT DEFAULT '',
                serie TEXT COLLATE NOCASE DEFAULT '',
                noAprobacion TEXT DEFAULT '',
                anoAprobacion TEXT DEFAULT '',
                folio INTEGER DEFAULT 0,
                fecha TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                fecha_timbrado TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                formaDePago TEXT DEFAULT '',
                noCertificado TEXT DEFAULT '',
                certificado TEXT DEFAULT '',
                condicionesDePago TEXT DEFAULT '',
                subTotal FLOAT DEFAULT 0,
                descuento FLOAT DEFAULT 0,
                motivoDescuento TEXT DEFAULT '',
                TipoCambio FLOAT DEFAULT 0,
                Moneda TEXT DEFAULT '',
                total FLOAT DEFAULT 0,
                tipoDeComprobante TEXT DEFAULT '',
                metodoDePago TEXT DEFAULT '',
                LugarExpedicion TEXT DEFAULT '',
                NumCtaPago TEXT DEFAULT '',
                totalImpuestosRetenidos FLOAT,
                totalImpuestosTrasladados FLOAT,
                xml TEXT DEFAULT '',
                id_cliente INTEGER DEFAULT 0,
                notas TEXT DEFAULT '',
                uuid TEXT DEFAULT '',
                donativo INTEGER DEFAULT 0,
                estatus TEXT COLLATE NOCASE DEFAULT '',
                regimen TEXT DEFAULT '',
                id_folio INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS prefacturas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT DEFAULT '',
                serie TEXT COLLATE NOCASE DEFAULT '',
                noAprobacion TEXT DEFAULT '',
                anoAprobacion TEXT DEFAULT '',
                folio INTEGER DEFAULT 0,
                fecha TIMESTAMP,
                formaDePago TEXT DEFAULT '',
                noCertificado TEXT DEFAULT '',
                certificado TEXT DEFAULT '',
                condicionesDePago TEXT DEFAULT '',
                subTotal FLOAT DEFAULT 0,
                descuento FLOAT DEFAULT 0,
                motivoDescuento TEXT DEFAULT '',
                TipoCambio FLOAT DEFAULT 0,
                Moneda TEXT DEFAULT '',
                total FLOAT DEFAULT 0,
                tipoDeComprobante TEXT DEFAULT '',
                metodoDePago TEXT DEFAULT '',
                LugarExpedicion TEXT DEFAULT '',
                NumCtaPago TEXT DEFAULT '',
                FolioFiscalOrig INTEGER DEFAULT 0,
                SerieFolioFiscalOrig TEXT DEFAULT '',
                FechaFolioFiscalOrig TIMESTAMP,
                MontoFolioFiscalOrig FLOAT DEFAULT 0,
                totalImpuestosRetenidos FLOAT,
                totalImpuestosTrasladados FLOAT,
                xml TEXT DEFAULT '',
                id_cliente INTEGER DEFAULT 0,
                notas TEXT DEFAULT '',
                uuid TEXT DEFAULT '',
                donativo INTEGER DEFAULT 0,
                estatus INTEGER DEFAULT 1,
                regimen TEXT DEFAULT '',
                id_folio INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS cfddetalle(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                categoria TEXT COLLATE NOCASE DEFAULT '',
                cantidad FLOAT DEFAULT 0,
                unidad TEXT DEFAULT '',
                noIdentificacion TEXT COLLATE NOCASE DEFAULT '',
                descripcion TEXT COLLATE NOCASE DEFAULT '',
                valorUnitario FLOAT DEFAULT 0,
                importe FLOAT DEFAULT 0,
                numero TEXT DEFAULT '',
                fecha TIMESTAMP,
                aduana TEXT DEFAULT '',
                CuentaPredial TEXT DEFAULT '',
                version TEXT COLLATE NOCASE DEFAULT '',
                alumno TEXT COLLATE NOCASE DEFAULT '',
                curp TEXT COLLATE NOCASE DEFAULT '',
                nivel TEXT COLLATE NOCASE DEFAULT '',
                autorizacion TEXT COLLATE NOCASE DEFAULT '',
                id_producto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS predetalle(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                categoria TEXT COLLATE NOCASE DEFAULT '',
                cantidad FLOAT DEFAULT 0,
                unidad TEXT DEFAULT '',
                noIdentificacion TEXT COLLATE NOCASE DEFAULT '',
                descripcion TEXT COLLATE NOCASE DEFAULT '',
                valorUnitario FLOAT DEFAULT 0,
                importe FLOAT DEFAULT 0,
                numero TEXT DEFAULT '',
                fecha TIMESTAMP,
                aduana TEXT DEFAULT '',
                CuentaPredial TEXT DEFAULT '',
                version TEXT COLLATE NOCASE DEFAULT '',
                alumno TEXT COLLATE NOCASE DEFAULT '',
                curp TEXT COLLATE NOCASE DEFAULT '',
                nivel TEXT COLLATE NOCASE DEFAULT '',
                autorizacion TEXT COLLATE NOCASE DEFAULT '',
                id_producto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS detalleimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                id_producto INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS predetalleimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                id_producto INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS cfdimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS preimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS cfdpersonalizados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                campo TEXT COLLATE NOCASE,
                valor TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS prepersonalizados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                campo TEXT COLLATE NOCASE,
                valor TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS bancos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT DEFAULT '',
                banco TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS cuentasbanco(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER DEFAULT 0,
                id_banco INTEGER DEFAULT 0,
                cuenta TEXT DEFAULT '',
                tipo_pago TEXT DEFAULT '',
                saldo FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS addendas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT COLLATE NOCASE DEFAULT '',
                addenda TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS asignaciones(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_addenda INTEGER DEFAULT 0,
                origen TEXT DEFAULT '',
                destino TEXT DEFAULT '',
                origen2 TEXT DEFAULT '',
                destino2 TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS camposreportes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campo TEXT DEFAULT '',
                mostrar TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS reportes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT COLLATE NOCASE DEFAULT '',
                sql TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS celdas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campo TEXT COLLATE NOCASE DEFAULT '',
                celda1 TEXT COLLATE NOCASE DEFAULT '',
                celda2 TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS leyendas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leyenda TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS cfdleyendas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfd INTEGER DEFAULT 0,
                leyenda TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS compras(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT DEFAULT '',
                serie TEXT COLLATE NOCASE DEFAULT '',
                folio INTEGER DEFAULT 0,
                fecha TIMESTAMP,
                formaDePago TEXT DEFAULT '',
                noCertificado TEXT DEFAULT '',
                condicionesDePago TEXT DEFAULT '',
                subTotal FLOAT DEFAULT 0,
                descuento FLOAT DEFAULT 0,
                motivoDescuento TEXT DEFAULT '',
                TipoCambio FLOAT DEFAULT 0,
                Moneda TEXT DEFAULT '',
                total FLOAT DEFAULT 0,
                tipoDeComprobante TEXT DEFAULT '',
                metodoDePago TEXT DEFAULT '',
                LugarExpedicion TEXT DEFAULT '',
                NumCtaPago TEXT DEFAULT '',
                totalImpuestosRetenidos FLOAT,
                totalImpuestosTrasladados FLOAT,
                xml TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                id_proveedor INTEGER DEFAULT 0,
                uuid TEXT DEFAULT '',
                estatus INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS ordenes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serie TEXT COLLATE NOCASE DEFAULT '',
                folio INTEGER DEFAULT 0,
                fecha TIMESTAMP,
                condicionesDePago TEXT DEFAULT '',
                subTotal FLOAT DEFAULT 0,
                descuento FLOAT DEFAULT 0,
                motivoDescuento TEXT DEFAULT '',
                TipoCambio FLOAT DEFAULT 0,
                Moneda TEXT DEFAULT '',
                total FLOAT DEFAULT 0,
                metodoDePago TEXT DEFAULT '',
                LugarExpedicion TEXT DEFAULT '',
                totalImpuestosRetenidos FLOAT,
                totalImpuestosTrasladados FLOAT,
                id_proveedor INTEGER DEFAULT 0,
                notas TEXT DEFAULT '',
                estatus INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS compradetalle(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_compra INTEGER DEFAULT 0,
                categoria TEXT COLLATE NOCASE DEFAULT '',
                cantidad FLOAT DEFAULT 0,
                unidad TEXT DEFAULT '',
                noIdentificacion TEXT COLLATE NOCASE DEFAULT '',
                descripcion TEXT COLLATE NOCASE DEFAULT '',
                valorUnitario FLOAT DEFAULT 0,
                importe FLOAT DEFAULT 0,
                numero TEXT DEFAULT '',
                fecha TIMESTAMP,
                aduana TEXT DEFAULT '',
                CuentaPredial TEXT DEFAULT '',
                id_producto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS ordendetalle(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_orden INTEGER DEFAULT 0,
                categoria TEXT COLLATE NOCASE DEFAULT '',
                cantidad FLOAT DEFAULT 0,
                unidad TEXT DEFAULT '',
                noIdentificacion TEXT COLLATE NOCASE,
                descripcion TEXT COLLATE NOCASE,
                valorUnitario FLOAT DEFAULT 0,
                importe FLOAT DEFAULT 0,
                numero TEXT DEFAULT '',
                fecha TIMESTAMP,
                aduana TEXT DEFAULT '',
                CuentaPredial TEXT DEFAULT '',
                id_producto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS compradetalleimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_compra INTEGER DEFAULT 0,
                id_producto INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS ordendetalleimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_orden INTEGER DEFAULT 0,
                id_producto INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS compraimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_compra INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS ordenimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_orden INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS niveles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel TEXT COLLATE NOCASE DEFAULT '',
                autorizacion TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS alumnos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER DEFAULT 0,
                alumno TEXT COLLATE NOCASE DEFAULT '',
                curp TEXT COLLATE NOCASE DEFAULT '',
                id_nivel INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS claves(
                id_producto INTEGER DEFAULT 0,
                clave TEXT COLLATE NOCASE DEFAULT '',
                noIdentificacion TEXT COLLATE NOCASE DEFAULT '',
                id_proveedor INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS tickets(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serie TEXT COLLATE NOCASE DEFAULT '',
                folio INTEGER DEFAULT 0,
                fecha TIMESTAMP,
                subtotal FLOAT DEFAULT 0,
                total FLOAT DEFAULT 0,
                metododepago TEXT DEFAULT '',
                id_cliente INTEGER DEFAULT 0,
                notas TEXT DEFAULT '',
                estatus TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS ticketdetalle(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ticket INTEGER DEFAULT 0,
                categoria TEXT COLLATE NOCASE DEFAULT '',
                cantidad FLOAT DEFAULT 0,
                unidad TEXT DEFAULT '',
                noIdentificacion TEXT COLLATE NOCASE DEFAULT '',
                descripcion TEXT COLLATE NOCASE DEFAULT '',
                valorUnitario FLOAT DEFAULT 0,
                importe FLOAT DEFAULT 0,
                id_producto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS ticketimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ticket INTEGER DEFAULT 0,
                nombre TEXT DEFAULT '',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS ticketpersonalizados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ticket INTEGER DEFAULT 0,
                campo TEXT COLLATE NOCASE DEFAULT '',
                valor TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS payment_methods(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT COLLATE NOCASE DEFAULT '',
                code TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS complements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT COLLATE NOCASE DEFAULT '',
                code_name TEXT COLLATE NOCASE DEFAULT '',
                complement TEXT COLLATE NOCASE DEFAULT '',
                version TEXT COLLATE NOCASE DEFAULT '',
                schema TEXT COLLATE NOCASE DEFAULT '',
                xmlns TEXT COLLATE NOCASE DEFAULT '',
                xmlns_value TEXT COLLATE NOCASE DEFAULT '',
                prefijo TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS cfdi_complements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER,
                code_name TEXT COLLATE NOCASE DEFAULT '',
                nodes TEXT COLLATE NOCASE DEFAULT '');
            """
        cursor = self.con.cursor()
        #~ if DRIVER:
        cursor.executescript(sql)
        #~ else:
            #~ cursor.execute(sql)
        self._insert_default_data()
        cursor.close()
        return

    def _create_tables_nomina(self):
        sql = """
            CREATE TABLE IF NOT EXISTS nominasat(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                xmlcfdi1 TEXT DEFAULT '',
                xmlcfdi2 TEXT DEFAULT '',
                xmlcfdi3 TEXT DEFAULT '',
                xmlversion TEXT DEFAULT '',
                nomina TEXT DEFAULT '',
                version TEXT DEFAULT '',
                prefijo TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS empleados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no_empleado TEXT COLLATE NOCASE DEFAULT '',
                rfc TEXT COLLATE NOCASE DEFAULT '',
                curp TEXT COLLATE NOCASE DEFAULT '',
                nombre TEXT COLLATE NOCASE DEFAULT '',
                calle TEXT COLLATE NOCASE DEFAULT '',
                no_exterior TEXT COLLATE NOCASE DEFAULT '',
                no_interior TEXT COLLATE NOCASE DEFAULT '',
                colonia TEXT COLLATE NOCASE DEFAULT '',
                referencia TEXT COLLATE NOCASE DEFAULT '',
                municipio TEXT COLLATE NOCASE DEFAULT '',
                estado TEXT COLLATE NOCASE DEFAULT '',
                pais TEXT COLLATE NOCASE DEFAULT 'México',
                codigo_postal TEXT DEFAULT '',
                extranjero INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_regimen TEXT COLLATE NOCASE DEFAULT '',
                imss TEXT COLLATE NOCASE DEFAULT '',
                periodicidad TEXT COLLATE NOCASE DEFAULT '',
                departamento TEXT COLLATE NOCASE DEFAULT '',
                clabe TEXT COLLATE NOCASE DEFAULT '',
                banco TEXT COLLATE NOCASE DEFAULT '',
                fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                puesto TEXT COLLATE NOCASE DEFAULT '',
                tipo_contrato TEXT COLLATE NOCASE DEFAULT '',
                tipo_jornada TEXT COLLATE NOCASE DEFAULT '',
                salario_base FLOAT DEFAULT 0,
                salario_diario FLOAT DEFAULT 0,
                riesgo_puesto TEXT COLLATE NOCASE DEFAULT '',
                notas TEXT COLLATE NOCASE DEFAULT '');
            CREATE TABLE IF NOT EXISTS nominacfdi(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT DEFAULT '',
                serie TEXT COLLATE NOCASE DEFAULT '',
                folio INTEGER DEFAULT 0,
                fecha TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                fecha_timbrado TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                forma_pago TEXT DEFAULT 'Pago en una sola exhibición',
                no_certificado TEXT DEFAULT '',
                condiciones_pago TEXT DEFAULT '',
                subtotal FLOAT DEFAULT 0,
                descuento FLOAT DEFAULT 0,
                motivo_descuento TEXT DEFAULT 'Deducciones nómina',
                tipo_cambio FLOAT DEFAULT 1.0,
                moneda TEXT DEFAULT 'peso',
                total FLOAT DEFAULT 0,
                tipo_comprobante TEXT DEFAULT 'egreso',
                metodo_pago TEXT DEFAULT '',
                lugar_expedicion TEXT DEFAULT '',
                cuenta_pago TEXT DEFAULT '',
                total_retenido FLOAT DEFAULT 0,
                total_traslado FLOAT DEFAULT 0,
                xml TEXT DEFAULT '',
                empleado TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                uuid TEXT DEFAULT '',
                estatus TEXT COLLATE NOCASE DEFAULT 'Guardado',
                version_nomina TEXT DEFAULT '',
                registro_patronal TEXT DEFAULT '',
                no_empleado TEXT DEFAULT '',
                curp TEXT DEFAULT '',
                tipo_regimen TEXT DEFAULT '',
                imss TEXT DEFAULT '',
                fecha_pago TIMESTAMP,
                fecha_inicial TIMESTAMP,
                fecha_final TIMESTAMP,
                dias_pagados INTEGER DEFAULT 0,
                periodicidad TEXT DEFAULT '',
                departamento TEXT DEFAULT '',
                clabe TEXT DEFAULT '',
                banco INTEGER DEFAULT 0,
                fecha_ingreso TIMESTAMP,
                antiguedad INTEGER DEFAULT 0,
                puesto TEXT DEFAULT '',
                tipo_contrato TEXT DEFAULT '',
                tipo_jornada TEXT DEFAULT '',
                salario_base FLOAT DEFAULT 0,
                salario_diario FLOAT DEFAULT 0,
                riesgo_puesto INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS nominadetalle(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER DEFAULT 0,
                cantidad FLOAT DEFAULT 1,
                unidad TEXT DEFAULT 'Servicio',
                descripcion TEXT COLLATE NOCASE,
                valor_unitario FLOAT DEFAULT 0,
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS nominaimpuestos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER DEFAULT 0,
                nombre TEXT DEFAULT 'ISR',
                tasa TEXT DEFAULT '',
                tipo TEXT DEFAULT 'Retencion',
                importe FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS nominapd(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER DEFAULT 0,
                percepcion INTEGER DEFAULT 1,
                clave TEXT DEFAULT '',
                clave_sat TEXT DEFAULT '',
                concepto TEXT DEFAULT '',
                gravado FLOAT DEFAULT 0,
                exento FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS nominaincapacidad(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER DEFAULT 0,
                dias FLOAT DEFAULT 0,
                tipo_sat TEXT DEFAULT '',
                descuento FLOAT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS nominahorasextra(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER DEFAULT 0,
                dias ENTERO,
                tipo TEXT DEFAULT '',
                horas INTEGER DEFAULT 0,
                importe FLOAT DEFAULT 0);
            """
        cursor = self.con.cursor()
        #~ if DRIVER:
        cursor.executescript(sql)
        #~ else:
            #~ cursor.execute(sql)
        self._insert_default_data_nomina()
        cursor.close()
        return

    def _insert_default_data(self):
        if not self.count('tiposcfdi'):
            values = (('todos',), ('ingreso',), ('egreso',), ('traslado',))
            self.executemany('tiposcfdi', ('tipo',), values)
        if not self.count('tipocontribuyente'):
            values = (('fisica',), ('moral',), ('ong',))
            self.executemany('tipocontribuyente', ('tipo',), values)
        if not self.count('estados'):
            values = (
                ("Aguascalientes", 'AGU'),
                ("Baja California", 'BCN'),
                ("Baja California Sur", 'BCS'),
                ("Campeche", 'CAM'),
                ("Chiapas", 'CHP'),
                ("Chihuahua", 'CHH'),
                ("Coahuila", 'COA'),
                ("Colima", 'COL'),
                ("Ciudad de México", 'CDM'),
                ("Durango", 'DUR'),
                ("Guanajuato", 'GUA'),
                ("Guerrero", 'GRO'),
                ("Hidalgo", 'HID'),
                ("Jalisco", 'JAL'),
                ("Estado de México", 'MEX'),
                ("Michoacán", 'MIC'),
                ("Morelos", 'MOR'),
                ("Nayarit", 'NAY'),
                ("Nuevo León", 'NLE'),
                ("Oaxaca", 'OAX'),
                ("Puebla", 'PUE'),
                ("Querétaro", 'QTO'),
                ("Quintana Roo", 'ROO'),
                ("San Luis Potosí", 'SLP'),
                ("Sinaloa", 'SIN'),
                ("Sonora", 'SON'),
                ("Tabasco", 'TAB'),
                ("Tamaulipas", 'TAM'),
                ("Tlaxcala", 'TLA'),
                ("Veracruz", 'VER'),
                ("Yucatán", 'YUC'),
                ("Zacatecas", 'ZAC'),
            )
            self.executemany('estados', ('estado', 'clave'), values)
        if not self.count('metodosdepago'):
            values = (
                ('No identificado',),
                ('Efectivo',),
                ('Cheque',),
                ('Transferencia Electrónica',)
            )
            self.executemany('metodosdepago',('metododepago',),values)
        if not self.count('monedas'):
            values = (
                ('peso','-(','/100 m.n.)-'),
                ('dólar','-(','/100 usd)-'),
                ('euro','-(','/100 €)-')
            )
            self.executemany('monedas', ('moneda', 'prefijo', 'sufijo'), values)
        if not self.count('tiposimpuestos'):
            values = (
                ('IVA',),
                ('ISR',),
                ('ISH',),
                ('INSPECCION DE OBRA',),
                ('IEPS',),
                ('ICIC',),
            )
            self.executemany('tiposimpuestos',('tipo',),values)
        if not self.count('unidades'):
            values = (('Hora',), ('Pieza',), ('Servicio',))
            self.executemany('unidades', ('unidad',), values)
        if not self.count('categorias'):
            values = (('Productos',0), ('Servicios',0))
            self.executemany('categorias', ('categoria', 'id_padre',), values)
        if not self.count('opciones'):
            values = (1, 0, 0, 0, 2, 100, '', '', '', '', '', 0, 0, 0, 0, 0, 0, 0)
            self.insertrow('opciones', values)
        if not self.count('opciones2'):
            values = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            self.insertrow('opciones2', values)
        if not self.count('sat'):
            values = (1,
                'ftp2.sat.gob.mx',
                '/Certificados/FEA',
                'http://www.sat.gob.mx/cfd/3',
                'http://www.w3.org/2001/XMLSchema-instance',
                'http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv32.xsd',
                '3.2',
                'http://www.sat.gob.mx/donat',
                'http://www.sat.gob.mx/donat http://www.sat.gob.mx/sitio_internet/cfd/donat/donat11.xsd',
                '1.1',
                'Este comprobante ampara un donativo, el cual será destinado por la donataria a los fines propios de su objeto social. En el caso de que los bienes donados hayan sido deducidos previamente para los efectos del impuesto sobre la renta, este donativo no es deducible. La reproducción no autorizada de este comprobante constituye un delito en los términos de las disposiciones fiscales.',
                'http://www.sat.gob.mx/iedu',
                'http://www.sat.gob.mx/iedu http://www.sat.gob.mx/sitio_internet/cfd/iedu/iedu.xsd',
                '1.0',
                'cfdi',
                'sha1')
            self.insertrow('sat', values)
        if not self.count('addendapersonalizada'):
            values = (1, 'empresalibre-org', 'http://empresalibre.org/cfd', 'http://empresalibre.org/cfd/addenda.xsd')
            self.insertrow('addendapersonalizada', values)
        if not self.count('leyendas'):
            values = (1, 'EFECTOS FISCALES AL PAGO')
            self.insertrow('leyendas', values)
        if not self.count('options'):
            values = (1, 'fldb_version', VERSION)
            self.insertrow('options', values)

        if not self.count('payment_methods'):
            fields = ('method', 'code')
            rows = tuple(zip(PAYMENT_METHODS.keys(), PAYMENT_METHODS.values()))
            self.executemany('payment_methods', fields, rows)
        return

    def _insert_default_data_nomina(self):
        if not self.count('nominasat'):
            values = (1,
                'http://www.sat.gob.mx/cfd/3',
                'http://www.w3.org/2001/XMLSchema-instance',
                'http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv32.xsd http://www.sat.gob.mx/nomina http://www.sat.gob.mx/sitio_internet/cfd/nomina/nomina11.xsd',
                '3.2',
                'http://www.sat.gob.mx/nomina',
                '1.1',
                'nomina')
            self.insertrow('nominasat', values)
        if not self.count('bancos'):
            values = (
                ('ABC CAPITAL', 138),
                ('ACCIVAL', 614),
                ('ACTINVER', 133),
                ('AFIRME', 62),
                ('AKALA', 638),
                ('AMERICAN EXPRESS', 103),
                ('ASEA', 652),
                ('AUTOFIN', 128),
                ('AZTECA', 127),
                ('B&B', 610),
                ('BAJIO', 30),
                ('BAMSA', 106),
                ('BANAMEX', 2),
                ('BANCO FAMSA', 131),
                ('BANCOMEXT', 6),
                ('BANCOPPEL', 137),
                ('BANJERCITO', 19),
                ('BANOBRAS', 9),
                ('BANORTE', 72),
                ('BANREGIO', 58),
                ('BANSEFI', 166),
                ('BANSI', 60),
                ('BARCLAYS', 129),
                ('BBASE', 145),
                ('BBVA BANCOMER', 12),
                ('BMONEX', 112),
                ('BMULTIVA', 132),
                ('BULLTICK CB', 632),
                ('CB ACTINVER', 621),
                ('CB INTERCAM', 630),
                ('CB JPMORGAN', 640),
                ('CBDEUTSCHE', 626),
                ('CI BOLSA', 631),
                ('CIBANCO', 143),
                ('CLS', 901),
                ('COMPARTAMOS', 130),
                ('CONSUBANCO', 140),
                ('CREDIT SUISSE', 126),
                ('DEUTSCHE', 124),
                ('ESTRUCTURADORES', 606),
                ('EVERCORE', 648),
                ('FINAMEX', 616),
                ('FINCOMUN', 634),
                ('GBM', 601),
                ('HDI SEGUROS', 636),
                ('HIPOTECARIA FEDERAL', 168),
                ('HSBC', 21),
                ('INBURSA', 36),
                ('INDEVAL', 902),
                ('ING', 116),
                ('INTERACCIONES', 37),
                ('INTERBANCO', 136),
                ('INVEX', 59),
                ('IXE', 32),
                ('JP MORGAN', 110),
                ('KUSPIT', 653),
                ('LIBERTAD', 670),
                ('MAPFRE', 619),
                ('MASARI', 602),
                ('MERRILL LYNCH', 615),
                ('MIFEL', 42),
                ('MONEXCB', 600),
                ('NAFIN', 135),
                ('OACTIN', 622),
                ('OPCIONES EMPRESARIALES DEL NOROESTE', 659),
                ('ORDER', 637),
                ('PROFUTURO', 620),
                ('REFORMA', 642),
                ('SANTANDER', 14),
                ('SCOTIABANK', 44),
                ('SEGMTY', 651),
                ('SKANDIA', 623),
                ('SKANDIA', 649),
                ('SOFIEXPRESS', 655),
                ('STERLING', 633),
                ('STP', 646),
                ('SU CASITA', 629),
                ('TELECOMM', 647),
                ('THE ROYAL BANK', 102),
                ('TIBER', 607),
                ('TOKYO', 108),
                ('UBS BANK', 139),
                ('UNAGRA', 656),
                ('UNICA', 618),
                ('VALMEX', 617),
                ('VALUE', 605),
                ('VE POR MAS', 113),
                ('VECTOR', 608),
                ('VOLKSWAGEN', 141),
                ('WAL-MART', 134),
                ('ZURICH', 627),
                ('ZURICHVI', 628)
            )
            self.executemany('bancos', ('banco', 'clave'), values)
        return

    def count(self, table_name):
        cursor = self.con.cursor()
        sql = 'SELECT COUNT(rowid) FROM %s' % table_name
        for row in cursor.execute(sql):
            c = row[0]
        cursor.close()
        return c

    def executemany(self, table_name, fields, values, commit=True):
        cursor = self.con.cursor()
        questions = '?,' * (len(fields) - 1) + '?'
        fields2 = ','.join(fields)
        sql = 'INSERT INTO %s(%s) values(%s)' % (table_name, fields2, questions)
        cursor.executemany(sql, values)
        #~ if DRIVER:
        if commit:
            self.con.commit()
        cursor.close()
        return

    def insertrow(self, table_name, values, commit=True):
        cursor = self.con.cursor()
        questions = '?,' * (len(values)-1) + '?'
        if isinstance(values, tuple):
            values2 = values
            sql = 'INSERT INTO %s values(%s)' % (table_name, questions)
        elif isinstance(values, dict):
            fields = ','.join(list(values.keys()))
            values2 = list(values.values())
            sql = 'INSERT INTO %s(%s) values(%s)' % (table_name, fields, questions)
        cursor.execute(sql, values2)
        if commit:
            self.con.commit()
        new_row = cursor.lastrowid
        cursor.close()
        return new_row

    def select_field(self, table_name, field_name):
        cursor = self.con.cursor()
        sql = 'SELECT %s FROM %s LIMIT 1' % (field_name, table_name)
        for row in cursor.execute(sql):
            cursor.close()
            return row[0]
        cursor.close()
        return ''

    def select(self, tables_names, fields=(), where='', order='', other1='', groupby=''):
        cursor = self.con.cursor()
        tables = ','.join(tables_names)
        if fields:
            fields2 = ','.join(fields)
        else:
            fields2 = '*'
        sql = 'SELECT {} FROM {}'.format(fields2, tables)
        if other1:
            sql += ' {}'.format(other1)
        if where:
            sql += ' WHERE {}'.format(where)
        if groupby:
            sql += ' GROUP BY {}'.format(groupby)
        if order:
            sql += ' ORDER BY {}'.format(order)
        #~ log.info(sql)
        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
            return data
        except sqlite.OperationalError as msg:
            log.error(sql)
            log.error(msg)
        else:
            log.error('SELECT: ', exc_info=True)
        return

    def update(self, table_name, values={}, where='', sin=False):
        cursor = self.con.cursor()
        new_values = []
        for key, value in values.items():
            if isinstance(value, str):
                if sin:
                    new_values.append("%s=%s" % (key, value))
                else:
                    new_values.append("%s='%s'" % (key, value))
            else:
                new_values.append("%s=%s" % (key, value))
        sql = "UPDATE %s SET %s" % (table_name, ','.join(new_values))
        #~ log.info(sql)
        if where:
            sql += ' WHERE %s' % where
        try:
            res = cursor.execute(sql)
            #~ if DRIVER:
            self.con.commit()
            return True
        except sqlite.OperationalError as msg:
            log.error(sql)
            log.error(msg)
            return False

    def update_or_insert(self, table, data):
        field = self.select((table,), ('id',), data['where'])
        del data['where']
        if field:
            self.update(table, data, 'id={}'.format(field[0][0]))
        else:
            self.insertrow(table, data)
        return

    #~ def get_option(self, field):
        #~ data = self.select(('options',), ('valor',), "campo='%s'" % field)
        #~ value = ''
        #~ if data:
            #~ value = data[0][0]
        #~ return value

    def delete(self, table_name, where=''):
        cursor = self.con.cursor()
        sql = 'DELETE FROM %s' % table_name
        if where:
            sql += ' WHERE %s' % where
        cursor.execute(sql)
        if not where:
            sql = "DELETE FROM SQLITE_SEQUENCE WHERE name='%s'" % (table_name)
            cursor.execute(sql)
        #~ if DRIVER:
        self.con.commit()
        return

    def load_file(self, path):
        data = util.load_file(path, True)
        return buffer(data)

    def get_cp_data(self, cp):
        if not util.exists(self.path_cp):
            return None
        con = sqlite.Connection(self.path_cp)
        cursor = con.cursor()
        sql = """
            SELECT colonia, municipio, estado
            FROM colonias, municipios, estados
            WHERE colonias.id_municipio=municipios.id
                AND municipios.id_estado=estados.id
                AND cp='{}'
            ORDER BY colonia""".format(cp)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        con.close()
        return data

    def get_emisor(self, path):
        emisor = ''
        path_db = util.join(path, DB_NAME)
        if not util.exists(path_db):
            return emisor
        con = sqlite.Connection(path_db)
        cursor = con.cursor()
        sql = "SELECT nombre FROM emisor"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        con.close()
        if data:
            emisor = data[0][0]
        return emisor

    def execute(self, sql):
        cursor = self.con.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        return data

    def has_data(self, table):
        data = self.select((table,), ('id',), other1='LIMIT 1')
        return bool(data)

    def sql(self, name, where=''):
        if name == 'get_products':
            extra = 'LEFT OUTER JOIN categorias ' \
                'ON productos.id_categoria = categorias.id'
            data = self.select(
                ('productos',),
                ('productos.id',
                    "CASE WHEN id_categoria THEN categoria ELSE '' END",
                    'noIdentificacion',
                    'descripcion',
                    'unidad',
                    'valorUnitario',
                    "CASE WHEN inventario THEN existencia ELSE '' END"),
                where=where,
                order='descripcion',
                other1=extra)
        elif name == 'get_phones':
            data = self.select(('telefonos',), ('telefono',), where=where)
        elif name == 'get_mails':
            data = self.select(('correos',), ('correo',), where=where)
        return data

    def get_description(self, id_product):
        data = self.select(('productos',), ('descripcion', ), 'id={}'.format(id_product))
        if data:
            return data[0][0]
        return ''

    # For v2
    def get_table(self, table, order='', fields=()):
        return self.select((table,), fields=fields, order=order)

    def get_option(self, field, default=''):
        value = default
        data = self.select(('options',), ('valor',), "campo='%s'" % field)
        if data and data[0][0]:
            value = data[0][0]
        return value

    def get_options(self):
        rows = self.get_table('options')
        data = {r[1]: r[2] for r in rows}
        return data

    def _states(self):
        values = (
            ("Aguascalientes", 'AGU'),
            ("Baja California", 'BCN'),
            ("Baja California Sur", 'BCS'),
            ("Campeche", 'CAM'),
            ("Chiapas", 'CHP'),
            ("Chihuahua", 'CHH'),
            ("Coahuila", 'COA'),
            ("Colima", 'COL'),
            ("Ciudad de México", 'CDM'),
            ("Durango", 'DUR'),
            ("Guanajuato", 'GUA'),
            ("Guerrero", 'GRO'),
            ("Hidalgo", 'HID'),
            ("Jalisco", 'JAL'),
            ("Estado de México", 'MEX'),
            ("Michoacán", 'MIC'),
            ("Morelos", 'MOR'),
            ("Nayarit", 'NAY'),
            ("Nuevo León", 'NLE'),
            ("Oaxaca", 'OAX'),
            ("Puebla", 'PUE'),
            ("Querétaro", 'QTO'),
            ("Quintana Roo", 'ROO'),
            ("San Luis Potosí", 'SLP'),
            ("Sinaloa", 'SIN'),
            ("Sonora", 'SON'),
            ("Tabasco", 'TAB'),
            ("Tamaulipas", 'TAM'),
            ("Tlaxcala", 'TLA'),
            ("Veracruz", 'VER'),
            ("Yucatán", 'YUC'),
            ("Zacatecas", 'ZAC'),
        )
        sql = "UPDATE estados SET estado='Ciudad de México' WHERE estado='México, D.F.'"
        self.execute(sql)
        sql = "UPDATE receptores SET estado='Ciudad de México' WHERE estado='México, D.F.'"
        self.execute(sql)

        try:
            data = self.select_field('estados', 'clave')
            return
        except:
            sql = "ALTER TABLE estados ADD COLUMN clave TEXT DEFAULT ''"
            self.execute(sql)

        for row in values:
            data = (row[1], row[0])
            sql = "UPDATE estados SET clave='{}' WHERE estado='{}'".format(*data)
            self.execute(sql)
        return

    def _table_payment_methods(self):
        try:
            data = self.select_field('payment_methods', 'id')
            return
        except:
            pass
        sql = """
            CREATE TABLE IF NOT EXISTS payment_methods(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT COLLATE NOCASE DEFAULT '',
                code TEXT COLLATE NOCASE DEFAULT ''
            )
        """
        self.execute(sql)

        fields = ('method', 'code')
        rows = tuple(zip(PAYMENT_METHODS.keys(), PAYMENT_METHODS.values()))
        self.executemany('payment_methods', fields, rows)
        return

    def _table_complements(self):
        try:
            data = self.select_field('complements', 'id')
            return
        except:
            pass
        sql = """
            CREATE TABLE IF NOT EXISTS complements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT COLLATE NOCASE DEFAULT '',
                code_name TEXT COLLATE NOCASE DEFAULT '',
                complement TEXT COLLATE NOCASE DEFAULT '',
                version TEXT COLLATE NOCASE DEFAULT '',
                schema TEXT COLLATE NOCASE DEFAULT '',
                xmlns TEXT COLLATE NOCASE DEFAULT '',
                xmlns_value TEXT COLLATE NOCASE DEFAULT '',
                prefijo TEXT COLLATE NOCASE DEFAULT ''
            )
        """
        self.execute(sql)

        sql = """
            CREATE TABLE IF NOT EXISTS cfdi_complements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cfdi INTEGER,
                code_name TEXT COLLATE NOCASE DEFAULT '',
                nodes TEXT COLLATE NOCASE DEFAULT ''
            )
        """
        self.execute(sql)
        return

    def _validate_complements(self):
        path_bin = util.get_dir_ext('bin')
        fields = (
            'name',
            'code_name',
            'complement',
            'version',
            'schema',
            'xmlns',
            'xmlns_value',
            'prefijo',
        )
        schema = 'http://www.sat.gob.mx/donat http://www.sat.gob.mx/sitio_internet/cfd/donat/donat11.xsd'
        values_donat = [
            'Donatarias',
            'donatarias',
            '',
            '1.1',
            schema,
            'xmlns:donat',
            'http://www.sat.gob.mx/donat',
            'donat:Donatarias',
        ]
        schema = 'http://www.sat.gob.mx/ine http://www.sat.gob.mx/sitio_internet/cfd/ine/ine10.xsd'
        values_ine = [
            'INE',
            'ine',
            '',
            '1.0',
            schema,
            'xmlns:ine',
            'http://www.sat.gob.mx/ine',
            'ine:INE',
        ]
        complements = (values_donat, values_ine)
        for complement in complements:
            where = "code_name='{}'".format(complement[1])
            data = self.select(('complements',), ('id',), where=where)
            if not data:
                path = util.join(path_bin, '{}.xml'.format(complement[1]))
                content = util.load_file(path)
                complement[2] = content
                self.executemany('complements', fields, (complement,))
        return

    def _update_version_db(self):
        sql = "UPDATE options SET valor='{}' " \
            "WHERE campo='fldb_version'".format(VERSION)
        self.execute(sql)
        return
