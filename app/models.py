from app import db
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