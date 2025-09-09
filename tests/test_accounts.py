import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Fix for Werkzeug version issue in GitHub Actions
import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '2.3.7'

# Import from your single app.py file directly
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the single app.py module (not the app package)
import importlib.util
app_py_path = os.path.join(os.path.dirname(__file__), '..', 'app.py')
spec = importlib.util.spec_from_file_location("app_module", app_py_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

@pytest.fixture
def client():
    app_module.app.config['TESTING'] = True
    app_module.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app_module.app.test_client() as client:
        with app_module.app.app_context():
            app_module.db.create_all()
            yield client
            app_module.db.drop_all()

# EXISTING TESTS
def test_health_check(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'account-management-api'
    # Database connection should also be tested
    assert 'database' in data

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

# NEW TESTS TO INCREASE COVERAGE

# Test home route
def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Account Management API is running!"
    assert data['status'] == "ok"

# Test health check database error
@patch('app_module.db.session.execute')
def test_health_check_database_error(mock_execute, client):
    mock_execute.side_effect = Exception("Database connection failed")
    response = client.get('/api/v1/health')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['status'] == 'unhealthy'
    assert 'error' in data

# Test create account validation errors
def test_create_account_missing_name(client):
    account_data = {'email': 'test@example.com'}
    response = client.post('/api/v1/accounts', json=account_data)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Name and email are required' in data['error']

def test_create_account_missing_email(client):
    account_data = {'name': 'Test User'}
    response = client.post('/api/v1/accounts', json=account_data)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Name and email are required' in data['error']

def test_create_account_no_data(client):
    response = client.post('/api/v1/accounts', json=None)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Name and email are required' in data['error']

def test_create_account_empty_data(client):
    response = client.post('/api/v1/accounts', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Name and email are required' in data['error']

def test_create_account_duplicate_email(client):
    account_data = {'name': 'User One', 'email': 'duplicate@example.com'}
    # Create first account
    client.post('/api/v1/accounts', json=account_data)
    
    # Try to create second account with same email
    account_data2 = {'name': 'User Two', 'email': 'duplicate@example.com'}
    response = client.post('/api/v1/accounts', json=account_data2)
    assert response.status_code == 409
    data = json.loads(response.data)
    assert 'Email already exists' in data['error']

# Test create account with only required fields
def test_create_account_minimal_data(client):
    account_data = {'name': 'Minimal User', 'email': 'minimal@example.com'}
    response = client.post('/api/v1/accounts', json=account_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Minimal User'
    assert data['email'] == 'minimal@example.com'
    assert data['phone'] is None

# Test get account not found
def test_get_account_not_found(client):
    response = client.get('/api/v1/accounts/999')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'Account not found' in data['error']

# Test update account not found
def test_update_account_not_found(client):
    update_data = {'name': 'Updated Name'}
    response = client.put('/api/v1/accounts/999', json=update_data)
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'Account not found' in data['error']

def test_update_account_no_data(client):
    # Create account first
    account_data = {'name': 'Test User', 'email': 'test@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Try to update with no data
    response = client.put(f'/api/v1/accounts/{account_id}', json=None)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'No data provided' in data['error']

def test_update_account_empty_data(client):
    # Create account first
    account_data = {'name': 'Test User', 'email': 'test@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Try to update with empty data
    response = client.put(f'/api/v1/accounts/{account_id}', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'No data provided' in data['error']

# Test delete account not found
def test_delete_account_not_found(client):
    response = client.delete('/api/v1/accounts/999')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'Account not found' in data['error']

# Test list accounts with data
def test_list_accounts_with_data(client):
    # Create multiple accounts
    accounts_data = [
        {'name': 'User 1', 'email': 'user1@example.com'},
        {'name': 'User 2', 'email': 'user2@example.com', 'phone': '555-0001'},
        {'name': 'User 3', 'email': 'user3@example.com', 'phone': '555-0002'}
    ]
    
    for account_data in accounts_data:
        client.post('/api/v1/accounts', json=account_data)
    
    response = client.get('/api/v1/accounts')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3
    assert all('name' in account for account in data)
    assert all('email' in account for account in data)

# Test Account model methods
def test_account_to_dict():
    with app_module.app.app_context():
        account = app_module.Account(
            name='Test User',
            email='test@example.com',
            phone='555-0123'
        )
        account.id = 1
        
        result = account.to_dict()
        assert result['id'] == 1
        assert result['name'] == 'Test User'
        assert result['email'] == 'test@example.com'
        assert result['phone'] == '555-0123'
        assert 'date_joined' in result

def test_account_to_dict_no_date():
    with app_module.app.app_context():
        account = app_module.Account(
            name='Test User',
            email='test@example.com'
        )
        account.id = 1
        account.date_joined = None
        
        result = account.to_dict()
        assert result['date_joined'] is None

def test_account_from_dict():
    with app_module.app.app_context():
        account = app_module.Account()
        data = {
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'phone': '555-9999',
            'extra_field': 'ignored'  # This should be ignored
        }
        
        account.from_dict(data)
        assert account.name == 'Updated Name'
        assert account.email == 'updated@example.com'
        assert account.phone == '555-9999'
        assert not hasattr(account, 'extra_field')

def test_account_from_dict_partial():
    with app_module.app.app_context():
        account = app_module.Account()
        account.name = 'Original Name'
        account.email = 'original@example.com'
        
        # Update only phone
        data = {'phone': '555-1111'}
        account.from_dict(data)
        
        assert account.name == 'Original Name'  # Unchanged
        assert account.email == 'original@example.com'  # Unchanged
        assert account.phone == '555-1111'  # Updated

# Test database error scenarios
@patch('app_module.db.session.commit')
def test_create_account_database_error(mock_commit, client):
    mock_commit.side_effect = Exception("Database error")
    
    account_data = {'name': 'Test User', 'email': 'test@example.com'}
    response = client.post('/api/v1/accounts', json=account_data)
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data

@patch('app_module.db.session.get')
def test_get_account_database_error(mock_get, client):
    mock_get.side_effect = Exception("Database error")
    
    response = client.get('/api/v1/accounts/1')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data

@patch('app_module.Account.query')
def test_list_accounts_database_error(mock_query, client):
    mock_query.all.side_effect = Exception("Database error")
    
    response = client.get('/api/v1/accounts')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data

@patch('app_module.db.session.commit')
def test_update_account_database_error(mock_commit, client):
    # Create account first
    account_data = {'name': 'Test User', 'email': 'test@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Mock database error on update
    mock_commit.side_effect = Exception("Database error")
    
    update_data = {'name': 'Updated Name'}
    response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data

@patch('app_module.db.session.commit')
def test_delete_account_database_error(mock_commit, client):
    # Create account first
    account_data = {'name': 'Test User', 'email': 'test@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Mock database error on delete
    mock_commit.side_effect = Exception("Database error")
    
    response = client.delete(f'/api/v1/accounts/{account_id}')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data

# Test app initialization functions
def test_init_db_success():
    with patch('app_module.db.create_all') as mock_create:
        mock_create.return_value = None
        result = app_module.init_db()
        assert result is True

def test_init_db_failure():
    with patch('app_module.db.create_all') as mock_create:
        mock_create.side_effect = Exception("Database initialization failed")
        result = app_module.init_db()
        assert result is False

def test_create_app_success():
    with patch('app_module.init_db') as mock_init:
        mock_init.return_value = True
        result = app_module.create_app()
        assert result is not None

def test_create_app_failure():
    with patch('app_module.init_db') as mock_init:
        mock_init.return_value = False
        with pytest.raises(Exception, match="Database initialization failed"):
            app_module.create_app()

# Test update with all fields
def test_update_account_all_fields(client):
    # Create account
    account_data = {'name': 'Original Name', 'email': 'original@example.com'}
    create_response = client.post('/api/v1/accounts', json=account_data)
    account_id = json.loads(create_response.data)['id']
    
    # Update all fields
    update_data = {
        'name': 'Updated Name',
        'email': 'updated@example.com',
        'phone': '555-9999'
    }
    response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Updated Name'
    assert data['email'] == 'updated@example.com'
    assert data['phone'] == '555-9999'

# Test create account with all fields including date verification
def test_create_account_with_date_verification(client):
    account_data = {
        'name': 'Date Test User',
        'email': 'datetest@example.com',
        'phone': '555-0000'
    }
    response = client.post('/api/v1/accounts', json=account_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'date_joined' in data
    assert data['date_joined'] is not None
    # Verify ISO format
    from datetime import datetime
    datetime.fromisoformat(data['date_joined'].replace('Z', '+00:00'))  # Should not raise error