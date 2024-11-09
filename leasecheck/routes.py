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

# Helper functions for dashboard statistics
def calculate_success_rate():
    total = Payment.query.count()
    if total == 0:
        return 0
    successful = Payment.query.filter_by(status='succeeded').count()
    return (successful / total) * 100

def get_revenue_by_plan():
    return db.session.query(
        Payment.plan_name,
        func.count(Payment.id).label('transactions'),
        func.sum(Payment.amount).label('revenue')
    ).filter_by(status='succeeded').group_by(Payment.plan_name).all()

def get_daily_trends():
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    return db.session.query(
        func.date(Payment.created_at).label('date'),
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('revenue')
    ).filter(
        Payment.created_at >= seven_days_ago,
        Payment.status == 'succeeded'
    ).group_by(func.date(Payment.created_at)).order_by(desc('date')).all()

def get_weekly_trends():
    four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
    return db.session.query(
        func.date_trunc('week', Payment.created_at).label('week'),
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('revenue')
    ).filter(
        Payment.created_at >= four_weeks_ago,
        Payment.status == 'succeeded'
    ).group_by('week').order_by(desc('week')).all()

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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('admin/login.html')
            
        admin = AdminUser.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Get statistics for dashboard
    stats = {
        'total_transactions': Payment.query.count(),
        'success_rate': calculate_success_rate(),
        'total_revenue': Payment.query.filter_by(status='succeeded').with_entities(func.sum(Payment.amount)).scalar() or 0,
        'today_transactions': Payment.query.filter(
            func.date(Payment.created_at) == datetime.utcnow().date()
        ).count(),
        'revenue_by_plan': get_revenue_by_plan(),
        'daily_trends': get_daily_trends(),
        'weekly_trends': get_weekly_trends()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    filters = {
        'search': request.args.get('search', ''),
        'status': request.args.get('status', ''),
        'plan': request.args.get('plan', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', '')
    }
    
    # Build query
    query = Payment.query
    
    if filters['search']:
        query = query.filter(
            (Payment.user_email.ilike(f"%{filters['search']}%")) |
            (Payment.stripe_payment_id.ilike(f"%{filters['search']}%"))
        )
    
    if filters['status']:
        query = query.filter(Payment.status == filters['status'])
    
    if filters['plan']:
        query = query.filter(Payment.plan_name == filters['plan'])
    
    if filters['date_from']:
        date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
        query = query.filter(Payment.created_at >= date_from)
    
    if filters['date_to']:
        date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
        query = query.filter(Payment.created_at <= date_to + timedelta(days=1))
    
    # Execute query with pagination
    pagination = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get available statuses and plans for filters
    available_statuses = db.session.query(Payment.status).distinct().all()
    available_plans = db.session.query(Payment.plan_name).distinct().all()
    
    return render_template('admin/transactions.html',
                         transactions=pagination.items,
                         pagination=pagination,
                         filters=filters,
                         available_statuses=[status[0] for status in available_statuses],
                         available_plans=[plan[0] for plan in available_plans])

@app.route('/admin/transaction/<transaction_id>')
@admin_required
def admin_transaction_details(transaction_id):
    transaction = Payment.query.filter_by(stripe_payment_id=transaction_id).first_or_404()
    
    try:
        # Fetch additional details from Stripe
        stripe_payment = stripe.PaymentIntent.retrieve(transaction_id)
        payment_method = None
        if hasattr(stripe_payment, 'payment_method') and stripe_payment.payment_method:
            payment_method = stripe.PaymentMethod.retrieve(stripe_payment.payment_method)
        
        details = {
            'user_email': transaction.user_email,
            'amount': transaction.amount,
            'status': transaction.status,
            'plan_name': transaction.plan_name,
            'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'customer_name': stripe_payment.metadata.get('full_name'),
            'customer_phone': stripe_payment.metadata.get('phone'),
            'payment_method': f"{payment_method.card.brand.title()} ending in {payment_method.card.last4}" if payment_method and hasattr(payment_method, 'card') else None,
            'error_log': stripe_payment.last_payment_error.message if hasattr(stripe_payment, 'last_payment_error') and stripe_payment.last_payment_error else None
        }
        
        return jsonify(details)
    
    except Exception as e:
        logger.error(f"Error while fetching transaction details: {str(e)}")
        return jsonify({
            'user_email': transaction.user_email,
            'amount': transaction.amount,
            'status': transaction.status,
            'plan_name': transaction.plan_name,
            'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'error_log': 'Failed to fetch additional details from Stripe'
        })
