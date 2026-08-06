export const meta = {
  name: 'auditoria-folha-municipio',
  description: 'Auditoria da folha do município de Sete Lagoas: panorama + teses A1–A5 (gerar→verificar) + eficiência + síntese McKinsey',
  phases: [
    { title: 'Panorama', detail: 'governing thought + sumário executivo a partir dos KPIs' },
    { title: 'Teses', detail: '5 teses jurídicas A1–A5, cada uma gerada e refutada adversarialmente' },
    { title: 'Eficiencia', detail: 'interpretação de Trilha B (custo) e Trilha C (quick wins)' },
    { title: 'Sintese', detail: 'matriz de priorização, envelope de oportunidade, riscos e pendências' },
  ],
}

const D = JSON.stringify(args.digest)
const BRIEF = args.brief_path
const LEIS_DIR = args.leis_dir
const CATALOGO = args.catalogo_path
const RELATORIO_SAUDE = args.relatorio_saude_path

const CONTEXTO = `
CONTEXTO DA AUDITORIA (município inteiro de Sete Lagoas/MG, competências mar/abr/mai 2026):
- Fonte folha: base pessoal.xlsx (SÓ PROVENTOS brutos; zero descontos — não há líquido nem teto líquido).
- Fonte metadados: cadastro(32).csv (snapshot 29/03/2026).
- Acervo legal COMPLETO baixado: todas as Leis Complementares do município + leis ordinárias citadas em rubricas (~299 normas, texto integral em ${LEIS_DIR}; índice de ementas em ${CATALOGO}).
- Brief jurídico (artigos já extraídos por tese): ${BRIEF}
- Fundamentação da auditoria anterior (só Saúde, reutilizável): ${RELATORIO_SAUDE}

DADOS CONSOLIDADOS (JSON, use estes números — são verificados e reconciliados):
${D}

REGRAS DE OURO:
- Todo achado tem R$ quantificado OU artigo citado; PROIBIDO "pode haver"/"merece análise" sem número.
- Leis fora da Saúde JÁ ESTÃO no acervo — cite-as (leia o texto em ${LEIS_DIR} se precisar confirmar um artigo).
- Anualização de recorrentes: fator 13,3× (12 + 13º + ⅓ férias).
- Honestidade de escopo: declarar limitações (só proventos; secretaria derivada; snapshot 29/03).
- R$ exposto ≠ economia garantida (glosa ≠ contingência ≠ risco/passivo ≠ saneamento).
`

// ---------- FASE 1: Panorama ----------
phase('Panorama')
const PANORAMA_SCHEMA = {
  type: 'object',
  required: ['governing_thought', 'sumario_executivo', 'kpis_destaque'],
  properties: {
    governing_thought: { type: 'string', description: '2–3 frases: a tese-mãe executiva (o "so what") da folha do município.' },
    sumario_executivo: { type: 'string', description: 'Prosa robusta e explicativa estilo McKinsey, 350–450 palavras, em PT-BR, conectando tamanho da folha, composição (vínculo/secretaria), concentração e as 2–3 maiores frentes de risco/oportunidade. Markdown (negrito permitido). NÃO bullets soltos.' },
    kpis_destaque: { type: 'array', items: { type: 'string' }, description: '4–6 destaques numéricos de uma linha.' },
  },
}
const panorama = await agent(
  `${CONTEXTO}\n\nVocê é consultor sênior (estilo McKinsey) de gestão pública. Escreva o PANORAMA executivo da folha do município. Foque no que importa para um gestor: magnitude, composição por vínculo (atenção ao peso de temporários) e por secretaria (Saúde vs. resto), concentração (Gini, faixas, elite>20k), e as maiores alavancas. Use os números do digest.`,
  { label: 'panorama', phase: 'Panorama', schema: PANORAMA_SCHEMA }
)

