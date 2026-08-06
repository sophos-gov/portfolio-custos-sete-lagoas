<#
monitor.ps1 — Verificação matinal / acompanhamento do agente noturno na Hermes.

Uso:
    .\deploy\monitor.ps1            # status + relatório + progresso
    .\deploy\monitor.ps1 -Follow    # acompanha o log em tempo real
    .\deploy\monitor.ps1 -Pull      # baixa o dashboard HTML para ./output
#>
param([switch]$Follow, [switch]$Pull)

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$VPS  = "2.25.171.61"
$KEY  = "$env:USERPROFILE\.ssh\hermes_vps"
$PROJ = "auditoria-folha-sete-lagoas"
$REMOTE = "/root/projetos/$PROJ"
$ROOT = Split-Path -Parent $PSScriptRoot

if ($Follow) {
    ssh -i $KEY root@$VPS "journalctl -u auditoria-folha.service -f"
    return
}

if ($Pull) {
    New-Item -ItemType Directory -Force -Path "$ROOT\output" | Out-Null
    scp -i $KEY "root@${VPS}:$REMOTE/output/relatorio_custos_folha_saude_setelagoas.html" "$ROOT\output\"
    scp -i $KEY "root@${VPS}:$REMOTE/RELATORIO_EXECUCAO.md" "$ROOT\" 2>$null
    Write-Host "Baixado para $ROOT\output\" -ForegroundColor Green
    Invoke-Item "$ROOT\output\relatorio_custos_folha_saude_setelagoas.html"
    return
}

Write-Host "==> Status do serviço" -ForegroundColor Cyan
ssh -i $KEY root@$VPS "systemctl is-active auditoria-folha.service; systemctl list-timers --no-pager | grep auditoria-folha"
Write-Host "`n==> RELATORIO_EXECUCAO.md" -ForegroundColor Cyan
ssh -i $KEY root@$VPS "cat $REMOTE/RELATORIO_EXECUCAO.md 2>/dev/null || echo '(ainda não gerado)'"
Write-Host "`n==> Últimas linhas do progresso" -ForegroundColor Cyan
ssh -i $KEY root@$VPS "tail -n 20 $REMOTE/progress.jsonl 2>/dev/null || echo '(sem progress.jsonl)'"
Write-Host "`n==> Tamanho do dashboard" -ForegroundColor Cyan
ssh -i $KEY root@$VPS "du -h $REMOTE/output/*.html 2>/dev/null || echo '(HTML ainda não gerado)'"
Write-Host "`nDica: .\deploy\monitor.ps1 -Pull  para baixar e abrir o dashboard." -ForegroundColor DarkGray
