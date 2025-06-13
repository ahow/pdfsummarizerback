from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.services.email_service import EmailService

email_bp = Blueprint('email', __name__)

@email_bp.route('/send-weekly-summary', methods=['POST'])
@login_required
def send_weekly_summary():
    """Send weekly summary email to the current user."""
    try:
        email_service = EmailService()
        success, message = email_service.send_weekly_summary(current_user.id)
        
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to send weekly summary: {str(e)}'}), 500

@email_bp.route('/send-test-email', methods=['POST'])
@login_required
def send_test_email():
    """Send a test email to verify email configuration."""
    try:
        email_service = EmailService()
        
        # Get email address
        email_address = current_user.notification_email or current_user.email
        if not email_address:
            return jsonify({'error': 'No email address configured'}), 400
        
        # Send test email
        subject = "PDF Summarizer - Test Email"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; color: #2563eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Test Email Successful!</h1>
                </div>
                <p>Hello {current_user.username},</p>
                <p>This is a test email to confirm that your email configuration is working correctly.</p>
                <p>You will receive weekly PDF summaries at this email address: <strong>{email_address}</strong></p>
                <p>Best regards,<br>PDF Summarizer Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Test Email Successful!

Hello {current_user.username},

This is a test email to confirm that your email configuration is working correctly.

You will receive weekly PDF summaries at this email address: {email_address}

Best regards,
PDF Summarizer Team
        """
        
        success = email_service.send_email(email_address, subject, html_content, text_content)
        
        if success:
            return jsonify({'message': f'Test email sent successfully to {email_address}'}), 200
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to send test email: {str(e)}'}), 500

@email_bp.route('/send-all-weekly-summaries', methods=['POST'])
@login_required
def send_all_weekly_summaries():
    """Send weekly summary emails to all users (admin function)."""
    try:
        # This could be restricted to admin users only
        email_service = EmailService()
        results = email_service.send_weekly_summaries_to_all_users()
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        return jsonify({
            'message': f'Sent weekly summaries to {successful}/{total} users',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to send weekly summaries: {str(e)}'}), 500

