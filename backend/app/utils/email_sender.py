"""
Email utilities for transactional emails.
"""
import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_password_reset_email(to_email: str, otp: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP settings are not configured")

    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER

    message = EmailMessage()
    message["Subject"] = "Password reset code"
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(
        "We received a password reset request.\n\n"
        f"OTP: {otp}\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
