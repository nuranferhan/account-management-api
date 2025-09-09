from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    CORS(app)
    
    from app.routes import accounts_bp
    app.register_blueprint(accounts_bp)
    
    with app.app_context():
        db.create_all()
    
    return app