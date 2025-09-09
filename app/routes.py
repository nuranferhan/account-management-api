from flask import Blueprint, request, jsonify
from app import db
from app.models import Account

accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/v1')

@accounts_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'account-management-api'}), 200

@accounts_bp.route('/accounts', methods=['POST'])
def create_account():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if email already exists
        existing = Account.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({'error': 'Email already exists'}), 409
        
        account = Account()
        account.from_dict(data)
        db.session.add(account)
        db.session.commit()
        
        return jsonify(account.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        return jsonify(account.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/accounts', methods=['GET'])
def list_accounts():
    try:
        accounts = Account.query.all()
        return jsonify([account.to_dict() for account in accounts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        account.from_dict(data)
        db.session.commit()
        
        return jsonify(account.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500