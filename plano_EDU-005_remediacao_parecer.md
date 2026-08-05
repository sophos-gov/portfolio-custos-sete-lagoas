# Plano: sanar as pendências do parecer de auditoria independente da EDU-005

## Pendência que este plano resolve

O `parecer_EDU-005_auditoria_independente.md` (emitido em 2026-08-03) aprovou a aritmética da frente
**EDU-005** sem ressalva e levantou 14 achados de método, dado e redação, dos quais 4 de alta
materialidade. A frente está publicada em `cardapio_unificado.html` e `cardapio_unificado_artifact.html`
com faixa piso R$ 599.876,04 · central R$ 666.512,27 · teto R$ 692.103,62, selo "Respaldo médio".

Este plano é diferente dos dois anteriores do projeto: **os números vão mudar**. O parecer não achou
erro de cálculo — achou que o cálculo mede outra coisa diferente do que o texto promete. Corrigir
isso exige reprocessar o modelo, e a faixa nova sairá do reprocessamento, não de edição de texto.

## Decisões tomadas nesta rodada (2026-08-04)

Três bifurcações do parecer foram decididas pelo usuário antes deste plano existir:

- **Escopo — completo, incluindo campo.** Executar redação (§5), higiene de código (§4.6),
  reprocessamento do modelo (§4.1 + §4.3) **e** as quatro verificações bloqueantes do §4.4, em vez
  de apenas preparar os pedidos.
- **§4.2 — consertar o DEA, opção (a).** A fronteira volta a ser o método principal declarado:
  completar o IDEB, rodar modelos separados para educação infantil e ensino fundamental, incluir o
  INSE. O benchmark por cargo continua sendo o filtro de seleção, e por isso a pendência bloqueante
  sobre a origem dos parâmetros **não é extinta por esta decisão** — ela migra para a Onda 2.
- **§4.5 — refazer as três pontas depois do reprocessamento.** Piso, central e teto não se mexem
  agora. A faixa nova é construída de uma vez sobre o modelo estratificado, na Onda 4.

Consequência de ordenação: **nenhum número publicado muda até a Onda 4.** Ondas 0 a 3 produzem
dado, código e evidência; a faixa só é reescrita quando todas as três já fecharam.

---

## Apuração já feita (não refazer)

Verificado diretamente nos arquivos em 2026-08-04, além do que o próprio parecer já registra:

- **As colunas de etapa estão limpas e são usáveis hoje.** `MatriculasEscola_SeteLagoas.xlsx`
  (aba `Matrículas`, 54 × 11) traz `MAT_CRECHE`, `MAT_PRE`, `MAT_INF_TOTAL`, `MAT_FUND_I`,
  `MAT_FUND_II`, `MAT_FUND_TOTAL`, `MAT_EM`, `MAT_EJA` sem nenhum nulo, e `MAT_INF_TOTAL` bate
  exatamente com `MAT_CRECHE + MAT_PRE` nas 54 linhas. Totais: creche 2.172, pré 4.096, fundamental
  7.084. `MAT_EM` e `MAT_EJA` são zero em toda a base. **A estratificação do §4.1 não depende de
  coleta nova nem de limpeza — é troca de coluna.**
- **A única divergência de `MAT_TOTAL` está explicada.** A soma das etapas dá 13.352 contra
  `MAT_TOTAL` de 13.989. A diferença de 637 é exatamente a matrícula da Escola Técnica Municipal
  (`ID_ESCOLA` 31145670), que não tem quadro de apoio na folha e portanto não entra em nenhum corte.
  Não há dado perdido a recuperar.
