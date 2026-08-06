# Parecer de auditoria independente — Frente EDU-005

**Objeto:** Enxugamento do apoio escolar não pedagógico medido por fronteira de eficiência
**Faixa sob exame:** piso R$ 599.876,04 · central R$ 666.512,27 · teto R$ 692.103,62
**Data:** 3 de agosto de 2026
**Natureza:** revisão independente de metodologia, dado e respaldo legal, com recomendações de aprimoramento

---

## 1. Escopo do que foi verificado

Foram examinados diretamente, e não por resumo:

| Item | Fonte |
|---|---|
| Redação da frente | `cardapio_unificado.html`, bloco `EDU-005` |
| Modelo | `Educação/Scripts/dea_eficiencia_escolas.py` (503 linhas, 17/06/2026) |
| Resultado | `DEA_Eficiencia_Escolas_SeteLagoas.xlsx`, 5 abas |
| Entradas | `MatriculasEscola_SeteLagoas.xlsx`, `ideb.xlsx`, `professor por escola.xlsx` |
| Base legal | LC nº 80/2003 (PCCV da Educação), texto integral |

**Conferência aritmética: aprovada sem ressalva.** As três pontas da faixa reproduzem exatamente a
planilha:

- Teto = R$ 51.909,07 × 13,333 = R$ 692.103,63 (publicado R$ 692.103,62 — diferença de 1 centavo,
  o mesmo arredondamento de gerador já registrado no `CLAUDE.md` do projeto para os totais da Educação)
- Central = R$ 49.989,67 × 13,333 = R$ 666.512,27 ✓
- Piso = R$ 49.989,67 × 12 = R$ 599.876,04 ✓
- 27 contratos, 17 escolas, 95,1 posições de excesso total, 69,6 em atrição ✓

**Nenhum número precisa mudar por erro de cálculo.** As observações abaixo são de método, de
composição do dado e de redação — não de aritmética.

---

## 2. Opinião geral

A frente tem mérito real e três qualidades que merecem registro antes de qualquer crítica:

1. **O filtro de estabilidade é correto e bem implementado.** Limitar o corte a `SERV.PUBL. CARGO
   TEMPORARIO` e `SERV.PUBL. CONTRATADO`, preservando efetivos, é juridicamente sólido e está
   codificado sem exceção. A decomposição "demissão imediata vs. atrição" (27 + 69,6 = 95,1) impede
   que o número de 95 circule como economia disponível. Isso é honestidade metodológica de bom nível.

2. **O box "piso-zero" é o melhor parágrafo da frente.** Declarar que nas 14 escolas efetivamente
   medidas o corte dá zero é uma admissão que a maioria dos trabalhos desse tipo esconde. Ela deve
   ser preservada — e, como se verá em §3.8, levada até a última consequência.

3. **O `math.ceil` no alvo por cargo** (linha 318 do script) arredonda o parâmetro a favor da escola
   e cria, na prática, um piso de 1 servidor por cargo em qualquer unidade com pelo menos 1 aluno.
   É uma escolha conservadora e acertada, provavelmente não deliberada, mas que protege as unidades
   pequenas do absurdo de "0,3 auxiliar de secretaria".

**Ressalva principal.** A frente é apresentada como medição de eficiência escola a escola. O que o
modelo entrega, na configuração atual, é um **corte linear de 10,5% sobre o quadro de apoio,
truncado pelo número de temporários**, aplicado majoritariamente a unidades de educação infantil
com um parâmetro derivado exclusivamente de escolas de ensino fundamental. A direção do resultado é
defensável; o mecanismo que a produz não é o que o texto diz que é. Isso é corrigível, e com esforço
baixo — as recomendações de §4 são quase todas de dado, não de modelagem nova.

---

## 3. Achados, por materialidade

### 3.1 · ALTO — A fronteira foi estimada em ensino fundamental e aplicada a creche

Este é o achado central.

