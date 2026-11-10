import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger("EmailService")


def send_verification_email(to_email: str, token: str, full_name: Optional[str] = None) -> bool:
    """
    Sends an email confirmation link to the newly registered user.
    If SMTP credentials are not configured in environment, logs the link for development/local execution.
    """
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    recipient_name = full_name or to_email.split("@")[0]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Confirm Your CAS Account</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F8FAFC; margin: 0; padding: 24px; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 32px; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .btn {{ display: inline-block; background-color: #2563EB; color: #ffffff !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; margin-top: 20px; }}
        .footer {{ margin-top: 32px; font-size: 11px; color: #64748B; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h2 style="color: #0F172A; margin: 0;">Contract Agentic Society (CAS)</h2>
          <p style="color: #64748B; font-size: 13px; margin-top: 4px;">Confirm your enterprise account email</p>
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.5;">Hello {recipient_name},</p>
        <p style="color: #334155; font-size: 14px; line-height: 1.5;">Thank you for registering for the Contract Agentic Society. Please verify your email address to activate your account and start reviewing contracts and multi-agent negotiations.</p>
        <div style="text-align: center;">
          <a href="{verify_url}" class="btn">Verify Email Address</a>
        </div>
        <p style="color: #64748B; font-size: 12px; margin-top: 24px;">If the button above does not work, copy and paste this URL into your browser:</p>
        <p style="color: #2563EB; font-size: 11px; word-break: break-all;">{verify_url}</p>
        <div class="footer">
          &copy; 2026 Contract Agentic Society. Automated verification dispatch.
        </div>
      </div>
    </body>
    </html>
    """

    if not settings.SMTP_HOST:
        logger.info(f"SMTP not configured. Emulated email verification for {to_email}. Verification Link: {verify_url}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Confirm Your CAS Account Email"
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        if settings.SMTP_USE_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Verification email successfully sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch verification email to {to_email}: {e}")
        return False
