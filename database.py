# ============================================================
#   database.py — Banco de dados SQLite centralizado
#   Todas as tabelas do bot ficam em data/natansites.db
# ============================================================
import sqlite3, os, logging

logger = logging.getLogger(__name__)
DB_FILE = "data/natansites.db"

def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row   # retorna linhas como dicionário
    conn.execute("PRAGMA journal_mode=WAL")  # mais seguro para reinicializações
    return conn

def init_db():
    """Cria todas as tabelas se não existirem."""
    with get_conn() as conn:
        conn.executescript("""
        -- ── LOJA ─────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS produtos (
            id        TEXT PRIMARY KEY,
            nome      TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor     TEXT NOT NULL,
            estoque   INTEGER NOT NULL DEFAULT 0,
            imagem    TEXT,
            msg_id    INTEGER
        );

        CREATE TABLE IF NOT EXISTS carrinho (
            user_id    TEXT NOT NULL,
            produto_id TEXT NOT NULL,
            nome       TEXT NOT NULL,
            valor      TEXT NOT NULL,
            PRIMARY KEY (user_id, produto_id)
        );

        -- ── COMPRAS ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS compras (
            id         TEXT PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            produto    TEXT NOT NULL,
            valor      TEXT NOT NULL,
            observacao TEXT,
            criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS compras_contador (
            id    INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 0
        );
        INSERT OR IGNORE INTO compras_contador (id, valor) VALUES (1, 0);

        -- ── PROJETOS ──────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS projetos (
            id        TEXT PRIMARY KEY,
            nome      TEXT NOT NULL,
            descricao TEXT NOT NULL,
            url       TEXT,
            imagem    TEXT,
            cliente   TEXT,
            msg_id    INTEGER
        );

        -- ── FREE ──────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS free_itens (
            id        TEXT PRIMARY KEY,
            nome      TEXT NOT NULL,
            descricao TEXT NOT NULL,
            link      TEXT NOT NULL,
            estoque   INTEGER,           -- NULL = ilimitado
            imagem    TEXT,
            msg_id    INTEGER
        );
        """)
    logger.info("✅ Banco de dados SQLite iniciado.")
