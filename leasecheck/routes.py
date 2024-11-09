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
from werkzeug.exceptions import BadRequest
from functools import wraps
from sqlalchemy import func, desc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
import mimetypes
from flask_talisman import Talisman

# Plan configuration
PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'price': 9.95,
        'features': [
            '1 Lease Analysis',
            'Ideal for single lease review',
            'Risk Analysis Report',
            'PDF Export'
        ]
    },
    'standard': {
        'name': 'Standard Plan',
        'price': 19.95,
        'features': [
            '3 Lease Analyses',
            'Valid for 30 days',
            'Compare Multiple Options',
            'Priority Support'
        ]
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 29.95,
        'features': [
            '6 Lease Analyses',
            'Valid for 30 days',
            'Best value for multiple reviews',
            'Priority Support + Consultation'
        ]
    }
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("Stripe API key is not set!")

# Create blueprint
bp = Blueprint('main', __name__)

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
    'img-src': ["'self'"],
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

@bp.route('/')
def index():
    return render_template('welcome_screen.html')

@bp.route('/onboarding')
def onboarding():
    return render_template('onboarding_screen.html')

@bp.route('/select-plan')
def select_plan():
    return render_template('select_plan.html')

@bp.route('/checkout')
def checkout():
    plan_id = request.args.get('plan')
    if not plan_id or plan_id not in PLANS:
        return redirect(url_for('main.select_plan'))
    plan = PLANS[plan_id]
    return render_template('checkout.html', 
                         plan_id=plan_id,
                         plan=plan,
                         stripe_public_key=os.environ.get('STRIPE_PUBLIC_KEY'))