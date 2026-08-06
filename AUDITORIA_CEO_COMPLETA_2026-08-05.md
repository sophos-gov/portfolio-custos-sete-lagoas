# Auditoria do Cardápio Unificado — Relatório

**Documentos auditados:** `cardapio_unificado.html` + `cardapio_unificado_artifact.html`
**Frentes:** 21 (5 Educação · 10 Saúde · 6 Contratos)
**Última revisão:** 2026-08-05

> **Nota de revisão (05/08).** As tabelas por frente da versão anterior deste relatório estavam
> erradas — foram montadas por inferência, não a partir do cardápio. Todos os valores abaixo foram
> reextraídos do HTML e conferidos contra as somas publicadas na capa.

---

## Impacto financeiro da auditoria

A auditoria alterou **um único número**: a exclusão do CON-001 do total de Saúde. Educação e
Contratos não foram tocados nesta rodada.

| Bloco             |                           Antes |                                 Depois | Δ |
| ----------------- | ------------------------------: | -------------------------------------: | -: |
| Saúde · piso    |   R$ 7.011.931 | R$ 6.618.631 |                           −R$ 393.300 |    |
| Saúde · central | R$ 21.840.410 | R$ 20.147.110 |                         −R$ 1.693.300 |    |
| Saúde · teto    | R$ 36.158.640 | R$ 33.965.340 |                         −R$ 2.193.300 |    |
| Educação        |                              — |                             inalterada | — |
| Contratos         |                              — | sem total (por decisão metodológica) | — |

O delta é exatamente a faixa do CON-001. Os totais de Educação (piso R$ 4.800.409 · central
R$ 6.070.194 · teto R$ 6.501.280) vinham da reescrita do EDU-005, concluída em 04/08, antes desta
auditoria.

**Os blocos não se somam.** Naturezas orçamentárias diferentes — economia recorrente, devolução
contábil, receita de governança, risco condicional. Somar produziria um número confortável e falso.

---

---

## TIER 2 — Ajustes de apresentação

### Aplicados no cardápio

Modalidade contratual dos 6 casos

| Caso                    | Instrumento                                                 |
| ----------------------- | ----------------------------------------------------------- |
| 1 · folha de pagamento | Serviço nº 078/2023 — contrato firme, declarado no texto |
| 2 · kits escolares     | Bens nº 209/2025                                           |
| 3 · som, luz e gerador | Ata de registro de preço nº 098/2025                      |
| 4 · máquinas pesadas  | Serviço nº 167/2025                                       |
| 5 · sistema de gestão | Serviço nº 253/2025                                       |
| 6 · kits reagentes     | Bens nº 045/2026                                           |

### Pendente de decisão sua

**Seção de questões abertas na capa.** Reunir na abertura as dependências que travam execução, em vez
de deixá-las só dentro de cada frente:

```markdown
## Questões abertas (dependências de execução)

1. REC-001 — SAMU regional depende de adesão. Aguarda acordo intermunicipal.
2. CON-003 — a economia de relicitação (R$ 930 mil a R$ 1,24 mi/ano) depende de nova licitação
   competitiva com benchmark de preço real, ainda inexistente. O contrato vencido sem instrumento
   publicado é exposição fiscal registrada à parte, não achado de auditoria — o encaminhamento à
   Procuradoria é decisão do cliente.

Cada frente tem números definidos; a execução é que depende dessas respostas.
```

**HOSP-002 saiu desta lista em 05/08.** Não é mais dependência que aguarda dado externo: a
investigação de custo operacional foi concluída em 31/07 com os dados disponíveis (ver TIER 3, item 2,
abaixo) e o central permanece sem alteração. O que resta — custo do HNSG segregado por procedimento —
é refinamento, não bloqueio de apresentação.

**PES-003 também saiu desta lista em 05/08.** A frente passou pela mesma auditoria adversarial externa
(agente independente) que as demais frentes deste cardápio já tinham recebido em julho — ver TIER 3,
item 4, abaixo. Nenhum erro de cálculo foi encontrado; o veredito segue Condicional, com uma condição
nova incorporada ao plano de execução (excluir UTI e Clínica Médica da não renovação médica). Não é
mais bloqueio de apresentação.

