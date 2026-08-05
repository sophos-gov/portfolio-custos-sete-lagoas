# Plano de Investigação — Oportunidades de Redução de Custo
## Folha da Secretaria de Saúde · Sete Lagoas/MG · Competência fev/2026

> **Status:** plano para revisão (não executado). Gerado em 2026-06-16.
> **Universo:** R$ 20,42 mi/mês · 3.260 servidores · 87,4% da folha vinculada a 16 leis.
> **Princípio reitor:** nenhum achado entra no relatório final sem **(a) fundamento legal citado e verificado no texto integral da lei** ou **(b) evidência econômica quantificada em R$**. Proibido "pode haver" / "merece análise".

---

## 0. Por que o relatório atual ainda NÃO é "certeiro" (3 lacunas a fechar)

Estas três constatações definem o trabalho. Sem fechá-las, qualquer alegação de ilegalidade ou ineficiência é frágil.

1. **A base jurídica está incompleta.** Os textos de lei em `legislacao_cache/*.txt` têm 900–1.700 caracteres — são **ementas e trechos**, não o articulado integral. Os PDFs/DOCs completos existem no cache (LC 190/16, LC 235/20, Lei 6544/01, 7757/09, 9526/23) mas **não foram extraídos**. A análise atual (`analysis/tabelas/analise_legislacao.json`) descreve as leis, mas **não conclui ilegalidade** — diz "merece análise". Para ser certeiro é obrigatório **extrair e reler o artigo específico**.

2. **DEA clássico exige *outputs* (produção) que a folha não possui.** Os dados têm *inputs* (custo, headcount, `Horas Semanais` — preenchida em 3.260/3.260) mas nenhuma medida de produção (atendimentos, procedimentos). **Decisão tomada:** a Trilha B usará uma **fronteira de benchmarking só com a folha** (custo-por-hora-padronizada entre unidades da mesma função) — não é DEA pleno, mas é defensável e roda com os dados atuais. (Puxar DATASUS/CNES fica como evolução opcional futura.)

3. **O teto remuneratório já tem abate parcial.** Existe a rubrica de desconto `R216 DESCLIMITE_CONSTITUCIONAL`. Logo, os 146 servidores com proventos **brutos** > R$ 20k (R$ 3,95 mi) precisam ser reavaliados **líquidos do R216 e contra o subsídio real do Prefeito** antes de afirmar violação de teto — caso contrário a tese cai.

---

## TRILHA A — Jurídica (legalidade estrita)

### A.0 Pré-requisito obrigatório (habilita todo o resto)
Extrair o **texto integral** das leis em `legislacao_cache/`:
- PDF → `pdfplumber` (LC 190/16, LC 235/20, Lei 6544, 7757, 9526)
- `.doc` → `win32com` (Word) **ou** LibreOffice CLI (`soffice --headless --convert-to txt`)
- Reler os artigos efetivamente citados nas rubricas e indexá-los por código de rubrica.

> Sem o articulado integral, **nenhuma tese abaixo é conclusiva**. Esta é a etapa que transforma "merece análise" em "é ilegal porque o art. X diz Y".

### A.1 — Teses ranqueadas por (confiança × valor)

