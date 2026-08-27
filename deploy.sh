#!/bin/bash
set -e

echo "=== Deploy Anaue Cobrança ==="

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "[INFO] Arquivo .env não encontrado. Copiando de .env.example..."
    cp .env.example .env
    echo "[AVISO] Edite o arquivo .env com suas credenciais antes de continuar!"
    echo "        Principalmente: MONGODB_URI, WHATSAPP_API_URL, WHATSAPP_API_KEY, EMAIL_USER, EMAIL_PASS"
    exit 1
fi

echo "[INFO] Parando containers existentes..."
docker compose down

echo "[INFO] Construindo imagens..."
docker compose build --no-cache

echo "[INFO] Subindo serviços..."
docker compose up -d

echo "[INFO] Aguardando healthchecks..."
# Aguarda MongoDB ficar healthy
echo "  Aguardando MongoDB..."
timeout 60 bash -c 'until docker compose ps mongodb | grep -q "healthy"; do sleep 2; done' || echo "  [AVISO] Timeout aguardando MongoDB"

# Aguarda App ficar healthy
echo "  Aguardando Dashboard..."
timeout 60 bash -c 'until docker compose ps app | grep -q "healthy"; do sleep 2; done' || echo "  [AVISO] Timeout aguardando Dashboard"

echo "[INFO] Verificando status..."
docker compose ps

echo ""
echo "=== Deploy Concluído ==="
echo "Dashboard: http://localhost:5000"
echo "Healthcheck: http://localhost:5000/health"
echo "MongoDB:   localhost:27017"
echo ""
echo "Logs:"
echo "  Dashboard: docker compose logs -f app"
echo "  Cron:      docker compose logs -f cron"
echo "  Automation (manual): docker compose run --rm automation"
echo ""
echo "Status dos Healthchecks:"
docker compose ps --format "table {{.Name}}\t{{.Status}}"