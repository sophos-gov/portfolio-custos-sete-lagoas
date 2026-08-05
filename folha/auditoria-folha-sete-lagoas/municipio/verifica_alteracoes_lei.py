# -*- coding: utf-8 -*-
"""Verifica, no SAPL da Camara de Sete Lagoas, se uma lei foi ALTERADA/REVOGADA.
Uso:  python verifica_alteracoes_lei.py <numero> <ano> [tipo_sigla]
Ex.:  python verifica_alteracoes_lei.py 84 2003        (Lei Complementar)
Tambem cruza com o acervo local (legislacao_full/) procurando quem cita a lei."""
import sys, json, urllib.request, urllib.parse, re
from pathlib import Path

SAPL = "https://sapl.setelagoas.mg.leg.br"
ACERVO = Path(__file__).resolve().parent.parent / "legislacao_full"

def get(path):
    req = urllib.request.Request(SAPL + path, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def tipos_vinculo():
    try:
        d = get("/api/norma/tipovinculonormajuridica/")
        return {t["id"]: (t.get("descricao_ativa") or t.get("sigla") or str(t["id"])) for t in d.get("results", [])}
    except Exception:
        return {}

def main():
    numero = sys.argv[1] if len(sys.argv) > 1 else "84"
    ano = sys.argv[2] if len(sys.argv) > 2 else "2003"
    q = urllib.parse.urlencode({"numero": numero, "ano": ano})
    res = get(f"/api/norma/normajuridica/?{q}").get("results", [])
    if not res:
        print(f"Nao encontrei norma {numero}/{ano} no SAPL."); return
    n = res[0]; nid = n["id"]
    print(f"NORMA: {n['__str__'].strip()}  (id {nid})")
    print(f"Pagina: {SAPL}/norma/{nid}  | Texto: {n.get('texto_integral','')}\n")

    tv = tipos_vinculo()
    def rel(param, rotulo):
        d = get(f"/api/norma/normarelacionada/?{param}={nid}")
        tot = d["pagination"]["total_entries"]
        print(f"{rotulo}: {tot} relacao(oes) registrada(s) no SAPL")
        for r in d.get("results", []):
            lab = tv.get(r.get("tipo_vinculo"), r.get("tipo_vinculo"))
            print(f"   - [{lab}] {r['__str__'].strip()}")
        return tot

    a = rel("norma_relacionada", "QUEM MEXEU NESTA LEI (alterada/revogada por)")
    b = rel("norma_principal", "O QUE ESTA LEI MEXE (altera/revoga)")

    # Cruzamento com acervo local
    print("\nACERVO LOCAL (quem cita esta lei no texto):")
    pat = re.compile(rf"\b{numero}/{ano}\b|\b{numero} de \d\d", re.I)
    hits = []
    if ACERVO.exists():
        for f in ACERVO.glob("lc_*.txt"):
            if f.name.startswith(f"lc_{numero}_"):
                continue
            txt = f.read_text(encoding="utf-8", errors="ignore")
            if pat.search(txt) or re.search(r"89-A|89-B", txt):
                hits.append(f.name)
    print("   " + (", ".join(hits) if hits else "(nenhuma outra lei cita / nada no acervo)"))

    print("\nRESUMO:", "SEM alteracao/revogacao registrada no SAPL." if (a == 0)
          else f"{a} relacao(oes) onde a lei foi afetada — conferir acima.")
    print("AVISO: o registro de relacoes do SAPL e INCOMPLETO (ex.: a revogacao da LC 79/2003 "
          "pela LC 192/2016 NAO esta registrada). Confirme sempre no TEXTO consolidado (LeisMunicipais).")

if __name__ == "__main__":
    main()
