# app.py - TAMAMEN YENİ VERSİYON
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Models (direkt burada tanımlayalım)
from datetime import datetime

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None
        }
    
    def from_dict(self, data):
        for field in ['name', 'email', 'phone']:
            if field in data:
                setattr(self, field, data[field])

# Routes (direkt burada tanımlayalım)
from flask import request, jsonify

@app.route('/')
def home():
    return "Account Management API is running!"

@app.route('/api/v1/health')
def health():
    return {"status": "healthy", "service": "account-management-api"}

@app.route('/api/v1/accounts', methods=['POST'])
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

@app.route('/api/v1/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        return jsonify(account.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts', methods=['GET'])
def list_accounts():
    try:
        accounts = Account.query.all()
        return jsonify([account.to_dict() for account in accounts]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts/<int:account_id>', methods=['PUT'])
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

@app.route('/api/v1/accounts/<int:account_id>', methods=['DELETE'])
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    print("Starting Account Management API...")
    app.run(debug=True, host='0.0.0.0', port=5000)