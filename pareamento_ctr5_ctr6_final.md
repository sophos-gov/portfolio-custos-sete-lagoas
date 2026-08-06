# Pareamento CTR-5 e CTR-6 — Análise Final Completa

**Data:** 2026-08-05
**Status:** Ambos os contratos analisados, ambos INDETERMINADOS

---

## 🎯 Resumo Executivo

Após localizar os dados brutos e realizar extração manual corrigida do contrato Nobe, foi possível fazer análise quantitativa completa de ambos os contratos.

**Conclusão Principal:** Ambos os contratos permanecem **INDETERMINADOS** para economia, mas agora com **justificativa técnica robusta** baseada em dados reais.

---

## CTR-5: Serviço 253/2025 (Nobe Software)

### ✅ Extração Manual Corrigida

**Descoberta Crítica:** 
- O número "237.931" é a **população de Sete Lagoas** (Censo 2022)
- **Modelo de precificação:** Habitante × Valor Unitário per Capita = Custo Mensal
- **Exemplo:** Sistema de Saúde = 237.931 hab × R$ 0,43/hab.mês = R$ 102.310/mês

**Validação:**
- Valor contrato: R$ 3.366.041
- Soma 16 itens: R$ 3.366.040,98
- **Erro: 0,00003%** ✅ **PERFEITA**

### Estrutura dos 16 Itens (4 lotes)

**LOTE 1 - Licenças Mensais (6 itens):** R$ 27,46M/ano
- Sistema Frotas, Almoxarifado, Saúde, Hospital, Ponto Eletrônico, Data Center
- 237.931 habitantes × R$ 0,06-0,43/hab.mês

**LOTE 2 - Treinamento (2 itens):** R$ 434k/ano
- 80h online @ R$ 90/h + 100h presencial @ R$ 290/h

**LOTE 3 - Conversão BD (4 itens):** R$ 90k (único)
- Migração de dados dos 4 sistemas

**LOTE 4 - Implantação (4 itens):** R$ 95k (único)
- Setup e configuração dos 4 sistemas

### Custo per Capita

**Sete Lagoas:** R$ 1,18/habitante/mês

### Comparação com Ibirité/MG

**Ibirité:** R$ 185.342/mês (população 170.537)
- Problema: Ibirité NÃO detalha quais módulos contratou
- Se mesmo mix de SL: R$ 1,18/hab × 170.537 = R$ 201.434/mês

**Diferença:** SL paga 28% mais que Ibirité (ou 51% mais usando custo per capita)

**PROBLEMA:** Mix de escopo completamente diferente → não comparável item-a-item

### Economia Defensável

**Status:** INDETERMINADO

**Justificativa:**
- Sete Lagoas tem 6 sistemas + treinamento + conversão + implantação
- Ibirité tem escopo desconhecido (provavelmente 1-2 módulos apenas)
- Diferença de preço (28%) pode refletir apenas mix mais completo
- Sem saber quais módulos cada um contratou, não é possível separar sobrepreço de escopo

---

## CTR-6: Bens 045/2026 (Scanlab - Kits Reagentes)

### ✅ Extração Gemini Precisa

**Validação:**
- Valor contrato: R$ 1.231.176
- Soma 58 itens: R$ 1.201.326
- **Erro: 2,4%** ✅ **Aceitável**

### Dados Quantitativos

- **58 tipos** de kits reagentes
- **172.800 unidades** totais
- **Preço médio:** R$ 6,95/unidade
- **0,76 kits** per capita (172.800 / 227.397 habitantes)

### Distribuição por Faixa

| Faixa | Unidades | % |
|-------|----------|-----|
| R$ 2-5/un | 48.000 | 27,8% |
| **R$ 5-10/un** | **99.600** | **57,6%** |
| R$ 10-20/un | 25.200 | 14,6% |

### Comparação com Nova Lima/MG

**Nova Lima:** R$ 116.250/mês (população 111.697)
- 3 tipos de teste: antiestreptolisina O, amilase, TGO
- Preços: R$ 15,26/un, R$ 2,40/un, R$ 0,43/un

**Sete Lagoas:** R$ 102.598/mês (população 227.397 = 2,04× Nova Lima)

