# -*- coding: utf-8 -*-
"""
build_parecer_teto.py — Parecer jurídico (formato técnico-jurídico formal) sobre o teto
remuneratório de Sete Lagoas/MG. Registro elevado; prosa autoral; números de
output/municipio/teto_aprofundamento.json (fonte única).

Uso:  python municipio/build_parecer_teto.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output" / "municipio"


def brl(v):
    return ("R$ " + f"{float(v):,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")


def mi(v):
    return ("R$ " + f"{float(v)/1e6:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".") + " mi"


def main():
    t = json.loads((OUT / "teto_aprofundamento.json").read_text(encoding="utf-8"))
    cen = t["cenarios"]; ag = t["agregados"]; sl = t["subsidio_legal"]; r216 = t["abate_teto_r216"]
    proxy = t["teto_proxy"]["valor"]
    n511 = cen["base_511"]["n"]; nbru = cen["bruto"]["n"]
    exc_ano = cen["base_511"]["exc_ano"]; exc_mes = cen["base_511"]["exc_mes"]
    nmed = ag["nao_medico"]; med = ag["medico"]; estrut = ag["estrutural_3de3"]

    css = """
    @page{size:A4;margin:18mm 20mm;}
    *{box-sizing:border-box;}
    body{font-family:'Times New Roman',Georgia,serif;color:#111;font-size:10.6pt;line-height:1.46;margin:0;background:#fff;}
    .doc{max-width:178mm;margin:0 auto;}
    .head{text-align:center;border-bottom:2px solid #111;padding-bottom:9px;margin-bottom:14px;}
    .head .org{font-size:8.5pt;letter-spacing:.16em;text-transform:uppercase;color:#444;}
    .head h1{font-size:14pt;margin:7px 0 2px;letter-spacing:.02em;}
    .head .meta{font-size:8.8pt;color:#555;margin-top:3px;}
    .ementa{font-size:9.6pt;line-height:1.4;text-align:justify;margin:0 0 14px;padding:9px 13px;
            border:1px solid #bbb;background:#f7f7f7;}
    .ementa b{letter-spacing:.01em;}
    h2{font-size:10.6pt;margin:13px 0 4px;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #999;padding-bottom:2px;}
    h3{font-size:10.2pt;margin:9px 0 2px;font-style:italic;font-weight:bold;}
    p{margin:5px 0;text-align:justify;text-indent:1.2em;}
    p.noind{text-indent:0;}
    blockquote{margin:5px 0 5px 22px;padding-left:11px;border-left:2px solid #999;font-size:9.6pt;
               color:#222;text-align:justify;font-style:italic;}
    ol{margin:5px 0;padding-left:22px;}li{margin:3px 0;text-align:justify;}
    .num{font-variant-numeric:tabular-nums;}
    .risco{font-weight:bold;}
    .sig{margin-top:20px;text-align:center;font-size:9.6pt;}
    .ref{font-size:8pt;color:#555;border-top:1px solid #bbb;margin-top:14px;padding-top:6px;text-align:justify;text-indent:0;}
    """

    # ---- evidência operacional (fatos verificados na folha; estáveis) ----
    cir_prov, cir_desemp, cir_r216 = 40101.84, 2475.97, 4366.50

    html = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>Parecer Jurídico — Teto Remuneratório · Sete Lagoas/MG</title>
<style>{css}</style></head><body><div class="doc">

<div class="head">
  <div class="org">Auditoria da Folha de Pagamento · Município de Sete Lagoas — Minas Gerais</div>
  <h1>PARECER JURÍDICO</h1>
  <div class="meta">Teto remuneratório constitucional (CF, art. 37, XI e §11) · competência de referência: maio/2026</div>
</div>

<p class="ementa noind"><b>EMENTA.</b> DIREITO CONSTITUCIONAL E ADMINISTRATIVO. TETO REMUNERATÓRIO
MUNICIPAL (CF, ART. 37, XI). SUBSÍDIO DO PREFEITO COMO LIMITE ÚNICO. CÔMPUTO QUE ABRANGE TODAS AS
PARCELAS REMUNERATÓRIAS, "INCORPORADAS OU NÃO" (LC MUN. 192/2016, ART. 130). EXCLUSÃO RESTRITA ÀS
VERBAS DE CARÁTER INDENIZATÓRIO (CF, ART. 37, §11). PROCURADORES MUNICIPAIS. EXCEDENTE INTEGRADO POR
APOSTILAMENTO, ADICIONAL POR TEMPO DE SERVIÇO E GRATIFICAÇÕES — VANTAGENS PESSOAIS QUE SE SUBMETEM AO
TETO. INEXISTÊNCIA DE DIREITO ADQUIRIDO A REGIME REMUNERATÓRIO (TEMA 257/STF, RE 606.358). ABATE-TETO
DEVIDO, DE EFICÁCIA PROSPECTIVA. AUSÊNCIA DE HONORÁRIOS SUCUMBENCIAIS (ADI 6.053 INAPLICÁVEL). OMISSÃO
NA FIXAÇÃO LEGAL DO SUBSÍDIO PARA A LEGISLATURA VIGENTE (CF, ART. 29, V).</p>

<h2>I — Relatório</h2>
<p>Submete-se a exame a observância do teto remuneratório na folha de pagamento do Município, à luz
do art. 37, XI, da Constituição, que limita a retribuição do servidor municipal ao subsídio do
Prefeito. A base analítica compreende a integralidade da folha (competência maio/2026), com
reconciliação ao centavo entre o consolidado por servidor e o detalhamento por rubrica. Embora a
base contenha apenas proventos, o nível de rubrica permite isolar as parcelas de natureza
indenizatória e, assim, depurar a base de cálculo do teto na forma do §11 do art. 37 — providência
que o exame originário não realizara. É o relatório.</p>

<h2>II — Fundamentação</h2>

<h3>II.1 — Do parâmetro do teto e da omissão na sua fixação</h3>
<p>O teto remuneratório municipal corresponde ao subsídio do Prefeito (CF, art. 37, XI), comando
reproduzido, com reforço, pelo art. 130 da Lei Complementar municipal nº 192/2016, que o faz incidir
sobre "todas as parcelas integrantes de seus vencimentos ou salários, <i>incorporados ou não</i>", e
pelo art. 37 da LC nº 83/2003. O subsídio foi fixado pela Lei municipal nº 8.180/2012 — Prefeito
{brl(sl['prefeito_2013'])} —, com revisão anual pelo IPCA assegurada pela Lei nº 8.325/2014.
Anote-se, desde logo, relevante <b>omissão</b>: não há, no acervo legislativo, lei de fixação do
subsídio para as legislaturas 2017-2020, 2021-2024 e 2025-2028, em aparente desatenção ao art. 29,
V, da Constituição, que exige fixação por legislatura. Adota-se, por isso, como parâmetro verificável,
o valor efetivamente satisfeito em maio/2026 — {brl(proxy)} —, sem prejuízo da recomendação de que se
edite a competente lei de fixação.</p>

<h3>II.2 — Da base de cálculo: a exclusão restrita do §11 e a prova do abate-teto</h3>
<p>Do teto somente se excluem as parcelas de <i>caráter indenizatório</i> (CF, art. 37, §11);
todas as demais — vencimento, gratificações, adicionais e vantagens pessoais — a ele se sujeitam.
Tal premissa não é teórica: a própria folha contém a rubrica <b>R216 — "Desconto Limite
Constitucional"</b>, que, em dois servidores, reduz a remuneração a exatos {brl(proxy)}, a confirmar
ser este o teto efetivamente praticado pela Administração. Contudo, em caso emblemático — médico
cirurgião com proventos de {brl(cir_prov)} —, o redutor preservou, acima do teto, precisamente a
<b>Gratificação de Desempenho</b> ({brl(cir_desemp)}): parcela de natureza <i>remuneratória</i>, não
indenizatória, que, por força do art. 130 da LC nº 192/2016, deveria compor o cômputo. Configura-se,
aí, <b>vício de subinclusão</b> da base de cálculo. Depurada a base na forma do §11, dos {nbru}
servidores que superam o teto em valores brutos remanescem <b>{n511}</b>, com excedente de
{brl(exc_mes)}/mês, ou <span class="num">{mi(exc_ano)}/ano</span>.</p>

<h3>II.3 — Da situação dos Procuradores Municipais</h3>
<p>Dos {n511} servidores, {nmed['n']} são não-médicos ({mi(nmed['exc_ano'])}/ano), com núcleo de
<b>7 Procuradores Municipais</b>; os demais {med['n']} são médicos, beneficiários de regime próprio
(acumulação lícita e plantões adstritos ao subsídio). O excedente dos Procuradores <b>não</b> decorre
de honorários sucumbenciais — inexistentes na folha —, mas do <b>empilhamento de vantagens pessoais</b>
(apostilamento, triênios, adicional por tempo de serviço e gratificações), na forma do art. 27 da LC
nº 205/2017. Tais parcelas submetem-se ao teto, à luz do <b>Tema 257 da repercussão geral</b> (RE
606.358):</p>
<blockquote>"Computa-se, para efeito de observância do teto remuneratório do art. 37, XI, da
Constituição da República, também o valor percebido a título de vantagens pessoais pelo servidor
público, dispensada a restituição dos valores recebidos em excesso e de boa-fé até o dia 18 de
novembro de 2015."</blockquote>
<p>Não há, pois, direito adquirido a regime remuneratório apto a excepcionar o teto. O apostilamento
— parcela de maior peso na espécie — encontra censura adicional no <b>Tema 395</b> (RE 638.115), que
reputou inconstitucional a incorporação de quintos/décimos oriundos de função comissionada. Tampouco
socorre os Procuradores a tese do <b>Tema 384</b> (incidência do teto por vínculo), restrita às
hipóteses de acumulação lícita (CF, art. 37, XVI), de que não se cuida — vínculo único. Por fim, a
<b>ADI 6.053</b>, que submete ao teto os honorários da advocacia pública, é <i>in casu</i>
inaplicável, ante a inexistência da verba.</p>

<h3>II.4 — Da eficácia temporal do abate-teto</h3>
<p>A glosa do excedente há de operar <b>prospectivamente</b>: o próprio Tema 257 dispensa a
restituição de valores percebidos de boa-fé até 18 de novembro de 2015, de sorte que não se cogita
de repetição do passado, mas de cessação, daqui por diante, do pagamento acima do teto, observados o
contraditório e a ampla defesa.</p>

<h2>III — Conclusão</h2>
<p class="noind">Ante o exposto, conclui-se:</p>
<ol>
<li>A exposição juridicamente sustentável, depurada na forma do §11, é de
<span class="num">{mi(exc_ano)}/ano</span> ({n511} servidores), e não a apurada pelo critério bruto
(R$ 5,78 mi); destes, {estrut['n']} excedem o teto de modo estrutural — <span class="risco">🟡</span>,
porquanto pendente a fixação nominal do subsídio;</li>
<li>Recomenda-se a <b>edição de lei de fixação</b> do subsídio do Prefeito, Vice e Secretários para a
legislatura vigente (CF, art. 29, V), sanando a omissão apontada — <span class="risco">🔴</span>;</li>
<li>Impõe-se o <b>acionamento do abate-teto</b> (rubrica R216), computando-se todas as parcelas
remuneratórias — inclusive a Gratificação de Desempenho e os prêmios de produtividade —, excluídas tão
somente as indenizatórias (§11), com correção do vício de subinclusão demonstrado;</li>
<li>Quanto aos <b>Procuradores Municipais</b>, a glosa do excedente é juridicamente sólida (Tema
257/STF), de <b>eficácia prospectiva</b>, respeitada a boa-fé até 18/11/2015 e o devido processo
legal;</li>
<li>A exposição não equivale a economia, sujeitando-se à confirmação individualizada e à fixação do
parâmetro nominal.</li>
</ol>

<p class="noind">É o parecer, <i>sub censura</i>.</p>
<div class="sig">Sete Lagoas/MG, 17 de junho de 2026.<br><br>
____________________________________<br>
<i>Auditoria da Folha — análise técnico-jurídica (minuta para subscrição por procurador/advogado habilitado)</i></div>

<div class="ref">Fundamentos (acervo SAPL/Leis Municipais, conferidos verbatim): CF, art. 37, XI e §11, e art.
29, V; LC mun. 192/2016, arts. 130 e 145; LC mun. 83/2003, art. 37; Leis mun. 8.180/2012 e 8.325/2014;
LC mun. 205/2017, art. 27; LC mun. 84/2003. Jurisprudência: STF, RE 606.358 (Tema 257); RE 638.115
(Tema 395); RE 612.975 e RE 602.043 (Tema 384); ADI 6.053. Suporte fático: servidor_mes.parquet ×
folha_municipio_long.parquet (maio/2026); detalhamento individual em CASOS_TETO_SETE_LAGOAS.xlsx.</div>

</div></body></html>"""

    out = OUT / "PARECER_TETO.html"
    out.write_text(html, encoding="utf-8")
    print(f"Parecer gravado: {out} ({out.stat().st_size/1024:.0f} KB)")
    return out


if __name__ == "__main__":
    main()
