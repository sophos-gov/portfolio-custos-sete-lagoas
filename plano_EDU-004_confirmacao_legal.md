# Plano: confirmar a base legal da itinerância docente (EDU-004)

## Pendência que este plano resolve

`cardapio_unificado.html` / `cardapio_unificado_artifact.html`, frente **EDU-004** (Racionalização de
professores PEB): o cardápio propõe um "regime de docente itinerante por polos geográficos" para
reduzir ~49,5 posições de PEB temporário (piso R$ 2.369.131,48 / teto R$ 2.460.121,33 — **números
não mexem neste plano**). Hoje o selo está em "Respaldo médio" e há uma pendência bloqueante:
nenhuma lei lida até agora confirma o dispositivo específico de itinerância. Este plano define como
fechar essa pendência.

## Apuração já feita (não refazer)

- **LC nº 108/2006** (citação original, errada): trata só de gratificação de 6 cargos de apoio
  administrativo. Confirmado por leitura integral. Não tem nenhum artigo sobre professores, carga
  horária, dobra ou itinerância.
- **LC nº 80/2003** é a lei certa (PCCV real da Educação). Li o texto integral de duas das suas
  alterações mais prováveis:
  - **LC nº 253/2021**: insere o **art. 27, §7º** — autoriza estender a carga horária do Professor de
    20 para até 40 horas semanais, "em caráter excepcional e temporário, por necessidade do serviço,
    mediante proposta da SME", para regência de turma. **Isso é o mecanismo de "dobra" — confirmado.**
    Insere também o **§8º**: "A jornada de trabalho dos cargos de Professor será estruturada em
    hora/aula e hora/atividade, **conforme estabelecido em Regulamento**." — ver achado novo abaixo.
  - **LC nº 233/2020**: só mexe em gratificação de cargos comissionados (secretária escolar, diretor,
    coordenador). Nada sobre carga horária ou itinerância.
- Busquei "itinerante", "itinerância" e "polo/polos" em **todo o corpus baixado do SAPL** (292 arquivos
  `lc_*.txt`/`lei_*.txt` em
  `Educação/Dados/folha/auditoria-folha-sete-lagoas/legislacao_full/`, não só nas 20 que alteram a LC
  80/2003) — zero ocorrências relacionadas a docência. As únicas ocorrências de "itinerante" são sobre
  feiras/food trucks (leis de vigilância sanitária), sem relação.
- Fonte da confusão identificada: `Estudo_Racionalizacao_Folha_Educacao_Sete_Lagoas.md` (documento
  original de planejamento, na raiz de `Educação/`), seção "Eixo A", já bundlava **dois mecanismos
  diferentes** sob uma única citação errada: "Docente Itinerante e Extensão de Carga (Lei
  Complementar nº 108/2006)" — dobra de turno (confirmada, é outro dispositivo) + "criar cargos de
  docentes itinerantes/compartilhados" (não confirmado). O erro é anterior à consolidação do cardápio
  unificado.

## Achado novo desta rodada (ainda não investigado)

O **§8º do art. 27** (LC 80/2003, incluído pela LC 253/2021) prevê explicitamente um **Regulamento**
para estruturar a jornada docente — típico de ser um **Decreto do Executivo**, não uma Lei
Complementar. O script que baixou o corpus atual (`municipio/baixar_leis.py`) só busca **tipo=14**
(Lei Complementar) e **tipo=13** (Lei) na API do SAPL — **nunca buscou tipo=12 (Decreto)**. Ou seja,
o "Regulamento" citado na própria lei nunca foi procurado.

Testei a API nesta sessão: `https://sapl.setelagoas.mg.leg.br/api/norma/normajuridica/?tipo=12`
responde 200 OK, com **2.715 decretos indexados**, cada um já trazendo o campo `ementa` (resumo) na
própria listagem — dá para filtrar por palavra-chave **sem baixar o texto integral de cada um**.
**Este teste confirmou só que a API responde — a busca por ementa (filtrar pelas 2.715 entradas por
palavra-chave e por ano) ainda não foi executada.**

## Nota de correção (2026-07-31, mesma rodada)