As 14 escolas que sustentam o modelo têm IDEB. IDEB só existe para ensino fundamental. O escore
médio θ = 0,895 dessas 14 unidades foi aplicado às outras 40, e é dele que saem **os 27 contratos —
todos eles**.

A composição da matrícula das 17 escolas que sofrem corte:

| Etapa | Alunos nas escolas cortadas |
|---|---|
| Creche (0 a 3 anos) | 1.084 |
| Pré-escola | 1.413 |
| **Educação infantil (subtotal)** | **2.497 (80,5%)** |
| Ensino fundamental | 604 (19,5%) |

**Doze das 17 escolas cortadas têm matrícula de ensino fundamental igual a zero** — são unidades
100% de educação infantil (Paulo Moreira da Costa, Milton Campos, Joselita Dias, Stella Drumond,
São Vicente de Paulo, Juvenal Machado, Maria Lourdes, Marisa Mara, Menino Deus, Padre Tarcizo,
Nemésio Teixeira, Jaime Rodrigues). Apenas uma unidade cortada é 100% fundamental.

E 25 dos 27 contratos são de **Servente Escolar** — a função mais diretamente ligada a limpeza,
troca e apoio à alimentação, que é justamente onde a creche demanda mais.

O parâmetro aplicado é de 0,0414 servente por aluno, ou **1 servente para cada 24,2 alunos**. Aplicá-lo
a uma turma de berçário, com o mesmo peso de uma turma de 5º ano, não se sustenta operacionalmente
nem perante o financiamento: o próprio Fundeb pondera creche em tempo integral com o maior fator de
custo-aluno de toda a educação básica, exatamente porque custa mais atender essa etapa. **O modelo de
despesa está ignorando a diferenciação de etapa que o modelo de receita da rede considera obrigatória.**

Consequência para a redação atual: a pendência hoje registrada — "obter IDEB para as 40 escolas que
recebem escore imputado" — **é impossível de cumprir para as unidades de educação infantil**, porque
o indicador não existe para essa etapa. Não é dado faltando; é incomensurabilidade. A pendência
precisa ser reescrita.

### 3.2 · ALTO — O escore imputado não mede eficiência; ele mede tamanho de quadro

Para as 40 escolas sem IDEB, o script calcula (linha 297) `excesso = (1 − 0,895) × apoio_total`.
Como θ é constante, o excesso vira função linear do tamanho do quadro. Verificado empiricamente
sobre a planilha:

- correlação entre excesso estimado e **tamanho do quadro de apoio**: **0,999**
- correlação entre excesso estimado e **razão apoio/aluno** (a medida natural de desproporção): **−0,199**

Ou seja: o excesso imputado é quase perfeitamente explicado pelo tamanho do quadro e é levemente
**anticorrelacionado** com a desproporção real. Não há conteúdo diagnóstico nessa etapa — é um
haircut de 10,5% uniforme.

O efeito prático aparece nos extremos. As três escolas com pior razão apoio/aluno da rede **não
sofrem corte nenhum**:

| Escola | Alunos | Apoio | Razão | Serventes / alvo / temporários | Corte |
|---|---|---|---|---|---|
| Regina Vitalino Botelho | 20 | 6 | 0,300 | 3 / 1 / 1 | **0** |
| Adélia Figueiredo | 22 | 4 | 0,182 | 2 / 1 / 1 | **0** |
| Renato T. Guimarães | 40 | 5 | 0,125 | 2 / 2 / 1 | **0** |
| *comparar:* Stella Drumond | 229 | 22 | 0,096 | — / — / 11 | **2** |

Regina Vitalino tem 1 servidor de apoio para cada 3,3 alunos, excesso de 2 serventes identificado
pelo próprio benchmark e 1 temporário disponível — e corta zero. O motivo é mecânico: o teto DEA de
0,105 × 6 = 0,63 posição arredonda para zero antes do filtro de vínculo. **O modelo protege
sistematicamente as unidades pequenas com pior razão, porque o teto é proporcional ao tamanho do
quadro, não à desproporção.**

