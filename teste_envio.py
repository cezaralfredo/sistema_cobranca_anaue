import sys
sys.path.insert(0, 'E:/Projetos/sistema_cobranca_anaue')

from skills.skill_whatsapp import WhatsAppSender
import os
from dotenv import load_dotenv

load_dotenv('E:/Projetos/sistema_cobranca_anaue/.env')

# Configurações
api_url = os.getenv('WHATSAPP_API_URL', 'http://localhost:8080')
instance = os.getenv('WHATSAPP_INSTANCE', 'anaue')
api_key = os.getenv('WHATSAPP_API_KEY', '')

print(f"Testando Evolution GO...")
print(f"API URL: {api_url}")
print(f"Instance: {instance}")
print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else f"API Key: {api_key}")

# Criar sender
sender = WhatsAppSender(
    api_url=api_url,
    instance=instance,
    api_key=api_key,
    timeout=30,
    retries=1
)

# Testar conexão
print("\nVerificando conexão...")
if sender.testar_conexao():
    print("✓ Instância conectada!")
    
    # Enviar mensagem de teste
    print("\nEnviando mensagem de teste para 5585935000528...")
    resultado = sender.enviar(
        numero="5585935000528",
        mensagem="Teste de envio - Sistema de Cobrança Anaue. Mensagem de teste automático."
    )
    
    if resultado:
        print("✓ Mensagem enviada com sucesso!")
    else:
        print("✗ Falha ao enviar mensagem")
else:
    print("✗ Instância desconectada!")
    print("Verifique se a Evolution GO está rodando e a instância está conectada.")
