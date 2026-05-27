# -*- coding: utf-8 -*-
"""
Painel lateral dockable de Viabilidade BIM.
Criado uma unica vez no startup e atualizado pelos botoes.
Compativel com IronPython 2 (pyRevit).
"""
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('RevitAPIUI')

from System.Windows import Visibility
from System.Windows.Media import BrushConverter
from System.IO import MemoryStream
from System.Text import Encoding
from System.Windows.Markup import XamlReader
from Autodesk.Revit.UI import DockablePaneId
from System import Guid

import config as cfg
import massas
import financeiro as fin

# ── ID compartilhado entre startup e botoes ───────────────────────────────────
PANE_GUID = '7A9B2C3D-4E5F-6789-ABCD-EF0123456789'
PANE_ID   = DockablePaneId(Guid(PANE_GUID))

_elemento = None   # FrameworkElement do painel (singleton)


# ── XAML do painel ────────────────────────────────────────────────────────────
XAML = u"""
<ScrollViewer
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    VerticalScrollBarVisibility="Auto"
    Background="#F5F7FA"
    FontFamily="Segoe UI">

  <StackPanel Margin="10,12,10,20">

    <!-- Cabecalho -->
    <TextBlock Text="VIABILIDADE BIM" FontSize="13" FontWeight="Bold"
               Foreground="#1A5276" Margin="0,0,0,10"/>

    <!-- Info do lote ativo -->
    <Border Background="#EAF4FB" CornerRadius="3" Padding="8,7" Margin="0,0,0,10">
      <TextBlock x:Name="txt_lote_info" TextWrapping="Wrap" FontSize="11"
                 Foreground="#1A5276" LineHeight="17"
                 Text="Configure o lote para comecar."/>
    </Border>

    <!-- RECEITA -->
    <TextBlock Text="RECEITA" FontSize="10" FontWeight="Bold"
               Foreground="#888" Margin="0,4,0,5"/>

    <Grid Margin="0,0,0,4">
      <Grid.ColumnDefinitions>
        <ColumnDefinition Width="*"/>
        <ColumnDefinition Width="90"/>
      </Grid.ColumnDefinitions>
      <TextBlock Grid.Column="0" Text="Preco venda (R$/m2)" VerticalAlignment="Center" FontSize="12"/>
      <TextBox   Grid.Column="1" x:Name="inp_preco" Text="8000" Padding="4,3" FontSize="12"/>
    </Grid>

    <!-- CUSTO -->
    <TextBlock Text="CUSTO" FontSize="10" FontWeight="Bold"
               Foreground="#888" Margin="0,8,0,5"/>

    <Grid Margin="0,0,0,4">
      <Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="90"/></Grid.ColumnDefinitions>
      <TextBlock Grid.Column="0" Text="Custo obra (R$/m2)" VerticalAlignment="Center" FontSize="12"/>
      <TextBox   Grid.Column="1" x:Name="inp_custo" Text="3500" Padding="4,3" FontSize="12"/>
    </Grid>

    <Grid Margin="0,0,0,4">
      <Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="90"/></Grid.ColumnDefinitions>
      <TextBlock Grid.Column="0" Text="Custo terreno (R$)" VerticalAlignment="Center" FontSize="12"/>
      <TextBox   Grid.Column="1" x:Name="inp_terreno" Text="0" Padding="4,3" FontSize="12"/>
    </Grid>

    <Grid Margin="0,0,0,4">
      <Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="90"/></Grid.ColumnDefinitions>
      <TextBlock Grid.Column="0" Text="Outras desp. (%VGV)" VerticalAlignment="Center" FontSize="12"/>
      <TextBox   Grid.Column="1" x:Name="inp_outras" Text="0.15" Padding="4,3" FontSize="12"/>
    </Grid>

    <!-- PROJETO -->
    <TextBlock Text="PROJETO" FontSize="10" FontWeight="Bold"
               Foreground="#888" Margin="0,8,0,5"/>

    <Grid Margin="0,0,0,4">
      <Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="90"/></Grid.ColumnDefinitions>
      <TextBlock Grid.Column="0" Text="Eficiencia planta" VerticalAlignment="Center" FontSize="12"/>
      <TextBox   Grid.Column="1" x:Name="inp_efic" Text="0.82" Padding="4,3" FontSize="12"/>
    </Grid>

    <Grid Margin="0,0,0,4">
      <Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="90"/></Grid.ColumnDefinitions>
      <TextBlock Grid.Column="0" Text="Pavimentos (vazio=max)" VerticalAlignment="Center" FontSize="12"/>
      <TextBox   Grid.Column="1" x:Name="inp_pav" Text="" Padding="4,3" FontSize="12"/>
    </Grid>

    <!-- Botao calcular -->
    <Button x:Name="btn_calcular" Content="CALCULAR"
            Padding="0,9" Margin="0,12,0,4"
            Background="#1A5276" Foreground="White"
            FontWeight="Bold" FontSize="12" Cursor="Hand"/>

    <Button x:Name="btn_atualizar" Content="Recarregar lote/legislacao"
            Padding="0,5" Margin="0,0,0,12"
            Background="#ECF0F1" Foreground="#555"
            FontSize="11" Cursor="Hand"/>

    <!-- Separador -->
    <Rectangle Height="1" Fill="#DDE" Margin="0,0,0,10"/>

    <!-- RESULTADOS -->
    <StackPanel x:Name="pnl_resultados" Visibility="Collapsed">

      <TextBlock Text="AREAS" FontSize="10" FontWeight="Bold"
                 Foreground="#888" Margin="0,0,0,6"/>

      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Area construida" FontSize="12"/>
        <TextBlock Grid.Column="1" x:Name="res_ac" FontSize="12" FontWeight="Bold" Foreground="#1A5276"/>
      </Grid>
      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Eficiencia" FontSize="12"/>
        <TextBlock Grid.Column="1" x:Name="res_ef" FontSize="12" Foreground="#444"/>
      </Grid>
      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Area privativa" FontSize="12"/>
        <TextBlock Grid.Column="1" x:Name="res_ap" FontSize="12" FontWeight="Bold" Foreground="#1A5276"/>
      </Grid>

      <TextBlock Text="FINANCEIRO" FontSize="10" FontWeight="Bold"
                 Foreground="#888" Margin="0,10,0,6"/>

      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="VGV" FontSize="12"/>
        <TextBlock Grid.Column="1" x:Name="res_vgv" FontSize="12" FontWeight="Bold" Foreground="#1A7A3F"/>
      </Grid>
      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Custo total" FontSize="12"/>
        <TextBlock Grid.Column="1" x:Name="res_ct"  FontSize="12" Foreground="#444"/>
      </Grid>
      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Lucro bruto" FontSize="12"/>
        <TextBlock Grid.Column="1" x:Name="res_lb"  FontSize="12" FontWeight="Bold"/>
      </Grid>

      <TextBlock Text="INDICADORES" FontSize="10" FontWeight="Bold"
                 Foreground="#888" Margin="0,10,0,6"/>

      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Margem" FontSize="15" FontWeight="SemiBold"/>
        <TextBlock Grid.Column="1" x:Name="res_mg"  FontSize="15" FontWeight="Bold"/>
      </Grid>
      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="ROI" FontSize="15" FontWeight="SemiBold"/>
        <TextBlock Grid.Column="1" x:Name="res_roi" FontSize="15" FontWeight="Bold"/>
      </Grid>
      <Grid Margin="0,2"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Custo/m2 priv." FontSize="11" Foreground="#666"/>
        <TextBlock Grid.Column="1" x:Name="res_cm2" FontSize="11" Foreground="#666"/>
      </Grid>

    </StackPanel>

  </StackPanel>
</ScrollViewer>
"""


