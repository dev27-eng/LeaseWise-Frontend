from flask import render_template
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
