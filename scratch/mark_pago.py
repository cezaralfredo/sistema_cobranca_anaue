import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client['sistema_assinaturas']
colecao = db.assinaturas

# Marcar um cliente qualquer como 'pago' para teste
result = colecao.update_one(
    {"cobranca.status": "pendente"},
    {"$set": {"cobranca.status": "pago"}}
)

if result.modified_count > 0:
    print("Sucesso! Um cliente foi marcado como 'pago'.")
else:
    print("Nenhum cliente pendente encontrado para marcar como 'pago'.")
