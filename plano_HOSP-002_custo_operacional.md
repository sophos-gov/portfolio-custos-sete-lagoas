# Plano: obter custo operacional completo do protocolo de parto adequado (HOSP-002)

## Pendência que este plano resolve

`cardapio_unificado.html` / `cardapio_unificado_artifact.html`, frente **HOSP-002** (Protocolo de
parto adequado no HNSG): a faixa (piso R$ 0 / central R$ 78.000 / teto R$ 238.000 — **números não
mexem neste plano**) captura só a diferença de repasse do SUS por parto (R$ 923,33 cesárea vs
R$ 588,44 normal = R$ 334,89), sobre 2.585 partos de 2024. Não inclui centro cirúrgico, anestesia
nem eventual UTI neonatal — custos que tendem a pesar mais numa cesárea evitável do que a diferença
de repasse capturada. A pendência registrada no cardápio hoje diz que o próximo passo é "levantar a
tabela SIGTAP"; este plano detalha isso e mais três frentes de dado que já estão mapeadas em outro
projeto e nunca foram fechadas.

## Apuração já feita (não refazer — ver saude7l)

Fonte: `saude7l/outputs_2026/08_pngc/RESUMO_EXECUTIVO_PNGC.md` e
`proximos_passos_recomendados.md` (coleta de 2026-04-23, duas rodadas).

- **Adesão ao PNGC/ApuraSUS:** não identificável em fonte pública indexada; nem o HNSG (CNES
  2206528) nem o Hospital Municipal (CNES 2109867) aparecem em material público de aderentes.
  Confirmação definitiva exige ofício à DESID — **modelo de e-mail já redigido**, ver seção 3 abaixo.
- **SIH-SUS (produção hospitalar, AIH):** TabNet (`tabnet.datasus.gov.br`) está acessível, mas o
  formulário exige **POST**; a ferramenta de fetch usada na coleta original só faz GET, então a
  consulta não foi executada. Os valores internos necessários já foram mapeados: CNES 2109867 =
  `SEstabelecimento=110`, CNES 2206528 = `SEstabelecimento=455`, arquivos `nimg24{01..12}.dbf` +
  `nimg25{01..12}.dbf`, incrementos `AIH_aprovadas`/`Valor_total`/`Media_permanencia`/`Obitos`.
- **Demonstrações Contábeis HNSG 2024** e **Contrato 125/2023 + 8 aditivos**: localizados no Google
  Drive do próprio HNSG, links diretos já capturados (`hnsg_google_drive_links.json`), mas nunca
  baixados — ficam atrás de `/file/d/<id>/view`, que exige navegação (não é um endpoint de download
  direto).
- **Boletim de Economia da Saúde dez/2021 (DESID/MS):** PDF **acessível agora, sem bloqueio**
  (`bvsms.saude.gov.br/bvs/publicacoes/boletim_economia_saude_dez2021.pdf`), contém custos
  hospitalares agregados por porte — nunca foi extraído em detalhe. Edições 2024-2025 não foram
  localizadas.
- **Repasses SMS → HNSG:** já fechados (R$ 103,2 mi em 2024, R$ 65,1 mi em jan-nov/2025) — não é o
  dado que falta aqui, é sobre financiamento agregado, não custo por procedimento.

## Ordem de execução recomendada (automação primeiro, por padrão do projeto)

1. **Boletim de Economia da Saúde dez/2021 — sem bloqueio, fazer primeiro.**
   Ler o PDF já baixável e extrair benchmark de custo/paciente-dia e custo/AIH por porte hospitalar.
   Serve como referência externa aproximada enquanto o dado interno do HNSG não vem. Não precisa de
   infraestrutura nova — só um agente lendo o PDF (ferramenta de leitura de PDF já disponível).

2. **Tabela SIGTAP (procedimentos SUS) — download público, automatizável.**
   A SIGTAP (Sistema de Gerenciamento da Tabela de Procedimentos, Medicamentos e OPM do SUS) é
   pública, distribuída em arquivos de competência mensal pelo DATASUS
   (`http://sigtap.datasus.gov.br/tabela-unificada/app/sec/downloads.jsp` — confirmar domínio atual
   antes de automatizar). A tabela decompõe o valor de referência de cada procedimento (ex.: parto
   cesáreo vs parto normal) em componentes — o mais próximo de um "custo operacional de referência"
   disponível publicamente sem depender de dado interno do hospital. Tentar 3 formas antes de
   qualquer coisa manual, na ordem: (a) download direto do arquivo de competência mais recente via
   `requests`; (b) API/serviço alternativo do DATASUS se o download direto estiver bloqueado; (c) se
   nenhum dos dois funcionar por bloqueio de allowlist de rede, documentar e pedir ajuste de
   allowlist antes de cair para qualquer coisa manual.

