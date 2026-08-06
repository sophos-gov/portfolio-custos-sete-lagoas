# -*- coding: utf-8 -*-
"""Atualiza TODOS os campos da tese A5 em auditoria_municipio.json (fonte de verdade) com as
correcoes da investigacao aprofundada (art. 228, teto RGPS 2026, RE 638.115=Tema 395, re-hierarquia,
escopo prospectivo). Idempotente. Apos rodar, regenerar com build_html_municipio.py."""
import json
from pathlib import Path

JSON = Path(__file__).resolve().parent.parent / "output" / "municipio" / "auditoria_municipio.json"

TITULO = ("Salário apostilado: teto do art. 89-A §2 estourado (ÂNCORA — glosa prospectiva "
          "~R$ 676 mil/ano) e beneficiários fora da janela do art. 89-B (verificar); base revogada "
          "pela LC 192/2016, com direitos preservados pelo art. 228. Ver PARECER_APOSTILADO")

ACHADO = (
"**ATUALIZAÇÃO (16/06/2026) — investigação aprofundada (ver PARECER_APOSTILADO.md/.html).** "
"Três correções ao A5 original: (1) a **LC 84/2003 está revogada** (LeisMunicipais/SAPL, pela LC 192/2016), "
"MAS o **art. 228 da mesma lei preserva os direitos adquiridos** (\"as disposições da LC 84/2003\") — regime "
"fechado, não vácuo; (2) o precedente do STF é o **RE 638.115 = Tema 395** "
"(não \"Tema 763\", que é o RE 786.540, assunto diverso); (3) o teto do RGPS de mai/2026 é **R$ 8.475,55** "
"(não R$ 8.157,41), recalculando o excesso para **R$ 50.841,71/mês = R$ 676.194,74/ano**. Hierarquia: "
"Tese A (teto §2) é a ÂNCORA 🔴 (glosa prospectiva limpa); Teses B e C são 🟡.\n\n"

"O Município paga, em mai/2026, a rubrica 36 \"SALÁRIO APOSTILADO\" a **109 servidores**, no total de "
"**R$ 506.153,21/mês** — equivalente a **R$ 6.731.837,69/ano** (x13,3). É a 21ª maior rubrica da folha; "
"beneficiários quase todos Estatutários Ativos / Estatutário+Comissionado (procuradores, auditores fiscais, "
"agentes administrativos), com admissões entre 1978 e 2009.\n\n"

"O apostilamento é o instituto pelo qual o servidor efetivo/estável que exerceu cargo em comissão incorpora "
"em definitivo o vencimento do cargo comissionado mesmo após a exoneração. A base legal local é a **LC 84/2003**, "
"que inseriu a \"Seção VII – Do Apostilamento\" (arts. 89-A e 89-B) na **LC 79/2003**.\n\n"

"**1) Base legal — REVOGADA + direitos preservados (🟡 regime fechado).** A **LC 84/2003 está revogada** "
"(confirmado no LeisMunicipais/SAPL), por força da LC 192/2016, **art. 232** (que revogou a LC 79/2003, sua lei "
"hospedeira); mas o **art. 228 da MESMA LC 192/2016** assegura expressamente \"as disposições da LC 84/2003\" — "
"*grandfathering* do direito adquirido (CF art. 5º XXXVI; art. 37 XV). Regime **fechado a novas concessões**, com "
"os direitos constituídos preservados. Atacar os R$ 6,73 mi/ano como \"base inconstitucional a anular\" é frágil "
"(colide com o art. 228 e com a modulação do RE 638.115/Tema 395). Esta camada é **exposição**, não economia. "
"Footprint: nenhuma norma viva da Prefeitura institui o apostilamento (as 4 instituidoras — LC 1/90, 21/97, 50/00, "
"84/03 — revogadas; 7 LCs vivas só o EXCLUEM de bases de cálculo), mas o instituto segue vivo na CÂMARA "
"(LO 9599/2023, arts. 68-69, em vigor) e a Prefeitura reconhece \"servidores apostilados\" em 2023 (LO 9527/2023).\n\n"

"**2) Teto do art. 89-A §2 ESTOURADO (R$ 676 mil/ano — ÂNCORA, glosa prospectiva limpa).** A própria LC 84/2003 "
"(art. 89-A §2) limita o apostilado ao maior provento do RGPS (**teto INSS 2026 = R$ 8.475,55**). **6 servidores** "
"acima do teto: LUIZ MARCIO C. MACHADO (R$ 20.410,05), AYRE A. PENNA (R$ 19.574,27), FLAVIO M. DUMONT "
"(R$ 19.574,26), AFONSO H. G. FRANÇA (R$ 16.231,09), LEONARDO L. BRAGA (R$ 15.403,32), OBERDAM J. G. CASTRO "
"(R$ 10.502,02). Excesso = **R$ 50.841,71/mês → R$ 676.194,74/ano** (com o teto 2025 de R$ 8.157,41 seria "
"R$ 701.582,32/ano). *Não se adquire direito maior do que a lei concede*: conformar ao teto é cumprir a lei "
"(Súmula 473 STF; trato sucessivo) — baixo risco.\n\n"

"**3) Beneficiários fora da janela do art. 89-B (R$ 1,15 mi/ano — VERIFICAR).** O art. 89-B restringe o direito "
"EXCLUSIVAMENTE a quem exerceu comissão **antes de 1º/01/2004**. **15 servidores** têm admissão ≥ 01/01/2004 "
"(FLAVIO 2006, AFONSO 2006, ANDRE W. LONGO 2007, SUSANA O. FRANÇA 2008, VIVIANE GUIMARAES 2009, entre outros) — "
"somam **R$ 86.817,70/mês → R$ 1.154.675,41/ano**. Ressalva decisiva: o art. 89-B exige **EXERCÍCIO** (não admissão) "
"antes de 2004, e o §5 computa períodos pré-lei; \"admissao\" é a do vínculo atual — exige ficha funcional. "
"Casos mais sensíveis: os admitidos em 2006-2009. FLAVIO e AFONSO estão também na camada do teto; exposição "
"combinada de-duplicada A+B = **R$ 120.077,72/mês = R$ 1.597.033,68/ano**.\n\n"

"Pano de fundo: o STF, no **RE 638.115 (Tema 395**, repercussão geral), assentou a inconstitucionalidade da "
"incorporação permanente de remuneração de cargo em comissão (\"quintos/décimos\") por afronta à legalidade. "
"A **modulação** protege quem já recebia até absorção por reajustes — cautela contra cessação **frontal**, mas "
"não autoriza pagar **acima do teto legal** (por isso a Tese 2 é a âncora). O **TJ-MG** tem jurisprudência "
"**contestada** sobre o apostilamento municipal (conferir inteiro teor); o **TCE-MG** o trata como instituto "
"restritivo de classe fechada.\n\n"

"LIMITAÇÕES: folha só com proventos brutos (sem descontos); secretaria derivada de descr_lotacao; cadastro é "
"snapshot de 29/03/2026; valor exposto ≠ economia garantida. **Escopo: cessação prospectiva** (passivo retroativo "
"fora — STJ Tema 531)."
)

