# Deploy Docker / Portainer CE - Sistema de Cobrança Anaue

## Pré-requisitos
- Docker 24+ e Docker Compose v2+
- Portainer CE (opcional, para UI)

---

## 1. Preparação

```bash
# Clone/entre no projeto
cd sistema_cobranca_anaue

# Copie e edite as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais reais:
# - MONGODB_URI (use mongodb://mongodb:27017/ no Docker)
# - WHATSAPP_API_URL (use http://host.docker.internal:8080 se Evolution API no host)
# - WHATSAPP_API_KEY
# - EMAIL_USER / EMAIL_PASS
```

---

## 2. Deploy via Script (Recomendado)

### Linux/macOS/Git Bash:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Windows PowerShell:
```powershell
.\deploy.ps1
```

---

## 3. Deploy Manual

```bash
# Build e sobe tudo
docker compose up -d --build

# Verifica status
docker compose ps

# Logs
docker compose logs -f app      # Dashboard
docker compose logs -f cron     # Agendador
```

---

## 4. Deploy no Portainer CE

### 4.0. Pré-requisitos no Servidor

```bash
# No servidor onde roda o Portainer Agent / Docker
# Verifique se Docker e Docker Compose estão instalados
docker --version
docker compose version

# Clone o repositório (ou copie os arquivos)
git clone <seu-repo> sistema_cobranca_anaue
cd sistema_cobranca_anaue
```

### 4.1. Passo a Passo Detalhado (Portainer UI)

#### 1. Preparar Variáveis de Ambiente
- No servidor, crie o arquivo `.env` baseado no `.env.example`:
```bash
cp .env.example .env
nano .env  # Edite com suas credenciais reais
```
- **Importante:** Use valores Docker:
  - `MONGODB_URI=mongodb://mongodb:27017/`
  - `WHATSAPP_API_URL=http://host.docker.internal:8080` (se Evolution API no host)

#### 2. Configurar Permissões do Docker Socket (OBRIGATÓRIO)
> **Faça isso ANTES de criar a stack**

1. No Portainer: **Environments** → clique no seu ambiente
2. **Settings** → **Security** (sidebar esquerda)
3. Marque:
   - ✅ **Allow bind mounts**
   - ✅ **Privileged containers**
4. Clique **Save settings**

#### 3. Criar a Stack

1. Menu lateral: **Stacks** → **Add stack**
2. **Name:** `anaue-cobranca`
3. **Build method:** **Editor** (ou "Repository" se usar Git)
4. **Editor:** Cole todo o conteúdo do arquivo `docker-compose.yml`
5. **Environment variables:** 
   - Opção A: Clique **Load from .env file** e selecione o `.env` do servidor
   - Opção B: Adicione manualmente cada variável (Name/Value)
6. Clique **Deploy the stack**

#### 4. Acompanhar Deploy

1. Após clicar Deploy, a tela mostra o log de build em tempo real
2. Aguarde aparecer **"Stack deployed successfully"**
3. Vá em **Containers** → filtre por `anaue-cobranca`
4. Verifique se os 4 containers estão **Running (healthy)**:

| Container Name | Status Esperado | Porta |
|----------------|-----------------|-------|
| `anaue-cobranca-app` | Running (healthy) | 5000 |
| `anaue-cobranca-cron` | Running (healthy) | — |
| `anaue-mongodb` | Running (healthy) | 27017 |
| `anaue-cobranca-automation` | Exited (0) ou Created | — |

> **Nota:** `automation` fica `Exited (0)` ou `Created` - é normal, ele roda sob demanda via cron.

#### 5. Validar Funcionamento

```bash
# No servidor (ou via Portainer > Containers > Logs)
# 1. Testa healthcheck do app
curl http://localhost:5000/health
# {"status":"healthy","service":"anaue-cobranca"}

# 2. Acessa dashboard
# Abra no navegador: http://SEU_IP:5000

# 3. Testa automação manual
docker exec anaue-cobranca-automation python main.py
```

---

### 4.2. Configuração Necessária no Portainer CE (Obrigatório para Cron)

O container `cron` precisa acessar o Docker Socket (`/var/run/docker.sock`) para executar `docker exec` no container `automation`. No Portainer CE:

