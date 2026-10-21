import uuid

from datetime import datetime, timezone

from .db import get_db


ALLOWED_TRANSITIONS = {
    "WAITING": {"CALLED", "CANCELLED"},
    "CALLED": {
        "SERVING",
        "NO_SHOW",
        "CANCELLED"
    },
    "SERVING": {"COMPLETED", "HOLD"},
    "HOLD": {
        "WAITING",
        "CALLED",
        "CANCELLED"
    },
    "COMPLETED": set(),
    "CANCELLED": set(),
    "NO_SHOW": set()
}


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def get_token(public_id):
    return get_db().execute(
        """
        SELECT
            tokens.*,
            services.service_name
        FROM tokens
        JOIN services
            ON services.id = tokens.service_id
        WHERE tokens.public_id = ?
        """,
        (public_id,)
    ).fetchone()


def create_token(
    service_id,
    student_id=None,
    source="DIGITAL"
):
    if source not in ("DIGITAL", "WALK_IN"):
        raise ValueError("Invalid token source.")

    if source == "DIGITAL" and student_id is None:
        raise ValueError(
            "Student login is required."
        )

    db = get_db()

    db.execute("BEGIN IMMEDIATE")

    try:
        service = db.execute(
            """
            SELECT *
            FROM services
            WHERE id = ?
            """,
            (service_id,)
        ).fetchone()

        if not service:
            raise ValueError(
                "Service not found."
            )

        if not service["is_open"]:
            raise ValueError(
                "Service is currently closed."
            )

        if student_id:
            existing = db.execute(
                """
                SELECT id
                FROM tokens
                WHERE student_id = ?
                  AND service_id = ?
                  AND status IN (
                      'WAITING',
                      'CALLED',
                      'SERVING',
                      'HOLD'
                  )
                LIMIT 1
                """,
                (student_id, service_id)
            ).fetchone()

            if existing:
                raise ValueError(
                    "You already have an active token "
                    "for this service."
                )

        sequence = db.execute(
            """
            SELECT COALESCE(
                MAX(sequence_number), 0
            ) + 1 AS next_number
            FROM tokens
            WHERE service_id = ?
            """,
            (service_id,)
        ).fetchone()["next_number"]

        queue_order = db.execute(
            """
            SELECT COALESCE(
                MAX(queue_order), 0
            ) + 1 AS next_order
            FROM tokens
            WHERE service_id = ?
            """,
            (service_id,)
        ).fetchone()["next_order"]

        token_number = (
            f"{service['service_code']}-{sequence:04d}"
        )

        public_id = str(uuid.uuid4())

        from .estimates import estimate_new_token

        estimated_seconds = estimate_new_token(
            db,
            service
        )

        db.execute(
            """
            INSERT INTO tokens (
                public_id,
                token_number,
                sequence_number,
                queue_order,
                service_id,
                student_id,
                status,
                source,
                created_at,
                estimated_wait_seconds
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                'WAITING', ?, ?, ?
            )
            """,
            (
                public_id,
                token_number,
                sequence,
                queue_order,
                service_id,
                student_id,
                source,
                utc_now(),
                estimated_seconds
            )
        )

        db.commit()

        return public_id

    except Exception:
        db.rollback()
        raise


