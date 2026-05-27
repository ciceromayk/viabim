# -*- coding: utf-8 -*-
"""
Botao: Gerar Massa — cria o envelope construtivo, os niveis e as lajes
por pavimento como DirectShapes no modelo Revit.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
import config as cfg
import massas

from pyrevit import revit, forms

doc = revit.doc


def _carregar_ou_abortar():
    lote = cfg.carregar_lote()
    if not lote:
        forms.alert(
            u'Configure o lote antes de gerar a massa.\n(Botao "Configurar Lote")',
            exitscript=True)

    leg = None
    try:
        leg = cfg.carregar_legislacao_ativa()
    except Exception:
        pass

    if not leg:
        legs = cfg.listar_legislacoes()
        if not legs:
            forms.alert(
                u'Nenhuma legislacao cadastrada.\nUse "Gerenciar Legislacao".',
                exitscript=True)
        escolha = forms.SelectFromList.show(
            [l['nome'] for l in legs],
            title=u'Selecionar Legislacao',
            button_name=u'Usar')
        if not escolha:
            sys.exit()
        leg = legs[[l['nome'] for l in legs].index(escolha)]
        cfg.definir_legislacao_ativa(leg['id'])

    return lote, leg


lote, leg = _carregar_ou_abortar()

erros = massas.validar_lote(lote, leg)
if erros:
    continuar = forms.alert(
        u'Atencao — lote fora dos parametros:\n\n' +
        '\n'.join(erros) +
        u'\n\nDeseja gerar mesmo assim?',
        ok=False, yes=True, no=True)
    if not continuar:
        sys.exit()

env = massas.calcular_envelope(lote, leg)

msg = (
    u'Envelope a gerar:\n\n'
    u'  Lote: {nome}  ({l}m x {p}m = {al:.0f} m2)\n'
    u'  Legislacao: {leg}\n\n'
    u'  Area de pavimento: {ap:.1f} m2\n'
    u'  Pavimentos: {pav}\n'
    u'  Pe-direito: {pe:.2f} m\n'
    u'  Gabarito total: {gab:.1f} m\n'
    u'  Area construida: {ac:.1f} m2\n\n'
    u'Serao criados automaticamente:\n'
    u'  - 1 massa envelope\n'
    u'  - {npav} niveis (Terreo ... Cobertura)\n'
    u'  - {nlaj} lajes simbolicas\n\n'
    u'Confirmar?'
).format(
    nome=lote['nome'],
    l=lote['largura_m'],
    p=lote['profundidade_m'],
    al=env['area_lote_m2'],
    leg=leg['nome'],
    ap=env['area_pavimento_m2'],
    pav=env['pavimentos_max'],
    pe=env['pe_direito_m'],
    gab=env['gabarito_m'],
    ac=env['area_construida_m2'],
    npav=env['pavimentos_max'] + 1,
    nlaj=env['pavimentos_max'] + 1,
)

if not forms.alert(msg, ok=False, yes=True, no=True):
    sys.exit()

el, env, niveis, lajes = massas.gerar_envelope(doc, lote, leg)

forms.alert(
    u'Concluido!\n\n'
    u'  Massa envelope:  criada\n'
    u'  Niveis criados:  {n}\n'
    u'  Lajes criadas:   {l}\n\n'
    u'  Area construida: {ac:.1f} m2\n'
    u'  Pavimentos:      {pav}'.format(
        n=len(niveis),
        l=len(lajes),
        ac=env['area_construida_m2'],
        pav=env['pavimentos_max'],
    )
)
