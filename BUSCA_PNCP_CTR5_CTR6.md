# Busca PNCP para CTR-5 e CTR-6 — Instrução para Nova IA

**Objetivo:** Encontrar contratos comparáveis no PNCP para validar se CTR-5 (Nobe) e CTR-6 (Scanlab) têm sobrepreço, comparando com outros fornecedores de escopo similar.

**Data de criação:** 2026-08-05 17:50  
**Status:** Pronto para execução em outra IA ou ferramenta

---

## ✅ O Que Procurar

### CTR-5: Contratos de Software/Gestão Integrada (NÃO Nobe)

**Características do contrato Sete Lagoas:**
- Valor: R$ 3.366.041 (12 meses)
- Valor mensal: R$ 280.503
- Escopo: 6 sistemas (Frotas, Almoxarifado, Saúde, Hospital, Ponto Eletrônico, Data Center) + treinamento + conversão + implantação
- Fornecedor: Nobe Software de Gestão Integrada Ltda
- Modelo de precificação: **Per capita** (R$ 1,18 por habitante por mês para Sete Lagoas)
- População: 227.397 (Censo 2022)

**Buscar no PNCP:**
- Contratos de "software gestão pública", "sistema gerencial", "ERP", "gestão integrada"
- Anos: 2024-2025 (mesmo período)
- Fornecedores: qualquer um EXCETO Nobe
- Filtro de valor: descarte extremos (outliers > 3x mais caro que SL)
- Objetivo: encontrar **3+ contratos** com contexto similar (mesma população ±30%, mesma quantidade de módulos/escopo)

**Resultado esperado:**
- Custo mensal por habitante para cada comparável
- Comparação per capita com SL
- Validação: SL está acima ou abaixo da mediana?

**Nota crítica:** Alguns municípios no PNCP publicam apenas agregados (ex: Ibirité publicou R$ 185.342 em amostra quando o total era R$ 233.333). Usar sempre o **contrato inteiro**, não subconjuntos.

---

### CTR-6: Contratos de Kits Reagentes/Exames Laboratoriais (NÃO Scanlab)

**Características do contrato Sete Lagoas:**
- Valor: R$ 1.231.176 (12 meses)
- Valor mensal: R$ 102.598
- Itens: 58 tipos de kits reagentes (vitaminas, hormônios, marcadores tumorais, sorologia, etc.)
- Quantidade total: 172.800 unidades
- Preço médio: R$ 6,95/unidade
- Fornecedor: Scanlab Diagnóstica Ltda
- Per capita: R$ 0,45 por habitante por mês
- População: 227.397 (Censo 2022)

**Buscar no PNCP:**
- Contratos de "kits reagentes", "kits exames", "reagentes laboratorial"
- Anos: 2024-2025 (mesmo período)
- Fornecedores: qualquer um EXCETO Scanlab
- Filtro de valor mensal: R$ 50k - R$ 300k (porte similar)
- População comparável: 150k - 350k hab (±30% de SL)
- Objetivo: encontrar **3+ contratos** com quantidade de itens similar (30-80 tipos de teste)

**Resultado esperado:**
- Valor total do contrato por habitante
- Custo por unidade de kit (se houver publicação de quantidade)
- Comparação per capita com SL
- Mix de testes (quantos tipos — básicos, hormônios, marcadores tumorais, etc.)

**Nota crítica:** 
- Nova Lima (único comparável achado) tem apenas 3 tipos de teste vs 58 em SL — mix incomparável
- Procurar por municípios com 40+ tipos de teste para comparação apple-to-apple
- Filtrar COMPOSIÇÕES SINAPI falsas: se todo item tem quantidade 5.000 em unidades diferentes (M³, HI, HP, L), descartar — é planilha de custo, não compra real

---

## 🔧 Como Executar

### Opção 1: Via Script Python Existente (Recomendado)

**Localização:** `C:/Users/victo/OneDrive/Documentos/Python/projetos/dashboard-contratos/comparativo-pncp/`

