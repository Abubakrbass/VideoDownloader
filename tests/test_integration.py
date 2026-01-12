import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_register_and_login(client):
    # Test registration
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    assert response.json['success'] is True

    # Test login
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['username'] == 'testuser'

def test_xss_prevention(client):
    # Test registration with malicious input
    response = client.post('/register', json={
        'username': '<script>alert("xss")</script>',
        'password': 'testpassword',
        'email': 'xss@example.com'
    })
    assert response.status_code == 200
    assert response.json['success'] is True

    # Test login with malicious input
    response = client.post('/login', json={
        'username': '<script>alert("xss")</script>',
        'password': 'testpassword'
    })
    assert response.status_code == 401
    assert response.json['error'] == 'Неверное имя пользователя или пароль'
