# -*- coding: utf-8 -*-
from facturalibre.settings import DEBUG, VERSION


class Config(object):

    def __init__(self, util):
        self.DEBUG = DEBUG
        self.ULM_VERSION = VERSION
        self.APP_TITULO = 'Factura Libre CFDI 3.2'
        self.ULM_NAME = 'Universo Libre México, A.C.'
        self.ULM_HOME = 'http://www.universolibre.org'
        self.ULM_ID = 'org.universolibre.facturalibre.cfdi'
        self.NODE = '/{}.Configuration/Settings'.format(self.ULM_ID)
        self.EXT_PATH = util.getPathExtension(self.ULM_ID)
        self.PATH_USER = util.getPathUser()
        self.OS = util.getOS()
        self.DB_NAME = 'facturalibre2.sqlite'
        self.DB_CP = 'cp.sqlite'
        self.CURRENT_PATH = util.get_configvalue(self.NODE, 'Actual')
        self.PAIS = 'México'
        self.IMPUESTO_EXENTO = 'EXENTO'
        self.IMPUESTO_IVA = 'IVA'
        self.IMPUESTO_ISR = 'ISR'
        self.SIGNO_MENOS = '-'
        self.LIMITE_IMPUESTO = 80
        self.RFC_EXTRANJERO = 'XEXX010101000'
        self.RFC_PUBLICO = 'XAXX010101000'
        self.PUBLICO = 'PÚBLICO EN GENERAL'
        self.WIN = 'win32'
        self.LINUX = 'linux'
        self.METODO_PAGO = 'No identificado'
        self.FORMA_PAGO = 'Pago en una sola exhibición'
        self.FORMAT = '{0:,.%sf}'
        self.PRE = '{http://www.sat.gob.mx/cfd/3}'
        self.PATH = util.join(util.urlToSystem(self.EXT_PATH), 'bin')
        self.FILE_NAME = '{serie}{folio:06d}_{receptor_rfc}'
