from queuesathi.db import get_db
from queuesathi.queue_logic import create_token


def test_unique_tokens(app):
    with app.app_context():
        first = create_token(1)
        second = create_token(1)

        assert first != second

        rows = get_db().execute(
            "SELECT token_number FROM tokens ORDER BY id"
        ).fetchall()

        assert rows[0]["token_number"] == "TST-0001"
        assert rows[1]["token_number"] == "TST-0002"