| # | Tese | Base legal a verificar no texto | Valor/mês exposto | Confiança a priori | Ação possível |
|---|------|--------------------------------|-------------------|--------------------|---------------|
| **A1** | **Contratação temporária para atividade permanente** — 2.450 servidores (75% do quadro), R$ 13,47 mi (65% da folha), lotados em unidades permanentes (Hospital Municipal, UPA, ESF, SAMU) | Art. 37, **II e IX**, CF/88 + jurisprudência consolidada do STF sobre requisitos do contrato temporário (confirmar precedentes exatos na execução) | R$ 13,47 mi (risco/passivo + custo de regularização, **não corte direto**) | 🔴 Alta | Plano de concurso + cronograma de regularização; mensurar passivo |
| **A2** | **Teto remuneratório** — 146 servidores > R$ 20k brutos (R$ 3,95 mi). Casos não-médicos flagrantes: *Agente Administrativo a R$ 46.247* e *Atendente de Consultório a R$ 44.976* | Art. 37, **XI**, CF/88 — limite municipal = subsídio do Prefeito (EC 41/03, EC 47/05). **Netar do R216** e obter subsídio vigente | Parcela acima do teto (a apurar líquida) | 🔴 Alta (não-médicos) / 🟡 (médicos em acumulação lícita) | Glosa do excedente; verificar acumulação lícita art. 37 XVI |
| **A3** | **Gratificações sem base legal** — `0094 GRAT. DESEMPENHO` (R$ 456k), `0164 RECONHECIMENTO` (R$ 24k), `0024/0089 GRAT. 10%/30%` (R$ 11k) | Art. 37, *caput* (legalidade) — vantagem paga sem lei é nula | ~R$ 0,5 mi | 🟡 Média | **Remapear contra o Estatuto (LC 192/16) antes** — só as verdadeiramente sem lastro contam |
| **A4** | **Insalubridade — laudo e base de cálculo** — `0011`+`0188`, 2.276 servidores, média R$ 399 | Súmula Vinculante 4/STF + exigência de **LTCAT/laudo técnico** | R$ 1,07 mi (contingente) | 🟡 Média | Verificar existência de laudo e base; regularizar |
| **A5** | **Incorporação/apostilamento e habitualidade** — `0053 FUNÇÃO GRATIFICADA APOSTILADO` (R$ 37k); habitualidade de plantões (LC 285/23 art. 17 **veda** incorporação) | Art. 37, CF — apostilamento pós-1998 é inconstitucional | R$ 37k + passivo de incorporação | 🟡 Média | Cessar incorporações indevidas |

> ⚠️ **Cautela "certeiro" sobre rubricas "não localizadas":** das rubricas marcadas `lei_status="nao localizada"` (confidence 0,3), **a maioria É legal** e só não foi mapeada (férias, 13º, adicional noturno, horas extras têm lastro estatutário/constitucional geral). Apenas as **verdadeiramente sem fundamento** (`GRAT. DESEMPENHO`, `RECONHECIMENTO`, `GRATIFICAÇÃO 10%/30%`) viram alvo. Remapear é parte do método — não confundir "não mapeado" com "ilegal".

### A.2 — Método por tese (loop)
1. Ler o **artigo integral** da lei criadora.
2. Cruzar com quem recebe (`folha_2026_02_rubricas_long`) — cargo, vínculo, unidade, valor.
3. Classificar: 🔴 **ILEGAL/INCONSTITUCIONAL** · 🟡 **ATENÇÃO** (risco de judicialização) · 🟢 **OK**.
4. Quantificar o **R$ sob risco** (mês e anualizado).
5. Propor a medida (suspender / reduzir / regularizar / glosar) **com a base legal citada**.

**Entregável A:** parecer jurídico-simplificado (linguagem de gestor, termos explicados) com a tabela de teses, artigo citado, valor exposto, classificação de risco e ação recomendada.

---

## TRILHA B — Econômica (eficiência) · **modo: fronteira só com a folha**

DMUs = ~40 unidades (já agregadas em `data/agg_por_unidade.csv`: headcount, custo, líquido, médio). Como não há outputs de produção, **não se roda DEA pleno**. Em vez disso:

### B.1 — Fronteira de custo-por-hora padronizada
- Calcular, por servidor, **custo / hora-equivalente** usando `Horas Semanais` (normalizar 12/20/24/30/35/40h).
- Agrupar unidades por **função homogênea** (todas ESF entre si; todas UPA/PA entre si; administrativo entre si).
- Estabelecer a **fronteira** (menor custo-hora viável do grupo) e medir a **folga** de cada unidade acima dela = excesso de custo potencial (R$).

### B.2 — Outliers alocativos (reaproveitar o que já existe)
- `analysis/tabelas/alertas_folha.csv` já traz `OUTLIER_CARGO` (ex.: *Agente Administrativo a 6,6× a mediana do cargo*). Consolidar como sinais de ineficiência e quantificar o desvio sobre a mediana do cargo.

### B.3 — Concentração e fragmentação
- Gini já = 0,3966; 4,54% dos servidores = 19,37% da folha. Detalhar por unidade.
- Fragmentação de rubricas idênticas (5 códigos `GRAT. LC192 ART.149`: 0266/0275/0276/0281/0307) → consolidação administrativa.