---

## TIER 3 — Quatro dependências externas

Não são falhas do documento. São questões que exigem decisão jurídica, dado de terceiro ou acordo
com outro ente — nenhuma se resolve por análise.

### 1. CON-003 — relicitação da atenção básica (SERMEP)

**Este documento é um cardápio de sugestões de corte de custo, não uma auditoria de legalidade.** A
proposição de CON-003 é a economia de competição: relicitar o serviço hoje prestado sob o ex-contrato
114/2022 captura o ganho típico de 10% a 20% de uma licitação plenamente competitiva, faixa de
R$ 930 mil a R$ 1,24 milhão/ano. Essa economia depende de um próximo passo técnico — termo de
referência e benchmark de preço unitário real, que ainda não existem — não de qualquer decisão
jurídica.

**Fato registrado à parte, como contexto, não como achado deste documento:** o contrato está vencido
desde 1º de novembro de 2023, e o serviço segue sendo pago sem instrumento publicado — 29 meses na
data do relatório-fonte, R$ 5,6 milhões em 2025, com exposição acumulada extrapolada em torno de
R$ 13,55 milhões. Isso é informação de governança que acompanha a proposição de corte de custo; a
análise da irregularidade e o eventual encaminhamento à Procuradoria são decisão do cliente, fora do
escopo deste projeto.

**Natureza:** a economia (relicitação) e o risco (exposição fiscal) são registrados separadamente e
não devem ser somados. A extrapolação do risco assume taxa constante, o que não está confirmado para
2023 e 2024.

### 2. HOSP-002 — custo operacional do protocolo de parto [investigação concluída em 31/07 — faixa não muda]

A faixa (piso R$ 0 · central R$ 78.000 · teto R$ 238.000) segue calculada pela diferença **bruta** de
repasse do SUS por parto: R$ 923,33 da cesárea contra R$ 588,44 do normal, sobre 2.585 partos de 2024.

