# -*- coding: utf-8 -*-
"""
gerar_editavel.py — Gera cardapio_unificado_editavel_artifact.html a partir de
cardapio_unificado.html: a mesma peça, mas com uma barra de edição embutida
(contenteditable + autosave em localStorage + baixar/copiar HTML) para o
usuário ajustar texto direto na página, sem depender de outra rodada de
edição por mim.

Regra igual à do gerar_artifact.py: EDITE SEMPRE cardapio_unificado.html e
rode este script. Nunca edite o arquivo _editavel_artifact diretamente — ele
é gerado. Se cardapio_unificado.html mudar, rode de novo para atualizar a
ferramenta (o rascunho salvo no navegador do usuário não é afetado — vive em
localStorage, por fora deste arquivo).

Uso:
    python gerar_editavel.py
"""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
FONTE = BASE / "cardapio_unificado.html"
DESTINO = BASE / "cardapio_unificado_editavel_artifact.html"

TITULO = "Cardápio Unificado de Soluções para Corte de Custos · Prefeitura de Sete Lagoas/MG"

EDITOR_CSS = """
/* ---------- barra de edição (adicionada por gerar_editavel.py) ---------- */
.editor-bar{
  position:sticky; top:0; z-index:70; background:var(--ink); color:var(--bg-raised);
  border-bottom:1px solid var(--line-strong);
}
.editor-bar .wrap{
  display:flex; align-items:center; gap:.7rem .9rem; flex-wrap:wrap;
  min-height:2.9rem; padding-top:.5rem; padding-bottom:.5rem;
}
.editor-label{
  font-family:var(--mono); font-size:.68rem; letter-spacing:.09em; text-transform:uppercase;
  color:var(--bg-raised); opacity:.72; white-space:nowrap;
}
.editor-actions{display:flex; gap:.5rem; flex-wrap:wrap; align-items:center; margin-left:auto}
.editor-btn{
  font-family:var(--mono); font-size:.7rem; letter-spacing:.03em;
  border:1px solid rgba(255,255,255,.3); background:transparent; color:var(--bg-raised);
  padding:.42rem .68rem; border-radius:3px; cursor:pointer;
}
.editor-btn:hover{border-color:var(--bg-raised)}
.editor-btn:focus-visible{outline:2px solid var(--gold); outline-offset:1px}
.editor-btn[aria-pressed="true"]{background:var(--piso); border-color:var(--piso); color:#fff}
.editor-btn.danger{color:var(--alerta)}
.editor-btn.danger:hover{border-color:var(--alerta)}
.editor-status{
  font-family:var(--mono); font-size:.68rem; color:var(--bg-raised); opacity:.68;
  white-space:nowrap; max-width:38ch; overflow:hidden; text-overflow:ellipsis;
}
.editor-status.ok{opacity:1; color:#bfe3cf}

.editor-banner{background:var(--gold-soft); border-bottom:1px solid var(--line); color:var(--ink); display:none}
.editor-banner.show{display:block}
.editor-banner .wrap{
  display:flex; align-items:center; gap:.6rem 1rem; flex-wrap:wrap;
  padding-top:.55rem; padding-bottom:.55rem; font-size:.85rem;
}
.editor-banner button{
  font-family:var(--mono); font-size:.68rem; border:1px solid var(--line-strong); background:var(--bg-raised);
  color:var(--ink); padding:.32rem .58rem; border-radius:3px; cursor:pointer;
}
.editor-banner button:hover{border-color:var(--accent); color:var(--accent)}

#cardapio-content{cursor:default}
#cardapio-content[contenteditable="true"]{cursor:text}
#cardapio-content[contenteditable="true"]:focus-within .frente{transition:box-shadow .12s}
body.is-editing .topnav{top:2.85rem}
@media (max-width:640px){
  body.is-editing .topnav{top:4.6rem}
}
"""

