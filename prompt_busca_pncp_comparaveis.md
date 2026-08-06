# PROMPT: Busca de Comparáveis PNCP para CTR-5 e CTR-6

**Use este prompt com: Gemini CLI, Claude, ou qualquer LLM que possa ler JSON**

**Comando de execução (Gemini CLI):**
```bash
gemini -p "$(cat prompt_busca_pncp_comparaveis.md | sed -n '/^# INICIO_PROMPT/,/^# FIM_PROMPT/p')" @contratos.json
```

---

# INICIO_PROMPT

## TAREFA: Encontrar Comparáveis no PNCP para Validação de Sobrepreço

Você vai analisar um arquivo JSON de contratos públicos (Sete Lagoas/MG) e encontrar contratos comparáveis no PNCP para dois casos específicos de possível sobrepreço.

### CONTEXTO

**Caso 1 (CTR-5) — Software de Gestão Integrada**
- Contrato Sete Lagoas: 253/2025 (Nobe)
- Valor: R$ 3.366.041 (12 meses) = R$ 280.503/mês
- Escopo: 6 sistemas (Frotas, Almoxarifado, Saúde, Hospital, Ponto, Data Center) + treinamento + conversão + implantação
- Fornecedor: Nobe Software de Gestão Integrada Ltda
- Per Capita: R$ 1,18/hab/mês (227.397 hab)
- **Pergunta:** Sete Lagoas está pagando ACIMA da mediana de mercado?

**Caso 2 (CTR-6) — Kits Reagentes Laboratoriais**
- Contrato Sete Lagoas: 045/2026 (Scanlab)
- Valor: R$ 1.231.176 (12 meses) = R$ 102.598/mês
- Escopo: 58 tipos de kits reagentes (vitaminas, hormônios, marcadores, sorologia)
- Quantidade: 172.800 unidades
- Preço médio: R$ 6,95/unidade
- Fornecedor: Scanlab Diagnóstica Ltda
- Per Capita: R$ 0,45/hab/mês (227.397 hab)
- **Pergunta:** Sete Lagoas está pagando ACIMA da mediana de mercado?

---

### TAREFA 1: BUSCAR COMPARÁVEIS DE SOFTWARE (CTR-5)

Procure contratos com estas características:

**Critérios de Busca:**
1. Descrição do objeto contém: "software", "gestão integrada", "sistema gerencial", "ERP", "gestão pública"
2. Ano: 2024 ou 2025 (mesmo período que SL)
3. Fornecedor: QUALQUER UM, EXCETO "nobe" (case-insensitive)
4. Valor: entre R$ 1.000.000 e R$ 10.000.000 (escala de software grande)
5. Municipio: população estimada entre 150.000 e 350.000 hab (±30% de Sete Lagoas)

**Resultado Esperado — Para cada contrato encontrado, retorne:**
```json
{
  "numero_contrato": "XXX/YYYY",
  "fornecedor": "Nome da Empresa",
  "municipio": "Cidade/UF",
  "ano": YYYY,
  "valor_total": NNNNNN.NN,
  "valor_mensal_estimado": NNNNN.NN,
  "descricao_objeto": "Texto resumido",
  "motivo_relevancia": "Por que este é comparável (qual sistema, qual escopo)"
}
```

**Limite:** Retorne no máximo os **5 melhores matches** (aqueles com maior similaridade de escopo com SL).

**Ordem de Prioridade:**
1. Municipios com 200k-250k hab (mais próximos de SL)
2. Contratos 2025 (mais recentes)
3. Contratos com nomes de sistema semelhantes (gestão integrada, ERPm municipal)

---

### TAREFA 2: BUSCAR COMPARÁVEIS DE KITS REAGENTES (CTR-6)

Procure contratos com estas características:

**Critérios de Busca:**
1. Descrição contém: "kit", "reagente", "exame", "laboratorial", "sorologia", "triagem"
2. Ano: 2024 ou 2025 (mesmo período que SL)
3. Fornecedor: QUALQUER UM, EXCETO "scanlab" (case-insensitive)
4. Valor: entre R$ 300.000 e R$ 2.000.000 (escala de kits para saúde municipal)
5. Municipio: população estimada entre 150.000 e 350.000 hab (±30% de Sete Lagoas)

**Resultado Esperado — Para cada contrato encontrado, retorne:**
```json
{
  "numero_contrato": "XXX/YYYY",
  "fornecedor": "Nome da Empresa",
  "municipio": "Cidade/UF",
  "ano": YYYY,
  "valor_total": NNNNNN.NN,
  "valor_mensal_estimado": NNNNN.NN,
  "descricao_objeto": "Texto resumido",
  "quantidade_itens_se_disponivel": "ex: 45 tipos, ou null se desconhecido",
  "motivo_relevancia": "Por que este é comparável (qual tipo de teste, qual escopo)"
}
```

**Limite:** Retorne no máximo os **5 melhores matches** (aqueles com maior similaridade de escopo com SL).

**Ordem de Prioridade:**
1. Municipios com 200k-250k hab (mais próximos de SL)
2. Contratos 2025 (mais recentes)
3. Contratos que mencionam "quantidade de testes" ou "unidades" (permitem cálculo de preço unitário)

---

### TAREFA 3: ANÁLISE COMPARATIVA

**Se encontrou ≥ 3 comparáveis em cada categoria:**

