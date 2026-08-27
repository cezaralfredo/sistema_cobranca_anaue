<# 
.SYNOPSIS
    Deploy script for Anaue Cobrança on Windows/PowerShell
#>

Write-Host "=== Deploy Anaue Cobrança ===" -ForegroundColor Cyan

# Verifica se .env existe
if (-not (Test-Path ".env")) {
    Write-Host "[INFO] Arquivo .env não encontrado. Copiando de .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[AVISO] Edite o arquivo .env com suas credenciais antes de continuar!" -ForegroundColor Red
    Write-Host "        Principalmente: MONGODB_URI, WHATSAPP_API_URL, WHATSAPP_API_KEY, EMAIL_USER, EMAIL_PASS" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Parando containers existentes..." -ForegroundColor Yellow
docker compose down

Write-Host "[INFO] Construindo imagens..." -ForegroundColor Yellow
docker compose build --no-cache

Write-Host "[INFO] Subindo serviços..." -ForegroundColor Yellow
docker compose up -d

Write-Host "[INFO] Aguardando healthchecks..." -ForegroundColor Yellow
Write-Host "  Aguardando MongoDB..." -ForegroundColor Gray
$timeout = 60
$start = Get-Date
while ((docker compose ps mongodb | Select-String "healthy") -eq $null) {
    if ((Get-Date) - $start).TotalSeconds -gt $timeout {
        Write-Host "  [AVISO] Timeout aguardando MongoDB" -ForegroundColor Yellow
        break
    }
    Start-Sleep -Seconds 2
}

Write-Host "  Aguardando Dashboard..." -ForegroundColor Gray
$start = Get-Date
while ((docker compose ps app | Select-String "healthy") -eq $null) {
    if ((Get-Date) - $start).TotalSeconds -gt $timeout {
        Write-Host "  [AVISO] Timeout aguardando Dashboard" -ForegroundColor Yellow
        break
    }
    Start-Sleep -Seconds 2
}

Write-Host "[INFO] Verificando status..." -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "=== Deploy Concluído ===" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Healthcheck: http://localhost:5000/health" -ForegroundColor Cyan
Write-Host "MongoDB:   localhost:27017" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "  Dashboard: docker compose logs -f app" -ForegroundColor Gray
Write-Host "  Cron:      docker compose logs -f cron" -ForegroundColor Gray
Write-Host "  Automation (manual): docker compose run --rm automation" -ForegroundColor Gray
Write-Host ""
Write-Host "Status dos Healthchecks:" -ForegroundColor Cyan
docker compose ps --format "table {{.Name}}\t{{.Status}}"