import os
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
import logging
from werkzeug.utils import secure_filename
import uuid
from jinja2.exceptions import TemplateNotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('main', __name__)

def get_available_components():
    """Get list of available components from the templates directory"""
    components_dir = os.path.join(current_app.root_path, 'templates', 'components')
    components = []
    
    try:
        # Get all subdirectories in the components directory
        for item in os.listdir(components_dir):
            component_path = os.path.join(components_dir, item)
            if os.path.isdir(component_path) and not item.startswith('_'):
                # Check for required component files
                html_file = os.path.join(component_path, f"{item}.html")
                if os.path.exists(html_file):
                    components.append(item)
                    logger.info(f"Found valid component: {item}")
        
        return sorted(components)
    except Exception as e:
        logger.error(f"Error scanning components directory: {str(e)}")
        return []

@bp.route('/')
def index():
    """Landing page route"""
    return render_template('welcome_screen.html')

@bp.route('/onboarding')
def onboarding():
    """Onboarding page route"""
    return render_template('components/onboarding/onboarding.html')

@bp.route('/preview/<component_name>')
def preview_component(component_name):
    """Preview a specific component in isolation"""
    try:
        # Get available components
        available_components = get_available_components()
        
        if not available_components:
            flash('No components available for preview', 'error')
            return redirect(url_for('main.index'))
        
        if component_name not in available_components:
            flash(f'Component "{component_name}" not found', 'error')
            return redirect(url_for('main.preview_component', component_name=available_components[0]))
        
        # Construct paths for component assets
        component_template = f"components/{component_name}/{component_name}.html"
        component_css = f"components/{component_name}/{component_name}.css"
        component_js = f"components/{component_name}/{component_name}.js"
        
        # Check if files exist
        static_folder = os.path.join(current_app.root_path, 'static')
        css_exists = os.path.exists(os.path.join(static_folder, component_css))
        js_exists = os.path.exists(os.path.join(static_folder, component_js))
        
        # Get the port from environment or use default 5000
        port = int(os.environ.get("PORT", 5000))
        
        logger.info(f"Rendering preview for component: {component_name}")
        
        return render_template('preview.html',
                           component_name=component_name,
                           component_template=component_template,
                           component_css=component_css if css_exists else None,
                           component_js=component_js if js_exists else None,
                           available_components=available_components,
                           port=port)
    
    except Exception as e:
        logger.error(f"Error rendering component preview: {str(e)}")
        flash('Error rendering component preview', 'error')
        return redirect(url_for('main.index'))

@bp.route('/preview')
def preview_index():
    """Redirect to the first available component preview"""
    available_components = get_available_components()
    if not available_components:
        flash('No components available for preview', 'error')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.preview_component', component_name=available_components[0]))

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

@bp.route('/admin/settings')
def admin_settings():
    """Admin settings page"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    admin_user = AdminUser.query.get(session['admin_id'])
    return render_template('admin_settings.html', admin_user=admin_user)

@bp.route('/admin/settings/update', methods=['POST'])
def admin_settings_update():
    """Update admin settings"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    admin_user = AdminUser.query.get(session['admin_id'])
    if admin_user:
        admin_user.name = request.form.get('name')
        admin_user.email = request.form.get('email')
        admin_user.password = request.form.get('password')
        db.session.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('main.admin_settings'))
    else:
        flash('Error updating settings', 'error')
        return redirect(url_for('main.admin_settings'))

@bp.route('/admin/users')
def admin_users():
    """Admin users management page"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    users = AdminUser.query.all()
    return render_template('admin_users.html', users=users)

@bp.route('/admin/users/add', methods=['POST'])
def admin_users_add():
    """Add a new admin user"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    if name and email and password:
        new_user = AdminUser(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully', 'success')
        return redirect(url_for('main.admin_users'))
    else:
        flash('Error adding user', 'error')
        return redirect(url_for('main.admin_users'))

@bp.route('/admin/users/delete/<int:user_id>')
def admin_users_delete(user_id):
    """Delete an admin user"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    user = AdminUser.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
        return redirect(url_for('main.admin_users'))
    else:
        flash('Error deleting user', 'error')
        return redirect(url_for('main.admin_users'))

@bp.route('/admin/documents')
def admin_documents():
    """Admin documents management page"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    documents = Document.query.all()
    return render_template('admin_documents.html', documents=documents)

@bp.route('/admin/documents/add', methods=['POST'])
def admin_documents_add():
    """Add a new document"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    document_name = request.form.get('name')
    document_file = request.files.get('file')
    if document_name and document_file:
        if document_file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('main.admin_documents'))
        filename = secure_filename(document_file.filename)
        document_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        new_document = Document(name=document_name, file_path=filename)
        db.session.add(new_document)
        db.session.commit()
        flash('Document added successfully', 'success')
        return redirect(url_for('main.admin_documents'))
    else:
        flash('Error adding document', 'error')
        return redirect(url_for('main.admin_documents'))

@bp.route('/admin/documents/delete/<int:document_id>')
def admin_documents_delete(document_id):
    """Delete a document"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    document = Document.query.get(document_id)
    if document:
        if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], document.file_path)):
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], document.file_path))
        db.session.delete(document)
        db.session.commit()
        flash('Document deleted successfully', 'success')
        return redirect(url_for('main.admin_documents'))
    else:
        flash('Error deleting document', 'error')
        return redirect(url_for('main.admin_documents'))

