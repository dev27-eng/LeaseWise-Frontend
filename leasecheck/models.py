from datetime import datetime
from .database import db
from sqlalchemy import event
import logging

logger = logging.getLogger(__name__)

class TermsAcceptance(db.Model):
    __tablename__ = 'terms_acceptance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    terms_version = db.Column(db.String(50), nullable=False)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), nullable=False, default='USD')
    status = db.Column(db.String(20), nullable=False, default='pending')
    user_email = db.Column(db.String(255), nullable=False)
    billing_address = db.Column(db.JSON, nullable=True)  # Made nullable for flexibility
    customer_name = db.Column(db.String(255), nullable=False)
    items = db.Column(db.JSON, nullable=False)  # Store line items
    notes = db.Column(db.Text)
    pdf_path = db.Column(db.String(500))  # Path to stored PDF invoice
    
    payment = db.relationship('Payment', backref=db.backref('invoice', uselist=False))

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

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
    
    # Payment method information
    payment_method_type = db.Column(db.String(50))  # card, sepa_debit, etc.
    payment_method_details = db.Column(db.JSON)  # Store detailed payment method info
    
    # Error tracking
    error_message = db.Column(db.Text)  # Store error messages if payment fails
    error_code = db.Column(db.String(100))  # Store error codes
    last_payment_error = db.Column(db.JSON)  # Store complete error information
    
    # Additional payment information
    payment_info = db.Column(db.JSON)  # Store additional payment data
    customer_name = db.Column(db.String(255))  # Customer's full name
    billing_address = db.Column(db.JSON)  # Store complete billing address
    
    # Refund and dispute information
    refund_status = db.Column(db.String(20))  # Status of any refunds
    refund_amount = db.Column(db.Integer)  # Amount refunded in cents
    refund_reason = db.Column(db.String(255))  # Reason for refund
    dispute_status = db.Column(db.String(20))  # Status of any disputes
    dispute_reason = db.Column(db.String(255))  # Reason for dispute

    def __repr__(self):
        return f'<Payment {self.stripe_payment_id}>'

    def generate_invoice(self):
        """Generate invoice for successful payment"""
        from .routes import create_invoice, generate_invoice_pdf
        try:
            if self.status != 'succeeded':
                logger.info(f"Payment {self.stripe_payment_id} is not in succeeded status, skipping invoice generation")
                return None

            # Check if invoice already exists
            existing_invoice = Invoice.query.filter_by(payment_id=self.id).first()
            if existing_invoice:
                logger.info(f"Invoice already exists for payment {self.stripe_payment_id}")
                return existing_invoice

            logger.info(f"Generating invoice for payment {self.stripe_payment_id}")
            invoice = create_invoice(self)
            if invoice:
                # Generate PDF immediately after creating invoice
                pdf_path = generate_invoice_pdf(invoice)
                if pdf_path:
                    invoice.pdf_path = pdf_path
                    invoice.status = 'completed'
                    db.session.commit()
                    logger.info(f"Successfully generated invoice PDF at {pdf_path}")
                else:
                    logger.error(f"Failed to generate PDF for invoice {invoice.invoice_number}")
                
                return invoice
            else:
                logger.error(f"Failed to create invoice for payment {self.stripe_payment_id}")
                return None
        except Exception as e:
            logger.error(f"Error generating invoice for payment {self.stripe_payment_id}: {str(e)}")
            db.session.rollback()
            return None

@event.listens_for(Payment, 'after_update')
def payment_status_changed(mapper, connection, target):
    """Listen for payment status changes and generate invoice when payment succeeds"""
    if target.status == 'succeeded':
        logger.info(f"Payment status changed to succeeded for {target.stripe_payment_id}")
        target.generate_invoice()

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
    
    # New fields for document type detection
    detected_type = db.Column(db.String(50))  # pdf, doc, docx
    content_valid = db.Column(db.Boolean)
    detection_error = db.Column(db.Text)
    
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