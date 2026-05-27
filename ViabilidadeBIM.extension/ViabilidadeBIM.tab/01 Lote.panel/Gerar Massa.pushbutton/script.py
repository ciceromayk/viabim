# -*- coding: utf-8 -*-
"""
Botao: Gerar Massa — seleciona forma volumetrica e gera DirectShapes no Revit.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
import config as cfg
import massas
import formas as frm

import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')

from System.Windows import Thickness, VerticalAlignment
from System.Windows.Controls import (
    Label, TextBox, TextBlock, StackPanel, Grid, ColumnDefinition,
)
from System.Windows.Controls import GridLength, GridUnitType
from System.Windows.Media import BrushConverter
from ui import xaml_load
from pyrevit import revit, forms as pvforms

doc = revit.doc

# ── Carregar dados ────────────────────────────────────────────────────────────

cfg.instalar_exemplos()

lote = cfg.carregar_lote()
if not lote:
    pvforms.alert(u'Configure o lote antes de gerar a massa.\n(Botao "Configurar Lote")',
                  exitscript=True)

leg = None
try:
    leg = cfg.carregar_legislacao_ativa()
except Exception:
    pass

if not leg:
    legs = cfg.listar_legislacoes()
    if not legs:
        pvforms.alert(u'Nenhuma legislacao cadastrada.\nUse "Gerenciar Legislacao".',
                      exitscript=True)
    escolha = pvforms.SelectFromList.show(
        [l['nome'] for l in legs], title=u'Selecionar Legislacao', button_name=u'Usar')
    if not escolha:
        sys.exit()
    leg = legs[[l['nome'] for l in legs].index(escolha)]
    cfg.definir_legislacao_ativa(leg['id'])

# ── XAML ─────────────────────────────────────────────────────────────────────

XAML = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Gerar Massa Volumetrica" Height="600" Width="540"
    ResizeMode="NoResize" WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">
  <Grid Margin="22">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <TextBlock Grid.Row="0" Text="Gerar Massa Volumetrica"
               FontSize="18" FontWeight="Bold" Foreground="#1A5276" Margin="0,0,0,16"/>

    <Grid Grid.Row="1" Margin="0,0,0,6">
      <Grid.ColumnDefinitions>
        <ColumnDefinition Width="130"/>
        <ColumnDefinition Width="*"/>
      </Grid.ColumnDefinitions>
      <Label Grid.Column="0" Content="Tipologia:" VerticalAlignment="Center"/>
      <ComboBox Grid.Column="1" x:Name="cmb_forma"/>
    </Grid>

    <Border Grid.Row="2" Background="#EAF4FB" CornerRadius="3" Padding="8,6" Margin="0,0,0,14">
      <TextBlock x:Name="txt_desc" TextWrapping="Wrap" FontSize="11"
                 Foreground="#1A5276" Text="Selecione uma tipologia."/>
    </Border>

    <TextBlock Grid.Row="3" Text="PARAMETROS" FontSize="10" FontWeight="Bold"
               Foreground="#888" Margin="0,0,0,6"/>

    <ScrollViewer Grid.Row="4" VerticalScrollBarVisibility="Auto" MaxHeight="155">
      <StackPanel x:Name="pnl_params"/>
    </ScrollViewer>

    <Border Grid.Row="6" Background="#F4F8FC" BorderBrush="#C8D8E8"
            BorderThickness="1" CornerRadius="4" Padding="14,10" Margin="0,10,0,16">
      <Grid>
        <Grid.ColumnDefinitions>
          <ColumnDefinition Width="*"/>
          <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        <StackPanel Grid.Column="0">
          <TextBlock Text="Area pavimento" FontSize="11" Foreground="#666"/>
          <TextBlock x:Name="res_ap"  FontSize="17" FontWeight="Bold" Foreground="#1A5276"/>
          <TextBlock Text="Area construida" FontSize="11" Foreground="#666" Margin="0,8,0,0"/>
          <TextBlock x:Name="res_ac"  FontSize="17" FontWeight="Bold" Foreground="#1A5276"/>
        </StackPanel>
        <StackPanel Grid.Column="1">
          <TextBlock Text="Pavimentos" FontSize="11" Foreground="#666"/>
          <TextBlock x:Name="res_pav" FontSize="17" FontWeight="Bold" Foreground="#1A5276"/>
          <TextBlock Text="CA utilizado" FontSize="11" Foreground="#666" Margin="0,8,0,0"/>
          <TextBlock x:Name="res_ca"  FontSize="17" FontWeight="Bold" Foreground="#1A5276"/>
        </StackPanel>
      </Grid>
    </Border>

    <StackPanel Grid.Row="7" Orientation="Horizontal" HorizontalAlignment="Right">
      <Button x:Name="btn_gerar" Content="Gerar no Revit"
              Padding="22,9" Background="#1A5276" Foreground="White"
              FontWeight="Bold" Margin="0,0,8,0" Cursor="Hand"/>
      <Button x:Name="btn_cancelar" Content="Cancelar" Padding="22,9" Cursor="Hand"/>
    </StackPanel>
  </Grid>
</Window>
"""


