from datetime import datetime
from . import db

class TermsAcceptance(db.Model):
    __tablename__ = 'terms_acceptance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    terms_version = db.Column(db.String(50), nullable=False)
