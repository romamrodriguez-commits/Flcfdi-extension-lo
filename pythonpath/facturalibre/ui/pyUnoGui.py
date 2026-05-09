# -*- coding: utf-8 -*-
# (C) Copyright 2011 Universo Libre México, A.C. <http://universolibre.org>
# Author: Mauricio Baeza <mauricio@correolibre.net>
# based on pyXray macro from Laurent Godard <lgodard@indesko.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#

#####################################################
#                                                  #
#              pyUnoGui                         #
#                                                  #
# UnoGui ()                                      #
#                                                  #
#####################################################

import uno
import unohelper
import re
import datetime
import sys
#from com.sun.star.awt import XWindowListener, XTopWindowListener, XMenuListener
#from com.sun.star.awt import Selection
from com.sun.star.awt import Rectangle, WindowDescriptor
from com.sun.star.awt.PosSize import POS, POSSIZE
from com.sun.star.awt.WindowClass import TOP, MODALTOP
from com.sun.star.beans import PropertyValue
#from com.sun.star.awt.WindowAttribute import \
#   MOVEABLE as A_MOVEABLE, CLOSEABLE as A_CLOSEABLE, \
#   BORDER as A_BORDER, SHOW as A_SHOW, SIZEABLE as A_SIZEABLE

RELATION = 0.361

