import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, session, current_app, make_response
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
from flask_wtf import FlaskForm
from wtforms import FileField, StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('main', __name__)

# Component categories for preview system
COMPONENT_CATEGORIES = {
    'primary': [
        {'id': 'welcome', 'name': '1. Welcome'},
        {'id': 'onboarding', 'name': '2. Onboarding'},
        {'id': 'select_plan', 'name': '3. Select Plan'},
        {'id': 'account_setup', 'name': '4. Account Setup'},
        {'id': 'legal_stuff', 'name': '5. Legal Stuff'},
        {'id': 'checkout', 'name': '6. Checkout'},
        {'id': 'payment_status', 'name': '7. Payment Status'},
        {'id': 'lease_upload', 'name': '8. Lease Upload'},
        {'id': 'lease_details', 'name': '9. Lease Details'},
        {'id': 'reviewing_lease', 'name': '10. Reviewing Lease'},
        {'id': 'risk_report', 'name': '11. Risk Report'},
        {'id': 'local_attorneys', 'name': '12. Local Attorneys'}
    ],
    'supporting': [
        {'id': 'terms_of_service', 'name': 'Terms of Service'},
        {'id': 'refund_policy', 'name': 'Refund Policy'},
        {'id': 'disclaimer', 'name': 'Disclaimer'},
        {'id': 'terms_declined', 'name': 'Terms Declined'},
        {'id': 'save_report', 'name': 'Save Report'},
        {'id': 'report_sent', 'name': 'Report Sent'},
        {'id': 'thank_you', 'name': 'Thank You'},
        {'id': 'lawyer_message_acknowledgment', 'name': 'Lawyer Message Acknowledgment'},
        {'id': 'error_report', 'name': 'Error Report'},
        {'id': 'support_issue', 'name': 'Support Issue'}
    ]
}

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

# Add Form classes
class LeaseUploadForm(FlaskForm):
    lease_file = FileField('Lease File', validators=[DataRequired()])
    csrf_token = StringField()

@bp.route('/')
def index():
    """Landing page route"""
    try:
        response = make_response(render_template('components/welcome/welcome.html'))
        return add_security_headers(response)
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return "Error loading page", 500

@bp.route('/onboarding')
def onboarding():
    """Onboarding page route"""
    response = make_response(render_template('components/onboarding/onboarding.html'))
    return add_security_headers(response)

@bp.route('/select-plan')
def select_plan():
    """Select plan page route"""
    response = make_response(render_template('components/select_plan/select_plan.html', plans=PLANS))
    return add_security_headers(response)

@bp.route('/account-setup')
def account_setup():
    """Account setup page route"""
    response = make_response(render_template('components/account_setup/account_setup.html'))
    return add_security_headers(response)

