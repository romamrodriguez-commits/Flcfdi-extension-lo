import traceback
import time
from facturalibre.modulos.pyXml import CFDIXMLNOMINA
from facturalibre.settings import PAYMENT_METHODS

SERIE_NOMINA = 'NOMINA'
CELDA_INICIAL = 'A4'
COL_INIT = 26
STEP = 2
P = 'P'
D = 'D'
TIPO_REGIMEN = {
    'Sueldos y salarios': 2,
    'Jubilados': 3,
    'Pensionados': 4,
    'Asimilados a salarios, Miembros de las Sociedades Cooperativas de Producción': 5,
    'Asimilados a salarios, Integrantes de Sociedades y Asociaciones Civiles': 6,
    'Asimilados a salarios, Miembros de consejos directivos, de vigilancia, consultivos, honorarios a administradores, comisarios y gerentes generales': 7,
    'Asimilados a salarios, Actividad empresarial (comisionistas)': 8,
    'Asimilados a salarios, Honorarios asimilados a salarios': 9,
    'Asimilados a salarios, Ingresos acciones o títulos valor': 10,
}
RIESGO_PUESTO = {
    '': 0,
    'Clase I': 1,
    'Clase II': 2,
    'Clase III': 3,
    'Clase IV': 4,
    'Clase V': 5
}
TIPO_INCAPACIDAD = {
    'Riesgo de trabajo': 1,
    'Enfermedad en general': 2,
    'Maternidad': 3
}


