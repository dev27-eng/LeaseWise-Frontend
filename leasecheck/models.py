from datetime import datetime
from . import db

class TermsAcceptance(db.Model):
    __tablename__ = 'terms_acceptance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    terms_version = db.Column(db.String(50), nullable=False)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    stripe_payment_id = db.Column(db.String(255), unique=True, nullable=False)
    user_email = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), nullable=False, default='USD')
    status = db.Column(db.String(20), nullable=False)
    plan_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
