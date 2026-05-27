# -*- coding: utf-8 -*-
"""
Biblioteca de formas volumetricas para viabilidade.
Cada forma expoe:
  nome, descricao, params_schema
  blocos(lc, pc, h, params) -> lista de dicts {ox, oy, oz, w, d, h}

Coordenadas relativas a area construivel (apos recuos).
oz e opcional (default 0) — usado apenas em formas com embasamento.
"""


class FormaRetangular(object):
    nome = u'Retangular'
    descricao = u'Envelope completo — ocupa toda a area construivel.'
    params_schema = {}

    def blocos(self, lc, pc, h, params):
        return [{'ox': 0, 'oy': 0, 'oz': 0, 'w': lc, 'd': pc, 'h': h}]


class FormaTorre(object):
    nome = u'Torre Central'
    descricao = u'Torre compacta centralizada no lote — eficiente em lotes pequenos.'
    params_schema = {
        'pct_largura':      {'label': u'Largura (%lc)',      'min': 0.20, 'max': 0.90, 'default': 0.50},
        'pct_profundidade': {'label': u'Profundidade (%pc)', 'min': 0.20, 'max': 0.90, 'default': 0.50},
    }

    def blocos(self, lc, pc, h, params):
        tw = lc * params.get('pct_largura', 0.50)
        td = pc * params.get('pct_profundidade', 0.50)
        return [{'ox': (lc - tw) / 2.0, 'oy': (pc - td) / 2.0, 'oz': 0,
                 'w': tw, 'd': td, 'h': h}]


class FormaLamina(object):
    nome = u'Lamina'
    descricao = u'Bloco alongado — maxima ventilacao e iluminacao lateral.'
    params_schema = {
        'pct_espessura': {'label': u'Espessura (%pc)',              'min': 0.15, 'max': 0.65, 'default': 0.35},
        'posicao':       {'label': u'Posicao (0=fundo / 1=frente)', 'min': 0.0,  'max': 1.0,  'default': 0.0},
    }

    def blocos(self, lc, pc, h, params):
        td = pc * params.get('pct_espessura', 0.35)
        oy = (pc - td) * params.get('posicao', 0.0)
        return [{'ox': 0, 'oy': oy, 'oz': 0, 'w': lc, 'd': td, 'h': h}]


class FormaL(object):
    nome = u'Forma em L'
    descricao = u'Uma asa lateral — patio aberto em dois lados, boa para esquinas.'
    params_schema = {
        'pct_asa_larg':  {'label': u'Largura da asa (%lc)', 'min': 0.25, 'max': 0.75, 'default': 0.45},
        'pct_base_prof': {'label': u'Prof. da base (%pc)',  'min': 0.20, 'max': 0.60, 'default': 0.40},
    }

    def blocos(self, lc, pc, h, params):
        al = lc * params.get('pct_asa_larg', 0.45)
        bp = pc * params.get('pct_base_prof', 0.40)
        return [
            {'ox': 0, 'oy': 0,  'oz': 0, 'w': lc, 'd': bp,      'h': h},
            {'ox': 0, 'oy': bp, 'oz': 0, 'w': al, 'd': pc - bp, 'h': h},
        ]


class FormaU(object):
    nome = u'Forma em U'
    descricao = u'Duas asas + fundo — patio frontal aberto, classica em residencial.'
    params_schema = {
        'pct_asa':   {'label': u'Largura de cada asa (%lc)',  'min': 0.15, 'max': 0.40, 'default': 0.28},
        'pct_fundo': {'label': u'Profundidade do fundo (%pc)','min': 0.15, 'max': 0.45, 'default': 0.30},
    }

    def blocos(self, lc, pc, h, params):
        aw = lc * params.get('pct_asa', 0.28)
        fd = pc * params.get('pct_fundo', 0.30)
        return [
            {'ox': 0,        'oy': 0,        'oz': 0, 'w': aw,        'd': pc, 'h': h},
            {'ox': lc - aw,  'oy': 0,        'oz': 0, 'w': aw,        'd': pc, 'h': h},
            {'ox': aw,       'oy': pc - fd,  'oz': 0, 'w': lc - 2*aw, 'd': fd, 'h': h},
        ]


