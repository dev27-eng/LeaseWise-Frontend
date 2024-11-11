from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, current_app
from .database import db, safe_transaction, DatabaseError, retry_on_operational_error
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment, AdminUser, Document, SupportTicket, Invoice
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import io
import stripe
import os
import logging
import json
import uuid
import click
from werkzeug.exceptions import BadRequest
from functools import wraps
from sqlalchemy import func, desc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Create blueprint
bp = Blueprint('main', __name__)

@bp.route('/lease-upload')
def lease_upload():
    """Display lease upload page"""
    return render_template('lease_upload.html')

def create_invoice(payment):
    """Create an invoice record for a payment"""
    try:
        invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{str(payment.id).zfill(4)}"
        
        # Default billing address if none provided
        billing_address = payment.billing_address or {
            'street': 'N/A',
            'street2': '',
            'city': 'N/A',
            'state': 'N/A',
            'zipCode': 'N/A',
            'country': 'US'
        }
        
        # Create invoice items
        items = [{
            'description': f"{payment.plan_name} Plan",
            'quantity': 1,
            'unit_price': payment.amount,
            'amount': payment.amount
        }]
        
        invoice = Invoice(
            invoice_number=invoice_number,
            payment_id=payment.id,
            created_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            total_amount=payment.amount,
            currency=payment.currency,
            status='pending',
            user_email=payment.user_email,
            billing_address=billing_address,
            customer_name=payment.customer_name or 'Customer',
            items=items
        )
        
        db.session.add(invoice)
        db.session.commit()
        logger.info(f"Created invoice {invoice_number} for payment {payment.stripe_payment_id}")
        return invoice
    except Exception as e:
        logger.error(f"Error creating invoice for payment {payment.stripe_payment_id}: {str(e)}")
        db.session.rollback()
        return None

def generate_pending_invoices():
    """Generate invoices for all succeeded payments that don't have invoices"""
    try:
        with safe_transaction() as session:
            # Get all succeeded payments without invoices
            payments = session.query(Payment).outerjoin(
                Invoice, Payment.id == Invoice.payment_id
            ).filter(
                Payment.status == 'succeeded',
                Invoice.id.is_(None)
            ).all()
            
            generated_count = 0
            for payment in payments:
                invoice = create_invoice(payment)
                if invoice:
                    pdf_path = generate_invoice_pdf(invoice)
                    if pdf_path:
                        invoice.pdf_path = pdf_path
                        invoice.status = 'completed'
                        generated_count += 1
                        logger.info(f"Generated invoice {invoice.invoice_number} for payment {payment.stripe_payment_id}")
                    else:
                        logger.error(f"Failed to generate PDF for invoice {invoice.invoice_number}")
            
            if generated_count > 0:
                session.commit()
            
            return generated_count
    except Exception as e:
        logger.error(f"Error generating pending invoices: {str(e)}")
        return 0

