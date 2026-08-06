# -*- coding: utf-8 -*-
"""
build_xlsx_teto.py — Planilha XLSX bem formatada com TODOS os casos acima do teto
remuneratório, especificando a situação de cada servidor.

Lê output/municipio/teto_aprofundamento.json (fonte única) e gera
output/municipio/CASOS_TETO_SETE_LAGOAS.xlsx com 2 abas:
  1. "Casos acima do teto" — os 38 com bruto > teto, classificados por situação
  2. "Base legal e resumo"  — KPIs, subsídio legal, brechas

Uso:  python municipio/build_xlsx_teto.py
"""
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output" / "municipio"

NAVY = "051C2C"; BLUE = "2251FF"; SOFT = "F4F6F8"
RED = "C0392B"; AMBER = "E08600"; GREEN = "1E7A46"; GREY = "8A94A0"
WHITE = "FFFFFF"

thin = Side(style="thin", color="D8DDE1")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
MONEY = 'R$ #,##0.00'


def classifica(r, teto, delta_idx):
    """Retorna (situacao, categoria_cor, encaminhamento) para um servidor de lista_bruto."""
    func = str(r["descr_funcao"]).upper()
    viola_511 = r["base_teto"] > teto
    if viola_511:
        if r["eh_inativo"]:
            return ("Acima do teto (§11) — inativo/pensionista", AMBER,
                    "Teto alcança aposentados (EC 41/03); pensão tem regra própria — segmentar e apurar.")
        if r["eh_medico"]:
            return ("Acima do teto (§11) — médico", AMBER,
                    "Verificar acumulação lícita (art. 37, XVI) e plantão limitado ao subsídio (LC 285/23).")
        if "PROCURADOR" in func:
            return ("Acima do teto (§11) — Procurador", RED,
                    "Empilhamento de vantagens (LC 205/17 art. 27): vencimento + ATS + apostilamento + gratificações. Aplicar abate-teto.")
        if "AUD" in func or "FISCAL" in func:
            return ("Acima do teto (§11) — auditor fiscal", RED,
                    "Excesso por apostilado + triênios + GEPFF (cross-ref A5). Aplicar abate-teto.")
        return ("Acima do teto (§11) — administrativo", RED,
                "Sem justificativa assistencial; apurar e aplicar abate-teto (R216).")
    # bruto > teto mas base §11 <= teto
    verba = delta_idx.get(r["matricula"], "—")
    return (f"Só no bruto — excesso indenizatório (NÃO viola teto)", GREEN,
            f"Verba dominante: {verba}. Férias/13º/rescisão (art. 37, §11) — não é violação de teto.")


def cell(ws, row, col, value, *, bold=False, color=None, fill=None, money=False,
         align="left", size=10, border=True, wrap=False):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name="Calibri", size=size, bold=bold,
                  color=color or ("FFFFFF" if fill in (NAVY, BLUE) else "1A1A1A"))
    if fill:
        c.fill = PatternFill("solid", fgColor=fill)
    c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
    if border:
        c.border = BORDER
    if money:
        c.number_format = MONEY
    return c


