# -*- coding: utf-8 -*-
"""
Motor de análise financeira de viabilidade imobiliária.
Nenhum valor está codificado — todos os parâmetros vêm do usuário.
"""

EFICIENCIA_PADRAO = 0.82   # ratio área privativa / área construída bruta


def calcular(envelope, params):
    """
    Análise completa de viabilidade.

    envelope : saída de massas.calcular_envelope()
    params   : {
        preco_venda_m2         : float  (R$/m² privativo)
        custo_construcao_m2    : float  (R$/m² construído)
        eficiencia_planta      : float  (0–1, padrão 0.82)
        custo_terreno          : float  (R$)
        outras_despesas_pct    : float  (0–1, % do VGV — corretagem, proj, taxas)
        n_pavimentos_override  : int | None
    }
    """
    n   = params.get('n_pavimentos_override') or envelope['pavimentos_max']
    ap  = envelope['area_pavimento_m2']
    ac  = ap * n                                       # área construída efetiva
    ef  = params.get('eficiencia_planta', EFICIENCIA_PADRAO)
    apr = ac * ef                                      # área privativa

    vgv               = apr  * params['preco_venda_m2']
    custo_obra        = ac   * params['custo_construcao_m2']
    custo_terreno     = params.get('custo_terreno', 0.0)
    outras_despesas   = vgv  * params.get('outras_despesas_pct', 0.15)
    custo_total       = custo_obra + custo_terreno + outras_despesas

    lucro             = vgv - custo_total
    margem            = lucro / vgv        if vgv        > 0 else 0.0
    roi               = lucro / custo_total if custo_total > 0 else 0.0
    custo_m2_priv     = custo_total / apr  if apr        > 0 else 0.0

    return {
        'n_pavimentos':         n,
        'area_construida_m2':   ac,
        'eficiencia_pct':       ef * 100,
        'area_privativa_m2':    apr,
        'vgv':                  vgv,
        'custo_obra':           custo_obra,
        'custo_terreno':        custo_terreno,
        'outras_despesas':      outras_despesas,
        'custo_total':          custo_total,
        'lucro_bruto':          lucro,
        'margem_pct':           margem * 100,
        'roi_pct':              roi * 100,
        'custo_m2_privativo':   custo_m2_priv,
    }


def calcular_tipologias(tipologias_geradas, envelope_base, params):
    """
    Calcula viabilidade para cada tipologia gerada por massas.gerar_tipologias().
    Retorna lista de dicts com nome + resultado financeiro completo.
    """
    resultados = []
    for tip in tipologias_geradas:
        env_tip = dict(envelope_base)
        env_tip['area_pavimento_m2'] = tip['area_pavimento_m2']
        env_tip['pavimentos_max']    = tip['pavimentos']

        fin = calcular(env_tip, params)
        fin['nome'] = tip['nome']
        resultados.append(fin)
    return resultados


# ── Formatação ───────────────────────────────────────────────────────────────

def fmt_reais(v):
    if abs(v) >= 1000000:
        return 'R$ {:.2f} M'.format(v / 1000000.0)
    if abs(v) >= 1000:
        return 'R$ {:.1f} k'.format(v / 1000.0)
    return 'R$ {:.2f}'.format(v)


def relatorio(resultado, envelope, nome_leg=''):
    linhas = [
        '=' * 52,
        '  RELATÓRIO DE VIABILIDADE',
    ]
    if nome_leg:
        linhas.append('  Legislação: ' + nome_leg)
    linhas += [
        '=' * 52,
        '',
        'PARÂMETROS URBANÍSTICOS',
        '  Área do lote      : {:>10.1f} m²'.format(envelope['area_lote_m2']),
        '  CA utilizado      : {:>10.2f}'.format(envelope['ca_utilizado']),
        '  TO utilizado      : {:>10.1%}'.format(envelope['to_utilizado']),
        '  Pavimentos        : {:>10d}'.format(resultado['n_pavimentos']),
        '  Gabarito          : {:>10.1f} m'.format(envelope['gabarito_m']),
        '',
        'ÁREAS',
        '  Área construída   : {:>10.1f} m²'.format(resultado['area_construida_m2']),
        '  Eficiência planta : {:>10.1f}%'.format(resultado['eficiencia_pct']),
        '  Área privativa    : {:>10.1f} m²'.format(resultado['area_privativa_m2']),
        '',
        'FINANCEIRO',
        '  VGV               : {:>18}'.format(fmt_reais(resultado['vgv'])),
        '  Custo obra        : {:>18}'.format(fmt_reais(resultado['custo_obra'])),
        '  Custo terreno     : {:>18}'.format(fmt_reais(resultado['custo_terreno'])),
        '  Outras despesas   : {:>18}'.format(fmt_reais(resultado['outras_despesas'])),
        '  ─' * 26,
        '  Custo total       : {:>18}'.format(fmt_reais(resultado['custo_total'])),
        '  Lucro bruto       : {:>18}'.format(fmt_reais(resultado['lucro_bruto'])),
        '  Margem            : {:>10.1f}%'.format(resultado['margem_pct']),
        '  ROI               : {:>10.1f}%'.format(resultado['roi_pct']),
        '=' * 52,
    ]
    return '\n'.join(linhas)
