from flask import render_template, redirect, url_for, flash, request, send_file, jsonify
from . import app, db
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment
from datetime import datetime
import weasyprint
import io
import stripe
import os
import logging
from werkzeug.exceptions import BadRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("Stripe API key is not set!")

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

# [Rest of the routes remain unchanged]
