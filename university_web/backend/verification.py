"""Email helpers. Credentials are supplied only through environment variables."""
import os, secrets, smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

# Generate a cryptographically random URL-safe token.
def generate_verification_token():
    return secrets.token_urlsafe(32)

# Send an HTML email over SMTP; logs and returns False when SMTP is not configured.
def _send(to_email, subject, html):
    host=os.getenv("SMTP_HOST")
    user=os.getenv("SMTP_USER")
    password=os.getenv("SMTP_PASSWORD")
    port=int(os.getenv("SMTP_PORT","587"))
    sender=os.getenv("SMTP_FROM", user or "")
    if not (host and user and password and sender):
        # Development-safe fallback: never expose a token in an API response.
        print(f"[EMAIL NOT CONFIGURED] To: {to_email}; Subject: {subject}")
        return False
    msg=MIMEText(html, "html")
    msg["Subject"]=subject; msg["From"]=sender; msg["To"]=to_email
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls(); smtp.login(user,password); smtp.send_message(msg)
    return True

# Email an account verification link (kept for completeness; verification is disabled).
def send_verification_email(to_email, verification_link):
    return _send(to_email, "Verify your University Web account",
                 f"<p>Please verify your account:</p><p><a href='{verification_link}'>Verify email</a></p>")

# Email a password reset link.
def send_password_reset_email(to_email, reset_link):
    return _send(to_email, "Reset your University Web password",
                 f"<p>Reset your password:</p><p><a href='{reset_link}'>Reset password</a></p>")
