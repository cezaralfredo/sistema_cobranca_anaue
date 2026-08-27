import requests
import os
from dotenv import load_dotenv

load_dotenv('E:/Projetos/sistema_cobranca_anaue/.env')

api_url = os.getenv('WHATSAPP_API_URL', 'http://localhost:8080').strip()
api_key = os.getenv('WHATSAPP_API_KEY', '').strip()
instance = os.getenv('WHATSAPP_INSTANCE', 'anaue').strip()

print("=== TESTE DE AUTENTICAÇÃO EVOLUTION GO ===")
print(f"URL: {api_url}")
print(f"Instance: {instance}")
print(f"API Key (primeiros 20): {api_key[:20]}")
print(f"API Key (length): {len(api_key)}")
print()

# Teste 1: Verificar se API responde
print("Teste 1: Verificando se API responde...")
try:
    r = requests.get(api_url, timeout=5)
    print(f"  Status: {r.status_code}")
except Exception as e:
    print(f"  ERRO: {e}")
    exit(1)

# Teste 2: Verificar status da instância (GET /instance/{name}/status)
print("\nTeste 2: Status da instância...")
url_status = f"{api_url}/instance/{instance}/status"
print(f"  URL: {url_status}")
headers_apikey = {"apikey": api_key}
headers_bearer = {"Authorization": f"Bearer {api_key}"}

for nome, headers in [("apikey", headers_apikey), ("Bearer", headers_bearer)]:
    try:
        r = requests.get(url_status, headers=headers, timeout=5)
        print(f"  {nome}: Status {r.status_code} - {r.text[:150]}")
    except Exception as e:
        print(f"  {nome}: ERRO {e}")

# Teste 3: Enviar mensagem de teste (POST /send/text)
print("\nTeste 3: Enviar mensagem de teste...")
url_send = f"{api_url}/send/text"
print(f"  URL: {url_send}")

payload = {
    "number": "558599627707",
    "text": "Teste de autenticação"
}

for nome, headers in [("apikey", headers_apikey), ("Bearer", headers_bearer)]:
    try:
        r = requests.post(url_send, json=payload, headers=headers, timeout=10)
        print(f"  {nome}: Status {r.status_code} - {r.text[:150]}")
        if r.status_code == 200:
            print("  *** SUCESSO! ***")
            break
    except Exception as e:
        print(f"  {nome}: ERRO {e}")

print("\n=== FIM DO TESTE ===")
