"""
Subsistema de enriquecimento legal das rubricas.

Princípio de robustez: a IDENTIFICAÇÃO da lei vem das DESCRIÇÕES das rubricas
(confiável, ex.: "GRAT. SERV. URGENCIA MEDICO LC 285/23"). O TEXTO da lei
(scraping) é enriquecimento OPCIONAL. Por isso a seção #legislacao é útil mesmo
sem internet e sem API.

Pipeline:
  discover_laws()        -> leis_alvo.json            (determinístico)
  fetch_law(lei_id)      -> legislacao_cache/<id>.txt (best-effort, cacheado)
  classify_rubricas()    -> rubricas_legislacao.json  (Flash; fallback determinístico)
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from . import config
from . import cheap

sys.path.insert(0, str(config.BASE / "analysis"))
import folha_tables  # noqa: E402


# ---------------------------------------------------------------------------
# Normalização e extração de referência legal
# ---------------------------------------------------------------------------
def _up(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return s.upper()


_RE_LC = re.compile(r"\b(?:LC|LEI\s*COMPL(?:EMENTAR)?\.?)\s*N?[º°O]?\.?\s*(\d{2,4})\s*(?:/\s*(\d{2,4}))?")
_RE_LEI = re.compile(r"\bLEI(?:\s*FEDERAL)?\s*N?[º°O]?\.?\s*(\d{3,5})\s*(?:/\s*(\d{2,4}))?")
_RE_NUM_ANO = re.compile(r"\b(\d{3,5})\s*/\s*(\d{2,4})\b")  # ex.: 7757/09, 1835/96


def _norm_ano(a: str | None) -> str | None:
    if not a:
        return None
    a = a.strip()
    if len(a) == 2:
        return ("19" + a) if int(a) > 40 else ("20" + a)
    return a


# Anos canônicos das LCs de Sete Lagoas (algumas rubricas omitem o ano)
_CANON_LC_ANO = {"183": "15", "190": "16", "192": "16", "235": "20", "285": "23", "263": "22", "174": "14"}


def lei_from_descricao(desc: str) -> str | None:
    """Extrai um identificador de lei a partir da descrição da rubrica."""
    d = _up(desc)
    m = _RE_LC.search(d)
    if m:
        num = m.group(1)
        ano = _norm_ano(m.group(2))
        ano2 = (ano[-2:] if ano else None) or _CANON_LC_ANO.get(num)
        return f"LC {num}/{ano2}" if ano2 else f"LC {num}"
    m = _RE_LEI.search(d)
    if m:
        ano = _norm_ano(m.group(2))
        return f"Lei {m.group(1)}/{ano}" if ano else f"Lei {m.group(1)}"
    m = _RE_NUM_ANO.search(d)
    if m:
        ano = _norm_ano(m.group(2))
        return f"Lei {m.group(1)}/{ano}"
    return None


# ---------------------------------------------------------------------------
# Heurística de grupo (propósito de custo) e lei inferida
# ---------------------------------------------------------------------------
_GRUPOS = [
    ("Plantão e urgência", ["PLANTAO", "SOBRE AVISO", "URGENCIA", "AMBULATORIAL", "ASSIST. MEDICA",
                            "ASSIST MEDICA", "SERV. URG", "SERV URG", "COORD UPA", "COORD PABV", "PAC"]),
    ("Insalubridade", ["INSALUBRIDADE"]),
    ("Periculosidade", ["PERICULOSIDADE"]),
    ("Tempo de serviço", ["QUINQUENIO", "TRIENIO", "TRINTENARIO", "30 ANOS", "TEMPO DE SERVICO",
                          "TEMPO DE SERVIÇO", "REPOSICAO TEMPO", "REPOSIÇAO TEMPO"]),
    ("Jornada extraordinária", ["HORAS EXTRA", "ADICIONAL NOTURNO", "NOTURNO"]),
    ("Função e comissão", ["FUNCAO GRATIFICADA", "FUNÇAO GRATIFICADA", "COMISSAO", "COMISSÃO",
                          "FUNCAO GRAT", "FG ", "MEMBRO"]),
    ("Férias, 13º e benefícios", ["FERIAS", "FÉRIAS", "1/3", "ABONO", "NATALICIO", "MATERNIDADE",
                                  "13.SAL", "13 SAL", "13.SALARIO", "DECIMO TERCEIRO", "SALARIO FAMILIA",
                                  "FERIAS PREMIO"]),
    ("Vencimento base / PCCV", ["VENCIMENTO BASICO", "SALARIO BASE", "SALÁRIO BASE", "SUBSIDIO",
                               "PADRAO VENC", "PADRÃO VENC", "SALARIO APOSTILADO", "VENCIMENTO BASE"]),
    ("Reposição / verba indenizatória", ["REPOSICAO", "REPOSIÇAO", "REPOSIÇÃO", "INDENIZAT"]),
    ("Contrato temporário", ["CONTRATO"]),
    ("Gratificações diversas", ["GRATIFICACAO", "GRATIFICAÇAO", "GRATIF", "GRAT", "ESPECIALIZACAO",
                               "DESEMPENHO", "EMPENHO", "RECONHECIMENTO", "PRODUT"]),
]

# Lei inferida por grupo quando a descrição não cita lei explícita
_LEI_INFERIDA = {
    "Vencimento base / PCCV": "LC 183/15",
    "Contrato temporário": "Lei de contratação temporária (PSS)",
    "Tempo de serviço": "Estatuto dos Servidores",
    "Insalubridade": "Estatuto / LC de insalubridade",
    "Periculosidade": "Estatuto / LC de periculosidade",
}


def grupo_de(desc: str) -> str:
    d = _up(desc)
    for grupo, kws in _GRUPOS:
        if any(k in d for k in kws):
            return grupo
    return "Outras rubricas"


# ---------------------------------------------------------------------------
# 1) Descoberta de leis (determinística)
# ---------------------------------------------------------------------------
def discover_laws(out: bool = True) -> list[dict]:
    dic = config.DATA_DIR / "dicionario_rubricas.csv"
    leis: dict[str, dict] = {}
    if dic.exists():
        df = folha_tables._read_csv_robusto(dic, dtype=str)
        df.columns = [folha_tables._norm_col(c) for c in df.columns]
        for _, r in df.iterrows():
            cod = str(r.get("codigo", "")).strip()
            desc = str(r.get("descricao", "")).strip()
            lei = lei_from_descricao(desc)
            if not lei:
                continue
            e = leis.setdefault(lei, {"lei_id": lei, "rubricas": [], "exemplos": []})
            e["rubricas"].append(cod)
            if len(e["exemplos"]) < 3:
                e["exemplos"].append(desc)
    leis_list = sorted(leis.values(), key=lambda x: -len(x["rubricas"]))
    for e in leis_list:
        e["n_rubricas"] = len(e["rubricas"])
    if out:
        (config.TABELAS_DIR / "leis_alvo.json").write_text(
            json.dumps(leis_list, ensure_ascii=False, indent=2), encoding="utf-8")
    return leis_list


# ---------------------------------------------------------------------------
# 2) Scraping best-effort (cacheado) — TEXTO da lei é opcional
# ---------------------------------------------------------------------------
def _slug(lei_id: str) -> str:
    return re.sub(r"[^\w]+", "_", _up(lei_id)).strip("_").lower()


def fetch_law(lei_id: str, timeout: int = 12) -> dict:
    """Tenta baixar o texto da lei. Retorna {lei_id, status, chars, source}."""
    cache = config.CACHE_DIR / f"{_slug(lei_id)}.txt"
    meta = config.CACHE_DIR / f"{_slug(lei_id)}.meta.json"
    if cache.exists() and cache.stat().st_size > 200:
        m = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        return {"lei_id": lei_id, "status": "cache", "chars": cache.stat().st_size, "source": m.get("source", "cache")}

    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception as e:
        return {"lei_id": lei_id, "status": "sem_dependencia", "chars": 0, "source": str(e)}

    m = re.search(r"(\d{2,5})(?:/(\d{2,4}))?", lei_id)
    numero = m.group(1) if m else lei_id
    termo = f"{lei_id} sete lagoas".replace(" ", "+")
    candidatos = [
        f"https://leismunicipais.com.br/a/mg/s/sete-lagoas/busca?q={termo}",
        f"https://www.google.com/search?q={termo}+site:leismunicipais.com.br",
    ]
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AuditoriaFolhaBot/1.0)"}
    for url in candidatos:
        dominio_ok = any(dom in url for dom in config.LAW_SCRAPE_DOMAINS) or "google.com" in url
        if not dominio_ok:
            continue
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code != 200 or len(resp.text) < 500:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            texto = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n")).strip()
            if len(texto) < 300:
                continue
            cache.write_text(texto[:60000], encoding="utf-8")
            meta.write_text(json.dumps({"lei_id": lei_id, "source": url}, ensure_ascii=False), encoding="utf-8")
            return {"lei_id": lei_id, "status": "ok", "chars": len(texto), "source": url}
        except Exception:
            continue
    return {"lei_id": lei_id, "status": "nao_localizada", "chars": 0, "source": None}


# ---------------------------------------------------------------------------
# 3) Classificação rubrica→lei→grupo→propósito + agregação de custo
# ---------------------------------------------------------------------------
def _proposito_flash(rubricas_lote: list[dict]) -> dict[str, str]:
    """Gera propósito de 1 linha por rubrica (lote) via modelo barato. Retorna {codigo: proposito}."""
    if not cheap.cheap_available():
        return {}
    itens = "\n".join(f'{r["codigo"]}: {r["descricao"]}' for r in rubricas_lote)
    prompt = (
        "Você classifica rubricas de folha de pagamento de uma prefeitura (Secretaria de Saúde).\n"
        "Para cada rubrica abaixo, escreva um PROPÓSITO de UMA linha (até 12 palavras), em PT-BR, "
        "explicando o que aquela verba paga. Não julgue legalidade. Responda APENAS JSON "
        '{"CODIGO": "proposito", ...}.\n\nRUBRICAS:\n' + itens
    )
    txt = cheap.gen_text(prompt, temperature=0.2)
    if not txt:
        return {}
    try:
        txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.MULTILINE).strip()
        d = json.loads(txt)
        return {str(k): str(v) for k, v in d.items()}
    except Exception:
        return {}


def classify_rubricas(use_flash: bool = True) -> dict:
    """Gera rubricas_legislacao.json. Funciona sem API (determinístico) e melhora com Flash."""
    long = folha_tables.load_long(config.DATA_DIR)
    rub_df, _ = folha_tables.gerar_rubricas_top(long, top=10000)  # todas as rubricas de provento
    rubricas = rub_df.to_dict("records")
    total_valor = sum(r["valor_total"] for r in rubricas) or 1.0

    # propósitos via Flash (lotes de 25), best-effort
    propos: dict[str, str] = {}
    metodo = "deterministico"
    if use_flash and cheap.cheap_available():
        lote = [{"codigo": r["codigo"], "descricao": r["descricao_rubrica"]} for r in rubricas]
        for i in range(0, len(lote), 25):
            propos.update(_proposito_flash(lote[i:i + 25]))
        if propos:
            metodo = "llm_barato"

    out_rubricas = []
    valor_com_lei = 0.0
    for r in rubricas:
        cod, desc, val = r["codigo"], r["descricao_rubrica"], r["valor_total"]
        grupo = grupo_de(desc)
        lei = lei_from_descricao(desc)
        status = "localizada"
        if not lei:
            lei = _LEI_INFERIDA.get(grupo)
            status = "inferida" if lei else "nao localizada"
        if lei:
            valor_com_lei += val
        out_rubricas.append({
            "codigo": cod, "descricao": desc, "grupo": grupo,
            "lei_criadora": lei or "—",
            "proposito_1linha": propos.get(cod, desc.title()),
            "valor_total": round(val, 2),
            "n_servidores": int(r["n_servidores"]),
            "lei_status": status,
            "confidence": 0.9 if status == "localizada" else (0.6 if status == "inferida" else 0.3),
        })

    # Agregações
    por_lei: dict[str, dict] = {}
    por_grupo: dict[str, dict] = {}
    for r in out_rubricas:
        if r["lei_criadora"] != "—":
            e = por_lei.setdefault(r["lei_criadora"], {"lei_id": r["lei_criadora"], "valor_total": 0.0,
                                                       "n_rubricas": 0, "grupo": r["grupo"]})
            e["valor_total"] += r["valor_total"]
            e["n_rubricas"] += 1
        g = por_grupo.setdefault(r["grupo"], {"grupo": r["grupo"], "valor_total": 0.0, "n_rubricas": 0})
        g["valor_total"] += r["valor_total"]
        g["n_rubricas"] += 1

    # Mesclar ementa oficial do SAPL (leis_resumo.json) como propósito de cada lei
    resumo_path = config.TABELAS_DIR / "leis_resumo.json"
    leis_sapl = {}
    if resumo_path.exists():
        try:
            leis_sapl = json.loads(resumo_path.read_text(encoding="utf-8")).get("leis", {})
        except Exception:
            leis_sapl = {}
    for e in por_lei.values():
        e["valor_total"] = round(e["valor_total"], 2)
        sapl = leis_sapl.get(e["lei_id"], {})
        ementa = (sapl.get("ementa") or "").strip()
        if ementa:
            e["proposito"] = ementa[:180].capitalize()
            e["data"] = sapl.get("data")
            e["fonte"] = sapl.get("fonte")
        else:
            e["proposito"] = e["grupo"]
    for g in por_grupo.values():
        g["valor_total"] = round(g["valor_total"], 2)

    resultado = {
        "metodo": metodo,
        "cobertura_valor_pct": round(valor_com_lei / total_valor * 100, 2),
        "valor_total_proventos": round(total_valor, 2),
        "por_lei": sorted(por_lei.values(), key=lambda x: -x["valor_total"]),
        "por_grupo": sorted(por_grupo.values(), key=lambda x: -x["valor_total"]),
        "rubricas": out_rubricas,
    }
    (config.TABELAS_DIR / "rubricas_legislacao.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


if __name__ == "__main__":
    leis = discover_laws()
    print(f"Leis descobertas: {len(leis)} -> {[l['lei_id'] for l in leis]}")
    res = classify_rubricas(use_flash=False)
    print(f"Método: {res['metodo']} | cobertura por valor: {res['cobertura_valor_pct']}% | "
          f"leis: {len(res['por_lei'])} | grupos: {len(res['por_grupo'])}")
    print("Top grupos:", [(g['grupo'], g['valor_total']) for g in res['por_grupo'][:5]])