Para CTR-5 (software), calcule e retorne:
```json
{
  "categoria": "CTR-5 Software",
  "comparaveis_encontrados": N,
  "analise": {
    "per_capita_sl": 1.2335,
    "per_capita_comparaveis": [X, Y, Z],
    "mediana_comparaveis": NUMERO,
    "media_comparaveis": NUMERO,
    "desvio_sl_vs_mediana_pct": NUMERO,
    "interpretacao": "SL está [X%] [acima/abaixo] da mediana"
  },
  "veredito": "Sobrepreço? SIM | NAO | INCONCLUSIVO"
}
```

Para CTR-6 (kits), calcule e retorne:
```json
{
  "categoria": "CTR-6 Kits Reagentes",
  "comparaveis_encontrados": N,
  "analise": {
    "per_capita_sl": 0.4512,
    "per_capita_comparaveis": [X, Y, Z],
    "mediana_comparaveis": NUMERO,
    "media_comparaveis": NUMERO,
    "desvio_sl_vs_mediana_pct": NUMERO,
    "mix_testes_validacao": "SL tem 58 tipos; comparáveis têm [X-Y tipos]; diferença de escopo: [grande/pequena/nenhuma]",
    "interpretacao": "SL está [X%] [acima/abaixo] da mediana"
  },
  "veredito": "Sobrepreço? SIM | NAO | INCONCLUSIVO"
}
```

**Se encontrou < 3 comparáveis em alguma categoria:**
```json
{
  "categoria": "CTR-X",
  "comparaveis_encontrados": N,
  "motivo_insuficiencia": "Descrição clara de por que não achou mais",
  "veredito": "INCONCLUSIVO — dados insuficientes"
}
```

---

### INSTRUÇÕES CRÍTICAS

1. **Não confundir "amostra" com "contrato inteiro":**
   - Se um município publica R$ 185.342/mês mas o contrato total é R$ 233.333/mês, USE O TOTAL
   - Procurar sempre pelo valor agregado do contrato, não por subcategorias

2. **Descartar composições SINAPI falsas:**
   - Se um contrato tem múltiplos itens com a MESMA quantidade (ex: 5.000) mas unidades diferentes (M³, HI, HP, L), é planilha de custo, não compra real → descartar
   - Se contrato tem "1 LOTE" ou "1 SRV" (lote global), é agregado sem quantidade real → descartar para análise de preço unitário

3. **Validação de escopo para CTR-6:**
   - Se comparável tem 3 testes (básicos) e SL tem 58 (complexos), anotar a diferença
   - Diferença grande pode justificar preço maior mesmo que per capita seja maior
   - Se diferença de escopo é clara, veredito fica "INCONCLUSIVO — escopo incomparável"

4. **Formato de saída:**
   - Retorne SEMPRE em JSON válido (não markdown, não texto)
   - Se alguma informação não está disponível, usar `null`
   - Datas em formato ISO (YYYY-MM-DD)

5. **Se não encontrar dados:**
   - Reportar exatamente quantos contratos foram varridos
   - Explicar por que não encontrou (falta de dados PNCP de 2024-2025? escopo muito específico?)
   - Sugerir alternativas (expandir para 2023? procurar em TCE-MG direto?)

---

### REFERÊNCIAS PARA CONTEXTO

- **População de Sete Lagoas (Censo IBGE 2022):** 227.397
- **Intervalo aceitável:** ±30% = 150.000 - 350.000 hab
- **Desvio menor que 10%:** SL está no mercado (sem sobrepreço claro)
- **Desvio 10-30%:** SL pode estar caro, investigar escopo
- **Desvio maior que 30%:** Possível sobrepreço significativo (validar escopo)

---

### FORMATO DE SAÍDA FINAL

Retorne um JSON com esta estrutura:

```json
{
  "data_execucao": "YYYY-MM-DD HH:MM",
  "municipio_auditado": "Sete Lagoas/MG",
  "populacao_referencia": 227397,
  "resultados": {
    "CTR-5": {
      "caso": "Software Gestão Integrada (Nobe 253/2025)",
      "comparaveis": [<array de JSON dos comparáveis encontrados>],
      "analise": <JSON de análise conforme acima>,
      "veredito": "SIM | NAO | INCONCLUSIVO",
      "justificativa": "Explicação breve do veredito"
    },
    "CTR-6": {
      "caso": "Kits Reagentes Laboratoriais (Scanlab 045/2026)",
      "comparaveis": [<array de JSON dos comparáveis encontrados>],
      "analise": <JSON de análise conforme acima>,
      "veredito": "SIM | NAO | INCONCLUSIVO",
      "justificativa": "Explicação breve do veredito"
    }
  },
  "observacoes_gerais": "Notas sobre qualidade dos dados, limitações encontradas, etc.",
  "proximos_passos": "Se inconclusivo, o que fazer?"
}
```

---

### CHECKLIST ANTES DE RETORNAR

- [ ] Procurou por ambas as categorias (CTR-5 e CTR-6)
- [ ] Aplicou filtros de ano (2024-2025)
- [ ] Aplicou filtros de fornecedor (excluiu Nobe e Scanlab)
- [ ] Validou população (±30% de SL)
- [ ] Retornou no máximo 5 best matches por categoria
- [ ] Calculou per capita para comparáveis
- [ ] Comparou com SL usando mediana (não média)
- [ ] Anotou motivo de relevância para cada comparável
- [ ] Retornou JSON válido (testado com json.parse ou similar)
- [ ] Explicou veredito (por que SIM/NAO/INCONCLUSIVO)

---

# FIM_PROMPT

