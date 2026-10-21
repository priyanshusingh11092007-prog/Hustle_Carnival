import sqlite3

from flask import current_app, g

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # psycopg is only required when DATABASE_URL is set
    psycopg = None


# =========================================================
# PostgreSQL compatibility wrapper
# =========================================================

class _NullCursor:
    """Returned for SQLite-only statements (PRAGMA) that PostgreSQL ignores."""

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class PostgresConnection:
    """
    Lets the existing QueueSathi code (written for sqlite3) run on PostgreSQL:
      - converts ? placeholders to %s
      - ignores PRAGMA statements
      - turns BEGIN IMMEDIATE into a table lock so tokens are issued safely
      - returns rows that support row["column_name"]
    """

    def __init__(self, url):
        if psycopg is None:
            raise RuntimeError(
                "psycopg is not installed. Run: pip install -r requirements.txt"
            )

        self._conn = psycopg.connect(
            url,
            row_factory=dict_row,
            connect_timeout=10,
            prepare_threshold=None,  # required for pooled (PgBouncer) connections
        )

    @staticmethod
    def _translate(sql):
        upper = sql.strip().upper()

        if upper.startswith("PRAGMA"):
            return None

        if upper.startswith("BEGIN IMMEDIATE"):
            # Serialises queue changes, like SQLite's BEGIN IMMEDIATE.
            return "LOCK TABLE tokens IN SHARE ROW EXCLUSIVE MODE"

        return sql.replace("?", "%s")

    def execute(self, sql, params=None):
        sql = self._translate(sql)

        if sql is None:
            return _NullCursor()

        return self._conn.execute(sql, params or None)

    def executescript(self, script):
        self._conn.execute(script)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


# =========================================================
# Connection management
# =========================================================

def using_postgres():
    return bool(current_app.config.get("DATABASE_URL"))


def get_db():
    if "db" not in g:
        if using_postgres():
            g.db = PostgresConnection(current_app.config["DATABASE_URL"])
        else:
            db = sqlite3.connect(current_app.config["DATABASE"], timeout=15)
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            db.execute("PRAGMA busy_timeout = 15000")
            g.db = db

    return g.db


def close_db(error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def column_exists(db, table, column):
    columns = db.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in columns)


# =========================================================
# Database initialisation
# =========================================================

def init_db():
    db = get_db()

    if using_postgres():
        with current_app.open_resource("schema_postgres.sql") as file:
            db.executescript(file.read().decode("utf-8"))
        db.commit()
        return

    # ---------- SQLite (local development) ----------

    with current_app.open_resource("schema.sql") as file:
        db.executescript(file.read().decode("utf-8"))

    # Upgrade databases created by older QueueSathi versions.
    if not column_exists(db, "users", "service_id"):
        db.execute(
            "ALTER TABLE users ADD COLUMN service_id INTEGER REFERENCES services(id)"
        )

    if not column_exists(db, "tokens", "student_id"):
        db.execute(
            "ALTER TABLE tokens ADD COLUMN student_id INTEGER REFERENCES students(id)"
        )

    if not column_exists(db, "tokens", "queue_order"):
        db.execute("ALTER TABLE tokens ADD COLUMN queue_order INTEGER")
        db.execute("UPDATE tokens SET queue_order = sequence_number")

    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_tokens_queue_order "
        "ON tokens(service_id, queue_order)"
    )

    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_tokens_student ON tokens(student_id)"
    )

    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)