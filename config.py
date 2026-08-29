"""
Módulo de configuração – carrega variáveis de ambiente do arquivo .env
e as expõe como constantes para uso no restante da aplicação.
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# ===== Banco de dados (PostgreSQL dedicado da stack) =====
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://anaue:cobranca@postgres:5432/sistema_cobranca",
).strip()

# ===== Evolution API (WhatsApp) =====
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "").strip()
WHATSAPP_INSTANCE = os.getenv("WHATSAPP_INSTANCE", "anaue").strip()
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "").strip()
WHATSAPP_DELAY_MIN = int(os.getenv("WHATSAPP_DELAY_MIN", "10"))
WHATSAPP_DELAY_MAX = int(os.getenv("WHATSAPP_DELAY_MAX", "30"))
WHATSAPP_TIMEOUT = int(os.getenv("WHATSAPP_TIMEOUT", "30"))
WHATSAPP_RETRIES = int(os.getenv("WHATSAPP_RETRIES", "3"))

# ===== SMTP (E-mail) =====
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")