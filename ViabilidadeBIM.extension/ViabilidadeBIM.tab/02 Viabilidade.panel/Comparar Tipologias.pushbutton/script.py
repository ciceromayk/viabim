# -*- coding: utf-8 -*-
"""
Botão: Comparar Tipologias — gera 4 tipologias volumétricas no modelo
e exibe tabela comparativa de viabilidade financeira.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
import config as cfg
import massas
import financeiro as fin

import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')

from ui import xaml_load

XAML_PARAMS = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Comparar Tipologias — Parâmetros" Height="420" Width="480"
    ResizeMode="NoResize" WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">
  <Grid Margin="24">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <TextBlock Grid.Row="0" Text="Parâmetros financeiros" FontSize="18"
               FontWeight="Bold" Foreground="#1A5276" Margin="0,0,0,16"/>

    <StackPanel Grid.Row="1">
      <StackPanel Orientation="Horizontal" Margin="0,0,0,8">
        <Label Content="Preço venda (R$/m² priv.)" Width="220" VerticalAlignment="Center"/>
        <TextBox x:Name="txt_preco" Width="160" Padding="5,4" Text="8000"/>
      </StackPanel>
      <StackPanel Orientation="Horizontal" Margin="0,0,0,8">
        <Label Content="Custo construção (R$/m²)" Width="220" VerticalAlignment="Center"/>
        <TextBox x:Name="txt_custo" Width="160" Padding="5,4" Text="3500"/>
      </StackPanel>
      <StackPanel Orientation="Horizontal" Margin="0,0,0,8">
        <Label Content="Custo do terreno (R$)" Width="220" VerticalAlignment="Center"/>
        <TextBox x:Name="txt_terreno" Width="160" Padding="5,4" Text="0"/>
      </StackPanel>
      <StackPanel Orientation="Horizontal" Margin="0,0,0,8">
        <Label Content="Outras despesas (% do VGV)" Width="220" VerticalAlignment="Center"/>
        <TextBox x:Name="txt_outras" Width="160" Padding="5,4" Text="0.15"/>
      </StackPanel>
      <StackPanel Orientation="Horizontal" Margin="0,0,0,8">
        <Label Content="Eficiência de planta (0–1)" Width="220" VerticalAlignment="Center"/>
        <TextBox x:Name="txt_efic" Width="160" Padding="5,4" Text="0.82"/>
      </StackPanel>
    </StackPanel>

    <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right">
      <Button x:Name="btn_gerar" Content="Gerar tipologias no modelo"
              Padding="16,8" Background="#1A5276" Foreground="White" Margin="0,0,8,0"/>
      <Button x:Name="btn_cancelar" Content="Cancelar" Padding="16,8"/>
    </StackPanel>
  </Grid>
</Window>
"""

XAML_RESULTADO = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Comparativo de Tipologias" Height="580" Width="860"
    ResizeMode="CanResizeWithGrip" WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">
  <Grid Margin="24">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <TextBlock Grid.Row="0" Text="Comparativo de Tipologias" FontSize="18"
               FontWeight="Bold" Foreground="#1A5276" Margin="0,0,0,16"/>

    <DataGrid Grid.Row="1" x:Name="grid_comp" AutoGenerateColumns="False"
              IsReadOnly="True" CanUserSortColumns="True"
              AlternatingRowBackground="#F4F8FC" GridLinesVisibility="Horizontal"
              HeadersVisibility="Column" RowHeight="36">
      <DataGrid.Columns>
        <DataGridTextColumn Header="Tipologia"         Binding="{Binding nome}"            Width="170"/>
        <DataGridTextColumn Header="Pavs."             Binding="{Binding pavimentos}"       Width="60"/>
        <DataGridTextColumn Header="Área Priv. (m²)"   Binding="{Binding area_priv}"        Width="110"/>
        <DataGridTextColumn Header="VGV"               Binding="{Binding vgv}"              Width="120"/>
        <DataGridTextColumn Header="Custo Total"       Binding="{Binding custo_total}"      Width="120"/>
        <DataGridTextColumn Header="Lucro"             Binding="{Binding lucro}"            Width="110"/>
        <DataGridTextColumn Header="Margem"            Binding="{Binding margem}"           Width="75"/>
        <DataGridTextColumn Header="ROI"               Binding="{Binding roi}"              Width="75"/>
      </DataGrid.Columns>
    </DataGrid>

    <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,16,0,0">
      <Button x:Name="btn_fechar" Content="Fechar" Padding="20,8"/>
    </StackPanel>
  </Grid>