def generate_invoice_pdf(invoice):
    """Generate PDF invoice using ReportLab"""
    try:
        # Create buffer for PDF
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Container for 'Flowable' objects
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        
        # Add header
        elements.append(Paragraph("LeaseCheck", title_style))
        elements.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        
        # Add dates
        elements.append(Paragraph(f"Date: {invoice.created_at.strftime('%B %d, %Y')}", styles["Normal"]))
        elements.append(Paragraph(f"Due Date: {invoice.due_date.strftime('%B %d, %Y')}", styles["Normal"]))
        elements.append(Spacer(1, 12))
        
        # Add billing information
        elements.append(Paragraph("Bill To:", styles["Heading3"]))
        elements.append(Paragraph(invoice.customer_name, styles["Normal"]))
        elements.append(Paragraph(invoice.user_email, styles["Normal"]))
        
        # Format billing address
        if invoice.billing_address:
            addr = invoice.billing_address
            address_lines = [
                addr.get('street', ''),
                addr.get('street2', ''),
                f"{addr.get('city', '')}, {addr.get('state', '')} {addr.get('zipCode', '')}",
                addr.get('country', '')
            ]
            for line in address_lines:
                if line and line.strip():
                    elements.append(Paragraph(line, styles["Normal"]))
        
        elements.append(Spacer(1, 20))
        
        # Create items table
        table_data = [['Description', 'Quantity', 'Unit Price', 'Amount']]
        for item in invoice.items:
            table_data.append([
                item['description'],
                str(item['quantity']),
                f"${item['unit_price']/100:.2f}",
                f"${item['amount']/100:.2f}"
            ])
        
        # Add total row
        table_data.append(['', '', 'Total:', 
                          f"${invoice.total_amount/100:.2f} {invoice.currency}"])
        
        # Create and style table
        table = Table(table_data, colWidths=[4*inch, 1*inch, 1.25*inch, 1.25*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 1, colors.black)
        ]))
        elements.append(table)
        
        # Add footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your business!", styles["Normal"]))
        elements.append(Paragraph("For questions about this invoice, please contact support@coloradoleasecheck.com", styles["Normal"]))
        
        # Build PDF
        doc.build(elements)
        
        # Create directory if it doesn't exist
        invoice_dir = os.path.join(os.getcwd(), 'leasecheck', 'static', 'invoices')
        os.makedirs(invoice_dir, exist_ok=True)
        
        # Save PDF file
        pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_path = os.path.join(invoice_dir, pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return os.path.join('invoices', pdf_filename)
            
    except Exception as e:
        logger.error(f"Error generating PDF invoice: {str(e)}")
        return None

def register_cli_commands(app):
    @app.cli.command('generate-pending-invoices')
    def generate_pending_invoices_command():
        """Generate invoices and PDFs for all succeeded payments without invoices"""
        count = generate_pending_invoices()
        click.echo(f"Generated {count} new invoice PDFs")

@bp.route('/invoice/<invoice_number>')
def view_invoice(invoice_number):
    """View invoice details"""
    try:
        invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
        
        if not invoice:
            logger.warning(f"Invoice {invoice_number} not found")
            flash('Invoice not found', 'error')
            return redirect(url_for('main.select_plan'))
        
        return render_template('invoice.html', invoice=invoice)
    except Exception as e:
        logger.error(f"Error viewing invoice {invoice_number}: {str(e)}")
        flash('Error loading invoice', 'error')
        return redirect(url_for('main.select_plan'))

@bp.route('/invoice/<invoice_number>/download')
def download_invoice(invoice_number):
    """Download invoice as PDF"""
    try:
        invoice = Invoice.query.filter_by(invoice_number=invoice_number).first_or_404()
        
        if not invoice.pdf_path:
            pdf_path = generate_invoice_pdf(invoice)
            if pdf_path:
                invoice.pdf_path = pdf_path
                db.session.commit()
            else:
                flash('Error generating invoice PDF', 'error')
                return redirect(url_for('main.view_invoice', invoice_number=invoice_number))
        
        full_path = os.path.join(os.getcwd(), 'leasecheck', 'static', invoice.pdf_path)
        if os.path.exists(full_path):
            return send_file(
                full_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"invoice_{invoice.invoice_number}.pdf"
            )
        
        flash('Invoice PDF file not found', 'error')
        return redirect(url_for('main.view_invoice', invoice_number=invoice_number))
    except Exception as e:
        logger.error(f"Error downloading invoice {invoice_number}: {str(e)}")
        flash('Error downloading invoice', 'error')
        return redirect(url_for('main.select_plan'))

@bp.route('/upload-lease', methods=['POST'])
def upload_lease():
    """Handle lease document upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
            
        # Validate file type
        allowed_types = {'pdf', 'doc', 'docx'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_types):
            return jsonify({'error': 'Invalid file type'}), 400
            
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join('uploads', unique_filename)
        
        # Save file
        file.save(os.path.join(current_app.static_folder, file_path))
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=original_filename,
            mimetype=file.mimetype,
            file_size=os.path.getsize(os.path.join(current_app.static_folder, file_path)),
            user_email=request.form.get('user_email', 'anonymous@example.com'),  # Replace with actual user email
            file_path=file_path,
            status='pending'
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Start processing in background (implement actual processing logic)
        # For now, we'll just update status after a delay
        document.status = 'processing'
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'document_id': document.id,
            'redirect_url': url_for('main.processing_status', document_id=document.id)
        })
        
    except Exception as e:
        logger.error(f"Error uploading lease document: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to upload document'}), 500

@bp.route('/processing-status/<int:document_id>')
def processing_status(document_id):
    """Show document processing status page"""
    try:
        document = Document.query.get_or_404(document_id)
        return render_template('processing_status.html', document=document)
    except Exception as e:
        logger.error(f"Error displaying processing status: {str(e)}")
        flash('Error loading document status', 'error')
        return redirect(url_for('main.lease_upload'))

@bp.route('/api/document-status/<int:document_id>')
def get_document_status(document_id):
    """API endpoint for checking document processing status"""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Calculate progress based on status
        progress_map = {
            'pending': 0,
            'validating': 25,
            'analyzing': 50,
            'processing': 75,
            'processed': 100,
            'error': 0
        }
        
        progress = progress_map.get(document.status, 0)
        
        return jsonify({
            'status': document.status,
            'progress': progress,
            'error_message': document.error_message if document.status == 'error' else None
        })
        
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        return jsonify({'error': 'Failed to get document status'}), 500

@bp.route('/view-document/<int:document_id>')
def view_document(document_id):
    """View processed document results"""
    try:
        document = Document.query.get_or_404(document_id)
        if document.status != 'processed':
            flash('Document is not ready for viewing', 'warning')
            return redirect(url_for('main.processing_status', document_id=document_id))
            
        return render_template('view_document.html', document=document)
    except Exception as e:
        logger.error(f"Error viewing document: {str(e)}")
        flash('Error loading document', 'error')
        return redirect(url_for('main.lease_upload'))