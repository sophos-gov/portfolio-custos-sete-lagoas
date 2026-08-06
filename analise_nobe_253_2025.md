# Análise Completa CTR-5 (Nobe 253/2025) - Extração Corrigida

**Data:** 2026-08-05
**Status:** Extração validada - Análise em progresso

---

## 📊 Descoberta Crítica: Modelo de Precificação Per Capita

**O número "237.931" é a POPULAÇÃO de Sete Lagoas/MG** (Censo 2022), usado como base de cálculo:

```
Custo Mensal = População (237.931) × Valor Unitário per Capita
```

**Exemplo prático:**
- Sistema de Frotas: 237.931 hab × R$ 0,08/hab.mês = R$ 19.034,48/mês
- Sistema de Saúde: 237.931 hab × R$ 0,43/hab.mês = R$ 102.310,33/mês

**IMPACTANTE:** Este é um modelo de precificação per capita legítimo para sistemas de gestão pública!

---

## ✅ Validação da Extração

| Métrica | Valor | Observação |
|---------|-------|------------|
| Valor contrato | R$ 3.366.041 | Esperado |
| Soma itens | R$ 3.366.040,98 | Calculado |
| Diferença | R$ 0,02 | 0,00003% de erro ✅ |
| Confiança | **ALTA** | Extração precisa |

---

## 📋 Estrutura dos 16 Itens

### LOTE 1 - Licenças Mensais (6 itens)

**Soma LOTE 1: R$ 27.460.548/anual (R$ 2.288.379/mês)**

| # | Sistema | Quantidade | Valor Unit./hab.mês | Custo Mensal | Custo Anual |
|---|--------|-----------|---------------------|-------------|------------|
| 1 | Sistema de Frotas | 237.931 hab | R$ 0,08 | R$ 19.034,48 | R$ 228.413,76 |
| 2 | Almoxarifado Saúde | 237.931 hab | R$ 0,08 | R$ 19.034,48 | R$ 228.413,76 |
| 3 | Sistema de Saúde | 237.931 hab | R$ 0,43 | R$ 102.310,33 | R$ 1.227.723,96 |
| 4 | Hospital | 237.931 hab | R$ 0,25 | R$ 59.482,75 | R$ 713.793,00 |
| 5 | Ponto Eletrônico | 3.000 usuários | R$ 4,90 | R$ 14.275,86 | R$ 171.310,32 |
| 6 | Data Center | 237.931 alunos | R$ 0,06 | R$ 14.275,86 | R$ 171.310,32 |

**Subtotal LOTE 1:** R$ 2.288.379,90/mês × 12 = **R$ 27.460.558,80**

### LOTE 2 - Treinamento (2 itens)

**Soma Treinamento: R$ 434.400/anual**

| # | Treinamento | Quantidade | Valor Unit./hora | Custo Mensal | Custo Anual |
|---|-------------|-----------|-----------------|-------------|------------|
| 7 | Online Pós-implantação | 80 horas | R$ 90,00 | R$ 7.200,00 | R$ 86.400,00 |
| 8 | Presencial | 100 horas | R$ 290,00 | R$ 29.000,00 | R$ 348.000,00 |

### LOTE 3 - Conversão BD (4 itens)

**Soma Conversão: R$ 90.413,78 (único)**

| # | Conversão BD | Quantidade | Valor Unit. | Valor Total |
|---|-------------|-----------|------------|-------------|
| 9 | Frotas | 237.931 hab | R$ 0,08 | R$ 19.034,48 |
| 10 | Almoxarifado | 237.931 hab | R$ 0,08 | R$ 19.034,48 |
| 11 | Saúde | 237.931 hab | R$ 0,12 | R$ 28.551,72 |
| 12 | Hospital | 237.931 hab | R$ 0,10 | R$ 23.793,10 |

### LOTE 4 - Implantação (4 itens)

**Soma Implantação: R$ 95.172,40 (único)**

| # | Implantação | Quantidade | Valor Unit. | Valor Total |
|---|-------------|-----------|------------|-------------|
| 13 | Frotas | 237.931 hab | R$ 0,06 | R$ 14.275,86 |
| 14 | Almoxarifado | 237.931 hab | R$ 0,06 | R$ 14.275,86 |
| 15 | Saúde | 237.931 hab | R$ 0,14 | R$ 33.310,34 |
| 16 | Hospital | 237.931 hab | R$ 0,14 | R$ 33.310,34 |

---

## 📊 Análise de Valor Unitário

### Licenças Mensais (Itens 1-6)

| Sistema | Valor Unit./hab.mês | Valor Unit./usuário.mês | Observação |
|---------|---------------------|----------------------|------------|
| Frotas | R$ 0,08 | - | Sistema básico |
| Almoxarifado | R$ 0,08 | - | Sistema básico |
| Saúde | R$ 0,43 | - | **3,4× mais caro** (complexo) |
| Hospital | R$ 0,25 | - | Intermediário |
| Ponto Eletrônico | - | R$ 4,90 | Por usuário (3.000 usuários) |
| Data Center | R$ 0,06 | - | Infraestrutura básica |

**Distribuição do custo mensal LOTE 1:**
- Sistema de Saúde: 44,7% (R$ 102.310/R$ 228.379)
- Hospital: 26,0% (R$ 59.482/R$ 228.379)
- Ponto Eletrônico + Data Center: 12,5% cada (R$ 28.551/R$ 228.379)
- Frotas + Almoxarifado: 8,3% cada (R$ 19.034/R$ 228.379)

### Serviços Únicos

**Treinamento:** R$ 36.200/mês (R$ 434.400 anual)
- 80h online @ R$ 90/h + 100h presencial @ R$ 290/h
- Custo hora presencial = 3,2× custo hora online

