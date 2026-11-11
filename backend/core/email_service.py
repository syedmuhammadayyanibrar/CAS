import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import httpx

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger("EmailService")

RESEND_API_URL = "https://api.resend.com/emails"


def _dispatch_via_resend(to_email: str, subject: str, html_content: str) -> bool:
    """Dispatches an HTML email using the Resend REST API."""
    api_key = settings.RESEND_API_KEY
    if not api_key:
        return False

    # Avoid live external HTTP calls during automated pytest runs unless explicitly mocked
    if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("FORCE_RESEND_LIVE"):
        logger.info(f"[Test Mode] Resend dispatch simulated for {to_email}: {subject}")
        return True

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            },
            timeout=10.0,
        )
        if response.status_code in (200, 201, 202):
            logger.info(f"Email dispatched via Resend to {to_email} (id={response.json().get('id')})")
            return True
        logger.warning(
            f"Resend API returned status {response.status_code} for {to_email}: {response.text}"
        )
        return False
    except Exception as exc:
        logger.error(f"Failed to send email via Resend to {to_email}: {exc}")
        return False


def send_otp_email(
    to_email: str,
    otp_code: str,
    full_name: Optional[str] = None,
    purpose: str = "verification",
    valid_minutes: int = 5,
) -> bool:
    """
    Sends a 6-digit OTP code via Resend (primary) or SMTP (fallback) for account creation
    verification or passwordless email sign-in.
    """
    recipient_name = full_name or to_email.split("@")[0]
    action_title = (
        "Sign in to Your CAS Account"
        if purpose == "login"
        else "Verify Your CAS Account Email"
    )
    action_desc = (
        "Use the one-time verification code below to complete your sign-in to the Contract Agentic Society (CAS) platform."
        if purpose == "login"
        else "Thank you for creating an account with the Contract Agentic Society (CAS). Enter the 6-digit verification code below to verify your email and activate your session."
    )

    subject = f"{otp_code} is your CAS verification code"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{action_title}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F8FAFC; margin: 0; padding: 24px;">
      <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #E2E8F0; border-radius: 14px; padding: 32px;">
        <div style="text-align: center; margin-bottom: 24px;">
          <h2 style="color: #0F172A; margin: 0; font-size: 20px;">Contract Agentic Society (CAS)</h2>
          <p style="color: #64748B; font-size: 13px; margin-top: 6px;">{action_title}</p>
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.5;">Hello {recipient_name},</p>
        <p style="color: #334155; font-size: 14px; line-height: 1.5;">{action_desc}</p>
        <div style="text-align: center; margin: 28px 0;">
          <div style="display: inline-block; background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 12px; padding: 16px 32px; font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #0F172A;">
            {otp_code}
          </div>
        </div>
        <p style="color: #64748B; font-size: 12px; text-align: center; margin-top: 16px;">
          This code is valid for <strong>{valid_minutes} minutes</strong>. Do not share this code with anyone.
        </p>
        <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #E2E8F0; font-size: 11px; color: #94A3B8; text-align: center;">
          &copy; 2026 Contract Agentic Society. Automated security dispatch via Resend.
        </div>
      </div>
    </body>
    </html>
    """

    if settings.RESEND_API_KEY:
        if _dispatch_via_resend(to_email, subject, html_content):
            return True

    if not settings.SMTP_HOST:
        logger.info(f"OTP generated for {to_email} ({purpose}): {otp_code}")
        return True

    return _dispatch_via_smtp(to_email, subject, html_content)


def send_verification_email(to_email: str, token: str, full_name: Optional[str] = None) -> bool:
    """
    Legacy/fallback confirmation link sender, also routed through Resend when configured.
    """
    if token.isdigit() and len(token) == 6:
        return send_otp_email(to_email, token, full_name=full_name, purpose="register")

    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    recipient_name = full_name or to_email.split("@")[0]
    subject = "Confirm Your CAS Account Email"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Confirm Your CAS Account</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F8FAFC; margin: 0; padding: 24px;">
      <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 32px;">
        <h2 style="color: #0F172A; margin: 0; text-align: center;">Contract Agentic Society (CAS)</h2>
        <p style="color: #334155; font-size: 14px; line-height: 1.5; margin-top: 20px;">Hello {recipient_name},</p>
        <p style="color: #334155; font-size: 14px; line-height: 1.5;">Please verify your email address to activate your account:</p>
        <div style="text-align: center; margin: 24px 0;">
          <a href="{verify_url}" style="display: inline-block; background-color: #2563EB; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">Verify Email Address</a>
        </div>
      </div>
    </body>
    </html>
    """

    if settings.RESEND_API_KEY:
        if _dispatch_via_resend(to_email, subject, html_content):
            return True

    if not settings.SMTP_HOST:
        logger.info(f"Emulated email verification for {to_email}. Link: {verify_url}")
        return True

    return _dispatch_via_smtp(to_email, subject, html_content)


def _dispatch_via_smtp(to_email: str, subject: str, html_content: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch SMTP email to {to_email}: {e}")
        return False
