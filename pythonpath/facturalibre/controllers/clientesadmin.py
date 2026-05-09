# -*- coding: utf-8 -*-

import logging
import facturalibre.ui.alumnos as alumnos
import traceback

from facturalibre.settings import LOG, KEY, TYPE_MSG, RFC_PUBLICO, PAIS
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class EventosClientesAdmin(object):
    def __init__(self,caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.globales = caller.globales
        self.db = caller.db
        self.dialog = caller.dialog
        self.id_cliente = caller.id_cliente
        self.alumnos = caller.alumnos
        self.niveles = {}
        self.dm = self.dialog.getModel()
        self.receptor = {'extranjero': 0, 'tipo': 0}
        if self.dm.optFisica.State:
            self.receptor['tipo'] = 1
        elif self.dm.optMoral.State:
            self.receptor['tipo'] = 2
        elif self.dm.optExtranjero.State:
            self.receptor['tipo'] = 3
            self.receptor['extranjero'] = 1
        data = self.db.select(('niveles',))
        for nivel in data:
            self.niveles[nivel[1]] = nivel[0]

    def cmdAlumnos(self):
        try:
            dialog_alumnos = alumnos.Dlg(self)
            dialog_alumnos.execute()
        except:
            print (traceback.format_exc())
        return

    def cmdGuardarSalir(self):
        try:
            if self._validar_datos():
                del self.receptor['tipo']
                self.receptor['nombre'] = self.dm.nombre.Text
                self.receptor['rfc'] = self.dm.rfc.Text
                self.receptor['calle'] = self.dm.calle.Text
                self.receptor['noExterior'] = self.dm.noExterior.Text
                self.receptor['noInterior'] = self.dm.noInterior.Text
                self.receptor['codigoPostal'] = self.dm.codigoPostal.Text
                self.receptor['colonia'] = self.dm.colonia.Text
                self.receptor['referencia'] = ''
                self.receptor['municipio'] = self.dm.municipio.Text
                self.receptor['estado'] = self.dialog.getControl('estado').SelectedItem
                self.receptor['pais'] = self.dm.pais.Text
                self.receptor['fechaalta'] = str(self.util.getDateFromControl(self.dm.fechaalta.Date, True))
                self.receptor['activo'] = self.dm.activo.State
                self.receptor['notas'] = self.dm.notas.Text
                self.receptor['metododepago'] = self.dialog.getControl('lst_payment_methods').SelectedItem
                self.receptor['cuentadepago'] = self.dm.cuentadepago.Text
                self.receptor['condiciondepago'] = self.dm.condiciondepago.Text
                self.receptor['esCliente'] = self.dm.chkCliente.State
                self.receptor['esProveedor'] = self.dm.chkProveedor.State
                a = self.dialog.getControl('lstAddendas').SelectedItem
                data = self.db.select(('addendas',), ('id',), "nombre='%s'" % a)
                if data:
                    self.receptor['id_addenda'] = data[0][0]
                else:
                    self.receptor['id_addenda'] = 0

                if self.caller.edit:
                    id_cliente = self.caller.id_cliente
                    self.db.update('receptores', self.receptor, 'id=%s' % id_cliente)
                    self.db.delete('correos', 'id_cliente=%s' % id_cliente)
                    self.db.delete('telefonos', 'id_cliente=%s' % id_cliente)
                    self.db.delete('contactos', 'id_cliente=%s' % id_cliente)
                else:
                    id_cliente = self.db.insertrow('receptores', self.receptor)
                self._datos_pago()
                data = self.dm.lstCorreo.StringItemList
                if data:
                    new_data = self.unogui.list_to_tuple(data, [id_cliente])
                    self.db.executemany(
                        'correos', ('correo', 'id_cliente'), new_data)
                data = self.dm.lstTelefono.StringItemList
                if data:
                    new_data = self.unogui.list_to_tuple(data, [id_cliente])
                    self.db.executemany(
                        'telefonos', ('telefono', 'id_cliente'), new_data)
                data = self.dm.lstContacto.StringItemList
                if data:
                    new_data = self.unogui.list_to_tuple(data, [id_cliente])
                    self.db.executemany(
                        'contactos', ('contacto', 'id_cliente'), new_data)
                if self.dialog.getControl('cmdAlumnos').isVisible():
                    if self.alumnos:
                        self.db.delete('alumnos', 'id_cliente=%s' % id_cliente)
                        data = []
                        for a in self.alumnos:
                            a[0] = id_cliente
                            a[3] = self.niveles[a[3]]
                            data.append(tuple(a))
                        self.db.executemany(
                            'alumnos',
                            ('id_cliente', 'alumno', 'curp', 'id_nivel'),
                            tuple(data))
                self.dialog.endDialog(id_cliente)
        except:
            print (traceback.format_exc())
        return

    def _datos_pago(self):
        #~ test = self.db.select(
                    #~ ('metodosdepago',),
                    #~ ('id',),
                    #~ "metododepago='%s'" % self.dm.metododepago.Text)
        #~ if not test:
            #~ self.db.insertrow(
                    #~ 'metodosdepago',
                    #~ {'metododepago': self.dm.metododepago.Text})
        test = self.db.select(
                    ('condicionesdepago',),
                    ('id',),
                    "condiciondepago='%s'" % self.dm.condiciondepago.Text)
        if not test:
            self.db.insertrow(
                    'condicionesdepago',
                    {'condiciondepago': self.dm.condiciondepago.Text})
        return

    def _validar_datos(self):
        if not self.receptor['tipo']:
            msg = 'Selecciona el tipo de contribuyente (Física, Moral o ' \
                'Extranjero)'
            util.msgbox(msg, TYPE_MSG['WARNING'])
            return False

        if self._validate('nombre','RAZÓN SOCIAL'):
            return False
        if self.caller.edit:
            data=self.db.select(
                ('receptores',),
                ('id',),
                "nombre='%s' and id<>%s" % (
                    self.dm.nombre.Text,self.caller.id_cliente))
        else:
            data=self.db.select(
                ('receptores',),('id',),"nombre='%s'" % self.dm.nombre.Text)
        if data:
            message = 'El nombre de este Receptor(Cliente) ya esta dado de ' \
                'alta \n\n ¿Estás seguro de volver a agregarlo?'
            if not self.unogui.createQuestion('Factura Libre',message):
                return False

        if self._validate('rfc', 'RFC'):
            return False
        if self.receptor['extranjero']:
            if self._validate('pais','PAÍS'):
                return False
            message = 'Estas agregando un cliente extranjero \n\n ¿Deseas ' \
                'omitir el resto de las validaciones?'
            if self.unogui.createQuestion('Factura Libre',message):
                return True
        else:
            if not self._validar_rfc():
                return False
            if self.caller.edit:
                data = self.db.select(
                    ('receptores',), ('id',), "rfc='%s' and id<>%s" % (
                        self.dm.rfc.Text, self.caller.id_cliente))
            else:
                data = self.db.select(
                    ('receptores',), ('id',), "rfc='%s'" % self.dm.rfc.Text)
            if data:
                message = 'Este RFC ya esta dado de alta \n\n ¿Estás ' \
                    'seguro de volver a agregarlo?'
                if not self.unogui.createQuestion('Factura Libre', message):
                    return False
            if self.dm.rfc.Text.upper() == RFC_PUBLICO:
                msg = 'Estas agregando el RFC de Público en General.\n\n' \
                    '¿Deseas omitir el resto de las validaciones?'
                if self.unogui.createQuestion('Factura Libre', msg):
                    self.dm.rfc.Text = RFC_PUBLICO
                    self.dialog.getControl('estado').selectItemPos(0, True)
                    self.dm.pais.Text = PAIS
                    return True

        if self._validate('calle','CALLE'):
            return False
        if self._validate('noExterior','NÚMERO EXTERIOR'):
            return False

        txtControl = self.dialog.getControl('noInterior')
        txtControl.Text = txtControl.Text.replace('|','').strip()

        if self._validate('codigoPostal','CODIGO POSTAL'):
            return False
        txtControl = self.dialog.getControl('codigoPostal')
        cp=txtControl.Text.strip('_')
        if len(cp)<5:
            message='El campo CODIGO POSTAL esta incompleto.'
            self.unogui.createMsgBox({'Message':message})
            txtControl.setFocus()
            return False
        if self._validate('colonia','COLONIA'):
            return False
        if self._validate('municipio','MUNICIPIO'):
            return False
        if not self.receptor['extranjero']:
            lstControl = self.dialog.getControl('estado')
            if lstControl.SelectedItemPos <= 0:
                message='Selecciona el estado'
                self.unogui.createMsgBox({'Message':message})
                lstControl.setFocus()
                return False
        date = self.util.getDateFromControl(self.dm.fechaalta.Date)
        if date < self.util.today() and not self.caller.edit:
            message = 'La fecha es una fecha pasada \n\n ¿Estás seguro de usar esta fecha?'
            if not self.unogui.createQuestion('Factura Libre', message):
                self.dialog.getControl('fechaalta').setFocus()
                return False
        if date > self.util.today():
            message = 'La fecha es una fecha futura'
            self.unogui.createMsgBox({'Message': message})
            return False
        self.dm.cuentadepago.Text = self.dm.cuentadepago.Text.strip()
        self.dm.condiciondepago.Text = self.dm.condiciondepago.Text.strip()

        #~ self.dm.metododepago.Text = self.dm.metododepago.Text.strip()
        listbox = self.dialog.getControl('lst_payment_methods')
        if not listbox.SelectedItem:
            msg = 'El método de pago es obligatorio'
            util.msgbox(msg)
            return False

        control = self.dialog.getControl('condiciondepago')
        if control.Text:
            dato = self.db.select(
                            ('condicionesdepago',),
                            ('condiciondepago',),
                            "condiciondepago='%s'" % control.Text)
            if not dato:
                message = 'La condición de pago: %s, no existe en la base de ' \
                    'datos, al guardar, esta será agregada automáticamente ' \
                    '\n\n ¿Estás de acuerdo?' % control.Text
                if not self.unogui.createQuestion('FacturaLibre', message):
                    control.setFocus()
                    return False
        cuentadepago = self.dialog.getControl('cuentadepago')
        text = cuentadepago.Text.replace('|','').strip()
        cuentadepago.Text = text
        if len(text) > 0 and len(text) < 4:
            message = 'La cuenta de pago debe ser de 4 digitos o más'
            self.unogui.createMsgBox({'Message': message})
            return False
        return True

    def _validar_rfc(self):
        rfc = self.dm.rfc.Text.upper()
        is_fisica = False
        if self.receptor['tipo'] == 1:
            is_fisica = True
        self.dm.rfc.Text = rfc
        ok, msg = util.validate_rfc(rfc, is_fisica)
        if not ok:
            util.msgbox(msg, TYPE_MSG['ERROR'])
        return ok

    def _validate(self, control_name, field_name):
        txtControl = self.dialog.getControl(control_name)
        if self.unogui.validate(txtControl, 'Vacio'):
            message ='El campo %s no puede estar vacío' % field_name
            self.unogui.createMsgBox({'Message':message})
            txtControl.setFocus()
            return True
        return False

    def cmdAgregarCampo(self, source):
        try:
            controls = {}
            controls['Correo'] = 'El campo CORREO no puede estar vacío'
            controls['Telefono'] = 'El campo TELEFONO no puede estar vacío'
            controls['Contacto'] = 'El campo CONTACTO no puede estar vacío'
            name = source.Model.Tag
            txtControl = self.dialog.getControl('txt%s' % name)
            if self.unogui.validate(txtControl, 'Vacio'):
                txtControl.setFocus()
                self.unogui.createMsgBox({'Message': controls[name]})
                return
            if name =='Correo':
                if not self.unogui.validate(txtControl, 'Correo'):
                    msg = 'La dirección de correo electrónico no es valida'
                    txtControl.setFocus()
                    self.unogui.createMsgBox({'Message': msg})
                    return
            field = txtControl.Text
            listbox = self.dialog.getControl('lst%s' % name)
            data = listbox.getItems()
            if self.unogui.string_in_tuple(field,data):
                msg = 'Este valor ya esta en la lista'
                txtControl.setFocus()
                self.unogui.createMsgBox({'Message': msg})
                return
            else:
                listbox.addItem(field, 0)
                txtControl.Text = ''
        except:
            print (traceback.format_exc())
        return

    def lstDobleClick(self, source):
        if source.ItemCount:
            source.removeItems(source.SelectedItemPos, 1)
        return

    def cmdEliminarCampo(self, source):
        lst = self.dialog.getControl(source.Model.Tag)
        if lst.SelectedItemPos < 0:
            message = 'Selecciona el elemento a eliminar'
            self.unogui.createMsgBox({'Message': message})
        else:
            self.lstDobleClick(lst)
        return

    def optTipoContribuyente(self,source):
        self.receptor['tipo'] = int(source.Model.Tag)
        if self.receptor['tipo'] == 3:
            self.dm.pais.ReadOnly = False
            self.dm.pais.Text = ''
            self.dm.rfc.ReadOnly = True
            self.dm.rfc.Text = self.globales['RFC_EXTRANJERO']
            self.dialog.getControl('estado').selectItemPos(0, True)
            self.dm.estado.Enabled = False
            self.receptor['extranjero'] = 1
        else:
            self.dm.pais.ReadOnly=True
            self.dm.pais.Text=self.globales['PAIS']
            if self.dm.rfc.Text==self.globales['RFC_EXTRANJERO']:
                self.dm.rfc.Text=''
            self.dm.rfc.ReadOnly=False
            self.dm.estado.Enabled=True
            self.receptor['extranjero']=0
        self.dialog.getControl('nombre').setFocus()
        return

    def codigoPostal_keyReleased(self,event):
        if event.KeyCode == KEY['RETURN']:
            cp = event.Source.Text.strip('_')
            if len(cp) != 5:
                msg = 'El Código Postal esta incompleto'
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return
            data = self.db.get_cp_data(cp)
            if not data:
                msg = 'El Código Postal: {}, no se encontró en la base ' \
                    'de datos, asegurate de que este correcto'.format(cp)
                util.msgbox(msg, TYPE_MSG['WARNING'])
                return
            self.dm.municipio.Text = data[0][1]
            self.dialog.getControl('estado').selectItem(data[0][2], True)
            if len(data) == 1:
                self.dm.colonia.Text = data[0][0]
            else:
                self.dm.colonia.Text = ''
                grid = self.dialog.getControl('gridColonias')
                self.unogui.gridAddRows(self.dm.gridColonias, data)
                grid.setVisible(True)
        return

    def gridColonias_selectionChanged(self, grid):
        grid_dm = grid.Model.GridDataModel
        if grid_dm.RowCount:
            row = grid.CurrentRow
            if row >=0:
                self.dm.colonia.Text = grid_dm.getCellData(0, row)
                grid.setVisible(False)
                #~ self.dialog.getControl('metododepago').setFocus()
        return

    def cmdSalir(self):
        self.dialog.endExecute()
        return
