import pytest
import json
from app import create_app, db
from app.models import Account

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_check(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_create_account(client):
    account_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123-456-7890'
    }
    response = client.post('/api/v1/accounts', 
                          json=account_data,
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'John Doe'
    assert data['email'] == 'john@example.com'

def test_get_account(client):
    # First create an account
    account_data = {'name': 'Jane Doe', 'email': 'jane@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Then get it
    response = client.get(f'/api/v1/accounts/{account_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Jane Doe'

def test_list_accounts(client):
    response = client.get('/api/v1/accounts')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_update_account(client):
    # Create account
    account_data = {'name': 'Bob Smith', 'email': 'bob@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Update account
    update_data = {'name': 'Robert Smith', 'phone': '555-0123'}
    response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Robert Smith'
    assert data['phone'] == '555-0123'

def test_delete_account(client):
    # Create account
    account_data = {'name': 'Alice Brown', 'email': 'alice@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Delete account
    response = client.delete(f'/api/v1/accounts/{account_id}')
    assert response.status_code == 200
    
    # Verify deletion
    get_response = client.get(f'/api/v1/accounts/{account_id}')
    assert get_response.status_code == 404