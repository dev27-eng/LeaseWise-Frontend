from flask_sqlalchemy import SQLAlchemy
import logging
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize database with proper configuration"""
    try:
        # Initialize the db with the app
        db.init_app(app)
        logger.info("Database initialization successful")
        
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Verify database connection
            engine = db.engine
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                connection.commit()
            logger.info("Database connection verified successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

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
