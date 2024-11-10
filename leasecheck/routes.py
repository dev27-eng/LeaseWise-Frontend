from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, session
from .database import db, safe_transaction, DatabaseError, retry_on_operational_error
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment, AdminUser, Document, SupportTicket
from datetime import datetime, timedelta
import weasyprint
import io
import stripe
import os
import logging
import json
from werkzeug.exceptions import BadRequest
from functools import wraps
from sqlalchemy import func, desc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
import mimetypes
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
DEVELOPMENT_MODE = os.environ.get('FLASK_ENV') == 'development'

if not stripe.api_key:
    logger.error("Stripe API key is not set!")

# Plan configuration remains unchanged...

# Create blueprint
bp = Blueprint('main', __name__)

# Initialize CSRF protection
csrf = CSRFProtect()

def csrf_exempt(view_func):
    """Mark a view function as being exempt from CSRF protection."""
    if view_func is None:
        return None
    view_func.csrf_exempt = True
    return view_func

# Update CSP settings
csp = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        'https://js.stripe.com',
        "'unsafe-inline'",
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
    ],
    'frame-src': [
        'https://js.stripe.com',
        'https://hooks.stripe.com',
    ],
    'img-src': ["'self'", 'https://*.stripe.com'],
    'connect-src': [
        "'self'",
        'https://api.stripe.com',
    ],
}

# Initialize Talisman with updated CSP
talisman = Talisman(
    content_security_policy=csp,
    content_security_policy_nonce_in=['script-src']
)

def log_stripe_event(event_type, event_data):
    """Enhanced logging for Stripe events"""
    try:
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': 'development' if DEVELOPMENT_MODE else 'production',
            'event_id': getattr(event_data, 'id', 'unknown'),
            'data': event_data
        }
        
        if DEVELOPMENT_MODE:
            logger.info(f"Development Mode - Stripe Event:\n{json.dumps(log_data, indent=2)}")
        else:
            logger.info(f"Stripe Event: {event_type} - ID: {getattr(event_data, 'id', 'unknown')}")
        
        return log_data
    except Exception as e:
        logger.error(f"Error logging Stripe event: {str(e)}")
        return None

@retry_on_operational_error
def update_payment_status(payment_intent_id, new_status, additional_data=None):
    """Update payment status in the database with enhanced error handling"""
    try:
        with safe_transaction() as session:
            payment = session.query(Payment).filter_by(stripe_payment_id=payment_intent_id).first()
            if payment:
                payment.status = new_status
                if additional_data and isinstance(additional_data, dict):
                    # Update payment details with additional data
                    for key, value in additional_data.items():
                        if hasattr(payment, key):
                            setattr(payment, key, value)
                    payment.payment_data = additional_data
                session.commit()
                logger.info(f"Payment status updated: {payment_intent_id} -> {new_status}")
                return True
            else:
                logger.warning(f"Payment not found: {payment_intent_id}")
                return False
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")
        raise

@bp.route('/stripe/events', methods=['POST'])
@csrf_exempt
def stripe_webhook():
    """Handle Stripe webhook events with enhanced error handling and logging"""
    if not webhook_secret:
        logger.error("Stripe webhook secret is not configured")
        return jsonify({'error': 'Webhook secret not configured'}), 500

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    if not sig_header:
        logger.warning("No Stripe signature found in request")
        return jsonify({'error': 'No Stripe signature'}), 401

    try:
        # Verify the event
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        
        # Log the event
        log_stripe_event(event.type, event.data.object)

        # Handle different event types
        if event.type == 'payment_intent.succeeded':
            intent = event.data.object
            update_payment_status(intent.get('id'), 'succeeded', {
                'amount': intent.get('amount'),
                'currency': intent.get('currency'),
                'payment_method_type': intent.get('payment_method_types', [None])[0],
                'payment_method_details': intent.get('payment_method_details')
            })
            
        elif event.type == 'payment_intent.payment_failed':
            intent = event.data.object
            error = intent.get('last_payment_error', {})
            error_info = {
                'error_message': error.get('message', 'Unknown error'),
                'error_code': error.get('code'),
                'last_payment_error': error
            }
            update_payment_status(intent.get('id'), 'failed', error_info)
            logger.error(f"Payment failed: {intent.get('id')} - {error_info['error_message']}")
            
        elif event.type == 'payment_intent.canceled':
            intent = event.data.object
            update_payment_status(intent.get('id'), 'canceled', {
                'cancellation_reason': intent.get('cancellation_reason')
            })
            
        elif event.type == 'payment_intent.requires_action':
            intent = event.data.object
            update_payment_status(intent.get('id'), 'requires_action', {
                'next_action': intent.get('next_action')
            })
            
        elif event.type == 'charge.failed':
            charge = event.data.object
            payment_intent_id = charge.get('payment_intent')
            update_payment_status(payment_intent_id, 'charge_failed', {
                'failure_code': charge.get('failure_code'),
                'failure_message': charge.get('failure_message'),
                'payment_method_type': charge.get('payment_method_details', {}).get('type'),
                'payment_method_details': charge.get('payment_method_details')
            })
            logger.error(f"Charge failed: {charge.get('id')} for payment {payment_intent_id}")
            
        elif event.type == 'charge.dispute.created':
            dispute = event.data.object
            payment_intent_id = dispute.get('payment_intent')
            update_payment_status(payment_intent_id, 'disputed', {
                'dispute_reason': dispute.get('reason'),
                'dispute_status': dispute.get('status'),
                'dispute_amount': dispute.get('amount'),
                'dispute_currency': dispute.get('currency')
            })
            logger.warning(f"Dispute created: {dispute.get('id')} for payment {payment_intent_id}")
            
        elif event.type == 'charge.refunded':
            charge = event.data.object
            payment_intent_id = charge.get('payment_intent')
            refunds = charge.get('refunds', {}).get('data', [{}])
            update_payment_status(payment_intent_id, 'refunded', {
                'refund_reason': refunds[0].get('reason') if refunds else None,
                'refund_amount': charge.get('amount_refunded'),
                'refund_status': 'completed',
                'refund_currency': charge.get('currency')
            })
            logger.info(f"Payment refunded: {payment_intent_id}")

        return jsonify({
            'status': 'success',
            'event_type': event.type,
            'event_id': event.id,
        }), 200

    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Invalid Stripe signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 401
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Other routes remain unchanged...
