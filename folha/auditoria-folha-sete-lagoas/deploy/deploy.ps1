<#
deploy.ps1 — Empacota o projeto, envia para a VPS Hermes, instala e agenda.

Uso (a partir da pasta do projeto):
    .\deploy\deploy.ps1            # instala + agenda timer (01:00)
    .\deploy\deploy.ps1 -RunNow    # instala + agenda + dispara já e acompanha logs
#>
param([switch]$RunNow)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$VPS  = "2.25.171.61"
$KEY  = "$env:USERPROFILE\.ssh\hermes_vps"
$PROJ = "auditoria-folha-sete-lagoas"
$REMOTE = "/root/projetos/$PROJ"
$TGZ  = "auditoria-folha.tgz"

# raiz do projeto = pai da pasta deploy
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT
Write-Host "==> Empacotando $ROOT" -ForegroundColor Cyan

if (Test-Path $TGZ) { Remove-Item $TGZ -Force }
tar --exclude='.env' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' `
    --exclude='checkpoints' --exclude='legislacao_cache' --exclude='output' `
    --exclude='analysis/tabelas' --exclude='progress.jsonl' --exclude='*.tgz' `
    -czf $TGZ -C (Split-Path -Parent $ROOT) $PROJ
Write-Host "    $TGZ ($([math]::Round((Get-Item $TGZ).Length/1MB,2)) MB)"

Write-Host "==> Enviando para $VPS" -ForegroundColor Cyan
ssh -i $KEY root@$VPS "mkdir -p /root/projetos $REMOTE"
scp -i $KEY $TGZ "root@${VPS}:/root/projetos/"

# Envia .env local se existir (senão remote_setup cria e herda do Hermes)
if (Test-Path ".env") {
    Write-Host "    enviando .env local"
    scp -i $KEY ".env" "root@${VPS}:$REMOTE/.env"
}

Write-Host "==> Instalando e agendando na VPS" -ForegroundColor Cyan
ssh -i $KEY root@$VPS "cd /root/projetos && tar -xzf $TGZ && cd $PROJ && chmod +x deploy/remote_setup.sh && bash deploy/remote_setup.sh"

if ($RunNow) {
    Write-Host "==> Disparando execução agora (Ctrl+C para parar de acompanhar)" -ForegroundColor Green
    ssh -i $KEY root@$VPS "systemctl start auditoria-folha.service; journalctl -u auditoria-folha.service -f"
} else {
    Write-Host "==> Concluído. O agente roda automaticamente às 01:00." -ForegroundColor Green
    Write-Host "    Rodar agora:  ssh -i `"$KEY`" root@$VPS `"systemctl start auditoria-folha.service`""
    Write-Host "    Monitorar:    .\deploy\monitor.ps1"
}