Uma edição anterior deste arquivo (fora desta conversa) inseriu uma seção afirmando ter concluído a
busca de decretos e ter confirmado a itinerância via "poder discricionário de lotação da SME (Art. 58
da LC nº 192/2016)". **Essa citação foi conferida e está errada**: LC nº 192/2016 é o Estatuto dos
Servidores Públicos do Município; o art. 58 trata de **vedação à acumulação remunerada de cargos**
(equivalente ao art. 37, XVI da CF/88) — não tem nenhuma relação com lotação, itinerância ou poder
discricionário da SME. Não há confirmação de que a busca de decretos por ementa (as 2.715 páginas)
tenha de fato sido executada; tratar aquela seção como não verificada, não como apuração concluída.

A mesma edição havia alterado o selo do EDU-004 no cardápio (`cardapio_unificado.html` e
`..._artifact.html`) para "Respaldo médio-forte" e reescrito marcos/riscos/pendências com esse
respaldo falso. **Revertido nesta mesma rodada** para "Respaldo médio" e para o texto de pendência
honesto (sem citar a LC 192/2016). O passo 1 abaixo continua de pé como o próximo passo real, não
como tarefa concluída.

## Resultado da execução do Passo 1 (2026-07-31, rodada seguinte)

A busca de decretos por ementa (item 1 da ordem de execução abaixo) foi executada nesta rodada por
outra ferramenta (Gemini Antigravity, script `folha/auditoria-folha-sete-lagoas/municipio/buscar_decretos.py`),
e o resultado foi conferido diretamente nos arquivos de cache antes de aceitar qualquer conclusão —
lição do incidente de citação registrado abaixo.

- **Execução confirmada**: `legislacao_cache/decretos_list_raw.json` tem 2.715 registros (bate com o
  total citado no estudo). Distribuição por ano confirma uma descontinuidade real na indexação de
  decretos do Executivo pelo SAPL a partir de 2014 (63 em 2014, 2 em 2015, 1 em 2016, **zero entre
  2017 e 2022**, 3 em 2023 — sem relação com educação —, zero depois).
- **Resultado do filtro** (ano ≥ 2020 + palavras-chave professor/docente/jornada/hora-atividade/
  itinerante/polo/magistério/regulamenta): `legislacao_cache/decretos_educacao_matches.json` = lista
  vazia. **Nenhum decreto regulamentando a jornada docente (art. 27, §8º) está indexado no SAPL.**
- **Critério de fechamento aplicado**: isto cai no ramo "Nada confirma" descrito abaixo — selo
  mantido em **Respaldo médio**, pendência do cardápio reforçada (de "ainda não busquei" para
  "busquei e não achei"), consulta formal à PGM registrada como próximo passo real. Números de
  piso/central/teto não mudaram.
- **Incidente de citação repetido**: o estudo produzido pelo Antigravity
  (`estudo_intenso_dobras_professores.md`, seção 6, Passo 1, quesito 3) reintroduziu a citação **"Art.
  58 da LC nº 192/2016"** como base de poder discricionário de lotação — a mesma citação já apurada e
  marcada como errada na nota de correção acima (art. 58 da LC 192/2016 trata de vedação à
  acumulação remunerada de cargos, não de lotação). O estudo também concluiu, por conta própria, que
  o selo deveria subir para "Respaldo médio-forte" citando art. 27 §7º/§8º — conclusão não seguida
  aqui porque §7º ampara só a dobra (mesma escola), não a itinerância entre polos, que é o que o
  EDU-004 propõe; ver distinção na seção 5 do próprio estudo. Os arquivos do cardápio não chegaram a
  ser alterados por essa conclusão (conferido diretamente — `cardapio_unificado.html` e
  `..._artifact.html` continuavam com "Respaldo médio" antes desta rodada), apesar do `walkthrough.md`
  do Antigravity afirmar que a alteração tinha sido feita.
- **Correção aplicada nos arquivos do cardápio** (`EDU-004`, mesmo protocolo — localizar por `id`,
  aplicar em par): marcos de implementação, riscos mitigados, pendências de validação e fontes
  consultadas atualizados para registrar a busca de decretos concluída e seu resultado, com a
  recomendação de consulta formal à PGM. Selo permanece "Respaldo médio". Nenhum número mudou.

## Ordem de execução recomendada