FUNDAMENTO = [
 "LC 84/2003 (Sete Lagoas), art. 89-A, caput: 'O servidor efetivo e/ou estável, que tenha exercido ou venha a "
 "exercer cargo de provimento em comissão (...) terá o direito a receber, caso assim opte, o vencimento "
 "correspondente ao cargo comissionado, mesmo após a sua exoneração' — instituiu o apostilamento, inserindo a "
 "Seção VII na LC 79/2003 (lc_84_03.txt).",
 "LC 84/2003, art. 89-A, §2º: 'O vencimento do servidor público municipal apostilado não poderá ser superior ao "
 "maior provento de aposentadoria definido no Regime Geral de Previdência Social' — teto legal próprio do benefício "
 "(teto RGPS 2026 = R$ 8.475,55; excesso de R$ 676.194,74/ano em 6 servidores).",
 "LC 84/2003, art. 89-B: 'O disposto nesta lei se aplica exclusivamente aos servidores públicos municipais que "
 "exercerem cargo de provimento em comissão no período anterior a 1º de janeiro de 2.004' — janela fechada (15 "
 "admitidos >= 01/01/2004 a verificar por ficha funcional, R$ 1.154.675,41/ano).",
 "LC 192/2016 (Estatuto vigente), art. 232: 'Ficam revogadas as disposições da Lei Complementar nº 79 de 09 de "
 "julho de 2003' — revoga a lei hospedeira da Seção VII do Apostilamento.",
 "LC 192/2016, art. 228 (lc_192_16.txt linha 1833): 'Ficam assegurados os benefícios e vantagens aos servidores "
 "estáveis e efetivos (...) bem como as disposições da Lei Complementar nº 84 de 08 de setembro de 2003' — PRESERVA "
 "expressamente o apostilado como direito adquirido (regime fechado a novas concessões, NÃO vácuo legal).",
 "CF/88, art. 37 caput/XIII e art. 39 §1º (vedam a incorporação permanente de remuneração de cargo em comissão); "
 "art. 5º XXXVI e art. 37 XV (direito adquirido/irredutibilidade protegem o núcleo do benefício, não o excesso ilegal).",
 "STF, RE 638.115 (Tema 395, repercussão geral — correção do antes citado 'Tema 763', que é o RE 786.540, assunto "
 "diverso): inconstitucionalidade da incorporação de 'quintos/décimos' por afronta à legalidade, com modulação que "
 "protege quem já recebia até absorção por reajustes — fundamento análogo ao apostilamento municipal.",
 "Súmula 473 STF (autotutela: a Administração anula seus próprios atos ilegais); Lei 9.784/99 art. 54 "
 "(decadência quinquenal; situações flagrantemente ilegais não se consolidam; trato sucessivo); STJ Tema 531 "
 "(irrepetibilidade de verba alimentar recebida de boa-fé — fundamenta o escopo de cessação prospectiva)."
]