**Scripts relevantes:**
- `busca_itens_pncp.py` — busca itens PNCP dado número de contrato
- `extrator_pncp.py` — busca contratos por municipio+ano+escopo
- `embeddings_comparativos.py` — matching semântico (similaridade de cosseno)

**Passo a passo:**

1. **Listar contratos comparativos já baixados:**
   ```bash
   cd C:/Users/victo/OneDrive/Documentos/Python/projetos/dashboard-contratos/comparativo-pncp/
   
   # Ver dados/contratos_comparativos.json
   python -c "import json; d=json.load(open('dados/contratos_comparativos.json')); print(f'Total: {len(d[\"contratos\"])}')"
   ```

2. **Filtrar manualmente por escopo (SQL-like em Python):**
   ```python
   import json
   
   with open('dados/contratos_comparativos.json', 'r', encoding='utf-8') as f:
       dados = json.load(f)
   
   # CTR-5: software
   software = [c for c in dados['contratos'] 
               if any(x in c.get('descObjeto','').upper() 
                      for x in ['SOFTWARE', 'GESTAO INTEGRADA', 'ERP'])
               and 'nobe' not in c.get('descForn','').lower()
               and int(c['numContrato'].split('/')[-1]) >= 2024]  # 2024+
   
   print(f"Software (2024+, sem Nobe): {len(software)}")
   for c in software[:5]:
       print(f"  {c['numContrato']} - {c['descForn'][:40]} - R$ {float(c['vlContrato']):,.0f}")
   
   # CTR-6: reagentes
   kits = [c for c in dados['contratos']
           if 'REAGENTE' in c.get('descObjeto','').upper() 
           and 'KIT' in c.get('descObjeto','').upper()
           and 'scanlab' not in c.get('descForn','').lower()
           and int(c['numContrato'].split('/')[-1]) >= 2024]  # 2024+
   
   print(f"\nKits reagentes (2024+, sem Scanlab): {len(kits)}")
   for c in kits[:5]:
       print(f"  {c['numContrato']} - {c['descForn'][:40]} - R$ {float(c['vlContrato']):,.0f}")
   ```

3. **Para cada comparável encontrado, buscar itens PNCP:**
   ```bash
   # Se numero_controle_pncp_compra estiver disponível:
   python busca_itens_pncp.py <numContrato>
   
   # Exemplo:
   python busca_itens_pncp.py "253/2025"
   ```

### Opção 2: Via Gemini CLI (Rápido)

**Se quiser usar Gemini CLI para análise:**

```bash
cd C:/Users/victo/OneDrive/Documentos/Python/projetos/dashboard-contratos/

gemini -p "
Analise o arquivo contratos.json e encontre:

1. Contratos de SOFTWARE/GESTAO INTEGRADA (2024-2025), sem Nobe:
   - Valor mensal: R$ 150k-500k
   - Municipios: população 150k-350k
   - Retorne: numero, fornecedor, valor, municipio, ano

2. Contratos de KITS REAGENTES (2024-2025), sem Scanlab:
   - Valor mensal: R$ 50k-300k
   - Municipios: população 150k-350k
   - Se houver informação de quantidade/tipos de teste, incluir
   - Retorne: numero, fornecedor, valor, municipio, ano, qtd itens

Priorize resultados de 2025, depois 2024. Se houver menos de 3 em cada categoria, incluir 2023.
" @contratos.json
```

---

## 📊 Análise dos Resultados

### Para CTR-5 (Software)

**Cálculo por comparável:**

```
Per Capita = Valor Mensal / População

SL: R$ 280.503 / 227.397 = R$ 1,2335/hab/mês

Comparável A: R$ <mensal> / <população> = R$ X/hab/mês
Comparável B: R$ <mensal> / <população> = R$ Y/hab/mês
Comparável C: R$ <mensal> / <população> = R$ Z/hab/mês

Mediana = mediana([X, Y, Z])
Desvio SL = (SL - Mediana) / Mediana × 100%
```

**Interpretação:**
- Desvio < -10%: SL está barato
- Desvio entre -10% e +10%: SL está no mercado
- Desvio > +10%: SL pode estar caro (investigar escopo)

