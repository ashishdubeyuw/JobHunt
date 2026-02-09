"""
Notification Module
Email and WhatsApp notification handlers
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


def send_email_notification(
    to_email: str,
    matched_jobs: List[Dict],
    subject: str = "🎯 New Job Matches Found!",
    from_email: Optional[str] = None,
    app_password: Optional[str] = None
) -> bool:
    """
    Send email notification with matched jobs.
    
    Args:
        to_email: Recipient email address
        matched_jobs: List of matched job dictionaries
        subject: Email subject line
        from_email: Sender email (uses env var if not provided)
        app_password: Gmail app password (uses env var if not provided)
        
    Returns:
        True if email sent successfully
    """
    from_email = from_email or os.getenv("GMAIL_ADDRESS")
    app_password = app_password or os.getenv("GMAIL_APP_PASSWORD")
    
    if not from_email or not app_password:
        print("⚠️ Gmail credentials not configured")
        return False
    
    try:
        # Create email content
        html_content = _create_email_html(matched_jobs)
        text_content = _create_email_text(matched_jobs)
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, app_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
        print(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


def send_whatsapp_notification(
    to_phone: str,
    matched_jobs: List[Dict],
    account_sid: Optional[str] = None,
    auth_token: Optional[str] = None,
    from_number: Optional[str] = None
) -> bool:
    """
    Send WhatsApp notification with matched jobs via Twilio.
    
    Args:
        to_phone: Recipient phone number (with country code, e.g., +1234567890)
        matched_jobs: List of matched job dictionaries
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        from_number: Twilio WhatsApp number
        
    Returns:
        True if message sent successfully
    """
    if not TWILIO_AVAILABLE:
        print("⚠️ Twilio library not installed")
        return False
    
    account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
    from_number = from_number or os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    
    if not account_sid or not auth_token:
        print("⚠️ Twilio credentials not configured")
        return False
    
    try:
        client = TwilioClient(account_sid, auth_token)
        
        # Format phone number for WhatsApp
        to_whatsapp = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
        
        # Create message content
        message_body = _create_whatsapp_message(matched_jobs)
        
        # Send message
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_whatsapp
        )
        
        print(f"✅ WhatsApp message sent: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp sending failed: {e}")
        return False


def _create_email_html(jobs: List[Dict]) -> str:
    """Create HTML email content."""
    job_cards = ""
    for i, job in enumerate(jobs[:5], 1):
        score = job.get("score", job.get("final_score", 0))
        score_pct = int(score * 100) if score <= 1 else int(score)
        
        # Color based on score
        if score_pct >= 80:
            color = "#22c55e"
            badge = "Excellent Match"
        elif score_pct >= 60:
            color = "#3b82f6"
            badge = "Good Match"
        else:
            color = "#f59e0b"
            badge = "Partial Match"
        
        job_cards += f"""
        <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="margin: 0 0 4px 0; color: #1f2937;">{i}. {job.get('title', 'Position')}</h3>
                    <p style="margin: 0; color: #6b7280;">{job.get('company', 'Company')} • {job.get('location', 'Location')}</p>
                </div>
                <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600;">
                    {score_pct}% {badge}
                </span>
            </div>
            <p style="margin: 12px 0; color: #374151; font-size: 14px;">
                {job.get('salary', 'Salary not specified')}
            </p>
            <a href="{job.get('apply_url', '#')}" 
               style="display: inline-block; background-color: #4f46e5; color: white; text-decoration: none; 
                      padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                Apply Now →
            </a>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                 background-color: #f3f4f6; padding: 20px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); 
                        padding: 32px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🎯 New Job Matches!</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">
                    We found {len(jobs)} jobs that match your profile
                </p>
            </div>
            <div style="background-color: #f9fafb; padding: 24px; border-radius: 0 0 12px 12px;">
                {job_cards}
                <p style="text-align: center; color: #6b7280; font-size: 12px; margin-top: 24px;">
                    Powered by Job Matching AI • <a href="#" style="color: #4f46e5;">Manage Preferences</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def _create_email_text(jobs: List[Dict]) -> str:
    """Create plain text email content."""
    lines = ["🎯 NEW JOB MATCHES FOUND!\n", "=" * 40, ""]
    
    for i, job in enumerate(jobs[:5], 1):
        score = job.get("score", job.get("final_score", 0))
        score_pct = int(score * 100) if score <= 1 else int(score)
        
        lines.append(f"{i}. {job.get('title', 'Position')}")
        lines.append(f"   Company: {job.get('company', 'N/A')}")
        lines.append(f"   Location: {job.get('location', 'N/A')}")
        lines.append(f"   Salary: {job.get('salary', 'Not specified')}")
        lines.append(f"   Match Score: {score_pct}%")
        lines.append(f"   Apply: {job.get('apply_url', 'See website')}")
        lines.append("")
    
    lines.append("-" * 40)
    lines.append("Powered by Job Matching AI")
    
    return "\n".join(lines)


def _create_whatsapp_message(jobs: List[Dict]) -> str:
    """Create WhatsApp message content."""
    lines = ["🎯 *New Job Matches Found!*\n"]
    
    for i, job in enumerate(jobs[:5], 1):
        score = job.get("score", job.get("final_score", 0))
        score_pct = int(score * 100) if score <= 1 else int(score)
        
        emoji = "🟢" if score_pct >= 80 else "🔵" if score_pct >= 60 else "🟡"
        
        lines.append(f"{emoji} *{job.get('title', 'Position')}*")
        lines.append(f"   📍 {job.get('company', 'Company')} • {job.get('location', 'Location')}")
        lines.append(f"   💰 {job.get('salary', 'Salary TBD')}")
        lines.append(f"   📊 Match: {score_pct}%")
        lines.append(f"   🔗 {job.get('apply_url', 'Apply on website')}")
        lines.append("")
    
    lines.append("_Powered by Job Matching AI_")
    
    return "\n".join(lines)


def test_email_notification(to_email: str) -> bool:
    """Test email notification setup."""
    test_jobs = [
        {
            "title": "Test Position",
            "company": "Test Company",
            "location": "Remote",
            "salary": "$100,000 - $150,000",
            "score": 0.85,
            "apply_url": "https://example.com/apply"
        }
    ]
    
    return send_email_notification(
        to_email=to_email,
        matched_jobs=test_jobs,
        subject="🧪 Test: Job Matching Notifications"
    )


def test_whatsapp_notification(to_phone: str) -> bool:
    """Test WhatsApp notification setup."""
    test_jobs = [
        {
            "title": "Test Position",
            "company": "Test Company",
            "location": "Remote",
            "salary": "$100,000 - $150,000",
            "score": 0.85,
            "apply_url": "https://example.com/apply"
        }
    ]
    
    return send_whatsapp_notification(
        to_phone=to_phone,
        matched_jobs=test_jobs
    )
