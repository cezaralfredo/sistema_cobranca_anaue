import sys
sys.path.insert(0, 'E:/Projetos/sistema_cobranca_anaue')

from skills.skill_whatsapp import WhatsAppSender
import os
from dotenv import load_dotenv

load_dotenv('E:/Projetos/sistema_cobranca_anaue/.env')

api_url = os.getenv('WHATSAPP_API_URL', 'http://localhost:8080')
instance = os.getenv('WHATSAPP_INSTANCE', 'anaue')
api_key = os.getenv('WHATSAPP_API_KEY', '')

print("Testando Evolution GO...")
print("API URL: " + api_url)
print("Instance: " + instance)

sender = WhatsAppSender(
    api_url=api_url,
    instance=instance,
    api_key=api_key,
    timeout=30,
    retries=1,
)

print("\nEnviando mensagem de teste para 5585996277707...")
resultado = sender.enviar(
    numero="5585996277707",
    mensagem="Teste de envio - Sistema de Cobrança Anaue. Mensagem de teste."
)

if resultado:
    print("SUCESSO! Mensagem enviada!")
else:
    print("FALHA ao enviar mensagem")
    print("Verifique:")
    print("1. Se a Evolution GO esta rodando")
    print("2. Se a instancia '" + instance + "' esta conectada")
    print("3. Se o numero esta correto")
