# ViabilidadeBIM — Guia de Instalação

## Pré-requisitos
- Autodesk Revit 2021 ou superior
- [pyRevit 4.8+](https://github.com/eirannejad/pyRevit/releases)

## Instalação

### 1. Abrir o pyRevit Settings
No Revit → aba **pyRevit** → botão **Settings**

### 2. Registrar a extensão
- Na aba **Custom Extensions**, clique em **Add Folder**
- Selecione: `C:\Arquivos\06. VIABILIDADE BIM\`
- Clique em **Save Settings & Reload**

O Revit vai recarregar e a aba **ViabilidadeBIM** aparecerá na faixa de opções.

---

## Estrutura da aba

```
ViabilidadeBIM
├── [01 Lote]
│   ├── Configurar Lote     → Define dimensões e seleciona a legislação ativa
│   └── Gerar Massa         → Cria o envelope construtivo no modelo 3D
│
├── [02 Viabilidade]
│   ├── Calcular VGV        → Análise financeira completa (VGV, custo, ROI, margem)
│   └── Comparar Tipologias → Gera 4 volumes e tabela comparativa
│
└── [03 Legislação]
    └── Gerenciar Legislação → Criar / editar / excluir configurações urbanísticas
```

## Fluxo de trabalho recomendado

```
1. Gerenciar Legislação  → Cadastrar as regras do município/zona
2. Configurar Lote       → Informar dimensões e selecionar a legislação
3. Gerar Massa           → Ver o envelope no modelo
4. Calcular VGV          → Análise financeira
5. Comparar Tipologias   → Design generativo com 4 volumes comparados
```

## Dados persistidos

As configurações ficam em `%APPDATA%\ViabilidadeBIM\`:
```
%APPDATA%\ViabilidadeBIM\
  legislacao\
    generico_residencial.json
    generico_misto.json
    generico_comercial.json
    <suas_configuracoes>.json
  lote_atual.json
  legislacao_ativa.json
```

Você pode criar configurações para qualquer município/zona sem tocar no código.

## Próximas funcionalidades (roadmap)

- [ ] Exportar relatório em PDF/Excel
- [ ] Otimização automática de tipologia por ROI máximo
- [ ] Recuos por fórmula variável (ex: H/6 dependente da altura)
- [ ] Suporte a lotes irregulares (polígono personalizado)
- [ ] Integração com Revit Schedule para área de pavimento tipo
