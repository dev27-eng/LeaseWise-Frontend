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
    'default-src': "'self'",
    'script-src': [
        "'self'",
        'https://js.stripe.com',
        "'unsafe-inline'"  # Required for Stripe.js
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'"  # Required for dynamic styles
    ],
    'frame-src': [
        "'self'",
        'https://js.stripe.com',
        'https://hooks.stripe.com'
    ],
    'img-src': ["'self'", 'data:', 'https:'],
    'connect-src': [
        "'self'",
        'https://api.stripe.com'
    ]
}

Talisman(app, content_security_policy=csp, force_https=False)

# Create all database tables
with app.app_context():
    db.create_all()

# Import routes after app is created to avoid circular imports
from . import routes