Registro de justiça, para não exagerar o achado: na média, as escolas cortadas têm razão pior
(0,092) do que as não cortadas (0,069). O modelo não é aleatório. Mas **quem produz esse sinal é o
benchmark por cargo, não o DEA** — o DEA entra apenas como freio, e freia na direção errada. Isso
tem consequência direta na recomendação de §4.2.

Risco de exposição: a planilha é auditável por terceiros. A pergunta "por que a escola com 1 servidor
para 3,3 alunos não foi tocada e a que tem 1 para 10,4 perdeu duas posições?" não tem resposta
defensável hoje.

### 3.3 · ALTO — A base de IDEB tem 14 linhas; a limitação é da extração, não do INEP

`ideb.xlsx` contém exatamente 14 registros, todos de escolas municipais de ensino fundamental, todos
com IDEB preenchido. Não há linhas vazias, não há escolas com IDEB nulo.

Isso reposiciona completamente a limitação. A frente afirma que "apenas 14 das 54 escolas têm IDEB
divulgado". O que a evidência mostra é que **apenas 14 escolas foram carregadas na base de entrada.**
O INEP divulga IDEB por escola em planilha pública para toda unidade de ensino fundamental com
participação suficiente no Saeb. Sete Lagoas tem cerca de 44 unidades com matrícula de fundamental
ou infantil, e é implausível que apenas 14 tenham indicador divulgado.

**Esta é a melhor oportunidade de aprimoramento da frente, e é barata.** Completar a extração do
IDEB do INEP é tarefa automatizável (download de planilha pública + join por código INEP, que já é
a chave `ID_ESCOLA` usada no modelo). Se a cobertura subir de 14 para, digamos, 30 escolas de
fundamental, o DEA passa a medir de fato uma parcela relevante da rede e o selo da frente pode subir
de "Respaldo médio" para forte na parte de ensino fundamental.

### 3.4 · ALTO — A base de matrícula já traz a etapa, e o modelo joga fora

`MatriculasEscola_SeteLagoas.xlsx` contém as colunas `MAT_CRECHE`, `MAT_PRE`, `MAT_INF_TOTAL`,
`MAT_FUND_I`, `MAT_FUND_II`, `MAT_FUND_TOTAL`, `MAT_EM`, `MAT_EJA`. **O modelo usa apenas
`MAT_TOTAL`.**

É o padrão de dado órfão já documentado no `CLAUDE.md` global do usuário para o projeto de Santa
Luzia: o dado necessário existe, foi coletado, e não chega ao cálculo. Aqui o custo é direto —
tratar um bebê de berçário e um aluno de 8º ano como uma unidade equivalente de demanda por servente
é o que produz o achado 3.1.

Correção sugerida em §4.1. Não exige coleta nova.

### 3.5 · MATERIAL — Temporário de substituição não é posição excedente

`DEMITIVEL = {"SERV.PUBL. CARGO TEMPORARIO", "SERV.PUBL. CONTRATADO"}` trata todo temporário como
corte disponível. A LC nº 80/2003 (art. 6º, parágrafo único) estabelece que a contratação por tempo
determinado "será em caso de **substituição, aposentadoria, férias e licenças** previstas em lei".

Se parte dos 27 contratos cobre efetivo afastado por licença, a posição **não é excedente**: o
efetivo permanece na folha e o corte não gera economia — gera desassistência na unidade. O modelo
não distingue os dois casos, e a base de folha usada (uma linha por servidor, com tipo de contrato)
provavelmente permite essa distinção via motivo de contratação ou vínculo de substituição.

**Verificação recomendada antes de qualquer comunicação a escola.** É plausível que reduza a
contagem de 27.

### 3.6 · MATERIAL — A lei municipal fortalece o corte e ameaça a permanência da economia

Dois dispositivos da LC nº 80/2003 puxam em direções opostas, e ambos deveriam estar no cardápio:

