from flask import render_template, redirect, url_for, flash, request, send_file, jsonify, session
from . import app, db
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment, AdminUser
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("Stripe API key is not set!")

# Admin authentication
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            logger.warning("Admin authentication failed: No admin_id in session")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Plan configurations
PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'price': 995,  # $9.95 in cents
        'features': ['1 Lease Analysis', 'Risk Analysis Report', 'PDF Export']
    },
    'standard': {
        'name': 'Standard Plan',
        'price': 1995,  # $19.95 in cents
        'features': ['3 Lease Analyses', 'Valid for 30 days', 'Priority Support']
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 2995,  # $29.95 in cents
        'features': ['6 Lease Analyses', 'Valid for 30 days', 'Priority Support + Consultation']
    }
}

@app.route('/')
@app.route('/welcome')
def welcome():
    return render_template('welcome_screen.html')

@app.route('/onboarding')
def onboarding():
    return render_template('onboarding_screen.html')

@app.route('/select-plan')
def select_plan():
    return render_template('select_plan.html')

@app.route('/admin/first-time-setup', methods=['GET', 'POST'])
def admin_first_time_setup():
    try:
        # Force query execution to check for admin existence
        admin_exists = bool(AdminUser.query.first())
        
        if admin_exists:
            flash('Admin account already exists', 'error')
            return redirect(url_for('admin_login'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not all([email, password, confirm_password]):
                flash('All fields are required', 'error')
                return render_template('admin/first_time_setup.html')
                
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('admin/first_time_setup.html')
            
            if len(password) < 8:
                flash('Password must be at least 8 characters long', 'error')
                return render_template('admin/first_time_setup.html')
                
            try:
                admin = AdminUser(
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(admin)
                db.session.commit()
                flash('Admin account created successfully', 'success')
                return redirect(url_for('admin_login'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating admin user: {e}")
                flash('Error creating admin account', 'error')
                
        return render_template('admin/first_time_setup.html')
        
    except Exception as e:
        logger.error(f"Error in first time setup: {e}")
        flash('System error occurred', 'error')
        return render_template('admin/first_time_setup.html')

# Rest of the original code continues as before... (admin_login, admin_dashboard, etc.)