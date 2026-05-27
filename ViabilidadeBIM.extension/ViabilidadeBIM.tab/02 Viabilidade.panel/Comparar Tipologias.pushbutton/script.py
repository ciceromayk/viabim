# -*- coding: utf-8 -*-
"""
Botao: Comparar Tipologias — gera todas as formas no modelo e exibe
ranking financeiro comparativo.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
import config as cfg
import massas
import formas as frm
import financeiro as fin

import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System.Data')

from System.Data import DataTable
from ui import xaml_load
from pyrevit import revit, forms as pvforms

doc = revit.doc

# ── Dados ─────────────────────────────────────────────────────────────────────

cfg.instalar_exemplos()

lote = cfg.carregar_lote()
if not lote:
    pvforms.alert(u'Configure o lote primeiro (botao "Configurar Lote").', exitscript=True)

leg = None
try:
    leg = cfg.carregar_legislacao_ativa()
except Exception:
    pass

if not leg:
    legs = cfg.listar_legislacoes()
    if not legs:
        pvforms.alert(u'Cadastre ao menos uma configuracao de legislacao.', exitscript=True)
    escolha = pvforms.SelectFromList.show(
        [l['nome'] for l in legs], title=u'Selecionar Legislacao', button_name=u'Usar')
    if not escolha:
        sys.exit()
    leg = legs[[l['nome'] for l in legs].index(escolha)]

# ── XAML de parametros ────────────────────────────────────────────────────────

XAML_PARAMS = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Comparar Tipologias — Parametros"
    Height="460" Width="500"
    ResizeMode="NoResize" WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">
  <Grid Margin="24">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <TextBlock Grid.Row="0" Text="Parametros financeiros"
               FontSize="17" FontWeight="Bold" Foreground="#1A5276" Margin="0,0,0,6"/>
    <TextBlock Grid.Row="1" TextWrapping="Wrap" Foreground="#555" FontSize="12"
               Margin="0,0,0,16"
               Text="Serao geradas todas as {n} tipologias no modelo, deslocadas lado a lado. A tabela exibira o ranking por ROI."/>

    <StackPanel Grid.Row="2">
      <Grid Margin="0,0,0,8">
        <Grid.ColumnDefinitions><ColumnDefinition Width="220"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
        <Label Grid.Column="0" Content="Preco venda (R$/m2 privativo)" VerticalAlignment="Center"/>
        <TextBox Grid.Column="1" x:Name="txt_preco" Padding="5,4" Text="8000"/>
      </Grid>
      <Grid Margin="0,0,0,8">
        <Grid.ColumnDefinitions><ColumnDefinition Width="220"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
        <Label Grid.Column="0" Content="Custo construcao (R$/m2)" VerticalAlignment="Center"/>
        <TextBox Grid.Column="1" x:Name="txt_custo" Padding="5,4" Text="3500"/>
      </Grid>
      <Grid Margin="0,0,0,8">
        <Grid.ColumnDefinitions><ColumnDefinition Width="220"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
        <Label Grid.Column="0" Content="Custo do terreno (R$)" VerticalAlignment="Center"/>
        <TextBox Grid.Column="1" x:Name="txt_terreno" Padding="5,4" Text="0"/>
      </Grid>
      <Grid Margin="0,0,0,8">
        <Grid.ColumnDefinitions><ColumnDefinition Width="220"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
        <Label Grid.Column="0" Content="Outras despesas (% do VGV)" VerticalAlignment="Center"/>
        <TextBox Grid.Column="1" x:Name="txt_outras" Padding="5,4" Text="0.15"/>
      </Grid>
      <Grid Margin="0,0,0,8">
        <Grid.ColumnDefinitions><ColumnDefinition Width="220"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
        <Label Grid.Column="0" Content="Eficiencia de planta (0-1)" VerticalAlignment="Center"/>
        <TextBox Grid.Column="1" x:Name="txt_efic" Padding="5,4" Text="0.82"/>
      </Grid>
      <Grid Margin="0,0,0,8">
        <Grid.ColumnDefinitions><ColumnDefinition Width="220"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
        <Label Grid.Column="0" Content="Espacamento entre formas (m)" VerticalAlignment="Center"/>
        <TextBox Grid.Column="1" x:Name="txt_gap" Padding="5,4" Text="10"/>
      </Grid>
    </StackPanel>

    <StackPanel Grid.Row="3" Orientation="Horizontal" HorizontalAlignment="Right">
      <Button x:Name="btn_gerar" Content="Gerar e Comparar"
              Padding="18,8" Background="#1A5276" Foreground="White"
              FontWeight="Bold" Margin="0,0,8,0" Cursor="Hand"/>
      <Button x:Name="btn_cancelar" Content="Cancelar" Padding="18,8" Cursor="Hand"/>
    </StackPanel>
  </Grid>
</Window>
"""

# ── XAML de resultado ─────────────────────────────────────────────────────────

