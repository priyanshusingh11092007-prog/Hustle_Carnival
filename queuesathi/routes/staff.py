from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    g,
    abort,
    jsonify
)

from ..auth import role_required

from ..db import get_db

from ..queue_logic import (
    call_next,
    change_status,
    create_token,
    skip_token
)


staff_bp = Blueprint(
    "staff",
    __name__
)


def assigned_service_id():
    if g.user["role"] == "ADMIN":
        return None

    return g.user["service_id"]


def dashboard_data():
    db = get_db()

    service_id = assigned_service_id()

    if service_id is None:
        services = db.execute(
            """
            SELECT *
            FROM services
            ORDER BY service_name
            """
        ).fetchall()

        tokens = db.execute(
            """
            SELECT
                tokens.*,
                services.service_name
            FROM tokens
            JOIN services
                ON services.id = tokens.service_id
            WHERE tokens.status IN (
                'WAITING',
                'CALLED',
                'SERVING',
                'HOLD'
            )
            ORDER BY
                tokens.service_id,
                tokens.queue_order,
                tokens.id
            """
        ).fetchall()

    else:
        services = db.execute(
            """
            SELECT *
            FROM services
            WHERE id = ?
            """,
            (service_id,)
        ).fetchall()

        tokens = db.execute(
            """
            SELECT
                tokens.*,
                services.service_name
            FROM tokens
            JOIN services
                ON services.id = tokens.service_id
            WHERE tokens.service_id = ?
              AND tokens.status IN (
                  'WAITING',
                  'CALLED',
                  'SERVING',
                  'HOLD'
              )
            ORDER BY
                tokens.queue_order,
                tokens.id
            """,
            (service_id,)
        ).fetchall()

    return services, tokens


def verify_service_access(service_id):
    if g.user["role"] == "ADMIN":
        return

    if g.user["service_id"] != service_id:
        abort(403)


def verify_token_access(token_id):
    token = get_db().execute(
        """
        SELECT *
        FROM tokens
        WHERE id = ?
        """,
        (token_id,)
    ).fetchone()

    if not token:
        abort(404)

    verify_service_access(
        token["service_id"]
    )

    return token


@staff_bp.get("/staff")
@role_required("STAFF", "ADMIN")
def dashboard():
    services, tokens = dashboard_data()

    return render_template(
        "staff/dashboard.html",
        services=services,
        tokens=tokens
    )


@staff_bp.get("/staff/api/queue")
@role_required("STAFF", "ADMIN")
def queue_api():
    _, tokens = dashboard_data()

    return jsonify({
        "tokens": [
            {
                "id": token["id"],
                "token_number": token["token_number"],
                "service_name": token["service_name"],
                "status": token["status"],
                "queue_order": token["queue_order"]
            }
            for token in tokens
        ]
    })


@staff_bp.post("/staff/call-next")
@role_required("STAFF", "ADMIN")
def call_next_route():
    service_id = request.form.get(
        "service_id",
        type=int
    )

    if not service_id:
        flash(
            "Select a service.",
            "error"
        )

        return redirect(
            url_for("staff.dashboard")
        )

    verify_service_access(service_id)

    try:
        call_next(
            service_id,
            g.user["id"]
        )

        flash(
            "Next token called.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(
        url_for("staff.dashboard")
    )


@staff_bp.post("/staff/token/<int:token_id>/<action>")
@role_required("STAFF", "ADMIN")
def token_action(token_id, action):
    verify_token_access(token_id)

    actions = {
        "serve": "SERVING",
        "complete": "COMPLETED",
        "hold": "HOLD",
        "resume": "WAITING",
        "cancel": "CANCELLED",
        "no-show": "NO_SHOW"
    }

    if action not in actions:
        abort(404)

    try:
        change_status(
            token_id,
            actions[action],
            g.user["id"]
        )

        flash(
            "Token updated successfully.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(
        url_for("staff.dashboard")
    )


@staff_bp.post("/staff/token/<int:token_id>/skip")
@role_required("STAFF", "ADMIN")
def skip_token_route(token_id):
    verify_token_access(token_id)

    try:
        skip_token(
            token_id,
            g.user["id"]
        )

        flash(
            "Token skipped and moved behind "
            "the next two waiting tokens.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(
        url_for("staff.dashboard")
    )


@staff_bp.post("/staff/walk-in")
@role_required("STAFF", "ADMIN")
def walk_in():
    service_id = request.form.get(
        "service_id",
        type=int
    )

    if not service_id:
        flash(
            "Select a service.",
            "error"
        )

        return redirect(
            url_for("staff.dashboard")
        )

    verify_service_access(service_id)

    try:
        create_token(
            service_id,
            source="WALK_IN"
        )

        flash(
            "Walk-in token created.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(
        url_for("staff.dashboard")
    )