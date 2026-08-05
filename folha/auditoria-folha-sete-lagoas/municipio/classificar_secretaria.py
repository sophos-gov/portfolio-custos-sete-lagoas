# -*- coding: utf-8 -*-
"""
classificar_secretaria.py — FASE 0.3: classifica cada `descr_lotacao` distinta
da folha do município em uma SECRETARIA, via Gemini robusto (grande contexto).

Lê servidor_mes.parquet (todas as competências), extrai as lotações distintas
com R$ e headcount, manda em lote ao Gemini com taxonomia fixa, e grava
municipio/mapa_secretaria.csv (descr_lotacao, secretaria, fonte).

Meta: ≥95% do R$ classificado (não-NAO_CLASSIFICADO).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import deepseek_client  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "municipio" / "data"
OUT = BASE / "municipio" / "mapa_secretaria.csv"

TAXONOMIA = [
    "Saúde", "Educação", "Assistência Social", "Obras/Serviços Urbanos",
    "Administração/Gestão", "Segurança/Guarda/Defesa Civil",
    "Cultura/Esporte/Lazer/Turismo", "Meio Ambiente/Agricultura/Desenvolvimento",
    "Inativos/Pensionistas", "Legislativo/Outros Órgãos", "Outras",
]

PROMPT_HEAD = f"""Você é um especialista em administração pública municipal brasileira.
Classifique cada UNIDADE DE LOTAÇÃO (descr_lotacao) da Prefeitura de Sete Lagoas/MG
em UMA secretaria/área, escolhendo EXCLUSIVAMENTE da lista abaixo (use o texto exato):

{chr(10).join('- ' + t for t in TAXONOMIA)}

Regras:
- "ESF", "UBS", "UPA", "SAMU", "CAPS", "Hospital", "Farmácia", "Vigilância Sanitária",
  "Centro de Saúde", "Maternidade", "Pronto Atendimento" => Saúde.
- "Escola", "CEMEI", "CMEI", "Creche", "Ensino", "Educação", "Biblioteca" => Educação.
- "CRAS", "CREAS", "Assistência", "Acolhimento", "Bolsa", "Convivência" => Assistência Social.
- "Obras", "Pavimentação", "Limpeza Urbana", "Serviços Urbanos", "Trânsito",
  "Iluminação", "Cemitério", "Manutenção viária" => Obras/Serviços Urbanos.
- "Gabinete", "Administração", "Fazenda", "Finanças", "Planejamento", "RH",
  "Procuradoria", "Tributação", "Licitação", "Tecnologia", "Controladoria" => Administração/Gestão.
- "Guarda Municipal", "Defesa Civil", "Segurança" => Segurança/Guarda/Defesa Civil.
- "Cultura", "Esporte", "Lazer", "Turismo" => Cultura/Esporte/Lazer/Turismo.
- "Meio Ambiente", "Agricultura", "Desenvolvimento Econômico", "Indústria", "Comércio" => Meio Ambiente/Agricultura/Desenvolvimento.
- "Aposentado", "Pensionista", "Inativo", "Previdência", "IPSEL", "Fundo Previdenciário" => Inativos/Pensionistas.
- "Câmara", "Legislativo", "Tribunal", "Junta", "Mandato Eletivo" => Legislativo/Outros Órgãos.
- Se for genérico/indefinido (ex.: "LOTACAO", "CARGO NAO DEFINIDO") ou não encaixar, use "Outras".

Responda SOMENTE com um array JSON, sem markdown, no formato:
[{{"descr_lotacao":"<texto exato recebido>","secretaria":"<da lista>"}}, ...]

UNIDADES A CLASSIFICAR (descr_lotacao | servidores | R$/mês):
"""


def carregar_lotacoes() -> pd.DataFrame:
    sm = pd.read_parquet(DATA / "servidor_mes.parquet")
    sm = sm[sm["descr_lotacao"].notna()].copy()
    g = (sm.groupby("descr_lotacao")
         .agg(n_serv=("matricula", "nunique"), rs=("proventos", "sum"))
         .reset_index())
    g["rs_mes"] = (g["rs"] / sm["mes"].nunique()).round(2)
    g = g.sort_values("rs", ascending=False).reset_index(drop=True)
    return g[["descr_lotacao", "n_serv", "rs_mes"]]


def _parse_json(txt: str):
    txt = txt.strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.MULTILINE).strip()
    i, j = txt.find("["), txt.rfind("]")
    if i >= 0 and j > i:
        txt = txt[i:j + 1]
    return json.loads(txt)


def classificar(g: pd.DataFrame, lote: int = 130) -> pd.DataFrame:
    registros = []
    for ini in range(0, len(g), lote):
        chunk = g.iloc[ini:ini + lote]
        linhas = "\n".join(
            f"{r.descr_lotacao} | {int(r.n_serv)} | {r.rs_mes:.2f}" for r in chunk.itertuples())
        prompt = PROMPT_HEAD + linhas
        print(f">> DeepSeek classificando lote {ini}-{ini+len(chunk)} ({len(chunk)} lotações)...",
              file=sys.stderr)
        out = deepseek_client.gen_text(prompt, temperature=0.0, max_tokens=8192)
        if not out:
            print(f"!! DeepSeek retornou vazio no lote {ini}", file=sys.stderr)
            out = "[]"
        try:
            data = _parse_json(out)
        except Exception as e:  # noqa
            print(f"!! parse falhou no lote {ini}: {e}; salvando raw p/ inspeção", file=sys.stderr)
            (DATA / f"_sec_raw_{ini}.txt").write_text(out, encoding="utf-8")
            data = []
        registros.extend(data)
    m = pd.DataFrame(registros)
    if not m.empty:
        m["descr_lotacao"] = m["descr_lotacao"].astype(str).str.strip()
        m["secretaria"] = m["secretaria"].astype(str).str.strip()
        m = m[m["secretaria"].isin(TAXONOMIA)]
        m = m.drop_duplicates(subset=["descr_lotacao"])
    return m


def main():
    g = carregar_lotacoes()
    print(f"Lotações distintas (todos os meses): {len(g)} | "
          f"R$/mês coberto: {g['rs_mes'].sum():,.2f}", file=sys.stderr)
    m = classificar(g)
    # juntar e medir cobertura
    merged = g.merge(m, on="descr_lotacao", how="left")
    falta = merged[merged["secretaria"].isna()]
    cob = (1 - falta["rs_mes"].sum() / g["rs_mes"].sum()) * 100
    print(f"Classificadas: {merged['secretaria'].notna().sum()}/{len(g)} | "
          f"cobertura R$: {cob:.2f}%", file=sys.stderr)
    if len(falta):
        print(f"NÃO classificadas ({len(falta)}): "
              f"{falta.head(15)['descr_lotacao'].tolist()}", file=sys.stderr)
    out = merged[["descr_lotacao", "secretaria"]].copy()
    out["secretaria"] = out["secretaria"].fillna("Outras")
    out["fonte"] = "deepseek-chat"
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Gravado: {OUT} ({len(out)} linhas)", file=sys.stderr)


if __name__ == "__main__":
    main()
