from queuesathi.queue_logic import (
    create_token,
    get_token
)

from queuesathi.estimates import get_queue_estimate


def test_people_ahead(app):
    with app.app_context():
        create_token(1)

        second_id = create_token(1)

        token = get_token(second_id)

        estimate = get_queue_estimate(token)

        assert estimate["people_ahead"] == 1