class FormaH(object):
    nome = u'Forma em H'
    descricao = u'Dois corredores abertos — dois patios laterais, boa ventilacao cruzada.'
    params_schema = {
        'pct_asa':      {'label': u'Largura de cada asa (%lc)', 'min': 0.15, 'max': 0.40, 'default': 0.28},
        'pct_corredor': {'label': u'Espessura do corredor (%pc)','min': 0.10, 'max': 0.35, 'default': 0.20},
    }

    def blocos(self, lc, pc, h, params):
        aw = lc * params.get('pct_asa', 0.28)
        cw = pc * params.get('pct_corredor', 0.20)
        cy = (pc - cw) / 2.0
        return [
            {'ox': 0,        'oy': 0,  'oz': 0, 'w': aw,        'd': pc, 'h': h},
            {'ox': lc - aw,  'oy': 0,  'oz': 0, 'w': aw,        'd': pc, 'h': h},
            {'ox': aw,       'oy': cy, 'oz': 0, 'w': lc - 2*aw, 'd': cw, 'h': h},
        ]


class FormaT(object):
    nome = u'Forma em T'
    descricao = u'Travessa frontal + haste posterior — classica para comercial e misto.'
    params_schema = {
        'pct_travessa_prof': {'label': u'Profundidade da travessa (%pc)', 'min': 0.15, 'max': 0.50, 'default': 0.35},
        'pct_haste_larg':    {'label': u'Largura da haste (%lc)',         'min': 0.20, 'max': 0.70, 'default': 0.45},
    }

    def blocos(self, lc, pc, h, params):
        td = pc * params.get('pct_travessa_prof', 0.35)
        tw = lc * params.get('pct_haste_larg', 0.45)
        ox = (lc - tw) / 2.0
        return [
            {'ox': 0,  'oy': 0,  'oz': 0, 'w': lc, 'd': td,      'h': h},
            {'ox': ox, 'oy': td, 'oz': 0, 'w': tw, 'd': pc - td, 'h': h},
        ]


class FormaDuasTorres(object):
    nome = u'Duas Torres'
    descricao = u'Dois blocos independentes lado a lado — passagem e iluminacao central.'
    params_schema = {
        'pct_torre': {'label': u'Largura de cada torre (%lc)', 'min': 0.15, 'max': 0.45, 'default': 0.35},
        'pct_gap':   {'label': u'Gap entre torres (%lc)',       'min': 0.05, 'max': 0.30, 'default': 0.10},
    }

    def blocos(self, lc, pc, h, params):
        tw    = lc * params.get('pct_torre', 0.35)
        gap   = lc * params.get('pct_gap', 0.10)
        total = 2 * tw + gap
        ox1   = (lc - total) / 2.0
        ox2   = ox1 + tw + gap
        return [
            {'ox': ox1, 'oy': 0, 'oz': 0, 'w': tw, 'd': pc, 'h': h},
            {'ox': ox2, 'oy': 0, 'oz': 0, 'w': tw, 'd': pc, 'h': h},
        ]


class FormaTorreComBase(object):
    nome = u'Torre com Embasamento'
    descricao = u'Base ampla nos primeiros andares + torre compacta acima — tipico de alto padrao.'
    params_schema = {
        'pavs_base':      {'label': u'Pavimentos do embasamento', 'min': 1,    'max': 10,   'default': 4},
        'pct_torre_larg': {'label': u'Largura da torre (%lc)',    'min': 0.20, 'max': 0.80, 'default': 0.50},
        'pct_torre_prof': {'label': u'Prof. da torre (%pc)',      'min': 0.20, 'max': 0.80, 'default': 0.50},
    }

    def blocos(self, lc, pc, h, params, pe=3.0):
        pv  = max(1, int(params.get('pavs_base', 4)))
        tw  = lc * params.get('pct_torre_larg', 0.50)
        td  = pc * params.get('pct_torre_prof', 0.50)
        hb  = pv * pe
        ht  = max(0.0, h - hb)
        tox = (lc - tw) / 2.0
        toy = (pc - td) / 2.0
        result = [{'ox': 0, 'oy': 0, 'oz': 0, 'w': lc, 'd': pc, 'h': hb}]
        if ht > 0.1:
            result.append({'ox': tox, 'oy': toy, 'oz': hb, 'w': tw, 'd': td, 'h': ht})
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Catalogo global
# ─────────────────────────────────────────────────────────────────────────────

FORMAS = [
    FormaRetangular(),
    FormaTorre(),
    FormaLamina(),
    FormaL(),
    FormaU(),
    FormaH(),
    FormaT(),
    FormaDuasTorres(),
    FormaTorreComBase(),
]

FORMAS_POR_NOME = {f.nome: f for f in FORMAS}
