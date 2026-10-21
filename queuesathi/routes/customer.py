from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
    g
)

from ..auth import student_required

from ..db import get_db

from ..queue_logic import (
    create_token,
    get_token,
    change_status
)

from ..estimates import get_queue_estimate


customer_bp = Blueprint(
    "customer",
    __name__
)


@customer_bp.get("/")
def index():
    if g.user:
        if g.user["role"] == "ADMIN":
            return redirect(
                url_for("admin.services")
            )

        return redirect(
            url_for("staff.dashboard")
        )

    if g.student:
        return redirect(
            url_for("customer.dashboard")
        )

    return redirect(
        url_for("auth.student_login")
    )


@customer_bp.get("/student/dashboard")
@student_required
def dashboard():
    db = get_db()

    services = db.execute(
        """
        SELECT *
        FROM services
        WHERE is_open = 1
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
        WHERE tokens.student_id = ?
        ORDER BY tokens.created_at DESC
        """,
        (g.student["id"],)
    ).fetchall()

    active_tokens = []
    history = []

    for token in tokens:
        if token["status"] in (
            "WAITING",
            "CALLED",
            "SERVING",
            "HOLD"
        ):
            active_tokens.append({
                "token": token,
                "estimate": get_queue_estimate(token)
            })
        else:
            history.append(token)

    return render_template(
        "customer/dashboard.html",
        services=services,
        active_tokens=active_tokens,
        history=history
    )


@customer_bp.get("/services")
@student_required
def services():
    rows = get_db().execute(
        """
        SELECT *
        FROM services
        WHERE is_open = 1
        ORDER BY service_name
        """
    ).fetchall()

    return render_template(
        "customer/index.html",
        services=rows
    )


@customer_bp.post("/join")
@student_required
def join_queue():
    service_id = request.form.get(
        "service_id",
        type=int
    )

    if not service_id:
        flash(
            "Please select a service.",
            "error"
        )

        return redirect(
            url_for("customer.dashboard")
        )

    try:
        public_id = create_token(
            service_id,
            student_id=g.student["id"]
        )

        flash(
            "Your token has been generated.",
            "success"
        )

        return redirect(
            url_for("customer.token_status",
                    public_id=public_id)
        )

    except ValueError as error:
        flash(str(error), "error")

        return redirect(
            url_for("customer.dashboard")
        )


def owned_token(public_id):
    token = get_token(public_id)

    if not token:
        abort(404)

    if token["student_id"] != g.student["id"]:
        abort(403)

    return token


@customer_bp.get("/token/<public_id>")
@student_required
def token_status(public_id):
    token = owned_token(public_id)

    estimate = get_queue_estimate(token)

    return render_template(
        "customer/token.html",
        token=token,
        estimate=estimate
    )


@customer_bp.get("/api/token/<public_id>")
@student_required
def token_api(public_id):
    token = owned_token(public_id)

    estimate = get_queue_estimate(token)

    return jsonify({
        "token_number": token["token_number"],
        "status": token["status"],
        "people_ahead": estimate["people_ahead"],
        "estimated_minutes": estimate["estimated_minutes"],
        "estimate_source": estimate["estimate_source"],
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat()
    })


@customer_bp.post("/token/<public_id>/cancel")
@student_required
def cancel_token(public_id):
    token = owned_token(public_id)

    try:
        change_status(
            token["id"],
            "CANCELLED"
        )

        flash(
            "Token cancelled successfully.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(
        url_for("customer.dashboard")
    )