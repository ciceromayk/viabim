# -*- coding: utf-8 -*-
"""
Utilitários de UI compartilhados entre os scripts do ViabilidadeBIM.
Compatível com IronPython 2 (pyRevit).
"""
import clr
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')

from System.Windows.Markup import XamlReader
from System.IO import MemoryStream
from System.Text import Encoding


def xaml_load(xaml_str):
    """
    Carrega uma janela WPF a partir de uma string XAML.
    Usa MemoryStream — compatível com IronPython (StringReader não funciona).
    """
    encoded = Encoding.UTF8.GetBytes(xaml_str)
    stream  = MemoryStream(encoded)
    return XamlReader.Load(stream)
