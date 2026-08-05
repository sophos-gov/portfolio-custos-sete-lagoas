# 🔬 Auditoria da Educação — Sete Lagoas/2025

*MDE (25%) e Fundeb · Fonte: SICOM/TCE-MG · Gerado em 2026-07-20*

---

## 📊 Resumo Executivo

- **Empenhos de educação analisados:** 2363
- 🟢 Verde (elegível): **582**
- 🟡 Amarela (cautelar): **1604**
- 🟠 Laranja (pendente): **3**
- 🔴 Vermelha (glosável): **174**
- **Índice de Conversão (Liquidado/Empenhado):** 97.3%

## 🔴 Despesas com Risco de Glosa

| Categoria | Nº Empenhos | Valor Empenhado |
|-----------|-------------|-----------------|
| merenda | 162 | R$ 8.488.603,84 |
| inativo | 9 | R$ 2.217.486,62 |
| uniforme | 1 | R$ 459.033,50 |
| copa_agua | 10 | R$ 137.583,71 |
| diarias_capacitacao | 65 | R$ 132.388,60 |

> ⚠️ **Ação recomendada**: estorno + remanejamento de fonte (de MDE/Fundeb para recursos livres ou fonte específica como PNAE 1.552.000).

### 🟡 Revisar: 505 empenhos de indenização trabalhista (R$ 18.007.637,85)

Natureza `3.1.90.94` na educação: possíveis **indenizações a inativos/pensionistas** (EC 108/2020 — glosa integral). Revisar historicamente cada um para confirmar se é inativo.

### Top 15 empenhos glosáveis

| Empenho | Data | Natureza | Fonte | Categoria | Valor |
|---------|------|----------|-------|-----------|-------|
| 206336 | 20251022 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 11.799,45 |
| 206255 | 20251021 | 3.3.90.30 | 1.500 | merenda (alimentacao escolar) | R$ 54.282,40 |
| 206957 | 20251024 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 10.172,75 |
| 206256 | 20251021 | 3.3.90.30 | 1.500 | merenda (alimentacao escolar) | R$ 18.146,00 |
| 205591 | 20251007 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 62.096,95 |
| 206261 | 20251021 | 3.3.90.30 | 1.500 | merenda (alimentacao escolar) | R$ 12.470,00 |
| 205896 | 20251014 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 953,50 |
| 206349 | 20251024 | 3.3.90.30 | 1.500 | merenda (alimentacao escolar) | R$ 17.449,80 |
| 206253 | 20251021 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 157.515,90 |
| 205592 | 20251007 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 21.658,40 |
| 206252 | 20251021 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 115.640,09 |
| 205897 | 20251014 | 3.3.90.30 | 1.500 | merenda (generos alimenticios) | R$ 4.760,00 |
| 206254 | 20251021 | 3.3.90.30 | 1.500 | merenda (pao) | R$ 4.408,00 |
| 205603 | 20251008 | 3.3.90.30 | 1.500 | merenda (alimentacao escolar) | R$ 5.077,50 |
| 206350 | 20251024 | 3.3.90.30 | 1.500 | merenda (alimentacao escolar) | R$ 22.043,30 |

*Exemplo de histórico:* `AQUISICAO DE GENEROS ALIMENTICIOS (PAES E BISCOITOS) DA AGRICULTURA FAMILIAR COM A FINALIDADE DE SUPRIR AS NECESSIDADES `

## 💰 Validações do Fundeb

- **Piso 70% (profissionais da educação):** 113.21% — **REGULAR_ATENCAO**
  - Índice 113.2% — piso cumprido, mas >100% da receita do Fundeb do exercício é incomum. Possíveis causas: uso de saldo financeiro/superávit de exercícios anteriores, ou despesa de pessoal em fonte Fundeb classificada além do repasse do ano corrente. Base: receita.csv SICOM (fonte Fundeb). Recomenda-se conciliar com o extrato da conta vinculada do Fundeb.
- **VAAT (Infantil 50% / Capital 15%):** Município não recebe VAAT (fonte 1.542 ausente).
- **4% Tempo Integral (EC 135/2024):** Nenhuma ação/IDU de 'Tempo Integral' identificada. Impossível validar os 4% (EC 135/2024). Exige marcação orçamentária específica.
- **Restos a Pagar:** RP (11,528,101) > 10% Fundeb (11,198,115); RP não processado elevado vs processado — risco de maquiagem do índice

## 📈 Análise Temporal

- IC global 97.3% dentro de parâmetros.
- 3 empenho(s) de CAPITAL emitido(s) em nov/dez — risco de não liquidação no exercício.
- RP não processado = 65.5% do total — risco de recalculo retroativo do índice.

## 📉 Simulação do Índice de 25% MDE

Índice apurado em 31.47% (meta 25%), com base na Receita Líquida de Impostos e Transferências (RLIT) realizada — fonte 1.500 do receita.csv SICOM. Apuração via classificação de Fonte de Recursos do SICOM, não o RREO Anexo 10 oficial — reconciliar com o RREO/SIOPE do exercício antes de uso em prestação de contas.

- Índice estimado: **31.47%** (meta 25%)
- MDE líquido (após glosas): R$ 261.099.265,74

---

*Skill `sicom-auditoria-educacao` · Conforme LDB (Arts. 70/71), Lei 14.113/2020, EC 135/2024, EC 108/2020 · Análise automatizada não substitui apuração oficial.*