XAML_RESULTADO = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Ranking de Tipologias — Viabilidade"
    Height="560" Width="940"
    ResizeMode="CanResizeWithGrip" WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">
  <Grid Margin="20">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <TextBlock Grid.Row="0" Text="Ranking de Tipologias"
               FontSize="17" FontWeight="Bold" Foreground="#1A5276" Margin="0,0,0,4"/>
    <TextBlock Grid.Row="1" x:Name="txt_subtitulo" Foreground="#666" FontSize="11"
               Margin="0,0,0,12"/>

    <DataGrid Grid.Row="2" x:Name="grid_rank"
              AutoGenerateColumns="False" IsReadOnly="True"
              CanUserSortColumns="True"
              AlternatingRowBackground="#F4F8FC"
              GridLinesVisibility="Horizontal"
              HeadersVisibility="Column"
              RowHeight="34">
      <DataGrid.Columns>
        <DataGridTextColumn Header="#"              Binding="{Binding [Rank]}"      Width="36"/>
        <DataGridTextColumn Header="Tipologia"      Binding="{Binding [Forma]}"     Width="160"/>
        <DataGridTextColumn Header="Area Priv.(m2)" Binding="{Binding [AreaPriv]}"  Width="105"/>
        <DataGridTextColumn Header="VGV"            Binding="{Binding [VGV]}"       Width="115"/>
        <DataGridTextColumn Header="Custo Total"    Binding="{Binding [Custo]}"     Width="115"/>
        <DataGridTextColumn Header="Lucro"          Binding="{Binding [Lucro]}"     Width="110"/>
        <DataGridTextColumn Header="Margem"         Binding="{Binding [Margem]}"    Width="75"/>
        <DataGridTextColumn Header="ROI"            Binding="{Binding [ROI]}"       Width="75"/>
      </DataGrid.Columns>
    </DataGrid>

    <StackPanel Grid.Row="3" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,14,0,0">
      <Button x:Name="btn_fechar" Content="Fechar" Padding="22,8" Cursor="Hand"/>
    </StackPanel>
  </Grid>
</Window>
"""


def _num(win, nome, pad=0.0):
    el = win.FindName(nome)
    try:
        return float(el.Text) if el and el.Text.strip() else pad
    except (ValueError, AttributeError):
        return pad


def _montar_tabela(resultados_financeiros):
    """Cria DataTable com resultados, ordenado por ROI decrescente."""
    ordenados = sorted(resultados_financeiros, key=lambda r: r['roi_pct'], reverse=True)

    dt = DataTable()
    for col in ('Rank', 'Forma', 'AreaPriv', 'VGV', 'Custo', 'Lucro', 'Margem', 'ROI'):
        dt.Columns.Add(col)

    for i, r in enumerate(ordenados):
        row = dt.NewRow()
        row['Rank']     = str(i + 1)
        row['Forma']    = r['nome_forma']
        row['AreaPriv'] = u'{:.0f} m\xb2'.format(r['area_privativa_m2'])
        row['VGV']      = fin.fmt_reais(r['vgv'])
        row['Custo']    = fin.fmt_reais(r['custo_total'])
        row['Lucro']    = fin.fmt_reais(r['lucro_bruto'])
        row['Margem']   = u'{:.1f}%'.format(r['margem_pct'])
        row['ROI']      = u'{:.1f}%'.format(r['roi_pct'])
        dt.Rows.Add(row)

    return dt, ordenados


def _exibir_ranking(resultados_financeiros, lote, leg):
    win  = xaml_load(XAML_RESULTADO)
    grid = win.FindName('grid_rank')
    sub  = win.FindName('txt_subtitulo')

    if sub:
        sub.Text = u'Lote: {}  |  Legislacao: {}  |  {} tipologias comparadas'.format(
            lote['nome'], leg['nome'], len(resultados_financeiros))

    dt, _ = _montar_tabela(resultados_financeiros)
    grid.ItemsSource = dt.DefaultView

    win.FindName('btn_fechar').Click += lambda s, e: win.Close()
    win.ShowDialog()


# ── Entry point ───────────────────────────────────────────────────────────────

win_p = xaml_load(XAML_PARAMS.replace('{n}', str(len(frm.FORMAS))))
confirmado = [False]

def _ao_gerar(s, e):
    confirmado[0] = True
    win_p.Close()

win_p.FindName('btn_gerar').Click    += _ao_gerar
win_p.FindName('btn_cancelar').Click += lambda s, e: win_p.Close()
win_p.ShowDialog()

if not confirmado[0]:
    sys.exit()

params_fin = {
    'preco_venda_m2':      _num(win_p, 'txt_preco',   8000),
    'custo_construcao_m2': _num(win_p, 'txt_custo',   3500),
    'custo_terreno':       _num(win_p, 'txt_terreno',  0),
    'outras_despesas_pct': _num(win_p, 'txt_outras',   0.15),
    'eficiencia_planta':   _num(win_p, 'txt_efic',     0.82),
}
espacamento = max(5.0, _num(win_p, 'txt_gap', 10.0))

# Gerar todas as formas no modelo
resultados_geo = massas.gerar_todas_as_formas(doc, lote, leg, espacamento_m=espacamento)

# Calcular financeiro de cada forma
resultados_fin = []
for env_forma, _ in resultados_geo:
    r = fin.calcular(env_forma, params_fin)
    r['nome_forma'] = env_forma['nome_forma']
    resultados_fin.append(r)

_exibir_ranking(resultados_fin, lote, leg)
