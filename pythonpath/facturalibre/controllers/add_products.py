#!
# -*- coding: utf-8 -*-

EXTENSION_PLANTILLA = '.ods'


class EventosAddProducts(object):
    def __init__(self,caller):
        self.caller = caller
        self.unogui = caller.unogui
        self.util = caller.util
        self.dialog = caller.dialog
        self.dm = self.dialog.getModel()

    def cmdSalir(self):
        self.dialog.endExecute()
        return

    def cmdAgregarProductos(self):
        plantilla = self.dialog.getControl('fileProductos')
        if self.unogui.validate(plantilla, 'Vacio'):
            plantilla.setFocus()
            message = 'Establece la ruta del archivo ODS de Calc con los ' \
                        'productos a importar'
            self.unogui.createMsgBox({'Message': message})
            return
        if not self.util.exists(plantilla.Text):
            message = 'No se encontró el archivo ODS en la ruta establecida'
            self.unogui.createMsgBox({'Message': message})
            return
        _,_,_,extension = self.util.getInfoPath(plantilla.Text)
        if extension != EXTENSION_PLANTILLA:
            message = 'El archivo no es un archivo ODS de Calc'
            self.unogui.createMsgBox({'Message': message})
            return
        try:
            properties = self.util.setPropertiesValues(('Hidden', True, 'AsTemplate', True))
            doc = self.unogui.openDoc(plantilla.Text, properties)
            sheet = doc.getSheets().getByIndex(0)
            data = self.__add_products(sheet)
            if data:
                self.caller.caller.new_products = data
                self.cmdSalir()
        except:
            log = traceback.format_exc()
            self.util.debug(log)
            print(log)
        finally:
            doc.dispose()        
        return

    def __add_products(self, sheet):
        data = self.__get_data(sheet)
        if not data:
            message = 'El archivo no contiene datos a importar'
            self.unogui.createMsgBox({'Message': message})
            return False
        rows_count = len(data)
        message = 'Se encontraron %s productos para agregar\n\n' \
                    '¿Estás seguro de agregarlos?' % rows_count
        if not self.unogui.createQuestion('Factura Libre', message):
            return False
        return data

    def __get_data(self, sheet):
        cell = sheet.getCellByPosition(0,0)
        c = sheet.createCursorByRange(cell)
        c.collapseToCurrentRegion()
        if c.getRows().getCount() == 1:
            return None
        cells = sheet.getCellRangeByPosition(
                                0, 1,
                                c.getRangeAddress().EndColumn,
                                c.getRangeAddress().EndRow)
        return cells.getDataArray()        