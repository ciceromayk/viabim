# -*- coding: utf-8 -*-
"""Botão: Gerenciar Legislação — CRUD de configurações urbanísticas."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
import config as cfg

import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')

from System.Windows import Window, Thickness
from ui import xaml_load

XAML = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Gerenciar Legislação Urbanística"
    Height="680" Width="820"
    ResizeMode="CanResizeWithGrip"
    WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">

  <Window.Resources>
    <Style TargetType="Label">
      <Setter Property="VerticalAlignment" Value="Center"/>
      <Setter Property="Foreground" Value="#444"/>
    </Style>
    <Style TargetType="TextBox">
      <Setter Property="Padding" Value="5,3"/>
      <Setter Property="Margin" Value="0,2,0,6"/>
      <Setter Property="BorderBrush" Value="#BBB"/>
    </Style>
    <Style TargetType="Button">
      <Setter Property="Padding" Value="14,6"/>
      <Setter Property="Margin" Value="4,0"/>
      <Setter Property="Cursor" Value="Hand"/>
    </Style>
    <Style x:Key="Header" TargetType="TextBlock">
      <Setter Property="FontSize" Value="11"/>
      <Setter Property="FontWeight" Value="SemiBold"/>
      <Setter Property="Foreground" Value="#888"/>
      <Setter Property="Margin" Value="0,10,0,4"/>
    </Style>
  </Window.Resources>

  <Grid>
    <Grid.ColumnDefinitions>
      <ColumnDefinition Width="240"/>
      <ColumnDefinition Width="*"/>
    </Grid.ColumnDefinitions>

    <!-- PAINEL ESQUERDO: lista -->
    <Border Grid.Column="0" Background="#F4F4F4" BorderBrush="#DDD" BorderThickness="0,0,1,0">
      <Grid Margin="12">
        <Grid.RowDefinitions>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="*"/>
          <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        <TextBlock Grid.Row="0" Text="Configurações salvas" FontWeight="Bold"
                   FontSize="14" Foreground="#1A5276" Margin="0,0,0,10"/>
        <ListBox Grid.Row="1" x:Name="lst_configs" Margin="0,0,0,8"
                 SelectionMode="Single" BorderBrush="#CCC"/>
        <StackPanel Grid.Row="2" Orientation="Vertical">
          <Button x:Name="btn_nova"      Content="+ Nova"/>
          <Button x:Name="btn_duplicar"  Content="Duplicar" Margin="4,4,4,0"/>
          <Button x:Name="btn_excluir"   Content="Excluir"  Margin="4,4,4,0" Foreground="#C0392B"/>
          <Button x:Name="btn_ativar"    Content="✓ Definir como Ativa" Margin="4,4,4,0" Foreground="#1A7A3F"/>
        </StackPanel>
      </Grid>
    </Border>

    <!-- PAINEL DIREITO: formulário de edição -->
    <ScrollViewer Grid.Column="1" VerticalScrollBarVisibility="Auto">
      <Grid x:Name="pnl_form" Margin="20,16,20,20" IsEnabled="False">
        <Grid.ColumnDefinitions>
          <ColumnDefinition Width="160"/>
          <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        <Grid.RowDefinitions>
          <RowDefinition Height="Auto"/>
          <!-- identif -->
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <!-- coef -->
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <!-- gabarito -->
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <!-- recuos -->
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <!-- outros -->
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <!-- notas -->
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
          <!-- botões -->
          <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <TextBlock Grid.Row="0" Grid.ColumnSpan="2" Style="{StaticResource Header}" Text="Identificação"/>

        <Label  Grid.Row="1" Grid.Column="0" Content="Nome *"/>
        <TextBox Grid.Row="1" Grid.Column="1" x:Name="txt_nome"/>

        <Label  Grid.Row="2" Grid.Column="0" Content="Município"/>
        <TextBox Grid.Row="2" Grid.Column="1" x:Name="txt_municipio"/>

        <Label  Grid.Row="3" Grid.Column="0" Content="Zona / Uso"/>
        <TextBox Grid.Row="3" Grid.Column="1" x:Name="txt_zona"/>

        <TextBlock Grid.Row="4" Grid.ColumnSpan="2" Style="{StaticResource Header}" Text="Coeficientes"/>

        <Label  Grid.Row="5" Grid.Column="0" Content="CA Básico"/>
        <TextBox Grid.Row="5" Grid.Column="1" x:Name="txt_ca_basico"/>

        <Label  Grid.Row="6" Grid.Column="0" Content="CA Máximo *"/>
        <TextBox Grid.Row="6" Grid.Column="1" x:Name="txt_ca_maximo"/>

        <Label  Grid.Row="7" Grid.Column="0" Content="TO Máximo (0–1) *"/>
        <TextBox Grid.Row="7" Grid.Column="1" x:Name="txt_to_maximo"/>

        <TextBlock Grid.Row="8" Grid.ColumnSpan="2" Style="{StaticResource Header}" Text="Gabarito (deixe vazio para calcular pelo CA)"/>

        <Label  Grid.Row="9" Grid.Column="0" Content="Máx. pavimentos"/>
        <TextBox Grid.Row="9" Grid.Column="1" x:Name="txt_pav_max"/>

        <Label  Grid.Row="10" Grid.Column="0" Content="Máx. altura (m)"/>
        <TextBox Grid.Row="10" Grid.Column="1" x:Name="txt_alt_max"/>

        <TextBlock Grid.Row="11" Grid.ColumnSpan="2" Style="{StaticResource Header}" Text="Recuos (m)"/>

        <Label  Grid.Row="12" Grid.Column="0" Content="Frontal"/>
        <TextBox Grid.Row="12" Grid.Column="1" x:Name="txt_rec_frontal"/>

        <Label  Grid.Row="13" Grid.Column="0" Content="Lateral"/>
        <TextBox Grid.Row="13" Grid.Column="1" x:Name="txt_rec_lateral"/>

        <Label  Grid.Row="14" Grid.Column="0" Content="Fundo"/>
        <TextBox Grid.Row="14" Grid.Column="1" x:Name="txt_rec_fundo"/>

        <TextBlock Grid.Row="15" Grid.ColumnSpan="2" Style="{StaticResource Header}" Text="Outros"/>

        <Label  Grid.Row="16" Grid.Column="0" Content="Pé-direito (m)"/>
        <TextBox Grid.Row="16" Grid.Column="1" x:Name="txt_pe_direito"/>

        <Label  Grid.Row="17" Grid.Column="0" Content="Outorga (% do VGV)"/>
        <TextBox Grid.Row="17" Grid.Column="1" x:Name="txt_outorga"/>

        <TextBlock Grid.Row="18" Grid.ColumnSpan="2" Style="{StaticResource Header}" Text="Notas / Observações"/>

        <TextBox Grid.Row="19" Grid.ColumnSpan="2" x:Name="txt_notas"
                 AcceptsReturn="True" Height="70" TextWrapping="Wrap"
                 VerticalScrollBarVisibility="Auto"/>

        <StackPanel Grid.Row="20" Grid.ColumnSpan="2" Orientation="Horizontal"
                    HorizontalAlignment="Right" Margin="0,16,0,0">
          <Button x:Name="btn_salvar" Content="Salvar" Background="#1A5276" Foreground="White"/>
          <Button x:Name="btn_cancelar_edicao" Content="Cancelar"/>
        </StackPanel>
      </Grid>
    </ScrollViewer>
  </Grid>
</Window>
"""


class JanelaLegislacao(object):
    def __init__(self):
        cfg.instalar_exemplos()
        self.win = xaml_load(XAML)
        self._dados_edicao = None

        self.lst  = self.win.FindName('lst_configs')
        self.form = self.win.FindName('pnl_form')

        self.win.FindName('btn_nova').Click       += self._nova
        self.win.FindName('btn_duplicar').Click   += self._duplicar
        self.win.FindName('btn_excluir').Click    += self._excluir
        self.win.FindName('btn_ativar').Click     += self._ativar
        self.win.FindName('btn_salvar').Click     += self._salvar
        self.win.FindName('btn_cancelar_edicao').Click += self._cancelar_edicao
        self.lst.SelectionChanged += self._selecionar

        self._recarregar_lista()

    def _recarregar_lista(self):
        ativa_id = ''
        try:
            la = cfg.carregar_legislacao_ativa()
            if la:
                ativa_id = la.get('id', '')
        except Exception:
            pass

        self.lst.Items.Clear()
        self._itens = cfg.listar_legislacoes()
        for leg in self._itens:
            label = leg['nome']
            if leg['id'] == ativa_id:
                label = u'[ATIVA] ' + label
            self.lst.Items.Add(label)

    def _selecionar(self, s, e):
        idx = self.lst.SelectedIndex
        if idx < 0:
            return
        self._carregar_form(self._itens[idx])

    def _carregar_form(self, leg):
        self._dados_edicao = leg
        p   = leg['parametros']
        rec = p['recuos_m']

        def s(nome, val):
            el = self.win.FindName(nome)
            if el:
                el.Text = '' if val is None else str(val)

        s('txt_nome',        leg.get('nome', ''))
        s('txt_municipio',   leg.get('municipio', ''))
        s('txt_zona',        leg.get('zona', ''))
        s('txt_ca_basico',   p.get('CA_basico', ''))
        s('txt_ca_maximo',   p.get('CA_maximo', ''))
        s('txt_to_maximo',   p.get('TO_maximo', ''))
        s('txt_pav_max',     p.get('gabarito_max_pavimentos', ''))
        s('txt_alt_max',     p.get('gabarito_max_m', ''))
        s('txt_rec_frontal', rec.get('frontal', ''))
        s('txt_rec_lateral', rec.get('lateral', ''))
        s('txt_rec_fundo',   rec.get('fundo', ''))
        s('txt_pe_direito',  p.get('altura_pe_direito_m', ''))
        s('txt_outorga',     p.get('outorga_percentual_vgv', ''))
        s('txt_notas',       leg.get('notas', ''))
        self.form.IsEnabled = True

    def _nova(self, s, e):
        self._carregar_form(cfg.template_legislacao())
        self.lst.SelectedIndex = -1

    def _duplicar(self, s, e):
        import copy
        idx = self.lst.SelectedIndex
        if idx < 0:
            return
        dup = copy.deepcopy(self._itens[idx])
        dup['id']   = ''
        dup['nome'] = dup['nome'] + ' (cópia)'
        self._carregar_form(dup)

    def _excluir(self, s, e):
        idx = self.lst.SelectedIndex
        if idx < 0:
            return
        leg = self._itens[idx]
        from System.Windows import MessageBox, MessageBoxButton, MessageBoxResult
        r = MessageBox.Show(
            u'Excluir "{}"?'.format(leg['nome']),
            'Confirmar exclusão', MessageBoxButton.YesNo)
        if r == MessageBoxResult.Yes:
            cfg.excluir_legislacao(leg['id'])
            self.form.IsEnabled = False
            self._recarregar_lista()

    def _ativar(self, s, e):
        idx = self.lst.SelectedIndex
        if idx < 0:
            return
        cfg.definir_legislacao_ativa(self._itens[idx]['id'])
        self._recarregar_lista()

    def _salvar(self, s, e):
        def g(nome):
            el = self.win.FindName(nome)
            return el.Text.strip() if el else ''

        def num(nome, padrao=None):
            v = g(nome)
            try:
                return float(v) if v else padrao
            except ValueError:
                return padrao

        def inteiro(nome, padrao=None):
            v = g(nome)
            try:
                return int(float(v)) if v else padrao
            except ValueError:
                return padrao

        nome = g('txt_nome')
        if not nome:
            from System.Windows import MessageBox
            MessageBox.Show('O campo "Nome" é obrigatório.')
            return

        dados = self._dados_edicao or cfg.template_legislacao()
        dados['nome']      = nome
        dados['municipio'] = g('txt_municipio')
        dados['zona']      = g('txt_zona')
        dados['notas']     = g('txt_notas')
        p = dados['parametros']
        p['CA_basico']                 = num('txt_ca_basico', 1.0)
        p['CA_maximo']                 = num('txt_ca_maximo', 2.5)
        p['TO_maximo']                 = num('txt_to_maximo', 0.60)
        p['gabarito_max_pavimentos']   = inteiro('txt_pav_max')
        p['gabarito_max_m']            = num('txt_alt_max')
        p['altura_pe_direito_m']       = num('txt_pe_direito', 3.0)
        p['outorga_percentual_vgv']    = num('txt_outorga', 0.10)
        p['recuos_m']['frontal']       = num('txt_rec_frontal', 5.0)
        p['recuos_m']['lateral']       = num('txt_rec_lateral', 1.5)
        p['recuos_m']['fundo']         = num('txt_rec_fundo', 3.0)

        cfg.salvar_legislacao(dados)
        self._recarregar_lista()
        from System.Windows import MessageBox
        MessageBox.Show(u'Configuração "{}" salva.'.format(nome))

    def _cancelar_edicao(self, s, e):
        self.form.IsEnabled = False
        self.lst.SelectedIndex = -1

    def show(self):
        self.win.ShowDialog()


JanelaLegislacao().show()
