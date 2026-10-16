import pytest
import sqlite3
import bcrypt
from app import app, DATABASE, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

@pytest.fixture
def cleanup():
    yield
    import os
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

def test_register_user(client, cleanup):
    response = client.post('/register', 
                          json={'username': 'testuser', 'password': 'testpass'},
                          content_type='application/json')
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'User registered successfully'

def test_register_duplicate_user(client, cleanup):
    client.post('/register', 
               json={'username': 'testuser', 'password': 'testpass'},
               content_type='application/json')
    response = client.post('/register', 
                          json={'username': 'testuser', 'password': 'testpass'},
                          content_type='application/json')
    assert response.status_code == 409
    data = response.get_json()
    assert data['error'] == 'Username already exists'

def test_register_missing_fields(client, cleanup):
    response = client.post('/register', 
                          json={'username': 'testuser'},
                          content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Username and password are required'

def test_login_valid_user(client, cleanup):
    client.post('/register', 
               json={'username': 'testuser', 'password': 'testpass'},
               content_type='application/json')
    response = client.post('/login', 
                          json={'username': 'testuser', 'password': 'testpass'},
                          content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Login successful'
    assert data['username'] == 'testuser'

def test_login_invalid_user(client, cleanup):
    response = client.post('/login', 
                          json={'username': 'nonexistent', 'password': 'testpass'},
                          content_type='application/json')
    assert response.status_code == 401
    data = response.get_json()
    assert data['error'] == 'Invalid username or password'

def test_login_wrong_password(client, cleanup):
    client.post('/register', 
               json={'username': 'testuser', 'password': 'testpass'},
               content_type='application/json')
    response = client.post('/login', 
                          json={'username': 'testuser', 'password': 'wrongpass'},
                          content_type='application/json')
    assert response.status_code == 401
    data = response.get_json()
    assert data['error'] == 'Invalid username or password'

def test_login_missing_fields(client, cleanup):
    response = client.post('/login', 
                          json={'username': 'testuser'},
                          content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Username and password are required'

def test_database_creation(client, cleanup):
    with app.app_context():
        init_db()
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        conn.close()
        assert table_exists is not None

def test_logout_success(client, cleanup):
    client.post('/register', 
               json={'username': 'testuser', 'password': 'testpass'},
               content_type='application/json')
    client.post('/login', 
               json={'username': 'testuser', 'password': 'testpass'},
               content_type='application/json')
    response = client.post('/logout', content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Logged out successfully'

def test_logout_without_login(client, cleanup):
    response = client.post('/logout', content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Logged out successfully'