@bp.route('/admin/support')
def admin_support():
    """Admin support tickets management page"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    tickets = SupportTicket.query.all()
    return render_template('admin_support.html', tickets=tickets)

@bp.route('/admin/support/mark-resolved/<int:ticket_id>')
def admin_support_mark_resolved(ticket_id):
    """Mark a support ticket as resolved"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    ticket = SupportTicket.query.get(ticket_id)
    if ticket:
        ticket.resolved = True
        db.session.commit()
        flash('Ticket marked as resolved', 'success')
        return redirect(url_for('main.admin_support'))
    else:
        flash('Error marking ticket as resolved', 'error')
        return redirect(url_for('main.admin_support'))

@bp.route('/admin/support/delete/<int:ticket_id>')
def admin_support_delete(ticket_id):
    """Delete a support ticket"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    ticket = SupportTicket.query.get(ticket_id)
    if ticket:
        db.session.delete(ticket)
        db.session.commit()
        flash('Ticket deleted successfully', 'success')
        return redirect(url_for('main.admin_support'))
    else:
        flash('Error deleting ticket', 'error')
        return redirect(url_for('main.admin_support'))

@bp.route('/admin/login')
def admin_login():
    """Admin login page"""
    return render_template('admin_login.html')

@bp.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Process admin login"""
    email = request.form.get('email')
    password = request.form.get('password')
    admin_user = AdminUser.query.filter_by(email=email).first()
    if admin_user and admin_user.check_password(password):
        session['admin_id'] = admin_user.id
        flash('Login successful', 'success')
        return redirect(url_for('main.admin_settings'))
    else:
        flash('Invalid email or password', 'error')
        return redirect(url_for('main.admin_login'))

@bp.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))

@bp.route('/documents/<filename>')
def download_document(filename):
    """Download a document"""
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found', 'error')
        return redirect(url_for('main.index'))

@bp.route('/support', methods=['GET', 'POST'])
def support():
    """Support ticket submission page"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        if subject and message:
            new_ticket = SupportTicket(subject=subject, message=message, user_id=session['user_id'])
            db.session.add(new_ticket)
            db.session.commit()
            flash('Ticket submitted successfully', 'success')
            return redirect(url_for('main.support'))
        else:
            flash('Please fill in all fields', 'error')
    return render_template('support.html')

@bp.route('/plans')
def plans():
    """Plans page"""
    return render_template('plans.html', plans=PLANS)

@bp.route('/payment/<plan_name>')
def payment(plan_name):
    """Payment page for a specific plan"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    plan = PLANS.get(plan_name)
    if plan:
        return render_template('payment.html', plan=plan)
    else:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('main.plans'))

@bp.route('/payment/success/<plan_name>')
def payment_success(plan_name):
    """Payment successful page"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    plan = PLANS.get(plan_name)
    if plan:
        new_payment = Payment(user_id=session['user_id'], plan_name=plan_name, amount=plan['price'], timestamp=datetime.now())
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment successful! You can now access your selected plan.', 'success')
        return render_template('payment_success.html', plan=plan)
    else:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('main.plans'))

@bp.route('/payment/cancel')
def payment_cancel():
    """Payment cancelled page"""
    flash('Payment cancelled', 'error')
    return redirect(url_for('main.plans'))

@bp.route('/terms')
def terms():
    """Terms and conditions page"""
    form = TermsAcceptanceForm()
    return render_template('terms.html', form=form)

@bp.route('/terms', methods=['POST'])
def terms_post():
    """Process terms and conditions acceptance"""
    form = TermsAcceptanceForm(request.form)
    if form.validate_on_submit():
        if 'user_id' in session:
            existing_acceptance = TermsAcceptance.query.filter_by(user_id=session['user_id']).first()
            if existing_acceptance:
                flash('You have already accepted the terms', 'info')
                return redirect(url_for('main.index'))
            else:
                new_acceptance = TermsAcceptance(user_id=session['user_id'], timestamp=datetime.now())
                db.session.add(new_acceptance)
                db.session.commit()
                flash('Terms accepted successfully', 'success')
                return redirect(url_for('main.index'))
        else:
            flash('Please login to accept the terms', 'error')
            return redirect(url_for('main.login'))
    else:
        flash('Please accept the terms', 'error')
        return render_template('terms.html', form=form)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign up page"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if name and email and password:
            existing_user = AdminUser.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists', 'error')
                return redirect(url_for('main.signup'))
            else:
                new_user = AdminUser(name=name, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                flash('Signup successful', 'success')
                return redirect(url_for('main.index'))
        else:
            flash('Please fill in all fields', 'error')
    return render_template('signup.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    """Logout"""
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))

@bp.route('/lease-analysis', methods=['GET', 'POST'])
def lease_analysis():
    """Lease analysis page"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('lease_analysis.html')

@bp.route('/lease-analysis/upload', methods=['POST'])
def lease_analysis_upload():
    """Upload lease document for analysis"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        # Process the uploaded file (e.g., send for analysis)
        # ...
        flash('Lease document uploaded successfully', 'success')
        return redirect(url_for('main.lease_analysis'))
    else:
        flash('Please select a file to upload', 'error')
        return redirect(url_for('main.lease_analysis'))

@bp.route('/lease-analysis/result/<filename>')
def lease_analysis_result(filename):
    """Display lease analysis results"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    # Retrieve analysis results from database or cache based on filename
    # ...
    return render_template('lease_analysis_result.html', filename=filename)

@bp.route('/lease-analysis/download/<filename>')
def lease_analysis_download(filename):
    """Download lease analysis results"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found', 'error')
        return redirect(url_for('main.lease_analysis'))