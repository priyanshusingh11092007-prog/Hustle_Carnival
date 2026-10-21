import os

from queuesathi import create_app

app = create_app()

if os.getenv("VERCEL") == "1":
    from queuesathi.db import init_db

    with app.app_context():
        init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=app.config["DEBUG"]
    )
