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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Check if any admin users exist
    if AdminUser.query.first() is None:
        return redirect(url_for('admin_first_time_setup'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = AdminUser.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('admin/login.html')

@app.route('/admin/first-time-setup', methods=['GET', 'POST'])
def admin_first_time_setup():
    # Redirect if admin users already exist
    if AdminUser.query.first() is not None:
        return redirect(url_for('admin_login'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate email format
        if not email or '@' not in email:
            flash('Please enter a valid email address', 'error')
            return render_template('admin/first_time_setup.html')
            
        # Validate password
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('admin/first_time_setup.html')
            
        # Check password requirements
        if not any(c.isupper() for c in password):
            flash('Password must contain at least one uppercase letter', 'error')
            return render_template('admin/first_time_setup.html')
            
        if not any(c.islower() for c in password):
            flash('Password must contain at least one lowercase letter', 'error')
            return render_template('admin/first_time_setup.html')
            
        if not any(c.isdigit() for c in password):
            flash('Password must contain at least one number', 'error')
            return render_template('admin/first_time_setup.html')
            
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            flash('Password must contain at least one special character', 'error')
            return render_template('admin/first_time_setup.html')
            
        # Check password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('admin/first_time_setup.html')
            
        # Create admin user
        admin = AdminUser(
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(admin)
        
        try:
            db.session.commit()
            flash('Admin account created successfully', 'success')
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
            flash('An error occurred while creating the admin account', 'error')
            
    return render_template('admin/first_time_setup.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Calculate summary statistics
    total_transactions = Payment.query.count()
    successful_transactions = Payment.query.filter_by(status='succeeded').count()
    success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
    
    # Calculate revenue by plan
    revenue_by_plan = db.session.query(
        Payment.plan_name,
        func.count(Payment.id).label('transactions'),
        func.sum(Payment.amount).label('revenue')
    ).filter_by(status='succeeded').group_by(Payment.plan_name).all()
    
    # Calculate daily trends (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_trends = db.session.query(
        func.date(Payment.created_at).label('date'),
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('revenue')
    ).filter(
        Payment.created_at >= seven_days_ago,
        Payment.status == 'succeeded'
    ).group_by(func.date(Payment.created_at)).order_by(desc('date')).all()
    
    # Calculate weekly trends (last 4 weeks)
    four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
    weekly_trends = db.session.query(
        func.date_trunc('week', Payment.created_at).label('week'),
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('revenue')
    ).filter(
        Payment.created_at >= four_weeks_ago,
        Payment.status == 'succeeded'
    ).group_by('week').order_by(desc('week')).all()
    
    stats = {
        'total_transactions': total_transactions,
        'success_rate': success_rate,
        'total_revenue': sum(plan.revenue for plan in revenue_by_plan) if revenue_by_plan else 0,
        'today_transactions': Payment.query.filter(
            func.date(Payment.created_at) == datetime.utcnow().date()
        ).count(),
        'revenue_by_plan': [
            {'name': plan.plan_name, 'transactions': plan.transactions, 'revenue': plan.revenue}
            for plan in revenue_by_plan
        ],
        'daily_trends': [
            {'date': day.date.strftime('%Y-%m-%d'), 'count': day.count, 'revenue': day.revenue}
            for day in daily_trends
        ],
        'weekly_trends': [
            {'date': week.week.strftime('%Y-%m-%d'), 'count': week.count, 'revenue': week.revenue}
            for week in weekly_trends
        ]
    }
    
    return render_template('admin/dashboard.html', stats=stats)

# ... rest of the original routes remain the same (create_payment, payment_status, etc.)