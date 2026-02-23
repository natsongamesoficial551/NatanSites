# ============================================================
#   database.py — PostgreSQL (Render persiste os dados!)
#   Variável de ambiente: DATABASE_URL
# ============================================================
import os
import logging
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

def get_conn():
    """Retorna conexão com o PostgreSQL via DATABASE_URL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("❌ Variável DATABASE_URL não definida!")
    # psycopg2 não aceita "postgres://", precisa ser "postgresql://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db():
    """Cria todas as tabelas se não existirem."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                -- ── LOJA ─────────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS produtos (
                    id        TEXT PRIMARY KEY,
                    nome      TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    valor     TEXT NOT NULL,
                    estoque   INTEGER NOT NULL DEFAULT 0,
                    imagem    TEXT,
                    msg_id    BIGINT
                );

                CREATE TABLE IF NOT EXISTS carrinho (
                    user_id    TEXT NOT NULL,
                    produto_id TEXT NOT NULL,
                    nome       TEXT NOT NULL,
                    valor      TEXT NOT NULL,
                    PRIMARY KEY (user_id, produto_id)
                );

                -- ── COMPRAS ───────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS compras (
                    id         TEXT PRIMARY KEY,
                    usuario_id BIGINT NOT NULL,
                    produto    TEXT NOT NULL,
                    valor      TEXT NOT NULL,
                    observacao TEXT,
                    criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS compras_contador (
                    id    INTEGER PRIMARY KEY CHECK (id = 1),
                    valor INTEGER NOT NULL DEFAULT 0
                );
                INSERT INTO compras_contador (id, valor)
                VALUES (1, 0)
                ON CONFLICT (id) DO NOTHING;

                -- ── PROJETOS ──────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS projetos (
                    id        TEXT PRIMARY KEY,
                    nome      TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    url       TEXT,
                    imagem    TEXT,
                    cliente   TEXT,
                    msg_id    BIGINT
                );

                -- ── FREE ──────────────────────────────────────────────
                CREATE TABLE IF NOT EXISTS free_itens (
                    id        TEXT PRIMARY KEY,
                    nome      TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    link      TEXT NOT NULL,
                    estoque   INTEGER,
                    imagem    TEXT,
                    msg_id    BIGINT
                );
                """)
        logger.info("✅ Banco de dados PostgreSQL iniciado.")
    finally:
        conn.close()
