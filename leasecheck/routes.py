from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, session
from .database import db, safe_transaction, DatabaseError, retry_on_operational_error
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment, AdminUser, Document, SupportTicket
from datetime import datetime, timedelta
import weasyprint
import io
import stripe
import os
import logging
from werkzeug.exceptions import BadRequest
from functools import wraps
from sqlalchemy import func, desc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
import mimetypes

# Plan pricing configuration
PLAN_PRICES = {
    'basic': 9.95,
    'standard': 19.95,
    'premium': 29.95
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("Stripe API key is not set!")

# Create blueprint
bp = Blueprint('main', __name__)

# File upload configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    return render_template('welcome_screen.html')

@bp.route('/onboarding')
def onboarding():
    return render_template('onboarding_screen.html')

@bp.route('/select-plan')
def select_plan():
    return render_template('select_plan.html')

@bp.route('/checkout')
def checkout():
    plan = request.args.get('plan')
    if not plan or plan not in PLAN_PRICES:
        return redirect(url_for('main.select_plan'))
    return render_template('checkout.html', plan=plan, plan_price=PLAN_PRICES[plan])
