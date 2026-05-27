# -*- coding: utf-8 -*-
"""
Gerenciamento de configurações de legislação urbanística e dados do lote.
Persiste em %APPDATA%\ViabilidadeBIM\ como arquivos JSON — sem vínculo
com nenhum município específico.

Compatível com IronPython 2 (pyRevit).
"""
import os
import io
import json
import uuid

_PASTA_BASE = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'ViabilidadeBIM')
_PASTA_LEG  = os.path.join(_PASTA_BASE, 'legislacao')
_ARQ_LOTE   = os.path.join(_PASTA_BASE, 'lote_atual.json')
_ARQ_LEGSEL = os.path.join(_PASTA_BASE, 'legislacao_ativa.json')


def _garantir_pastas():
    """Cria as pastas de dados se ainda não existirem (compatível com Python 2)."""
    if not os.path.exists(_PASTA_BASE):
        os.makedirs(_PASTA_BASE)
    if not os.path.exists(_PASTA_LEG):
        os.makedirs(_PASTA_LEG)


def _ler_json(caminho):
    with io.open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


def _gravar_json(caminho, dados):
    with io.open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ── Legislação ───────────────────────────────────────────────────────────────

def listar_legislacoes():
    _garantir_pastas()
    resultado = []
    for arq in os.listdir(_PASTA_LEG):
        if arq.endswith('.json'):
            try:
                resultado.append(_ler_json(os.path.join(_PASTA_LEG, arq)))
            except Exception:
                pass
    return sorted(resultado, key=lambda x: x.get('nome', ''))


def carregar_legislacao(leg_id):
    caminho = os.path.join(_PASTA_LEG, leg_id + '.json')
    if not os.path.exists(caminho):
        raise IOError('Legislacao nao encontrada: ' + leg_id)
    return _ler_json(caminho)


def salvar_legislacao(dados):
    _garantir_pastas()
    if not dados.get('id'):
        dados['id'] = str(uuid.uuid4())[:8]
    _gravar_json(os.path.join(_PASTA_LEG, dados['id'] + '.json'), dados)
    return dados['id']


def excluir_legislacao(leg_id):
    caminho = os.path.join(_PASTA_LEG, leg_id + '.json')
    if os.path.exists(caminho):
        os.remove(caminho)


def carregar_legislacao_ativa():
    if not os.path.exists(_ARQ_LEGSEL):
        return None
    ref = _ler_json(_ARQ_LEGSEL)
    return carregar_legislacao(ref['id'])


def definir_legislacao_ativa(leg_id):
    _garantir_pastas()
    _gravar_json(_ARQ_LEGSEL, {'id': leg_id})


# ── Lote atual ───────────────────────────────────────────────────────────────

def carregar_lote():
    if not os.path.exists(_ARQ_LOTE):
        return None
    return _ler_json(_ARQ_LOTE)


def salvar_lote(lote):
    _garantir_pastas()
    _gravar_json(_ARQ_LOTE, lote)


# ── Templates ────────────────────────────────────────────────────────────────

def template_legislacao():
    """Retorna estrutura base vazia de uma configuração de legislação."""
    return {
        'id': '',
        'nome': 'Nova Configuracao',
        'municipio': '',
        'zona': '',
        'parametros': {
            'CA_basico': 1.0,
            'CA_maximo': 2.5,
            'TO_maximo': 0.60,
            'gabarito_max_m': None,
            'gabarito_max_pavimentos': 12,
            'recuos_m': {
                'frontal': 5.0,
                'lateral': 1.5,
                'fundo': 3.0,
            },
            'altura_pe_direito_m': 3.0,
            'outorga_percentual_vgv': 0.10,
        },
        'notas': '',
    }


def template_lote():
    return {
        'nome': 'Lote 01',
        'largura_m': 20.0,
        'profundidade_m': 40.0,
    }


def instalar_exemplos():
    """Instala configurações de exemplo se ainda não houver nenhuma."""
    if listar_legislacoes():
        return

    exemplos = [
        {
            'id': 'generico_residencial',
            'nome': u'Genérico — Residencial Médio Padrão',
            'municipio': u'Genérico',
            'zona': 'Residencial',
            'parametros': {
                'CA_basico': 1.0,
                'CA_maximo': 2.5,
                'TO_maximo': 0.60,
                'gabarito_max_m': None,
                'gabarito_max_pavimentos': 12,
                'recuos_m': {'frontal': 5.0, 'lateral': 1.5, 'fundo': 3.0},
                'altura_pe_direito_m': 3.0,
                'outorga_percentual_vgv': 0.10,
            },
            'notas': u'Parâmetros genéricos. Ajuste conforme a legislação local.',
        },
        {
            'id': 'generico_misto',
            'nome': u'Genérico — Zona Mista / Alta Densidade',
            'municipio': u'Genérico',
            'zona': 'Misto',
            'parametros': {
                'CA_basico': 2.0,
                'CA_maximo': 6.0,
                'TO_maximo': 0.70,
                'gabarito_max_m': None,
                'gabarito_max_pavimentos': None,
                'recuos_m': {'frontal': 3.0, 'lateral': 0.0, 'fundo': 3.0},
                'altura_pe_direito_m': 3.0,
                'outorga_percentual_vgv': 0.10,
            },
            'notas': u'Parâmetros genéricos para zonas mistas. Ajuste pelo PDM local.',
        },
        {
            'id': 'generico_comercial',
            'nome': u'Genérico — Comercial / Sem Gabarito',
            'municipio': u'Genérico',
            'zona': 'Comercial',
            'parametros': {
                'CA_basico': 1.0,
                'CA_maximo': 8.0,
                'TO_maximo': 0.80,
                'gabarito_max_m': None,
                'gabarito_max_pavimentos': None,
                'recuos_m': {'frontal': 0.0, 'lateral': 0.0, 'fundo': 0.0},
                'altura_pe_direito_m': 3.0,
                'outorga_percentual_vgv': 0.10,
            },
            'notas': u'Zona comercial irrestrita. Verifique legislação local.',
        },
    ]
    for ex in exemplos:
        salvar_legislacao(ex)
