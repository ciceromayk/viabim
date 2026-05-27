# -*- coding: utf-8 -*-
"""
Calculo de envelope construtivo e geracao de massas no Revit via DirectShape.
Totalmente parametrico — nenhum municipio esta codificado aqui.
Compativel com IronPython 2 (pyRevit).
"""

try:
    from Autodesk.Revit.DB import (
        XYZ, Line, CurveLoop, GeometryCreationUtilities,
        DirectShape, ElementId, BuiltInCategory, Transaction,
        UnitUtils, Level, FilteredElementCollector,
        Plane, SketchPlane,
    )
    from System.Collections.Generic import List as CsList
    try:
        from Autodesk.Revit.DB import UnitTypeId
        def _m(metros):
            return UnitUtils.ConvertToInternalUnits(metros, UnitTypeId.Meters)
    except ImportError:
        from Autodesk.Revit.DB import DisplayUnitType
        def _m(metros):
            return UnitUtils.ConvertToInternalUnits(metros, DisplayUnitType.DUT_METERS)
    REVIT_OK = True
except ImportError:
    REVIT_OK = False
    def _m(metros):
        return metros * 3.28084


# ── Calculos de envelope ─────────────────────────────────────────────────────

def calcular_envelope(lote, legislacao):
    p        = legislacao['parametros']
    rec      = p['recuos_m']
    al       = lote['largura_m']
    ap       = lote['profundidade_m']
    area_lote = al * ap

    lc = max(0.0, al - rec['lateral'] * 2)
    pc = max(0.0, ap - rec['frontal'] - rec['fundo'])

    area_pav = min(lc * pc, area_lote * p['TO_maximo'])
    area_total_ca = area_lote * p['CA_maximo']
    pe = p.get('altura_pe_direito_m', 3.0)

    if p.get('gabarito_max_pavimentos'):
        n_pav    = int(p['gabarito_max_pavimentos'])
        gabarito = n_pav * pe
    elif p.get('gabarito_max_m'):
        gabarito = float(p['gabarito_max_m'])
        n_pav    = int(gabarito / pe)
    else:
        n_pav    = int(area_total_ca / area_pav) if area_pav > 0 else 0
        gabarito = n_pav * pe

    if area_pav > 0:
        n_pav = min(n_pav, int(area_total_ca / area_pav))

    gabarito        = n_pav * pe
    area_construida = area_pav * n_pav

    return {
        'area_lote_m2':               area_lote,
        'largura_construivel_m':      lc,
        'profundidade_construivel_m': pc,
        'area_pavimento_m2':          area_pav,
        'pavimentos_max':             n_pav,
        'gabarito_m':                 gabarito,
        'area_construida_m2':         area_construida,
        'ca_utilizado':               area_construida / area_lote if area_lote > 0 else 0,
        'to_utilizado':               area_pav / area_lote if area_lote > 0 else 0,
        'pe_direito_m':               pe,
        'recuos_m':                   rec,
    }


def validar_lote(lote, legislacao):
    p   = legislacao['parametros']
    rec = p['recuos_m']
    erros = []
    min_l = rec['lateral'] * 2 + 2.0
    min_p = rec['frontal'] + rec['fundo'] + 2.0
    if lote['largura_m'] < min_l:
        erros.append('Largura {:.1f}m insuficiente (min. {:.1f}m)'.format(
            lote['largura_m'], min_l))
    if lote['profundidade_m'] < min_p:
        erros.append('Profundidade {:.1f}m insuficiente (min. {:.1f}m)'.format(
            lote['profundidade_m'], min_p))
    return erros


# ── Geometria base ────────────────────────────────────────────────────────────

def _criar_solido(largura_m, prof_m, altura_m, ox_m=0.0, oy_m=0.0, oz_m=0.0):
    """Solido retangular extrudado com origem em (ox, oy, oz) em metros."""
    ox = _m(ox_m); oy = _m(oy_m); oz = _m(oz_m)
    l  = _m(largura_m); p = _m(prof_m); h = _m(altura_m)
    pts = [XYZ(ox, oy, oz), XYZ(ox+l, oy, oz),
           XYZ(ox+l, oy+p, oz), XYZ(ox, oy+p, oz)]
    loop = CurveLoop()
    for i in range(4):
        loop.Append(Line.CreateBound(pts[i], pts[(i+1) % 4]))
    return GeometryCreationUtilities.CreateExtrusionGeometry([loop], XYZ.BasisZ, h)