**A favor.** Servente Escolar, Auxiliar de Secretaria, Assistente de Turno e Assistente de Biblioteca
são cargos do quadro permanente da SME (art. 4º e Anexo I; art. 27, IV, alíneas *l*, *m*, *n*, *p*,
com gratificação de 10%). Contrato por tempo determinado é definido (art. 3º, XVIII) como regime
especial "com a mesma denominação, remuneração e atribuições do cargo efetivo correspondente", e o
art. 6º, parágrafo único, I limita a vacância a **6 meses, prorrogável uma única vez**. Contratos que
ultrapassem 12 meses fora das hipóteses legais são irregulares por força da própria lei municipal.
**Não renová-los deixa de ser escolha de gestão e vira dever de conformidade** — isso eleva o
respaldo jurídico da frente, não o reduz.

**Contra.** O mesmo art. 6º, parágrafo único, II determina que "durante o período de contratação,
obrigatoriamente, deverá ser realizado Concurso Público para preenchimento do cargo vago". Se a
necessidade é permanente — e para servente escolar em creche muito provavelmente é —, o município
terá de prover por concurso. **Servidor efetivo custa mais que temporário**: encargo patronal de
regime próprio, progressão na carreira, gratificação de 10% do art. 27, estabilidade. A economia
pode ser transitória e, no horizonte de 24 a 36 meses, inverter-se.

**Pendência que falta no cardápio:** verificar se há concurso vigente ou cadastro de reserva para
Servente Escolar. Se houver candidatos aprovados aguardando nomeação, a economia de R$ 600 mil é
contábil e efêmera — troca-se temporário por efetivo mais caro.

### 3.7 · MATERIAL — O piso ×12 subestima por construção, e o custo de saída não está no cálculo

O piso multiplica a folha mensal por 12, "sem décimo terceiro nem terço de férias". Isso não é
conservadorismo: **ao encerrar o contrato, o município efetivamente deixa de pagar 13º e o terço** —
verbas devidas ao temporário. Retirá-las do piso remove economia que de fato ocorre, sem tratar
nenhuma das incertezas que realmente ameaçam a frente.

Em compensação, dois efeitos reais estão ausentes:

- **Custo de rescisão** (saldo, 13º proporcional, férias proporcionais + 1/3) reduz o ano 1;
- **Timing de execução** — corte a partir do 4º mês entrega 9/12 do valor anual, não 12/12;
- **Encargos patronais** não entram no cálculo, que usa proventos brutos (linha 195). Isso
  **subestima** a economia recorrente, e é o único viés na direção favorável. Deve ser registrado
  como upside, não incorporado sem apuração.

Piso mais honesto e mais defensável = **economia do ano 1 com execução parcial e líquida de
rescisão**, sobre a contagem de contratos que sobreviver às verificações de §3.5 e §4. Ver §4.5.

### 3.8 · MATERIAL — Tensão de comunicação entre o box "piso-zero" e o piso de R$ 599 mil

A frente afirma, corretamente e com coragem: *"Onde a eficiência foi de fato medida, o corte dá
zero."* E em seguida publica piso de R$ 599.876,04.

Um leitor crítico — TCE-MG, câmara municipal, sindicato — vai colocar as duas frases lado a lado. O
documento tem precedente próprio para resolver isso: **três frentes da Saúde declaram piso R$ 0**
justamente porque não há valor validado que sustente piso maior, e a Parte II explica que "o piso
zero protege o gestor de anunciar economia que a evidência ainda não sustenta".

EDU-005 está exatamente nessa situação e não aplicou o próprio critério do documento. Recomendação
em §4.5.

### 3.9 · MÉDIO — 92% da frente é servente escolar, e isso reabre o acoplamento com EDU-003

| Cargo | Contratos | Folha mensal | Peso |
|---|---|---|---|
| Servente Escolar | 25 | R$ 47.870,67 | 92,2% |
| Auxiliar de Secretaria | 1 | R$ 2.171,00 | 4,2% |
| Assistente de Turno | 1 | R$ 1.867,40 | 3,6% |

