"""
Camada de acesso a dados do Sistema de Cobrança Anaue (PostgreSQL).

Adapta a estrutura original (que usava MongoDB) para o PostgreSQL dedicado da
stack, mantendo a MESMA interface que a aplicação consome: objetos do tipo
"coleção" com find/count_documents/insert_one/find_one/update_one/delete_one e
documentos no formato aninhado (ex.: {"cobranca": {"status": ...}}).

Tabela: clientes_anaue
Colunas: id (serial), mongo_id (unique), nome, telefone, email,
         cobranca_status, cobranca_data_vencimento, cobranca_pix,
         cobranca_valor, mensagem_customizada, notificacoes_enviadas (text[]),
         criado_em
"""

import os
import uuid

import config

try:
    import psycopg2
    import psycopg2.extras
except Exception as _e:  # pragma: no cover - import guard
    psycopg2 = None


class DatabaseUnavailable(Exception):
    """Ocorre quando não é possível conectar ao PostgreSQL."""


class ObjectId(str):
    """Compat: o id do documento é a string mongo_id (24 hex)."""
    pass


# ── Inicialização do schema (idempotente, roda 1x por processo) ─────
_schema_ready = False
_INIT_SQL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "db", "init.sql",
)


def _ensure_schema():
    """Cria a tabela + seed no PostgreSQL se ainda não existirem."""
    global _schema_ready
    if _schema_ready:
        return
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.clientes_anaue')")
        if cur.fetchone()[0] is None:
            raw = ""
            if os.path.exists(_INIT_SQL_PATH):
                with open(_INIT_SQL_PATH, "r", encoding="utf-8") as f:
                    raw = f.read()
            if raw.strip():
                cur.execute(raw)  # psycopg2 aceita varias sentencas separadas por ';'
        conn.commit()
        _schema_ready = True
    finally:
        conn.close()


# ── Conflitos/Mapeamento ──────────────────────────────────────────────
# Tabela de mapeamento: campo aninhado (mongo) -> coluna postgres
FIELD_TO_COL = {
    "nome": "nome",
    "telefone": "telefone",
    "email": "email",
    "mensagem_customizada": "mensagem_customizada",
    "criado_em": "criado_em",
    "cobranca.status": "cobranca_status",
    "cobranca.data_vencimento": "cobranca_data_vencimento",
    "cobranca.pix": "cobranca_pix",
    "cobranca.valor": "cobranca_valor",
    "notificacoes_enviadas": "notificacoes_enviadas",
    "_id": "mongo_id",
}

_COLUMNS = (
    "mongo_id", "nome", "telefone", "email", "cobranca_status",
    "cobranca_data_vencimento", "cobranca_pix", "cobranca_valor",
    "mensagem_customizada", "notificacoes_enviadas", "criado_em",
)


def _col(field: str) -> str:
    """Converte um caminho de campo mongo para o nome da coluna."""
    return FIELD_TO_COL.get(field, field)


def _connect():
    if psycopg2 is None:
        raise DatabaseUnavailable("psycopg2 não instalado")
    try:
        return psycopg2.connect(config.DATABASE_URL)
    except Exception as e:
        raise DatabaseUnavailable(str(e))


def _row_to_doc(row: dict) -> dict:
    """Converte uma linha SQL no formato de documento que a app já usa."""
    dv = row.get("cobranca_data_vencimento")
    notif = row.get("notificacoes_enviadas") or []

    return {
        "_id": row.get("mongo_id") or "",
        "nome": row.get("nome"),
        "telefone": row.get("telefone"),
        "email": row.get("email"),
        "cobranca": {
            "status": row.get("cobranca_status"),
            "data_vencimento": dv.strftime("%Y-%m-%d") if dv else "",
            "pix": row.get("cobranca_pix"),
            "valor": float(row.get("cobranca_valor") or 0),
        },
        "notificacoes_enviadas": list(notif) if isinstance(notif, list) else [],
        "mensagem_customizada": row.get("mensagem_customizada"),
        "criado_em": row.get("criado_em"),
    }


def _doc_to_insert(doc: dict) -> dict:
    """Converte o documento (aninhado) que a app cria em linha SQL."""
    cob = doc.get("cobranca", {})
    cdv = cob.get("data_vencimento") or ""
    return {
        "mongo_id": doc.get("_id") or uuid.uuid4().hex,
        "nome": doc.get("nome"),
        "telefone": (doc.get("telefone") or "") or None,
        "email": (doc.get("email") or "") or None,
        "cobranca_status": cob.get("status") or "pendente",
        "cobranca_data_vencimento": cdv or None,
        "cobranca_pix": (cob.get("pix") or ""),
        "cobranca_valor": float(cob.get("valor") or 0),
        "mensagem_customizada": doc.get("mensagem_customizada") or "",
        "notificacoes_enviadas": list(doc.get("notificacoes_enviadas") or []),
        "criado_em": doc.get("criado_em"),
    }


