import os
import sys

from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))

from queuesathi import create_app
from queuesathi.db import get_db, init_db


def seed():
    app = create_app()

    with app.app_context():
        init_db()

        db = get_db()

        services = [
            ("Administrative Help Desk", "ADM"),
            ("Library Support", "LIB"),
            ("Fee Counter", "FEE"),
            ("Campus Canteen", "CAN")
        ]

        for name, code in services:
            db.execute(
                '''
                INSERT INTO services (
                    service_name,
                    service_code
                )
                VALUES (?, ?)
                ON CONFLICT DO NOTHING
                ''',
                (name, code)
            )

        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")

        if not username or not password:
            raise RuntimeError(
                "Set ADMIN_USERNAME and ADMIN_PASSWORD in .env."
            )

        if len(password) < 12:
            raise RuntimeError(
                "ADMIN_PASSWORD must contain at least 12 characters."
            )

        existing = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not existing:
            db.execute(
                '''
                INSERT INTO users (
                    username,
                    password_hash,
                    role
                )
                VALUES (?, ?, 'ADMIN')
                ''',
                (
                    username,
                    generate_password_hash(password)
                )
            )

        db.commit()

        print("Demo services created.")
        print("Admin account ready.")
        print(f"Admin username: {username}")
        print("Password: the value configured in your .env file")


if __name__ == "__main__":
    seed()
