from flask import Flask
import os
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import logging
from .database import init_db, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
csrf = CSRFProtect()

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-key-for-testing")
    
    # Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'max_overflow': 10,
        'echo': True if app.debug else False,
        'echo_pool': True if app.debug else False
    }
    app.config['SERVER_NAME'] = None

    # Initialize extensions with app
    csrf.init_app(app)
    
    try:
        init_db(app)
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

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

    # Import and register blueprints
    from .routes import bp
    app.register_blueprint(bp, url_prefix='')
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