**Entregável B:** ranking de eficiência por unidade/cargo + lista de outliers com **folga estimada em R$** e priorização.

> **Evolução opcional (fora deste escopo):** se houver produção por unidade (DATASUS SIA-SUS/SIH, e-SUS APS, CNES — equipes/leitos), migrar para DEA BCC/CCR input-oriented; as folgas (slacks) dariam o excesso de custo na fronteira de produção real.

---

## TRILHA C — Quick wins de qualidade de dado (baixo esforço, alta credibilidade)
Já identificados na amostragem — executáveis de imediato sobre `folha_2026_02_wide`:
- `Horas Semanais = 275` (fisicamente impossível) e `= 0` com proventos > 0 → erro de cadastro.
- Servidores com **desconto = 100% dos proventos** (ex.: matr. 5016448, 5013915) → líquido zero, revisar lançamento.
- **Ghost-payment check:** gratificação paga com `Quant = 0`. Em `0249` **não há** (159/159 com Quant>0 — bom sinal); varrer as outras 15 rubricas de plantão/sobreaviso.
- Fragmentação de rubricas idênticas (item B.3).

**Entregável C:** lista de anomalias de cadastro/pagamento com matrícula e valor.

---

## Ferramentas / automação (não reinventar)
Construir sobre o pipeline existente (`analysis/folha_tables.py`, `run_analysis.py`, que já carregam a folha):
- `legal_extract.py` — PDF/DOC → texto integral (pdfplumber / win32com / LibreOffice CLI).
- `teto_check.py` — proventos líquidos do R216 vs subsídio do Prefeito.
- `fronteira_eficiencia.py` — custo-hora padronizado + folga por unidade.
- Enquadramento jurídico de cada artigo via **DeepSeek/Gemini** (Anthropic sem crédito), reutilizando o cliente de **retry + fallback** já existente em `agent/`.

---

## Sequência recomendada
1. **Trilha C** (≈1 dia) — quick wins, estabelece credibilidade.
2. **Trilha A.0 + A1 + A2** — pré-requisito (extração de leis) + maior valor/maior confiança (temporários + teto).
3. **Trilha A3–A5** — gratificações sem lastro, insalubridade, incorporação.
4. **Trilha B** — fronteira de eficiência.
5. **Síntese** — relatório consolidado com matriz valor × confiança × exequibilidade.

---

## Envelope de oportunidade (bruto, a validar — NÃO somar cegamente)

| Alvo | Exposição/mês | Natureza |
|------|---------------|----------|
| A1 Temporários | R$ 13,47 mi | Risco jurídico / passivo (não corte) |
| A2 Teto (>R$20k bruto) | R$ 3,95 mi (parcela acima, a apurar) | Glosa do excedente |
| A4 Insalubridade | R$ 1,07 mi | Contingente (depende de laudo/base) |
| A3 Gratificações sem lastro | ~R$ 0,5 mi | Corte potencial direto |
| A5 Apostilamento | R$ 37k + passivo | Cessação |

> Anualização relevante: aplicar fator ≈ **13,3×** (12 meses + 13º + 1/3 de férias) sobre valores recorrentes ao estimar impacto anual.

---

## Definition of Done (critério de aceite do relatório final)
- [ ] Cada tese jurídica cita **artigo + lei + texto integral verificado** e classificação 🔴/🟡/🟢.
- [ ] Cada oportunidade econômica tem **R$ quantificado** (folga ou desvio).
- [ ] Teto reavaliado **líquido do R216** e contra subsídio real.
- [ ] Quick wins de dado com matrícula e valor.
- [ ] Matriz final de priorização (valor × confiança × exequibilidade).
- [ ] Zero ocorrências de "pode haver" / "merece análise" sem quantificação.

## Riscos e limitações declarados
- Fronteira de eficiência (B) **não substitui DEA**: mede custo relativo, não produtividade real (faltam outputs).
- Substituir temporários por efetivos **pode elevar o custo unitário** (efetivo médio R$ 9.252 vs temporário R$ 5.500) — o ganho de A1 é **redução de risco/passivo e regularização**, não corte de folha imediato. Declarar isso explicitamente.
- Conclusões de ilegalidade dependem da **fidelidade da extração** dos PDFs/DOCs e da obtenção do **subsídio do Prefeito** (dado externo a confirmar).
