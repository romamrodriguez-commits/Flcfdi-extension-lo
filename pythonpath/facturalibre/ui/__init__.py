# -*- coding: utf-8 -*-


class Dialog(object):

    def __init__(self, caller, option=''):
        self.caller = caller
        self.ctx = caller.ctx
        self.util = caller.util
        self.db = caller.db
        self.globales = caller.globales
        self.unogui = caller.unogui
        getattr(self, '_{}'.format(option))()

    def _configuracion(self):
        from . import configuracion
        return configuracion.Dlg(self)

    def _empleados(self):
        from . import empleados
        return empleados.Dlg(self.db)

    def _generarnomina(self):
        from . import nomina
        return nomina.Dlg(self)

    def _adminnomina(self):
        from . import adminnomina
        return adminnomina.Dlg(self)

    def _clientes(self):
        from . import clientes
        return clientes.Dlg(self)

    def _productosadmin(self):
        from . import productosadmin
        return productosadmin.Dlg(self)

    def _generarcfdi(self):
        from . import cfdi
        return cfdi.Dlg(self)

    def _admincfdi(self):
        from . import admincfdi
        return admincfdi.Dlg(self)

    def _tools(self):
        from . import tools
        return tools.Dlg(self)

    def _admincompras(self):
        from . import admincompras
        return admincompras.Dlg(self)

    def _importXML(self):
        from . import importXML
        return importXML.Dlg(self)

    def _reportes(self):
        from . import reportes
        return reportes.Dlg(self)

    def _repclitot(self):
        from . import repclitot
        return repclitot.Dlg(self)

    def _repprod(self):
        from . import repprod
        return repprod.Dlg(self)

    def _reportes(self):
        from . import reportes
        return reportes.Dlg(self)

    def _reportep(self):
        from . import reportep
        return reportep.Dlg(self)

    def _repclitot(self):
        from . import repclitot
        return repclitot.Dlg(self)

    def _repprotot(self):
        from . import repprotot
        return repprotot.Dlg(self)

    def _repprod(self):
        from . import repprod
        return repprod.Dlg(self)

    def _repprop(self):
        from . import repprop
        return repprop.Dlg(self)



