from flask import render_template, redirect, url_for, flash, request
from . import app
from .forms import TermsAcceptanceForm

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

@app.route('/legal-stuff', methods=['GET', 'POST'])
def legal_stuff():
    form = TermsAcceptanceForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('You must accept the terms to continue', 'error')
            return render_template('legal_stuff.html', form=form)
        
        if form.accept_terms.data:
            flash('Terms accepted successfully!', 'success')
            return redirect(url_for('account_setup'))
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