</Window>
"""


def _num(win, nome, pad=0.0):
    el = win.FindName(nome)
    try:
        return float(el.Text) if el.Text.strip() else pad
    except (ValueError, AttributeError):
        return pad


def _mostrar_comparativo(resultados):
    win = xaml_load(XAML_RESULTADO)
    grid = win.FindName('grid_comp')

    from System.Collections.ObjectModel import ObservableCollection
    from System.Dynamic import ExpandoObject

    items = ObservableCollection[object]()
    for r in resultados:
        row = ExpandoObject()
        d   = dict(row)
        d['nome']       = r['nome']
        d['pavimentos'] = str(r['n_pavimentos'])
        d['area_priv']  = u'{:.0f} m²'.format(r['area_privativa_m2'])
        d['vgv']        = fin.fmt_reais(r['vgv'])
        d['custo_total']= fin.fmt_reais(r['custo_total'])
        d['lucro']      = fin.fmt_reais(r['lucro_bruto'])
        d['margem']     = u'{:.1f}%'.format(r['margem_pct'])
        d['roi']        = u'{:.1f}%'.format(r['roi_pct'])
        # ExpandoObject populado via IDictionary
        from System.Collections.Generic import KeyValuePair
        exp = ExpandoObject()
        exp_dict = exp
        for k, v in d.items():
            exp_dict[k] = v
        items.Add(exp)

    grid.ItemsSource = items
    win.FindName('btn_fechar').Click += lambda s, e: win.Close()
    win.ShowDialog()


# ── Entry point ───────────────────────────────────────────────────────────────

from pyrevit import revit, forms

doc = revit.doc

lote = cfg.carregar_lote()
if not lote:
    forms.alert('Configure o lote primeiro (botão "Configurar Lote").', exitscript=True)

leg = None
try:
    leg = cfg.carregar_legislacao_ativa()
except Exception:
    pass

if not leg:
    legs = cfg.listar_legislacoes()
    if not legs:
        forms.alert('Cadastre ao menos uma configuração de legislação.', exitscript=True)
    escolha = forms.SelectFromList.show(
        [l['nome'] for l in legs], title='Selecionar Legislação', button_name='Usar')
    if not escolha:
        import sys; sys.exit()
    leg = legs[[l['nome'] for l in legs].index(escolha)]

env = massas.calcular_envelope(lote, leg)

# Janela de parâmetros
win_p = xaml_load(XAML_PARAMS)
confirmado = [False]

def _gerar(s, e):
    confirmado[0] = True
    win_p.Close()

win_p.FindName('btn_gerar').Click    += _gerar
win_p.FindName('btn_cancelar').Click += lambda s, e: win_p.Close()
win_p.ShowDialog()

if not confirmado[0]:
    import sys; sys.exit()

params = {
    'preco_venda_m2':      _num(win_p, 'txt_preco',   8000),
    'custo_construcao_m2': _num(win_p, 'txt_custo',   3500),
    'custo_terreno':       _num(win_p, 'txt_terreno',  0),
    'outras_despesas_pct': _num(win_p, 'txt_outras',   0.15),
    'eficiencia_planta':   _num(win_p, 'txt_efic',     0.82),
}

tipologias, env = massas.gerar_tipologias(doc, lote, leg)
resultados      = fin.calcular_tipologias(tipologias, env, params)

_mostrar_comparativo(resultados)