### Para CTR-6 (Kits)

**Cálculo por comparável:**

```
Per Capita = Valor Mensal / População

SL: R$ 102.598 / 227.397 = R$ 0,4512/hab/mês

Comparável A: R$ <mensal> / <população> = R$ X/hab/mês
...

Custo Unitário (se disponível):
SL: R$ 1.231.176 / 172.800 un = R$ 6,95/un

Comparável: R$ <valor> / <unidades> = R$ Y/un
```

**Interpretação:**
- Se SL está 30%+ abaixo: provavelmente bom preço
- Se SL está 30%+ acima: possível sobrepreço (mas validar mix de testes)

---

## 📝 Saída Esperada

Criar documento: `ANALISE_PNCP_CTR5_CTR6.md` com:

1. **CTR-5 (Software)**
   - Comparáveis encontrados (n=?)
   - Tabela: Municipio | População | R$/mês | R$/hab/mês | Ano | Fornecedor
   - Mediana per capita
   - Desvio SL vs mediana
   - Veredito: Sobrepreço? Sim/Não/Inconclusivo

2. **CTR-6 (Kits)**
   - Comparáveis encontrados (n=?)
   - Tabela: Municipio | População | R$/mês | R$/hab/mês | Tipos teste | Ano | Fornecedor
   - Mediana per capita
   - Desvio SL vs mediana
   - Validação de mix (SL 58 tipos vs X tipos no comparável)
   - Veredito: Sobrepreço? Sim/Não/Inconclusivo

---

## ⚠️ Checklist de Qualidade

Antes de confirmar resultado, validar:

**Para ambos:**
- [ ] Contratos são de 2024-2025 (mesmo período que SL)
- [ ] Valores estão em reais e completos (não amostra)
- [ ] Populações estão dentro de ±30% de SL (150k-350k)
- [ ] N de comparáveis ≥ 3 para confiança média, ≥ 5 para alta
- [ ] Nenhum outlier > 3× valor de SL (descartá-los)

**Para CTR-5:**
- [ ] Validar se escopo é similar (quantos módulos cada um tem)
- [ ] Procurar informação sobre treinamento/conversão/implantação inclusas
- [ ] Se contrato é ERP educacional (ex: Edutec R$ 6,3M), pode não ser comparável

**Para CTR-6:**
- [ ] Validar quantidade de tipos de teste (não apenas valor agregado)
- [ ] Descartar se compilação SINAPI detectada (mesma qtd, unidades diferentes)
- [ ] Separar: básicos (3-10 testes) vs avançados (40-100 testes)
- [ ] Se SL tem 58 e comparável tem 3, não é apple-to-apple

---

## 📞 Questões Abertas

Se após busca não encontrar dados suficientes:

1. **Há poucos contratos 2024-2025 no PNCP?**
   → Expandir para 2023 (máximo 2 anos atrás)

2. **CTR-5: Software de gestão integrada é raro em pequenos municípios?**
   → Procurar por cidades médias (300k-600k hab) que provavelmente têm sistema integrado

3. **CTR-6: Kits reagentes com detalhamento de quantidade é raro?**
   → Procurar por contratos que citam "número de testes" ou "unidades estimadas" na descrição
   → Alguns municípios publicam via submissões diretas ao SIAFEM, não PNCP

4. **Nenhuma busca retorna?**
   → Manter veredito como "INCONCLUSIVO — dados insuficientes no PNCP"
   → Recomendar levantamento com TCE-MG diretamente

---

## 🔗 Referências Internas

- `pareamento_ctr5_ctr6_final.md` — Análise anterior (comparando com mesma empresa)
- `analise_nobe_253_2025.md` — Detalhe de CTR-5
- `pareamento_ctr5_ctr6_scanlab.md` — Detalhe de CTR-6
- `dashboard-contratos/contratos.json` — Base de dados Sete Lagoas
- `dashboard-contratos/comparativo-pncp/dados/contratos_comparativos.json` — Comparáveis PNCP

---

**Pronto para executar? Invoque outra IA com este documento.**
