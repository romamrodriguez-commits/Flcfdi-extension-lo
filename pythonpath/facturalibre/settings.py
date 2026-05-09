# -*- coding: utf-8 -*-

DEBUG = False
VERSION = '1.18.2'
IMPLE_NAME = 'org.universolibre.facturalibre.cfdi'
CADENA = '||{version}|{UUID}|{FechaTimbrado}|{selloCFD}|{noCertificadoSAT}||'
CELL_TYPE = 'ScCellObj'
CLEAN = "\{(\w.+)\}"
CLIENTES_COUNT = 101
CURRENCY = 'peso'
DB_NAME = 'facturalibre2.sqlite'
DB_CP = 'cp.sqlite'
DECIMALS = 2
DOUBLE_CLICK = 2
FILE_NAME = '{serie}{folio:06d}_{receptor_rfc}'
FORMAT = '{{0:,.{}f}}'
LIMIT_MARGIN = 23000
MOSTRAR_LIMITE = 1
ULM_NAME = 'Universo Libre México AC'
ULM_WWW = 'http://www.universolibre.org'
NODE = '/{}.Configuration/Settings'.format(IMPLE_NAME)
NODE_PATHS = 'Rutas'
NODE_EMPRESAS = 'Empresas'
PAIS = 'México'
RFC_EXTRANJERO = 'XEXX010101000'
RFC_PUBLICO = 'XAXX010101000'
SAT_WS = 'https://consultaqr.facturaelectronica.sat.gob.mx/consultacfdiservice.svc'
SPLIT = '|'
TITLE = 'Factura Libre CFDI'
WIN = 'win32'

SAT_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope
        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <soap:Header/>
        <soap:Body>
        <Consulta xmlns="http://tempuri.org/">
            <expresionImpresa>
                <![CDATA[?re={emisor_rfc}&rr={receptor_rfc}&tt={total}&id={uuid}]]>
            </expresionImpresa>
        </Consulta>
        </soap:Body>
    </soap:Envelope>"""

LOG = {
    'NAME': 'FL',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'DATE': '%d/%m/%Y %H:%M:%S',
}
CURRENCIES = {
    'mxn': CURRENCY,
}
COLORS = {
    'YELLOW': 16777164,
    'WHITE': 16777215,
}
PAC = {
    'id_test': '2b3a8764-d586-4543-9b7e-82834443f219',
    'id_com': '19771df9-dc85-44b7-a112-0a773d502531',
    'id_ong': '8d7c2ad8-21e0-4b3b-bdfe-14e5f0f3a2d7',
}
BUTTONS = {
    'OK': 1,
    'YES_NO': 3,
    'YES_NO_CANCEL': 4,
}
BUTTON_CLICK = {
    'CLOSE': 0,
    'YES': 2,
    'NO': 3,
}
TYPE_MSG = {
    'ERROR': 'errorbox',
    'WARNING': 'warningbox',
    'QUERY': 'querybox',
}
PRE = {
    '2.0': '{http://www.sat.gob.mx/cfd/2}',
    '2.2': '{http://www.sat.gob.mx/cfd/2}',
    '3.0': '{http://www.sat.gob.mx/cfd/3}',
    '3.2': '{http://www.sat.gob.mx/cfd/3}',
    'TIMBRE': '{http://www.sat.gob.mx/TimbreFiscalDigital}',
}
KEY = {
    'RETURN': 1280,
    'TAB': 1282,
}
EXT = {
    'XML': 'xml',
    'ODS': 'ods',
    'PDF': 'pdf',
}
SEND_MAIL = {
    'ASK': 1,
    'USE_CLIENT': 2,
    'SMTP': 3,
}
ICONS = {
    'ADDENDA': 'addenda.png',
    'ADD': 'add.png',
    'CALC': 'calc.png',
    'CANCEL': 'cancel.png',
    'CLEAN': 'clean.png',
    'CLOSE': 'close.png',
    'CLIENT_INFO': 'client_info.png',
    'CONNECT': 'connect.png',
    'COTIZA': 'cotiza.png',
    'DELETE': 'delete.png',
    'DOWN': 'down.png',
    'EDIT': 'edit.png',
    'FILTER': 'filter.png',
    'FOLDER': 'folder.png',
    'FOLIO': 'folio.png',
    'FIELDS': 'fields.png',
    'FTP': 'ftpcon.png',
    'IMPORT': 'import.png',
    'LOGO': 'logo.png',
    'MAIL': 'mail.png',
    'NOTE': 'note.png',
    'NEW_CLIENT': 'new_client.png',
    'NEW_EMPLOYER': 'new_employer.png',
    'OK': 'ok.png',
    'PAY': 'payed.png',
    'PDF': 'pdf.png',
    'PRINT': 'print.png',
    'PREINVOICE': 'preinvoice.png',
    'PRODUCT_ADD': 'product_add.png',
    'PRODUCT_EDIT': 'product_edit.png',
    'PRODUCT_DELETE': 'product_delete.png',
    'REPORT': 'report.png',
    'REINVOICE': 'reinvoice.png',
    'REGIMEN': 'regimen.png',
    'SAT': 'sat.png',
    'SAVE': 'save.png',
    'SELECT': 'select.png',
    'SETTINGS': 'settings.png',
    'SHOW': 'show.png',
    'SIN_TIMBRAR': 'sintimbrar.png',
    'TOPAY': 'to_pay.png',
    'UP': 'up.png',
    'XML': 'xml.png',
    'XML3': 'file_xml.png',
    'ZERO': 'zero.png',
}
FIELDS_CFDI = {
    'CFDI': ('version',
        'serie',
        'noAprobacion',
        'anoAprobacion',
        'folio',
        'fecha',
        'formaDePago',
        'condicionesDePago',
        'noCertificado',
        'certificado',
        'subTotal',
        'descuento',
        'motivoDescuento',
        'TipoCambio',
        'Moneda',
        'total',
        'tipoDeComprobante',
        'metodoDePago',
        'LugarExpedicion',
        'NumCtaPago'),
    'CUSTOMER': (
        'calle',
        'noExterior',
        'noInterior',
        'colonia',
        'localidad',
        'referencia',
        'municipio',
        'estado',
        'pais',
        'codigoPostal'),
    'DETAILS': (
        'id_cfd',
        'id_producto',
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
        'CuentaPredial'),
}
NIVELES_IEDU = (
    'Preescolar',
    'Primaria',
    'Secundaria',
    'Profesional técnico',
    'Bachillerato o su equivalente'
)

DEFAULT_PAYMENT_METHOD = 'Otros'
PAYMENT_METHODS = {
    'Efectivo': '01',
    'Cheque nominativo': '02',
    'Transferencia electrónica de fondos': '03',
    'Tarjeta de Crédito': '04',
    'Monedero Electrónico': '05',
    'Dinero electrónico': '06',
    'Vales de despensa': '08',
    'Tarjeta de Débito': '28',
    'Tarjeta de Servicio': '29',
    'Otros': '99',
    'No aplica': 'No aplica',
}