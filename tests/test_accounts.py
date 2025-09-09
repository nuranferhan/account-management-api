import pytest
import json
import sys
import os

# Fix for Werkzeug version issue in GitHub Actions
import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '2.3.7'

# Change working directory to parent to find app.py
original_cwd = os.getcwd()
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(parent_dir)
sys.path.insert(0, parent_dir)

try:
    # Now import app.py directly
    import app as app_module
finally:
    # Restore original working directory
    os.chdir(original_cwd)

@pytest.fixture
def client():
    app_module.app.config['TESTING'] = True
    app_module.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app_module.app.test_client() as client:
        with app_module.app.app_context():
            app_module.db.create_all()
            yield client
            app_module.db.drop_all()

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