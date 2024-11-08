from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__, 
    template_folder='leasecheck/templates',
    static_folder='leasecheck/static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

@app.route('/')
def index():
    return render_template('welcome_screen.html')

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

@app.route('/handle-terms/<action>')
def handle_terms(action):
    if action == 'accept':
        # For now, redirect to welcome page on acceptance
        return redirect(url_for('welcome'))
    else:
        return redirect(url_for('terms_declined'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
