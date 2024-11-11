from flask_sqlalchemy import SQLAlchemy
import logging
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError, DBAPIError
from functools import wraps
from contextlib import contextmanager
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

def retry_on_operational_error(max_retries=3, delay=1):
    """Decorator to retry database operations on operational errors"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                        verify_db_connection()  # Verify connection before retry
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error in database operation: {str(e)}")
                    raise
            logger.error(f"Database operation failed after {max_retries} attempts: {str(last_error)}")
            raise DatabaseError(f"Operation failed after {max_retries} retries: {str(last_error)}")
        return wrapper
    return decorator

@contextmanager
def safe_transaction():
    """Context manager for safe database transactions with automatic rollback"""
    try:
        yield db.session
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Integrity Error in database transaction: {str(e)}")
        raise DatabaseError(f"Database integrity error: {str(e)}")
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"Operational Error in database transaction: {str(e)}")
        raise DatabaseError(f"Database operational error: {str(e)}")
    except DBAPIError as e:
        db.session.rollback()
        logger.error(f"Database API Error in transaction: {str(e)}")
        raise DatabaseError(f"Database connection error: {str(e)}")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database Error in transaction: {str(e)}")
        raise DatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in database transaction: {str(e)}")
        raise
    finally:
        db.session.close()

def init_db(app):
    """Initialize database with proper configuration and error handling"""
    try:
        # Initialize the db with the app
        db.init_app(app)
        logger.info("Database initialization successful")
        
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Verify database connection
            verify_db_connection()
            logger.info("Database connection verified successfully")
            
    except OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise DatabaseError(f"Failed to connect to database: {str(e)}")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise DatabaseError(f"Failed to initialize database: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        raise

@retry_on_operational_error(max_retries=5, delay=2)
def verify_db_connection():
    """Verify database connection with retry logic"""
    try:
        engine = db.engine
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.commit()
    except Exception as e:
        logger.error(f"Failed to verify database connection: {str(e)}")
        raise

def cleanup_idle_connections():
    """Clean up idle database connections"""
    try:
        engine = db.engine
        if hasattr(engine, 'dispose'):
            engine.dispose()
            logger.info("Successfully cleaned up idle database connections")
    except Exception as e:
        logger.error(f"Error cleaning up idle connections: {str(e)}")

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite specific configurations if using SQLite"""
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def get_db():
    """Helper function to get database instance"""
    return db
