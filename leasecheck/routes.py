from flask import render_template, redirect, url_for
from . import app

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

@app.route('/legal-stuff')
def legal_stuff():
    return render_template('legal_stuff.html')

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

# Add routes for handling terms acceptance/rejection
@app.route('/handle-terms/<action>')
def handle_terms(action):
    if action == 'accept':
        # In the next step, we'll implement proper tracking in the database
        return redirect(url_for('welcome'))
    else:
        return redirect(url_for('terms_declined'))