def aba_casos(wb, tap):
    ws = wb.active
    ws.title = "Casos acima do teto"
    teto = tap["teto_proxy"]["valor"]
    cen = tap["cenarios"]
    liq = tap.get("liquido_real", {})
    delta_idx = {d["matricula"]: d["verba_dominante"] for d in tap.get("delta_511", [])}
    rec511 = {r["matricula"]: r["meses_viola"] for r in tap.get("lista_511", [])}

    # título
    ws.merge_cells("A1:N1")
    cell(ws, 1, 1, "TETO REMUNERATÓRIO — CASOS ACIMA DO SUBSÍDIO DO PREFEITO · Sete Lagoas/MG · mai/2026",
         bold=True, fill=NAVY, size=13, align="left", border=False)
    ws.merge_cells("A2:N2")
    cell(ws, 2, 1,
         f"Teto-proxy = subsídio do Prefeito {f'R$ {teto:,.2f}'}  ·  "
         f"{cen['bruto']['n']} acima no bruto  ·  {cen['base_511']['n']} acima no líquido (art. 37, §11)  ·  "
         f"exposição §11 R$ {cen['base_511']['exc_ano']:,.2f}/ano",
         fill=SOFT, size=10, align="left", border=False)
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 20

    headers = ["#", "Matrícula", "Nome", "Função", "Secretaria", "Vínculo",
               "Proventos brutos", "Indenizatórias (§11)", "Base de teto (§11)",
               "Líquido real (Saúde/fev)", "Excedente §11", "Recorrência",
               "Situação", "Encaminhamento"]
    hr = 4
    for j, h in enumerate(headers, 1):
        cell(ws, hr, j, h, bold=True, fill=BLUE, align="center", size=10, wrap=True)
    ws.row_dimensions[hr].height = 40

    # ordena: violadores §11 primeiro (por base desc), depois os "só bruto"
    lista = sorted(tap["lista_bruto"],
                   key=lambda r: (0 if r["base_teto"] > teto else 1, -r["base_teto"]))
    r = hr + 1
    for i, s in enumerate(lista, 1):
        sit, cor, enc = classifica(s, teto, delta_idx)
        viola = s["base_teto"] > teto
        lr = liq.get(s["matricula"], {}).get("liquido_fev")
        meses = rec511.get(s["matricula"], s["meses_viola"])
        exc511 = max(0.0, s["base_teto"] - teto)
        cell(ws, r, 1, i, align="center")
        cell(ws, r, 2, s["matricula"], align="center")
        cell(ws, r, 3, s["nome"])
        cell(ws, r, 4, s["descr_funcao"])
        cell(ws, r, 5, str(s["secretaria"]))
        cell(ws, r, 6, str(s["vinculo"]))
        cell(ws, r, 7, s["proventos"], money=True, align="right")
        cell(ws, r, 8, s["indeniz"], money=True, align="right")
        cell(ws, r, 9, s["base_teto"], money=True, align="right", bold=True)
        cell(ws, r, 10, lr if lr else "—", money=bool(lr), align="right")
        cell(ws, r, 11, exc511 if viola else 0, money=True, align="right")
        cell(ws, r, 12, f"{meses}/3" if viola else "—", align="center")
        cell(ws, r, 13, sit, color=cor, bold=True, wrap=True, size=9)
        cell(ws, r, 14, enc, wrap=True, size=9)
        if i % 2 == 0:
            for j in range(1, 15):
                cc = ws.cell(row=r, column=j)
                if cc.fill.fgColor.rgb in (None, "00000000"):
                    cc.fill = PatternFill("solid", fgColor="FBFCFD")
        r += 1

    # totais
    cell(ws, r, 1, "", border=False)
    cell(ws, r, 6, "TOTAL (38 casos)", bold=True, fill=NAVY, align="right")
    cell(ws, r, 7, sum(s["proventos"] for s in lista), money=True, bold=True, fill=NAVY, align="right")
    cell(ws, r, 8, sum(s["indeniz"] for s in lista), money=True, bold=True, fill=NAVY, align="right")
    cell(ws, r, 9, sum(s["base_teto"] for s in lista), money=True, bold=True, fill=NAVY, align="right")
    cell(ws, r, 10, "", fill=NAVY, border=True)
    cell(ws, r, 11, sum(max(0.0, s["base_teto"] - teto) for s in lista), money=True, bold=True, fill=NAVY, align="right")
    for j in (12, 13, 14):
        cell(ws, r, j, "", fill=NAVY, border=True)

    widths = [4, 11, 30, 26, 22, 16, 16, 16, 16, 16, 14, 11, 30, 46]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "C5"
    ws.sheet_view.showGridLines = False


