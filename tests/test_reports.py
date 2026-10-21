from queuesathi.reports import get_statistics


def test_empty_reports(app):
    with app.app_context():
        result = get_statistics()

        assert result["total_tokens"] == 0
        assert result["total_served"] == 0