EDITOR_BODY_TEMPLATE = """
<div class="editor-bar">
  <div class="wrap">
    <span class="editor-label">Editor · rascunho local</span>
    <button id="editToggle" class="editor-btn" type="button" aria-pressed="false">Ativar edição</button>
    <span id="editStatus" class="editor-status" role="status" aria-live="polite"></span>
    <div class="editor-actions">
      <button id="editDownload" class="editor-btn" type="button">Baixar HTML editado</button>
      <button id="editCopy" class="editor-btn" type="button">Copiar HTML</button>
      <button id="editReset" class="editor-btn danger" type="button">Restaurar original</button>
    </div>
  </div>
</div>
<div id="editBanner" class="editor-banner">
  <div class="wrap">
    <span id="editBannerText"></span>
    <button id="editBannerDiscard" type="button">Descartar rascunho e usar original</button>
  </div>
</div>
"""

EDITOR_SCRIPT_TEMPLATE = """
<script id="editor-script">
(function(){
  var root = document.getElementById('cardapio-content');
  var pristine = document.getElementById('pristine-content');
  var toggleBtn = document.getElementById('editToggle');
  var downloadBtn = document.getElementById('editDownload');
  var copyBtn = document.getElementById('editCopy');
  var resetBtn = document.getElementById('editReset');
  var statusEl = document.getElementById('editStatus');
  var banner = document.getElementById('editBanner');
  var bannerText = document.getElementById('editBannerText');
  var bannerDiscard = document.getElementById('editBannerDiscard');
  var STORAGE_KEY = 'cardapio-editavel-v1';
  var saveTimer = null;
  var editing = false;

  function fmtHora(iso){
    try {
      var d = new Date(iso);
      return d.toLocaleString('pt-BR', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
    } catch(e){ return iso; }
  }

  function setStatus(msg, ok){
    statusEl.textContent = msg;
    statusEl.classList.toggle('ok', !!ok);
  }

  function loadDraft(){
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch(e){ return null; }
  }

  function saveDraft(){
    try {
      var payload = { html: root.innerHTML, savedAt: new Date().toISOString() };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
      setStatus('Rascunho salvo às ' + fmtHora(payload.savedAt), true);
    } catch(e){
      setStatus('Não consegui salvar o rascunho neste navegador.', false);
    }
  }

  function scheduleAutosave(){
    setStatus('Editando…', false);
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveDraft, 900);
  }

  function setEditing(on, silent){
    editing = on;
    root.setAttribute('contenteditable', on ? 'true' : 'false');
    toggleBtn.textContent = on ? 'Desativar edição' : 'Ativar edição';
    toggleBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    document.body.classList.toggle('is-editing', on);
    if (!silent) setStatus(on ? 'Modo edição ativo — clique no texto para editar.' : 'Edição desativada.', false);
  }

  function montarDocumento(){
    var styleHtml = document.querySelector('style').outerHTML;
    var navHtml = document.getElementById('doc-nav').outerHTML;
    var scriptHtml = document.getElementById('orig-script').outerHTML;
    return '<!DOCTYPE html>\\n<html lang="pt-BR">\\n<head>\\n<meta charset="utf-8">\\n'
      + '<meta name="viewport" content="width=device-width, initial-scale=1">\\n'
      + '<title>__TITULO__</title>\\n' + styleHtml + '\\n</head>\\n<body>\\n'
      + navHtml + '\\n' + root.innerHTML + '\\n' + scriptHtml + '\\n</body>\\n</html>\\n';
  }

  var draft = loadDraft();
  if (draft && draft.html) {
    root.innerHTML = draft.html;
    bannerText.textContent = 'Rascunho carregado (salvo ' + fmtHora(draft.savedAt) + ').';
    banner.classList.add('show');
  }

  setEditing(false, true);
  setStatus(draft ? 'Rascunho carregado.' : 'Clique em \\u201cAtivar edição\\u201d para começar.', false);

  toggleBtn.addEventListener('click', function(){ setEditing(!editing); });
  root.addEventListener('input', scheduleAutosave);

  bannerDiscard.addEventListener('click', function(){
    if (!confirm('Descartar o rascunho e voltar ao texto original publicado?')) return;
    root.innerHTML = pristine.innerHTML;
    localStorage.removeItem(STORAGE_KEY);
    banner.classList.remove('show');
    setStatus('Original restaurado.', true);
  });

  resetBtn.addEventListener('click', function(){
    if (!confirm('Restaurar o texto original e apagar o rascunho salvo neste navegador? Essa ação não pode ser desfeita.')) return;
    root.innerHTML = pristine.innerHTML;
    localStorage.removeItem(STORAGE_KEY);
    banner.classList.remove('show');
    setStatus('Original restaurado.', true);
  });

  downloadBtn.addEventListener('click', async function(){
    if (!window.claude || !window.claude.downloads) {
      setStatus('Download indisponível aqui — use "Copiar HTML".', false);
      return;
    }
    var doc = montarDocumento();
    setStatus('Baixando…', false);
    try {
      await window.claude.downloads.save({ filename: 'cardapio_unificado_editado.html', data: doc });
      setStatus('Arquivo baixado.', true);
    } catch(err) {
      if (err && (err.code === 'extension_not_enabled' || err.code === 'rejected_extension')) {
        try {
          await window.claude.downloads.save({ filename: 'cardapio_unificado_editado.txt', data: doc });
          setStatus('Baixado como .txt — renomeie para .html ao salvar.', true);
        } catch(err2) {
          setStatus('Não consegui baixar. Use "Copiar HTML".', false);
        }
      } else if (err && err.code === 'declined') {
        setStatus('Download cancelado.', false);
      } else if (err && err.code === 'rate_limited') {
        setStatus('Aguarde um instante e tente de novo.', false);
      } else {
        setStatus('Não consegui baixar. Use "Copiar HTML".', false);
      }
    }
  });

  copyBtn.addEventListener('click', async function(){
    var doc = montarDocumento();
    try {
      await navigator.clipboard.writeText(doc);
      setStatus('HTML completo copiado para a área de transferência.', true);
    } catch(e) {
      setStatus('Não consegui copiar automaticamente — selecione o texto à mão.', false);
    }
  });
})();
</script>
""".replace("__TITULO__", TITULO)


