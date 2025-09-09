from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)

# Configuration - basit ve güvenli
app.config['SECRET_KEY'] = 'dev-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Models 
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

# Routes
@app.route('/')
def home():
    return jsonify({"message": "Account Management API is running!", "status": "ok"})

@app.route('/api/v1/health')
def health():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({"status": "healthy", "service": "account-management-api", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "service": "account-management-api", "error": str(e)}), 500

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
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    try:
        account = Account.query.get_or_404(account_id)
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
        account = Account.query.get_or_404(account_id)
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        account.from_dict(data)
        db.session.commit()
        
        return jsonify(account.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    try:
        account = Account.query.get_or_404(account_id)
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Initialize database
def init_db():
    try:
        with app.app_context():
            db.create_all()
            print("✓ Database tables created successfully!")
            return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

# Application startup
if __name__ == '__main__':
    print("Starting Account Management API...")
    if init_db():
        print("Starting server on 0.0.0.0:5000...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to initialize database, exiting...")
        exit(1)

# For gunicorn
def create_app():
    print("Creating app for gunicorn...")
    if init_db():
        print("✓ App created successfully for gunicorn")
        return app
    else:
        print("✗ Failed to create app for gunicorn")
        raise Exception("Database initialization failed")