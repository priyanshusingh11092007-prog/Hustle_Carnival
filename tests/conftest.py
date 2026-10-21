import pytest

from queuesathi import create_app

from queuesathi.db import init_db


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "test.sqlite3"

    app = create_app({
        "TESTING": True,
        "DATABASE": str(database),
        "DATABASE_URL": None,      # never run tests against the live database
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        init_db()

        db = __import__(
            "queuesathi.db",
            fromlist=["get_db"]
        ).get_db()

        db.execute(
            '''
            INSERT INTO services (
                service_name,
                service_code
            )
            VALUES ('Test Desk', 'TST')
            '''
        )

        db.commit()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()