// ---------- FASE 2: Teses A1–A5 (gerar → verificar adversarial) ----------
const TESES = [
  { id: 'A1', titulo: 'Contratação temporária em atividade permanente', foco: 'CF art. 37, IX. No município há 4.014 servidores em Contrato Temporário (~39,75% da folha, ~R$ 19,6 mi/mês). Avalie se há cargos efetivos correspondentes no Estatuto/PCCV (acervo completo disponível) e se a contratação temporária virou permanente (risco/passivo, NÃO corte). Quantifique o R$ exposto.' },
  { id: 'A2', titulo: 'Teto remuneratório', foco: 'CF art. 37, XI. Use elite>20k bruto (ver kpis_mes: elite_n/elite_total no mês). SÓ proventos brutos (sem R216/descontos). Pendência: subsídio do Prefeito (externo) define o teto — declare. Quantifique quantos e quanto acima de R$ 20k; NÃO conclua ilegalidade sem o subsídio.' },
  { id: 'A3', titulo: 'Gratificações e adicionais — lastro e fragmentação', foco: 'LC 192/16 art. 149 e leis de gratificação (acervo). A Trilha C achou 44 rubricas distintas de gratificação geral (~R$ 7,66 mi/mês) + 6 de função gratificada. Avalie lastro legal de cada família e a FRAGMENTAÇÃO (mesma base, múltiplos códigos). Quantifique e recomende consolidação/saneamento.' },
  { id: 'A4', titulo: 'Adicional de insalubridade/periculosidade', foco: 'Súmula Vinculante 4/STF (base de cálculo) + exigência de laudo (LTCAT). Trilha C: 3 rubricas de insalubridade (~R$ 1,08 mi/mês). Verifique base de cálculo prevista nas leis do acervo e a pendência de laudos. Quantifique.' },
  { id: 'A5', titulo: 'Apostilamento/incorporação de funções', foco: 'Regras de incorporação no Estatuto (acervo). Procure rubricas de salário/função apostilada. Avalie se há incorporação sem base/vedada pós-EC. Quantifique o que houver; se irrelevante no município, diga e classifique 🟢.' },
]

const GEN_SCHEMA = {
  type: 'object',
  required: ['id', 'titulo', 'achado', 'fundamento', 'rs_mes', 'classificacao', 'recomendacao'],
  properties: {
    id: { type: 'string' }, titulo: { type: 'string' },
    achado: { type: 'string', description: 'Prosa: o achado, com números e contexto. PT-BR, Markdown.' },
    fundamento: { type: 'array', items: { type: 'string' }, description: 'Citações legais (lei, artigo, inciso) com trecho curto. Use o brief e, se preciso, leia o texto da lei.' },
    rs_mes: { type: 'number', description: 'R$/mês exposto ou em discussão (0 se não quantificável; explique no achado).' },
    rs_ano: { type: 'number', description: 'R$/ano (rs_mes × 13,3 se recorrente).' },
    classificacao: { type: 'string', enum: ['🔴', '🟡', '🟢'], description: '🔴 alto / 🟡 atenção / 🟢 conforme.' },
    recomendacao: { type: 'string' },
  },
}
const VERIFY_SCHEMA = {
  type: 'object',
  required: ['veredito', 'classificacao_final', 'critica_revisor'],
  properties: {
    veredito: { type: 'string', description: 'Ex.: "mantida", "rebaixada de 🔴 para 🟡", "refutada".' },
    classificacao_final: { type: 'string', enum: ['🔴', '🟡', '🟢'] },
    critica_revisor: { type: 'string', description: 'O que foi checado e por que o veredito; aponte exageros, falta de lei, ou R$ inflado.' },
    rs_ajustado_mes: { type: 'number', description: 'R$/mês após ajuste do revisor (repita o original se não mudou).' },
  },
}

const teses = await pipeline(
  TESES,
  (t) => agent(
    `${CONTEXTO}\n\nTESE ${t.id} — ${t.titulo}.\n${t.foco}\n\nVocê é procurador municipal + auditor. Gere a tese: achado quantificado, fundamento legal CITADO (consulte ${BRIEF}; se precisar confirmar um artigo, leia o arquivo da lei em ${LEIS_DIR}), classificação e recomendação. Seja específico e citável.`,
    { label: `tese:${t.id}`, phase: 'Teses', schema: GEN_SCHEMA }
  ).then(async (gen) => {
    if (!gen) return null
    const verdict = await agent(
      `${CONTEXTO}\n\nVocê é um REVISOR ADVERSARIAL (procurador cético). Tente REFUTAR a tese abaixo. Cheque: (a) o R$ está correto e bem definido (exposto ≠ economia)? (b) a base legal citada existe e sustenta a conclusão? (c) a classificação 🔴/🟡/🟢 é proporcional ou exagerada? Rebaixe se houver dúvida razoável. Seja rigoroso.\n\nTESE GERADA:\n${JSON.stringify(gen)}`,
      { label: `verif:${t.id}`, phase: 'Teses', schema: VERIFY_SCHEMA }
    )
    return { ...gen, veredito: verdict?.veredito, classificacao_final: verdict?.classificacao_final,
             critica_revisor: verdict?.critica_revisor, rs_ajustado_mes: verdict?.rs_ajustado_mes ?? gen.rs_mes }
  })
)
const teses_ok = teses.filter(Boolean)

