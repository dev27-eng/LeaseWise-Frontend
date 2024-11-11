from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, session
from .database import db, safe_transaction, DatabaseError, retry_on_operational_error
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment, AdminUser, Document, SupportTicket
from .cache import (
    cache, clear_all_caches, clear_cache_by_key, clear_cache_by_pattern,
    clear_user_cache, clear_document_cache, clear_plan_cache, clear_admin_cache,
    get_cache_stats, cached_with_key
)
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

# For testing purposes, set admin session
@bp.before_request
def setup_test_admin():
    if os.environ.get('FLASK_ENV') == 'development':
        session['is_admin'] = True

@bp.route('/admin/cache', methods=['GET'])
def admin_cache_dashboard():
    """Admin dashboard for cache management"""
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    stats = get_cache_stats()
    return render_template('admin/cache_dashboard.html', stats=stats)

@bp.route('/admin/cache/clear', methods=['POST'])
def admin_clear_cache():
    """Admin route to clear all caches"""
    try:
        cache_type = request.form.get('type', 'all')
        if cache_type == 'all':
            clear_all_caches()
            flash('All caches cleared successfully', 'success')
        elif cache_type == 'user':
            user_email = request.form.get('user_email')
            if user_email:
                clear_user_cache(user_email)
                flash(f'Cache cleared for user: {user_email}', 'success')
        elif cache_type == 'document':
            document_id = request.form.get('document_id')
            if document_id:
                clear_document_cache(document_id)
                flash(f'Cache cleared for document: {document_id}', 'success')
        elif cache_type == 'plan':
            clear_plan_cache()
            flash('Plan cache cleared successfully', 'success')
        elif cache_type == 'admin':
            clear_admin_cache()
            flash('Admin cache cleared successfully', 'success')
    except Exception as e:
        flash(f'Error clearing cache: {str(e)}', 'error')
    return redirect(url_for('main.admin_cache_dashboard'))

@bp.route('/')
@cache.cached(timeout=300)  # Cache for 5 minutes
def index():
    return render_template('welcome_screen.html')

@bp.route('/onboarding')
@cached_with_key('onboarding')
def onboarding():
    return render_template('onboarding_screen.html')

@bp.route('/select-plan')
@cached_with_key('plan_selection')
def select_plan():
    return render_template('select_plan.html', plans=PLANS)

@bp.route('/checkout')
def checkout():
    """Don't cache checkout page for security reasons"""
    plan_id = request.args.get('plan')
    if not plan_id or plan_id not in PLANS:
        return redirect(url_for('main.select_plan'))
    plan = PLANS[plan_id]
    return render_template('checkout.html', 
                         plan_id=plan_id,
                         plan=plan,
                         stripe_public_key=os.environ.get('STRIPE_PUBLIC_KEY'))

# Add cache control headers to all responses
@bp.after_request
def add_cache_control(response):
    """Add cache control headers to responses"""
    if request.endpoint != 'static':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

def clear_user_specific_cache(user_email):
    """Clear all caches related to a specific user"""
    clear_user_cache(user_email)

def clear_document_specific_cache(document_id):
    """Clear all caches related to a specific document"""
    clear_document_cache(document_id)