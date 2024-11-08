from flask import render_template, redirect, url_for, flash, request, send_file
from . import app, db
from .forms import TermsAcceptanceForm
from .models import TermsAcceptance
from datetime import datetime
import weasyprint
import io

@app.route('/')
@app.route('/welcome')
def welcome():
    return render_template('welcome_screen.html')

@app.route('/onboarding')
def onboarding():
    return render_template('onboarding_screen.html')

@app.route('/select-plan')
def select_plan():
    return render_template('select_plan.html')

@app.route('/account-setup')
def account_setup():
    return render_template('account_setup.html')

@app.route('/legal-stuff', methods=['GET', 'POST'])
def legal_stuff():
    form = TermsAcceptanceForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('Please fill in all required fields correctly', 'error')
            return render_template('legal_stuff.html', form=form)
        
        if form.accept_terms.data:
            # Record the terms acceptance
            terms_acceptance = TermsAcceptance(
                user_email=form.email.data,
                ip_address=request.remote_addr,
                terms_version='1.0'  # You can update this based on your terms versioning
            )
            try:
                db.session.add(terms_acceptance)
                db.session.commit()
                flash('Terms accepted successfully!', 'success')
                return redirect(url_for('account_setup'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while processing your request. Please try again.', 'error')
                return render_template('legal_stuff.html', form=form)
        return redirect(url_for('terms_declined'))
    return render_template('legal_stuff.html', form=form)

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/refund-policy')
def refund_policy():
    return render_template('refund_policy.html')

@app.route('/legal-disclaimer')
def legal_disclaimer():
    return render_template('disclaimer.html')

@app.route('/terms-declined')
def terms_declined():
    return render_template('terms_declined.html')

@app.route('/download-terms-pdf')
def download_terms_pdf():
    # Generate PDF from the terms of service template
    html = render_template('terms_of_service.html', download_mode=True)
    pdf = weasyprint.HTML(string=html).write_pdf()
    
    # Create a BytesIO object to store the PDF
    pdf_buffer = io.BytesIO(pdf)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        download_name='LeaseCheck-Terms-of-Service.pdf',
        mimetype='application/pdf',
        as_attachment=True
    )