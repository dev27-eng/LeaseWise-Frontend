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

@app.route('/checkout/<plan_id>')
def checkout(plan_id):
    if plan_id not in PLANS:
        flash('Invalid plan selected', 'error')
        logger.warning(f"Invalid plan ID attempted: {plan_id}")
        return redirect(url_for('select_plan'))
    
    stripe_public_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    if not stripe_public_key:
        logger.error("Stripe publishable key is not set!")
        flash('Payment system is currently unavailable', 'error')
        return redirect(url_for('select_plan'))
    
    plan = PLANS[plan_id]
    return render_template('checkout.html',
                         plan_id=plan_id,
                         plan_name=plan['name'],
                         plan_price=plan['price'] / 100,  # Convert cents to dollars
                         PLANS=PLANS,
                         stripe_public_key=stripe_public_key)

@app.route('/create-payment', methods=['POST'])
def create_payment():
    try:
        if not request.is_json:
            raise BadRequest('Content-Type must be application/json')

        data = request.get_json()
        if not data:
            raise BadRequest('No JSON data received')

        plan_id = data.get('plan_id')
        payment_method_id = data.get('payment_method_id')
        user_info = data.get('user_info', {})

        # Log payment attempt
        logger.info(f"Payment attempt for plan: {plan_id}")

        # Validate required fields
        required_fields = [
            ('full_name', 'Full name is required'),
            ('email', 'Email is required'),
            ('phone', 'Phone number is required'),
            ('address.street', 'Street address is required'),
            ('address.city', 'City is required'),
            ('address.state', 'State is required'),
            ('address.zip_code', 'ZIP code is required'),
            ('address.country', 'Country is required')
        ]

        for field, message in required_fields:
            if field.startswith('address.'):
                if not user_info.get('address', {}).get(field.split('.')[1]):
                    logger.warning(f"Missing required field: {field}")
                    return jsonify({'error': message}), 400
            elif not user_info.get(field):
                logger.warning(f"Missing required field: {field}")
                return jsonify({'error': message}), 400

        if plan_id not in PLANS:
            logger.error(f"Invalid plan ID: {plan_id}")
            return jsonify({'error': 'Invalid plan selected'}), 400

        plan = PLANS[plan_id]
        
        try:
            # Create payment intent with customer details
            intent = stripe.PaymentIntent.create(
                amount=plan['price'],
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                return_url=url_for('payment_status', _external=True),
                metadata={
                    'full_name': user_info['full_name'],
                    'email': user_info['email'],
                    'phone': user_info['phone'],
                    'address_street': user_info['address']['street'],
                    'address_street2': user_info['address'].get('street2', ''),
                    'address_city': user_info['address']['city'],
                    'address_state': user_info['address']['state'],
                    'address_zip': user_info['address']['zip_code'],
                    'address_country': user_info['address']['country']
                }
            )

            logger.info(f"Payment intent created: {intent.id}")

            # Record the payment attempt
            payment = Payment(
                stripe_payment_id=intent.id,
                user_email=user_info['email'],
                amount=plan['price'],
                currency='USD',
                status=intent.status,
                plan_name=plan['name']
            )
            db.session.add(payment)
            db.session.commit()
            logger.info(f"Payment record created for intent: {intent.id}")

            if intent.status == 'requires_action':
                return jsonify({
                    'requires_action': True,
                    'client_secret': intent.client_secret
                })
            
            if intent.status == 'succeeded':
                logger.info(f"Payment succeeded for intent: {intent.id}")
                return jsonify({'success': True})

            logger.warning(f"Payment failed for intent: {intent.id} with status: {intent.status}")
            return jsonify({'error': 'Payment failed'}), 400

        except stripe.error.CardError as e:
            error_msg = e.error.message
            logger.error(f"Card error for user {user_info['email']}: {error_msg}")
            return jsonify({'error': error_msg}), 400

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return jsonify({'error': 'Payment processing error. Please try again.'}), 400

    except BadRequest as e:
        logger.error(f"Bad request error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in payment processing: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

@app.route('/payment-status')
def payment_status():
    status = request.args.get('status', 'failed')
    logger.info(f"Payment status page accessed with status: {status}")
    return render_template('payment_status.html', status=status)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = AdminUser.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('admin/login.html')

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
        if stripe_payment.payment_method:
            payment_method = stripe.PaymentMethod.retrieve(stripe_payment.payment_method)
        
        details = {
            'user_email': transaction.user_email,
            'amount': transaction.amount,
            'status': transaction.status,
            'plan_name': transaction.plan_name,
            'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'customer_name': stripe_payment.metadata.get('full_name'),
            'customer_phone': stripe_payment.metadata.get('phone'),
            'payment_method': f"{payment_method.card.brand.title()} ending in {payment_method.card.last4}" if payment_method else None,
            'error_log': stripe_payment.last_payment_error.message if stripe_payment.last_payment_error else None
        }
        
        return jsonify(details)
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error while fetching transaction details: {str(e)}")
        return jsonify({
            'user_email': transaction.user_email,
            'amount': transaction.amount,
            'status': transaction.status,
            'plan_name': transaction.plan_name,
            'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'error_log': 'Failed to fetch additional details from Stripe'
        })