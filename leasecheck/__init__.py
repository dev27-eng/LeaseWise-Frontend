from flask import Flask
import os
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-key-for-testing")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

# Configure security headers with Talisman
csp = {
    'default-src': ["'self'", "*.replit.dev", "https://*.stripe.com"],
    'script-src': [
        "'self'",
        "*.replit.dev",
        'https://js.stripe.com',
        "'unsafe-inline'",
        "'unsafe-eval'"
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        "*.replit.dev"
    ],
    'frame-src': [
        "'self'",
        'https://js.stripe.com',
        'https://hooks.stripe.com',
        "*.replit.dev"
    ],
    'img-src': ["'self'", 'data:', 'https:', "*.replit.dev"],
    'connect-src': [
        "'self'",
        'https://api.stripe.com',
        'https://js.stripe.com',
        "*.replit.dev"
    ],
    'font-src': ["'self'", 'data:', "*.replit.dev"]
}

Talisman(app, 
         content_security_policy=csp,
         content_security_policy_nonce_in=['script-src'],
         force_https=False)

# Create all database tables
with app.app_context():
    db.create_all()

# Import routes after app is created to avoid circular imports
from . import routes