// ---------- FASE 3: Eficiência + Quick wins ----------
phase('Eficiencia')
const EFIC_SCHEMA = {
  type: 'object',
  required: ['eficiencia_texto', 'quickwins_texto', 'achados'],
  properties: {
    eficiencia_texto: { type: 'string', description: 'Prosa sobre Trilha B (custo relativo/hora, outliers de cargo, concentração). DECLARE a limitação (custo ≠ produtividade). Markdown.' },
    quickwins_texto: { type: 'string', description: 'Prosa sobre Trilha C (jornada ausente/impossível, pago sem cadastro, fragmentação de rubricas, variações bruscas). Markdown.' },
    achados: { type: 'array', items: { type: 'string' }, description: '4–6 quick wins acionáveis com R$.' },
  },
}
const efic = await agent(
  `${CONTEXTO}\n\nInterprete para um gestor os resultados de eficiência (Trilha B) e qualidade de dado (Trilha C) que estão no digest (trilha_b, trilha_c). Seja honesto sobre limitações. Conecte os números a ações.`,
  { label: 'eficiencia', phase: 'Eficiencia', schema: EFIC_SCHEMA }
)

// ---------- FASE 4: Síntese McKinsey ----------
phase('Sintese')
const SINT_SCHEMA = {
  type: 'object',
  required: ['matriz', 'envelope_texto', 'sumario_final', 'riscos', 'pendencias'],
  properties: {
    matriz: { type: 'array', items: { type: 'object', properties: {
      item: { type: 'string' }, valor: { type: 'string', enum: ['Alto', 'Médio', 'Baixo'] },
      confianca: { type: 'string', enum: ['Alta', 'Média', 'Baixa'] },
      exequibilidade: { type: 'string', enum: ['Alta', 'Média', 'Baixa'] },
      rs_ano: { type: 'number' } } } },
    envelope_texto: { type: 'string', description: 'Prosa: o envelope de oportunidade, explicando por que NÃO somar cegamente as cifras. Markdown.' },
    sumario_final: { type: 'string', description: 'Fechamento executivo de 2–3 parágrafos.' },
    riscos: { type: 'array', items: { type: 'string' } },
    pendencias: { type: 'array', items: { type: 'string' }, description: 'Pendências externas (subsídio do Prefeito, laudos, etc.).' },
  },
}
const sintese = await agent(
  `${CONTEXTO}\n\nVocê é o sócio responsável. Sintetize TUDO numa matriz de priorização (valor × confiança × exequibilidade) e num envelope de oportunidade.\n\nTESES VERIFICADAS:\n${JSON.stringify(teses_ok.map(t => ({ id: t.id, titulo: t.titulo, classificacao_final: t.classificacao_final, rs_ajustado_mes: t.rs_ajustado_mes, veredito: t.veredito })))}\n\nEFICIÊNCIA/QUICKWINS:\n${JSON.stringify(efic)}\n\nMonte a matriz com as principais iniciativas (teses + quick wins), o envelope (disciplina de não somar tipos diferentes), riscos e pendências externas.`,
  { label: 'sintese', phase: 'Sintese', schema: SINT_SCHEMA }
)

return {
  governing_thought: panorama?.governing_thought,
  sumario_executivo: panorama?.sumario_executivo,
  kpis_destaque: panorama?.kpis_destaque,
  teses: teses_ok,
  eficiencia_texto: efic?.eficiencia_texto,
  quickwins_texto: efic?.quickwins_texto,
  quickwins_achados: efic?.achados,
  matriz: sintese?.matriz,
  envelope_texto: sintese?.envelope_texto,
  sumario_final: sintese?.sumario_final,
  riscos: sintese?.riscos,
  pendencias: sintese?.pendencias,
}
