from flask import render_template, redirect, url_for, flash, request, send_file, jsonify
from . import app, db
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment
from datetime import datetime
import weasyprint
import io
import stripe
import os

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

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

@app.route('/account-setup')
def account_setup():
    return render_template('account_setup.html')

@app.route('/checkout/<plan_id>')
def checkout(plan_id):
    if plan_id not in PLANS:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('select_plan'))
    
    plan = PLANS[plan_id]
    return render_template('checkout.html',
                         plan_id=plan_id,
                         plan_name=plan['name'],
                         plan_price=plan['price'] / 100,  # Convert cents to dollars
                         stripe_public_key=os.environ.get('STRIPE_PUBLISHABLE_KEY'))

@app.route('/create-payment', methods=['POST'])
def create_payment():
    try:
        data = request.json
        plan_id = data.get('plan_id')
        payment_method_id = data.get('payment_method_id')
        user_info = data.get('user_info', {})

        if not all([
            user_info.get('full_name'),
            user_info.get('email'),
            user_info.get('address', {}).get('street'),
            user_info.get('address', {}).get('city'),
            user_info.get('address', {}).get('state'),
            user_info.get('address', {}).get('zip_code'),
            user_info.get('address', {}).get('country')
        ]):
            return jsonify({'error': 'Missing required user information'}), 400

        if plan_id not in PLANS:
            return jsonify({'error': 'Invalid plan'}), 400

        plan = PLANS[plan_id]
        
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
                'phone': user_info.get('phone', ''),
                'address_street': user_info['address']['street'],
                'address_city': user_info['address']['city'],
                'address_state': user_info['address']['state'],
                'address_zip': user_info['address']['zip_code'],
                'address_country': user_info['address']['country']
            }
        )

        # Record the payment
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

        if intent.status == 'requires_action':
            return jsonify({
                'requires_action': True,
                'client_secret': intent.client_secret
            })
        
        if intent.status == 'succeeded':
            return jsonify({'success': True})

        return jsonify({'error': 'Payment failed'}), 400

    except stripe.error.CardError as e:
        return jsonify({'error': str(e.error.message)}), 400
    except Exception as e:
        return jsonify({'error': 'An error occurred processing your payment'}), 400

@app.route('/payment-status')
def payment_status():
    status = request.args.get('status', 'failed')
    return render_template('payment_status.html', status=status)

@app.route('/legal-stuff', methods=['GET', 'POST'])
def legal_stuff():
    form = TermsAcceptanceForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('Please fill in all required fields correctly', 'error')
            return render_template('legal_stuff.html', form=form)
        
        if form.accept_terms.data:
            # Record the terms acceptance
            terms_acceptance = TermsAcceptance(
                user_email=form.email.data,
                ip_address=request.remote_addr,
                terms_version='1.0'  # You can update this based on your terms versioning
            )
            try:
                db.session.add(terms_acceptance)
                db.session.commit()
                flash('Terms accepted successfully!', 'success')
                return redirect(url_for('account_setup'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while processing your request. Please try again.', 'error')
                return render_template('legal_stuff.html', form=form)
        return redirect(url_for('terms_declined'))
    return render_template('legal_stuff.html', form=form)

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/refund-policy')
def refund_policy():
    return render_template('refund_policy.html')

@app.route('/legal-disclaimer')
def legal_disclaimer():
    return render_template('disclaimer.html')

@app.route('/terms-declined')
def terms_declined():
    return render_template('terms_declined.html')

@app.route('/download-terms-pdf')
def download_terms_pdf():
    # Generate PDF from the terms of service template
    html = render_template('terms_of_service.html', download_mode=True)
    pdf = weasyprint.HTML(string=html).write_pdf()
    
    # Create a BytesIO object to store the PDF
    pdf_buffer = io.BytesIO(pdf)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        download_name='LeaseCheck-Terms-of-Service.pdf',
        mimetype='application/pdf',
        as_attachment=True
    )
