# -*- coding: utf-8 -*-
#~ '****************************************************************************
#~ '    Factura Libre CFDI
#~ '
#~ '    Copyright (C) 2009 Mauricio Baeza Servin
#~ '    Este programa es software libre. Puede redistribuirlo y/o modificarlo
#~ '    bajo los términos de la Licencia Pública General de GNU según es
#~ '    publicada por la Free Software Foundation, bien de la versión 3 de dicha
#~ '    Licencia o bien (según su elección) de cualquier versión posterior.
#~ '
#~ '    Este programa se distribuye con la esperanza de que sea útil, pero SIN
#~ '    NINGUNA GARANTÍA, incluso sin la garantía MERCANTIL implícita o sin
#~ '    garantizar la CONVENIENCIA PARA UN PROPÓSITO PARTICULAR.
#~ '    Véase la Licencia Pública General de GNU para más detalles.
#~ '
#~ '    Debería haber recibido una copia de la Licencia Pública General junto
#~ '    con este programa. Si no ha sido así, escriba a la Free Software
#~ '    Foundation, Inc., en 675 Mass Ave, Cambridge, MA 02139, EEUU.
#~ '
#~ '    Mauricio Baeza - public ARROBA mauriciobaeza.net
#~ '
#~ '****************************************************************************

import logging
import unohelper
from com.sun.star.lang import XServiceInfo
from com.sun.star.task import XJobExecutor
from facturalibre.settings import DEBUG, IMPLE_NAME, LOG
from facturalibre.modulos.util import get_path_debug


formatter = logging.Formatter(LOG['FORMAT'], datefmt=LOG['DATE'])
logging.basicConfig(
    level=logging.DEBUG, format=LOG['FORMAT'], datefmt=LOG['DATE'])
log = logging.getLogger(LOG['NAME'])


class Cfdi(unohelper.Base, XServiceInfo, XJobExecutor):

    def __init__(self, ctx):
        self.ctx = ctx

    # XJobExecutor
    def trigger(self, *args):
        """CFDI called by this kind of URL:
        service:org.universolibre.facturalibre.cfd?OPTION_VALUE"""
        handler = logging.FileHandler(get_path_debug())
        handler.setFormatter(formatter)
        if DEBUG:
            handler.setLevel(logging.DEBUG)
        else:
            handler.setLevel(logging.INFO)
        log.addHandler(handler)
        try:
            import facturalibre
            dialog = facturalibre.CFDI(self.ctx, args[0])
            if dialog.validate:
                dialog.show()
        except Exception as e:
            log.error('INIT: ', exc_info=True)
        return

    # XServiceInfo
    def getImplementationName(self):
        return IMPLE_NAME

    def supportsService(self, ServiceName):
        return ServiceName == IMPLE_NAME

    def getSupportedServiceNames(self):
        return (IMPLE_NAME,)


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(Cfdi, IMPLE_NAME, (IMPLE_NAME,),)