O título "apoio escolar não pedagógico" sugere amplitude que o resultado não tem. Nenhum vigia foi
cortado (todos efetivos). A frente é, operacionalmente, **uma frente de servente escolar**.

Isso tem duas consequências:

- A **independência declarada** em relação às demais frentes da Educação é mais frágil do que o texto
  sugere. Servente é a função mais acoplada a EDU-003 (fim da segunda merenda).
- Mas o cardápio hoje trata essa interação apenas como **risco**, e ela é também **sinergia**: se
  EDU-003 elimina a segunda refeição diária, a carga de trabalho de servente **cai**, e o excesso
  medido depois de EDU-003 será maior e mais defensável, não menor. Sequenciar EDU-003 → remedição
  → EDU-005 fortalece as duas frentes. Vale inverter parte do enquadramento.

### 3.10 · MÉDIO — Parâmetro proporcional puro é inadequado para funções de perímetro e turno

Vigia de Educação e Assistente de Turno recebem parâmetro de 0,0063 servidor por aluno (1 para
158,7). Vigilância é função de **perímetro e cobertura de turno**: uma escola de 100 e uma de 800
alunos precisam de número semelhante de vigias para cobrir os mesmos turnos. Assistente de turno,
pelo próprio nome, escala com **turnos e turmas**, não com matrícula. Auxiliar de Secretaria tem
piso fixo — toda unidade precisa de secretaria funcionando, com 50 ou com 500 alunos.

O `math.ceil` já cria um piso implícito de 1 (elogiado em §2), mas de forma acidental. A forma
correta é **parâmetro com intercepto**: `alvo = a + b × alunos`, com `a` refletindo a cobertura
mínima por turno ou por prédio. É o padrão em dimensionamento de quadro e elimina a distorção sem
mudar a lógica do resto do pipeline.

### 3.11 · MÉDIO — Ausência de controle socioeconômico

O DEA trata IDEB como produto e apoio como insumo, sem controlar nível socioeconômico do alunado.
Escolas com público mais vulnerável tendem a ter IDEB menor por razões alheias ao quadro de apoio —
e serão marcadas como ineficientes, sofrendo corte justamente onde a necessidade de apoio é maior.

O INSE (Indicador de Nível Socioeconômico) do INEP está disponível por escola e cobre as mesmas
unidades do IDEB. Incluí-lo como variável não discricionária, ou usá-lo em regressão de segundo
estágio sobre os escores, é prática consolidada. **Risco de equidade e risco reputacional**, além de
técnico.

### 3.12 · MÉDIO — Escores sem intervalo de confiança, com 14 unidades

DEA é determinístico e sensível a outlier e a erro de medida. Com 14 DMUs, 1 insumo e 2 produtos, o
modelo passa por pouco na regra prática de dimensionamento (n ≥ 3(m+s) = 9), e o BCC com insumo único
tende a inflar o número de unidades na fronteira — a distribuição observada confirma: mediana 0,9595,
quartil superior 1,000, mínimo 0,645, desvio-padrão 0,133.

O θ_médio de 0,895, que sozinho determina 100% do resultado financeiro, é portanto uma estimativa
pontual sobre amostra pequena e dispersa, apresentada sem incerteza.

Recomendação barata: **bootstrap de Simar-Wilson**, ou no mínimo um jackknife (retirar uma DMU por
vez e observar a variação de θ_médio). Transformar "θ = 0,895" em "θ = 0,895 [IC 0,84–0,94]" custa
minutos de processamento e dá à faixa uma base estatística que hoje ela não tem.

### 3.13 · BAIXO — Higiene de código com efeito de auditoria

Pontos que não alteram resultado, mas que um auditor externo encontra e usa:

- **Docstring divergente da implementação.** As linhas 17-19 descrevem o grupo B como tratado por
  "benchmark de razão do relatório, alvo = teto 0,0690 servidor/aluno". O código executa
  `(1 − θ_médio) × apoio` (linha 297). São metodologias diferentes. A aba *Metodologia* da planilha
  está correta; apenas o cabeçalho do script descreve uma versão anterior. Quem ler o script conclui
  método diferente do executado.
