# -*- coding: utf-8 -*-

from .listenersadmin import listener
from facturalibre.modulos import util


DLG_NAME = 'dlgClientesAdmin.xdl'
ICON_GUARDAR='save.png'
ICON_SALIR = 'close.png'
ICON_AGREGAR = 'add.png'
ICON_DELETE = 'delete.png'
ICON_EDIT = 'edit.png'


class Dlg(object):

    def __init__(self, caller, edit=False, id_cliente=0):
        self.caller = caller
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui
        self.db = caller.db
        self.edit = edit
        self.id_cliente = id_cliente
        self.alumnos = []
        dlg_url = '%s/dialogs/%s' % (self.globales['EXT_PATH'],DLG_NAME)
        self.dialog = self.unogui.createDialogFromURL(dlg_url)
        self.dm = self.dialog.Model
        self.listener = listener(self)
        self.__config()
        self.listener.clientesadmin()

    def __config(self):
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_GUARDAR)
        self.dm.cmdGuardarSalir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_SALIR)
        self.dm.cmdSalir.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_AGREGAR)
        self.dm.cmdAgregarCorreo.ImageURL = img_url
        self.dm.cmdAgregarTelefono.ImageURL = img_url
        self.dm.cmdAgregarContacto.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_DELETE)
        self.dm.cmdBorrarCorreo.ImageURL = img_url
        self.dm.cmdBorrarTelefono.ImageURL = img_url
        self.dm.cmdBorrarContacto.ImageURL = img_url
        img_url = '%s/icons/%s' % (self.globales['EXT_PATH'], ICON_EDIT)
        self.dm.cmdAlumnos.ImageURL = img_url

        data = self.db.select(('estados',),('estado',))
        listbox = self.dialog.getControl('estado')
        self.unogui.query_to_listbox(data,listbox)
        listbox.addItem(' ',0)

        data = self.db.select(('payment_methods',),('method',), order='method')
        listbox = self.dialog.getControl('lst_payment_methods')
        self.unogui.query_to_listbox(data,listbox)

        data = self.db.select_field('asignaciones', 'id')
        if data:
            data = self.db.select(('addendas',), ('nombre',))
            listbox = self.dialog.getControl('lstAddendas')
            self.unogui.query_to_listbox(data, listbox)
            listbox.addItem('Seleccionar Addenda', 0)
        else:
            self.dialog.getControl('lstAddendas').setVisible(False)
            self.dialog.getControl('lblAddenda').setVisible(False)

        if self.edit:
            title = '%s - Editar Receptor' % self.globales['APP_TITULO']
            fields = (
                    'id',
                    'rfc',
                    'nombre',
                    'calle',
                    'noExterior',
                    'noInterior',
                    'colonia',
                    'municipio',
                    'estado',
                    'pais',
                    'codigoPostal',
                    'extranjero',
                    'activo',
                    'DATE(fechaalta)',
                    'metododepago',
                    'cuentadepago',
                    'condiciondepago',
                    'notas',
                    'id_addenda',
                    'esCliente',
                    'esProveedor',
                    'saldoCliente',
                    'saldoProveedor')
            receptor = self.db.select(
                        ('receptores',),
                        fields,
                        'id=%s' % self.id_cliente)[0]
            self.dm.id.Text = receptor[0]
            self.dm.rfc.Text = receptor[1]
            self.dm.nombre.Text = receptor[2]
            self.dm.calle.Text = receptor[3]
            self.dm.noExterior.Text = receptor[4]
            self.dm.noInterior.Text = receptor[5]
            self.dm.colonia.Text = receptor[6]
            self.dm.municipio.Text = receptor[7]
            estado = receptor[8]
            self.dm.pais.Text = receptor[9]
            self.dm.codigoPostal.Text = receptor[10]
            self.dm.optExtranjero.State = receptor[11]
            self.dm.activo.State = receptor[12]
            self.dm.fechaalta.Date = self.util.setUtilDate(receptor[13])

            self.dialog.getControl('lst_payment_methods').selectItem(receptor[14], True)

            self.dm.cuentadepago.Text = receptor[15]
            self.dm.condiciondepago.Text = receptor[16]
            self.dm.notas.Text = receptor[17]
            self.dm.chkCliente.State = bool(receptor[19])
            self.dm.chkProveedor.State = bool(receptor[20])
            self.dm.saldoCliente.Text = receptor[21]
            self.dm.saldoProveedor.Text = receptor[22]

            if receptor[11]:
                self.dm.estado.Enabled = False
                self.dm.pais.ReadOnly = False
                self.dm.rfc.ReadOnly = True
            else:
                if len(receptor[1]) == 12:
                    self.dm.optMoral.State = 1
                elif len(receptor[1]) == 13:
                    self.dm.optFisica.State = 1

            data = self.db.select(
                        ('correos',),
                        ('correo',),
                        'id_cliente=%s' % self.id_cliente)
            listbox = self.dialog.getControl('lstCorreo')
            self.unogui.query_to_listbox(data,listbox)
            data = self.db.select(
                        ('telefonos',),
                        ('telefono',),
                        'id_cliente=%s' % self.id_cliente)
            listbox = self.dialog.getControl('lstTelefono')
            self.unogui.query_to_listbox(data,listbox)
            data = self.db.select(
                        ('contactos',),
                        ('contacto',),
                        'id_cliente=%s' % self.id_cliente)
            listbox = self.dialog.getControl('lstContacto')
            self.unogui.query_to_listbox(data,listbox)
            listbox = self.dialog.getControl('estado')
            if receptor[18]:
                data = self.db.select(('addendas',),
                                        ('nombre',),
                                        'id=%s' % receptor[18])
                self.dialog.getControl('lstAddendas').selectItem(data[0][0], True)
            else:
                self.dialog.getControl('lstAddendas').selectItemPos(0, True)
            alumnos = self.db.select(
                ('alumnos', 'niveles'),
                ('alumnos.id', 'alumno', 'curp', 'nivel'),
                'alumnos.id_nivel=niveles.id and id_cliente=%s' % self.id_cliente,
                order='alumno')
            self.alumnos = [list(r) for r in alumnos]
        else:
            title = '%s - Nuevo Receptor' % self.globales['APP_TITULO']
            self.dm.fechaalta.Date = self.util.setUtilDate()
            self.dm.id.Text = '<Nuevo>'
            estado = self.db.select_field('opciones', 'id_estado')
            if estado:
                estado = self.db.select(
                                        ('estados',),
                                        ('estado',),
                                        'id=%s'%estado)[0][0]
            else:
                estado = ' '
            self.dialog.getControl('lstAddendas').selectItemPos(0, True)
        listbox.selectItem(estado, True)

        data = self.db.select(('condicionesdepago',), ('condiciondepago',))
        combo = self.dialog.getControl('condiciondepago')
        self.unogui.query_to_listbox(data, combo)
        data = self.db.select_field('emisor', 'escuela')
        self.dialog.getControl('cmdAlumnos').setVisible(bool(data))

        properties = {}
        properties['Name'] = 'gridColonias'
        properties['PositionX'] = 70
        properties['PositionY'] = 100
        properties['Width'] = 120
        properties['Height'] = 80
        properties['Step'] = 0
        columns = (
        {'Title': 'Colonias', 'ColumnWidth': 100, 'HorizontalAlign': 0},
        {'Title': 'Municipio', 'ColumnWidth': 0, 'HorizontalAlign': 0},
        {'Title': 'Estado', 'ColumnWidth':0, 'HorizontalAlign': 0})
        grid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridColonias').setVisible(False)
        self.dialog.Title = title
        return

    def execute(self):
        self.dialog.getControl('nombre').setFocus()
        return self.dialog.execute()
