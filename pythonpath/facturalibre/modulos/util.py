# -*- coding: utf-8 -*-

from functools import wraps
import re
import os
import sys
import glob
import json
import uno
import zipfile
import subprocess
import time
import datetime
import urllib
import shutil
import smtplib
import tempfile
import logging
from threading import Thread
from smtplib import SMTPException, SMTPAuthenticationError
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from xml.etree import ElementTree as ET
from xml.dom.minidom import parseString

from urllib import request
from xml.sax.saxutils import escape

from socket import AF_INET, SOCK_DGRAM
import socket
import struct

from com.sun.star.beans import PropertyValue
from com.sun.star.awt.PosSize import POS

from facturalibre.settings import LOG, TITLE, BUTTONS, IMPLE_NAME, TYPE_MSG, \
    PRE, WIN, FORMAT, DECIMALS, SAT_WS, SAT_SOAP
from facturalibre.modulos.pac import Ecodex as Pac
from facturalibre.modulos.pac import SAT


log = logging.getLogger(LOG['NAME'])
CTX = uno.getComponentContext()
SM = CTX.getServiceManager()


def catch_exception(f):
    @wraps(f)
    def func(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log.error(f.__name__, exc_info=True)
    return func


class GetTimbres(Thread):

    def __init__(self, rfc, label, new_server=True, ong=False):
        self.rfc = rfc
        self.label = label
        self.new_server = new_server
        self.ong = ong
        Thread.__init__(self)

    def run(self):
        ok, timbres = get_timbres(self.rfc, self.new_server, self.ong)
        if ok:
            self.label.Label = 'Folios PAC: {}'.format(timbres)


def _create_instance(name, with_context=False):
    if with_context:
        instance = SM.createInstanceWithContext(name, CTX)
    else:
        instance = SM.createInstance(name)
    return instance


def _create_struct(name):
    return uno.createUnoStruct(name)


def get_path_debug(name='debug.log'):
    path = get_path_user()
    return join(path, name)


def get_path_user():
    path = _create_instance('com.sun.star.util.PathSettings')
    return uno.fileUrlToSystemPath(path.Work)


def join(*paths):
    return os.path.join(*paths)


def get_version():
    cp = _create_instance('com.sun.star.configuration.ConfigurationProvider')
    arg = _create_struct('com.sun.star.beans.PropertyValue')
    arg.Name = 'nodepath'
    arg.Value = '/org.openoffice.Setup/Product'
    node = cp.createInstanceWithArguments(
        'com.sun.star.configuration.ConfigurationAccess', (arg,))
    return float(node.getByName('ooSetupVersion'))


def msgbox(message, type_msg='infobox', title=TITLE, buttons=1):
    """ Create message box
        type_msg: infobox, warningbox, errorbox, querybox, messbox
    """
    desktop = _create_instance('com.sun.star.frame.Desktop', True)
    doc = desktop.getCurrentComponent()
    toolkit = _create_instance('com.sun.star.awt.Toolkit')
    parent = toolkit.getDesktopWindow()
    #~ parent = doc.getCurrentController().getFrame().getContainerWindow()
    if not isinstance(message, str):
        message = str(message)
    if get_version() == 4.1:
        rec = _create_struct('com.sun.star.awt.Rectangle')
        mb = toolkit.createMessageBox(
            parent, rec, type_msg, buttons, title, message)
    else:
        mb = toolkit.createMessageBox(parent, type_msg, buttons, title, message)
    return mb.execute()


def question(message, buttons=BUTTONS['YES_NO']):
    return msgbox(message, TYPE_MSG['QUERY'], buttons=buttons)


def get_config_value(nodepath, prop):
    name = 'com.sun.star.configuration.ConfigurationProvider'
    cp = _create_instance(name, True)
    node = PropertyValue()
    node.Name = 'nodepath'
    node.Value = nodepath
    try:
        ca = cp.createInstanceWithArguments(
            'com.sun.star.configuration.ConfigurationAccess', (node,))
        if ca and (ca.hasByName(prop)):
            return ca.getPropertyValue(prop)
    except:
        return None

def get_os():
    return sys.platform

def check_app():
    os = get_os()
    if os in ('linux', 'darwin'):
        try:
            pipe = subprocess.Popen('xsltproc', stdout=subprocess.PIPE)
            return True, ''
        except:
            msg = 'No tienes instalado XSLTPROC, es necesario instalarlo ' \
                'primero para poder continuar'
            return False, msg
    else:
        try:
            openssl = join(
                path_to(get_path_extension(), False), 'bin', 'openssl.exe')
            test = subprocess.check_output(openssl, shell=True).decode()
            return True, ''
        except:
            msg = 'No tienes instalado OPENSSL, es necesario instalarlo ' \
                'primero para poder continuar'
            return False, msg


def path_exists(path):
    return os.path.exists(path)


def path_info(path):
    path, filename = os.path.split(path)
    name, extension = os.path.splitext(filename)
    return [path, filename, name, extension]


def path_to(path, url=True):
    if url:
        return uno.systemPathToFileUrl(path)
    else:
        return uno.fileUrlToSystemPath(path)


def get_path_extension():
    """Get extension directory url from the extension id."""
    pip_name = '/singletons/com.sun.star.deployment.PackageInformationProvider'
    if CTX.hasByName(pip_name):
        pip = CTX.getByName(pip_name)
        return pip.getPackageLocation(IMPLE_NAME)
    return ''

def create_dialog(path):
    """Create dialog from URL."""
    dp = _create_instance('com.sun.star.awt.DialogProvider', True)
    return dp.createDialog(path)

def center_dialog(dialog):
    """Center dialog box in screen"""
    RELATION = 0.361

    toolkit = _create_instance('com.sun.star.awt.Toolkit', True)
    try:
        pos_size = toolkit.getActiveTopWindow().PosSize
        pos_x = (pos_size.Width - dialog.getModel().Width / RELATION) / 2
        pos_y = (pos_size.Height - dialog.getModel().Height / RELATION) / 2
    except:
        pos_x = 0
        pos_y = 0
    dialog.setPosSize(
        pos_x, pos_y, dialog.getModel().Width, dialog.getModel().Height, POS)
    return None

def rgb(r, g, b):
    return int('%02x%02x%02x' % (r, g, b), 16)

def create_control(dialog, type_control, properties):
    controls = {
        'Button': 'com.sun.star.awt.UnoControlButtonModel',
        'CheckBox': 'com.sun.star.awt.UnoControlCheckBoxModel',
        'ComboBox': 'com.sun.star.awt.UnoControlComboBoxModel',
        'CurrencyField': 'com.sun.star.awt.UnoControlCurrencyFieldModel',
        'DateField': 'com.sun.star.awt.UnoControlDateFieldModel',
        'Edit': 'com.sun.star.awt.UnoControlEditModel',
        'FileControl': 'com.sun.star.awt.UnoControlFileControlModel',
        'FixedHyperlink': 'com.sun.star.awt.UnoControlFixedHyperlinkModel',
        'FixedLine': 'com.sun.star.awt.UnoControlFixedLineModel',
        'FixedText': 'com.sun.star.awt.UnoControlFixedTextModel',
        'FormattedField': 'com.sun.star.awt.UnoControlFormattedFieldModel',
        'GroupBox': 'com.sun.star.awt.UnoControlGroupBoxModel',
        'ImageControl': 'com.sun.star.awt.UnoControlImageControlModel',
        'ListBox': 'com.sun.star.awt.UnoControlListBoxModel',
        'NumericField': 'com.sun.star.awt.UnoControlNumericFieldModel',
        'PatternField': 'com.sun.star.awt.UnoControlPatternFieldModel',
        'ProgressBar': 'com.sun.star.awt.UnoControlProgressBarModel',
        'RadioButton': 'com.sun.star.awt.UnoControlRadioButtonModel',
        'ScrollBar': 'com.sun.star.awt.UnoControlScrollBarModel',
        'SimpleAnimation': 'com.sun.star.awt.UnoControlSimpleAnimationModel',
        'SpinButton': 'com.sun.star.awt.UnoControlSpinButtonModel',
        'Throbber': 'com.sun.star.awt.UnoControlThrobberModel',
        'TimeField': 'com.sun.star.awt.UnoControlTimeFieldModel',
        'Roadmap': 'com.sun.star.awt.UnoControlRoadmapModel',
        'Grid': 'com.sun.star.awt.grid.UnoControlGridModel',
    }
    controls_properties = {}
    controls_properties['Button'] = {'PositionX': 0, 'PositionY': 0,
        'Width': 60, 'Height': 12, 'Step': 0, 'TabIndex': 1,
        'Label': 'CommandButton', 'DefaultButton': False, 'PushButtonType': 0}
    controls_properties['CheckBox'] = {'PositionX': 0, 'PositionY': 0,
        'Width': 40, 'Height': 10, 'Step': 0, 'TabIndex': 1, 'Label': 'CheckBox'}
    controls_properties['ComboBox'] = {'PositionX': 0, 'PositionY': 0,
        'Width': 60, 'Height': 13, 'Step': 0, 'TabIndex': 1, 'Dropdown': True}
    controls_properties['CurrencyField'] = {'PositionX': 0, 'PositionY': 0,
        'Width': 60, 'Height': 13, 'Step': 0, 'TabIndex': 1, 'Spin': True}
    controls_properties['DateField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1,'Dropdown':True}
    controls_properties['Edit'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['FileControl'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['FixedHyperlink'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['FixedLine'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':5,'Step':0,'TabIndex':1}
    controls_properties['FixedText'] = {'PositionX':0,'PositionY':0,'Width':40,'Height':10,'Step':0,'TabIndex':1,'Label':'Label'}
    controls_properties['FormattedField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['GroupBox'] = {'PositionX':0,'PositionY':0,'Width':100,'Height':30,'Step':0,'TabIndex':1}
    controls_properties['ImageControl'] = {'PositionX':0,'PositionY':0,'Width':30,'Height':30,'Step':0,'TabIndex':1}
    controls_properties['ListBox'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':30,'Step':0,'TabIndex':1}
    controls_properties['NumericField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['PatternField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['ProgressBar'] = {'PositionX':0,'PositionY':0,'Width':100,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['RadioButton'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['ScrollBar'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['SimpleAnimation'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':30,'Step':0,'TabIndex':1}
    controls_properties['SpinButton'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['Throbber'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':30,'Step':0,'TabIndex':1}
    controls_properties['TimeField'] = {'PositionX':0,'PositionY':0,'Width':60,'Height':13,'Step':0,'TabIndex':1}
    controls_properties['Roadmap'] = {'PositionX':0,'PositionY':0,'Width':75,'Height':200,'Step':0,'TabIndex':1,'Text':'Opciones'}
    controls_properties['Grid'] = {'BackgroundColor': rgb(255, 255, 255),
        'Sizeable': False, 'ShowColumnHeader': True, 'ShowRowHeader': True,
        'UseGridLines': True}

    """Create controls"""
    if not 'Name' in properties:
        return None
    dialog_model = dialog.getModel()
    # Only add if not exist
    if dialog_model.hasByName(properties['Name']):
        return None
    if type_control in controls:
        control = dialog_model.createInstance(controls[type_control])
        # Add default properties
        for propertie in list(controls_properties[type_control].keys()):
            if not propertie in properties:
                properties[propertie] = \
                    controls_properties[type_control][propertie]
        # Only properties in control
        for propertie in list(properties.keys()):
            if control.getPropertySetInfo().hasPropertyByName(propertie):
                # Properties special
                if propertie == 'StringItemList':
                    uno.invoke(control, "setPropertyValue" , (
                        "StringItemList", uno.Any(
                            "[]string", properties[propertie])))
                else:
                    control.setPropertyValue(propertie, properties[propertie])
    dialog_model.insertByName(properties['Name'], control)
    return control

def change_control(dialog, properties):
    """Change control properties"""
    dialog_model = dialog.getModel()
    if not dialog_model.hasByName(properties['Name']):
        return
    control = dialog_model.getByName(properties['Name'])
    # Only properties in control
    for propertie in list(properties.keys()):
        if control.getPropertySetInfo().hasPropertyByName(propertie):
            # Properties special
            if propertie == 'StringItemList':
                uno.invoke(control, "setPropertyValue", (
                    "StringItemList", uno.Any(
                        "[]string", properties[propertie])))
            else:
                control.setPropertyValue(propertie, properties[propertie])
    return control

def create_grid(dialog, columns, properties, resizeable=False):
    """Create control grid"""
    default_properties = {
        'BackgroundColor': rgb(255, 255, 255),
        'Sizeable': False,
        'ShowColumnHeader': True,
        'ShowRowHeader': True,
        'UseGridLines': True
    }
    if not 'Name' in properties:
        return None
    dialog_model = dialog.getModel()
    if dialog_model.hasByName(properties['Name']):
        return None
    control = dialog_model.createInstance(
        'com.sun.star.awt.grid.UnoControlGridModel')
    # Add default properties
    for propertie in list(default_properties.keys()):
        if not propertie in properties:
            properties[propertie] = default_properties[propertie]
    column_model = _create_instance(
        'com.sun.star.awt.grid.DefaultGridColumnModel')
    data_model = _create_instance(
        'com.sun.star.awt.grid.DefaultGridDataModel')
    for col in columns:
        grid_column = _create_instance('com.sun.star.awt.grid.GridColumn')
        for propertie in list(col.keys()):
            setattr(grid_column, propertie, col[propertie])
        setattr(grid_column, 'Resizeable', resizeable)
        column_model.addColumn(grid_column)
    properties['ColumnModel'] = column_model
    properties['GridDataModel'] = data_model
    # Only properties present in control
    for propertie in list(properties.keys()):
        if control.getPropertySetInfo().hasPropertyByName(propertie):
            control.setPropertyValue(propertie,properties[propertie])
    dialog_model.insertByName(properties['Name'], control )
    return control

def data_to_grid(grid, rows, show_id=False):
    grid.removeAllRows()
    if show_id:
        heading = tuple([i[0] for i in rows])
    else:
        heading = tuple(range(1, len(rows) + 1))
    rows = tuple(tuple(i) for i in rows)
    grid.addRows(heading, rows)
    return

def grid_add_row(grid, row):
    grid.addRow(grid.RowCount + 1, row)
    return

def add_options_roadmap(roadmap, options):
    for i, v in enumerate(options):
        opt = roadmap.createInstance()
        opt.ID = i
        opt.Label = v
        roadmap.insertByIndex(i, opt)
    return

def get_folder(init_folder=''):
    folder = _create_instance('com.sun.star.ui.dialogs.FolderPicker')
    if init_folder:
        init_folder = uno.systemPathToFileUrl(init_folder)
    folder.setDisplayDirectory(init_folder)
    if folder.execute():
        return uno.fileUrlToSystemPath(folder.getDirectory())
    else:
        return ''

def is_readable(path):
    return os.access(path, os.R_OK)

def is_dir(path):
    return os.path.isdir(path)

def get_files(path, ext):
    files = []
    for folder,_,_ in os.walk(path):
        files.extend(glob.glob(os.path.join(folder, '*.{}'.format(ext))))
    return files


def exists(path):
    return os.path.exists(path)


def files_to_zip(path, source):
    z = zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED)
    for f in source:
        if exists(f):
            _, name, _, _ = path_info(f)
            z.write(f, name)
    z.close()
    return


def now(s=False, minutes=0):
    n = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
    if s:
        return n.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return n.replace(microsecond=0)


def load_file(path, binary=False):
    if not exists(path):
        return ''
    if binary:
        file_tmp = open(path, 'rb')
    else:
        file_tmp = open(path)
    data = file_tmp.read()
    file_tmp.close()
    return data


def set_properties(properties):
    properties_list = []
    for p in properties:
        pv = PropertyValue()
        pv.Name = p[0]
        pv.Value = p[1]
        properties_list.append(pv)
    return tuple(properties_list)

def doc_open(path, options):
    desktop = _create_instance('com.sun.star.frame.Desktop', True)
    path_url = uno.systemPathToFileUrl(path)
    try:
        doc = desktop.loadComponentFromURL(path_url, '_blank', 0, options)
        return doc
    except:
        log.error('INIT: ', exc_info=True)
        return None

def validate(control, type_validate='Vacio'):
    text = control.Text.replace('|','').replace("'",'').strip()
    lines = text.split('\n')
    new_lines = []
    for l in lines:
        if l.strip():
            new_lines.append(' '.join(l.split()))
    control.Text = '\n'.join(new_lines)
    if type_validate == 'Vacio':
        return not bool(control.Text)
    if type_validate == 'Correo':
        pattern = '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,6}$'
        return re.match(pattern, text)

def match(pattern, text):
    return re.match(pattern, text)

def validate_rfc(rfc, is_fisica=True):
    rfc = rfc.upper().strip()
    lenght = 12
    start = 3
    if is_fisica:
        lenght = 13
        start = 4
    if len(rfc) != lenght:
        msg = 'La longitud del RFC es incorrecta'
        return False, msg
    part = rfc[0:start]
    if not match('[A-Z,&Ñ]{{{}}}'.format(start), part):
        msg = 'El RFC tiene caractéres inválidos al inicio'
        return False, msg
    part = rfc[-3:]
    if not match('[A-Z,0-9]{3}', part):
        message = 'El RFC tiene caractéres inválidos al final'
        return False, msg
    part = rfc[-9:-3]
    try:
        date = strptime(part, '%y%m%d')
    except ValueError as e:
        msg = 'La fecha introducida en el RFC es incorrecta'
        return False, msg
    return True, rfc

def strptime(date_string, format_user, timestamp=False):
    tmp = datetime.datetime.strptime(date_string, format_user)
    if timestamp:
        tmp = tmp.timestamp()
    return tmp

#~ def get_acuse(rfc, uuid, new_server=True):
    #~ pac = PAC(rfc, new_server)
    #~ if pac.get_acuse(uuid):
        #~ return True, pac.xml
    #~ else:
        #~ return False, pac.error

def get_patron(template='([^{}]*)}'):
    return re.compile(template)

def sleep(sec=1):
    time.sleep(sec)
    return

def is_connect():
    try:
        response = urllib.request.urlopen('http://google.com', timeout=5)
        return True
    except:
        return False

def send_mail(data):
    # id, servidor, puerto, usuario, contrasena, copia, asunto, cuerpo
    files = data['files']
    receivers = data['receivers']
    mail_server = data['mail_server']
    sender = mail_server['user']
    subject = 'Enviamos su factura {serie}{folio}'
    if mail_server['subject']:
        subject = mail_server['subject']
    body = 'Le enviamos su archivo XML y PDF\n\nGracias'
    if mail_server['body']:
        body = mail_server['body']
    if files:
        for f in files:
            if f.endswith('.xml'):
                break
        fields = _make_fields(f)
        html = _make_info(body, fields)
        subject = _make_info(subject, fields, True)
    else:
        html = body
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ', '.join(receivers)
    message['CC'] = mail_server['copy']
    message['Subject'] = subject
    message.attach(MIMEText(html, 'html'))
    for f in files:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload( open(f,"rb").read() )
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            "attachment; filename=%s" % os.path.basename(f))
        message.attach(part)
    if mail_server['copy']:
        receivers += mail_server['copy'].split(',')
    try:
        smtpObj = smtplib.SMTP(
            mail_server['server'], mail_server['port'], timeout=10)
        if mail_server['ssl']:
            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.ehlo()
        smtpObj.login(mail_server['user'], mail_server['pass'])
        smtpObj.sendmail(sender, receivers, message.as_string())
        smtpObj.quit()
        return True, ''
    except SMTPAuthenticationError as e:
        if e[0] == 534 and 'gmail' in mail_server['server']:
            msg = 'Necesitas activar el acceso a otras aplicaciones en tu ' \
                'cuenta de GMail'
            return False, msg
        elif e[0] == 535:
            return False, 'Nombre de usuario o contraseña inválidos'
    except SMTPException as e:
        return False, str(e) # 100
    except Exception as e:
        return False, str(e) # 200

def _make_fields(path):
    xml = ET.parse(path).getroot()
    data = xml.attrib.copy()
    del(data['certificado'])
    version = data['version']
    receptor = xml.find('{}Receptor'.format(PRE[version]))
    data['receptor_nombre'] = receptor.attrib['nombre']
    data['receptor_rfc'] = receptor.attrib['rfc']
    return data

def _make_info(data, fields, subject=False):
    if subject:
        return data.format(**fields)
    html = data.format(**fields).replace('\n', '<br/>')
    html = """
    <html>
      <head></head>
      <body>
        <p>{}
        </p>
      </body>
    </html>
    """.format(html)
    return html


def save_file(path, data, mode='w'):
    file_tmp = open(path, mode)
    if isinstance(data, str):
        file_tmp.write(data)
    else:
        file_tmp.write(data.decode('utf-8'))
    file_tmp.close()
    return


def get_path_temp(name=''):
    if name:
        temp = join(tempfile.gettempdir(), name)
    else:
        temp = tempfile.mkstemp()[1]
    return temp

def send_mail_client(data):
    files = data['files']
    mail_server = data['mail_server']
    if get_os() == WIN:
        ssmail = _create_instance('com.sun.star.system.SimpleSystemMail')
    else:
        ssmail = _create_instance('com.sun.star.system.SimpleCommandMail')
    client = ssmail.querySimpleMailClient()
    mail = client.createSimpleMailMessage()
    ccmail = []
    if data['receivers']:
        mail.setRecipient(data['receivers'][0])
        if len(data['receivers']) > 1:
            ccmail = data['receivers'][1:]
    subject = 'Enviamos su factura'
    if mail_server:
        ccmail = mail_server['copy'].split(',') + ccmail
        if mail_server['subject']:
            subject = mail_server['subject']
    mail.setCcRecipient(tuple(ccmail))
    attach = tuple([uno.systemPathToFileUrl(path) for path in files])
    mail.setAttachement(attach)

    for f in files:
        if f.endswith('.xml'):
            break
    fields = _make_fields(f)
    subject = _make_info(subject, fields, True)

    mail.setSubject(subject)
    try:
        client.sendSimpleMailMessage(mail, 0)
        return True
    except:
        return False

def kill(path):
    try:
        os.remove(path)
    except:
        pass
    return

def is_date(value):
    return type(value) is datetime.datetime

def clear_sel(sel):
    return tuple([x for x in sel if x >-1])

def query_to_tree(tree, parents, show_id=False):
    tree_dm = add_tree_data_model(tree, tree.Model.Tag)
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
    #~ self.cat = {}
    return

def add_tree_data_model(tree, raiz):
    tree_dm = _createInstance('com.sun.star.awt.tree.MutableTreeDataModel')
    r = tree_dm.createNode(raiz, True)
    r.DataValue = 0
    tree_dm.setRoot(r)
    tree.Model.DataModel = tree_dm
    return tree_dm

def query_to_listbox(query, listbox):
    listbox.Model.StringItemList = tuple([r[0] for r in query])
    return

def set_visible(dlg, names, visible=True):
    if isinstance(names, tuple):
        for control in names:
            dlg.getControl(control).setVisible(visible)
    else:
        dlg.getControl(names).setVisible(visible)
    return

def currency(value, decimals=DECIMALS, f=FORMAT):
    return f.format(decimals).format(value)


def get_timbres(rfc, new_server=True, ong=False):
    pac = Pac(rfc, new_server, ong)
    estatus_cuenta = pac.estatus_cuenta()
    if estatus_cuenta:
        return True, estatus_cuenta['TimbresDisponibles']
    else:
        return False, pac.error


def estatus_timbrado(rfc, id_original=0, new_server=True, ong=False):
    pac = Pac(rfc, new_server, ong)
    res = pac.estatus_timbrado(id_original)
    if res:
        return True, res
    else:
        return False, pac.error


def timbra_xml(rfc, xml, id_original, new_server=True, ong=False):
    pac = Pac(rfc, new_server, ong)
    timbrada = pac.timbra_xml(xml, id_original)
    if timbrada:
        #~ timbrada = timbrada.replace("'", "''")
        xml = ET.fromstring(timbrada)
        version = xml.attrib['version']
        timbre = xml.find('{}Complemento'.format(PRE[version]))
        timbre = timbre.find('{}TimbreFiscalDigital'.format(PRE['TIMBRE']))
        data = {
            'xml': timbrada.replace("'", "''"),
            'uuid': timbre.attrib['UUID'],
            'fecha': timbre.attrib['FechaTimbrado'].replace('T',' '),
        }
        return True, data
    else:
        return False, pac.error


def obtener_timbrado(rfc, id_original, new_server=True, ong=False):
    pac = Pac(rfc, new_server, ong)
    timbrada = pac.obtener_timbrado(id_original)
    if timbrada:
        return True, timbrada.replace("'", "''")
        #~ return True, to_pretty_xml(timbrada)
    else:
        return False, pac.error


def cancela_multiple(rfc, uuid, new_server=True, ong=False):
    pac = Pac(rfc, new_server, ong)
    estatus = pac.cancela_multiple(uuid)
    if estatus:
        return True, estatus
    else:
        if 'EntityAlreadyExists' in pac.error:
            return True, 'EntityAlreadyExists'
        if pac.error:
            msg = 'Error con el documento: {}\n{}'.format(uuid, pac.error)
            log.error(msg)
            return False, pac.error
        if new_server:
            return cancela_multiple_old(rfc, uuid)
        else:
            return False, ''

def cancela_multiple_old(rfc, uuid, ong=False):
    pac = Pac(rfc, False, ong)
    estatus = pac.cancela_multiple(uuid)
    if estatus:
        return True, estatus
    return False, pac.error

def recuperar_acuse(rfc, uuid, new_server=True, ong=False):
    pac = Pac(rfc, new_server, ong)
    acuse = pac.recuperar_acuse(uuid)
    if acuse:
        return True, acuse
    else:
        return False, pac.error


def render(text):
    p = '\{(\w+)\}'
    fields = re.findall(p, text, re.IGNORECASE)
    if not fields:
        return text
    data = {}
    months = ('Diciembre', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo',
        'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre')
    try:
        for field in fields:
            d, i = field.split('_')
            if d.lower() == 'mes':
                value = datetime.datetime.now().month - int(i)
                value = months[value]
            elif d.lower() == 'año':
                value = datetime.datetime.now().year - int(i)
            data[field] = value
        return text.format(**data)
    except Exception as e:
        return text


def to_pretty_xml(source):
    tree = parseString(source)
    xml = tree.toprettyxml(encoding='utf-8').decode('utf-8')
    return xml


def copy_xml(data, paths, pdf=''):
    new_path_xml = ''
    xml = to_pretty_xml(data['xml'])
    for path in paths:
        if not exists(path[0]):
            continue
        new_path = join(path[0], data['year'], data['month'])
        if not exists(new_path):
            os.makedirs(new_path)
        new_path_xml = join(new_path, data['name'])
        with open(new_path_xml, 'w', encoding='utf-8') as f:
            f.write(xml)
        if pdf:
            shutil.copy(pdf, new_path)
    return new_path_xml


def dumps(values):
    return json.dumps(values)


def loads(values):
    return json.loads(values)


def get_dir_ext(name=''):
    return join(path_to(get_path_extension(), False), name)


def mri(target):
    mri = _create_instance('mytools.Mri', True)
    mri.inspect(target)
    return


def get_ntp_time(host='cronos.cenam.mx', port=123):
    buf = 1024
    address = (host, port)
    msg = '\x1b' + 47 * '\0'

    # reference time (in seconds since 1900-01-01 00:00:00)
    TIME1970 = 2208988800 # 1970-01-01 00:00:00

    # connect to server
    client = socket.socket(AF_INET, SOCK_DGRAM)
    client.sendto(msg.encode(), address)
    msg, address = client.recvfrom(buf)

    t = struct.unpack( "!12I", msg )[10]
    t -= TIME1970
    return datetime.datetime.fromtimestamp(t)


def get_args_sat(xml):
    data = {}
    try:
        xml = ET.fromstring(xml)
        prefix = PRE[xml.attrib['version']]
        data['total'] = xml.attrib['total']
        node = xml.find('{}Emisor'.format(prefix))
        data['emisor_rfc'] = escape(node.attrib['rfc'])
        node = xml.find('{}Receptor'.format(prefix))
        data['receptor_rfc'] = escape(node.attrib['rfc'])
        node = xml.find('{}Complemento/{}TimbreFiscalDigital'.format(
            prefix, PRE['TIMBRE']))
        data['uuid'] = node.attrib['UUID']
        return data
    except Exception as e:
        return {}


def get_status_sat(xml):
    data = get_args_sat(xml)
    if not data:
        msg = 'Error al obtener los datos de consulta'
        return False, msg

    try:
        soap = SAT_SOAP.format(**data).encode('utf-8')
        headers = {
            'SOAPAction': '"http://tempuri.org/IConsultaCFDIService/Consulta"',
            'Content-length': len(soap),
            'Content-type': 'text/xml; charset="UTF-8"'
        }
        req = request.Request(url=SAT_WS, data=soap, method='POST')
        for k, v in headers.items():
            req.add_header(k, v)
        f = request.urlopen(req, timeout=5)
        response = f.read().decode('utf-8')
        result = re.search("(?s)(?<=Estado>).+?(?=</a:)", response).group()
        return True, result
    except Exception as e:
        msg = 'Ocurrio un error al consultar al SAT, intenta de nuevo más tarde'
        return False, msg