1. Vá em **Environments** → selecione seu ambiente
2. **Settings** → **Security**
3. Marque:
   - ✅ **Allow bind mounts**
   - ✅ **Privileged containers**
4. Salve e faça **redeploy** da stack

> **Nota:** Sem essa permissão, o cron iniciará mas falhará ao tentar executar a automação (erro: `permission denied` no Docker socket).

### 4.3. Limitações Conhecidas do Portainer CE

| Limitação | Workaround |
|-----------|------------|
| Não edita stacks via UI após deploy (só redeploy) | Edite o `docker-compose.yml` local e faça **Redeploy** na stack |
| Variáveis sensíveis ficam visíveis na UI | Use **Docker Secrets** (requer modo Swarm) ou injete via CI/CD externo |
| Cron precisa de `/var/run/docker.sock` | Habilite "Allow bind mounts" + "Privileged containers" (acima) |
| Healthchecks aparecem mas não bloqueiam deploy | Monitore via `docker compose ps` ou Portainer → Containers → Status |

---

## 5. Containers Criados (Verificação Pós-Deploy)

Após o deploy bem-sucedido, **4 containers** devem existir:

| Container Name | Imagem | Status Esperado | Porta | Função |
|----------------|--------|-----------------|-------|--------|
| `anaue-cobranca-app` | `anaue-cobranca:latest` (build local) | **Running (healthy)** | 5000 | Dashboard Web (Flask) |
| `anaue-cobranca-cron` | `crazymax/swiss-army-knife:latest` | **Running (healthy)** | — | Agendador (cron 09:00) |
| `anaue-mongodb` | `mongo:7` | **Running (healthy)** | 27017 | Banco de dados |
| `anaue-cobranca-automation` | `anaue-cobranca:latest` (build local) | **Exited (0)** ou **Created** | — | Worker de cobrança (sob demanda) |

### 5.1. Estados Normais por Container

#### `anaue-cobranca-app` (Dashboard)
- **Status:** `Up X minutes (healthy)`
- **Healthcheck:** `GET /health` a cada 30s
- **Logs:** `docker compose logs -f app` ou Portainer > Logs
- **Acesso:** http://localhost:5000

#### `anaue-cobranca-cron` (Agendador)
- **Status:** `Up X minutes (healthy)`
- **Healthcheck:** Verifica Docker socket a cada 60s
- **Logs:** `docker compose logs -f cron`
- **Execução:** Roda `docker exec anaue-cobranca-automation python main.py` às 09:00

#### `anaue-mongodb` (Banco)
- **Status:** `Up X minutes (healthy)`
- **Healthcheck:** `mongosh --eval "db.adminCommand('ping')"` a cada 10s
- **Dados:** Persistidos no volume `mongodb_data`
- **Backup:** Ver seção 6

#### `anaue-cobranca-automation` (Worker)
- **Status:** `Exited (0) X minutes ago` **OU** `Created`
- **Comportamento:** Normal! Ele NÃO roda continuamente
- **Execução:** 
  - Automática: Via cron (diário 09:00)
  - Manual: `docker compose run --rm automation` ou `docker exec anaue-cobranca-automation python main.py`
- **Opções:** `--whatsapp`, `--email` (ex: `python main.py --whatsapp`)

### 5.2. Verificação Rápida (Checklist)

```bash
# 1. Todos containers existem?
docker compose ps
# Deve mostrar 4 linhas

# 2. Healthchecks passing?
docker compose ps --format "table {{.Name}}\t{{.Status}}"
# Deve mostrar (healthy) para app, cron, mongodb

# 3. Dashboard responde?
curl -s http://localhost:5000/health | jq
# {"status":"healthy","service":"anaue-cobranca"}

# 4. Automação roda manualmente?
docker compose run --rm automation
# Deve processar clientes e sair com código 0

# 5. Cron agendou? (ver logs após 09:00)
docker compose logs cron
# Deve mostrar execução do comando docker exec
```

---

## 6. Serviços

