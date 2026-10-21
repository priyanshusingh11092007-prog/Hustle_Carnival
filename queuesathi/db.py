import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        db = sqlite3.connect(
            current_app.config["DATABASE"],
            timeout=15
        )

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
    columns = db.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return any(row["name"] == column for row in columns)


def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as file:
        schema = file.read().decode("utf-8")

    db.executescript(schema)

    # Upgrade databases created by the previous QueueSathi version.

    if not column_exists(db, "users", "service_id"):
        db.execute(
            """
            ALTER TABLE users
            ADD COLUMN service_id INTEGER REFERENCES services(id)
            """
        )

    if not column_exists(db, "tokens", "student_id"):
        db.execute(
            """
            ALTER TABLE tokens
            ADD COLUMN student_id INTEGER REFERENCES students(id)
            """
        )

    if not column_exists(db, "tokens", "queue_order"):
        db.execute(
            """
            ALTER TABLE tokens
            ADD COLUMN queue_order INTEGER
            """
        )

        db.execute(
            """
            UPDATE tokens
            SET queue_order = sequence_number
            """
        )

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tokens_queue_order
        ON tokens(service_id, queue_order)
        """
    )

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tokens_student
        ON tokens(student_id)
        """
    )

    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)