**O que a investigação de 31/07 fechou** (`plano_HOSP-002_custo_operacional.md`, seção "Resultado da
execução"; detalhamento em `saude7l/outputs_2026/08_pngc/ESTUDO_CUSTO_PARTO_HNSG.md`):

- **Adesão ao PNGC/ApuraSUS confirmada** — Sete Lagoas é aderente (verificado no CSV público de
  unidades do ApuraSUS; a suposição anterior de não adesão estava errada). Mas o painel de custo por
  procedimento é restrito a gestor autenticado da unidade — inacessível a esta análise.
- **Demonstrações Contábeis do HNSG 2024 obtidas e analisadas** — o hospital teve resultado positivo
  de R$ 14,1 milhões no ano, mas o demonstrativo não segrega despesa por centro de custo ou
  procedimento. Não substitui o dado que falta.
- **Estimativa construída com duas referências externas** (PLANSERV/BA, contas hospitalares reais de
  2024; e Rangel et al. 2018, micro-custeio de maternidades públicas do SUS, atualizado por IPCA):
  ambas confirmam a cesárea custando **9% a 32% a mais** que o parto normal na produção. Como a
  cesárea também fatura mais repasse do SUS, a diferença **líquida** de resultado entre as duas vias
  cai para **R$ 125 a R$ 400 por parto** — bem abaixo dos R$ 334,89 brutos usados no cálculo oficial.
- Sob essa métrica líquida, a mesma redução de nove pontos percentuais equivaleria a **R$ 29 mil a
  R$ 93 mil por ano**. O central publicado (R$ 78.000, base bruta) cai dentro dessa faixa, mas perto
  do teto dela — é uma estimativa **otimista**, não conservadora como o texto do cardápio sugeria.

**Decisão desta rodada: não alterar o número.** O central já foi auditado e é defensável; a revisão
para a métrica líquida (mediana ~R$ 46 mil) fica para a próxima consolidação do cardápio, não para
edição isolada fora do processo de merge. O que segue indisponível é o custo real do HNSG segregado
por procedimento — resolver exige acesso ao ApuraSUS como gestor autenticado ou pedido formal (LAI) ao
hospital. Isso é refinamento futuro, não bloqueio: por isso a frente saiu da lista de "Questões
abertas" de TIER 2.

O piso de R$ 0 é escolha metodológica e não muda.

### 3. REC-001 — SAMU regional depende de adesão [respaldo per capita reforçado em 05/08]

A economia pressupõe rateio intermunicipal formal, e **nenhum instrumento desse tipo foi localizado**
— não há carta de intenção nem contrato de rateio (Lei 11.107/2005) assinado por nenhum dos 11
municípios. O piso é R$ 0 justamente por isso.

**Nota de precisão:** o SICOM mostra 23,1% do custeio de 2025 vindo de uma fonte classificada como
"fundo a fundo SUS de Governos Municipais" — isso é repasse do SUS entre fundos municipais, um
mecanismo diferente de um contrato de rateio de consórcio público (que corre por recursos não
vinculados de impostos, não por fundo a fundo SUS). Não é evidência de adesão formal, mas também não
é "zero" fluxo intermunicipal; é outro tipo de fluxo, que não serve de prova nem de refutação para a
pendência desta frente.

**Central e teto ganharam respaldo quantitativo em 05/08/2026:** dois contratos de rateio reais de
2026 de um consórcio de SAMU comparável (CISRU Centro Sul, Sul de Minas) convergem em torno de
R$ 12,8 por habitante ao ano. Aplicado à população dos 11 municípios do SAMU de Sete Lagoas
(264.066 habitantes, Censo IBGE 2022), o valor esperado é de cerca de R$ 3,39 milhões por ano —
dentro da faixa central-teto já publicada (R$ 3-4 milhões), mais perto do central. Detalhamento no
próprio `cardapio_unificado.html`, frente REC-001, seção "Respaldo em evidência".

**Próximo passo:** formalizar adesão de pelo menos três municípios antes de tratar a faixa como
orçamentária.

### 4. PES-003 — quadro do Hospital Municipal [validação externa concluída em 05/08]

**O que "validação externa" queria dizer neste projeto:** não um consultor humano contratado, e sim a
mesma segunda leitura adversarial (um agente de IA distinto rodando como "Agente Externo
Independente") que MED-001, ADM-001, CON-001, CON-002, HOSP-001 e PES-002 já tinham recebido em
06-07/07/2026. A PES-003 foi fechada em 03/08/2026, depois dessa rodada, e nunca tinha passado por
ela. Rodei essa mesma auditoria em 05/08/2026.

**Resultado:** nenhum erro de cálculo. O agente reproduziu a aritmética da faixa, o dimensionamento
pela COFEN 743/2024 e os percentis contra os 193 hospitais pareados direto contra os arquivos-fonte —
todos batem. A correção metodológica desta versão (trocar o denominador de altas por leito ocupado) foi
avaliada como melhoria real, não ajuste para reduzir o número.

**Veredito mantido: Condicional** — no mesmo patamar de severidade do HOSP-001 (conta certa, mas
100% condicionada a uma variável, a queda de permanência, que o hospital não controla sozinho).

**Achado novo, incorporado ao cardápio:** a redução médica é calculada no agregado do grupo "médico",
sem excluir UTI e Clínica Médica — exatamente as duas especialidades que outro estudo do mesmo projeto
associa à mortalidade anômala do hospital (7,63% contra 3,0%-4,5% dos pares), por subdimensionamento
de intensivistas e clínicos titulados. Virou condição nova do veredito: excluir essas duas
especialidades da não renovação até a medição WISN confirmar folga real nelas.

**Uma segunda alegação do agente não se sustentou** (a natureza jurídica do vínculo "CONTRATO" não
estaria confirmada em norma) — verifiquei a fonte que ele mesmo citou e essa ressalva já tinha sido
resolvida mais adiante no mesmo documento (o vínculo é art. 37, IX, CF, confirmado em cadeia normativa
completa). Não incorporada.

Detalhamento completo do parecer no próprio `cardapio_unificado.html`, frente PES-003, "Riscos a
monitorar" e veredito.

### Descartado — EDU-004 não era bloqueador

A "base legal da itinerância docente" era **erro de premissa**. Professor é titular de cargo, não de
unidade escolar; distribuir sua carga horária entre escolas da mesma rede é ato ordinário de lotação,
dentro do poder discricionário da SME. Não há instituto a criar, logo não havia dispositivo a
encontrar.

O que exigiria base legal específica seria alterar jornada, cargo ou remuneração — e a extensão de
jornada já está amparada no art. 27, §7º da LC nº 80/2003, incluído pela LC nº 253/2021.

A varredura dos 2.715 decretos do SAPL perseguia um problema inexistente.
`plano_EDU-004_confirmacao_legal.md` está **prejudicado** e não deve orientar novas rodadas.

Removidos do cardápio: ressalva do título, marco de levantamento jurídico, risco de "base legal não
identificada", pendência bloqueante e citação da varredura. Permanece o risco sindical, que é real e
operacional.

---

## Faixas por frente

Valores extraídos do cardápio em 05/08/2026.

### Educação — 5 frentes

| Frente          | Proposição                              |                                        Piso |                Central | Teto |
| --------------- | ----------------------------------------- | ------------------------------------------: | ---------------------: | ---: |
| EDU-001         | Extinção dos oficineiros do contraturno |               R$ 1.349.611 | R$ 2.036.219 |           R$ 2.079.988 |      |
| EDU-002         | Rescisão da locação com a FUMEP        |                   R$ 206.603 | R$ 229.558 |             R$ 252.514 |      |
| EDU-003         | Fim da segunda merenda (Projeto)          |                   R$ 705.436 | R$ 829.925 |             R$ 954.413 |      |
| EDU-004         | Racionalização de professores PEB       |               R$ 2.369.131 | R$ 2.447.768 |           R$ 2.460.121 |      |
| EDU-005         | Quadro administrativo do fundamental      |                   R$ 169.628 | R$ 526.724 |             R$ 754.243 |      |
| **Total** |                                           | **R$ 4.800.409** | **R$ 6.070.194** | **R$ 6.501.280** |      |

EDU-002, EDU-003 e EDU-004 dependem da execução de EDU-001 — é o encerramento do contraturno que
libera salas, elimina a segunda refeição e reduz a fragmentação de contratos. EDU-005 é independente.

### Saúde — 10 frentes

| Frente          | Proposição                                       |                                         Piso |                 Central | Teto |
| --------------- | -------------------------------------------------- | -------------------------------------------: | ----------------------: | ---: |
| MED-001         | Medicamentos por ata estadual e consórcio         |                  R$ 562.000 | R$ 1.260.000 |            R$ 1.950.000 |      |
| ADM-001         | Apoio administrativo na atenção primária        |                R$ 1.307.699 | R$ 3.807.777 |            R$ 7.712.389 |      |
| ~~CON-001~~    | ~~Contrato CIAS 101/2025~~ — **inviável** |         ~~R$ 393.300~~ | ~~R$ 1.693.300~~ |       ~~R$ 2.193.300~~ |      |
| CON-002         | Contratos SERMEP 028/2025 e 089/2024               |                    R$ 416.757 | R$ 416.757 |            R$ 1.607.976 |      |
| CON-003         | Relicitação da atenção básica                 |                          R$ 0 | R$ 930.000 |            R$ 1.240.000 |      |
| HOSP-001        | Contratualização por desempenho (HNSG)           |                  R$ 473.000 | R$ 1.568.000 |            R$ 2.116.000 |      |
| HOSP-002        | Protocolo de parto adequado                        |                           R$ 0 | R$ 78.000 |              R$ 238.000 |      |
| PES-002         | Governança das horas extras                       |                R$ 1.500.000 | R$ 4.700.000 |            R$ 7.000.000 |      |
| REC-001         | Rateio do SAMU regional                            |                        R$ 0 | R$ 3.000.000 |            R$ 4.000.000 |      |
| PES-003         | Quadro do Hospital Municipal                       |                R$ 2.359.175 | R$ 4.386.576 |            R$ 8.100.975 |      |
| **Total** | sem CON-001                                        | **R$ 6.618.631** | **R$ 20.147.110** | **R$ 33.965.340** |      |

Três frentes têm piso R$ 0 — CON-003, HOSP-002 e REC-001. Não é omissão: é a declaração de que a
economia mínima garantida é zero enquanto a dependência não se resolver.

### Contratos — 6 casos

| Caso | Objeto                      |                                    Valor do contrato | Economia defensável |
| ---- | --------------------------- | ---------------------------------------------------: | -------------------- |
| 1    | Folha de pagamento (Caixa)  | R$ 15.000.000 · 60 m | R$ 900 mil a R$ 1,5 mi/ano |                      |
| 2    | Kits escolares              |                                 R$ 4.199.997 · 12 m | Indefinida           |
| 3    | Som, luz e gerador          |        R$ 2.991.200 · 12 m | R$ 0 a R$ 1,9 mi/ano |                      |
| 4    | Máquinas pesadas           |       R$ 1.899.955 · 12 m | R$ 0 a R$ 535 mil/ano |                      |
| 5    | Sistema de gestão pública |                                 R$ 3.366.041 · 12 m | Indeterminada        |
| 6    | Kits reagentes              |                                 R$ 1.231.176 · 12 m | Indeterminada        |

Três casos quantificados (1, 3 e 4) e três sem quantificação (2, 5 e 6). **O bloco não recebe total** —
somar faixas indeterminadas produziria um número falso.

---

## Próximos passos

**Antes de apresentar ao prefeito**

1. Decidir sobre a seção de questões abertas na capa — único item de TIER 2 em aberto.
2. Republicar o Artifact.

**Encaminhamentos que não dependem do documento**

| Destinatário          | Assunto                                             |
| ---------------------- | --------------------------------------------------- |
| Procuradoria           | CON-003 — exposição dos 29 meses sem instrumento |
| DESID/MS (`pngc@saude.gov.br`) | HOSP-002 — ofício confirmando adesão formal ao PNGC/ApuraSUS (minuta pronta em `saude7l/outputs_2026/08_pngc/oficio_desid_pngc_sete_lagoas.docx`, nunca enviada) |
| Municípios da região | REC-001 — adesão ao rateio do SAMU                |
| RH/SMS | PES-003 — medição WISN de carga de trabalho em UTI, Clínica Médica, ortopedia e anestesia, antes de qualquer não renovação médica |

**Sequenciamento na execução:** EDU-001 antes de EDU-002, EDU-003 e EDU-004.

---

## Estado do documento

**Verificado:** números rastreáveis ao cardápio; totais batendo com as somas por frente;
heterogeneidade das naturezas preservada; as duas variantes do HTML sincronizadas
(`gerar_artifact.py --check` OK); 21 frentes íntegras.

**Em aberto:** as quatro dependências de TIER 3 continuam dentro das seções expandíveis de cada
frente, não na abertura — é o que a seção de questões abertas resolveria.

---

## Recomendação

Apresentar como **documento de trabalho com dependências declaradas**. As quatro questões de TIER 3
não são fragilidades da análise: são condições de execução que dependem de terceiros. Declará-las é
o que protege o gestor perante o TCE-MG e a câmara — um cardápio que promete economia sem ressalva é
mais frágil, não mais forte.

---

## Arquivos

| Arquivo                                       | Papel                                                     |
| --------------------------------------------- | --------------------------------------------------------- |
| `cardapio_unificado.html`                   | Fonte única — editar sempre aqui                        |
| `cardapio_unificado_artifact.html`          | Gerado por`gerar_artifact.py`; nunca editar direto      |
| `plano_HOSP-002_custo_operacional.md`       | Investigação do custo operacional                       |
| `plano_EDU-005_remediacao_parecer.md`       | Remediação da EDU-005                                   |
| `parecer_EDU-005_auditoria_independente.md` | Parecer que disparou a remediação                       |
| `plano_EDU-004_confirmacao_legal.md`        | **Prejudicado** — perseguia pendência inexistente |
| `AUDITORIA_CEO_pre-revisao.bak`             | Versão anterior deste relatório, com as tabelas erradas |
