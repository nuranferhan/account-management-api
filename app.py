from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Direct app creation instead of factory
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Simple route for testing
@app.route('/')
def home():
    return "Account Management API is running!"

@app.route('/api/v1/health')
def health():
    return {"status": "healthy", "service": "account-management-api"}

if __name__ == '__main__':
    print("Starting Account Management API...")
    app.run(debug=True, host='0.0.0.0', port=5000)