from flask import Flask
import os
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "dev-key-for-testing")
csrf = CSRFProtect(app)

# Import routes after app is created to avoid circular imports
from . import routes
