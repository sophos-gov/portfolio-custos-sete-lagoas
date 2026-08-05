# -*- coding: utf-8 -*-
"""
legal_extract.py — Trilha A.0 (Agente de EXTRACAO LEGAL)

Extrai o TEXTO INTEGRAL de TODAS as leis em legislacao_cache:
  - .pdf  -> pdfplumber
  - .doc  -> Word COM (win32com)
  - .bin  -> na verdade .docx (URL termina em .docx) -> Word COM (win32com)

Salva cada texto em legislacao_full/<id>.txt (id = nome sem extensao).
Usa UMA instancia do Word para todos os arquivos Office, sequencial.
"""
import os
import sys
import glob
import json
import shutil
import traceback

BASE = r"C:\Users\victo\OneDrive\Documentos\Python\projetos\custos\folha\auditoria-folha-sete-lagoas"
CACHE = os.path.join(BASE, "legislacao_cache")
OUT = os.path.join(BASE, "legislacao_full")
os.makedirs(OUT, exist_ok=True)

# WdSaveFormat
WD_FORMAT_TEXT = 2          # wdFormatText
WD_FORMAT_UNICODE_TEXT = 7  # wdFormatEncodedText (UTF) - usaremos via SaveAs2 com encoding

results = {}  # id -> dict(metodo, chars, arquivo_saida, ok, erro)


def out_path(stem):
    return os.path.join(OUT, stem + ".txt")


# ----------------------------------------------------------------------
# 1) PDFs via pdfplumber
# ----------------------------------------------------------------------
def extract_pdfs():
    import pdfplumber
    pdfs = sorted(glob.glob(os.path.join(CACHE, "*.pdf")))
    for p in pdfs:
        stem = os.path.splitext(os.path.basename(p))[0]
        try:
            parts = []
            with pdfplumber.open(p) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    parts.append(t)
            text = "\n".join(parts)
            dst = out_path(stem)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)
            results[stem] = dict(metodo="pdfplumber", chars=len(text),
                                 arquivo_saida=dst, ok=len(text) > 0, erro=None)
            print(f"[PDF] {stem}: {len(text)} chars -> {dst}")
        except Exception as e:
            results[stem] = dict(metodo="pdfplumber", chars=0,
                                 arquivo_saida=out_path(stem), ok=False,
                                 erro=f"{type(e).__name__}: {e}")
            print(f"[PDF][ERRO] {stem}: {e}")
            traceback.print_exc()


# ----------------------------------------------------------------------
# 2) .doc e .bin (docx) via Word COM
# ----------------------------------------------------------------------
def extract_office():
    # Coleta arquivos office: .doc e .bin (que e docx)
    office = sorted(glob.glob(os.path.join(CACHE, "*.doc")))
    bins = sorted(glob.glob(os.path.join(CACHE, "*.bin")))

    # Usa LATE BINDING (dynamic.Dispatch) p/ evitar o gen_py cache corrompido.
    import win32com.client.dynamic as dynamic

    word = dynamic.Dispatch("Word.Application")
    word.Visible = False
    try:
        word.DisplayAlerts = 0  # wdAlertsNone
    except Exception:
        pass

    # Para .bin: o Word abre por conteudo, mas a extensao .bin nao e reconhecida.
    # Estrategia robusta: copiar para um arquivo .docx temporario antes de abrir.
    tmp_files = []

    def open_and_extract(src_path, stem, metodo_label, confirm_conversions=False):
        doc = None
        try:
            doc = word.Documents.Open(
                src_path,
                ConfirmConversions=confirm_conversions,
                ReadOnly=True,
                AddToRecentFiles=False,
            )
            text = doc.Content.Text or ""
            # Word usa \r como separador de paragrafo; normaliza para \n
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            dst = out_path(stem)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)
            results[stem] = dict(metodo=metodo_label, chars=len(text),
                                 arquivo_saida=dst, ok=len(text) > 0, erro=None)
            print(f"[WORD] {stem}: {len(text)} chars -> {dst}")
        except Exception as e:
            results[stem] = dict(metodo=metodo_label, chars=0,
                                 arquivo_saida=out_path(stem), ok=False,
                                 erro=f"{type(e).__name__}: {e}")
            print(f"[WORD][ERRO] {stem}: {e}")
            traceback.print_exc()
        finally:
            if doc is not None:
                try:
                    doc.Close(SaveChanges=0)
                except Exception:
                    pass

    try:
        # .doc files
        for p in office:
            stem = os.path.splitext(os.path.basename(p))[0]
            open_and_extract(p, stem, "win32com(.doc)", confirm_conversions=False)

        # .bin files -> copiar para .docx temp e abrir
        for p in bins:
            stem = os.path.splitext(os.path.basename(p))[0]
            tmp = os.path.join(CACHE, "_tmp_" + stem + ".docx")
            try:
                shutil.copyfile(p, tmp)
                tmp_files.append(tmp)
                open_and_extract(tmp, stem, "win32com(.bin->docx)", confirm_conversions=False)
            except Exception as e:
                # fallback: tentar abrir o .bin diretamente com ConfirmConversions
                print(f"[WORD] copia docx falhou p/ {stem} ({e}); tentando abrir .bin direto")
                open_and_extract(p, stem, "win32com(.bin-direct)", confirm_conversions=False)
    finally:
        try:
            word.Quit()
        except Exception:
            pass
        for t in tmp_files:
            try:
                os.remove(t)
            except Exception:
                pass


if __name__ == "__main__":
    print("=== EXTRACAO PDFs ===")
    extract_pdfs()
    print("\n=== EXTRACAO OFFICE (.doc/.bin) via Word COM ===")
    extract_office()

    print("\n=== RESUMO ===")
    summary = []
    for stem in sorted(results.keys()):
        r = results[stem]
        summary.append({"id": stem, **r})
        print(f"{stem:18s} ok={r['ok']!s:5s} chars={r['chars']:>8d} metodo={r['metodo']}")

    with open(os.path.join(OUT, "_extract_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\nResumo salvo em", os.path.join(OUT, "_extract_summary.json"))