def aba_resumo(wb, tap):
    ws = wb.create_sheet("Base legal e resumo")
    ws.sheet_view.showGridLines = False
    cen = tap["cenarios"]; ag = tap["agregados"]
    sl = tap.get("subsidio_legal", {}); r216 = tap.get("abate_teto_r216", {})

    ws.merge_cells("A1:D1")
    cell(ws, 1, 1, "BASE LEGAL, CENÁRIOS E BRECHAS", bold=True, fill=NAVY, size=13, border=False)
    row = 3

    def secao(titulo):
        nonlocal row
        ws.merge_cells(f"A{row}:D{row}")
        cell(ws, row, 1, titulo, bold=True, fill=BLUE, size=11, border=False)
        row += 1

    def kv(k, v, money=False):
        nonlocal row
        cell(ws, row, 1, k, bold=True, fill=SOFT)
        ws.merge_cells(f"B{row}:D{row}")
        cell(ws, row, 2, v, money=money, align="right" if money else "left")
        row += 1

    secao("Cenários (mai/2026)")
    kv("Teto-proxy (subsídio do Prefeito)", tap["teto_proxy"]["valor"], money=True)
    kv("Acima no BRUTO", f"{cen['bruto']['n']} servidores — excedente R$ {cen['bruto']['exc_ano']:,.2f}/ano")
    kv("Acima no LÍQUIDO §11 (correto)", f"{cen['base_511']['n']} servidores — excedente R$ {cen['base_511']['exc_ano']:,.2f}/ano")
    kv("Efeito do art. 37, §11", f"−{cen['reducao_pct']:.0f}% na exposição")
    kv("Não-médicos / médicos / inativos", f"{ag['nao_medico']['n']} / {ag['medico']['n']} / {ag['inativo_pensionista']['n']}")
    kv("Estruturais (violam 3/3 meses)", f"{ag['estrutural_3de3']['n']}")
    row += 1

    secao("Subsídio do Prefeito — base legal")
    kv("Lei de fixação", sl.get("lei_fixacao", "—"))
    kv("Alteração", sl.get("lei_alteracao", "—"))
    kv("Prefeito (valor 2013)", sl.get("prefeito_2013"), money=True)
    kv("Vice-Prefeito (2013)", sl.get("vice_2013"), money=True)
    kv("Secretários (2013)", sl.get("secretario_2013"), money=True)
    kv("Lei posterior de fixação", sl.get("sem_fixacao_posterior", "—"))
    kv("Valor na folha (mai/2026, proxy)", sl.get("proxy_folha_mai2026"), money=True)
    kv("Fonte", sl.get("fonte", "—"))
    row += 1

    secao("Abate-teto (mecanismo existente)")
    kv("Rubrica R216 DESC.LIMITE CONSTITUCIONAL", f"aplicada a {r216.get('n_servidores','—')} servidores — {r216.get('fonte','')}")
    row += 1

    secao("Aparato de produtividade fiscal / gratificações (brechas)")
    cell(ws, row, 1, "Aparato", bold=True, fill=BLUE); cell(ws, row, 2, "Lei", bold=True, fill=BLUE)
    cell(ws, row, 3, "Servidores", bold=True, fill=BLUE, align="center")
    cell(ws, row, 4, "R$/mês (mai)", bold=True, fill=BLUE, align="center")
    row += 1
    for b in tap.get("brechas", []):
        if not b["n_serv_long"]:
            continue
        cell(ws, row, 1, f"{b['rotulo']} (cód {b['codigo']})")
        cell(ws, row, 2, str(b["lei"]))
        cell(ws, row, 3, b["n_serv_long"], align="center")
        cell(ws, row, 4, b["valor_mes_long"], money=True, align="right")
        row += 1

    for col, w in zip("ABCD", [34, 30, 14, 18]):
        ws.column_dimensions[col].width = w


def main():
    tap = json.loads((OUT / "teto_aprofundamento.json").read_text(encoding="utf-8"))
    wb = Workbook()
    aba_casos(wb, tap)
    aba_resumo(wb, tap)
    out = OUT / "CASOS_TETO_SETE_LAGOAS.xlsx"
    wb.save(out)
    print(f"XLSX gravado: {out} ({out.stat().st_size/1024:.0f} KB)")
    return out


if __name__ == "__main__":
    main()