class CompatCollection:
    """
    Objeto com interface semelhante à collection do MongoDB, por cima da
    tabela clientes_anaue. Suportado apenas o subconjunto de operações
    realmente usadas pelo dashboard.py/main.py.
    """

    def __init__(self):
        self.database = _CompatDatabase()
        _ensure_schema()

    def _query_where(self, query: dict) -> tuple:
        """Constrói WHERE + params a partir do dict de query (subset usado)."""
        conds, params = [], []
        for field, val in query.items():
            col = _col(field)
            # Regex de busca por nome (dashboard usa $regex com $options "i")
            if isinstance(val, dict) and "$regex" in val:
                conds.append(f"{col} ILIKE %s")
                params.append(f"%{val['$regex']}%")
            elif isinstance(val, list):
                conds.append(f"{col} = ANY(%s)")
                params.append(val)
            elif isinstance(val, ObjectId):
                conds.append(f"{col} = %s")
                params.append(str(val))
            else:
                conds.append(f"{col} = %s")
                if col == "cobranca_data_vencimento":
                    params.append(val)
                elif col in ("cobranca_valor",):
                    params.append(float(val) if val is not None else None)
                else:
                    params.append(val)
        where = " AND ".join(conds) if conds else "TRUE"
        return where, params

    def find(self, query=None, **kwargs):
        query = query or {}
        where, params = self._query_where(query)
        order_sql = ""
        sort = kwargs.get("sort")
        if sort and isinstance(sort, list) and len(sort) == 2:
            order_sql = f" ORDER BY {_col(sort[0])} {sort[1] and 'ASC' or 'DESC'}"
        conn = _connect()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(f"SELECT {', '.join(_COLUMNS)} FROM clientes_anaue WHERE {where}{order_sql}", params)
            rows = cur.fetchall()
            return [_row_to_doc(dict(r)) for r in rows]
        finally:
            conn.close()

    def find_one(self, query=None):
        docs = self.find(query or {})
        return docs[0] if docs else None

    def count_documents(self, query=None):
        query = query or {}
        where, params = self._query_where(query)
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM clientes_anaue WHERE {where}", params)
            return cur.fetchone()[0]
        finally:
            conn.close()

    def insert_one(self, doc: dict):
        data = _doc_to_insert(doc)
        cols = list(data.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO clientes_anaue ({', '.join(cols)}) VALUES ({placeholders})",
                [data[c] for c in cols],
            )
            conn.commit()
        finally:
            conn.close()

    def update_one(self, query, update):
        where, params = self._query_where(query)
        # Monta SET a partir de $set e $push
        setters, push = {}, []
        ups = update or {}
        for key, val in ups.items():
            if key == "$set":
                for f, v in val.items():
                    setters[_col(f)] = _to_col_value(f, v)
            elif key == "$push":
                for f, v in val.items():
                    push.append((_col(f), v))
        set_sql = ", ".join([f"{c} = %s" for c in setters]) if setters else "TRUE"
        params_set = list(setters.values())
        params_all = params_set + list(params)
        conn = _connect()
        try:
            cur = conn.cursor()
            if push:
                # array_append na coluna text[]
                for col, val in push:
                    cur.execute(
                        f"UPDATE clientes_anaue SET {col} = array_append(COALESCE({col}, '{{}}'), %s) WHERE {where}",
                        [str(val)] + params,
                    )
            if setters:
                cur.execute(f"UPDATE clientes_anaue SET {set_sql} WHERE {where}", params_all)
            conn.commit()
        finally:
            conn.close()

    def delete_one(self, query):
        where, params = self._query_where(query)
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM clientes_anaue WHERE {where}", params)
            n = cur.rowcount
            conn.commit()
            class _R:
                deleted_count = n
            return _R()
        finally:
            conn.close()

    def ping(self):
        conn = _connect()
        try:
            conn.cursor().execute("SELECT 1")
        finally:
            conn.close()
        return {}


def _to_col_value(field: str, val):
    """Normaliza o valor de acordo com a coluna (datas/strings vazias)."""
    col = _col(field)
    if col == "cobranca_data_vencimento":
        return val or None
    if col in ("telefone", "email", "mensagem_customizada", "cobranca_pix", "nome"):
        return val if val != "" else None if col in ("telefone", "email") else (val or "")
    return val


class _CompatDatabase:
    def command(self, _cmd=None, **kwargs):
        return {}


def get_colecao():
    """Retorna um objeto coleção compatível (tabela clientes_anaue)."""
    c = CompatCollection()
    c.ping()  # valida conexão imediatamente (equivale ao .admin.command("ping"))
    return c


class DatabaseManager:
    """
    Manager usado pelo main.py (worker/scheduler). Expõe os métodos que o
    fluxo de cobrança chama, mantendo o documento no formato aninhado.
    """

    def __init__(self, uri: str = "", db_name: str = ""):
        # uri/db_name aceites por compatibilidade; o target vem de config.DATABASE_URL
        self.colecao = CompatCollection()

    def buscar_clientes_pendentes(self) -> list:
        return self.colecao.find({"cobranca.status": "pendente"})

    def registrar_envio(self, cliente_id, estagio: str) -> None:
        self.colecao.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$push": {"notificacoes_enviadas": estagio}},
        )

    def fechar_conexao(self) -> None:
        pass