from datetime import datetime
from .app import db

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

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    user_email = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, processing, processed, error
    file_path = db.Column(db.String(500), nullable=False)
    error_message = db.Column(db.Text)
    processing_started = db.Column(db.DateTime)
    processing_completed = db.Column(db.DateTime)
    
    # Review-related fields
    review_status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, completed
    risk_level = db.Column(db.String(20))  # low, medium, high
    risk_factors = db.Column(db.JSON)
    annotations = db.Column(db.JSON)  # Store document annotations
    last_reviewed = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_email = db.Column(db.String(255), nullable=False)
    issue_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    document = db.relationship('Document', backref=db.backref('support_tickets', lazy=True))