@bp.route('/preview/<component_name>')
def preview_component(component_name):
    """Preview a specific component in isolation"""
    try:
        # Get available components
        available_components = COMPONENT_CATEGORIES
        
        if not available_components['primary'] and not available_components['supporting']:
            flash('No components available for preview', 'error')
            return redirect(url_for('main.index'))
        
        # Check if component exists
        component_exists = False
        component_data = None
        for category in available_components.values():
            for comp in category:
                if comp['id'] == component_name:
                    component_exists = True
                    component_data = comp
                    break
            if component_exists:
                break
        
        if not component_exists:
            flash(f'Component "{component_name}" not found', 'error')
            return redirect(url_for('main.index'))
        
        # Construct paths for component assets
        component_template = f"components/{component_name}/{component_name}.html"
        component_css = f"components/{component_name}/{component_name}.css"
        component_js = f"components/{component_name}/{component_name}.js"
        
        # Get the port from environment or use default 5000
        port = int(os.environ.get("PORT", 5000))
        
        logger.info(f"Rendering preview for component: {component_name}")
        
        # Add mock data for specific components
        extra_data = {}
        if component_name == 'select_plan':
            extra_data['plans'] = PLANS
        elif component_name == 'lease_upload':
            extra_data['form'] = LeaseUploadForm()
        elif component_name == 'lease_details':
            extra_data.update({
                'document': {
                    'filename': 'sample_lease.pdf',
                    'upload_date': datetime.now(),
                    'file_size': '2.5 MB'
                },
                'lease_details': {
                    'property_address': '123 Sample St, San Francisco, CA 94105',
                    'lease_term': '12 months',
                    'monthly_rent': '2,500',
                    'security_deposit': '3,750'
                },
                'status': 'Under Review'
            })
        elif component_name == 'error_report':
            extra_data.update({
                'error_count': 5,
                'critical_errors': 2,
                'warnings': 2,
                'suggestions': 1,
                'errors': [
                    {
                        'id': 1,
                        'severity': 'critical',
                        'title': 'Missing Security Deposit Terms',
                        'description': 'The lease agreement does not specify security deposit terms.',
                        'recommendation': 'Add clear security deposit terms including amount and return conditions.'
                    },
                    {
                        'id': 2,
                        'severity': 'warning',
                        'title': 'Unclear Maintenance Responsibilities',
                        'description': 'Maintenance responsibilities are not clearly defined.',
                        'recommendation': 'Specify which maintenance tasks are tenant vs landlord responsibilities.'
                    }
                ]
            })
        elif component_name == 'thank_you':
            extra_data.update({
                'message': 'Thank you for using our service!',
                'next_steps': [
                    'Check your email for the report',
                    'Review our recommendations',
                    'Contact a local attorney if needed'
                ]
            })
        elif component_name == 'lawyer_message_acknowledgment':
            extra_data.update({
                'attorney': {
                    'name': 'Law Office of John Doe',
                    'contact': 'contact@johndoelaw.example.com',
                    'message': 'Your message has been sent to the attorney.'
                }
            })
        
        response = make_response(render_template(
            'preview.html',
            component_name=component_name,
            component_template=component_template,
            component_css=component_css,
            component_js=component_js,
            available_components=available_components,
            port=port,
            **extra_data
        ))
        
        return add_security_headers(response)
    
    except TemplateNotFound as e:
        logger.error(f"Template not found: {str(e)}")
        flash('Component template not found', 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Error rendering component preview: {str(e)}")
        flash('Error rendering component preview', 'error')
        return redirect(url_for('main.index'))

# Add new routes for Review Flow Components
@bp.route('/save-report', methods=['GET', 'POST'])
def save_report():
    """Save report page route"""
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        # TODO: Implement report saving logic
        return jsonify({'success': True, 'message': 'Report saved successfully'})
    response = make_response(render_template('components/save_report/save_report.html'))
    return add_security_headers(response)

@bp.route('/report-sent')
def report_sent():
    """Report sent confirmation page route"""
    response = make_response(render_template('components/report_sent/report_sent.html'))
    return add_security_headers(response)

@bp.route('/thank-you')
def thank_you():
    """Thank you page route"""
    extra_data = {
        'message': 'Thank you for using our service!',
        'next_steps': [
            'Check your email for the report',
            'Review our recommendations',
            'Contact a local attorney if needed'
        ]
    }
    response = make_response(render_template('components/thank_you/thank_you.html', **extra_data))
    return add_security_headers(response)

@bp.route('/legal-stuff')
def legal_stuff():
    """Legal information page route"""
    response = make_response(render_template('components/legal_stuff/legal_stuff.html'))
    return add_security_headers(response)

@bp.route('/preview/legal_stuff')
def preview_legal_stuff():
    """Preview the legal_stuff component"""
    response = make_response(render_template('preview.html',
                           component_name='legal_stuff',
                           component_template='components/legal_stuff/legal_stuff.html',
                           available_components=get_available_components()))
    return add_security_headers(response)

@bp.route('/admin/settings')
def admin_settings():
    """Admin settings page"""
    if 'admin_id' not in session:
        return redirect(url_for('main.login'))
    admin_user = AdminUser.query.get(session['admin_id'])
    response = make_response(render_template('admin_settings.html', admin_user=admin_user))
    return add_security_headers(response)

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
    response = make_response(render_template('admin_users.html', users=users))
    return add_security_headers(response)

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
    response = make_response(render_template('admin_documents.html', documents=documents))
    return add_security_headers(response)

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
    response = make_response(render_template('admin_support.html', tickets=tickets))
    return add_security_headers(response)

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
    response = make_response(render_template('admin_login.html'))
    return add_security_headers(response)

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
    response = make_response(render_template('support.html'))
    return add_security_headers(response)

@bp.route('/plans')
def plans():
    """Plans page"""
    response = make_response(render_template('plans.html', plans=PLANS))
    return add_security_headers(response)

@bp.route('/payment/<plan_name>')
def payment(plan_name):
    """Payment page for a specific plan"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    plan = PLANS.get(plan_name)
    if plan:
        response = make_response(render_template('payment.html', plan=plan))
        return add_security_headers(response)
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
        response = make_response(render_template('payment_success.html', plan=plan))
        return add_security_headers(response)
    else:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('main.plans'))

@bp.route('/checkout')
def checkout():
    """Checkout page route"""
    plan_id = request.args.get('plan')
    if not plan_id or plan_id not in PLANS:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('main.select_plan'))
    
    plan = PLANS[plan_id]
    response = make_response(render_template('components/checkout/checkout.html', plan=plan))
    return add_security_headers(response)

@bp.route('/payment/cancel')
def payment_cancel():
    """Payment cancelled page"""
    flash('Payment cancelled', 'error')
    return redirect(url_for('main.plans'))

@bp.route('/terms')
def terms():
    """Terms and conditions page"""
    form = TermsAcceptanceForm()
    response = make_response(render_template('terms.html', form=form))
    return add_security_headers(response)

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
    response = make_response(render_template('signup.html'))
    return add_security_headers(response)

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
    response = make_response(render_template('login.html'))
    return add_security_headers(response)

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
    response = make_response(render_template('lease_analysis.html'))
    return add_security_headers(response)

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
    response = make_response(render_template('lease_analysis_result.html', filename=filename))
    return add_security_headers(response)

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

def get_component_info(component_name):
    """Get information about a specific component"""
    for category in COMPONENT_CATEGORIES.values():
        for component in category:
            if component['id'] == component_name:
                return component
    return None

def get_available_components():
    """Get list of available components from the templates directory"""
    components_dir = os.path.join(current_app.root_path, 'templates', 'components')
    components = {'primary': [], 'supporting': []}
    
    try:
        # Get all subdirectories in the components directory
        for item in os.listdir(components_dir):
            component_path = os.path.join(components_dir, item)
            if os.path.isdir(component_path) and not item.startswith('_'):
                # Check for required component files
                html_file = os.path.join(component_path, f"{item}.html")
                if os.path.exists(html_file):
                    # Determine category
                    is_primary = any(comp['id'] == item for comp in COMPONENT_CATEGORIES['primary'])
                    category = 'primary' if is_primary else 'supporting'
                    components[category].append({
                        'id': item,
                        'name': get_component_info(item)['name'] if get_component_info(item) else item
                    })
                    logger.info(f"Found valid component: {item} in category {category}")
        
        return components
    except Exception as e:
        logger.error(f"Error scanning components directory: {str(e)}")
        return {'primary': [], 'supporting': []}

def add_security_headers(response):
    """Add security headers to response"""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

@bp.route('/preview')
def preview_index():
    """Redirect to the first available component preview"""
    try:
        available_components = get_available_components()
        if not available_components['primary'] and not available_components['supporting']:
            flash('No components available for preview', 'error')
            return redirect(url_for('main.index'))
        
        first_component = (available_components['primary'][0]['id'] 
                         if available_components['primary'] 
                         else available_components['supporting'][0]['id'])
        
        return redirect(url_for('main.preview_component', component_name=first_component))
    except Exception as e:
        logger.error(f"Error in preview index: {str(e)}")
        flash('Error accessing preview system', 'error')
        return redirect(url_for('main.index'))