class JanelaGerarMassa(object):
    def __init__(self):
        self.win          = xaml_load(XAML)
        self.cmb_forma    = self.win.FindName('cmb_forma')
        self.txt_desc     = self.win.FindName('txt_desc')
        self.pnl_params   = self.win.FindName('pnl_params')
        self._inp_fields  = {}
        self._forma_atual = None

        for f in frm.FORMAS:
            self.cmb_forma.Items.Add(f.nome)
        self.cmb_forma.SelectionChanged += self._ao_selecionar
        self.cmb_forma.SelectedIndex = 0

        self.win.FindName('btn_gerar').Click    += self._ao_gerar
        self.win.FindName('btn_cancelar').Click += lambda s, e: self.win.Close()

    def _ao_selecionar(self, s, e):
        idx = self.cmb_forma.SelectedIndex
        if idx < 0:
            return
        forma = frm.FORMAS[idx]
        self._forma_atual = forma
        self.txt_desc.Text = forma.descricao
        self._rebuild_params(forma)
        self._atualizar_preview()

    def _rebuild_params(self, forma):
        self.pnl_params.Children.Clear()
        self._inp_fields = {}

        if not forma.params_schema:
            tb = TextBlock()
            tb.Text = u'Sem parametros ajustaveis para esta forma.'
            tb.Foreground = BrushConverter().ConvertFromString('#888')
            tb.FontSize = 11
            self.pnl_params.Children.Add(tb)
            return

        for key, schema in forma.params_schema.items():
            row = Grid()
            c1 = ColumnDefinition()
            c1.Width = GridLength(220)
            c2 = ColumnDefinition()
            c2.Width = GridLength(1, GridUnitType.Star)
            row.ColumnDefinitions.Add(c1)
            row.ColumnDefinitions.Add(c2)
            row.Margin = Thickness(0, 0, 0, 6)

            lbl = Label()
            lbl.Content = schema['label']
            lbl.VerticalAlignment = VerticalAlignment.Center
            Grid.SetColumn(lbl, 0)

            tb = TextBox()
            tb.Text = str(schema['default'])
            tb.Padding = Thickness(5, 3, 5, 3)
            tb.TextChanged += self._ao_mudar_param
            Grid.SetColumn(tb, 1)
            self._inp_fields[key] = tb

            row.Children.Add(lbl)
            row.Children.Add(tb)
            self.pnl_params.Children.Add(row)

    def _ao_mudar_param(self, s, e):
        self._atualizar_preview()

    def _params_atuais(self):
        result = {}
        if not self._forma_atual:
            return result
        for key, schema in self._forma_atual.params_schema.items():
            tb = self._inp_fields.get(key)
            try:
                result[key] = float(tb.Text) if tb and tb.Text.strip() else schema['default']
            except (ValueError, TypeError):
                result[key] = schema['default']
        return result

    def _atualizar_preview(self):
        if not self._forma_atual:
            return
        try:
            env = massas.calcular_envelope_forma(lote, leg, self._forma_atual,
                                                 self._params_atuais())
            def _s(nome, txt):
                el = self.win.FindName(nome)
                if el:
                    el.Text = txt
            _s('res_ap',  u'{:.0f} m\xb2'.format(env['area_pavimento_m2']))
            _s('res_ac',  u'{:.0f} m\xb2'.format(env['area_construida_m2']))
            _s('res_pav', str(env['pavimentos_max']))
            _s('res_ca',  u'{:.2f}'.format(env['ca_utilizado']))
        except Exception:
            pass

    def _ao_gerar(self, s, e):
        if not self._forma_atual:
            return
        params = self._params_atuais()

        erros = massas.validar_lote(lote, leg)
        if erros:
            from System.Windows import MessageBox
            MessageBox.Show(u'Atencao — lote fora dos parametros:\n' + u'\n'.join(erros))

        try:
            env, _ = massas.gerar_forma(doc, lote, leg, self._forma_atual, params)
            from System.Windows import MessageBox
            MessageBox.Show(
                u'Massa gerada!\n\n'
                u'Forma:           {forma}\n'
                u'Area pavimento:  {ap:.0f} m\xb2\n'
                u'Area construida: {ac:.0f} m\xb2\n'
                u'Pavimentos:      {pav}\n'
                u'CA utilizado:    {ca:.2f}'.format(
                    forma=self._forma_atual.nome,
                    ap=env['area_pavimento_m2'],
                    ac=env['area_construida_m2'],
                    pav=env['pavimentos_max'],
                    ca=env['ca_utilizado'],
                )
            )
            self.win.Close()
        except Exception as ex:
            from System.Windows import MessageBox
            MessageBox.Show(u'Erro ao gerar massa:\n' + str(ex))

    def show(self):
        self.win.ShowDialog()


JanelaGerarMassa().show()
