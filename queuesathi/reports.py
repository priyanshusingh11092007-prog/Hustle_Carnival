from datetime import datetime

from .db import get_db


def get_statistics():
    db = get_db()

    rows = db.execute(
        '''
        SELECT *
        FROM tokens
        ORDER BY created_at DESC
        '''
    ).fetchall()

    completed = [
        row for row in rows
        if row["status"] == "COMPLETED"
    ]

    service_durations = []
    waiting_durations = []
    prediction_errors = []

    for token in completed:
        if not token["serving_at"] or not token["completed_at"]:
            continue

        created = datetime.fromisoformat(
            token["created_at"]
        )

        started = datetime.fromisoformat(
            token["serving_at"]
        )

        finished = datetime.fromisoformat(
            token["completed_at"]
        )

        wait_minutes = (
            started - created
        ).total_seconds() / 60

        service_minutes = (
            finished - started
        ).total_seconds() / 60

        waiting_durations.append(wait_minutes)
        service_durations.append(service_minutes)

        if token["estimated_wait_seconds"] is not None:
            predicted = token["estimated_wait_seconds"] / 60

            prediction_errors.append(
                abs(predicted - wait_minutes)
            )

    def average(values):
        if not values:
            return 0

        return round(sum(values) / len(values), 2)

    busy_hours = db.execute(
        '''
        SELECT substr(created_at, 12, 2) AS hour,
               COUNT(*) AS total
        FROM tokens
        GROUP BY substr(created_at, 12, 2)
        ORDER BY total DESC
        LIMIT 5
        '''
    ).fetchall()

    return {
        "total_tokens": len(rows),
        "total_served": len(completed),
        "total_waiting": sum(
            token["status"] == "WAITING"
            for token in rows
        ),
        "total_cancelled": sum(
            token["status"] == "CANCELLED"
            for token in rows
        ),
        "average_wait": average(waiting_durations),
        "average_service": average(service_durations),
        "prediction_error": average(prediction_errors),
        "busy_hours": busy_hours
    }
