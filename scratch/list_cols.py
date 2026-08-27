import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client['sistema_assinaturas']
print("Collections in 'sistema_assinaturas':")
print(db.list_collection_names())
