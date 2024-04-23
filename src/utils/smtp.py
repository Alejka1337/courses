import smtplib
from email.mime.text import MIMEText

from src.config import SMTP_PASS, SMTP_PORT, SMTP_SERVER, SMTP_USER


def send_mail_with_code(to_email: str, mail_title: str, mail_body: str):
    msg = MIMEText(mail_body)
    msg["Subject"] = mail_title
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