- **Constante morta.** `TETO_REDE = 0.0690` (linha 72) é definida e nunca usada.
- **Inconsistência entre parâmetros.** A soma dos benchmarks por cargo é 0,0414 + 0,0138 + 3 × 0,0063
  = **0,0741**, acima do teto de rede declarado de **0,0690**. Os dois parâmetros são mutuamente
  incompatíveis; convivem no arquivo porque um deles não é aplicado.
- **Fator anual divergente entre frentes do mesmo cardápio.** EDU-001 usa 13,3; EDU-005 usa 13,333.
  O correto conceitualmente é 13,333 (12 + 1 + ⅓). Padronizar.
- **Match sem garantia de bijetividade.** `construir_crosswalk` aceita fuzzy ≥ 0,80 e não verifica se
  duas escolas da folha mapearam para o mesmo `ID_ESCOLA`. Um colapso silencioso duplicaria ou
  perderia quadro sem aviso. Um `assert` de unicidade resolve.
- **Sem guarda de sanidade para matrícula zero.** O grupo A filtra `MAT_TOTAL > 0` (linha 271); o
  grupo B não. Foi exatamente por essa porta que entrou o caso Isis da Silva Oliveira. Verificado:
  há **duas** escolas com matrícula zero na base — Isis e o CAIC. O CAIC não gerou falso positivo
  apenas porque tem quadro de apoio zero. A menção do cardápio a um único caso está correta quanto
  ao efeito, mas a fragilidade estrutural é maior do que um caso isolado.

  Nota de precisão sobre a redação atual: o cardápio afirma que, na Isis, "todo o seu quadro de apoio
  foi lido como excesso". O benchmark de fato leu os 10; o teto DEA conteve em 1,1, e o corte final
  foi 1. A conclusão (excluir o contrato) está certa; a descrição do mecanismo, não.

### 3.14 · A VERIFICAR — A economia é caixa livre ou permanece carimbada?

Ponto de finanças educacionais ausente do cardápio, e material para o cliente.

Despesa com apoio escolar integra a manutenção e desenvolvimento do ensino. Duas verificações
mudam o significado da economia:

- **Piso constitucional de 25% (art. 212 da CF).** Se Sete Lagoas aplica próximo ao mínimo, reduzir
  despesa de MDE **não libera caixa livre** — o recurso continua vinculado e precisa ser reaplicado
  em educação. A frente entregaria realocação, não economia orçamentária. Se o município aplica com
  folga, a leitura muda.
- **Fundeb e o mínimo de 70% (Lei nº 14.113/2020, art. 26).** É preciso saber por qual fonte esses
  27 contratos são pagos. O enquadramento de servente escolar como "profissional da educação básica"
  para fins dos 70% remete ao art. 61 da LDB e **não é pacífico entre os tribunais de contas**. Se
  esses contratos compõem a base dos 70%, cortá-los reduz o numerador e pode pressionar o
  cumprimento do mínimo.

**Recomendação:** identificar a fonte de recurso de cada um dos contratos antes de apresentar a
faixa como economia disponível. Sem isso, a frente pode entregar ao cliente um número que o
orçamento não consegue converter em folga fiscal.

**Nota favorável, no sentido oposto:** qualquer que seja a fonte, a redução de despesa de pessoal
melhora a posição no limite da LRF (art. 169 da CF e art. 19-20 da LRF). Esse é um benefício
colateral real, mensurável e hoje não mencionado.

---

## 4. Recomendações, em ordem de retorno sobre esforço

### 4.1 · Estratificar por etapa — esforço baixo, impacto alto

Substituir `MAT_TOTAL` por **matrícula ponderada por etapa**, usando as colunas que já existem na
base. Referência de ponderação disponível e defensável: os fatores de custo-aluno do próprio Fundeb,
que já reconhecem creche como a etapa mais intensiva. E rodar **modelos separados para educação
infantil e ensino fundamental** — são funções de produção distintas, com quadro de apoio distinto e
indicadores de resultado distintos.

