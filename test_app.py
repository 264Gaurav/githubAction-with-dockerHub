import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    with flask_app.test_client() as client:
        yield client


def test_index_returns_hello_world(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello, World!"}


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