- **A meta do §4.3 é quantificável: 26, não 54.** Há 26 escolas com `MAT_FUND_TOTAL > 0` e 28
  unidades 100% de educação infantil. A pendência hoje escrita no cardápio ("obter IDEB para as 40
  escolas") é impossível como está; o alvo real é **12 escolas de fundamental sem IDEB carregado**
  (26 com fundamental menos as 14 já presentes em `ideb.xlsx`).
- **`Admissao` e `Tempo` existem, são limpos, e abrem um achado que o parecer não explorou.**
  Entre os 898 registros de apoio da folha, **294 são temporários**. Todos os 294 têm `Admissao`
  preenchida (datetime, zero nulos), todos admitidos em 2025, `Tempo` máximo de 0,874 ano — a foto
  da folha é de aproximadamente dezembro de 2025. Como a LC nº 80/2003, art. 6º, parágrafo único, I
  limita o contrato a 6 meses prorrogáveis **uma única vez**, qualquer um desses contratos ainda
  ativo em agosto de 2026 já ultrapassou o teto legal. O §3.6 do parecer deixa de ser argumento
  jurídico abstrato e vira **teste executável por script**, desde que se obtenha a folha corrente.
- **A coluna `Função` não serve para o §3.5.** Nos 294 temporários de apoio ela vale `' - '` em
  todas as linhas. A distinção entre substituição de efetivo afastado e vaga estrutural não sai
  dessa coluna; precisa de varredura das outras 105 ou de resposta da SME.
- **O crosswalk está limpo hoje.** 52 dos 56 locais de trabalho da folha mapeiam para 52
  `ID_ESCOLA` distintos, zero colisões, menor escore aceito 0,839 e correto. O `assert` de
  bijetividade do §3.13 é **guarda de regressão**, não conserto de bug existente.
- **Há um risco de dupla contagem que o parecer não registra, em sentido oposto ao §3.7.** O custo
  unitário sai de `Proventos` brutos (linha 195), e a folha traz `1/3 FERIAS`, `ABONO NATALICIO`,
  `FERIAS PREMIO INDENIZADAS` e `HORAS EXTRAS 50%` como verbas do próprio mês. Se algum dos 27
  contratos tem essas verbas no mês da foto, multiplicar por 13,333 conta 13º e terço duas vezes.
  Em compensação, a coluna `BASE PREVID.PATRONAL (21%INSS)` está disponível e permite quantificar
  o *upside* de encargos patronais que o §3.7 aponta como ausente. **Ambos precisam ser medidos na
  Onda 2, antes de a faixa nova ser fechada.**
- **Existe template pronto para baixar dado do INEP.** `Educação/Merenda/Python/extrair_escolas_sete_lagoas.py`
  já baixa e parseia os microdados do Censo Escolar (`download.inep.gov.br/dados_abertos/...`,
  latin-1, separador `;`). Serve de base para o extrator de IDEB, de INSE e para a matrícula
  corrente do §4.4.4. Não há, hoje, nenhum script de IDEB em toda a pasta `Educação`.
- **O script é determinístico e re-executável**, com `__main__`, sem semente aleatória (HiGHS é
  determinístico) e caminhos derivados de `__file__`. Não tem argparse: **sobrescreve o xlsx de
  saída silenciosamente a cada execução.** Congelar o baseline é pré-requisito da Onda 0.

---

## Resultado da execução das Ondas 1 e 2 (2026-08-04)

Baseline congelado em `DEA_Eficiencia_Escolas_SeteLagoas_baseline_20260804.xlsx` antes de qualquer
reexecução. Onda 0 **não** foi executada — o script original segue intacto, e a v2 foi escrita como
arquivo separado (`Scripts/dea_eficiencia_escolas_v2.py`), importando os helpers do original em vez
de duplicá-los. A unificação das duas atrás de `--modelo` continua pendente.

### Onda 1

- **IDEB (§4.3): cobertura de 14 para 22 das 26 escolas com matrícula de fundamental.** Script
  `Scripts/baixar_ideb_inep.py`. Endpoint correto é
  `download.inep.gov.br/ideb/resultados/divulgacao_{anos_iniciais,anos_finais}_escolas_2023.zip`
  (102 MB e 74 MB); o caminho `portal_ideb/planilhas_para_download` só serve até 2021.
- **A hipótese do §3.3 do parecer está ERRADA e precisa ser corrigida.** O parecer afirma que "apenas
  14 escolas foram carregadas na base" e que a limitação era da extração. A divulgação estrita de
  2023 do INEP entrega **exatamente 14** escolas municipais de Sete Lagoas com indicador — as mesmas
  14 já em `ideb.xlsx`. A base original estava correta. Verificado ainda por engenharia reversa que
  `ideb.xlsx` usa a **média de anos iniciais e anos finais**, batendo 14/14. O ganho real de
  cobertura não veio de corrigir extração, veio de **aceitar IDEB de anos anteriores** onde 2023 não
  existe: 4 escolas entram com 2019, 3 com 2021, 1 com 2017. Isso é imputação temporal e precisa ser
  declarada como tal — a regra implementada é hierárquica (2023 onde existe, série antiga só na
  lacuna), justamente para não degradar as 14 que já eram sólidas.
- **4 escolas de fundamental nunca tiveram IDEB em ano nenhum**: Virgílio Pacheco, Renato Teixeira
  Guimarães, Adélia Figueiredo e Regina Vitalino Botelho. Três delas são exatamente as que o §3.2 do
  parecer aponta como as piores razões apoio/aluno da rede com corte zero. São unidades pequenas
  (11 a 44 alunos de fundamental) sem participação suficiente no Saeb.
- **INSE (§3.11): BLOQUEADO.** 15 URLs testadas em quatro padrões de diretório e duas buscas web; só
  as notas técnicas em PDF estão localizáveis, nunca as planilhas por escola. O modelo v2 roda sem
  INSE e o risco de equidade do §3.11 permanece aberto. Próxima tentativa possível: espelho do
  `basedosdados` ou pedido direto ao INEP.
- **Matrícula corrente (§4.4.4): resolvida por Censo Escolar 2024**, script
  `Scripts/atualizar_matriculas_censo.py`. Três achados que mudam o texto do cardápio:
  - **A base de matrícula do modelo JÁ É o Censo 2024** — total bate exato (13.352) e 53 das 54
    escolas coincidem. Não havia dado desatualizado a corrigir.
  - **E.M. Isis da Silva Oliveira aparece PARALISADA no Censo 2024**
    (`TP_SITUACAO_FUNCIONAMENTO = 2`), com matrícula nula. **Sobreposto por informação de campo em
    2026-08-04: a SME confirma que a unidade está em funcionamento**, e prevalece o dado de campo
    sobre o Censo. Implementado como `MATRICULA_OVERRIDE = {31386928: 337}` na v2, usando o número
    que o cardápio já publica. Com 337 alunos a escola fica **abaixo** do alvo do benchmark nos dois
    cargos (7 serventes contra alvo de 14; 3 auxiliares de secretaria contra alvo de 5), e o modelo
    dá corte zero por conta própria — não foi preciso criar exceção. **Pendência**: confirmar com a
    SME a matrícula exata e a distribuição por etapa, e corrigir a base de origem, que segue com
    zero. Enquanto a base não for corrigida, o override é a única coisa impedindo o falso positivo.
  - **Duas das quatro unidades sem match são CONVENIADAS, da rede privada**: Creche Flor Amarela
    Brígida Postorino (id 31336629, 79 alunos) e Creche São José Operário (id 31246875, 253 alunos).
    As outras duas — CEMEI Magda Macedo Coelho e CEMEI Padre Adrianus — **não existem como entidade
    INEP em rede nenhuma**. A pendência não é "escola sem registro de matrícula": é servidor
    municipal lotado em unidade conveniada, que é outra pergunta e vai para a SME.

### Onda 2

Script `Scripts/dea_eficiencia_escolas_v2.py`, saída `DEA_Eficiencia_Escolas_SeteLagoas_v2.xlsx`.

- **Segmentação**: 26 escolas com fundamental, 25 puramente infantil, 3 sem matrícula de etapa. As 17
  mistas são todas dominadas por fundamental (share infantil ≤ 0,50), o que torna o corte limpo.
- **Os dois grupos passam folgado na regra n ≥ 3(m+s)**: FUND com 22 DMUs contra 12 exigidas, INF com
  25 contra 9. A amostra degenerada de 14 DMUs do §3.12 deixou de existir.
- **θ com intervalo por jackknife**: FUND 0,8726; INF 0,8164 [IC95% 0,7425–0,8904].
- **Parâmetro com intercepto**, slope recalibrado por bisseção para preservar o alvo agregado da rede
  sob o parâmetro antigo — de modo que a mudança redistribua entre escolas grandes e pequenas sem
  mexer no nível geral do corte.
- **Critério de fechamento da onda: ATENDIDO.** corr(excesso, razão apoio/aluno) foi de **−0,199 para
  +0,412**, e corr(excesso, tamanho do quadro) de **+0,999 para +0,108**. Regina Vitalino Botelho e
  Adélia Figueiredo, que cortavam zero, passam a cortar 1 cada.
- **Dupla contagem do §3.7: imaterial.** Só 7 dos 294 temporários de apoio têm verba não recorrente
  no mês da foto, somando R$ 867,07 sobre R$ 578.766,03 de proventos — 0,15%. O fator 13,333 não
  produz dupla contagem relevante. Meia pendência do §3.7 fecha aqui.
- **Encargo patronal: não mensurável por esta via.** A coluna `BASE PREVID.PATRONAL (21%INSS)` é
  praticamente zero para os temporários (R$ 350,66/mês no agregado), o que indica coluna de RPPS que
  não alcança contrato temporário. O *upside* do §3.7 continua real e continua não quantificado.
- **Bug encontrado e corrigido durante a execução**: a Escola Técnica Municipal tem 637 alunos em
  `MAT_TOTAL` e zero em todas as colunas de etapa, e por isso caiu com escala ponderada nula — o
  mesmo modo de falha do §3.13 que a onda deveria estar eliminando. Corrigido com termo de resíduo a
  peso 1,0 em `alunos_ponderados`.

### Dois achados que travam a publicação do número novo

**1. A rede está 171 posições ABAIXO do alvo do próprio benchmark.** Somando as 54 escolas:
853 servidores de apoio contra alvo de 1.024. Todos os cargos, sem exceção, estão em déficit
agregado — servente −44, auxiliar de secretaria −74, vigia −23, assistente de biblioteca −17,
assistente de turno −14. As 71 posições de excesso convivem com 242 posições de déficit em escolas
abaixo do alvo. **O benchmark é aplicado só como teto, nunca como piso.** Isso vale igualmente para a
v1, onde ficava mascarado pelo freio do DEA. Pelo próprio parâmetro da frente, a rede precisa de
mais apoio, não de menos — o que reposiciona EDU-005 como argumento de **realocação**, não de
economia, ou então reabre a pendência bloqueante sobre a origem do parâmetro, que pode simplesmente
não descrever esta rede.

**2. θ_INF (0,8164) e θ_FUND (0,8726) não são comparáveis entre si.** O modelo de infantil tem 2
produtos e o de fundamental tem 3, e em DEA um conjunto menor de produtos deprime o escore por
construção. Boa parte do corte maior na educação infantil é artefato de dimensionalidade, não
ineficiência medida. **Não usar essa diferença como evidência de que a creche é menos eficiente.**

### Números da v2 (NÃO publicáveis como estão)

| Indicador | v1 (publicado) | v2 |
|---|---|---|
| DMUs medidas | 14 | 47 |
| Demissões | 27 | 41 |
| Economia mensal | R$ 51.909,07 | R$ 78.338,14 |
| Economia anual ×13,333 | R$ 692.103,62 | R$ 1.044.482,42 |

Distribuição dos 41 cortes: **34 no grupo de educação infantil** (R$ 64.681,94/mês) e **7 no grupo de
ensino fundamental** (R$ 13.656,20/mês). A Isis contribui com **zero** após o override de matrícula.

A concentração na educação infantil é o ponto a tratar com cuidado: 83% dos cortes vêm do grupo cujo
θ está deprimido por dimensionalidade (problema 2 acima), não por ineficiência medida. Antes de
publicar, é preciso ou equalizar a dimensionalidade dos dois modelos, ou declarar explicitamente que
a comparação entre grupos não sustenta leitura de "creche menos eficiente".

### Contexto que muda o enquadramento (informado pelo usuário em 2026-08-04)

O município está no **limite prudencial de despesa com pessoal** — 95% do limite da LRF (art. 22,
parágrafo único). Isso torna a redução obrigação legal, não escolha de gestão, e responde à questão
levantada acima sobre "realocação versus economia": o déficit de 171 posições contra o alvo do
benchmark **não pode ser preenchido de qualquer forma**, porque no limite prudencial vigoram as
vedações de provimento de cargo, contratação e horas extras. A ressalva do parecer sobre economia
transitória (§3.6, troca de temporário por efetivo mais caro) também perde força pelo mesmo motivo.

Isso **não elimina** a necessidade de divulgar o déficit agregado: ele continua sendo a objeção mais
previsível do sindicato e da câmara, e a resposta correta é declará-lo junto com o enquadramento de
LRF, não omiti-lo. Verificar o percentual exato no RGF antes de citar o número.

---

## Reescopo da frente (2026-08-04, decisão do usuário)

Depois de ver o resultado da Onda 2, o usuário redefiniu o alvo: **sem corte em creche**, foco em
eficientizar o **quadro administrativo** das escolas grandes. Isso não é ajuste de parâmetro, é outra
frente — e obrigou a trocar a metodologia, não só o filtro.

### O que o dado mostrou sobre a premissa

**Escolas grandes são as mais enxutas, não as mais inchadas.** Administrativos por 100 alunos:
1,94 nas 15 maiores escolas de fundamental, 2,30 nas demais, 0,96 na educação infantil. Das 15
maiores, **14 estão abaixo** do alvo do parâmetro antigo (Galvão tem 9 administrativos contra alvo de
17; Nádia Lúcia tem 7 contra 12). Na rede inteira: 215 administrativos contra alvo de 316, com
excesso somado de 3 posições. **Pelo parâmetro da frente anterior, cortar administrativo rende zero.**

### A saída: abandonar o parâmetro e comparar a rede consigo mesma

Em vez de brigar com um parâmetro cuja origem nunca foi documentada — a pendência bloqueante que
segue aberta desde a versão original —, o padrão passa a ser derivado da própria rede: escolas de
ensino fundamental comparadas entre si, com referência no **quartil inferior de administrativos por
aluno**. É a opção (b) do §4.2 do parecer, que a chama de "mais rápida e mais honesta", e tem a
vantagem decisiva de ser **comprovadamente exequível**: o padrão não é meta teórica, é o que 7 das 25
escolas já praticam hoje.

O escore DEA do grupo de fundamental passa a ser camada de **validação**, não de seleção — o papel
que o §4.2(b) reserva a ele.

Script: `Scripts/benchmark_administrativo_pares.py`.
Saída: `Benchmark_Administrativo_Fundamental.xlsx`.

### Escopo final

| | |
|---|---|
| Dentro | Auxiliar de Secretaria, Assistente de Turno, Assistente de Biblioteca, Técnico de Biblioteca, Auxiliar de Almoxarifado — **só em escolas de ensino fundamental** |
| Fora | Servente escolar (era 92% da frente anterior), vigia de educação, e todo o grupo de educação infantil |

### Resultado com o padrão p25 (1,802 adm por 100 alunos)

| Indicador | Valor |
|---|---|
| Escolas no universo | 25 |
| Escolas afetadas | 10 |
| Posições acima do padrão | 21 |
| Cortáveis (contrato temporário) | **18** |
| Presas em vínculo efetivo (só atrição) | 3 |
| Economia mensal | **R$ 39.505,26** |
| Economia anual ×13,333 | **R$ 526.723,63** |

Dos 18 cortes, 16 são Auxiliar de Secretaria. Maior caso isolado: E.M. Professor Raymundo Gravito,
com 3,759 administrativos por 100 alunos — mais que o dobro do padrão da rede — e 4 posições
cortáveis.

**Ressalva sobre a premissa das "escolas grandes":** as 10 unidades afetadas são de porte médio (221
a 439 alunos), não as maiores. As três maiores da rede (Galvão 760, Juca Dias 596, Nádia Lúcia 505)
**não sofrem corte** porque já operam abaixo do padrão. O benchmark seleciona por desproporção, não
por tamanho — e é isso que o torna defensável.

Sensibilidade ao padrão, com custo real: p50 R$ 172.989/ano (6 cortes) · **p25 R$ 526.724/ano (18)** ·
p10 R$ 749.620/ano (26) · escola mais enxuta R$ 836.115/ano (29).

---

## Resultado das Ondas 3 e 4 (2026-08-04)

Decisão do usuário nesta rodada: **só esgotar automação**, sem redigir ofícios; **não usar** o teste
de tempo de contrato enquanto a folha corrente não chegar; e **reescrever o cardápio com as
pendências declaradas**.

### Onda 3 — automação

- **Fonte de recurso (§3.14): RESOLVIDO por dado local**, sem pedir nada à prefeitura. Script
  `Scripts/fonte_recurso_contratos_sicom.py` sobre o SICOM 2025 já extraído. Da contratação por
  tempo determinado da função Educação (R$ 63,88 mi empenhados em 2025): **68,9% pela fonte 1.500 —
  recursos não vinculados de impostos** e **31,1% pela fonte 1.540 — transferências do Fundeb**.
  Leitura: a parcela do Fundeb é integralmente carimbada e reduzi-la pressiona o mínimo de 70%; a
  parcela de impostos computa no piso de 25% quando aplicada em educação, então a liberação de caixa
  depende da margem com que o município supera esse piso. **Ressalva**: o dado é agregado da função
  Educação, não atribuível contrato a contrato.
- **Concurso vigente (§3.6): PARCIAL.** Três tentativas — portal `concursos.setelagoas.mg.gov.br`
  retornou HTTP 403, e duas buscas trouxeram só parte. Confirmado que **assistente de biblioteca e
  técnico de biblioteca** constam de concurso da prefeitura, e que houve homologação em julho de
  2025. **Não confirmado para auxiliar de secretaria**, que é justamente 16 dos 18 cortes. Segue
  como pendência, com a ressalva de que a vedação de provimento do limite prudencial suspende o
  risco enquanto durar.
- **Natureza de cada contrato e folha corrente**: não automatizáveis, seguem com a SME. Nenhum
  documento formal foi redigido nesta rodada, por decisão.

### Onda 4 — cardápio reescrito

Bloco `id="EDU-005"` reescrito em `cardapio_unificado.html`, artifact regenerado por
`gerar_artifact.py` e `--check` OK. Conferido que as duas variantes carregam os mesmos valores e que
o `<body>` é idêntico.

Alterações fora do bloco, decorrentes do reescopo:

- Entrada do sumário e texto da capa da Parte I reescritos.
- **Totais somados da Parte I recalculados**: piso de R$ 5.230.657,41 para **R$ 4.800.409,13**,
  central de R$ 6.209.982,84 para **R$ 6.070.194,20**, teto de R$ 6.439.140,74 para
  **R$ 6.501.280,40**. Aparecem em dois lugares cada (capa geral e capa da Parte I).
- O box protetor da frente deixou de ser o "piso-zero" e passou a declarar o achado do déficit
  agregado: a rede opera com 215 administrativos contra 316 que o parâmetro anterior indicava, e a
  frente decorre de dispersão entre unidades, não de excesso agregado.

Selo mantido em `selo-media`. Pelo critério de fechamento deste plano, ele só sobe com a Onda 3
fechada, e as duas verificações que dependem da SME continuam abertas.

**Não republicado como Artifact.** Os números mudaram muito e não passaram por revisão humana; a
republicação em `https://claude.ai/code/artifact/f4f85244-7425-4978-8705-532e911bd228` fica para
depois da conferência do usuário.

---

## Alocação de modelos de IA

A regra é atribuir por natureza da tarefa, não por tamanho. Julgamento jurídico, desenho
metodológico e prosa de cliente vão para Opus; especificação fechada vira código em Sonnet;
volume mecânico e conferência vão para Haiku; leitura de base larga e documentação externa vai
para Gemini Flash, conforme o protocolo de fallback já estabelecido no `CLAUDE.md` global.

| Modelo | Onde usar nesta remediação | Por quê |
|---|---|---|
| **Opus 5** | Desenho da ponderação por etapa e da função de produção da educação infantil (Onda 2); decisão da estrutura da faixa nova (Onda 4); reescrita do bloco EDU-005 no cardápio com as skills `humanizer` e `mckinsey-consultant`; redação das consultas formais à SME e à PGM com a skill `direito-administrativo-skill`; conferência final número a número contra a planilha nova. | São os pontos onde errar custa credibilidade perante TCE-MG e câmara municipal. O `CLAUDE.md` do projeto já fixa Opus + as duas skills para toda reescrita do cardápio. |
| **Sonnet 5** | Refatoração de `dea_eficiencia_escolas.py` (estratificação, dois modelos, parâmetro com intercepto, jackknife, argparse, itens de higiene do §4.6); `baixar_ideb_inep.py`; `baixar_inse_inep.py`; `atualizar_matriculas_censo.py`; `classificar_contratos_temporarios.py`; script de comparação baseline × novo. | Especificação fechada, resultado verificável por execução. Não precisa de julgamento aberto. |
| **Haiku 4.5** | Executar os scripts e coletar saídas; extrair células da planilha nova para a tabela de conferência; rodar `gerar_artifact.py --check` e diffar as duas variantes do HTML; atualizar as linhas de índice em `init.md`, `CLAUDE.md` e `revisao_cardapio.html`. | Volume mecânico, verdade verificável por comparação direta. Gastar Opus aqui é desperdício. |
| **Gemini 2.5 Flash** (skill `gemini-robust`, `generate_with_retry_and_fallback`, `fallback_to_flash=True`) | Varredura das 106 colunas × 3.463 linhas da folha atrás de qualquer marcador de afastamento ou substituição (§3.5), antes de recorrer à SME; leitura dos dicionários e layouts de IDEB/INSE do INEP; leitura dos extratos do SICOM na busca de fonte de recurso (§3.14). | Padrão do projeto para contexto largo e barato. Flash é o default; Pro só entra se o extrato do SICOM estourar 1M de tokens, e sempre com fallback. |

Modelo externo (Gemini Antigravity ou equivalente) **não deve fechar conclusão sozinho** nesta
frente. O incidente registrado no `plano_EDU-004_confirmacao_legal.md` — reintrodução de uma citação
legal já marcada como errada — é precedente suficiente: qualquer saída de ferramenta externa entra
aqui como insumo a conferir por leitura direta, nunca como veredito.

---

## Ordem de execução

Automação primeiro em cada passo, por padrão do projeto: três tentativas documentadas antes de
qualquer caminho manual.

### Onda 0 — Congelar o baseline e limpar o código (nenhum número pode se mover)

**Modelo: Sonnet 5 para o código, Haiku 4.5 para executar e diffar.**

1. **Congelar.** Copiar `DEA_Eficiencia_Escolas_SeteLagoas.xlsx` para
   `DEA_Eficiencia_Escolas_SeteLagoas_baseline_20260804.xlsx`. O script sobrescreve a saída sem
   aviso; sem essa cópia não há como provar que a higiene não moveu nada.
2. **Adicionar `argparse`** com `--out` e `--modelo {atual,estratificado}`, para que as variantes
   rodem lado a lado em vez de se sobrescreverem.
3. **Aplicar os itens do §4.6 que não tocam resultado:** corrigir a docstring das linhas 17-19, que
   descreve um método (`teto 0,0690 serv./aluno`) diferente do executado na linha 297
   (`(1 − θ_médio) × apoio`); remover a constante morta `TETO_REDE` da linha 72; padronizar o fator
   anual em 13,333 (EDU-001 usa 13,3); acrescentar `assert` de bijetividade em
   `construir_crosswalk`; acrescentar guarda de sanidade para `MAT_TOTAL == 0` no grupo B, espelhando
   o filtro que a linha 271 já aplica ao grupo A; corrigir o rótulo de método, que hoje devolve
   `"DEA (θ médio)"` para escolas com quadro de apoio zero, onde método nenhum foi aplicado.
4. **Provar a neutralidade.** Rodar e comparar célula a célula contra o baseline. As cinco abas
   têm de sair idênticas, com **uma exceção esperada e única**: o teto muda de R$ 692.103,62 para
   R$ 692.103,63 por causa do fator 13,333, que é o arredondamento de um centavo já documentado no
   `CLAUDE.md`. Qualquer outra diferença é bug introduzido e a onda não fecha.
5. **Reconciliar os parâmetros incompatíveis do §3.13.** A soma dos benchmarks por cargo
   (0,0414 + 0,0138 + 3 × 0,0063 = 0,0741) excede o teto de rede declarado de 0,0690. Documentar
   qual dos dois é o parâmetro de fato e por quê — isso alimenta diretamente a pendência bloqueante
   da Onda 2.

### Onda 1 — Completar as bases públicas do INEP

**Modelo: Sonnet 5 para os scripts, Gemini Flash para ler os layouts do INEP.**

1. **`baixar_ideb_inep.py`.** Baixar a divulgação de IDEB por escola (anos iniciais e finais) do
   portal de dados abertos do INEP e fazer o join por código INEP, que já é a chave `ID_ESCOLA` do
   modelo. **Alvo: as 12 escolas de fundamental hoje ausentes de `ideb.xlsx`.** Se o INEP divulgar
   IDEB para todas as 26, a imputação deixa de existir para o ensino fundamental. Se algumas não
   tiverem indicador por participação insuficiente no Saeb, registrar quais e por quê — a limitação
   passa a ser documentada em vez de presumida.
2. **`baixar_inse_inep.py`.** Baixar o Indicador de Nível Socioeconômico por escola (§3.11) e juntar
   pela mesma chave. Entra na Onda 2 como variável não discricionária.
3. **`atualizar_matriculas_censo.py`.** Resolver o §4.4.4 por dado público em vez de por pergunta à
   SME: extrair a matrícula corrente da E.M. Isis da Silva Oliveira (hoje zero na base, 337 alunos
   reais) e das quatro unidades em `MANUAL_UNMATCHED` (CEMEI Magda Macedo Coelho, CEMEI Padre
   Adrianus, Creche Flor Amarela Brígida Postorino, Creche São José Operário) direto dos microdados
   do Censo Escolar. Reaproveitar `extrair_escolas_sete_lagoas.py`, que já resolve download, encoding
   e parsing.
4. **Se o download direto falhar**, tentar na ordem: (a) API de dados abertos do INEP,
   (b) espelho do pacote `basedosdados`, (c) documentar o bloqueio de allowlist e pedir ajuste.
   Documentar cada tentativa antes de considerar qualquer caminho manual.

### Onda 2 — Remodelar (§4.1 + §4.2a + parte técnica do §4.6)

**Modelo: Opus 5 desenha, Sonnet 5 implementa, Haiku 4.5 executa.**

1. **Separar os dois modelos.** Educação infantil e ensino fundamental são funções de produção
   distintas e passam a rodar separadamente:
   - *Fundamental* (26 escolas): insumo apoio, produtos `MAT_FUND_TOTAL` e IDEB, com INSE como
     variável não discricionária. Com o IDEB completo da Onda 1, este modelo mede de verdade.
   - *Infantil* (28 escolas): IDEB não existe para a etapa e **não vai existir** — não é dado
     faltando, é incomensurabilidade, como o §3.1 estabelece. Produtos passam a ser `MAT_CRECHE` e
     `MAT_PRE` separados, que já estão na base. Opus decide se a ponderação usa os fatores de
     custo-aluno do Fundeb como referência de peso relativo, e registra a justificativa — é a única
     escolha metodológica aberta desta onda.
2. **Parâmetro com intercepto** (§3.10): `alvo = a + b × alunos` para vigia de educação, assistente
   de turno e auxiliar de secretaria, cujo dimensionamento escala com perímetro, turno e prédio, não
   com matrícula. O `math.ceil` da linha 318 já cria um piso implícito de 1, mas por acidente;
   substituí-lo por intercepto explícito preserva o efeito elogiado no §2 e o torna defensável.
3. **Incerteza sobre θ** (§3.12): jackknife como mínimo, bootstrap de Simar-Wilson se o tempo
   permitir. A faixa nova precisa publicar θ com intervalo, não como estimativa pontual.
4. **Medir os dois efeitos de custo levantados na apuração acima:** quanto dos `Proventos` dos
   contratos selecionados é 13º, terço de férias ou hora extra do próprio mês (risco de dupla
   contagem contra o fator 13,333), e quanto vale o encargo patronal disponível em
   `BASE PREVID.PATRONAL (21%INSS)` (*upside* do §3.7). Os dois entram na Onda 4 como componentes
   explícitos da faixa, não embutidos.
5. **Diagnóstico de aceitação da onda.** Recalcular as duas correlações do §3.2 sobre o resultado
   novo: excesso estimado contra tamanho do quadro (hoje 0,999) e contra razão apoio/aluno
   (hoje −0,199). **Se a segunda continuar negativa, o modelo continua freando na direção errada e
   a opção (a) do §4.2 falhou** — nesse caso a decisão volta ao usuário, com a opção (b) sobre a
   mesa. Teste concreto de sanidade: Regina Vitalino Botelho, com 1 servidor de apoio para cada 3,3
   alunos e corte zero hoje, precisa aparecer no resultado novo.
6. **Documentar a origem dos parâmetros por cargo.** Continua sendo pendência bloqueante mesmo na
   opção (a), porque quem seleciona posições segue sendo o benchmark. Alimentada pelo item 5 da
   Onda 0.

### Onda 3 — Verificações de campo (§4.4, bloqueantes antes de qualquer comunicação a escola)

**Modelo: Sonnet 5 e Gemini Flash tentam automatizar; Opus 5 redige o que sobrar como consulta formal.**

1. **Natureza de cada contrato temporário** (§3.5) — substituição de efetivo afastado *versus* vaga
   estrutural. A coluna `Função` está vazia; antes de perguntar à SME, Gemini Flash varre as 106
   colunas da folha atrás de qualquer marcador de afastamento, licença ou vínculo de substituição, e
   testa o cruzamento inverso (efetivo lotado na mesma escola e cargo com proventos compatíveis com
   licença). Só o que não sair daí vira pergunta.
2. **Tempo de contrato contra o limite legal** — achado novo desta apuração, e o mais barato dos
   quatro. `classificar_contratos_temporarios.py` calcula, para cada um dos 294 temporários de apoio,
   os meses decorridos desde `Admissao` na data de referência, e classifica contra os 6 meses
   prorrogáveis uma vez do art. 6º, parágrafo único, I. **Requer a folha corrente**: a disponível é
   de dezembro de 2025 e todos os contratos aparecem com menos de 12 meses nela. Pedir a folha
   atualizada à SME é o primeiro item da consulta formal, porque destrava também os itens 1 e 3.
3. **Concurso vigente ou cadastro de reserva para Servente Escolar** (§3.6). Determina se a economia
   é permanente ou se apenas troca temporário por efetivo mais caro em 24 a 36 meses. Tentar
   automatizar contra o portal da prefeitura e o Diário Oficial do Município, reaproveitando o
   acesso ao SAPL já usado em `buscar_decretos.py` na rodada do EDU-004.
4. **Fonte de recurso de cada contrato** (§3.14) — MDE, Fundeb 70%, Fundeb 30% ou recursos próprios.
   Determina se a economia vira folga fiscal ou apenas realocação dentro da vinculação
   constitucional. Tentar primeiro pelos extratos do SICOM, com a skill `sicom-auditoria-educacao` e
   leitura por Gemini Flash; o que não se resolver aí entra na consulta.
5. **Consulta formal.** Opus 5 redige, com `direito-administrativo-skill`, um documento único à SME
   pedindo folha corrente, natureza de cada um dos contratos selecionados e fonte de recurso, e um
   segundo à PGM sobre o enquadramento de servente escolar como profissional da educação básica para
   fins dos 70% do Fundeb (art. 26 da Lei nº 14.113/2020 c/c art. 61 da LDB), que o parecer registra
   como não pacífico entre tribunais de contas.

### Onda 4 — Reconstruir a faixa e reescrever o cardápio

**Modelo: Opus 5 escreve e confere; Haiku 4.5 sincroniza e indexa.**

1. **Montar a faixa nova** sobre a estrutura do §4.5, agora com os insumos das Ondas 2 e 3:
   piso sobre contratos confirmados escola a escola, líquido de rescisão e com execução parcial no
   ano 1; central sobre o benchmark estratificado por etapa; teto como limite superior teórico do
   modelo integral. Se as verificações do §4.4 não tiverem retornado até aqui, o piso é **R$ 0**,
   aplicando a EDU-005 o mesmo critério que o documento já aplica a três frentes da Saúde — e isso
   resolve, de uma vez, a tensão do §3.8 entre o box "piso-zero" e um piso de R$ 599 mil.
2. **Aplicar os cinco ajustes de redação do §5:** separar a pendência de IDEB em duas (trivial para
   fundamental, impossível para infantil); declarar a composição por etapa das escolas cortadas
   (80,5% educação infantil, parâmetro vindo exclusivamente de fundamental); nomear o que o modelo
   faz no grupo imputado; acrescentar as duas pendências ausentes (concurso e fonte de recurso);
   acrescentar o respaldo legal favorável do art. 6º, parágrafo único, I da LC nº 80/2003, que foi
   localizado e lido no texto integral — diferente do que ocorreu no EDU-004.
3. **Corrigir a descrição do caso Isis** (§3.13, nota final): o cardápio diz que "todo o seu quadro
   de apoio foi lido como excesso". O benchmark leu os 10, o teto DEA conteve em 1,1 e o corte final
   foi 1. A conclusão está certa; o mecanismo descrito, não. Registrar também que há **duas** escolas
   com matrícula zero na base — Isis e o CAIC —, e que o CAIC só não gerou falso positivo porque tem
   quadro de apoio zero.
4. **Reenquadrar o acoplamento com EDU-003** (§4.7): hoje a interação aparece só como risco. Se
   EDU-003 elimina a segunda refeição diária, a carga de servente cai e o excesso medido depois fica
   maior e mais defensável. Sequenciar EDU-003 → remedição → EDU-005 fortalece as duas frentes.
5. **Registrar o benefício de LRF** (§3.14, nota favorável): qualquer que seja a fonte de recurso,
   redução de despesa de pessoal melhora a posição no limite do art. 169 da CF e dos arts. 19-20 da
   LRF. É real, mensurável e hoje não está no documento.
6. **Conferência número a número** de toda a frente contra a planilha nova, por Opus, conforme o
   passo 4 do pipeline do `CLAUDE.md`. Nenhum valor entra no HTML sem bater com a célula de origem.
7. **Sincronizar e publicar.** Editar **somente** `cardapio_unificado.html`, rodar `gerar_artifact.py`,
   conferir com `--check`, e republicar na mesma URL
   (`https://claude.ai/code/artifact/f4f85244-7425-4978-8705-532e911bd228`). Localizar o bloco por
   `id="EDU-005"`, nunca por linha absoluta. Atualizar a linha de EDU-005 em `revisao_cardapio.html`
   para status de revisão pendente, e as entradas de índice em `init.md` e `CLAUDE.md`.

---

## Critério de fechamento

- **Onda 0 fecha** quando a planilha regenerada bate célula a célula com o baseline, com a única
  diferença esperada de um centavo no teto pelo fator 13,333. Diferença adicional = bug, e a onda
  não fecha.
- **Onda 1 fecha** quando `ideb.xlsx` cobrir as 26 escolas de fundamental ou quando as ausências
  estiverem nominalmente justificadas pela divulgação do INEP, e quando a matrícula corrente da Isis
  e das quatro unidades sem match estiver na base.
- **Onda 2 fecha** com a correlação entre excesso estimado e razão apoio/aluno **positiva**. Se
  continuar negativa, a opção (a) do §4.2 falhou tecnicamente, a decisão volta ao usuário com a
  opção (b) sobre a mesa, e o selo não sobe.
- **Onda 3 fecha** com as quatro verificações respondidas ou com as consultas formais protocoladas e
  a resposta pendente registrada como tal no cardápio. Enquanto não fecharem, **nenhuma comunicação
  a escola ou a servidor pode partir desta frente.**
- **Selo.** Com as Ondas 1 a 3 fechadas e os cinco ajustes aplicados, o selo pode subir de
  `selo-media` para `selo-mediaforte` **na parte de ensino fundamental**. A parte de educação
  infantil permanece em "Respaldo médio" enquanto o modelo dela não tiver produto validado — IDEB
  não existe para a etapa e não vai passar a existir.
- **Números.** A faixa só é reescrita na Onda 4, de uma vez, e a estrutura nova (inclusive um
  eventual piso R$ 0) é decisão do usuário sobre o resultado do reprocessamento, não correção
  editorial que eu aplique por conta própria.

---

## Verificação

Como provar, ao final, que a remediação funcionou:

1. `python dea_eficiencia_escolas.py --modelo atual --out baseline_check.xlsx` reproduz o baseline
   congelado — prova que a refatoração não quebrou o caminho antigo.
2. `python dea_eficiencia_escolas.py --modelo estratificado --out DEA_..._v2.xlsx` roda sem erro e
   produz as cinco abas com a aba `Metodologia` descrevendo o método efetivamente executado.
3. As duas correlações do §3.2, recalculadas sobre a saída nova, entram na aba `Metodologia`.
4. Regina Vitalino Botelho, Adélia Figueiredo e Renato T. Guimarães — as três piores razões
   apoio/aluno da rede, hoje com corte zero — aparecem no resultado novo com corte compatível com a
   desproporção que apresentam.
5. `python gerar_artifact.py --check` sai com código 0.
6. Diff do `<body>` das duas variantes do HTML sem diferença além da quebra de linha pré-existente
   entre `</style>` e `<nav>`.
7. Todo valor no bloco EDU-005 do HTML rastreável a uma célula nomeada da planilha nova.

---

## Arquivos e fontes envolvidos

- `custos/parecer_EDU-005_auditoria_independente.md` — origem de todas as pendências deste plano.
- `Educação/Scripts/dea_eficiencia_escolas.py` — alvo das Ondas 0 e 2. Linhas de referência: 17-19
  docstring divergente, 72 `TETO_REDE`, 195 custo por `Proventos` brutos, 204-230 crosswalk, 271
  filtro do grupo A, 297 excesso do grupo B, 318 `math.ceil` do alvo, 501-502 `__main__`.
- `Educação/DEA_Eficiencia_Escolas_SeteLagoas.xlsx` — congelar como baseline antes de qualquer
  execução; o script sobrescreve sem aviso.
- `Educação/Dados/DadosGerados/MatriculasEscola_SeteLagoas.xlsx` — colunas de etapa, prontas para uso.
- `Educação/Dados/DadosGerados/ideb.xlsx` — 14 linhas hoje; alvo de 26 na Onda 1.
- `Educação/Dados/DadosGerados/professor por escola.xlsx` — 3.463 × 106; `Admissao`, `Tempo`,
  `Tipo Contrato`, `BASE PREVID.PATRONAL (21%INSS)`. **Precisa de versão corrente** para a Onda 3.
- `Educação/Merenda/Python/extrair_escolas_sete_lagoas.py` — template de download do INEP, reusar
  nos três extratores da Onda 1.
- `Educação/Dados/folha/auditoria-folha-sete-lagoas/legislacao_full/lc_80_03.txt` — LC nº 80/2003,
  texto integral já baixado. Art. 3º, XVIII; art. 4º e Anexo I; art. 6º, parágrafo único, I e II;
  art. 27, IV.
- `custos/gerar_artifact.py` — gerar a variante `_artifact`. Editar sempre o arquivo principal e
  rodar o script; nunca editar o `_artifact` diretamente.
- `custos/cardapio_unificado.html` e `custos/cardapio_unificado_artifact.html`, bloco `id="EDU-005"`
  — onde o resultado final é aplicado, sempre em par, localizando por `id` e não por linha absoluta.
- `custos/revisao_cardapio.html`, `custos/init.md`, `custos/CLAUDE.md` — índices e papel de trabalho
  a atualizar no fechamento.

---

*Plano emitido em 2026-08-04, sobre o parecer de 2026-08-03. Escopo, método e tratamento da faixa
decididos pelo usuário na abertura desta rodada.*
