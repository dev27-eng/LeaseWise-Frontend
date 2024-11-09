from flask import render_template, redirect, url_for, flash, request, send_file, jsonify, session
from . import app, db
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("Stripe API key is not set!")

# File upload configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/lease-upload')
def lease_upload():
    return render_template('lease_upload.html')

@app.route('/upload-lease', methods=['POST'])
def upload_lease():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF, DOC, and DOCX files are allowed.'}), 400

        if file.content_length and file.content_length > MAX_CONTENT_LENGTH:
            return jsonify({'error': 'File size exceeds the maximum limit of 10MB'}), 400

        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create user-specific directory
        user_dir = os.path.join(UPLOAD_FOLDER, session.get('user_email', 'anonymous'))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        file_path = os.path.join(user_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=secure_filename(file.filename),
            mimetype=file.content_type or mimetypes.guess_type(file.filename)[0],
            file_size=os.path.getsize(file_path),
            user_email=session.get('user_email', 'anonymous'),
            file_path=file_path
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'document_id': document.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/documents')
def list_documents():
    user_email = session.get('user_email')
    if not user_email:
        flash('Please log in to view your documents', 'error')
        return redirect(url_for('login'))
        
    documents = Document.query.filter_by(user_email=user_email).order_by(Document.upload_date.desc()).all()
    return render_template('documents.html', documents=documents)

@app.route('/download-document/<int:document_id>')
def download_document(document_id):
    user_email = session.get('user_email')
    if not user_email:
        return jsonify({'error': 'Unauthorized'}), 401
        
    document = Document.query.get_or_404(document_id)
    
    if document.user_email != user_email:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        return send_file(
            document.file_path,
            mimetype=document.mimetype,
            as_attachment=True,
            download_name=document.original_filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

@app.route('/submit-support-ticket', methods=['POST'])
def submit_support_ticket():
    try:
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({'error': 'Unauthorized'}), 401
            
        data = request.get_json()
        document_id = data.get('document_id')
        issue_type = data.get('issue_type')
        description = data.get('description')
        
        if not all([document_id, issue_type, description]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        document = Document.query.get_or_404(document_id)
        
        if document.user_email != user_email:
            return jsonify({'error': 'Unauthorized'}), 403
            
        support_ticket = SupportTicket(
            document_id=document_id,
            user_email=user_email,
            issue_type=issue_type,
            description=description
        )
        
        db.session.add(support_ticket)
        db.session.commit()
        
        return jsonify({'message': 'Support ticket submitted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error submitting support ticket: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/review-document/<int:document_id>')
def review_document(document_id):
    user_email = session.get('user_email')
    if not user_email:
        flash('Please log in to review documents', 'error')
        return redirect(url_for('login'))
        
    document = Document.query.get_or_404(document_id)
    
    if document.user_email != user_email:
        flash('Unauthorized access', 'error')
        return redirect(url_for('list_documents'))
        
    if document.status != 'processed':
        flash('Document is not ready for review', 'error')
        return redirect(url_for('list_documents'))
        
    return render_template('review_document.html', document=document)
