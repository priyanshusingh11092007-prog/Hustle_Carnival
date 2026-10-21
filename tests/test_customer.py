def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200

    assert b"Ellora" in response.data


def test_join_queue(client):
    response = client.post(
        "/join",
        data={"service_id": 1},
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/token/" in response.headers["Location"]
