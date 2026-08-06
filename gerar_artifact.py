# -*- coding: utf-8 -*-
"""
gerar_artifact.py — Regenera cardapio_unificado_artifact.html a partir de
cardapio_unificado.html.

Motivo: as duas variantes precisam ser idênticas em conteúdo. A variante
_artifact é o mesmo documento sem DOCTYPE/html/head/body, formato exigido pela
ferramenta Artifact. Manter as duas à mão já causou perda de conteúdo: a frente
PES-003 foi adicionada só no arquivo principal e ficou fora do artifact
publicado (detectado em 2026-08-03).

Regra: EDITE SEMPRE cardapio_unificado.html e rode este script. Nunca edite o
_artifact diretamente — ele é gerado.

Uso:
    python gerar_artifact.py            # regenera
    python gerar_artifact.py --check    # só verifica se está em dia (exit 1 se não)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
FONTE = BASE / "cardapio_unificado.html"
DESTINO = BASE / "cardapio_unificado_artifact.html"


def montar(html: str) -> str:
    """Extrai <style> do head + conteúdo do <body> e concatena."""
    m_style = re.search(r"<style>.*?</style>", html, re.S)
    if not m_style:
        raise SystemExit("ERRO: bloco <style> não encontrado em %s" % FONTE.name)

    m_body = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    if not m_body:
        raise SystemExit("ERRO: <body> não encontrado em %s" % FONTE.name)

    return m_style.group(0) + m_body.group(1).rstrip() + "\n"


def main() -> None:
    checar = "--check" in sys.argv
    novo = montar(FONTE.read_text(encoding="utf-8"))
    atual = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else None

    if atual == novo:
        print("OK: %s já está em dia com %s." % (DESTINO.name, FONTE.name))
        return

    if checar:
        print("DESATUALIZADO: %s difere do gerado a partir de %s."
              % (DESTINO.name, FONTE.name))
        print("Rode 'python gerar_artifact.py' antes de publicar.")
        raise SystemExit(1)

    DESTINO.write_text(novo, encoding="utf-8")
    print("Regenerado: %s (%d bytes) a partir de %s."
          % (DESTINO.name, len(novo.encode("utf-8")), FONTE.name))


if __name__ == "__main__":
    main()
