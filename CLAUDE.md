# CLAUDE.md — Projeto custos

## Propósito

Consolidar os "cardápios de soluções para corte de custos" produzidos em três projetos
separados (educação Sophos, saude7l, dashboard-contratos) em documentos unificados de
entrega formal ao cliente (Prefeitura de Sete Lagoas/MG). Este projeto não gera dado
novo — ele monta, reescreve e empacota o que os outros três já produziram.

## Estado atual (2026-07-30)

- `cardapio_unificado.html` (arquivo completo, abre direto no navegador) e
  `cardapio_unificado_artifact.html` (mesma coisa, sem DOCTYPE/html/head/body —
  formato exigido pela ferramenta Artifact) — primeira versão consolidada.
- Publicado como Artifact privado: https://claude.ai/code/artifact/f4f85244-7425-4978-8705-532e911bd228
- Fontes desta versão: Educação (4 frentes), Saúde v0.9-pareamento-sicom-rec001 (9
  frentes), Contratos (6 casos do deck `apresentacao_contratos_ativos_robustos.html`).
- Ainda precisa de revisão humana linha a linha antes de ir ao cliente — é reescrita de
  IA sobre conteúdo de auditoria sensível (ver seção Pendências).
- **2026-07-30 (tarde):** adicionada seção "Achado complementar — comparação item a
  item" na Parte III (Contratos), com o achado do pipeline generalizado de itens de
  `dashboard-contratos/comparativo-pncp` (`PLANO_ITENS_MULTIPLOS.md` v3, Lotes 0-3):
  contrato 004/2026 (hortifrutigranjeiros PNAE), item couve-flor, R$ 17,53/kg em Sete
  Lagoas contra R$ 9,09/kg em ata de Araguari/MG, confirmado por LLM item a item —
  economia R$ 15.192/ano, cobertura de só 2,4% do valor do contrato (1 de 19 itens).
  Seção deliberadamente separada dos 6 casos originais (pergunta diferente: item
  contra item, não contrato contra contrato; nenhum dos itens checados passou pela
  revisão de contrato inteiro). Artifact republicado na mesma URL.
- **2026-07-31:** migrados os 24 contratos de item único restantes para o pipeline de
  itens múltiplos (ver `dashboard-contratos/comparativo-pncp/PLANO_ITENS_MULTIPLOS.md`,
  seção "Migração dos 23/24 contratos"). Nenhum achado novo — o cardápio não mudou.
- **2026-07-31:** criado `revisao_cardapio.html` — papel de trabalho interativo para a
  revisão humana linha a linha (as 21 frentes das 3 secretarias, com controle de status
  Pendente/Conferido/Divergência, notas e exportação em Markdown; estado salvo no
  navegador via localStorage). Publicado como Artifact:
  https://claude.ai/code/artifact/8f2c8b59-a5c4-40c1-a9c4-44780203742d. Não substitui a
  revisão — só organiza. A revisão em si continua pendente.
