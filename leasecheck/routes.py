from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify
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

@bp.route('/')
def index():
    """Root endpoint redirects to select plan"""
    return redirect(url_for('main.select_plan'))

@bp.route('/select-plan')
def select_plan():
    """Plan selection page"""
    plans = {
        'basic': {
            'name': 'Basic Plan',
            'price': 9.95,
            'features': ['1 Lease Analysis', 'Ideal for single lease']
        },
        'standard': {
            'name': 'Standard Plan',
            'price': 19.95,
            'features': ['3 uses in 30 days', 'Great for comparing options']
        },
        'premium': {
            'name': 'Premium Plan',
            'price': 29.95,
            'features': ['6 uses in 30 days', 'Best value for multiple reviews']
        }
    }
    return render_template('select_plan.html', plans=plans)

@bp.route('/checkout')
def checkout():
    """Checkout page for selected plan"""
    plan_id = request.args.get('plan')
    if not plan_id:
        flash('Please select a plan first', 'error')
        return redirect(url_for('main.select_plan'))
    
    plans = {
        'basic': {
            'name': 'Basic Plan',
            'price': 9.95,
            'features': ['1 Lease Analysis', 'Ideal for single lease']
        },
        'standard': {
            'name': 'Standard Plan',
            'price': 19.95,
            'features': ['3 uses in 30 days', 'Great for comparing options']
        },
        'premium': {
            'name': 'Premium Plan',
            'price': 29.95,
            'features': ['6 uses in 30 days', 'Best value for multiple reviews']
        }
    }
    
    plan = plans.get(plan_id)
    if not plan:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('main.select_plan'))
    
    stripe_public_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    return render_template('checkout.html', plan=plan, stripe_public_key=stripe_public_key)

def generate_invoice_number():
    """Generate a unique invoice number"""
    try:
        prefix = datetime.utcnow().strftime('%Y%m')
        # Get the latest invoice number for the current month
        latest_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f'INV-{prefix}-%')
        ).order_by(desc(Invoice.invoice_number)).first()
        
        if latest_invoice:
            # Extract the sequence number and increment it
            current_seq = int(latest_invoice.invoice_number.split('-')[-1])
            next_seq = current_seq + 1
        else:
            next_seq = 1
        
        # Format with leading zeros
        invoice_number = f"INV-{prefix}-{next_seq:04d}"
        return invoice_number
    except Exception as e:
        logger.error(f"Error generating invoice number: {str(e)}")
        raise

@retry_on_operational_error
def create_invoice(payment):
    """Create an invoice for a successful payment"""
    try:
        # Validate payment data
        if not all([payment.user_email, payment.amount, payment.plan_name,
                   payment.customer_name, payment.billing_address]):
            logger.error(f"Missing required payment data for invoice creation")
            return None

        with safe_transaction() as session:
            # Check for existing invoice
            existing_invoice = session.query(Invoice).filter_by(payment_id=payment.id).first()
            if existing_invoice:
                logger.info(f"Invoice already exists for payment {payment.stripe_payment_id}")
                return existing_invoice

            # Create invoice items
            items = [{
                'description': f"{payment.plan_name} - Lease Analysis Service",
                'quantity': 1,
                'unit_price': payment.amount,
                'amount': payment.amount
            }]
            
            # Create invoice record
            invoice = Invoice()
            invoice.invoice_number = generate_invoice_number()
            invoice.payment_id = payment.id
            invoice.due_date = datetime.utcnow() + timedelta(days=30)
            invoice.total_amount = payment.amount
            invoice.currency = payment.currency or 'USD'
            invoice.status = 'pending'
            invoice.user_email = payment.user_email
            invoice.billing_address = payment.billing_address
            invoice.customer_name = payment.customer_name
            invoice.items = items
            
            session.add(invoice)
            session.flush()

            # Generate PDF
            pdf_path = generate_invoice_pdf(invoice)
            if pdf_path:
                invoice.pdf_path = pdf_path
                invoice.status = 'paid'
                session.commit()
                logger.info(f"Invoice created successfully: {invoice.invoice_number}")
                return invoice
            else:
                session.rollback()
                logger.error(f"Failed to generate PDF for invoice: {invoice.invoice_number}")
                return None

    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        return None

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

def update_payment_status(payment_intent_id, new_status, additional_data=None):
    """Update payment status and generate invoice if payment is successful"""
    try:
        with safe_transaction() as session:
            payment = session.query(Payment).filter_by(
                stripe_payment_id=payment_intent_id).first()
            
            if not payment:
                logger.warning(f"Payment not found: {payment_intent_id}")
                return False
            
            logger.info(f"Updating payment status for {payment_intent_id} to {new_status}")
            
            # Update payment status and additional data
            payment.status = new_status
            if additional_data and isinstance(additional_data, dict):
                for key, value in additional_data.items():
                    if hasattr(payment, key):
                        setattr(payment, key, value)
            
            # Commit the payment status update first
            session.commit()
            
            # Generate invoice for successful payments
            if new_status == 'succeeded':
                invoice = create_invoice(payment)
                if invoice:
                    logger.info(f"Invoice {invoice.invoice_number} generated successfully for payment {payment_intent_id}")
                    return True
                else:
                    logger.error(f"Failed to generate invoice for payment {payment_intent_id}")
                    return False
            
            return True
            
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")
        return False
