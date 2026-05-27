# -*- coding: utf-8 -*-
"""
Botao: Calcular VGV — abre/foca o painel lateral de viabilidade.
O painel fica dockado na interface do Revit (sem janela popup).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))

import painel
from pyrevit import HOST_APP, forms

try:
    # Mostra/foca o painel dockable
    pane = HOST_APP.uiapp.GetDockablePane(painel.PANE_ID)
    pane.Show()
    # Recarrega os dados do lote ativo
    painel.atualizar_lote()
except Exception as ex:
    forms.alert(
        u'Nao foi possivel abrir o painel lateral.\n\n'
        u'Reinicie o Revit para registrar o painel.\n\n'
        u'Detalhe: ' + str(ex)
    )
