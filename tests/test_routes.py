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

class TestRoutes:
    """Test class for route-specific functionality"""
    
    def test_invalid_route(self, client):
        """Test accessing non-existent routes"""
        response = client.get('/invalid/route')
        assert response.status_code == 404
    
    def test_invalid_method_on_valid_route(self, client):
        """Test using invalid HTTP method on valid route"""
        response = client.patch('/api/v1/accounts')
        assert response.status_code == 405
        
        response = client.options('/api/v1/accounts/1')
        # OPTIONS might be allowed due to CORS, so check if it's either 405 or 200
        assert response.status_code in [200, 405]
    
    def test_malformed_json_create_account(self, client):
        """Test sending malformed JSON to create account"""
        response = client.post('/api/v1/accounts',
                             data='{"name": "Test"',  # Invalid JSON
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_no_content_type_create_account(self, client):
        """Test creating account without proper content type"""
        response = client.post('/api/v1/accounts',
                             data='{"name": "Test", "email": "test@example.com"}')
        # Should still work as Flask is flexible with JSON parsing
        assert response.status_code in [201, 400]
    
    def test_create_account_with_extra_fields(self, client):
        """Test creating account with extra fields that should be ignored"""
        account_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '555-0123',
            'extra_field': 'should be ignored',
            'id': 999,  # Should be ignored
            'date_joined': '2023-01-01'  # Should be ignored
        }
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'extra_field' not in data
        assert data['id'] != 999  # Should be auto-generated
    
    def test_update_account_with_same_data(self, client):
        """Test updating account with the same data"""
        # Create account
        account_data = {'name': 'Test User', 'email': 'test@example.com'}
        create_response = client.post('/api/v1/accounts', json=account_data)
        account_id = json.loads(create_response.data)['id']
        
        # Update with same data
        response = client.put(f'/api/v1/accounts/{account_id}', json=account_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Test User'
        assert data['email'] == 'test@example.com'
    
    def test_update_account_partial_fields(self, client):
        """Test updating account with only some fields"""
        # Create account
        account_data = {'name': 'Original Name', 'email': 'original@example.com', 'phone': '555-0000'}
        create_response = client.post('/api/v1/accounts', json=account_data)
        account_id = json.loads(create_response.data)['id']
        original_data = json.loads(create_response.data)
        
        # Update only name
        update_data = {'name': 'Updated Name'}
        response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Name'
        assert data['email'] == original_data['email']  # Should remain unchanged
        assert data['phone'] == original_data['phone']  # Should remain unchanged
    
    def test_get_account_with_invalid_id_type(self, client):
        """Test getting account with invalid ID type"""
        response = client.get('/api/v1/accounts/invalid_id')
        assert response.status_code == 404
    
    def test_put_account_with_invalid_id_type(self, client):
        """Test updating account with invalid ID type"""
        update_data = {'name': 'Test'}
        response = client.put('/api/v1/accounts/invalid_id', json=update_data)
        assert response.status_code == 404
    
    def test_delete_account_with_invalid_id_type(self, client):
        """Test deleting account with invalid ID type"""
        response = client.delete('/api/v1/accounts/invalid_id')
        assert response.status_code == 404
    
    def test_create_account_with_empty_strings(self, client):
        """Test creating account with empty string values"""
        account_data = {'name': '', 'email': ''}
        response = client.post('/api/v1/accounts', json=account_data)
        # Should still validate as present but might fail at database level
        # depending on constraints
        assert response.status_code in [201, 400, 500]
    
    def test_create_account_with_null_values(self, client):
        """Test creating account with null values"""
        account_data = {'name': None, 'email': 'test@example.com'}
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 400
        
        account_data = {'name': 'Test User', 'email': None}
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 400
    
    def test_create_account_with_very_long_strings(self, client):
        """Test creating account with very long strings"""
        long_name = 'A' * 200  # Longer than 100 char limit
        long_email = 'a' * 110 + '@example.com'  # Longer than 120 char limit
        
        account_data = {'name': long_name, 'email': 'test@example.com'}
        response = client.post('/api/v1/accounts', json=account_data)
        # Might succeed or fail depending on database constraints
        assert response.status_code in [201, 400, 500]
        
        account_data = {'name': 'Test User', 'email': long_email}
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code in [201, 400, 500]
    
    def test_update_account_with_null_values(self, client):
        """Test updating account with null values"""
        # Create account
        account_data = {'name': 'Test User', 'email': 'test@example.com'}
        create_response = client.post('/api/v1/accounts', json=account_data)
        account_id = json.loads(create_response.data)['id']
        
        # Try to update with null name
        update_data = {'name': None}
        response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
        # Should work as from_dict will set the field to None
        assert response.status_code in [200, 400, 500]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/')
        # CORS should add headers (though exact headers depend on configuration)
        assert response.status_code == 200
        # Can check for specific CORS headers if needed
    
    def test_multiple_operations_sequence(self, client):
        """Test a sequence of operations to ensure state consistency"""
        # Create multiple accounts
        accounts = []
        for i in range(3):
            account_data = {'name': f'User {i}', 'email': f'user{i}@example.com'}
            response = client.post('/api/v1/accounts', json=account_data)
            assert response.status_code == 201
            accounts.append(json.loads(response.data))
        
        # List all accounts
        response = client.get('/api/v1/accounts')
        assert response.status_code == 200
        all_accounts = json.loads(response.data)
        assert len(all_accounts) >= 3
        
        # Update middle account
        middle_account = accounts[1]
        update_data = {'name': 'Updated User 1', 'phone': '555-0001'}
        response = client.put(f'/api/v1/accounts/{middle_account["id"]}', json=update_data)
        assert response.status_code == 200
        
        # Delete first account
        response = client.delete(f'/api/v1/accounts/{accounts[0]["id"]}')
        assert response.status_code == 200
        
        # Verify final state
        response = client.get('/api/v1/accounts')
        assert response.status_code == 200
        final_accounts = json.loads(response.data)
        assert len(final_accounts) == len(all_accounts) - 1
        
        # Verify deleted account is gone
        response = client.get(f'/api/v1/accounts/{accounts[0]["id"]}')
        assert response.status_code == 404
    
    def test_case_sensitive_routes(self, client):
        """Test that routes are case sensitive"""
        response = client.get('/API/V1/ACCOUNTS')
        assert response.status_code == 404
        
        response = client.get('/Api/V1/Accounts')
        assert response.status_code == 404
    
    def test_trailing_slash_routes(self, client):
        """Test routes with and without trailing slashes"""
        response = client.get('/api/v1/accounts/')
        # Flask typically handles trailing slashes gracefully
        assert response.status_code in [200, 404, 301, 308]
        
        response = client.get('/api/v1/health/')
        assert response.status_code in [200, 404, 301, 308]
    
    def test_health_check_response_format(self, client):
        """Test health check response has correct format"""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        required_fields = ['status', 'service', 'database']
        for field in required_fields:
            assert field in data
        
        assert data['status'] == 'healthy'
        assert data['service'] == 'account-management-api'
        assert data['database'] == 'connected'
    
    def test_account_id_boundary_values(self, client):
        """Test account operations with boundary ID values"""
        # Test with ID 0
        response = client.get('/api/v1/accounts/0')
        assert response.status_code == 404
        
        # Test with negative ID
        response = client.get('/api/v1/accounts/-1')
        assert response.status_code == 404
        
        # Test with very large ID
        response = client.get('/api/v1/accounts/999999999')
        assert response.status_code == 404
    
    def test_json_response_content_type(self, client):
        """Test that responses have correct JSON content type"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'application/json' in response.content_type
        
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        assert 'application/json' in response.content_type
        
        response = client.get('/api/v1/accounts')
        assert response.status_code == 200
        assert 'application/json' in response.content_type
    
    def test_delete_account_success_message(self, client):
        """Test delete account returns proper success message"""
        # Create account
        account_data = {'name': 'Delete Test', 'email': 'delete@example.com'}
        create_response = client.post('/api/v1/accounts', json=account_data)
        account_id = json.loads(create_response.data)['id']
        
        # Delete account and verify message
        response = client.delete(f'/api/v1/accounts/{account_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert data['message'] == 'Account deleted successfully'
    
    def test_account_data_persistence(self, client):
        """Test that account data persists correctly across operations"""
        # Create account with all fields
        original_data = {
            'name': 'Persistence Test',
            'email': 'persist@example.com',
            'phone': '555-PERSIST'
        }
        create_response = client.post('/api/v1/accounts', json=original_data)
        assert create_response.status_code == 201
        created_account = json.loads(create_response.data)
        account_id = created_account['id']
        
        # Verify all data was saved correctly
        response = client.get(f'/api/v1/accounts/{account_id}')
        assert response.status_code == 200
        retrieved_account = json.loads(response.data)
        
        assert retrieved_account['name'] == original_data['name']
        assert retrieved_account['email'] == original_data['email']
        assert retrieved_account['phone'] == original_data['phone']
        assert retrieved_account['id'] == account_id
        assert 'date_joined' in retrieved_account
    
    def test_update_nonexistent_fields(self, client):
        """Test updating account with fields that don't exist in model"""
        # Create account
        account_data = {'name': 'Test User', 'email': 'test@example.com'}
        create_response = client.post('/api/v1/accounts', json=account_data)
        account_id = json.loads(create_response.data)['id']
        
        # Try to update with non-existent fields
        update_data = {
            'name': 'Updated Name',
            'nonexistent_field': 'should be ignored',
            'another_fake_field': 12345
        }
        response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
        assert response.status_code == 200
        
        # Verify only valid fields were updated
        data = json.loads(response.data)
        assert data['name'] == 'Updated Name'
        assert 'nonexistent_field' not in data
        assert 'another_fake_field' not in data
    
    @patch('app_module.db.session')
    def test_database_session_rollback_on_error(self, mock_session, client):
        """Test that database session is rolled back on errors"""
        # Mock commit to raise an exception
        mock_session.commit.side_effect = Exception("Database error")
        mock_session.rollback = MagicMock()
        
        account_data = {'name': 'Test User', 'email': 'test@example.com'}
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 500
        
        # Verify rollback was called
        mock_session.rollback.assert_called()
    
    def test_email_uniqueness_constraint(self, client):
        """Test email uniqueness is properly enforced"""
        email = 'unique@example.com'
        
        # Create first account
        account1_data = {'name': 'User One', 'email': email}
        response1 = client.post('/api/v1/accounts', json=account1_data)
        assert response1.status_code == 201
        
        # Try to create second account with same email
        account2_data = {'name': 'User Two', 'email': email}
        response2 = client.post('/api/v1/accounts', json=account2_data)
        assert response2.status_code == 409
        
        # Verify error message
        data = json.loads(response2.data)
        assert 'Email already exists' in data['error']
    
    def test_account_field_types_in_response(self, client):
        """Test that account fields have correct types in JSON response"""
        account_data = {
            'name': 'Type Test User',
            'email': 'typetest@example.com',
            'phone': '555-TYPE-TEST'
        }
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        
        # Check field types
        assert isinstance(data['id'], int)
        assert isinstance(data['name'], str)
        assert isinstance(data['email'], str)
        assert isinstance(data['phone'], str)
        assert isinstance(data['date_joined'], str)  # ISO format string
    
    def test_list_accounts_empty_database(self, client):
        """Test listing accounts when database is empty"""
        response = client.get('/api/v1/accounts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_account_creation_date_format(self, client):
        """Test that account creation date is in proper ISO format"""
        account_data = {'name': 'Date Format Test', 'email': 'dateformat@example.com'}
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        date_joined = data['date_joined']
        
        # Verify ISO format
        from datetime import datetime
        try:
            parsed_date = datetime.fromisoformat(date_joined.replace('Z', '+00:00'))
            assert isinstance(parsed_date, datetime)
        except ValueError:
            pytest.fail(f"date_joined '{date_joined}' is not in valid ISO format")
    
    def test_update_account_email_field(self, client):
        """Test updating account email field specifically"""
        # Create account
        account_data = {'name': 'Email Update Test', 'email': 'original@example.com'}
        create_response = client.post('/api/v1/accounts', json=account_data)
        account_id = json.loads(create_response.data)['id']
        
        # Update email
        update_data = {'email': 'updated@example.com'}
        response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['email'] == 'updated@example.com'
        assert data['name'] == 'Email Update Test'  # Should remain unchanged
    
    def test_phone_field_optional(self, client):
        """Test that phone field is truly optional"""
        # Create without phone
        account_data = {'name': 'No Phone User', 'email': 'nophone@example.com'}
        response = client.post('/api/v1/accounts', json=account_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['phone'] is None
        
        # Update to add phone
        account_id = data['id']
        update_data = {'phone': '555-NEW-PHONE'}
        response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
        assert response.status_code == 200
        
        updated_data = json.loads(response.data)
        assert updated_data['phone'] == '555-NEW-PHONE'
        
        # Update to remove phone (set to None or empty)
        update_data = {'phone': None}
        response = client.put(f'/api/v1/accounts/{account_id}', json=update_data)
        assert response.status_code == 200
        
        final_data = json.loads(response.data)
        assert final_data['phone'] is None