def change_status(
    token_id,
    new_status,
    actor_id=None
):
    db = get_db()

    db.execute("BEGIN IMMEDIATE")

    try:
        token = db.execute(
            """
            SELECT *
            FROM tokens
            WHERE id = ?
            """,
            (token_id,)
        ).fetchone()

        if not token:
            raise ValueError(
                "Token not found."
            )

        old_status = token["status"]

        if new_status not in ALLOWED_TRANSITIONS.get(
            old_status,
            set()
        ):
            raise ValueError(
                f"Cannot change {old_status} "
                f"to {new_status}."
            )

        if new_status in ("CALLED", "SERVING"):
            occupied = db.execute(
                """
                SELECT id
                FROM tokens
                WHERE service_id = ?
                  AND id != ?
                  AND status IN (
                      'CALLED',
                      'SERVING'
                  )
                LIMIT 1
                """,
                (
                    token["service_id"],
                    token_id
                )
            ).fetchone()

            if occupied:
                raise ValueError(
                    "Another token is currently active."
                )

        timestamp = utc_now()

        fields = {
            "CALLED": "called_at",
            "SERVING": "serving_at",
            "COMPLETED": "completed_at",
            "CANCELLED": "cancelled_at",
            "NO_SHOW": "cancelled_at"
        }

        field = fields.get(new_status)

        if field:
            db.execute(
                f"""
                UPDATE tokens
                SET status = ?,
                    {field} = ?
                WHERE id = ?
                """,
                (
                    new_status,
                    timestamp,
                    token_id
                )
            )

        else:
            db.execute(
                """
                UPDATE tokens
                SET status = ?
                WHERE id = ?
                """,
                (
                    new_status,
                    token_id
                )
            )

        db.execute(
            """
            INSERT INTO audit_events (
                token_id,
                actor_id,
                action,
                previous_status,
                new_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_id,
                actor_id,
                new_status,
                old_status,
                new_status,
                timestamp
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise


def call_next(service_id, actor_id):
    db = get_db()

    db.execute("BEGIN IMMEDIATE")

    try:
        occupied = db.execute(
            """
            SELECT id
            FROM tokens
            WHERE service_id = ?
              AND status IN (
                  'CALLED',
                  'SERVING'
              )
            LIMIT 1
            """,
            (service_id,)
        ).fetchone()

        if occupied:
            raise ValueError(
                "Resolve the current token first."
            )

        token = db.execute(
            """
            SELECT *
            FROM tokens
            WHERE service_id = ?
              AND status = 'WAITING'
            ORDER BY queue_order, id
            LIMIT 1
            """,
            (service_id,)
        ).fetchone()

        if not token:
            raise ValueError(
                "No waiting tokens."
            )

        timestamp = utc_now()

        db.execute(
            """
            UPDATE tokens
            SET status = 'CALLED',
                called_at = ?
            WHERE id = ?
            """,
            (
                timestamp,
                token["id"]
            )
        )

        db.execute(
            """
            INSERT INTO audit_events (
                token_id,
                actor_id,
                action,
                previous_status,
                new_status,
                created_at
            )
            VALUES (
                ?, ?, 'CALLED',
                'WAITING', 'CALLED', ?
            )
            """,
            (
                token["id"],
                actor_id,
                timestamp
            )
        )

        db.commit()

        return token["id"]

    except Exception:
        db.rollback()
        raise


def skip_token(token_id, actor_id):
    """
    Move a CALLED token behind the next two
    WAITING tokens in the same service.
    """

    db = get_db()

    db.execute("BEGIN IMMEDIATE")

    try:
        token = db.execute(
            """
            SELECT *
            FROM tokens
            WHERE id = ?
            """,
            (token_id,)
        ).fetchone()

        if not token:
            raise ValueError(
                "Token not found."
            )

        if token["status"] != "CALLED":
            raise ValueError(
                "Only a CALLED token can be skipped."
            )

        waiting_tokens = db.execute(
            """
            SELECT *
            FROM tokens
            WHERE service_id = ?
              AND status = 'WAITING'
            ORDER BY queue_order, id
            """,
            (token["service_id"],)
        ).fetchall()

        waiting_ids = [
            row["id"]
            for row in waiting_tokens
        ]

        # Put the skipped token after two waiting tokens.
        insert_position = min(
            2,
            len(waiting_ids)
        )

        waiting_ids.insert(
            insert_position,
            token_id
        )

        # Allocate fresh order numbers above every existing
        # queue_order value, avoiding uniqueness conflicts.
        maximum = db.execute(
            """
            SELECT COALESCE(MAX(queue_order), 0)
            AS maximum
            FROM tokens
            WHERE service_id = ?
            """,
            (token["service_id"],)
        ).fetchone()["maximum"]

        for position, current_id in enumerate(
            waiting_ids,
            start=1
        ):
            db.execute(
                """
                UPDATE tokens
                SET queue_order = ?
                WHERE id = ?
                """,
                (
                    maximum + position,
                    current_id
                )
            )

        db.execute(
            """
            UPDATE tokens
            SET status = 'WAITING',
                called_at = NULL
            WHERE id = ?
            """,
            (token_id,)
        )

        db.execute(
            """
            INSERT INTO audit_events (
                token_id,
                actor_id,
                action,
                previous_status,
                new_status,
                created_at
            )
            VALUES (
                ?, ?, 'SKIPPED',
                'CALLED', 'WAITING', ?
            )
            """,
            (
                token_id,
                actor_id,
                utc_now()
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise