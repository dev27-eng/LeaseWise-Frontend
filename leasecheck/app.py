from flask import Flask
import os
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-key-for-testing")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SERVER_NAME'] = None

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)

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

    Talisman(
        app,
        content_security_policy=csp,
        force_https=True
    )

    with app.app_context():
        # Import models to ensure they're known to Flask-SQLAlchemy
        from . import models
        
        # Create all database tables
        try:
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

        # Import and register routes
        from . import routes
        
        return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