- **2026-07-31 (rodada de correções pós-revisão):** aplicadas as 6 correções apontadas
  pelo usuário na primeira passada de `revisao_cardapio.html` (via `prototipo_correcoes.html`,
  comentários do usuário, plano em `~/.claude/plans/coment-rios-prot-tipo-wild-feather.md`).
  Nenhum número de faixa mudou em nenhuma das 6. Resumo:
  - **EDU-003**: título e proposta agora deixam explícito que o corte é só da modalidade
    "Projeto Matutino/Vespertino" (contraturno recreativo) — a Creche Integral, modalidade
    contábil separada, nunca entrou no cálculo e continua fora.
  - **HOSP-002**: promovido para o mesmo nível da faixa piso/central/teto o aviso de que o
    cálculo só captura a diferença de repasse do SUS por parto (não inclui centro cirúrgico,
    anestesia, UTI neonatal) — antes só aparecia enterrado em "Riscos a monitorar". A pendência
    de custo operacional completo foi atualizada com o resultado real da investigação: o
    projeto saude7l concluiu que o HNSG provavelmente não é aderente ao PNGC/ApuraSUS, nenhum
    dado veio por essa via; próximo passo real (não executado) é levantar a tabela SIGTAP.
  - **Removido o achado couve-flor** (`CTR-ITENS`, contrato 004/2026) do cardápio do cliente —
    a pedido do usuário. Continua no deck interno `apresentacao_contratos_ativos_robustos.html`
    de `dashboard-contratos`; nota datada em `PLANO_ITENS_MULTIPLOS.md` registra a remoção.
  - **CON-003**: sem edição — apurado que o gap que o usuário lembrava (especialistas vs.
    atenção básica) já está coberto em CON-001 (Neurologia) e CON-002 (Anestesiologia), não
    em CON-003 (contrato 114/2022, ESF/Atenção Básica).
  - **EDU-004**: confirmado por leitura direta do texto integral que a LC nº 108/2006 (citada
    antes) trata só de gratificação de cargos de apoio administrativo, nada a ver com
    professores — erro herdado dos documentos de planejamento originais da Educação. Lida a
    íntegra das 20 leis complementares que alteram a LC nº 80/2003 (a PCCV real da Educação,
    `Educação/Dados/folha/auditoria-folha-sete-lagoas/legislacao_full/`): confirmado o
    mecanismo de extensão de carga horária de 20 para 40 horas (dobra, art. 27 §7º, incluído
    pela LC nº 253/2021), mas **não encontrado** nenhum dispositivo específico de "docente
    itinerante por polos geográficos", que é o mecanismo que a frente propõe. Citação trocada
    para LC nº 80/2003 como base geral, pendência bloqueante explícita registrada, selo
    rebaixado de "Respaldo forte" para "Respaldo médio" (`selo-media`). **Pendência em aberto:**
    falta confirmação jurídica formal do dispositivo exato de itinerância antes de comunicar a
    mudança aos professores.
  - **Fechamento/Metodologia**: reescrito eyebrow/título/abertura da Parte III (Contratos) —
    tom descritivo de método e dados em vez de moldura editorial ("A maioria não resiste ao
    escrutínio..."); acrescentada frase sobre uso de embeddings + LLM (Gemini) na classificação
    de domínio comparável, e um parágrafo novo, só sobre Saúde, citando a tentativa
    PNGC/ApuraSUS, os microdados de AIH/DATASUS e o cruzamento com o SICOM. Os 5 princípios
    originais foram mantidos como estavam.
  - Diff do `<body>` de `cardapio_unificado.html` contra `cardapio_unificado_artifact.html`
    confirma as duas variantes em par (única diferença remanescente é uma quebra de linha
    pré-existente entre `</style>` e `<nav>`, sem relação com o conteúdo). Nenhum
    `href="#CTR-ITENS"` restante. Artifact republicado na mesma URL.
- **2026-07-31 (execução do plano EDU-004 — Passo 1):** outra ferramenta (Gemini Antigravity,
  fora deste projeto) rodou a busca de decretos do §8º pendente no plano
  (`plano_EDU-004_confirmacao_legal.md`) — varredura completa dos 2.715 decretos indexados na API
  do SAPL (tipo=12), filtrados por ano ≥ 2020 e palavras-chave de jornada docente. Execução
  conferida diretamente nos arquivos de cache (`folha/auditoria-folha-sete-lagoas/legislacao_cache/
  decretos_list_raw.json` e `decretos_educacao_matches.json`): resultado real é **zero decretos
  encontrados** — confirma o ramo "Nada confirma" do plano, não o "Decreto encontrado". A
  ferramenta externa concluiu, por conta própria, que o selo deveria subir para "Respaldo
  médio-forte" e reintroduziu a citação **"Art. 58 da LC nº 192/2016"** já marcada como errada na
  rodada anterior — não foi seguida (nota de correção acrescentada em
  `estudo_intenso_dobras_professores.md`, que vive fora deste projeto, em
  `~/.gemini/antigravity/brain/`). Selo do EDU-004 mantido em "Respaldo médio"; marcos, riscos e
  pendências no cardápio (ambas as variantes) atualizados para registrar a busca concluída e seu
  resultado, com consulta formal à PGM como próximo passo real. Nenhum número mudou. Detalhamento
  completo em `plano_EDU-004_confirmacao_legal.md`, seção "Resultado da execução do Passo 1". Ainda
  não republicado como Artifact nesta rodada.
- **2026-08-04 (EDU-005 reescrita por inteiro):** após o `parecer_EDU-005_auditoria_independente.md`,
  a frente foi remediada e depois **reescopada por decisão do usuário**. Ver
  `plano_EDU-005_remediacao_parecer.md` para o detalhamento completo das 4 ondas. O essencial:
  - **A frente virou outra coisa.** De "apoio escolar não pedagógico em toda a rede, por fronteira
    de eficiência" para "**quadro administrativo das escolas de ensino fundamental, por comparação
    entre pares**". Servente escolar (92% da frente anterior), vigia e toda a educação infantil
    saíram do escopo. Motivo: o usuário determinou que não haja corte em creche e que o foco seja
    administrativo.
  - **Faixa nova**: piso R$ 169.627,76 · central R$ 526.723,63 · teto R$ 754.243,28 (era
    599.876,04 / 666.512,27 / 692.103,62). As três pontas agora são três padrões de exigência
    (mediana, quartil inferior, percentil 10 de administrativos por aluno), não variações de encargo.
  - **Totais da Parte I recalculados**: piso R$ 4.800.409,13 · central R$ 6.070.194,20 · teto
    R$ 6.501.280,40. Aparecem em dois lugares cada no HTML.
  - **O parâmetro externo foi abandonado.** O padrão agora é o quartil inferior observado entre as
    25 escolas de fundamental da própria rede (1,802 adm/100 alunos, praticado por 7 delas). Isso
    **extingue a pendência bloqueante** sobre a origem do parâmetro, que era a maior exposição da
    frente.
  - **Achado a não perder**: pelo parâmetro antigo a rede está **101 posições administrativas
    ABAIXO** do alvo (215 contra 316). A frente decorre de dispersão entre unidades, não de excesso
    agregado. Está declarado no box de abertura da frente — não remover.
  - **Correção ao parecer**: o §3.3 dele está errado. A divulgação estrita de IDEB 2023 do INEP dá
    exatamente 14 escolas, as mesmas já na base; `ideb.xlsx` usa a média de anos iniciais e finais e
    bate 14/14. Não houve falha de extração. O ganho para 22 veio de aceitar IDEB de anos anteriores.
  - **Fonte de recurso apurada** (SICOM 2025, local): contratação temporária da Educação é 68,9%
    fonte 1.500 (não vinculados) e 31,1% fonte 1.540 (Fundeb).
  - **Isis da Silva Oliveira**: consta PARALISADA no Censo 2024, mas a SME confirma em
    funcionamento; prevalece o campo. Tratada por `MATRICULA_OVERRIDE = {31386928: 337}` no script.
    **A base de origem segue com zero** — sem o override o quadro inteiro é lido como excesso.
  - Scripts novos em `Educação/Scripts/`: `baixar_ideb_inep.py`, `atualizar_matriculas_censo.py`,
    `dea_eficiencia_escolas_v2.py`, `benchmark_administrativo_pares.py`,
    `fonte_recurso_contratos_sicom.py`. O original `dea_eficiencia_escolas.py` está intacto e o
    baseline congelado em `DEA_Eficiencia_Escolas_SeteLagoas_baseline_20260804.xlsx`.
  - **Não republicado como Artifact** — aguarda revisão humana. `revisao_cardapio.html` foi
    atualizado com EDU-005 (que nunca esteve lá) marcada como "Reescrita 04/08".
- **2026-08-05 (auditoria CEO + fechamento das 4 pendências de TIER 2):** rodada em duas partes.
  Detalhamento completo em `AUDITORIA_CEO_COMPLETA_2026-08-05.md`.
  - **Parte da manhã** (auditoria CEO): removidos 14 selos de respaldo interno (documento passa a
    ser lido "certeiro" pelo prefeito, sem escala de confiança que só fazia sentido internamente);
    removida a "divergência 66/198" de EDU-001/EDU-004 (não é achado — nem todo contrato tem
    empenho no mesmo recorte do SICOM); **EDU-004 descartado como bloqueador jurídico** — era erro
    de premissa (professor é titular de cargo, não de unidade; lotação entre escolas da mesma rede
    é ato ordinário da SME, `plano_EDU-004_confirmacao_legal.md` fica **prejudicado**); CON-001
    excluído do total de Saúde (marcador "Inviável", faixa mantida como referência histórica,
    delta −R$ 393.300/−R$ 1.693.300/−R$ 2.193.300). Nesta rodada o `cardapio_unificado.html` foi
    corrompido por edição via PowerShell (dobra de UTF-8, 5.300 ocorrências de mojibake) e
    recuperado a partir do `_artifact.html` intacto — **nunca editar HTML por PowerShell**, só
    Python com `encoding='utf-8'` explícito ou as ferramentas Edit/Write.
  - **Parte da tarde** (fechamento das 4 dependências de TIER 2 — nenhum piso/central/teto mudou):
    - **HOSP-002**: pendência de custo operacional fechada. PNGC/ApuraSUS confirmado aderente
      (hipótese anterior de não adesão estava errada); Demonstrações Contábeis HNSG 2024 obtidas
      mas sem segregação por procedimento; estimativa por referência externa (PLANSERV/BA + Rangel
      et al. 2018) mostra que, sob métrica líquida (custo menos receita de AIH), o central de
      R$78.000 é otimista, não conservador — mantido mesmo assim, revisão fica para próxima rodada.
      Ver `plano_HOSP-002_custo_operacional.md`, seção "Resultado da execução".
    - **CON-003**: reenquadrado. O documento não é auditoria de legalidade — é cardápio de corte de
      custo. Exposição fiscal dos 29 meses sem instrumento passou a contexto de governança à parte;
      encaminhamento à Procuradoria é decisão do cliente, não achado deste projeto.
    - **REC-001**: respaldo per capita reforçado com dois contratos de rateio reais de 2026 (CISRU
      Centro Sul, Prados e Ritápolis, ~R$12,8/hab/ano convergentes) aplicados à população dos 11
      municípios do SAMU (264.066 hab., Censo 2022) ≈ R$3,39 milhões/ano — dentro da faixa
      central-teto já publicada, corroborando-a em vez de contradizê-la.
    - **PES-003**: rodada a mesma auditoria adversarial externa (agente Fable 5) que MED-001,
      ADM-001, CON-001, CON-002, HOSP-001 e PES-002 já tinham recebido em julho. Nenhum erro de
      cálculo; veredito Condicional mantido; achado novo incorporado — a redução médica agregada
      não excluía UTI e Clínica Médica, especialidades que outro estudo do mesmo projeto liga à
      mortalidade anômala do hospital por falta de intensivistas. Virou condição do veredito.
  - **Seção "Questões abertas" publicada na capa geral** do `cardapio_unificado.html`, com as 2
    dependências que sobraram (REC-001, CON-003) — HOSP-002 e PES-003 saíram da lista por já
    estarem resolvidas nesta mesma rodada.
  - Artifact republicado na mesma URL.
- **2026-08-05 (edição manual do usuário + rodada de limpeza para entrega):** o usuário editou
  `cardapio_unificado.html` manualmente antes desta rodada — removeu o box "Os três totais não se
  somam", a seção "Questões abertas" da capa (publicada na rodada da manhã do mesmo dia) e o
  parágrafo de honestidade sobre o valor descartado de R$ 515.144,09 em EDU-001, e reescreveu a
  abertura do documento e parte da proposta de EDU-005 num tom mais direto. Em seguida, quatro
  pedidos executados nesta sessão:
  - **Notas de honestidade removidas por completo** (9 boxes `class="honestidade"` fora de CON-001,
    mais o de CON-001 já embutido na reescrita abaixo — 10 no total). Decisão explícita do usuário,
    contra o protocolo documentado neste arquivo ("manter 100%, nunca suavizar") — sinalizado antes
    de executar, usuário confirmou exclusão total. Uma das notas removidas (HOSP, enfermagem) tinha
    um guardrail relevante — "esse número não foi usado como alvo e não deve ser citado como
    economia" — que não sobrevive em nenhuma outra parte do documento. Vale ter isso em mente se a
    frente de enfermagem for questionada pelo cliente.
  - **Menções a dados internos removidas**: os dois lugares restantes que citavam nome de arquivo
    (`Scripts/benchmark_administrativo_pares.py`, `Benchmark_Administrativo_Fundamental.xlsx`,
    `Scripts/dea_eficiencia_escolas_v2.py` em EDU-005; `plano_HOSP-002_custo_operacional.md` em
    HOSP-002) viraram descrição em prosa, sem nome de arquivo.
  - **CON-002**: removida a seção "Pendências que refinam a estimativa" (7 itens). Resto da frente
    intocado.
  - **CON-001 (CIAS 101/2025) reescrito do zero por agente Opus** (skills `humanizer` +
    `mckinsey-consultant`, seguindo o pipeline deste projeto). A seção original acumulava 5-6 camadas
    de remendo ("⚠️ REVISADO 04/08", "RECONCILIAÇÃO 04/08" etc.) sobre o texto pré-PES-003, com o
    mesmo fato repetido várias vezes e um "Plano de ação" que ainda mandava negociar com o CIAS a
    redução de horas de ortopedia — contradizendo a própria conclusão de inviabilidade. Reescrita
    como narrativa única: a frente é INVIÁVEL (6 ortopedistas efetivos reais, não 18; custo-hora
    R$ 233,68 acima dos R$ 182,08 do CIAS, absorção vira despesa, não economia); o componente de
    neurologia não foi afetado pela reconciliação e segue como hipótese pendente de confirmação.
    Piso/central/teto (R$ 393.300 / R$ 1.693.300 / R$ 2.193.300) mantidos exatamente iguais,
    conferidos um a um contra o texto anterior — nenhum número mudou. Adicionado um
    `<p class="piso-zero">` deixando explícito que a faixa é referência histórica e não soma ao
    total (mesmo padrão já usado em CON-003, HOSP-002 e REC-001).
  - `cardapio_unificado_artifact.html` regenerado via `python gerar_artifact.py` (não editado à
    mão). Artifact republicado na mesma URL.
- **2026-08-05 (versão editável):** criado `gerar_editavel.py`, que gera
  `cardapio_unificado_editavel_artifact.html` a partir de `cardapio_unificado.html` — mesma
  aparência e CSS, com uma barra de edição embutida (contenteditable + autosave em localStorage do
  navegador + botões "Baixar HTML editado" / "Copiar HTML" / "Restaurar original", usando a
  capability `downloads` do Artifact). Publicado como Artifact separado (favicon ✏️):
  https://claude.ai/code/artifact/dea4ac55-e88e-4aa0-a099-f5664b70b7fa. Não é edição compartilhada
  entre dispositivos nem grava direto neste repositório — o rascunho vive só no navegador de quem
  edita; o fluxo real é editar ali e depois baixar/colar o HTML de volta para eu sincronizar com
  `cardapio_unificado.html`. Regra igual à do `gerar_artifact.py`: editar sempre o arquivo-fonte e
  rodar `python gerar_editavel.py` de novo para atualizar a ferramenta — nunca editar o
  `_editavel_artifact` à mão.

## Decisões e protocolo (para próximas rodadas de merge)

### Fusão de fontes heterogêneas

- Cada fonte mantém sua própria natureza de "economia" (recorrente, devolução
  contábil, receita/governança, condicional). **Nunca somar os totais das 3
  secretarias num número único** — a heterogeneidade é um cuidado deliberado dos
  documentos originais e tem que sobreviver na versão unificada.
- Saúde é a fonte mais densa: cada frente carrega códigos de evidência internos
  (E1-E60, P1-P8, F1-F17), uma tabela "Evidências quantitativas" e uma seção "Fontes e
  rastreabilidade" com caminhos de arquivo internos. Para a versão cliente:
  - **Remover**: os códigos inline, a tabela de evidências, a lista de rastreabilidade.
  - **Manter 100%**: riscos, pendências, veredito de auditoria (Robusta/Condicional/
    Parcial), notas de honestidade. São disclaimers metodológicos deliberados — não
    enchimento de texto. Frases como "o teto nunca é promessa", "isto não é economia,
    é exposição fiscal", "o piso é honestamente R$ 0" protegem o cliente de
    superestimar economia perante TCE-MG e câmara municipal. Nunca suavizar.
- **Nenhum número muda na reescrita.** Todo valor (R$, %, datas, nº de contrato/lei)
  tem que ser conferido contra a fonte antes de publicar.

### Pipeline de reescrita

1. Ler as fontes completas (nunca resumir de segunda mão — arquivos grandes, mas o
   conteúdo importa linha a linha).
2. Confirmar que a fonte está atualizada (checar timestamp do arquivo — já aconteceu
   de eu ler uma versão anterior enquanto o cardápio de Saúde estava sendo
   regenerado no mesmo dia).
3. Reescrever com modelo Opus + skills `humanizer` (anti-IA) e `mckinsey-consultant`
   (estilo consultivo), preservando fatos e ressalvas.
4. Validar número a número contra a fonte antes de considerar pronto.
5. Gerar a variante sem DOCTYPE/html/head/body e publicar como Artifact.

### Achado já registrado (não re-investigar)

- **Educação**: a soma dos 4 componentes dá piso R$ 4.630.781,**38** e teto
  R$ 5.747.037,**13**; a fonte (`html_cardapio/index.html`, gerado por
  `gerar_html_cardapio_edu.py`) publica ,**37** e ,**12** — diferença de 1 centavo,
  arredondamento do gerador original. Mantivemos o valor da fonte na versão unificada.
  Vale corrigir na origem se o cardápio de Educação for reemitido.

## Pendências conhecidas: EDU-004 e HOSP-002

- **EDU-004** (base legal da itinerância docente): descartado como bloqueador em 05/08/2026 — era erro
  de premissa (professor é titular de cargo, não de unidade; lotação entre escolas da mesma rede é ato
  ordinário da SME). Ver `AUDITORIA_CEO_COMPLETA_2026-08-05.md`, seção "Descartado — EDU-004 não era
  bloqueador". `plano_EDU-004_confirmacao_legal.md` está **prejudicado** e não deve orientar novas
  rodadas.
- **HOSP-002** (custo operacional completo do protocolo de parto adequado): **fechado em 05/08/2026**,
  sem alteração de piso/central/teto. A investigação em `saude7l/outputs_2026/08_pngc/` (concluída em
  31/07) confirmou adesão de Sete Lagoas ao PNGC/ApuraSUS (a hipótese anterior de não adesão estava
  errada), obteve e analisou as Demonstrações Contábeis do HNSG 2024 (que não segregam custo por
  procedimento) e estimou a diferença de custo cesárea-vs-normal por referência externa (PLANSERV/BA +
  Rangel et al. 2018): sob métrica líquida (custo menos receita de repasse), o central publicado de
  R$ 78.000 é otimista, não conservador, mas segue dentro da faixa defensável — não foi alterado. Ver
  `plano_HOSP-002_custo_operacional.md`, seção "Resultado da execução", e o texto atualizado da própria
  frente em `cardapio_unificado.html`/`_artifact.html`. Saiu da lista de "Questões abertas" de TIER 2 do
  `AUDITORIA_CEO_COMPLETA_2026-08-05.md` — o que resta (custo do HNSG por procedimento) é refinamento
  futuro, não bloqueio de apresentação.

## Pendência conhecida: casos "Indeterminada" em dashboard-contratos

Ver plano detalhado em
`dashboard-contratos\comparativo-pncp\PLANO_ITENS_MULTIPLOS.md`.

Resumo: casos como "Kits Reagentes" (contrato 045/2026) aparecem como economia
indeterminada no deck de contratos, mas **o dado real já existe** — foi extraído via
OCR/Gemini direto do PDF oficial do contrato (`comparativo-pncp/dados/itens_pdf_sl.json`,
132 dos 169 contratos processados têm planilha de itens real). Esse dado nunca chegou
ao deck final porque o script de comparação por item
(`comparar_item_unico_pncp.py`) só cobre os 25 contratos de item ÚNICO — contratos
multi-item (como Kits Reagentes, com vários reagentes diferentes na mesma compra)
não têm comparador ainda. Não é um problema de coleta de dado, é um problema de
pipeline incompleto.

## Skills instaladas para este projeto

- `humanizer` (github.com/blader/humanizer) — remove sinais de texto gerado por IA.
- `mckinsey-consultant` (fleurytian/awesome-claude-skills) — estrutura de comunicação
  executiva estilo consultoria.

Ambas em `~/.claude/skills/`, symlinks para `~/.agents/skills/`.

## Localização das fontes

- Educação: `C:\Users\victo\OneDrive - Sophos Governança\SETE LAGOAS - Documentos\Execução\02. Estudo de custos\Educação\html_cardapio\`
- Saúde: `C:\Users\victo\OneDrive\Documentos\Python\projetos\saude7l\outputs_2026\18_cardapio_cortes\html\`
- Contratos: `C:\Users\victo\OneDrive\Documentos\Python\projetos\dashboard-contratos\comparativo-pncp\apresentacao_contratos_ativos_robustos.html`