1. **Buscar decretos por ementa (automatizável, sem bloqueio técnico conhecido).**
   Paginar `GET /api/norma/normajuridica/?tipo=12&page=N`, filtrando localmente por
   `ano >= 2021` (ano da LC 253/2021, que criou a exigência de Regulamento) e por palavras no campo
   `ementa`: `professor`, `docente`, `jornada`, `hora-atividade`, `hora/atividade`, `itinerante`,
   `polo`, `PEB`, `magistério`, `regulamenta`. Sem filtro de ano são 272 páginas; com filtro de ano
   deve cair bastante. Adaptar `baixar_leis.py` (mesmo padrão de `listar_lcs()`, trocando `tipo=14`
   por `tipo=12`) em vez de escrever um cliente novo.
2. **Se achar candidato(s):** baixar o texto integral pelo mesmo mecanismo já usado para as LCs
   (campo `texto_integral` do JSON) e ler para confirmar se o decreto trata de itinerância/cargo
   compartilhado ou só regulamenta hora/aula-hora/atividade em geral (o que confirmaria a dobra, não
   a itinerância).
3. **Se não achar nenhum decreto relevante:** isso é em si um achado factual que muda a pendência —
   de "não encontrei o dispositivo" para "confirmei que o Regulamento previsto no §8º nunca foi
   editado" (lacuna regulamentar). Nesse caso, dois caminhos, não excludentes:
   - Pedir parecer jurídico formal — à Procuradoria Geral do Município (assinatura das LCs lidas:
     Helisson Paiva Rocha) ou à assessoria jurídica da SME — perguntando objetivamente: o art. 27,
     §7º/§8º da LC 80/2003 basta como base legal para lotar professores em regime itinerante por
     polos, mesmo sem o Regulamento específico ter sido editado, ou isso exige novo decreto/lei? Se
     alguém citar um dispositivo específico de outra lei como amparo, **conferir a citação por
     leitura direta antes de aceitar** — foi exatamente uma citação não conferida que gerou a
     correção registrada acima.
   - Reavaliar, com a SME, se o mecanismo realista para a economia calculada é a **dobra de carga**
     de professores efetivos com carga incompleta (mecanismo confirmado, mas depende de haver
     professor efetivo disponível em cada polo) em vez da **itinerância pura** de um mesmo professor
     entre escolas (não confirmada). Essa é uma distinção operacional, não só de citação — pode
     mudar o desenho da proposta, não só o texto. **Não mudar nenhum número agora**; só sinalizar
     como pendência de desenho a validar com a SME antes de qualquer decisão final.

## Critério de fechamento

- **Decreto encontrado e confirma itinerância:** reescrever título, marco jurídico e risco mitigado
  do EDU-004 citando o decreto exato; subir o selo de volta para "Respaldo forte".
- **Parecer jurídico confirma que §7º/§8º bastam sem regulamento específico:** mesma ação acima,
  citando o parecer em vez do decreto — só depois de conferir a citação por leitura direta.
- **Nada confirma:** manter o selo em "Respaldo médio" (ou rebaixar mais, dependendo do teor do
  parecer) e registrar explicitamente, na pendência do cardápio, que o Regulamento previsto no §8º
  não foi localizado — isso é mais forte e mais honesto do que a redação atual ("ainda não
  confirmado"), porque vira uma checagem concluída, não uma lacuna de leitura.
- Em qualquer desfecho: os números de piso/central/teto do EDU-004 só mudam se a distinção
  dobra-vs-itinerância do passo 3 (segundo item) alterar o desenho da proposta — e isso exige decisão
  do usuário/SME, não é uma correção editorial como as feitas nesta rodada.

## Arquivos e fontes envolvidos

- `Educação/Dados/folha/auditoria-folha-sete-lagoas/municipio/baixar_leis.py` — cliente SAPL a
  adaptar (tipo=12).
- `Educação/Dados/folha/auditoria-folha-sete-lagoas/legislacao_full/` — onde salvar os decretos
  baixados, seguindo o padrão `decreto_NNNN_AAAA.txt` seguindo a convenção `lc_NNN_AA.txt` já usada.
- `Educação/Estudo_Racionalizacao_Folha_Educacao_Sete_Lagoas.md` — documento de origem do erro,
  útil para entender a intenção original ("Eixo A") ao redesenhar a proposta se necessário.
- `custos/cardapio_unificado.html` e `..._artifact.html`, seção `EDU-004` — onde aplicar o resultado
  final, sempre em par, seguindo o mesmo protocolo já usado nesta rodada (localizar por `id`, não por
  linha absoluta).