Resolve 3.1 e 3.4 de uma vez. Não exige coleta nova.

### 4.2 · Decidir qual é o método principal — esforço baixo, impacto alto

O diagnóstico de §3.2 é claro: quem seleciona posições é o benchmark por cargo; o DEA entra como
freio e freia na direção errada. Duas saídas legítimas, e a frente precisa escolher uma:

- **(a) Consertar o DEA** — completar o IDEB (§4.3), estratificar (§4.1), incluir INSE (§3.11). A
  fronteira passa a medir de fato, e o teto por escola volta a ter conteúdo.
- **(b) Assumir o benchmark como método principal**, documentar sua origem (pendência bloqueante já
  registrada e ainda aberta) e usar o DEA apenas como camada de validação nas 14 escolas onde ele é
  legítimo.

A opção (b) é mais rápida e mais honesta com o que o modelo realmente faz hoje. A (a) é mais forte
se houver janela. **O que não se sustenta é a configuração atual**, que apresenta (a) e executa algo
próximo de (b) com um freio arbitrário no meio.

### 4.3 · Completar a base de IDEB — esforço baixo, impacto alto

Baixar a série de IDEB por escola do INEP e refazer o join por código INEP (`ID_ESCOLA` já é a
chave). Tarefa automatizável de ponta a ponta. Se a cobertura subir de 14 para a maior parte das
unidades de fundamental, a frente deixa de depender de imputação para essa etapa e o selo pode ser
revisto.

Resolve 3.3, e é pré-requisito para 4.2(a).

### 4.4 · Verificações de campo antes de qualquer comunicação — esforço médio, bloqueantes

Quatro, em ordem:

1. **Natureza de cada contrato temporário** — substituição de efetivo afastado *versus* vaga
   estrutural (§3.5). Reduz a contagem de 27 para o número real de posições excedentes.
2. **Existência de concurso vigente ou cadastro de reserva** para Servente Escolar (§3.6). Determina
   se a economia é permanente ou transitória.
3. **Fonte de recurso** de cada contrato — MDE, Fundeb 70%, Fundeb 30%, recursos próprios (§3.14).
   Determina se a economia vira folga fiscal.
4. **Matrícula corrente** de Isis da Silva Oliveira e das quatro unidades hoje fora da análise
   (CEMEI Magda Macedo Coelho, CEMEI Padre Adrianus, Creche Flor Amarela Brígida Postorino, Creche
   São José Operário) — pendência já registrada no cardápio, mantida.

### 4.5 · Reconstruir a faixa sobre a incerteza real — esforço baixo, impacto alto na credibilidade

Hoje o que separa piso, central e teto é (i) um caso de dado errado e (ii) incluir ou não o 13º.
Nenhuma das três pontas reflete a incerteza que de fato ameaça a frente, que é ordens de grandeza
maior. Estrutura sugerida:

| Ponta | Base proposta |
|---|---|
| **Piso** | Apenas contratos confirmados escola a escola pela SME, líquidos de rescisão e com execução parcial no ano 1. Enquanto as verificações de §4.4 não ocorrerem, **R$ 0** — aplicando a EDU-005 o mesmo critério que o documento já aplica a três frentes da Saúde. |
| **Central** | Benchmark por cargo estratificado por etapa (§4.1), com origem do parâmetro documentada. |
| **Teto** | Modelo integral atual, mantido como limite superior teórico. |

Isso resolve 3.7 e 3.8 e alinha EDU-005 ao padrão metodológico do próprio cardápio.

### 4.6 · Aprimoramentos técnicos — esforço baixo, impacto médio

- Parâmetro com intercepto (`a + b × alunos`) para vigia, assistente de turno e auxiliar de
  secretaria (§3.10).
