from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId


class DatabaseManager:
    """
    Centraliza todas as interações com o MongoDB para o sistema de cobranças.

    Parâmetros:
        uri     → String de conexão do MongoDB (padrão: localhost)
        db_name → Nome do banco de dados
    """

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017/",
        db_name: str = "sistema_assinaturas",
    ):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.colecao: Collection = self.db["assinaturas"]

    def buscar_clientes_pendentes(self) -> list[dict]:
        """Retorna todos os clientes com status de cobrança 'pendente'."""
        return list(self.colecao.find({"cobranca.status": "pendente"}))

    def registrar_envio(self, cliente_id: ObjectId, estagio: str) -> None:
        """
        Atualiza o documento do cliente registrando que a mensagem
        do estágio informado foi enviada.

        Parâmetros:
            cliente_id → _id do documento no MongoDB
            estagio    → Estágio enviado (ex: "t_minus_5")
        """
        self.colecao.update_one(
            {"_id": cliente_id},
            {"$push": {"notificacoes_enviadas": estagio}},
        )

    def fechar_conexao(self) -> None:
        """Fecha a conexão com o MongoDB."""
        self.client.close()
