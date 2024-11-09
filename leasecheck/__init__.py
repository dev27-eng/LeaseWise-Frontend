from flask import Flask
import os
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-key-for-testing")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SERVER_NAME'] = None

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

# Configure security headers with Talisman
csp = {
    'default-src': ["'self'", "https://*"],
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://js.stripe.com", "https://*"],
    'style-src': ["'self'", "'unsafe-inline'", "https://*"],
    'img-src': ["'self'", "data:", "https:", "https://*"],
    'connect-src': ["'self'", "https://api.stripe.com", "https://*", "wss://*"],
    'frame-src': ["'self'", "https://js.stripe.com", "https://hooks.stripe.com", "https://*"],
    'font-src': ["'self'", "data:", "https://*"]
}

talisman = Talisman(
    app,
    content_security_policy=csp,
    force_https=True
)

# Create all database tables
with app.app_context():
    db.create_all()

# Import routes after app is created to avoid circular imports
from . import routes