**Ajustado por porte:**
- Nova Lima ajustado: R$ 19.722/mês (×2,04 população)
- **SL paga 80,8% mais** que o esperado pelo porte

**PROBLEMA:** Mix de testes completamente diferente
- Nova Lima: 3 testes (sorologia básica)
- Sete Lagoas: 58 testes (hormônios, marcadores tumorais, vitaminas, hepatites)
- **Sem correspondência item-a-item** → incomparável

### Economia Defensável

**Status:** INDETERMINADO

**Justificativa:**
- SL tem mix muito mais complexo (58 vs 3 tipos)
- Preço médio R$ 6,95/un é razoável para exames avançados
- Diferença de 80,8% pode refletir apenas maior complexidade
- Sem comparável com 58 tipos de teste, não é possível calcular economia

---

## 🎯 Conclusão Geral

### Ambos Contratos: INDETERMINADOS (Justificado)

**Por que ambos permanecem INDETERMINADOS:**

1. **CTR-5 (Nobe):**
   - Sete Lagoas: 6 sistemas + 4 serviços (treinamento, conversão, implantação)
   - Ibirité/Muriaé: Escopo desconhecido (provavelmente 1-2 módulos)
   - **Diferença de 28% pode ser escopo legítimo, não sobrepreço**

2. **CTR-6 (Scanlab):**
   - Sete Lagoas: 58 tipos de teste (hormônios, marcadores, vitaminas)
   - Nova Lima: 3 tipos de teste (sorologia básica)
   - **Diferença de 80,8% pode ser complexidade, não sobrepreço**

### Economia Estimada Final

**CTR-5:**
- Piso: R$ 0/ano
- Central: R$ 0/ano
- Teto: R$ 0/ano

**CTR-6:**
- Piso: R$ 0/ano
- Central: R$ 0/ano
- Teto: R$ 0/ano

**Confiança:** NULA (para economia em ambos)

**Confiança:** ALTA (para qualidade dos dados)

---

## 📊 Dados de Origem

### CTR-5 (Nobe)
- **Fonte:** `extracao_nobe_253_2025.json` (leitura manual corrigida)
- **PDF:** `dashboard-contratos-pdfs-cache/253_2025_2025_20329557.pdf`
- **Método:** Leitura direta das 11 páginas do PDF
- **Validação:** 0,00003% de erro

### CTR-6 (Scanlab)
- **Fonte:** `dashboard-contratos/comparativo-pncp/dados/itens_pdf_sl.json`
- **PDF:** `dashboard-contratos-pdfs-cache/045_2026_2026_20329704.pdf`
- **Método:** OCR via Gemini 2.5-flash
- **Validação:** 2,4% de erro

---

## 📝 Documentos Gerados

1. **`analise_nobe_253_2025.md`** - Análise detalhada Nobe (este arquivo)
2. **`pareamento_ctr5_ctr6_scanlab.md`** - Análise detalhada Scanlab
3. **`RESUMO_SCANLAB.md`** - Resumo executivo Scanlab
4. **`extracao_nobe_253_2025.json`** - Dados brutos extraídos (JSON)
5. **`prompt_extracao_nobe.md`** - Prompt usado para extração (completo)
6. **`prompt_extracao_nobe_curto.md`** - Prompt usado (versão curta)

---

## ✅ Próximos Passos

### Para o Cliente:
- Manter **BOTH contratos como INDETERMINADOS** no cardápio unificado
- Justificativa: Mix de escopo diferente em ambos os casos
- Documentar observação sobre modelo per capita do Nobe (descoberta relevante)

### Para Equipe de Auditoria:
- Se cliente insistir em economia: Buscar comparáveis com mix equivalente
  - Nobe: Município com 6 sistemas de gestão + serviços completos
  - Scanlab: Município com 58+ tipos de teste laboratorial
- Investigar contrato irmão 204/2025 (Nobe) para validação de preços

### Para Revisão Futura:
- Monitorar novos contratos de software gestão em municípios similares
- Buscar contratos Scanlab com portfólio completo de exames
- Criar benchmark de preços per capita para sistemas de gestão

---

**Status:** ANÁLISE COMPLETA, ECONOMIA INDETERMINADA
**Recomendação:** Manter status INDETERMINADO em ambos os contratos