# ── Ciclo de vida ─────────────────────────────────────────────────────────────

def inicializar():
    global _elemento
    if _elemento is not None:
        return
    encoded  = Encoding.UTF8.GetBytes(XAML)
    _elemento = XamlReader.Load(MemoryStream(encoded))
    _conectar_eventos()
    atualizar_lote()


def get_elemento():
    inicializar()
    return _elemento


def _f(nome):
    return _elemento.FindName(nome) if _elemento else None


def _conectar_eventos():
    btn = _f('btn_calcular')
    if btn:
        btn.Click += _ao_calcular
    btn2 = _f('btn_atualizar')
    if btn2:
        btn2.Click += lambda s, e: atualizar_lote()


# ── Atualizacao de dados ──────────────────────────────────────────────────────

def atualizar_lote():
    """Recarrega lote e legislacao ativa e exibe no cabecalho do painel."""
    info = _f('txt_lote_info')
    if not info:
        return

    lote = cfg.carregar_lote()
    if not lote:
        info.Text = u'Nenhum lote configurado.\nUse "Configurar Lote".'
        return

    leg = None
    try:
        leg = cfg.carregar_legislacao_ativa()
    except Exception:
        pass

    if not leg:
        info.Text = u'{} — {}m x {}m\nLegislacao nao definida.'.format(
            lote['nome'], lote['largura_m'], lote['profundidade_m'])
        return

    env = massas.calcular_envelope(lote, leg)
    info.Text = (
        u'{nome} — {l}m x {p}m  ({al:.0f} m2)\n'
        u'Leg.: {leg}\n'
        u'Area max: {ac:.0f} m2  |  {pav} pav.  |  {gab:.0f} m'
    ).format(
        nome=lote['nome'], l=lote['largura_m'], p=lote['profundidade_m'],
        al=env['area_lote_m2'], leg=leg['nome'],
        ac=env['area_construida_m2'], pav=env['pavimentos_max'],
        gab=env['gabarito_m'],
    )


