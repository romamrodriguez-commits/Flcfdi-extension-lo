# -*- coding: utf-8 -*-
import logging
from threading import Thread
from .listeners import listener
from facturalibre.settings import TITLE, VERSION, LOG, ULM_WWW, ULM_NAME, ICONS
from facturalibre.modulos import util


log = logging.getLogger(LOG['NAME'])


class Dlg(object):
    PATH_EXT = util.get_path_extension()

    def __init__(self, caller):
        self.caller = caller
        self.ctx = caller.ctx
        self.util = caller.util
        self.globales = caller.globales
        self.unogui = caller.unogui

        self.db = caller.db
        self.options = self._get_options()
        _, _, name, _ = util.path_info(__file__)
        name = 'dlg_{}.xdl'.format(name)
        path_dlg = '{}/dialogs/{}'.format(self.PATH_EXT, name)
        self.dialog = util.create_dialog(path_dlg)
        self.dm = self.dialog.Model
        self.opcion_correo = 0
        self.listener = listener(self)
        self._config()
        self.listener.configuracion()
        self.dialog.execute()
        self.dialog.dispose()

    def _get_options(self):
        rows = self.db.select(('options',))
        data = {r[1]: r[2] for r in rows}
        return data

    def _config(self):
        self.img_url = '{}/icons/{{}}'.format(self.PATH_EXT)
        self.icon_add = self.img_url.format(ICONS['ADD'])
        self.icon_delete = self.img_url.format(ICONS['DELETE'])
        self.icon_save = self.img_url.format(ICONS['SAVE'])
        self.dm.cmdSalir.ImageURL = self.img_url.format(ICONS['CLOSE'])

        nombre = self.db.select_field('emisor', 'nombre')
        title = '{} - Configuración '.format(TITLE)
        if nombre:
            title += '- {}'.format(nombre)
        self.dialog.Title = title

        properties = {}
        properties['Name'] = 'txtURL'
        properties['PositionX'] = 185
        properties['PositionY'] = 36
        properties['Width'] = 70
        properties['URL'] = ULM_WWW
        properties['Label'] = ULM_NAME
        properties['Step'] = 15
        ctr = util.create_control(self.dialog, 'FixedHyperlink', properties)
        properties.clear()
        properties['Name'] = 'txtURL2'
        properties['PositionX'] = 200
        properties['PositionY'] = 185
        properties['Width'] = 70
        properties['URL'] = ULM_WWW
        properties['Label'] = 'Donaciones'
        properties['Step'] = 15
        oVinculo = self.unogui.createControl(
                            self.dialog, 'FixedHyperlink', properties)

        properties.clear()
        properties['Name'] = 'imgLogo'
        properties['ImageURL'] = '{}/icons/logo.png'.format(self.PATH_EXT)
        oImagen = self.unogui.changeControl(self.dialog, properties)

        properties.clear()
        properties['Name'] = 'rmMapa'
        properties['Height'] = 250
        oMapa = self.unogui.createControl(self.dialog, 'Roadmap', properties)
        options = (
            'Certificados',
            'Emisor',
            'Expedido En',
            'Folios',
            'Catálogos CFDI',
            'Catálogos Productos',
            'Campos personalizados',
            'Opciones',
            'Correo',
            'Rutas de Trabajo',
            'Addendas',
            'Reportes'
        )
        self.unogui.addOptionsRoadMap(oMapa, options)

        self._page1()
        self._page2()
        self._page3()
        self._page4()
        self._page5()
        self._page6()
        self._page7()
        self._page8()
        self._page9()
        self._page10()
        self._page11()
        self._page12()
        util.center_dialog(self.dialog)
        self.dialog.Model.Step = 15
        return

    def _page1(self):
        self.dm.cmdVerificar.ImageURL = self.img_url.format(ICONS['OK'])
        self.dm.cmdVerificarSat.ImageURL = self.img_url.format(ICONS['OK'])
        self.dm.cmdCerTest.ImageURL = self.img_url.format(ICONS['UP'])
        self.dm.cmdGuardarCertificado.ImageURL = self.icon_save
        properties = {}
        properties['Name'] = 'gridCertificado'
        properties['PositionX'] = 82
        properties['PositionY'] = 85
        properties['Width'] = 280
        properties['Height'] = 100
        properties['Step'] = 1
        properties['SelectionModel'] = 0

        data = self.db.select(
            ('certificado',),
            ('nombre', 'rfc', 'noCertificado',
                'SUBSTR(inicio,1,10)', 'SUBSTR(final,1,10)'))
        if data:
            data = data[0]
            data2 = (
                data[0],
                data[1],
                data[2],
                self.util.format_date(data[3], '%d-%b-%Y'),
                self.util.format_date(data[4], '%d-%b-%Y'),
                )
        else:
            data2 = ('', '', '', '', '')
        columns = (
            {'Title': '', 'ColumnWidth': 90, 'HorizontalAlign': 2},
            {'Title':'Datos del certificado guardados',
                'ColumnWidth':170, 'HorizontalAlign':0}
        )
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        rows = (
            ('Razón Social: ',data2[0]),
            ('RFC: ',data2[1]),
            ('Serie: ',data2[2]),
            ('Desde: ',data2[3]),
            ('Hasta: ',data2[4])
        )
        self.unogui.gridAddRows(oGrid,rows)
        return

    def _page2(self):
        self.dm.cmdAgregarRegimen.ImageURL = self.icon_add
        self.dm.cmdEliminarRegimen.ImageURL = self.icon_delete
        self.dm.cmdGuardarEmisor.ImageURL = self.icon_save
        self.dm.cmdNiveles.ImageURL = self.img_url.format(ICONS['FIELDS'])

        data = self.db.select(('estados',),('estado',))
        listbox = self.dialog.getControl('lstEstados')
        self.unogui.query_to_listbox(data,listbox)
        listbox.addItem(' ',0)
        listbox = self.dialog.getControl('lstEstados2')
        self.unogui.query_to_listbox(data,listbox)
        listbox.addItem(' ',0)
        listbox = self.dialog.getControl('lstEstadoPre')
        self.unogui.query_to_listbox(data,listbox)
        listbox.addItem(' ',0)

        data = self.db.select(('regimenesfiscales',),('Regimen',))
        listbox = self.dialog.getControl('lstRegimen')
        self.unogui.query_to_listbox(data, listbox)
        data = self.db.select(('emisor',))
        if data:
            emisor = data[0]
            self.dm.txtCalle.Text = emisor[3]
            self.dm.txtNumExt.Text = emisor[4]
            self.dm.txtNumInt.Text = emisor[5]
            self.dm.txtColonia.Text = emisor[6]
            self.dm.txtMunicipio.Text = emisor[9]
            self.dialog.getControl('lstEstados').selectItem(emisor[10], True)
            self.dm.txtCodigoPostal.Text = emisor[12]
            self.dm.txtTelefono.Text = emisor[13]
            self.dm.txtCorreo.Text = emisor[14]
            if emisor[16] == 1:
                self.dm.optFisica.State = 1
            elif emisor[16] == 2:
                self.dm.optMoral.State = 1
            elif emisor[16] == 3:
                self.dm.optOng.State = 1
            self.dm.txtAutorizacionOng.Text = emisor[17]
            if emisor[18]:
                date = emisor[18][0:10]
                self.dm.txtFechaOng.Date = self.util.setUtilDate(date)
            self.dm.chkEscuela.State = emisor[19]
            self.dm.txtRegistroPatronal.Text = emisor[20]
        else:
            emisor = [0]
            emisor.append(self.db.select_field('certificado', 'rfc'))
            emisor.append(self.db.select_field('certificado', 'nombre'))
            if len(emisor[1]) == 12:
                self.dm.optMoral.State = 1
            elif len(emisor[1]) == 13:
                self.dm.optFisica.State = 1
        self.dm.txtRfc.Text = emisor[1]
        self.dm.txtNombre.Text = emisor[2]
        self.dm.lblPac.Label = 'Consultando al PAC...'

        properties = {}
        properties['Name'] = 'gridColonias'
        properties['PositionX'] = 142
        properties['PositionY'] = 96
        properties['Width'] = 95
        properties['Height'] = 100
        properties['Step'] = 2
        columns = (
        {'Title': 'Colonias', 'ColumnWidth': 75, 'HorizontalAlign': 0},
        {'Title': 'Municipio', 'ColumnWidth': 0, 'HorizontalAlign': 0},
        {'Title': 'Estado', 'ColumnWidth':0, 'HorizontalAlign': 0})
        grid = self.unogui.createGrid(self.dialog, columns, properties)
        self.dialog.getControl('gridColonias').setVisible(False)

        if self.dm.txtRfc.Text:
            is_ong = bool(self.dm.optOng.State)
            t = util.GetTimbres(self.dm.txtRfc.Text, self.dm.lblPac, not is_ong, is_ong)
            t.start()
            #~ ok, timbres = util.get_timbres(self.dm.txtRfc.Text)
            #~ self.dm.lblPac.Label = 'Folios PAC: {}'.format(timbres)
        return

    def _page3(self):
        self.dm.cmdGuardarExpedido.ImageURL = self.img_url.format(ICONS['SAVE'])
        self.dm.cmdLimpiarExpedido.ImageURL = self.img_url.format(ICONS['CLEAN'])
        data=self.db.select(('expedidoen',))
        if data:
            emisor=data[0]
            self.dm.txtCalle2.Text=emisor[1]
            self.dm.txtNumExt2.Text=emisor[2]
            self.dm.txtNumInt2.Text=emisor[3]
            self.dm.txtColonia2.Text=emisor[4]
            self.dm.txtMunicipio2.Text=emisor[7]
            self.dialog.getControl('lstEstados2').selectItem(emisor[8],True)
            self.dm.txtCodigoPostal2.Text=emisor[10]
            self.dm.txtTelefono2.Text=emisor[11]
        return

    def _page4(self):
        self.dm.cmdAgregarFolios.ImageURL = self.icon_add
        self.dm.cmdEliminarFolios.ImageURL = self.icon_delete
        self.dm.cmdPredeterminar.ImageURL = self.img_url.format(ICONS['OK'])
        w = 0
        if self.dm.txtAutorizacionOng.Text:
            w = 10
        properties = {}
        properties['Name'] = 'gridFolios'
        properties['PositionX'] = 82
        properties['PositionY'] = 85
        properties['Width'] = 290
        properties['Height'] = 90
        properties['Step'] = 4
        columns=(
            {'Title': 'id', 'ColumnWidth': 0,'HorizontalAlign': 0},
            {'Title': 'Serie', 'ColumnWidth': 40, 'HorizontalAlign': 1},
            {'Title': 'Inicio', 'ColumnWidth': 40, 'HorizontalAlign': 1},
            {'Title': 'Usar con','ColumnWidth': 40, 'HorizontalAlign': 1},
            {'Title': 'Predeterminado', 'ColumnWidth':45, 'HorizontalAlign': 1},
            {'Title': 'Plantilla', 'ColumnWidth':100, 'HorizontalAlign': 2},
            {'Title': 'D', 'ColumnWidth':w, 'HorizontalAlign': 1},
        )
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        data = self.db.select(
                ('folios', 'tiposcfdi'),
                ('folios.id','serie', 'inicio', 'tipo',
                    "case when predeterminado then 'SI' else '' end",
                    'plantilla',
                    "case when donativo then 'SI' else '' end"),
                'folios.usarcon=tiposcfdi.id')
        if data:
            self.unogui.gridAddRows(oGrid,data)
            self.dm.cmdEliminarFolios.Enabled = True
            self.dm.cmdPredeterminar.Enabled = True
        data = self.db.select(('tiposcfdi',),('tipo',))
        listbox = self.dialog.getControl('lstUsarCon')
        self.unogui.query_to_listbox(data,listbox)
        listbox.addItem(' ',0)
        return

    def _page5(self):
        self.dm.cmdAgregarAduana.ImageURL = self.icon_add
        self.dm.cmdAgregarCondicionPago.ImageURL = self.icon_add
        self.dm.cmdAgregarMetodoPago.ImageURL = self.icon_add
        self.dm.cmdAgregarMoneda.ImageURL = self.icon_add
        self.dm.cmdEliminarAduana.ImageURL = self.icon_delete
        self.dm.cmdEliminarCondicionPago.ImageURL = self.icon_delete
        self.dm.cmdEliminarMetodoPago.ImageURL = self.icon_delete
        self.dm.cmdEliminarMoneda.ImageURL = self.icon_delete
        self.dm.cmdGuardarCatalogosCfdi.ImageURL = self.icon_save

        properties = {}
        properties['Name'] = 'gridMonedas'
        properties['PositionX'] = 82
        properties['PositionY'] = 161
        properties['Width'] = 175
        properties['Height'] = 65
        properties['Step'] = 5
        columns=({'Title':'id','ColumnWidth':0,'HorizontalAlign':1},
        {'Title':'Moneda','ColumnWidth':60,'HorizontalAlign':1},
        {'Title':'Prefijo','ColumnWidth':50,'HorizontalAlign':1},
        {'Title':'Sufijo','ColumnWidth':50,'HorizontalAlign':1})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        data=self.db.select(('monedas',))
        if data:
            self.unogui.gridAddRows(oGrid,data)
            self.dm.cmdAgregarMoneda.Enabled=True
            self.dm.cmdEliminarMoneda.Enabled=True

        data = self.db.select(('condicionesdepago',),('condiciondepago',))
        listbox = self.dialog.getControl('lstCondicionPago')
        self.unogui.query_to_listbox(data,listbox)

        #~ data = self.db.select(('metodosdepago',),('metododepago',))
        data = self.db.select(('payment_methods',),('method',), order='method')
        listbox = self.dialog.getControl('lstMetodoPago')
        self.unogui.query_to_listbox(data,listbox)

        data = self.db.select(('aduanas',),('aduana',))
        listbox = self.dialog.getControl('lstAduana')
        self.unogui.query_to_listbox(data,listbox)
        return

    def _page6(self):
        self.dm.cmdAgregarImpuesto.ImageURL = self.icon_add
        self.dm.cmdAgregarUnidad.ImageURL = self.icon_add
        self.dm.cmdAgregarCategoria.ImageURL = self.icon_add
        self.dm.cmdEliminarUnidad.ImageURL = self.icon_delete
        self.dm.cmdEliminarImpuesto.ImageURL = self.icon_delete
        self.dm.cmdEliminarCategoria.ImageURL = self.icon_delete
        self.dm.cmdGuardarCatalogosProductos.ImageURL = self.icon_save

        properties = {}
        properties['Name'] = 'gridImpuestos'
        properties['PositionX'] = 82
        properties['PositionY'] = 32
        properties['Width'] = 142
        properties['Height'] = 85
        properties['Step'] = 6
        columns=({'Title':'id','ColumnWidth':0,'HorizontalAlign':1},
        {'Title':'Impuesto','ColumnWidth':35,'HorizontalAlign':1},
        {'Title':'Tasa','ColumnWidth':35,'HorizontalAlign':1},
        {'Title':'Tipo','ColumnWidth':40,'HorizontalAlign':1})
        oGrid = self.unogui.createGrid(self.dialog, columns, properties)
        data = self.db.select(('impuestos',), order='nombre')
        if data:
            self.unogui.gridAddRows(oGrid, data, True)
            self.dm.cmdEliminarImpuesto.Enabled = True

        data = self.db.select(('unidades',), ('unidad',))
        listbox = self.dialog.getControl('lstUnidad')
        self.unogui.query_to_listbox(data, listbox)

        data = self.db.select(('tiposimpuestos',), ('tipo',))
        listbox = self.dialog.getControl('lstImpuestos')
        self.unogui.query_to_listbox(data, listbox)
        listbox.addItem(' ', 0)

        tree = self.dialog.getControl('treeCategorias')
        select = getattr(self.db, 'select')
        self.unogui.query_to_tree(tree, 'categorias', select, True)

        return

    def _page7(self):
        self.dm.cmdAgregarPersonalizado.ImageURL = self.icon_add
        self.dm.cmdEliminarPersonalizado.ImageURL = self.icon_delete
        self.dm.cmdGuardarCamposPersonalizados.ImageURL = self.icon_save
        self.dm.cmdCargarAddenda.ImageURL = self.img_url.format(ICONS['UP'])

        data = self.db.select(('addendapersonalizada',))[0]
        self.dm.txtNodo.Text = data[1]
        self.dm.txtAtributo1.Text = data[2]
        self.dm.txtAtributo2.Text = data[3]

        properties = {}
        properties['Name'] = 'gridPersonalizados'
        properties['PositionX'] = 82
        properties['PositionY'] = 35
        properties['Width'] = 130
        properties['Height'] = 118
        properties['Step'] = 7
        columns = ({'Title': 'id','ColumnWidth': 0, 'HorizontalAlign': 1},
                    {'Title': 'Campo','ColumnWidth': 90, 'HorizontalAlign': 0},
                    {'Title': 'Nodo','ColumnWidth': 0, 'HorizontalAlign': 1})
        grid = self.unogui.createGrid(self.dialog, columns, properties)
        data = self.db.select(('campospersonalizados',),
                                ('id', 'campo', 'nodo'))
        if data:
            self.unogui.gridAddRows(grid, data)
        return

    def _page8(self):
        self.dm.cmdSeleccionarImpuesto.ImageURL = \
            self.img_url.format(ICONS['DOWN'])
        self.dm.cmdAgregarDirectorio.ImageURL = self.icon_add
        self.dm.cmdEliminarDirectorio.ImageURL = self.icon_delete
        self.dm.cmdProbarFtp.ImageURL = self.img_url.format(ICONS['CONNECT'])
        self.dm.cmdGuardarOpciones.ImageURL = self.icon_save

        properties = {}
        properties['Name'] = 'gridImpuestos2'
        properties['PositionX'] = 82
        properties['PositionY'] = 52
        properties['Width'] = 147
        properties['Height'] = 105
        properties['Step'] = 8
        columns=({'Title':'id','ColumnWidth':0,'HorizontalAlign':1},
        {'Title':'Impuesto','ColumnWidth':40,'HorizontalAlign':1},
        {'Title':'Tasa','ColumnWidth':40,'HorizontalAlign':1},
        {'Title':'Tipo','ColumnWidth':40,'HorizontalAlign':1})
        grid = self.unogui.createGrid(self.dialog, columns, properties)

        data = self.db.select(('rutasespejo',),('ruta',))
        listbox = self.dialog.getControl('lstRutasEspejo')
        self.unogui.query_to_listbox(data,listbox)
        return

    def _page9(self):
        self.dm.cmdBorrarDatosCorreo.ImageURL = self.img_url.format(ICONS['CLEAN'])
        self.dm.cmdCorreoProbar.ImageURL = self.img_url.format(ICONS['OK'])
        self.dm.cmdGuardarCorreo.ImageURL = self.icon_save

        data = self.db.select(('correo',))
        if data:
            self.dm.txtCorreoServidor.Text = data[0][1]
            self.dm.txtCorreoPuerto.Value = data[0][2]
            self.dm.txtCorreoUsuario.Text = data[0][3]
            self.dm.txtCorreoContrasena.Text = data[0][4]
            self.dm.txtCorreoCopia.Text = data[0][5]
            self.dm.txtCorreoAsunto.Text = data[0][6]
            self.dm.txtCorreoCuerpo.Text = data[0][7]
            self.dm.chkSeguridad.State = data[0][8]
            self.dm.cmdBorrarDatosCorreo.Enabled = True
        self.dm.cmdGuardarCorreo.Enabled = True
        self.opcion_correo = self.db.select_field('opciones2', 'opcion5')
        if self.opcion_correo == 0:
            self.dm.optCorreo0.State = 1
        elif self.opcion_correo == 1:
            self.dm.optCorreo1.State = 1
        elif self.opcion_correo == 2:
            self.dm.optCorreo2.State = 1
        elif self.opcion_correo == 3:
            self.dm.optCorreo3.State = 1
        return

    def _page10(self):
        self.dm.cmdAgregarRuta.ImageURL = self.icon_add
        self.dm.cmdEliminarRuta.ImageURL = self.icon_delete
        self.dm.cmdGuardarRutas.ImageURL = self.icon_save

        properties = {}
        properties['Name'] = 'gridRutas'
        properties['PositionX'] = 80
        properties['PositionY'] = 30
        properties['Width'] = 294
        properties['Height'] = 100
        properties['Step'] = 10
        properties['TabIndex'] = 207
        properties['TabStop'] = True
        columns = ({'Title': 'id','ColumnWidth': 0, 'HorizontalAlign': 1},
                {'Title': 'Emisor','ColumnWidth': 110, 'HorizontalAlign': 0},
                {'Title': 'Ruta','ColumnWidth': 162, 'HorizontalAlign': 0})
        grid = self.unogui.createGrid(self.dialog, columns, properties)

        self.dm.txtPlantilla1.Text = self.db.select_field('opciones', 'plantilla')
        self.dm.txtPlantilla2.Text = self.db.select_field('opciones', 'plantilla2')
        return

    def _page11(self):
        self.dm.cmdAgregarAddenda.ImageURL = self.icon_add
        self.dm.cmdEliminarAddenda.ImageURL = self.icon_delete
        self.dm.cmdEditarAddenda.ImageURL = self.img_url.format(ICONS['EDIT'])
        self.dm.cmdAsignarCampos.ImageURL = self.img_url.format(ICONS['CONNECT'])

        properties = {}
        properties['Name'] = 'gridAddendas'
        properties['PositionX'] = 124
        properties['PositionY'] = 38
        properties['Width'] = 85
        properties['Height'] = 170
        properties['Step'] = 11
        columns=({'Title': 'id','ColumnWidth': 0, 'HorizontalAlign': 1},
        {'Title': 'Nombre','ColumnWidth': 70, 'HorizontalAlign': 0})
        grid = self.unogui.createGrid(self.dialog, columns, properties)
        data = self.db.select(('addendas',), ('id', 'nombre'))
        if data:
            self.unogui.gridAddRows(grid, data)
        else:
            self.dm.cmdEliminarAddenda.Enabled = False
            self.dm.cmdEditarAddenda.Enabled = False
            self.dm.cmdAsignarCampos.Enabled = False
        return

    def _page12(self):
        self.dm.cmdAgregarReporte.ImageURL = self.icon_add
        self.dm.cmdEliminarReporte.ImageURL = self.icon_delete
        self.dm.cmdProbarSql.ImageURL = self.img_url.format(ICONS['OK'])
        data = self.db.select(('reportes',), order='nombre')
        if data:
            reports = self.dialog.getControl('lstReportes')
            for r in data:
                reports.addItem(r[1], reports.getItemCount())
        else:
            self.dm.cmdEliminarReporte.Enabled = False
        return