RECOMENDACAO = (
"Cessação prospectiva, por camada de segurança (detalhe em PARECER_APOSTILADO.md/.html): "
"(1) GLOSA PROSPECTIVA do excesso ao teto do art. 89-A §2 nos 6 servidores acima do teto RGPS 2026 (R$ 8.475,55): "
"economia de R$ 50.841,71/mês = R$ 676.194,74/ano, ancorada na própria lei do benefício (preservada pelo art. 228) "
"+ Súmula 473 STF + trato sucessivo — baixo risco; com contraditório/devido processo. "
"(2) AUDITORIA FUNCIONAL dos 15 admitidos >= 01/01/2004: requisitar a ficha funcional comprovando exercício de "
"comissão por 5 anos ANTES de 2004 (art. 89-B + §5); priorizar os 5 admitidos em 2006-2009; sem prova, suspender "
"(R$ 86.817,70/mês = R$ 1,15 mi/ano em discussão). "
"(3) PARECER PGM sobre os 109: documentar a tese art. 228 x 232 (regime fechado, direito adquirido preservado) e "
"mapear os atos de concessão, à luz do RE 638.115/Tema 395 e sua modulação; vedar novas concessões. "
"(4) Atualizar o teto do §2 anualmente conforme o RGPS e registrar o saneamento ao TCE-MG. "
"Passivo retroativo fora do escopo (irrepetibilidade de verba alimentar de boa-fé, STJ Tema 531)."
)

MATRIZ_ITEM = ("A5 — Salário apostilado: teto §2 estourado (âncora, glosa prospectiva ~R$ 676 mil/ano) + janela "
               "89-B (verificar); base preservada pelo art. 228 da LC 192/2016")
MATRIZ_VEREDITO = ("🔴 âncora = glosa prospectiva do excesso ao teto §2 (R$ 676.194,74/ano, teto RGPS 2026), de baixo "
                   "risco. Camadas janela (89-B) e base são exposição a verificar (R$ 120.077,72/mês de-duplicado). "
                   "Base legal preservada pelo art. 228 da LC 192/2016 (não revogada). Precedente: RE 638.115/Tema 395.")

ADDENDUM = ("\\n\\nADENDO (16/06/2026 — investigação aprofundada): a verificação ORIGINAL acima permanece como "
            "trilha de auditoria, mas FICA SUPERADA em três pontos pelo PARECER_APOSTILADO: (i) a base NÃO está "
            "revogada — art. 228 da LC 192/2016 preserva a LC 84/2003 (regime fechado, não vácuo); (ii) o precedente "
            "é RE 638.115/Tema 395 (não Tema 763); (iii) o teto RGPS de mai/2026 é R$ 8.475,55, logo o excesso "
            "acionável é R$ 50.841,71/mês = R$ 676.194,74/ano. rs de-duplicado mantido em R$ 120.077,72/mês.")

d = json.loads(JSON.read_text(encoding="utf-8"))
a5 = next(t for t in d["teses"] if t.get("id") == "A5")
a5["titulo"] = TITULO
a5["achado"] = ACHADO
a5["fundamento"] = FUNDAMENTO
a5["recomendacao"] = RECOMENDACAO
a5["rs_mes"] = 120077.72
a5["rs_ano"] = 1597033.68
a5["rs_ajustado_mes"] = 120077.72
if a5.get("critica_revisor") and "ADENDO (16/06/2026" not in a5["critica_revisor"]:
    a5["critica_revisor"] = a5["critica_revisor"] + ADDENDUM

for m in d.get("matriz", []):
    if str(m.get("item", "")).startswith("A5"):
        m["item"] = MATRIZ_ITEM
        if "veredito_resumo" in m:
            m["veredito_resumo"] = MATRIZ_VEREDITO

JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(">> A5 atualizada (titulo/achado/fundamento/recomendacao/rs/matriz). len(achado)=", len(ACHADO))
