import sys
from pathlib import Path

import click

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))


from queuesathi import create_app
from queuesathi.db import get_db


def main():
    app = create_app()

    with app.app_context():
        db = get_db()

        services = db.execute(
            """
            SELECT *
            FROM services
            ORDER BY service_name
            """
        ).fetchall()

        print("\nAvailable Services:\n")

        for service in services:
            print(
                f"{service['service_code']} - "
                f"{service['service_name']} "
            
            )

        print()

        code = input(
            "Enter service code: "
        ).strip().upper()

        service = db.execute(
            """
            SELECT *
            FROM services
            WHERE service_code = ?
            """,
            (code,)
        ).fetchone()

        if not service:
            print("Invalid service code.")
            return

        username = input(
            "Staff username: "
        ).strip()

        password = click.prompt(
            "Staff password",
            hide_input=False,
            confirmation_prompt=True
        )

        if len(password) < 12:
            print(
                "Password must contain at least 12 characters."
            )
            return

        existing = db.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if existing:
            print("Username already exists.")
            return

        db.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                role,
                active,
                service_id
            )
            VALUES (?, ?, 'STAFF', 1, ?)
            """,
            (
                username,
                generate_password_hash(password),
                service["id"]
            )
        )

        db.commit()

        print()
        print("Staff account created.")
        print("Username:", username)
        print("Department:", service["service_name"])


if __name__ == "__main__":
    main()