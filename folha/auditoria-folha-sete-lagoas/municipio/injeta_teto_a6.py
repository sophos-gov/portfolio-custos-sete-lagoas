# -*- coding: utf-8 -*-
"""
injeta_teto_a6.py — Atualiza auditoria_municipio.json com a análise aprofundada de
teto remuneratório (art. 37 §11) e brechas. IDEMPOTENTE.

Faz duas coisas, lendo os R$ de output/municipio/teto_aprofundamento.json (fonte única):
  1. CORRIGE a tese A2 in-place: rebaixa o headline (rs_mes/rs_ano/rs_ajustado_mes)
     para o cenário §11; prepende parágrafo "Atualização §11" ao achado; corrige a
     recomendação que apontava o caso AUX.ADMINISTRATIVO (rescisão) como prioridade;
     atualiza a linha A2 da matriz.
  2. ADICIONA/SOBRESCREVE a tese A6 "Teto, abate-teto e brechas remuneratórias", com
     fundamentos legais conferidos VERBATIM (nº de linha em legislacao_full/).

Uso:  python municipio/injeta_teto_a6.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
AUD = BASE / "output/municipio/auditoria_municipio.json"
TAP = BASE / "output/municipio/teto_aprofundamento.json"

MARCA_A2 = "**Atualização (art. 37, §11"


def brl(v):
    s = f"{float(v):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def milhoes(v):
    return f"R$ {float(v)/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    aud = json.loads(AUD.read_text(encoding="utf-8"))
    tap = json.loads(TAP.read_text(encoding="utf-8"))
    c = tap["cenarios"]; ag = tap["agregados"]
    b = {x["rotulo"]: x for x in tap["brechas"]}
    sl = tap.get("subsidio_legal", {})
    proxy = tap["teto_proxy"]["valor"]
    e_mes = c["base_511"]["exc_mes"]; e_ano = c["base_511"]["exc_ano"]
    br_ano = c["bruto"]["exc_ano"]
    n511 = c["base_511"]["n"]; nbru = c["bruto"]["n"]
    red = c["reducao_pct"]
    nmed = ag["nao_medico"]; med = ag["medico"]
    estrut = ag["estrutural_3de3"]; inat = ag["inativo_pensionista"]

    teses = aud["teses"]
    a2 = next(t for t in teses if t["id"] == "A2")

    # ---------- 1. CORRIGE A2 ----------
    if MARCA_A2 not in a2["achado"]:
        update = (
            f"{MARCA_A2} — cálculo líquido das indenizatórias).** A base LONG do município "
            f"permite separar as verbas indenizatórias (tipo_rubrica EVENTUAL_INDENIZATORIA) "
            f"e aplicar o art. 37, §11 — o que o A2 original não fez. Excluídas as "
            f"indenizatórias, os violadores caem de **{nbru} para {n511}** e o excedente recua "
            f"de {brl(br_ano)}/ano (cenário-bruto, exposição máxima) para **{brl(e_mes)}/mês "
            f"= {milhoes(e_ano)}/ano (−{red:.0f}%)**. **18 dos {nbru}** 'violadores' saíram por "
            f"serem férias/13º/rescisão — inclusive o caso **AUX.ADMINISTRATIVO I de R$ 125.985 "
            f"(rescisão; base de teto ≈ R$ 860), que NÃO é violação de teto**. O detalhamento "
            f"(três lentes, abate-teto e brechas) está na tese **A6** e nos Exhibits 6.1–6.3. "
            f"Headline rebaixado para o cenário §11.\n\n")
        a2["achado"] = update + a2["achado"]

    a2["rs_mes"] = round(e_mes, 2)
    a2["rs_ano"] = round(e_ano, 2)
    a2["rs_ajustado_mes"] = round(e_mes, 2)

    # corrige frase contraditória no corpo original (bruto era 'o número relevante')
    a2["achado"] = a2["achado"].replace(
        "Este é o número juridicamente relevante (sujeito a ajuste quando o subsídio "
        "nominal for obtido e expurgadas as verbas indenizatórias do art. 37, §11).",
        "Este era o número apontado como relevante no A2 original; a atualização §11 no "
        f"topo desta tese já expurgou as indenizatórias e o rebaixou para {brl(e_mes)}/mês "
        "(ver tese A6).")

    # rebaixa o 'headline' citado na verificação adversarial original
    if "NOTA (§11)" not in a2.get("critica_revisor", ""):
        a2["critica_revisor"] = (
            f"NOTA (§11): o headline desta tese foi rebaixado para o cenário líquido das "
            f"indenizatórias ({n511} servidores, {brl(e_mes)}/mês = {milhoes(e_ano)}/ano); a "
            f"checagem abaixo refere-se ao cenário-bruto original ({nbru} servidores). "
            + a2.get("critica_revisor", ""))

    nota_rec = (" — ATUALIZAÇÃO (§11): o caso AUX.ADMINISTRATIVO I (R$ 125.985) é rescisão "
                "(verbas indenizatórias; base de teto ≈ R$ 860), reclassificado para fora do "
                "teto — ver A6. Prioridade real: os 7 Procuradores estruturais e o auditor "
                "fiscal; segmentar inativos/pensão.")
    if "ATUALIZAÇÃO (§11)" not in a2.get("recomendacao", ""):
        a2["recomendacao"] = a2.get("recomendacao", "") + nota_rec

    # matriz: linha A2
    for m in aud.get("matriz", []):
        if str(m.get("item", "")).strip().startswith("A2"):
            m["rs_ano"] = round(e_ano, 2)

    # ---------- 2. ADICIONA/SOBRESCREVE A6 ----------
    achado_a6 = (
        f"**Escopo.** Aprofundamento do teto remuneratório do município (CF art. 37, XI), "
        f"competência mai/2026, com o teto-proxy = subsídio do Prefeito **{brl(proxy)}** "
        f"(valor nominal ainda pendente). Mede-se a remuneração em **três lentes** contra esse "
        f"teto e investiga-se por que o abate-teto não opera. Listas completas nos Exhibits "
        f"6.1 (servidores acima do teto), 6.2 (efeito do §11) e 6.3 (aparato de produtividade).\n\n"

        f"**1) As três lentes (quem está acima do Prefeito).** (a) **Bruto:** {nbru} servidores; "
        f"(b) **Base §11** (proventos − indenizatórias, o conceito correto de teto): **{n511} "
        f"servidores**, excedente {brl(e_mes)}/mês = {milhoes(e_ano)}/ano; (c) **Líquido real** "
        f"(pós-INSS/IRRF/consignações): só apurável para 14 dos {nbru} (base Saúde/fev) — e, "
        f"pós-descontos, quase todos os médicos caem abaixo do bruto do Prefeito. Núcleo dos "
        f"{n511}: **{nmed['n']} não-médicos** ({milhoes(nmed['exc_ano'])}/ano), dos quais 7 "
        f"Procuradores, e **{med['n']} médicos** ({milhoes(med['exc_ano'])}/ano, estouros "
        f"pequenos + escudo de acumulação lícita e plantão limitado ao subsídio). **{estrut['n']} "
        f"dos {n511} são estruturais** (violam 3/3 meses); {inat['n']} são inativos/pensionistas "
        f"(teto alcança aposentados — EC 41/2003 — mas pensão tem regra própria; segmentar).\n\n"

        f"**2) O abate-teto existe na lei e na folha, mas está praticamente desligado.** O teto "
        f"municipal é fixado pela LC 192/2016, art. 130, que manda incluir no cômputo **'todas "
        f"as parcelas integrantes de seus vencimentos ou salários, incorporados ou não'** — "
        f"redação mais ampla que a própria CF. A folha já possui a rubrica de abate "
        f"**R216 DESC.LIMITE CONSTITUCIONAL**, mas ela foi aplicada a **apenas 4 servidores** "
        f"(base Saúde/fev; R$ 5,7 mil), enquanto {n511} excedem o teto. Não há, no acervo "
        f"(~302 normas), decreto regulamentando o cálculo do abate. O mecanismo existe e não é "
        f"acionado.\n\n"

        f"**3) Brecha do auditor fiscal — produtividade tratada como 'fora do teto'.** Há um "
        f"aparato de produtividade fiscal vultoso: **REVADEF** ({b['REVADEF']['n_serv_long']} "
        f"servidores, {brl(b['REVADEF']['valor_mes_long'])}/mês), **GEPFF** "
        f"({b['GEPFF']['n_serv_long']} servidores, {brl(b['GEPFF']['valor_mes_long'])}/mês) e "
        f"**PREVISA/PROVISA** (Lei 9.526/2023; juntos ~{brl(b['PREVISA']['valor_mes_long']+b['PROVISA']['valor_mes_long'])}/mês). "
        f"A Lei 9.526/2023, art. 9º, diz que esses prêmios **'não se incorporam aos vencimentos "
        f"para qualquer efeito'** — cláusula que governa a **permanência/aposentadoria**, e que "
        f"pode estar sendo lida indevidamente como 'não computa no teto'. Mas o art. 37, §11 da "
        f"CF só exclui do teto as parcelas **indenizatórias**, e o art. 130 da LC 192/2016 inclui "
        f"as parcelas **'incorporados ou não'**: logo, **a produtividade fiscal compõe o teto**. "
        f"A REVADEF, registre-se, **continua vigente** (Lei 6.990/2004, alterada pela LC 205/2017, "
        f"art. 38); só deixou de ser paga à Vigilância Sanitária (Lei 9.526/2023, art. 10) — o "
        f"pagamento tem lastro; a brecha é de **teto**, não de base legal. O auditor fiscal que "
        f"de fato excede o teto (OBERDAM, base §11 R$ 36.016) estoura por **salário apostilado + "
        f"triênios + GEPFF**, caso de incorporação que conversa com a tese A5.\n\n"

        f"**4) Incorporações que pressionam o teto.** Três vetores legais de empilhamento: "
        f"(i) **triênios** — LC 192/2016, art. 145: 10% do vencimento a cada 3 anos, que **'se "
        f"incorpora, para fins de aposentadoria, limitando-se a 10 triênios'** (até +100%); "
        f"(ii) **apostilamento** (LC 84/2003 — tese A5); (iii) **retribuição dos Procuradores** "
        f"(LC 205/2017, art. 27): vencimento + vantagens pessoais + adicional por tempo de "
        f"serviço + apostilamento + gratificações somados — a engenharia que leva os 7 "
        f"procuradores à faixa de R$ 40–52 mil de base de teto.\n\n"

        f"**5) O parâmetro legal do teto — e uma lacuna.** O subsídio do Prefeito foi fixado pela "
        f"**Lei nº 8.180/2012** (legislatura 2013-2016): Prefeito {brl(sl['prefeito_2013'])}, "
        f"Vice {brl(sl['vice_2013'])}, Secretários {brl(sl['secretario_2013'])} — em parcela única, "
        f"vedados acréscimos —, com revisão anual pelo IPCA assegurada pela **Lei nº 8.325/2014**. "
        f"**Não consta no SAPL lei de fixação para as legislaturas 2017-2020, 2021-2024 nem 2025-2028** "
        f"(CF art. 29, V exige fixação por legislatura): o subsídio atual repousa sobre a base de 2012 "
        f"acrescida de revisões. O valor pago em mai/2026 ({brl(proxy)}, adotado como proxy do teto) "
        f"situa-se abaixo do que resultaria da aplicação integral do IPCA desde 2013 — indício de que "
        f"as revisões não foram todas aplicadas, e de que o proxy é conservador.\n\n"

        f"**Honestidade de escopo.** O *valor nominal definitivo* do teto depende da edição de lei de "
        f"fixação para a legislatura vigente (hoje inexistente); o proxy pode conter indenizatórias e "
        f"o teto real pode ser menor; o líquido real é de competência distinta (fev/Saúde) e cobre só "
        f"parte; não se conclui ilegalidade — quantifica-se **exposição** ({milhoes(e_ano)}/ano no "
        f"cenário §11) e fixa-se prioridade de apuração.")

    rec_a6 = (
        "Em camadas, da mais segura à mais estrutural: "
        "1) **Ligar o abate-teto**: aplicar a R216 mensalmente computando TODAS as parcelas "
        "remuneratórias (LC 192/2016, art. 130), inclusive produtividade fiscal "
        "(REVADEF/GEPFF/PREVISA/PROVISA) e gratificações 'não incorporáveis', excluídas apenas "
        "as indenizatórias (art. 37, §11). "
        "2) **Obter o subsídio nominal do Prefeito** (lei de fixação da legislatura) para fechar "
        "o teto exato. "
        "3) **Parecer da PGM** sobre se a cláusula 'não se incorporam' (Lei 9.526/2023, art. 9º) "
        "vem sendo indevidamente lida como exclusão do teto. "
        "4) **Priorizar os 7 Procuradores estruturais** e o auditor fiscal (núcleo não-médico de "
        + milhoes(nmed['exc_ano']) + "/ano), segmentando ativos × inativos × pensão. O abate do "
        "excedente encontra respaldo direto no **Tema 257/STF (RE 606.358)** — vantagens pessoais "
        "(apostilamento, triênios, ATS, gratificações) submetem-se ao teto, sem direito adquirido —, "
        "com **eficácia prospectiva** (dispensada a restituição de boa-fé até 18/11/2015); a defesa "
        "de honorários (ADI 6.053) não socorre, pois inexistem na folha. "
        "5) **Comunicar a exposição como " + milhoes(e_ano) + "/ano (cenário §11), não os "
        + milhoes(br_ano) + " do bruto** — e jamais como economia garantida.")

    critica_a6 = (
        "Verificação adversarial. NÚMEROS: todos reproduzidos de teto_aprofundamento.json "
        "(servidor_mes + folha_municipio_long, mai/2026); teto-proxy R$ 33.259,37; bruto "
        f"{nbru} (R$ 434.631/mês), base §11 {n511} (R$ {e_mes:,.2f}/mês = R$ {e_ano:,.2f}/ano), "
        f"−{red:.0f}%; recorrência {estrut['n']}/3-3; brechas REVADEF/GEPFF/PREVISA/PROVISA "
        "conferidas no LONG. BASE LEGAL conferida VERBATIM em legislacao_full/: LC 192/2016 "
        "art. 130 (linha 1151) e art. 145 (linha 1218); LC 83/2003 art. 37 (linhas 252-254, com "
        "parágrafo único do consultor ≤ secretário); Lei 9.526/2023 art. 9º (linha 151) e art. 10 "
        "(linha 153); LC 205/2017 art. 27 (linhas 167-170) e art. 38 (altera a Lei 6.990/2004 da "
        "REVADEF, linhas 335-339). RESSALVAS: subsídio nominal pendente (proxy pode conter "
        "indenizatórias → teto real possivelmente menor); líquido real é fev/Saúde (competência "
        "distinta, 14/38); REVADEF tem lastro legal — a tese ataca o TETO, não a legalidade do "
        "prêmio. PROPORCIONALIDADE: 🟡 — exposição material e bem fundamentada, mas dependente do "
        "subsídio nominal e de apuração caso a caso; não se afirma ilegalidade."
    )

    fund_a6 = [
        "CF/88, art. 37, XI: a remuneração não poderá exceder, nos Municípios, o subsídio do Prefeito.",
        "CF/88, art. 37, §11: não serão computadas, para o teto, as parcelas de caráter indenizatório previstas em lei (base do cálculo §11 desta tese).",
        "CF/88, art. 29, V: o subsídio do Prefeito, Vice e Secretários é fixado por lei de iniciativa da Câmara, em cada legislatura — fundamento da lacuna apontada (sem fixação para 2017-2020, 2021-2024 e 2025-2028).",
        "Lei municipal nº 8.180/2012: fixa o subsídio do Prefeito em R$ 21.000,00 (Vice R$ 14.700; Secretários R$ 9.900), para a legislatura 2013-2016, em parcela única, vedados acréscimos (§2º), com 13º (art. 3º). Lei nº 8.325/2014: assegura revisão anual pelo IPCA, em janeiro. Fonte: SAPL Sete Lagoas (normas 5898 e 240).",
        "LC 192/2016 (Estatuto), art. 130 (linha 1151): 'O teto remuneratório do servidor público municipal, ativo e aposentado, incluídas todas as parcelas integrantes de seus vencimentos ou salários, incorporados ou não, tem como limite máximo, o subsídio atribuído ao Prefeito Municipal.' — manda incluir produtividade e gratificações no teto.",
        "LC 192/2016, art. 145 (linha 1218): triênio de 10% sobre o vencimento, 'o qual a este se incorpora, para fins de aposentadoria, limitando-se a 10 (dez) triênios' (até +100%).",
        "LC 83/2003 (Pró-Saúde), art. 37 (linhas 252-254): 'Nenhum Servidor Público Municipal [...] poderá ter remuneração superior ao subsídio do Chefe do Poder Executivo Municipal'; Parágrafo único: 'O consultor não poderá ter remuneração superior à remuneração do secretário municipal.'",
        "Lei 9.526/2023, art. 9º (linha 151): 'Os prêmios instituídos nesta Lei não se incorporam aos vencimentos para qualquer efeito [...]' — cláusula de incorporação, não de exclusão do teto.",
        "Lei 9.526/2023, art. 10 (linha 153): cessa a REVADEF apenas para a Superintendência de Vigilância Sanitária — REVADEF segue vigente para os demais fiscais.",
        "LC 205/2017, art. 38 (linhas 335-339): altera os arts. 6º e 7º da Lei 6.990/2004 (REVADEF), confirmando sua vigência; art. 27 (linhas 167-170): estrutura de retribuição dos Procuradores (vencimento + vantagens pessoais + ATS + apostilamento + gratificações).",
        "LC 84/2003 (apostilamento) — base do empilhamento de vencimento de comissão; cross-referência com a tese A5.",
        "STF, RE 606.358 (Tema 257, repercussão geral): 'Computa-se, para efeito de observância do teto remuneratório do art. 37, XI, da Constituição, também o valor percebido a título de vantagens pessoais pelo servidor público, dispensada a restituição dos valores recebidos em excesso e de boa-fé até o dia 18 de novembro de 2015.' — precedente diretamente aplicável aos Procuradores (apostilado/triênios/ATS/gratificações), afastando alegação de direito adquirido; glosa de eficácia prospectiva.",
        "STF, RE 638.115 (Tema 395, repercussão geral): inconstitucionalidade da incorporação de quintos/décimos decorrentes de função comissionada — análogo do salário apostilado, parcela de maior peso na remuneração dos Procuradores.",
        "STF, RE 612.975 e RE 602.043 (Tema 384): o teto incide isoladamente sobre cada vínculo apenas nas hipóteses de acumulação lícita (CF, art. 37, XVI) — protege os médicos acumulantes, não os Procuradores (vínculo único).",
        "STF, ADI 6.053: honorários sucumbenciais da advocacia pública submetem-se ao teto — inaplicável in casu, pois inexiste rubrica de honorários/sucumbência na folha do Município (0 servidores).",
    ]

    a6 = dict(
        id="A6",
        titulo="Teto, abate-teto e brechas remuneratórias: exposição §11 de "
               + milhoes(e_ano) + "/ano e abate-teto desligado",
        achado=achado_a6,
        fundamento=fund_a6,
        rs_mes=round(e_mes, 2),
        rs_ano=round(e_ano, 2),
        classificacao="🟡",
        recomendacao=rec_a6,
        veredito="mantida",
        classificacao_final="🟡",
        critica_revisor=critica_a6,
        rs_ajustado_mes=round(e_mes, 2),
    )

    teses = [t for t in teses if t.get("id") != "A6"]  # idempotência
    teses.append(a6)
    aud["teses"] = teses

    AUD.write_text(json.dumps(aud, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: A2 corrigido (rs_ano={e_ano:,.2f}) + A6 injetado. Teses: "
          f"{[t['id'] for t in teses]}")


if __name__ == "__main__":
    main()
