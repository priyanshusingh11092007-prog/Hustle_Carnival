def test_staff_dashboard_requires_login(client):
    response = client.get("/staff")

    assert response.status_code == 302

    assert "/login" in response.headers["Location"]


def test_staff_actions_require_login(client):
    response = client.post(
        "/staff/call-next",
        data={"service_id": 1}
    )

    assert response.status_code == 302
