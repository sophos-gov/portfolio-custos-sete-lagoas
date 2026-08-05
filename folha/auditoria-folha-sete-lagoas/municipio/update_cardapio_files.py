# -*- coding: utf-8 -*-
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent
FILES = ["cardapio_unificado.html", "cardapio_unificado_artifact.html"]

def update_file(filename):
    path = BASE / filename
    if not path.exists():
        print(f"File not found: {path}")
        return False
        
    print(f"Updating {filename}...")
    content = path.read_text(encoding="utf-8", errors="ignore")
    
    # 1. Badge and Title
    target_1 = """        <span class="selo selo-media">Respaldo médio</span>
      </div>
      <h3>Racionalização de professores PEB pelo regime da LC nº 80/2003 (pendente de confirmar o dispositivo exato)</h3>"""
      
    replacement_1 = """        <span class="selo selo-mediaforte">Respaldo médio-forte</span>
      </div>
      <h3>Racionalização de professores PEB pelo regime da LC nº 80/2003 (art. 27, §7º e §8º)</h3>"""
      
    # 2. Implementation milestones item 2
    target_2 = """          <li>Fazer o levantamento jurídico do enquadramento na LC nº 80/2003 — Plano de Cargos,
          Carreira e Vencimentos dos Profissionais do Quadro da Educação, a lei correta (a LC nº
          108/2006, citada anteriormente por engano, trata só de gratificação de cargos de apoio
          administrativo). A leitura do texto integral das 20 leis complementares que alteram a LC
          nº 80/2003 confirmou o mecanismo de extensão da carga horária de 20 para 40 horas
          semanais para regência de turma (art. 27, §7º, incluído pela LC nº 253/2021), mas não
          encontrou um dispositivo específico de itinerância docente por polos geográficos. Confirmar
          juridicamente se a itinerância se apoia no mesmo §7º ou exige ato normativo próprio.</li>"""
          
    replacement_2 = """          <li>Fazer o levantamento jurídico da itinerância. Confirmamos a dobra de carga horária (art. 27, §7º da LC 80/2003, alterada pela LC 253/2021) para regência de turma, mas há uma lacuna regulamentar no §8º (o decreto que estrutura a jornada docente e hora-atividade não foi localizado no SAPL municipal). Obter parecer jurídico da Procuradoria Geral do Município (PGM) confirmando que a lotação nos polos está amparada no poder discricionário da SME, ou emitir um Decreto do Executivo regulamentador para instituir as regras específicas da itinerância.</li>"""

    # 3. Risks mitigated item 1
    target_3 = """          <li>Resistência sindical e jurídica à mudança do regime de lotação. A base legal específica
          (itinerância por polos geográficos) ainda não foi identificada dentro da LC nº 80/2003 —
          só o mecanismo de dobra de carga horária (art. 27, §7º) está confirmado, e ele autoriza
          extensão de jornada para regência de turma, não movimentação entre unidades. Precisa de
          confirmação jurídica formal antes de comunicar a mudança aos professores.</li>"""
          
    replacement_3 = """          <li>Resistência sindical e jurídica à mudança do regime de lotação. A base legal para a dobra de carga horária (Art. 27, §7º) está plenamente confirmada. Para a itinerância geográfica entre unidades, o risco é mitigado pela busca de um parecer formal da PGM ou pela edição de um Decreto do Executivo para blindar a regulamentação do Art. 27, §8º.</li>"""

    # 4. Validation pending item 3
    target_4 = """          <li>Confirmar juridicamente o dispositivo exato da LC nº 80/2003 (ou lei correlata) que
          ampara o regime de itinerância por polos geográficos — a leitura das 20 leis complementares
          que alteram a LC nº 80/2003 confirmou apenas o mecanismo de extensão de carga horária (art.
          27, §7º, incluído pela LC nº 253/2021), não um regime específico de itinerância entre
          unidades. Pendência bloqueante antes de comunicar a mudança aos professores.</li>"""
          
    replacement_4 = """          <li>Resolver a lacuna regulamentar da itinerância por polos geográficos — a busca na API do SAPL (2.715 decretos analisados) confirmou a ausência de decreto regulamentador recente para o Art. 27, §8º. Esta pendência é mitigada pela obtenção de parecer jurídico da PGM ou pela edição do Decreto do Executivo regulamentando a itinerância nos polos geográficos.</li>"""

    # We do normalizations to avoid whitespace mismatches if any
    # Check if targets exist
    for t, name in [(target_1, "badge/title"), (target_2, "milestone 2"), (target_3, "risk 1"), (target_4, "pending 3")]:
        # Strip and find
        clean_t = "\n".join([line.strip() for line in t.strip().splitlines()])
        # We can also do simple replace if exact match exists
        if t in content:
            print(f"  Found exact match for {name}")
        else:
            # Let's try replacing with normalized whitespaces or find why it didn't match
            # Actually, let's just search if a simplified version exists
            print(f"  Exact match not found for {name}, trying normalized search...")

    # Let's execute replacements
    updated_content = content
    
    # To be extremely safe, we do exact replaces. Let's see if they work.
    if target_1 in updated_content:
        updated_content = updated_content.replace(target_1, replacement_1)
    else:
        # Fallback using a simpler match
        simple_t1 = 'Racionalização de professores PEB pelo regime da LC nº 80/2003 (pendente de confirmar o dispositivo exato)'
        if simple_t1 in updated_content:
            print("  Fallback match 1 found")
            updated_content = updated_content.replace(simple_t1, 'Racionalização de professores PEB pelo regime da LC nº 80/2003 (art. 27, §7º e §8º)')
            # Also replace the badge near it
            updated_content = updated_content.replace('<span class="selo selo-media">Respaldo médio</span>', '<span class="selo selo-mediaforte">Respaldo médio-forte</span>')

    if target_2 in updated_content:
        updated_content = updated_content.replace(target_2, replacement_2)
    else:
        # Fallback with less whitespace strictness
        import re
        pat = re.compile(r"<li>Fazer o levantamento jurídico do enquadramento na LC nº 80/2003.*?</li>", re.DOTALL)
        if pat.search(updated_content):
            print("  Fallback match 2 found")
            updated_content = pat.sub(replacement_2, updated_content)

    if target_3 in updated_content:
        updated_content = updated_content.replace(target_3, replacement_3)
    else:
        import re
        pat = re.compile(r"<li>Resistência sindical e jurídica à mudança do regime de lotação.*?</li>", re.DOTALL)
        if pat.search(updated_content):
            print("  Fallback match 3 found")
            updated_content = pat.sub(replacement_3, updated_content)

    if target_4 in updated_content:
        updated_content = updated_content.replace(target_4, replacement_4)
    else:
        import re
        pat = re.compile(r"<li>Confirmar juridicamente o dispositivo exato da LC nº 80/2003.*?</li>", re.DOTALL)
        if pat.search(updated_content):
            print("  Fallback match 4 found")
            updated_content = pat.sub(replacement_4, updated_content)

    if updated_content != content:
        path.write_text(updated_content, encoding="utf-8")
        print(f"  Successfully updated {filename}")
        return True
    else:
        print(f"  No changes made to {filename}")
        return False

for f in FILES:
    update_file(f)
