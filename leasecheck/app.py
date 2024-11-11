from flask import Flask, render_template
import os
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import logging
from .database import init_db, db
from .cache import init_cache, cache

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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///leasecheck.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'max_overflow': 10,
        'echo': True if app.debug else False,
        'echo_pool': True if app.debug else False
    }

    # Static files configuration
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache
    app.config['STATIC_FOLDER'] = 'static'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['TEMPLATE_FOLDER'] = 'templates'  # Fixed template folder name
    
    # Initialize extensions with app
    csrf.init_app(app)
    
    try:
        init_db(app)
        init_cache(app)
        logger.info("Database and cache initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application components: {str(e)}")
        raise

    # Configure security headers with Talisman
    csp = {
        'default-src': ["'self'", "https://*"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "https://js.stripe.com",
            "https://*"
        ],
        'style-src': ["'self'", "'unsafe-inline'", "https://*"],
        'img-src': ["'self'", "data:", "https:", "https://*"],
        'connect-src': [
            "'self'",
            "https://api.stripe.com",
            "https://*",
            "wss://*"
        ],
        'frame-src': [
            "'self'",
            "https://js.stripe.com",
            "https://hooks.stripe.com",
            "https://*"
        ],
        'font-src': ["'self'", "data:", "https://*"]
    }

    Talisman(
        app,
        content_security_policy=csp,
        force_https=False,  # Set to False for development
        strict_transport_security=False,  # Disabled for development
        session_cookie_secure=False  # Disabled for development
    )

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Import and register blueprints
    from .routes import bp
    app.register_blueprint(bp)
    
    return app

__all__ = ['create_app', 'db', 'cache']