class EventosNomina(object):

    def __init__(self, caller):
        self.caller = caller
        self.globales = caller.globales
        self.util = caller.util
        self.unogui = caller.unogui
        self.db = caller.db
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()
        self.doc = None
        self.hojas = None
        self.empleados = None
        self.comprobante = {}
        self.regimenfiscal = ''
        self.rfc = ''
        self.rutas = None
        self._init_data()

    def _init_data(self):
        version = self.db.select_field('sat', 'xmlversion')
        version_nomina = self.db.select_field('nominasat', 'version')
        #~ serie = self.db.select_field('folios', 'serie')
        serie = SERIE_NOMINA
        #~ folio = self.db.select_field('folios', 'inicio')
        no_certificado = self.db.select_field('certificado', 'noCertificado')
        self.regimenfiscal = self.db.select_field('regimenesfiscales', 'Regimen')
        self.rfc = self.db.select_field('certificado', 'rfc')
        rutas = self.db.select(('rutasespejo',), ('ruta',))
        self.rutas = [r[0] for r in rutas]
        self.comprobante['version'] = version
        self.comprobante['version_nomina'] = version_nomina
        self.comprobante['serie'] = serie
        self.comprobante['folio'] = self._get_folio(serie)
        self.comprobante['no_certificado'] = no_certificado
        return

    def cmdEnviar(self):
        try:
            res = self._enviar_timbrar()
            if res:
                msg = 'Todos los documentos se timbraron correctamente'
                self.unogui.createMsgBox({'Message': msg})
            self.msg_user('Proceso terminado...')
        except:
            print (traceback.format_exc())
        return

    def cmdImportar(self):
        try:
            self._validate_sheet()
            res, count = self._guardar_nomina()
            if not res:
                return
            self.msg_user('Nomina guardada...')
            if count:
                msg = 'La nomina se ha importado correctamente'
            else:
                msg = 'No se encontraron nuevos datos a importar'
            self.unogui.createMsgBox({'Message': msg})
            self.cmdCancelar()
            return
        except:
            self.util.debug(traceback.format_exc())
            print (traceback.format_exc())
        return

    def cmdCancelar(self):
        self.dialog.endExecute()
        return

    def _validate_sheet(self):
        self.doc = self.util.get_active_doc()
        self.hojas = self.doc.getSheets()
        return True

    def _validate_data(self, rows, inc, he):
        titles = rows[0]
        for i, v in enumerate(titles):
            if v is None:
                celda = self.empleados.getCellByPosition(i, 0)
                self.doc.getCurrentController().select(celda)
                msg = ('Valor incorrecto en celda: {}\n\n'
                    'Debe ser una clave del SAT'.format(celda.AbsoluteName))
                self.unogui.createMsgBox({'Message': msg})
                return False
        data = rows[3:]
        if len(data) != inc:
            msg = 'Tienes datos vacíos en las incapacidades'
            self.unogui.createMsgBox({'Message': msg})
            return False
        if len(data) != he:
            msg = 'Tienes datos vacíos en las horas extras'
            self.unogui.createMsgBox({'Message': msg})
            return False
        for row in data:
            empleado = row[1]
            if not self._validar_rfc(row[1], row[2]):
                return False
            if not self._validar_curp(row[1], row[3]):
                return False
            if not isinstance(row[5], str):
                msg = '{}:\n\nEl IMSS debe estar formateado como texto'.format(
                    empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
            if not isinstance(row[6], float):
                msg += '{}:\n\nFecha de pago NO es fecha'.format(empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
            if not isinstance(row[7], float):
                msg = '{}:\n\nFecha Inicial de pago NO es fecha'.format(
                    empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
            if not isinstance(row[8], float):
                msg = '{}:\n\nFecha Final de pago NO es fecha'.format(empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
            if not isinstance(row[9], float):
                msg = '{}:\n\nNumero de días pagados NO es número'.format(
                    empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
            if row[12] and len(row[12]) != 18:
                msg = '{}:\n\nLa CLABE bancaria debe ser de 18 digitos'.format(
                    empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
            if row[14] and not isinstance(row[14], float):
                msg = '{}:\n\nFecha de inicio de relación laboral ' \
                    'NO es fecha'.format(empleado)
                self.unogui.createMsgBox({'Message': msg})
                return False
        return True

    def _guardar_nomina(self):
        #~ self.empleados = self.hojas.getByName(HOJA_EMPLEADOS)
        self.empleados = self.doc.getCurrentController().getActiveSheet()
        rows = self._get_rows(self.empleados, CELDA_INICIAL)
        if len(rows) < 4:
            msg = 'No se encontraron datos en la hoja activa'
            self.unogui.createMsgBox({'Message': msg})
            return False, 0

        inc = self._get_next_rows(self.empleados, len(rows[0]))
        he = self._get_next_rows(
            self.empleados, len(rows[0]) + len(inc[0]) + 1)
        if not self._validate_data(rows, len(inc)-1, len(he)-1):
            return False, 0
        msg = 'Los datos son correctos.\n\nPresiona SI para guardar ' \
            'estos datos o NO para salir sin guardar'
        if not self.unogui.createQuestion('Nomina Libre', msg):
            return False, 0
        i = 0
        e = 0
        avance = self.dialog.getControl('pbInfo')
        avance.setRange(0, len(rows))
        for r in rows:
            avance.setValue(i)
            init = self.util.now()
            if i == 0:
                titles1 = r
                i += 1
            elif i == 1:
                titles2 = r
                i += 1
            elif i == 2:
                i += 1
            else:
                i += 1
                e += self._save_row(r, titles1, titles2, inc[i-3], he[i-3])
            dif = self.util.now() - init
            if not dif.total_seconds():
                time.sleep(1)
        return True, e

    def _save_row(self, row, t1, t2, inc, he):
        id_empleado = self._save_empleado(row)
        #~ print ('ID Empleado', id_empleado)
        new_id = self._save_comprobante(row, id_empleado)
        if new_id:
            data = self._save_pd(new_id, row, t1, t2)
            self.db.update('nominacfdi', data, "id=%s" % new_id, True)
            importe = data['subtotal']
            total_retenido = None
            if 'total_retenido' in data:
                total_retenido = data['total_retenido']
            data = {}
            data['id_cfdi'] = new_id
            data['descripcion'] = row[25]
            data['valor_unitario'] = importe
            data['importe'] = importe
            self.db.insertrow('nominadetalle', data)
            data = {}
            if total_retenido:
                data['id_cfdi'] = new_id
                data['importe'] = total_retenido
                self.db.insertrow('nominaimpuestos', data)
            self._save_incapacidad(new_id, inc)
            self._save_horas_extra(new_id, he)
            return new_id
        else:
            return 0

    def _save_incapacidad(self, id_cfdi, row):
        data = {}
        for i in range(0, len(row), 3):
            dias = row[i+1]
            descuento = row[i+2]
            if not dias and not descuento:
                continue
            data['id_cfdi'] = id_cfdi
            data['tipo_sat'] = TIPO_INCAPACIDAD[row[i]]
            data['dias'] = dias
            data['descuento'] = descuento
            self.db.insertrow('nominaincapacidad', data)
        return

    def _save_horas_extra(self, id_cfdi, row):
        data = {}
        for i in range(0, len(row), 4):
            horas = row[i+2]
            importe = row[i+3]
            if not horas and not importe:
                continue
            data['id_cfdi'] = id_cfdi
            data['dias'] = row[i]
            data['tipo'] = row[i+1]
            data['horas'] = horas
            data['importe'] = importe
            self.db.insertrow('nominahorasextra', data)
        return

    def _save_pd(self, id_cfdi, row, t1, t2):
        data = {}
        for i in range(COL_INIT, len(row), STEP):
            gravado = row[i]
            exento = row[i+1]
            if not gravado and not exento:
                continue
            data['id_cfdi'] = id_cfdi
            if t1[i][0] == P:
                data['percepcion'] = 1
            elif t1[i][0] == D:
                data['percepcion'] = 0
            clave = int(t1[i+1])
            data['clave'] = clave
            data['clave_sat'] = clave
            data['concepto'] = t2[i]
            data['gravado'] = gravado
            data['exento'] = exento
            self.db.insertrow('nominapd', data)
        data = {}
        subtotal = self.db.select(
            ('nominapd',),
            ('SUM(gravado)+SUM(exento)',),
            "id_cfdi=%s AND percepcion=1" % id_cfdi)[0][0]
        descuento = self.db.select(
            ('nominapd',),
            ('SUM(gravado)+SUM(exento)',),
            "id_cfdi=%s AND percepcion=0 AND clave!=2" % id_cfdi)[0][0]
        total_retenido = self.db.select(
            ('nominapd',),
            ('gravado+exento',),
            "id_cfdi=%s AND percepcion=0 AND clave=2" % id_cfdi)
        if total_retenido:
            total_retenido = total_retenido[0][0]
        else:
            total_retenido = None
        data['subtotal'] = round(float(subtotal or 0), 2)
        data['descuento'] = round(float(descuento or 0), 2)
        if total_retenido:
            data['total_retenido'] = total_retenido
        data['total'] = round(
            data['subtotal'] - \
            data['descuento'] - \
            round(float(total_retenido or 0), 2), 2)
        return data

    def _save_comprobante(self, row, id_empleado):
        w = "curp='{}' and fecha_pago='{}' and descripcion='{}' and " \
            "estatus!='Cancelado' AND nominacfdi.id=nominadetalle.id_cfdi"
        fecha_pago = str(self.util.calc_to_date(row[6]))
        exists = self.db.select(
            ('nominacfdi', 'nominadetalle'),
            ('nominacfdi.id',),
            w.format(row[3], fecha_pago, row[25]))
        if exists:
            msg = 'Existente: %s' % row[1]
            self.util.debug(msg)
            return False

        banco = self.db.select(
            ('bancos',), ('clave',), "banco='%s'" % row[13])
        if banco:
            banco = int(banco[0][0])
        else:
            banco = 0
        self.comprobante['folio'] = self.comprobante['folio'] + 1
        self.comprobante['no_empleado'] = id_empleado
        self.comprobante['empleado'] = row[1].strip().upper()
        self.comprobante['curp'] = row[3]
        self.comprobante['tipo_regimen'] = TIPO_REGIMEN[row[4].strip()]
        self.comprobante['imss'] = row[5]
        self.comprobante['fecha_pago'] = fecha_pago
        self.comprobante['fecha_inicial'] = str(self.util.calc_to_date(row[7]))
        self.comprobante['fecha_final'] = str(self.util.calc_to_date(row[8]))
        self.comprobante['dias_pagados'] = row[9]
        self.comprobante['periodicidad'] = row[10]
        self.comprobante['departamento'] = row[11]
        self.comprobante['clabe'] = row[12]
        self.comprobante['banco'] = int(banco)
        self.comprobante['fecha_ingreso'] = str(self.util.calc_to_date(row[14]))
        if row[15]:
            self.comprobante['antiguedad'] = int(row[15])
        self.comprobante['puesto'] = row[16]
        self.comprobante['tipo_contrato'] = row[17]
        self.comprobante['tipo_jornada'] = row[18]
        self.comprobante['salario_base'] = row[19]
        self.comprobante['salario_diario'] = row[20]
        self.comprobante['riesgo_puesto'] = RIESGO_PUESTO[row[21].strip()]
        self.comprobante['lugar_expedicion'] = row[22]
        self.comprobante['registro_patronal'] = row[23]
        self.comprobante['metodo_pago'] = PAYMENT_METHODS.get(row[24], '99')
        new_id = self.db.insertrow('nominacfdi', self.comprobante)
        return new_id

    def _save_empleado(self, row):
        empleado = {}
        empleado['no_empleado'] = int(row[0])
        empleado['nombre'] = row[1].strip()
        empleado['rfc'] = row[2].strip().upper()
        empleado['curp'] = row[3].strip().upper()
        empleado['tipo_regimen'] = row[4]
        empleado['imss'] = row[5]
        empleado['periodicidad'] = row[10]
        empleado['departamento'] = row[11]
        empleado['clabe'] = row[12]
        empleado['banco'] = row[13]
        empleado['fecha_ingreso'] = str(self.util.calc_to_date(row[14]))
        empleado['puesto'] = row[16]
        empleado['tipo_contrato'] = row[17]
        empleado['tipo_jornada'] = row[18]
        empleado['salario_base'] = row[19]
        empleado['salario_diario'] = row[20]
        empleado['riesgo_puesto'] = row[21]

        where = "rfc='{}'".format(empleado['rfc'])
        exists = self.db.select(('empleados',), ('id',), where)
        if exists:
            self.db.update('empleados', empleado, where)
            return exists[0][0]
        else:
            new_id = self.db.insertrow('empleados', empleado)
        return new_id

    def _get_folio(self, serie):
        folio = self.db.select(
            ('nominacfdi', ), ('MAX(folio)',), "serie='%s'" % serie)[0][0]
        return folio or 0

    def _get_rows(self, sheet, cell):
        r = sheet.getCellRangeByName(cell)
        c = sheet.createCursorByRange(r)
        c.collapseToCurrentRegion()
        return c.getDataArray()

    def _get_next_rows(self, sheet, cols):
        r = sheet.getCellByPosition(cols+1, 2)
        c = sheet.createCursorByRange(r)
        c.collapseToCurrentRegion()
        return c.getDataArray()

    def msg_user(self, msg):
        self.dm.lblInfo.Label = msg
        return

    def _validar_rfc(self, empleado, data):
        largo = 4
        rfc = data.strip().upper()
        if len(rfc) != 13:
            message='%s\n\nEl RFC de una persona Física, tiene que ser de 13 caracteres.' % empleado
            self.unogui.createMsgBox({'Message':message})
            return False
        part = rfc[0:largo]
        if not self.util.match('[A-Z,&Ñ]{%s}' % largo, part):
            message = '%s\n\nEl RFC tiene caractéres inválidos al inicio.' % empleado
            self.unogui.createMsgBox({'Message': message})
            return False
        part = rfc[-3:]
        if not self.util.match('[A-Z,0-9]{3}', part):
            message='%s\n\nEl RFC tiene caractéres inválidos al final.' % empleado
            self.unogui.createMsgBox({'Message': message})
            return False
        part = rfc[-9:-3]
        try:
            date = self.util.strptime(part, '%y%m%d')
        except ValueError as e:
            message = '%s\n\nLa fecha introducida en el RFC es incorrecta.' % empleado
            self.unogui.createMsgBox({'Message': message})
            return False
        return True

    def _validar_curp(self, empleado, data):
        curp = data.strip().upper()
        if len(curp) != 18:
            message = '%s\n\nEl CURP tiene que ser de 18 caracteres.' % empleado
            self.unogui.createMsgBox({'Message': message})
            return False
        patron = '[A-Z][A,E,I,O,U,X][A-Z]{2}[0-9]{2}[0-1][0-9][0-3]' \
            '[0-9][M,H][A-Z]{2}[B,C,D,F,G,H,J,K,L,M,N,Ñ,P,Q,R,S,T,V' \
            ',W,X,Y,Z]{3}[0-9,A-Z][0-9]'
        if self.util.match(patron, curp):
            return True
        else:
            message = '%s\n\nEl CURP no es valido' % empleado
            self.unogui.createMsgBox({'Message': message})
            return False
