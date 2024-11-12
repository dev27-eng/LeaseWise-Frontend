from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, session, current_app
from .database import db, safe_transaction, DatabaseError, retry_on_operational_error
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance, Payment, AdminUser, Document, SupportTicket
from .cache import (
    cache, clear_all_caches, clear_cache_by_key, clear_cache_by_pattern,
    clear_user_cache, clear_document_cache, clear_plan_cache, clear_admin_cache,
    get_cache_stats, cached_with_key
)
from datetime import datetime, timedelta
import os
import logging
from werkzeug.utils import secure_filename
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('main', __name__)

# Plan configuration
PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'price': 9.95,
        'features': [
            '1 Lease Analysis',
            'Ideal for single lease review',
            'Risk Analysis Report',
            'PDF Export'
        ]
    },
    'standard': {
        'name': 'Standard Plan',
        'price': 19.95,
        'features': [
            '3 Lease Analyses',
            'Valid for 30 days',
            'Compare Multiple Options',
            'Priority Support'
        ]
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 29.95,
        'features': [
            '6 Lease Analyses',
            'Valid for 30 days',
            'Best value for multiple reviews',
            'Priority Support + Consultation'
        ]
    }
}

# Screen Routes
@bp.route('/')
@cache.cached(timeout=300)
def index():
    """Welcome Screen (1 Welcome.png)"""
    return render_template('components/welcome/welcome.html')

@bp.route('/onboarding')
@cached_with_key('onboarding')
def onboarding():
    """Onboarding Screen (2 On Boarding.png)"""
    return render_template('components/onboarding/onboarding.html')

@bp.route('/select-plan')
@cached_with_key('plan_selection')
def select_plan():
    """Select Plan Screen (3 Select Plan.png)"""
    return render_template('components/select_plan/select_plan.html', plans=PLANS)

@bp.route('/account-setup')
def account_setup():
    """Account Setup Screen (4 Account Setup.png)"""
    return render_template('components/account_setup/account_setup.html')

@bp.route('/legal-stuff')
def legal_stuff():
    """Legal Stuff Screen (5 Legal Stuff.png)"""
    return render_template('components/legal_stuff/legal_stuff.html')

@bp.route('/terms-of-service')
def terms_of_service():
    """Terms of Service Screen (5a Terms of Service.png)"""
    last_updated = datetime.now().strftime("%B %d, %Y")
    return render_template('components/terms_of_service/terms_of_service.html', last_updated=last_updated)

@bp.route('/refund-policy')
def refund_policy():
    """Refund Policy Screen (5b Refund Policy.png)"""
    return render_template('components/refund_policy/refund_policy.html')

@bp.route('/disclaimer')
def disclaimer():
    """Disclaimer Screen (5c Disclaimer.png)"""
    return render_template('components/disclaimer/disclaimer.html')

@bp.route('/terms-declined')
def terms_declined():
    """Terms Declined Screen (5d Terms Declined Screen.png)"""
    return render_template('components/terms_declined/terms_declined.html')

@bp.route('/checkout')
def checkout():
    """Checkout Screen (6 Checkout.png)"""
    plan_id = request.args.get('plan')
    if not plan_id or plan_id not in PLANS:
        return redirect(url_for('main.select_plan'))
    return render_template('components/checkout/checkout.html', plan=PLANS[plan_id], plan_id=plan_id)

@bp.route('/payment-status')
def payment_status():
    """Payment Status Screen (7 Payment Status.png)"""
    status = request.args.get('status', 'success')
    return render_template('components/payment_status/payment_status.html', status=status)

@bp.route('/lease-upload')
def lease_upload():
    """Lease Upload Screen (8 Lease Upload.png)"""
    return render_template('components/lease_upload/lease_upload.html')

@bp.route('/lease-details')
def lease_details():
    """Lease Details Screen (9 Lease Details.png)"""
    return render_template('components/lease_details/lease_details.html')

@bp.route('/error-report')
def error_report():
    """Error Report Screen (9a Error Report.png)"""
    return render_template('components/error_report/error_report.html')