3. **SIH-SUS bruto via download em lote — automatizável, evita o bloqueio do TabNet.**
   Em vez de tentar de novo o formulário POST do TabNet, baixar os arquivos brutos `.DBC` direto de
   `datasus.saude.gov.br/transferencia-de-arquivos/` (SIHSUS → RD → MG → competências 2024-01 a
   2025-12) e processar com `pyreaddbc` (Python), filtrando pelo CNES 2206528. Isso dá AIH aprovadas,
   valor total, permanência e óbitos por competência — permite substituir o corte único de 2024 por
   série mensal e, se o SIH abrir os componentes de valor (diária, SP/SADT, OPM), aproximar melhor o
   que fica de fora do cálculo atual.

4. **Demonstrações Contábeis HNSG 2024 (PDF, Google Drive) — provável melhor fonte de custo real.**
   Link já conhecido:
   `https://drive.google.com/file/d/1hY4hi3VN60YaPUU_b5rSoJWYemP89Qy-/view`. Tentar automatizar o
   download (ex. `gdown` ou requisição direta ao endpoint de export do Drive) antes de qualquer coisa
   manual; só cair para "baixar manualmente e subir como anexo numa sessão" se as tentativas
   automatizadas falharem — documentando cada tentativa, conforme o protocolo de automação do
   projeto. Se as demonstrações contábeis do HNSG segregarem despesa por centro de custo (centro
   cirúrgico, UTI, anestesia), este é o dado mais direto para fechar a pendência — mais direto que
   SIGTAP, que é valor de referência nacional, não custo real local.

5. **Contrato 125/2023 + aditivos (PDF, Google Drive) — mesmo tratamento do item 4.**
   Link em `hnsg.com.br/portaltransparencia/contratualizacao/`. Relevante como cruzamento: se o
   contrato tiver cláusula de custo por tipo de procedimento ou componente de leito/UTI, ajuda a
   validar (ou substituir) o número aproximado por SIGTAP/Boletim.

6. **Ofício à DESID confirmando adesão ao PNGC — ação humana, não bloqueante para os itens acima.**
   Texto já pronto em `saude7l/outputs_2026/08_pngc/proximos_passos_recomendados.md` (seção A);
   enviar para `pngc@saude.gov.br`, prazo de resposta 15 dias úteis, com pedido via LAI
   (`falabr.cgu.gov.br`, art. 7º da Lei 12.527/2011) como alternativa formal se não houver resposta.
   Esta frente não precisa esperar essa resposta para avançar — os itens 1-5 não dependem dela.

## Critério de fechamento

- Quando houver dado real de custo por componente (de preferência das Demonstrações Contábeis do
  HNSG; na falta, SIGTAP + Boletim de Economia da Saúde como aproximação), recalcular central e teto
  do HOSP-002 incorporando centro cirúrgico, anestesia e UTI neonatal. **O piso continua R$ 0** —
  isso não muda, é escolha metodológica documentada e independente deste plano.
- Se só for possível chegar a uma aproximação (via SIGTAP/Boletim, sem dado interno do HNSG),
  manter o aviso atual ("o número tende a subestimar, não a superestimar") em vez de publicar um
  novo central/teto pouco confiável — mudar de estimativa aproximada para estimativa aproximada
  melhor não justifica sozinho reabrir o número sem dado direto do hospital.
- Registrar o resultado da confirmação PNGC (item 6) na pendência do cardápio, independentemente do
  resultado dos itens 1-5, porque hoje o texto diz "provavelmente não aderente" — uma resposta da
  DESID transforma isso em fato confirmado.

## Arquivos e fontes envolvidos

- `saude7l/outputs_2026/08_pngc/` — toda a apuração já feita (CNES, repasses, links do Drive, modelo
  de ofício).
- `custos/cardapio_unificado.html` e `..._artifact.html`, seção `HOSP-002` — onde aplicar o
  resultado final, sempre em par, seguindo o mesmo protocolo já usado nesta rodada.