def _sanitizar_nome(s):
    """Remove/substitui caracteres proibidos pelo Revit em nomes de elementos."""
    _PROIBIDOS = u'—–‒―'  # travessoes e tracoes Unicode
    _PROIBIDOS_ASCII = u'\\:{}[]|;<>?`~'
    for ch in _PROIBIDOS:
        s = s.replace(ch, u'-')
    for ch in _PROIBIDOS_ASCII:
        s = s.replace(ch, u'')
    s = s.strip()
    return s if s else u'Massa'


def _inserir_directshape(doc, solid, nome):
    cat = ElementId(BuiltInCategory.OST_Mass)
    ds  = DirectShape.CreateElement(doc, cat)
    ds.SetShape([solid])
    ds.Name = _sanitizar_nome(nome)
    return ds


def _nome_nivel(i, n_total):
    if i == 0:
        return u'Terreo'
    if i == n_total:
        return u'Cobertura'
    return u'{}o Pavimento'.format(i)


# ── 1. Contorno do lote ───────────────────────────────────────────────────────

def criar_limite_lote(doc, lote, legislacao):
    al  = lote['largura_m']
    ap  = lote['profundidade_m']
    p   = legislacao['parametros']
    rec = p['recuos_m']
    lc  = max(0.0, al - rec['lateral'] * 2)
    pc  = max(0.0, ap - rec['frontal'] - rec['fundo'])
    ox  = rec['lateral']
    oy  = rec['fundo']

    with Transaction(doc, u'ViabilidadeBIM - Limite do Lote') as t:
        t.Start()
        try:
            plane  = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, XYZ(0, 0, 0))
            sketch = SketchPlane.Create(doc, plane)

            def _seg(x1, y1, x2, y2):
                p1 = XYZ(_m(x1), _m(y1), 0)
                p2 = XYZ(_m(x2), _m(y2), 0)
                doc.Create.NewModelCurve(Line.CreateBound(p1, p2), sketch)

            _seg(0,  0,  al, 0)
            _seg(al, 0,  al, ap)
            _seg(al, ap, 0,  ap)
            _seg(0,  ap, 0,  0)

            _seg(ox,      oy,      ox + lc, oy)
            _seg(ox + lc, oy,      ox + lc, oy + pc)
            _seg(ox + lc, oy + pc, ox,      oy + pc)
            _seg(ox,      oy + pc, ox,      oy)

            t.Commit()
        except Exception as ex:
            t.RollBack()
            raise ex


# ── 2. Niveis e lajes ─────────────────────────────────────────────────────────

def criar_niveis_e_lajes(doc, envelope):
    n_pav    = envelope['pavimentos_max']
    pe       = envelope['pe_direito_m']
    rec      = envelope['recuos_m']
    lc       = envelope['largura_construivel_m']
    pc       = envelope['profundidade_construivel_m']
    esp_laje = 0.20
    blocos   = envelope.get('blocos')  # None quando envelope simples (sem forma)

    niveis_criados = []
    lajes_criadas  = []

    with Transaction(doc, u'ViabilidadeBIM - Niveis e Lajes') as t:
        t.Start()

        existentes = FilteredElementCollector(doc).OfClass(Level).ToElements()
        ids = CsList[ElementId]()
        for lv in existentes:
            ids.Add(lv.Id)
        if ids.Count > 0:
            try:
                doc.Delete(ids)
            except Exception:
                for lv_id in list(ids):
                    try:
                        doc.Delete(lv_id)
                    except Exception:
                        pass

        for i in range(n_pav + 1):
            elev_m   = i * pe
            elev_pes = _m(elev_m)
            nome     = _nome_nivel(i, n_pav)

            try:
                nivel = Level.Create(doc, elev_pes)
                nivel.Name = _sanitizar_nome(nome)
                niveis_criados.append(nivel)
            except Exception:
                pass

            if blocos:
                # Cria uma laje por bloco da forma, apenas nos niveis que o bloco alcanca
                for j, b in enumerate(blocos):
                    b_oz = b.get('oz', 0.0)
                    if b_oz <= elev_m <= b_oz + b['h']:
                        solid_laje = _criar_solido(
                            b['w'], b['d'], esp_laje,
                            ox_m=rec['lateral'] + b['ox'],
                            oy_m=rec['fundo']   + b['oy'],
                            oz_m=elev_m,
                        )
                        label = (u'Laje - {} [{}]'.format(nome, j + 1)
                                 if len(blocos) > 1 else u'Laje - ' + nome)
                        laje = _inserir_directshape(doc, solid_laje, label)
                        lajes_criadas.append(laje)
            else:
                solid_laje = _criar_solido(lc, pc, esp_laje,
                                           ox_m=rec['lateral'],
                                           oy_m=rec['fundo'],
                                           oz_m=elev_m)
                laje = _inserir_directshape(doc, solid_laje, u'Laje - ' + nome)
                lajes_criadas.append(laje)

        t.Commit()

    return niveis_criados, lajes_criadas