@bp.route('/support-issue')
def support_issue():
    """Support Issue Screen (9b Support Issue.png)"""
    return render_template('components/support_issue/support_issue.html')

@bp.route('/reviewing-lease')
def reviewing_lease():
    """Reviewing Lease Screen (10 Reviewing Lease.png)"""
    return render_template('components/reviewing_lease/reviewing_lease.html')

@bp.route('/risk-report')
def risk_report():
    """Risk Report Screen (11 Risk Report.png)"""
    return render_template('components/risk_report/risk_report.html')

@bp.route('/save-report')
def save_report():
    """Save Report Screen (11a Save Report.png)"""
    return render_template('components/save_report/save_report.html')

@bp.route('/report-sent')
def report_sent():
    """Report Sent Screen (11b Report Sent.png)"""
    return render_template('components/report_sent/report_sent.html')

@bp.route('/thank-you')
def thank_you():
    """Thank You Screen (11c Thank You - End.png)"""
    return render_template('components/thank_you/thank_you.html')

@bp.route('/local-attorneys')
def local_attorneys():
    """Local Attorneys Screen (12 Local Attorneys.png)"""
    return render_template('components/local_attorneys/local_attorneys.html')

@bp.route('/lawyer-message-acknowledgment')
def lawyer_message_acknowledgment():
    """Lawyer Message Acknowledgment Screen (12a Lawyer Msg Ack.png)"""
    return render_template('components/lawyer_message_acknowledgment/lawyer_message_acknowledgment.html')

# API Routes
@bp.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    email = request.json.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    verification_code = ''.join([str(uuid.uuid4())[:6]])
    # TODO: Implement email sending logic
    return jsonify({'message': 'Verification code sent'})

@bp.route('/api/verify-code', methods=['POST'])
def verify_code():
    code = request.json.get('code')
    if not code:
        return jsonify({'error': 'Verification code is required'}), 400
    # TODO: Implement verification logic
    return jsonify({'message': 'Code verified successfully'})

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# File upload route from original code (not removed)
@bp.route('/upload-lease', methods=['POST'])
def upload_lease():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{str(uuid.uuid4())}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        try:
            file.save(file_path)
            
            # Save file info to database
            document = Document(
                original_filename=filename,
                stored_filename=unique_filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                upload_date=datetime.utcnow(),
                status='pending'
            )
            db.session.add(document)
            db.session.commit()
            
            return jsonify({
                'message': 'File uploaded successfully',
                'document_id': document.id
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

# File download route
@bp.route('/download-document/<int:document_id>')
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.original_filename
    )

# Allowed file check function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

# Add cache control headers to all responses
@bp.after_request
def add_cache_control(response):
    if request.endpoint != 'static':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# Admin cache routes
@bp.route('/admin/cache')
def admin_cache_dashboard():
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    stats = get_cache_stats()
    return render_template('admin/cache_dashboard.html', stats=stats)

@bp.route('/admin/cache/clear', methods=['POST'])
def admin_clear_cache():
    try:
        cache_type = request.form.get('type', 'all')
        if cache_type == 'all':
            clear_all_caches()
            flash('All caches cleared successfully', 'success')
        elif cache_type == 'user':
            user_email = request.form.get('user_email')
            if user_email:
                clear_user_cache(user_email)
                flash(f'Cache cleared for user: {user_email}', 'success')
        elif cache_type == 'document':
            document_id = request.form.get('document_id')
            if document_id:
                clear_document_cache(document_id)
                flash(f'Cache cleared for document: {document_id}', 'success')
        elif cache_type == 'plan':
            clear_plan_cache()
            flash('Plan cache cleared successfully', 'success')
        elif cache_type == 'admin':
            clear_admin_cache()
            flash('Admin cache cleared successfully', 'success')
    except Exception as e:
        flash(f'Error clearing cache: {str(e)}', 'error')
    return redirect(url_for('main.admin_cache_dashboard'))