# ── Calculo ───────────────────────────────────────────────────────────────────

def _num(nome, pad=0.0):
    el = _f(nome)
    if not el:
        return pad
    try:
        return float(el.Text) if el.Text.strip() else pad
    except Exception:
        return pad


def _inteiro(nome):
    el = _f(nome)
    if not el:
        return None
    try:
        return int(float(el.Text)) if el.Text.strip() else None
    except Exception:
        return None


def _ao_calcular(sender, args):
    lote = cfg.carregar_lote()
    leg  = None
    try:
        leg = cfg.carregar_legislacao_ativa()
    except Exception:
        pass

    info = _f('txt_lote_info')
    if not lote or not leg:
        if info:
            info.Text = u'Configure o lote e a legislacao antes de calcular.'
        return

    env = massas.calcular_envelope(lote, leg)
    params = {
        'preco_venda_m2':        _num('inp_preco',   8000),
        'custo_construcao_m2':   _num('inp_custo',   3500),
        'custo_terreno':         _num('inp_terreno',    0),
        'outras_despesas_pct':   _num('inp_outras',  0.15),
        'eficiencia_planta':     _num('inp_efic',    0.82),
        'n_pavimentos_override': _inteiro('inp_pav'),
    }

    r = fin.calcular(env, params)
    _exibir_resultados(r)


def _cor(hex_str):
    return BrushConverter().ConvertFromString(hex_str)


def _exibir_resultados(r):
    def _set(nome, texto):
        el = _f(nome)
        if el:
            el.Text = texto

    _set('res_ac',  u'{:.0f} m2'.format(r['area_construida_m2']))
    _set('res_ef',  u'{:.1f}%'.format(r['eficiencia_pct']))
    _set('res_ap',  u'{:.0f} m2'.format(r['area_privativa_m2']))
    _set('res_vgv', fin.fmt_reais(r['vgv']))
    _set('res_ct',  fin.fmt_reais(r['custo_total']))
    _set('res_lb',  fin.fmt_reais(r['lucro_bruto']))
    _set('res_mg',  u'{:.1f}%'.format(r['margem_pct']))
    _set('res_roi', u'{:.1f}%'.format(r['roi_pct']))
    _set('res_cm2', fin.fmt_reais(r['custo_m2_privativo']) + u'/m2')

    # Cor do lucro/margem/ROI
    cor_ok  = _cor('#1A7A3F')
    cor_neg = _cor('#C0392B')
    positivo = r['lucro_bruto'] >= 0

    for nome in ('res_lb', 'res_mg', 'res_roi'):
        el = _f(nome)
        if el:
            el.Foreground = cor_ok if positivo else cor_neg

    pnl = _f('pnl_resultados')
    if pnl:
        pnl.Visibility = Visibility.Visible