- Bootstrap ou jackknife sobre θ, publicando intervalo (§3.12).
- Corrigir docstring, remover `TETO_REDE`, reconciliar 0,0741 vs 0,0690, padronizar o fator para
  13,333, `assert` de bijetividade no crosswalk, guarda de sanidade para matrícula zero (§3.13).

### 4.7 · Sequenciar com EDU-003 como sinergia, não só como risco

Executar EDU-003, remedir carga de trabalho de servente por unidade, e então executar EDU-005 sobre
a carga nova. Fortalece as duas frentes e retira a objeção mais previsível — cortar limpeza sem
saber quanto trabalho sobrou.

---

## 5. Efeito sobre a redação do cardápio

Nada aqui exige refazer o cálculo. Cinco ajustes de texto, todos dentro do que a evidência já
suporta:

1. **Reescrever a pendência de IDEB.** Hoje: "obter IDEB para as 40 escolas". Ela é (i) impossível
   para as unidades de educação infantil, que são a maioria das cortadas, e (ii) provavelmente
   trivial para boa parte das de fundamental, porque a limitação é da extração. São duas pendências
   distintas e devem aparecer separadas.
2. **Declarar a composição por etapa.** Que 80,5% da matrícula das escolas cortadas é educação
   infantil, e que o parâmetro aplicado vem exclusivamente de escolas de ensino fundamental, é
   informação que o leitor precisa ter. Omiti-la é o maior risco de credibilidade da frente.
3. **Nomear o que o modelo faz.** O box "piso-zero" já anda 80% do caminho. Falta dizer que, no
   grupo imputado, o excesso é proporcional ao tamanho do quadro (correlação 0,999) e não à
   desproporção observada.
4. **Acrescentar as duas pendências ausentes** — concurso/cadastro de reserva (§3.6) e fonte de
   recurso (§3.14).
5. **Acrescentar o respaldo legal favorável.** A LC nº 80/2003, art. 6º, parágrafo único, I, limita
   o contrato temporário a 12 meses. Isso reforça a frente e hoje não está no documento. Diferente
   de EDU-004, aqui o dispositivo foi localizado e lido no texto integral.

Com os itens 1 a 5 aplicados e as verificações de §4.4 concluídas, o selo "Respaldo médio" está
adequado e pode subir na parte de ensino fundamental. **Sem elas, a frente é sustentável como
hipótese de trabalho, mas não deve ser apresentada como medição escola a escola** — e é assim que o
título e a proposta a apresentam hoje.

---

## 6. Conclusão

EDU-005 identifica um problema real. Quadro de apoio não pedagógico dimensionado por contratação
temporária escola a escola, sem norma vinculada, é exatamente onde se acumula despesa sem
contrapartida — e o filtro de estabilidade, a decomposição entre demissão e atrição e o box
"piso-zero" mostram um trabalho feito com cuidado e com honestidade sobre os próprios limites.

O que precisa mudar não é a tese. É a distância entre o que o texto promete — medição de eficiência
escola a escola — e o que o modelo entrega na configuração atual: um corte proporcional de 10,5%,
truncado por vínculo, aplicado em 80% a unidades de educação infantil com parâmetro de ensino
fundamental.

Duas recomendações têm retorno desproporcional e custo de horas, não de semanas: **estratificar por
etapa** (§4.1), usando colunas que já estão na base, e **completar a extração do IDEB** (§4.3), que é
dado público. Juntas, elas atacam os dois achados de maior materialidade e podem mover a frente de
"hipótese de trabalho bem construída" para "medição defensável perante o TCE-MG".

A faixa financeira, tal como publicada, está aritmeticamente correta. A ressalva é sobre o que ela
representa, não sobre quanto ela soma.

---

*Parecer emitido em revisão independente sobre `dea_eficiencia_escolas.py`, `DEA_Eficiencia_Escolas_SeteLagoas.xlsx`, bases de matrícula e IDEB, e LC nº 80/2003 (texto integral). Todos os valores citados foram reconferidos contra a planilha de origem.*
