import smtplib
from email.message import EmailMessage
from pathlib import Path

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
USERNAME = "pg22688n8n@gmail.com"
PASSWORD = "tcwqvhsfzpgbospe"

def send_email_with_attachment(to_addr, subject, body, file_path):
    msg = EmailMessage()
    msg["From"] = USERNAME
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    path = Path(file_path)
    data = path.read_bytes()
    msg.add_attachment(
        data,
        maintype="application",
        subtype="octet-stream",
        filename=path.name,
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(USERNAME, PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    send_email_with_attachment(
        "pgpankajgautam@gmail.com",
        "Test mail",
        "Please find the report attached.",
        "requirements.txt",
    )