## Resultado da execução (31/07 a 05/08/2026)

Os itens 1-5 da ordem de execução foram percorridos (ver
`saude7l/outputs_2026/08_pngc/STATUS_HONESTO_PLANO_HOSP002.md` para o relato honesto do que foi
automatizado e do que ficou bloqueado). Resultado consolidado na versão final e verificada,
`saude7l/outputs_2026/08_pngc/ESTUDO_CUSTO_PARTO_HNSG.md` (que corrige três erros de versões
intermediárias da mesma sessão — ver errata no topo daquele arquivo):

- **Item 6 (adesão ao PNGC) confirmado, sem precisar do ofício.** Sete Lagoas é aderente — CNES
  2206528 (HNSG) e 2109867 (Hospital Municipal) aparecem no CSV público de unidades do ApuraSUS
  (`dados_brutos/apurasus/V2_Apurasus_Unidades.csv`, linhas 344 e 352 — conferido diretamente nesta
  sessão). A hipótese anterior de não adesão, registrada na rodada de correções de 31/07, estava
  errada. **Mas isso não abre a porta para o dado que falta:** o painel de custo por procedimento do
  ApuraSUS continua restrito a gestor autenticado da unidade (confirmado em
  `outputs_2026/05_entregaveis/APURASUS_CUSTOS_HOSPITALARES.md`, abril/2026). O ofício à DESID segue
  como próximo passo real — minuta pronta (`oficio_desid_pngc_sete_lagoas.docx`), nunca enviada, pois
  depende de acesso à caixa de e-mail institucional.
- **Item 4 (Demonstrações Contábeis do HNSG 2024) obtido e analisado, mas insuficiente.** O PDF foi
  baixado e as páginas 5-6 extraídas (`ANALISE_DEMONSTRACOES_RESULTADOS_HNSG.md`): resultado do
  exercício positivo de R$ 14,1 milhões em 2024 (contra prejuízo de R$ 11,5 milhões em 2023), receita
  operacional líquida de R$ 124 milhões. O demonstrativo é por hospital inteiro — não segrega despesa
  por centro de custo (cirúrgico, anestesia, UTI) nem por procedimento. Não fecha a pendência de
  custo operacional por parto.
- **Itens 1-3 (Boletim de Economia da Saúde, SIGTAP, SIH-SUS bruto) superados por um caminho melhor.**
  Em vez de montar um custo de referência nacional via SIGTAP, a análise final usou duas fontes que já
  decompõem o custo hospitalar completo do parto: PLANSERV/BA (tabela de valores referenciais,
  contas hospitalares reais de agosto/2024) e Rangel et al. 2018 (micro-custeio de três maternidades
  públicas do SUS no Rio de Janeiro e em Belo Horizonte, corrigido pela inflação). As duas confirmam a
  cesárea custando 9% a 32% a mais que o parto normal na produção — mas, como a cesárea também fatura
  mais repasse do SUS, a diferença **líquida** (custo menos receita) cai para R$ 125-400 por parto, e
  a mesma redução de nove pontos percentuais do central oficial equivaleria, sob essa métrica, a
  R$ 29-93 mil/ano. **O central publicado (R$ 78.000) cai dentro dessa faixa, mas perto do teto — é
  uma estimativa otimista, não conservadora.**

### Decisão tomada (05/08/2026)

Seguindo o critério de fechamento já registrado acima ("mudar de estimativa aproximada para
estimativa aproximada melhor não justifica sozinho reabrir o número"): **o central e o teto do
HOSP-002 não foram alterados nesta rodada.** O cardápio (`cardapio_unificado.html`, seção HOSP-002)
foi atualizado só no texto — a pendência sobre PNGC/SIGTAP foi corrigida para refletir o resultado
real da investigação, e um novo risco foi registrado alertando que o central é otimista, não
conservador, sob a métrica líquida. **HOSP-002 saiu da lista de "Questões abertas" de TIER 2** do
relatório `AUDITORIA_CEO_COMPLETA_2026-08-05.md`: não é mais uma frente que aguarda dado externo para
ser apresentada — o que resta (custo real do HNSG segregado por procedimento) é refinamento futuro,
não bloqueio. Este plano está encerrado; qualquer revisão numérica fica para a próxima consolidação
do cardápio, fora deste plano.
