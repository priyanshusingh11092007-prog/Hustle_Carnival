from datetime import datetime, timezone

from .db import get_db


def average_service_seconds(service_id, db=None):
    db = db or get_db()

    rows = db.execute(
        """
        SELECT serving_at, completed_at
        FROM tokens
        WHERE service_id = ?
          AND status = 'COMPLETED'
          AND serving_at IS NOT NULL
          AND completed_at IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT 20
        """,
        (service_id,)
    ).fetchall()

    durations = []

    for row in rows:
        started = datetime.fromisoformat(
            row["serving_at"]
        )

        completed = datetime.fromisoformat(
            row["completed_at"]
        )

        seconds = (
            completed - started
        ).total_seconds()

        if seconds > 0:
            durations.append(seconds)

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

    if not durations:
        return (
            service["default_service_seconds"],
            "default"
        )

    return (
        sum(durations) / len(durations),
        "recent average"
    )


def estimate_new_token(db, service):
    average, _ = average_service_seconds(
        service["id"],
        db
    )

    waiting = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM tokens
        WHERE service_id = ?
          AND status = 'WAITING'
        """,
        (service["id"],)
    ).fetchone()["total"]

    active = db.execute(
        """
        SELECT *
        FROM tokens
        WHERE service_id = ?
          AND status IN (
              'CALLED',
              'SERVING'
          )
        LIMIT 1
        """,
        (service["id"],)
    ).fetchone()

    remaining = remaining_service_seconds(
        active,
        average
    )

    return round(
        waiting * average + remaining
    )


def remaining_service_seconds(token, average):
    if not token:
        return 0

    if token["status"] != "SERVING":
        return average

    if not token["serving_at"]:
        return average

    started = datetime.fromisoformat(
        token["serving_at"]
    )

    elapsed = (
        datetime.now(timezone.utc) - started
    ).total_seconds()

    return max(
        0,
        average - elapsed
    )


def get_queue_estimate(token):
    db = get_db()

    status = token["status"]

    if status in (
        "COMPLETED",
        "CANCELLED",
        "NO_SHOW"
    ):
        return {
            "people_ahead": 0,
            "estimated_minutes": 0,
            "estimate_source": "not applicable"
        }

    if status in ("CALLED", "SERVING"):
        return {
            "people_ahead": 0,
            "estimated_minutes": 0,
            "estimate_source": "turn reached"
        }

    average, source = average_service_seconds(
        token["service_id"],
        db
    )

    ahead = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM tokens
        WHERE service_id = ?
          AND queue_order < ?
          AND status = 'WAITING'
        """,
        (
            token["service_id"],
            token["queue_order"]
        )
    ).fetchone()["total"]

    active = db.execute(
        """
        SELECT *
        FROM tokens
        WHERE service_id = ?
          AND status IN (
              'CALLED',
              'SERVING'
          )
        LIMIT 1
        """,
        (token["service_id"],)
    ).fetchone()

    remaining = remaining_service_seconds(
        active,
        average
    )

    if status == "HOLD":
        return {
            "people_ahead": ahead,
            "estimated_minutes": None,
            "estimate_source": "paused"
        }

    estimated_seconds = (
        ahead * average + remaining
    )

    return {
        "people_ahead": ahead,
        "estimated_minutes": round(
            estimated_seconds / 60,
            1
        ),
        "estimate_source": source
    }