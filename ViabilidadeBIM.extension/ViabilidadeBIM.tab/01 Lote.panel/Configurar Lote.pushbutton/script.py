# -*- coding: utf-8 -*-
"""Botão: Configurar Lote — define dimensões e seleciona a legislação ativa."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
import config as cfg
import massas

from ui import xaml_load

XAML = u"""
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Configurar Lote" Height="560" Width="520"
    ResizeMode="NoResize" WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI" FontSize="13">
  <Window.Resources>
    <Style TargetType="Label">
      <Setter Property="VerticalAlignment" Value="Center"/>
      <Setter Property="Foreground" Value="#444"/>
      <Setter Property="Width" Value="160"/>
    </Style>
    <Style TargetType="TextBox">
      <Setter Property="Padding" Value="5,4"/>
      <Setter Property="Margin" Value="0,3,0,8"/>
      <Setter Property="BorderBrush" Value="#BBB"/>
    </Style>
  </Window.Resources>
  <Grid Margin="24">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <TextBlock Grid.Row="0" Text="Configuração do Lote" FontSize="18"
               FontWeight="Bold" Foreground="#1A5276" Margin="0,0,0,20"/>

    <StackPanel Grid.Row="1" Orientation="Horizontal">
      <Label Content="Identificação do lote"/>
      <TextBox x:Name="txt_nome" Width="280" Text="Lote 01"/>
    </StackPanel>

    <StackPanel Grid.Row="2" Orientation="Horizontal">
      <Label Content="Largura do lote (m)"/>
      <TextBox x:Name="txt_largura" Width="120" Text="20"/>
    </StackPanel>

    <StackPanel Grid.Row="3" Orientation="Horizontal">
      <Label Content="Profundidade do lote (m)"/>
      <TextBox x:Name="txt_profundidade" Width="120" Text="40"/>
    </StackPanel>

    <Border Grid.Row="4" Background="#EAF4FB" CornerRadius="4" Padding="12,8" Margin="0,4,0,16">
      <TextBlock x:Name="txt_area" Text="Área do lote: —  m²"
                 FontWeight="SemiBold" Foreground="#1A5276"/>
    </Border>

    <!-- Seleção de legislação -->
    <TextBlock Grid.Row="5" Text="LEGISLAÇÃO ATIVA" FontSize="11" FontWeight="SemiBold"
               Foreground="#888" Margin="0,0,0,6"/>

    <ComboBox Grid.Row="6" x:Name="cmb_leg" Margin="0,0,0,8"
              DisplayMemberPath="nome" HorizontalContentAlignment="Left"/>

    <Border Grid.Row="7" Background="#F8F8F8" BorderBrush="#DDD" BorderThickness="1"
            CornerRadius="4" Padding="10" Margin="0,0,0,16">
      <TextBlock x:Name="txt_resumo_leg" TextWrapping="Wrap" Foreground="#555" FontSize="12"
                 Text="Selecione uma configuração de legislação acima."/>
    </Border>

    <StackPanel Grid.Row="8" Orientation="Horizontal" HorizontalAlignment="Right">
      <Button x:Name="btn_ok" Content="Salvar" Padding="20,8"
              Background="#1A5276" Foreground="White" Margin="0,0,8,0"/>
      <Button x:Name="btn_cancelar" Content="Cancelar" Padding="20,8"/>
    </StackPanel>
  </Grid>
</Window>
"""


class JanelaLote(object):
    def __init__(self):
        cfg.instalar_exemplos()
        self.win = xaml_load(XAML)

        self.txt_nome    = self.win.FindName('txt_nome')
        self.txt_larg    = self.win.FindName('txt_largura')
        self.txt_prof    = self.win.FindName('txt_profundidade')
        self.txt_area    = self.win.FindName('txt_area')
        self.cmb_leg     = self.win.FindName('cmb_leg')
        self.txt_resumo  = self.win.FindName('txt_resumo_leg')

        self.txt_larg.TextChanged += self._atualizar_area
        self.txt_prof.TextChanged += self._atualizar_area
        self.cmb_leg.SelectionChanged += self._leg_selecionada

        self.win.FindName('btn_ok').Click       += self._salvar
        self.win.FindName('btn_cancelar').Click += lambda s, e: self.win.Close()

        self._legislacoes = cfg.listar_legislacoes()
        for leg in self._legislacoes:
            self.cmb_leg.Items.Add(leg)

        # Pré-selecionar ativa e lote salvo
        leg_ativa = None
        try:
            leg_ativa = cfg.carregar_legislacao_ativa()
        except Exception:
            pass

        if leg_ativa:
            for i, l in enumerate(self._legislacoes):
                if l['id'] == leg_ativa['id']:
                    self.cmb_leg.SelectedIndex = i
                    break
        elif self._legislacoes:
            self.cmb_leg.SelectedIndex = 0

        lote = cfg.carregar_lote()
        if lote:
            self.txt_nome.Text = lote.get('nome', 'Lote 01')
            self.txt_larg.Text = str(lote.get('largura_m', 20))
            self.txt_prof.Text = str(lote.get('profundidade_m', 40))

        self._atualizar_area(None, None)

    def _atualizar_area(self, s, e):
        try:
            l = float(self.txt_larg.Text)
            p = float(self.txt_prof.Text)
            self.txt_area.Text = u'Área do lote: {:.1f} m²'.format(l * p)
        except (ValueError, TypeError):
            self.txt_area.Text = u'Área do lote: —'

    def _leg_selecionada(self, s, e):
        idx = self.cmb_leg.SelectedIndex
        if idx < 0:
            self.txt_resumo.Text = 'Selecione uma configuração.'
            return
        leg = self._legislacoes[idx]
        p   = leg['parametros']
        rec = p['recuos_m']
        self.txt_resumo.Text = (
            u'CA máx.: {ca}  |  TO máx.: {to:.0%}  |  Pav.: {pav}  |  '
            u'Recuos: Fr {rf}m / Lat {rl}m / Fu {rfn}m\n'
            u'Pé-direito: {pe}m  |  Outorga: {out:.0%} do VGV\n'
            u'{notas}'
        ).format(
            ca=p['CA_maximo'], to=p['TO_maximo'],
            pav=p.get('gabarito_max_pavimentos') or 'sem limite',
            rf=rec['frontal'], rl=rec['lateral'], rfn=rec['fundo'],
            pe=p.get('altura_pe_direito_m', 3.0),
            out=p.get('outorga_percentual_vgv', 0),
            notas=leg.get('notas', ''),
        )

    def _salvar(self, s, e):
        try:
            larg = float(self.txt_larg.Text)
            prof = float(self.txt_prof.Text)
        except ValueError:
            from System.Windows import MessageBox
            MessageBox.Show('Largura e profundidade devem ser números.')
            return

        if larg <= 0 or prof <= 0:
            from System.Windows import MessageBox
            MessageBox.Show('Dimensões devem ser maiores que zero.')
            return

        idx = self.cmb_leg.SelectedIndex
        if idx < 0:
            from System.Windows import MessageBox
            MessageBox.Show('Selecione uma configuração de legislação.')
            return

        lote = {'nome': self.txt_nome.Text.strip() or 'Lote 01',
                'largura_m': larg, 'profundidade_m': prof}
        leg  = self._legislacoes[idx]

        erros = massas.validar_lote(lote, leg)
        if erros:
            from System.Windows import MessageBox
            MessageBox.Show(u'Atenção:\n' + '\n'.join(erros))

        cfg.salvar_lote(lote)
        cfg.definir_legislacao_ativa(leg['id'])

        env = massas.calcular_envelope(lote, leg)
        from System.Windows import MessageBox
        MessageBox.Show(
            u'Lote salvo!\n\n'
            u'Área construível: {ac:.1f} m²\n'
            u'Pavimentos máx.: {pav}\n'
            u'Gabarito: {gab:.1f} m\n'
            u'CA utilizado: {ca:.2f}\n'
            u'TO utilizado: {to:.1%}'.format(
                ac=env['area_construida_m2'], pav=env['pavimentos_max'],
                gab=env['gabarito_m'], ca=env['ca_utilizado'], to=env['to_utilizado']))
        self.win.Close()

    def show(self):
        self.win.ShowDialog()


JanelaLote().show()