#class Controles(unohelper.Base):
class UnoGui():
    """Class for create GUI and controls"""

    def __init__(self, ctx=uno.getComponentContext()):
        """Context : a Valid UNO context"""
        #self.ctx = uno.getComponentContext()
        self.ctx = ctx
        self.sm = self.ctx.ServiceManager
        self.desktop = self.sm.createInstanceWithContext(
            'com.sun.star.frame.Desktop', self.ctx)
        self.toolkit = self.sm.createInstanceWithContext(
            'com.sun.star.awt.Toolkit', self.ctx)
        self.pos_size = self.toolkit.getActiveTopWindow().PosSize
        self.cat = {}
        self.ver = self.get_version()
        self.controls = {}
        self.controls['Button'] = 'com.sun.star.awt.UnoControlButtonModel'
        self.controls['CheckBox'] = 'com.sun.star.awt.UnoControlCheckBoxModel'
        self.controls['ComboBox'] = 'com.sun.star.awt.UnoControlComboBoxModel'
        self.controls['CurrencyField'] = 'com.sun.star.awt.UnoControlCurrencyFieldModel'
        self.controls['DateField'] = 'com.sun.star.awt.UnoControlDateFieldModel'
        self.controls['Edit'] = 'com.sun.star.awt.UnoControlEditModel'
        self.controls['FileControl'] = 'com.sun.star.awt.UnoControlFileControlModel'
        self.controls['FixedHyperlink'] = 'com.sun.star.awt.UnoControlFixedHyperlinkModel'
        self.controls['FixedLine'] = 'com.sun.star.awt.UnoControlFixedLineModel'
        self.controls['FixedText'] = 'com.sun.star.awt.UnoControlFixedTextModel'
        self.controls['FormattedField'] = 'com.sun.star.awt.UnoControlFormattedFieldModel'
        self.controls['GroupBox'] = 'com.sun.star.awt.UnoControlGroupBoxModel'
        self.controls['ImageControl'] = 'com.sun.star.awt.UnoControlImageControlModel'
        self.controls['ListBox'] = 'com.sun.star.awt.UnoControlListBoxModel'
        self.controls['NumericField'] = 'com.sun.star.awt.UnoControlNumericFieldModel'
        self.controls['PatternField'] = 'com.sun.star.awt.UnoControlPatternFieldModel'
        self.controls['ProgressBar'] = 'com.sun.star.awt.UnoControlProgressBarModel'
        self.controls['RadioButton'] = 'com.sun.star.awt.UnoControlRadioButtonModel'
        self.controls['ScrollBar'] = 'com.sun.star.awt.UnoControlScrollBarModel'
        self.controls['SimpleAnimation'] = 'com.sun.star.awt.UnoControlSimpleAnimationModel'
        self.controls['SpinButton'] = 'com.sun.star.awt.UnoControlSpinButtonModel'
        self.controls['Throbber'] = 'com.sun.star.awt.UnoControlThrobberModel'
        self.controls['TimeField'] = 'com.sun.star.awt.UnoControlTimeFieldModel'
        # This controls requiere more elements
        self.controls['Roadmap'] = 'com.sun.star.awt.UnoControlRoadmapModel'
        self.controls['Grid'] = 'com.sun.star.awt.grid.UnoControlGridModel'
        #self.controls['Tree'] = 'com.sun.star.awt.TreeControlModel'

        self.controls_properties = {}
        self.controls_properties['Button'] = {
            'PositionX': 0,
            'PositionY': 0,
            'Width': 60,
            'Height': 12,
            'Step': 0,
            'TabIndex':1,
            'Label': 'CommandButton',
            'DefaultButton': False,
            'PushButtonType': 0}
        self.controls_properties['CheckBox'] = {
            'PositionX': 0,
            'PositionY': 0,
            'Width': 40,
            'Height': 10,
            'Step': 0,
            'TabIndex': 1,
            'Label': 'CheckBox'}
        self.controls_properties['ComboBox'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1,'Dropdown':True}
        self.controls_properties['CurrencyField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1,'Spin':True}
        self.controls_properties['DateField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1,'Dropdown':True}
        self.controls_properties['Edit'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['FileControl'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['FixedHyperlink'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['FixedLine'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':5,'Step':0,'TabIndex':1}
        self.controls_properties['FixedText'] = {'PositionX':0,'PositionY':0,'Width':40,'Height':10,'Step':0,'TabIndex':1,'Label':'Label'}
        self.controls_properties['FormattedField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['GroupBox'] = {'PositionX':0,'PositionY':0,'Width':100,'Height':30,'Step':0,'TabIndex':1}
        self.controls_properties['ImageControl'] = {'PositionX':0,'PositionY':0,'Width':30,'Height':30,'Step':0,'TabIndex':1}
        self.controls_properties['ListBox'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':30,'Step':0,'TabIndex':1}
        self.controls_properties['NumericField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['PatternField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['ProgressBar'] = {'PositionX':0,'PositionY':0,'Width':100,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['RadioButton'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['ScrollBar'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['SimpleAnimation'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':30,'Step':0,'TabIndex':1}
        self.controls_properties['SpinButton'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['Throbber'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':30,'Step':0,'TabIndex':1}
        self.controls_properties['TimeField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
        self.controls_properties['Roadmap'] = {'PositionX':0,'PositionY':0,'Width':75,'Height':200,'Step':0,'TabIndex':1,'Text':'Opciones'}
        self.controls_properties['Grid'] = {
            'BackgroundColor': self.rgb(255, 255, 255),
            'Sizeable': False,
            'ShowColumnHeader': True,
            'ShowRowHeader': True,
            'UseGridLines': True}

    def get_version(self):
        cp = self.sm.createInstance(
            'com.sun.star.configuration.ConfigurationProvider')
        pv = PropertyValue()
        pv.Name = 'nodepath'
        pv.Value = '/org.openoffice.Setup/Product'
        node = cp.createInstanceWithArguments(
            'com.sun.star.configuration.ConfigurationAccess', (pv,))
        return float(node.getByName('ooSetupVersion'))

    def createMsgBox(self, properties):
        """Create message box
            Type:
            infobox - cuadro de mensaje informativo, omite el parametro Buttons, solo muestra Aceptar.
            warningbox - cuadro de mensaje de advertencia.
            errorbox - cuadro de mensaje de error.
            querybox - cuadro de mensaje de pregunta.
            messbox - cuadro de mensaje normal.

            Buttons:
            from com.sun.star.awt.MessageBoxButtons import
            (BUTTONS_OK, BUTTONS_OK_CANCEL, BUTTONS_YES_NO, BUTTONS_YES_NO_CANCEL, BUTTONS_RETRY_CANCEL,
            BUTTONS_ABORT_IGNORE_RETRY, DEFAULT_BUTTON_OK, DEFAULT_BUTTON_CANCEL, DEFAULT_BUTTON_RETRY,
            DEFAULT_BUTTON_YES, DEFAULT_BUTTON_NO, DEFAULT_BUTTON_IGNORE)
        """
        msgbox_default = {
            'Type': 'infobox',
            'Buttons': 1,
            'Title': 'Factura Libre',
            'Message': ''
        }
        for propertie in list(msgbox_default.keys()):
            if propertie in properties:
                msgbox_default[propertie] = properties[propertie]
        if msgbox_default['Message']:
            DesktopWindow = self.toolkit.getDesktopWindow()
            message = msgbox_default['Message']
            if not isinstance(message, str):
                message = str(message)
            if self.ver == 4.1:
                MsgBox = self.toolkit.createMessageBox(
                    DesktopWindow,
                    Rectangle(),
                    msgbox_default['Type'],
                    msgbox_default['Buttons'],
                    msgbox_default['Title'],
                    message
                )
            else:
                MsgBox = self.toolkit.createMessageBox(
                    DesktopWindow,
                    msgbox_default['Type'],
                    msgbox_default['Buttons'],
                    msgbox_default['Title'],
                    message
                )
            return MsgBox.execute()

    def createQuestion(self, title, message):
        """Create message box question
        """
        if message:
            DesktopWindow = self.toolkit.getDesktopWindow()
            if self.ver == 4.1:
                MsgBox = self.toolkit.createMessageBox(
                    DesktopWindow, Rectangle(), 'querybox', 3, title, message)
            else:
                MsgBox = self.toolkit.createMessageBox(
                    DesktopWindow, 'querybox', 3, title, message)
            res = MsgBox.execute()
            if res == 3:
                return False
            else:
                return True

    def createDialog(self, properties):
        """Create dialog box"""

        #create the dialog model and set the properties
        dialog_default = {'PositionX':0,'PositionY':0,'Width':200,'Height':200,'Step':0,'TabIndex':0,'WindowClass':MODALTOP,'Title':'LibreOffice'}
        dialog = self.sm.createInstanceWithContext('com.sun.star.awt.UnoControlDialog',self.ctx)
        dialog_model = self.sm.createInstanceWithContext('com.sun.star.awt.UnoControlDialogModel',self.ctx)
        # Only add properties if not exist
        for propertie in list(dialog_default.keys()):
            if not propertie in properties:
                properties[propertie]=dialog_default[propertie]
        # Only set properties if support
        for propertie in list(properties.keys()):
            if hasattr(dialog_model,propertie):
                setattr(dialog_model,propertie,properties[propertie])

        dialog.setModel(dialog_model)

        # If position is zero, set dialog center
        #pos_size = self.toolkit.getActiveTopWindow().PosSize
        if properties['PositionX'] == 0:
            properties['PositionX'] = (self.pos_size.Width - properties['Width']/RELATION) / 2
        if properties['PositionY'] == 0:
            properties['PositionY'] = (self.pos_size.Height - properties['Height']/RELATION) / 2
        dialog.setPosSize( properties['PositionX'], properties['PositionY'], properties['Width'], properties['Height'], POS )

        #UNO toolkit definition
        rect = Rectangle()
        rect.X = properties['PositionX']
        rect.Y = properties['PositionY']
        rect.Width = properties['Width']
        rect.Height = properties['Height']

        #win_descriptor = uno.createUnoStruct('com.sun.star.awt.WindowDescriptor')
        win_descriptor = WindowDescriptor()
        win_descriptor.Type = properties['WindowClass']
        # ParentIndex -1 = Desktop
        win_descriptor.ParentIndex = -1
        win_descriptor.Bounds = rect
        peer = self.toolkit.createWindow( win_descriptor )
        dialog.createPeer( self.toolkit, peer )
        return dialog

    def centerDialog(self, dialog):
        """Center dialog box in screen"""
        #pos_size = self.toolkit.getActiveTopWindow().PosSize
        pos_x = (self.pos_size.Width - dialog.getModel().Width/RELATION) / 2
        pos_y = (self.pos_size.Height - dialog.getModel().Height/RELATION) / 2
        dialog.setPosSize( pos_x, pos_y, dialog.getModel().Width, dialog.getModel().Height, POS )
        return None

    def createControl(self, dialog, type_control, properties):
        """Create controls"""
        if not 'Name' in properties:
            return None
        dialog_model = dialog.getModel()
        # Only add if not exist
        if dialog_model.hasByName(properties['Name']):
            return None
        if type_control in self.controls:
            control = dialog_model.createInstance( self.controls[type_control] )
            # Add default properties
            for propertie in list(self.controls_properties[type_control].keys()):
                if not propertie in properties:
                    properties[propertie] = self.controls_properties[type_control][propertie]
            # Only properties in control
            for propertie in list(properties.keys()):
                if control.getPropertySetInfo().hasPropertyByName(propertie):
                    # Properties special
                    if propertie == 'StringItemList':
                        uno.invoke( control, "setPropertyValue" , ("StringItemList",uno.Any( "[]string", properties[propertie])) )
                    else:
                        control.setPropertyValue(propertie,properties[propertie])
            dialog_model.insertByName(properties['Name'], control )
            return control

    def changeControl(self, dialog, properties):
        """Change control properties"""
        dialog_model = dialog.getModel()
        if dialog_model.hasByName(properties['Name']):
            control = dialog_model.getByName(properties['Name'])
            # Only properties in control
            for propertie in list(properties.keys()):
                if control.getPropertySetInfo().hasPropertyByName(propertie):
                    # Properties special
                    if propertie == 'StringItemList':
                        uno.invoke( control, "setPropertyValue" , ("StringItemList",uno.Any( "[]string", properties[propertie])) )
                    else:
                        control.setPropertyValue(propertie,properties[propertie])
            return control

    def changePropertyControl(self,dialog,properties):
        dialog_model = dialog.getModel()
        if dialog_model.hasByName(properties[0]):
            control = dialog_model.getByName(properties[0])
            control.setPropertyValue(properties[1],properties[2])
            return None

    def createGrid(self, dialog, columns, properties, resizeable=False):
        """Create control grid"""
        if not 'Name' in properties:
            return None
        dialog_model = dialog.getModel()
        if dialog_model.hasByName(properties['Name']):
            return None
        control = dialog_model.createInstance( self.controls['Grid'] )
        # Add default properties
        for propertie in list(self.controls_properties['Grid'].keys()):
            if not propertie in properties:
                properties[propertie] = self.controls_properties['Grid'][propertie]

        oColumnModel = self.sm.createInstance('com.sun.star.awt.grid.DefaultGridColumnModel')
        oDataModel = self.sm.createInstance('com.sun.star.awt.grid.DefaultGridDataModel')
        #oColumnModel.setDefaultColumns(columns)
        for col in columns:
            oColumn = self.sm.createInstance('com.sun.star.awt.grid.GridColumn')
            for propertie in list(col.keys()):
                setattr(oColumn, propertie, col[propertie])
            setattr(oColumn, 'Resizeable', resizeable)
            oColumnModel.addColumn(oColumn)

        properties['ColumnModel'] = oColumnModel
        properties['GridDataModel'] = oDataModel

        # Only properties in control
        for propertie in list(properties.keys()):
            if control.getPropertySetInfo().hasPropertyByName(propertie):
                control.setPropertyValue(propertie,properties[propertie])
        dialog_model.insertByName(properties['Name'], control )
        return control

    def gridAddRows(self, grid, rows, show_id=False):
        grid.GridDataModel.removeAllRows()
        if rows:
            if show_id:
                heading = tuple([i[0] for i in rows])
            else:
                heading = tuple(range(1, len(rows) + 1))
            rows = tuple(tuple(i) for i in rows)
            grid.GridDataModel.addRows(heading, rows)
            #~ grid.RowBackgroundColors = tuple(range(len(rows)))

    def gridAddRow(self,grid,row):
        grid.GridDataModel.addRow( grid.GridDataModel.RowCount+1, row )

    def selectRow(self,grid,row):
        grid_dm = grid.Model.GridDataModel
        for r in range(grid_dm.RowCount):
            if grid_dm.getCellData(0,r) == row:
                grid.selectRow(r)
                break
        return

    def gridChangeColumn(self,grid,columns):
        oColumns = grid.ColumnModel
        oColumns.setDefaultColumns(len(columns))
        for i,col in enumerate(columns):
            column = oColumns.getColumn(i)
            #setattr(column,'Resizeable',True)
            for propertie in list(col.keys()):
                setattr(column, propertie, col[propertie])

    def addOptionsRoadMap(self,mapa,opciones):
        for i, v in enumerate(opciones):
            oMapaOpcion = mapa.createInstance()
            oMapaOpcion.ID = i
            oMapaOpcion.Label = v
            mapa.insertByIndex(i, oMapaOpcion)
        return

    def createDialogFromURL(self,dlg_url):
        """Create dialog from URL."""
        dp = self.sm.createInstanceWithContext('com.sun.star.awt.DialogProvider', self.ctx)
        return dp.createDialog(dlg_url)

    def validate(self, control, type_validate):
        text = control.Text.replace('|','').replace("'",'').strip()
        lines = text.split('\n')
        new_lines = []
        for l in lines:
            if l.strip():
                new_lines.append(' '.join(l.split()))
        #~ words = text.split()
        #~ text = ' '.join(words)
        #~ print 'D', '\n'.join(new_lines)
        control.Text = '\n'.join(new_lines)
        if type_validate == 'Vacio':
            return not bool(control.Text)
        if type_validate == 'Correo':
            pattern = '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,6}$'
            return re.match(pattern, text)

    def query_to_listbox(self, query, listbox):
        data_list = []
        for row in query:
            data_list.append(row[0])
        listbox.Model.StringItemList = tuple(data_list)
        return

    def setVisible(self, dlg, names, visible=True):
        if isinstance(names, tuple):
            for control in names:
                dlg.getControl(control).setVisible(visible)
        else:
            dlg.getControl(names).setVisible(visible)
        return

    def rgb(self, r, g, b):
        return int('%02x%02x%02x' % (r, g, b), 16)

    def list_to_tuple(self, lists, list2=[]):
        lista = []
        for item in lists:
            row = [item]
            row.extend(list2)
            lista.append(tuple(row))
        return tuple(lista)

    def string_in_tuple(self, string, data):
        if data:
            for tmp in data:
                if tmp.lower() == string.lower():
                    return True
        return False

    def grid_to_tuple(self, grid):
        grid_dm = grid.GridDataModel
        col = grid_dm.ColumnCount
        fil = grid_dm.RowCount
        data = []
        for f in range(fil):
            row = []
            for c in range(1, col):
                row.append(grid_dm.getCellData(c, f))
            data.append(tuple(row))
        return tuple(data)

    def getFolder(self, init_folder=''):
        folder = self.sm.createInstance('com.sun.star.ui.dialogs.FolderPicker')
        if init_folder:
            init_folder = uno.systemPathToFileUrl(init_folder)
        folder.setDisplayDirectory(init_folder)
        if folder.execute():
            return uno.fileUrlToSystemPath(folder.getDirectory())
        else:
            return ''

    def query_to_tree(self, tree, table, select, show_id=False):
        tree_dm = self.addTreeDataModel(tree, tree.Model.Tag)
        padres = select((table,), ('DISTINCT id_padre',), order='id_padre')
        for row in padres:
            if self.cat:
                if row[0] in self.cat:
                    padre = self.cat[row[0]]
                else:
                    padre = None
            else:
                padre = tree_dm.Root
            hijos = select((table,), where='id_padre=%s' % row[0], order='id')
            for row2 in hijos:
                hijo = self.addChildNode(tree_dm, row2, show_id)
                if padre:
                    padre.appendChild(hijo)
        tree.expandNode(tree_dm.Root)
        self.cat = {}
        return

    def addTreeDataModel(self, tree, raiz):
        tree_dm = self.sm.createInstance('com.sun.star.awt.tree.MutableTreeDataModel')
        r = tree_dm.createNode(raiz, True)
        r.DataValue = 0
        tree_dm.setRoot(r)
        tree.Model.DataModel = tree_dm
        return tree_dm

    def addChildNode(self, tree, row, show_id=False):
        if show_id:
            hijo = tree.createNode('%s - %s' % (row[0], row[1]), False)
        else:
            hijo = tree.createNode(row[1], False)
        hijo.DataValue = row[0]
        self.cat[row[0]] = hijo
        return hijo

    def debug(self, data, name_file='debug.txt'):
        debug_file = open(name_file, 'a')
        debug_file.write(str(datetime.datetime.now()) + ' ' + str(data) + '\n')
        debug_file.close()

    def openDoc(self, path, options):
        path_url = uno.systemPathToFileUrl(path)
        try:
            doc = self.desktop.loadComponentFromURL(path_url, '_blank', 0, options)
            return doc
        except:
            #print >> sys.stderr, "failed to load spreadsheet. error is", sys.exc_info()[0]
            return None