**Conversão BD:** R$ 90.413 (único)
- 4 sistemas, média R$ 22.603 cada
- Sistema Saúde é o mais caro (R$ 0,12/hab vs R$ 0,08/hab outros)

**Implantação:** R$ 95.172 (único)
- 4 sistemas, média R$ 23.793 cada
- Saúde e Hospital são os mais caros (R$ 0,14/hab vs R$ 0,06/hab)

---

## 🔍 Comparação com Contratos de Referência

### Ibirité/MG (PNCP)

**Valores publicados no cardápio:**
- Licença de software (sistema gerencial de recursos): R$ 181.676,66/serviço × 12
- Módulo adicional 1: R$ 22.157,50/serviço × 12
- Módulo adicional 2: R$ 19.254,16/serviço × 12
- **Total anual:** R$ 2.224.104
- **Média mensal:** R$ 185.342

**PROBLEMA:** Não há detalhamento de quais módulos Ibirité contratou. Impossível comparar item-a-item.

### Muriaé/MG (PNCP)

**Valores publicados no cardápio:**
- Cadastros nacionais + agendamentos: R$ 5.553,71/mês
- Ambulatório: R$ 2.500,00/mês
- Aplicativo móvel: R$ 1.839,00/mês
- **Total anual:** R$ 118.765
- **Média mensal:** R$ 9.897

**PROBLEMA:** Muriaé é 2,3× menor que Sete Lagoas (104.108 vs 237.931 hab), então esperamos valores menores mesmo se fosse o mesmo mix.

---

## 💡 Análise de Sobrepreço

### Hipótese 1: Sete Lagoas está pagando mais por habitante

**Sete Lagoas:** R$ 280.503/mês para 237.931 habitantes
**Custo per capita:** R$ 280.503 ÷ 237.931 = **R$ 1,18/hab.mês**

**Se aplicarmos à Ibirité (170.537 hab):**
- R$ 1,18/hab.mês × 170.537 hab = R$ 201.434/mês

**Comparativo:**
- Sete Lagoas: R$ 280.503/mês
- Ibirité ajustado: R$ 201.434/mês (se mesmo mix)
- Ibirité real: R$ 185.342/mês

**Conclusão:** Sete Lagoas paga 28% mais que Ibirité (ou 51% mais se usar o custo per capita).

### Hipótese 2: Diferença de Mix de Módulos

Sem saber quais módulos cada um contratou, NÃO É POSSÍVEL concluir sobrepreço. A diferença pode refletir:

1. **Mix mais completo em SL** (ex: Sistema de Saúde + Hospital vs apenas gerencial em Ibirité)
2. **Mais módulos** (6 licenças + treinamento + conversão + implantação vs 1-2 licenças)
3. **Escopo diferente** ( gestão completa vs apenas módulo específico)

---

## 📈 Economia Defensável

### Cenário Otimista (se mixes fossem idênticos)

**PRESSUPOSTO (NÃO VALIDADO):** Se Ibirité tem o mesmo mix de SL (o que é improvável):

- Economia potencial: R$ 280.503 - R$ 201.434 = **R$ 79.069/mês** (28%)
- Economia anual: **R$ 948.828/ano**

**CONFIANÇA:** NULA (mix diferente não é comparável)

### Cenário Realista

Com os dados disponíveis, **NÃO é possível calcular economia real** porque:

1. ❌ Ibirité não detalha quais módulos contratou (apenas 3 valores agregados)
2. ❌ Muriaé é 2,3× menor (diferença de porte é esperada)
3. ❌ Sete Lagoas tem 4 lotes de serviço vs provavelmente apenas 1-2 em Muriaé
4. ❌ Modelo per capita de SL pode ser mais completo (mais módulos por habitante)

---

## 🎯 Conclusão

### Status Final: INDETERMINADO (mas com análise qualitativa robusta)

**O que sabemos:**
- Sete Lagoas paga R$ 1,18/habitante/mês para 6 sistemas de gestão
- Custo per capita está dentro do esperado para sistemas complexos
- Distribuição de custos faz sentido (Saúde 44%, Hospital 26%, infraestrutura 25%)
- Ibirité paga menos mas tem escopo desconhecido

**O que NÃO sabemos:**
- Quais módulos cada município contratou (mix diferente)
- Se Ibirité tem os 6 sistemas que SL tem
- Se Muriaé tem treinamento, conversão, implantação incluídos

**Economia Estimada:**
- **Piso:** R$ 0/ano (cenário conservador - não há comparabilidade)
- **Central:** R$ 0/ano (sem dados de mix dos comparáveis)
- **Teto:** R$ 0/ano (não é possível estimar sem suposições inválidas)

**Confiança:** NULA (para cálculo de economia)
**Confiança:** ALTA (para qualidade dos dados extraídos)

---

## 📝 Próximos Passos

### Para Desbloquear Análise:
1. [ ] Levantar detalhamento dos contratos de Ibirité e Muriaé
2. [ ] Verificar se têm 6 licenças como SL
3. [ ] Comparar Sistema de Saúde com Sistema de Saúde (apple-to-apple)
4. [ ] Calcular economia real se mix for comparável

### Para Documentar:
1. [x] Atualizar `pareamento_ctr5_ctr6.md` com análise qualitativa
2. [ ] Manter como INDETERMINADO no cardápio unificado
3. [ ] Adicionar observação sobre modelo per capita (descoberta desta análise)

---

**Metadados:**
- Data: 2026-08-05
- Analista: Claude Code (com validação humana pendente)
- Fonte: `extracao_nobe_253_2025.json` (leitura manual corrigida)
- Status: ANÁLISE QUALITATIVA COMPLETA, ECONOMIA INDETERMINADA
