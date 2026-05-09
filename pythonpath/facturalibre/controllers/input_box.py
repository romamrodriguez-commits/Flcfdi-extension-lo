# -*- coding: utf-8 -*-
import logging
from facturalibre.settings import LOG


log = logging.getLogger(LOG['NAME'])


class InputBoxEvents(object):

    def __init__(self, dialog, caller):
        self.dialog = dialog
        self.caller = caller
        self.dm = self.dialog.getModel()

    def ok(self, event):
        txt = self.dialog.getControl('value')
        self.caller.value = txt.Text.strip()
        self.dialog.endDialog(1)
        return

    def cancel(self, event):
        self.dialog.endDialog(0)
        return














