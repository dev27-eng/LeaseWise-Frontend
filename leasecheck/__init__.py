from flask import Flask
import os
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-key-for-testing")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

# Create all database tables
with app.app_context():
    db.create_all()

# Import routes after app is created to avoid circular imports
from . import routes
