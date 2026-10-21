import pytest

from queuesathi.queue_logic import (
    create_token,
    get_token,
    change_status
)


def test_invalid_transition(app):
    with app.app_context():
        public_id = create_token(1)

        token = get_token(public_id)

        with pytest.raises(ValueError):
            change_status(token["id"], "COMPLETED")
