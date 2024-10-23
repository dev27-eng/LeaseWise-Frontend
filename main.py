from flask import Flask, render_template
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

@app.route('/')
def index():
    return render_template('splash_screen.html')

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