# ── 3. Operacoes de alto nivel ────────────────────────────────────────────────

def gerar_envelope(doc, lote, legislacao, n_pav_override=None):
    env = calcular_envelope(lote, legislacao)
    rec = env['recuos_m']
    n   = n_pav_override if n_pav_override else env['pavimentos_max']
    h   = n * env['pe_direito_m']

    try:
        criar_limite_lote(doc, lote, legislacao)
    except Exception:
        pass

    with Transaction(doc, u'ViabilidadeBIM - Envelope') as t:
        t.Start()
        solid = _criar_solido(env['largura_construivel_m'],
                              env['profundidade_construivel_m'],
                              h, ox_m=rec['lateral'], oy_m=rec['fundo'])
        el = _inserir_directshape(doc, solid,
                                  u'Envelope Maximo - ' + lote.get('nome', ''))
        t.Commit()

    niveis, lajes = criar_niveis_e_lajes(doc, env)
    return el, env, niveis, lajes


def calcular_envelope_forma(lote, legislacao, forma, params_forma=None):
    from formas import FormaTorreComBase

    env = calcular_envelope(lote, legislacao)

    if params_forma is None:
        params_forma = {k: v['default'] for k, v in forma.params_schema.items()}

    pe = env['pe_direito_m']
    lc = env['largura_construivel_m']
    pc = env['profundidade_construivel_m']
    h  = env['gabarito_m']

    if isinstance(forma, FormaTorreComBase):
        bs = forma.blocos(lc, pc, h, params_forma, pe=pe)
    else:
        bs = forma.blocos(lc, pc, h, params_forma)

    ap = sum(b['w'] * b['d'] for b in bs)
    n  = env['pavimentos_max']

    env2 = dict(env)
    env2['blocos']             = bs
    env2['nome_forma']         = forma.nome
    env2['area_pavimento_m2']  = ap
    env2['area_construida_m2'] = ap * n
    env2['ca_utilizado']       = (ap * n) / env['area_lote_m2'] if env['area_lote_m2'] > 0 else 0
    env2['to_utilizado']       = ap / env['area_lote_m2'] if env['area_lote_m2'] > 0 else 0
    return env2


def gerar_forma(doc, lote, legislacao, forma, params_forma=None, criar_niveis=True):
    env = calcular_envelope_forma(lote, legislacao, forma, params_forma)
    rec = env['recuos_m']
    ox_base = rec['lateral']
    oy_base = rec['fundo']

    elementos = []
    nome_base = forma.nome + u' - ' + lote.get('nome', '')

    with Transaction(doc, u'ViabilidadeBIM - ' + forma.nome) as t:
        t.Start()
        try:
            criar_limite_lote(doc, lote, legislacao)
        except Exception:
            pass
        for idx, b in enumerate(env['blocos']):
            solid = _criar_solido(
                b['w'], b['d'], b['h'],
                ox_m=ox_base + b['ox'],
                oy_m=oy_base + b['oy'],
                oz_m=b.get('oz', 0.0),
            )
            label = nome_base if len(env['blocos']) == 1 else u'{} [{}]'.format(nome_base, idx + 1)
            el = _inserir_directshape(doc, solid, label)
            elementos.append(el)
        t.Commit()

    if criar_niveis:
        criar_niveis_e_lajes(doc, env)

    return env, elementos


