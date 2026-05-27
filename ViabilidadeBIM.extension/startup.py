# -*- coding: utf-8 -*-
"""
startup.py — executado pelo pyRevit ao carregar a extensao.
Registra o painel lateral dockable de Viabilidade BIM.
"""
import os, sys

_lib = os.path.join(os.path.dirname(__file__), 'lib')
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import clr
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.UI import IDockablePaneProvider, DockablePaneProviderData

import painel as _painel


class _PainelProvider(IDockablePaneProvider):
    def SetupDockablePane(self, data):
        _painel.inicializar()
        data.FrameworkElement = _painel.get_elemento()


try:
    from pyrevit import HOST_APP
    HOST_APP.uiapp.RegisterDockablePane(
        _painel.PANE_ID,
        u'Viabilidade BIM',
        _PainelProvider(),
    )
except Exception as ex:
    # Ja registrado (reload do pyRevit) — ignora
    pass