| Serviço | Descrição | Porta | Acesso | Healthcheck |
|---------|-----------|-------|--------|-------------|
| `app` | Dashboard Web (Flask) | 5000 | http://localhost:5000 | `GET /health` |
| `automation` | Worker de cobrança (roda sob demanda) | - | `docker compose run --rm automation` | - |
| `cron` | Agendador diário (09:00) | - | Logs: `docker compose logs -f cron` | Docker socket |
| `mongodb` | Banco de dados | 27017 | Interno / localhost:27017 | `db.adminCommand('ping')` |

---

## 5.1. Healthchecks

Todos os serviços principais possuem healthchecks configurados:

```bash
# Verifica status de healthcheck
docker compose ps

# Exemplo saída esperada:
# NAME                    STATUS
# anaue-cobranca-app      Up 30s (healthy)
# anaue-cobranca-cron     Up 30s (healthy)
# anaue-mongodb           Up 30s (healthy)
```

**Endpoints:**
- **App:** `http://localhost:5000/health` → retorna `{"status":"healthy","service":"anaue-cobranca"}`
- **MongoDB:** `mongosh --eval "db.adminCommand('ping')"`
- **Cron:** Verifica se Docker socket está acessível

**Configuração (docker-compose.yml):**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

O `deploy.sh` / `deploy.ps1` aguarda automaticamente os healthchecks passarem antes de concluir.

---

## 6. Comandos Úteis

```bash
# Rodar automação manualmente
docker compose run --rm automation

# Rodar apenas WhatsApp ou Email
docker compose run --rm automation python main.py --whatsapp
docker compose run --rm automation python main.py --email

# Ver logs do cron (execuções agendadas)
docker compose logs -f cron

# Backup do MongoDB
docker exec anaue-mongodb mongodump --uri="mongodb://localhost:27017/sistema_assinaturas" --out=/data/backup
docker cp anaue-mongodb:/data/backup ./backup-$(date +%F)

# Restart apenas do dashboard
docker compose restart app

# Parar tudo
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados do MongoDB)
docker compose down -v
```

---

## 7. Ajuste de Horário do Cron

Edite `docker-compose.yml` → serviço `cron` → `CRON_SCHEDULE`:

```yaml
environment:
  - CRON_SCHEDULE=0 9 * * *   # 09:00 todos os dias (padrão)
  # Exemplos:
  # - CRON_SCHEDULE=0 8 * * 1-5  # 08:00 seg-sex
  # - CRON_SCHEDULE=0 */6 * * *  # A cada 6 horas
  - TZ=America/Sao_Paulo
```

---

## 8. Evolution API no Host (Windows/macOS)

Se a Evolution API roda no **host** (fora do Docker):

- **Docker Desktop (Win/Mac/Linux):** `http://host.docker.internal:8080`
- **Linux nativo (sem Docker Desktop):** Descubra IP da interface `docker0`:
  ```bash
  ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
  # Use: http://<IP_DOCKER0>:8080
  ```

---

## 9. Troubleshooting

| Problema | Solução |
|----------|---------|
| `connection refused` MongoDB | Aguarde ~10s após `up -d`, ou verifique `docker compose logs mongodb` |
| WhatsApp não envia | Verifique `WHATSAPP_API_URL` acessível do container (`curl` de dentro do container) |
| Cron não roda | Verifique logs: `docker compose logs cron`; confirme `TZ` e `CRON_SCHEDULE` |
| Dashboard não carrega | `docker compose logs app`; verifique porta 5000 livre |
| Permissão Docker Socket | Ver [Seção 4.1](#41-configuração-necessária-no-portainer-ce-obrigatório-para-cron): habilite "Allow bind mounts" + "Privileged containers" no Portainer |
| Healthcheck falha (app) | Verifique `docker compose logs app`; confirme se `/health` responde (curl localhost:5000/health) |
| Healthcheck falha (mongodb) | Verifique `docker compose logs mongodb`; MongoDB pode estar iniciando (aguarde `start_period`) |
| Container fica em `starting` | Healthcheck não passa; verifique logs e aumente `start_period` se necessário |

---

## 10. Estrutura de Volumes

```
./static/          → QR Code PIX (compartilhado app/automation/cron)
mongodb_data       → Dados persistentes do MongoDB (volume nomeado)
```