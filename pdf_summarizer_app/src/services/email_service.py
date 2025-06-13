import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from src.models.pdf_summary import PDFSummary
from src.models.user import User

class EmailService:
    def __init__(self):
        # Email configuration - these should be set as environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send an email with HTML content."""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_address
            message["To"] = to_email
            
            # Create text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, message.as_string())
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def generate_weekly_summary_html(self, user, summaries):
        """Generate HTML content for weekly summary email."""
        week_start = datetime.now() - timedelta(days=7)
        week_end = datetime.now()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly PDF Summary</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2563eb;
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    color: #6b7280;
                    margin: 10px 0 0 0;
                    font-size: 16px;
                }}
                .summary-card {{
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 20px;
                    margin-bottom: 20px;
                    background-color: #fafafa;
                }}
                .summary-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1f2937;
                    margin-bottom: 8px;
                }}
                .summary-meta {{
                    font-size: 14px;
                    color: #6b7280;
                    margin-bottom: 12px;
                }}
                .summary-content {{
                    font-size: 15px;
                    color: #374151;
                    margin-bottom: 15px;
                    line-height: 1.5;
                }}
                .key-messages {{
                    background-color: #eff6ff;
                    border-left: 4px solid #2563eb;
                    padding: 12px;
                    margin: 12px 0;
                }}
                .key-messages h4 {{
                    margin: 0 0 8px 0;
                    color: #1e40af;
                    font-size: 14px;
                    font-weight: 600;
                }}
                .key-messages ul {{
                    margin: 0;
                    padding-left: 16px;
                }}
                .key-messages li {{
                    font-size: 14px;
                    color: #1e40af;
                    margin-bottom: 4px;
                }}
                .view-link {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                .view-link:hover {{
                    background-color: #1d4ed8;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 14px;
                }}
                .no-summaries {{
                    text-align: center;
                    padding: 40px 20px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 Weekly PDF Summary</h1>
                    <p>Your document analysis report for {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}</p>
                </div>
                
                <p>Hello {user.username},</p>
                <p>Here's your weekly summary of PDF documents that were processed in the last 7 days:</p>
        """
        
        if not summaries:
            html_content += """
                <div class="no-summaries">
                    <h3>No new documents this week</h3>
                    <p>No PDF files were added or processed in the past week. Upload new documents or scan your Google Drive to get started!</p>
                </div>
            """
        else:
            html_content += f"<p><strong>{len(summaries)} document(s)</strong> were processed this week:</p>"
            
            for summary in summaries:
                key_messages_html = ""
                if summary.key_messages:
                    messages = [msg.strip() for msg in summary.key_messages.split('\n') if msg.strip()]
                    if messages:
                        key_messages_html = """
                        <div class="key-messages">
                            <h4>🔑 Key Messages:</h4>
                            <ul>
                        """
                        for message in messages[:3]:  # Show only first 3 key messages
                            key_messages_html += f"<li>{message}</li>"
                        key_messages_html += "</ul></div>"
                
                html_content += f"""
                <div class="summary-card">
                    <div class="summary-title">{summary.title}</div>
                    <div class="summary-meta">
                        📅 Added: {summary.date_added.strftime('%B %d, %Y at %I:%M %p')}
                    </div>
                    <div class="summary-content">
                        <strong>Summary:</strong><br>
                        {summary.summary}
                    </div>
                    {key_messages_html}
                    <a href="{summary.google_drive_link}" class="view-link" target="_blank">View in Google Drive</a>
                </div>
                """
        
        html_content += f"""
                <div class="footer">
                    <p>This email was sent to {user.notification_email or user.email}</p>
                    <p>PDF Summarizer - AI-Powered Document Analysis</p>
                    <p><em>Automatically generated on {datetime.now().strftime('%B %d, %Y')}</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_weekly_summary_text(self, user, summaries):
        """Generate plain text content for weekly summary email."""
        week_start = datetime.now() - timedelta(days=7)
        week_end = datetime.now()
        
        text_content = f"""
Weekly PDF Summary
{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}

Hello {user.username},

Here's your weekly summary of PDF documents that were processed in the last 7 days:
        """
        
        if not summaries:
            text_content += """
No new documents this week

No PDF files were added or processed in the past week. Upload new documents or scan your Google Drive to get started!
            """
        else:
            text_content += f"\n{len(summaries)} document(s) were processed this week:\n\n"
            
            for i, summary in enumerate(summaries, 1):
                text_content += f"""
{i}. {summary.title}
   Added: {summary.date_added.strftime('%B %d, %Y at %I:%M %p')}
   
   Summary: {summary.summary}
   
"""
                if summary.key_messages:
                    messages = [msg.strip() for msg in summary.key_messages.split('\n') if msg.strip()]
                    if messages:
                        text_content += "   Key Messages:\n"
                        for message in messages[:3]:
                            text_content += f"   • {message}\n"
                        text_content += "\n"
                
                text_content += f"   View: {summary.google_drive_link}\n\n"
        
        text_content += f"""
---
This email was sent to {user.notification_email or user.email}
PDF Summarizer - AI-Powered Document Analysis
Automatically generated on {datetime.now().strftime('%B %d, %Y')}
        """
        
        return text_content
    
    def send_weekly_summary(self, user_id):
        """Send weekly summary email to a specific user."""
        try:
            # Get user
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Get email address
            email_address = user.notification_email or user.email
            if not email_address:
                return False, "No email address configured"
            
            # Get summaries from the last week
            week_ago = datetime.now() - timedelta(days=7)
            summaries = PDFSummary.query.filter(
                PDFSummary.user_id == user_id,
                PDFSummary.date_added >= week_ago
            ).order_by(PDFSummary.date_added.desc()).all()
            
            # Generate email content
            subject = f"Weekly PDF Summary - {len(summaries)} document(s) processed"
            html_content = self.generate_weekly_summary_html(user, summaries)
            text_content = self.generate_weekly_summary_text(user, summaries)
            
            # Send email
            success = self.send_email(email_address, subject, html_content, text_content)
            
            if success:
                return True, f"Weekly summary sent to {email_address}"
            else:
                return False, "Failed to send email"
                
        except Exception as e:
            return False, f"Error sending weekly summary: {str(e)}"
    
    def send_weekly_summaries_to_all_users(self):
        """Send weekly summary emails to all users."""
        users = User.query.all()
        results = []
        
        for user in users:
            success, message = self.send_weekly_summary(user.id)
            results.append({
                'user_id': user.id,
                'username': user.username,
                'success': success,
                'message': message
            })
        
        return results