def gerar_todas_as_formas(doc, lote, legislacao, espacamento_m=10.0):
    from formas import FORMAS, FormaTorreComBase

    env_base   = calcular_envelope(lote, legislacao)
    rec        = env_base['recuos_m']
    lote_larg  = lote['largura_m']
    resultados = []

    for i, forma in enumerate(FORMAS):
        params_pad = {k: v['default'] for k, v in forma.params_schema.items()}

        pe = env_base['pe_direito_m']
        lc = env_base['largura_construivel_m']
        pc = env_base['profundidade_construivel_m']
        h  = env_base['gabarito_m']

        if isinstance(forma, FormaTorreComBase):
            bs = forma.blocos(lc, pc, h, params_pad, pe=pe)
        else:
            bs = forma.blocos(lc, pc, h, params_pad)

        ap  = sum(b['w'] * b['d'] for b in bs)
        n   = env_base['pavimentos_max']
        env = dict(env_base)
        env['blocos']             = bs
        env['nome_forma']         = forma.nome
        env['area_pavimento_m2']  = ap
        env['area_construida_m2'] = ap * n
        env['ca_utilizado']       = (ap * n) / env['area_lote_m2'] if env['area_lote_m2'] > 0 else 0
        env['to_utilizado']       = ap / env['area_lote_m2'] if env['area_lote_m2'] > 0 else 0

        offset_x = i * (lote_larg + espacamento_m)
        ox_base_i = rec['lateral'] + offset_x
        oy_base_i = rec['fundo']
        elementos = []

        with Transaction(doc, u'ViabilidadeBIM - ' + forma.nome) as t:
            t.Start()
            for idx, b in enumerate(bs):
                solid = _criar_solido(
                    b['w'], b['d'], b['h'],
                    ox_m=ox_base_i + b['ox'],
                    oy_m=oy_base_i + b['oy'],
                    oz_m=b.get('oz', 0.0),
                )
                label = u'{} [{}]'.format(forma.nome, idx + 1) if len(bs) > 1 else forma.nome
                el = _inserir_directshape(doc, solid, label)
                elementos.append(el)
            t.Commit()

        resultados.append((env, elementos))

    criar_niveis_e_lajes(doc, env_base)
    return resultados


def gerar_tipologias(doc, lote, legislacao):
    """Gera 4 tipologias volumetricas para comparacao."""
    env = calcular_envelope(lote, legislacao)
    rec = env['recuos_m']
    lc  = env['largura_construivel_m']
    pc  = env['profundidade_construivel_m']
    pe  = env['pe_direito_m']
    n   = env['pavimentos_max']
    h   = env['gabarito_m']

    tipologias = []

    with Transaction(doc, u'ViabilidadeBIM - Tipologias') as t:
        t.Start()

        ap1 = lc * pc
        e1  = _inserir_directshape(doc, _criar_solido(lc, pc, h, rec['lateral'], rec['fundo']),
                                   u'T1 - Envelope Completo')
        tipologias.append({'elemento': e1, 'nome': u'T1 Envelope Completo',
                           'area_pavimento_m2': ap1, 'pavimentos': n,
                           'area_construida_m2': ap1 * n})

        tw, tp = lc * 0.50, pc * 0.50
        ap2    = tw * tp
        e2 = _inserir_directshape(doc, _criar_solido(tw, tp, h,
                                  rec['lateral'] + lc * 0.25,
                                  rec['fundo']   + pc * 0.25), u'T2 - Torre Central')
        tipologias.append({'elemento': e2, 'nome': u'T2 Torre Central',
                           'area_pavimento_m2': ap2, 'pavimentos': n,
                           'area_construida_m2': ap2 * n})

        n3  = max(1, int(n * 0.70))
        ap3 = lc * pc * 0.40
        e3  = _inserir_directshape(doc, _criar_solido(lc, pc * 0.40, n3 * pe,
                                   rec['lateral'], rec['fundo']), u'T3 - Lamina')
        tipologias.append({'elemento': e3, 'nome': u'T3 Lamina Frontal',
                           'area_pavimento_m2': ap3, 'pavimentos': n3,
                           'area_construida_m2': ap3 * n3})

        n4  = max(1, int(n * 0.60))
        ew  = lc * 0.28
        ap4 = (ew * pc) * 2 + (lc - 2 * ew) * pc * 0.35
        _inserir_directshape(doc, _criar_solido(ew, pc, n4 * pe,
                             rec['lateral'], rec['fundo']), u'T4 - Forma U esq')
        _inserir_directshape(doc, _criar_solido(ew, pc, n4 * pe,
                             rec['lateral'] + lc - ew, rec['fundo']), u'T4 - Forma U dir')
        e4 = _inserir_directshape(doc, _criar_solido(lc - 2*ew, pc*0.35, n4*pe,
                                  rec['lateral'] + ew, rec['fundo'] + pc*0.65),
                                  u'T4 - Forma U fundo')
        tipologias.append({'elemento': e4, 'nome': u'T4 Forma em U',
                           'area_pavimento_m2': ap4, 'pavimentos': n4,
                           'area_construida_m2': ap4 * n4})

        t.Commit()

    criar_niveis_e_lajes(doc, env)
    return tipologias, env