def montar(html: str) -> str:
    m_style = re.search(r"<style>.*?</style>", html, re.S)
    if not m_style:
        raise SystemExit("ERRO: bloco <style> não encontrado em %s" % FONTE.name)

    m_body = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    if not m_body:
        raise SystemExit("ERRO: <body> não encontrado em %s" % FONTE.name)
    body = m_body.group(1)

    m_nav = re.search(r"<nav class=\"topnav\">.*?</nav>", body, re.S)
    if not m_nav:
        raise SystemExit("ERRO: <nav class=\"topnav\"> não encontrada.")
    nav_html = m_nav.group(0)
    resto = body[m_nav.end():]

    m_script = re.search(r"<script>.*?</script>", resto, re.S)
    if not m_script:
        raise SystemExit("ERRO: script original (tema/scrollspy) não encontrado.")
    conteudo = resto[: m_script.start()].strip()
    script_original = m_script.group(0)

    nav_com_id = nav_html.replace(
        '<nav class="topnav">', '<nav class="topnav" id="doc-nav">', 1
    )
    script_original_com_id = script_original.replace(
        "<script>", '<script id="orig-script">', 1
    )

    # Injeta o CSS extra do editor dentro do mesmo bloco <style>...</style> original.
    style_final = m_style.group(0)[: -len("</style>")] + EDITOR_CSS + "</style>"

    saida = []
    saida.append(style_final)
    saida.append(EDITOR_BODY_TEMPLATE.strip())
    saida.append(nav_com_id)
    saida.append('<div id="cardapio-content">')
    saida.append(conteudo)
    saida.append("</div>")
    saida.append('<template id="pristine-content">' + conteudo + "</template>")
    saida.append(script_original_com_id)
    saida.append(EDITOR_SCRIPT_TEMPLATE.strip())

    return "\n\n".join(saida) + "\n"


def main() -> None:
    novo = montar(FONTE.read_text(encoding="utf-8"))
    DESTINO.write_text(novo, encoding="utf-8")
    print(
        "Gerado: %s (%d bytes) a partir de %s."
        % (DESTINO.name, len(novo.encode("utf-8")), FONTE.name)
    )


if __name__ == "__main__":
    main()
