import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

print("--- Email Configuration Diagnostic (SMTP Mode) ---")

server = os.getenv('MAIL_SERVER')
port = os.getenv('MAIL_PORT')
use_tls = os.getenv('MAIL_USE_TLS')
username = os.getenv('MAIL_USERNAME')
password = os.getenv('MAIL_PASSWORD')
sender = os.getenv('MAIL_DEFAULT_SENDER') or username

print(f"MAIL_SERVER: {server}")
print(f"MAIL_PORT: {port}")
print(f"MAIL_USE_TLS: {use_tls}")
print(f"MAIL_USERNAME: {username}")
print(f"MAIL_PASSWORD: {'[SET]' if password else '[MISSING]'}")

if not all([server, port, username, password]):
    print("\nCRITICAL ERROR: Missing one or more required environment variables.")
    print("Please check your .env file or system environment variables.")
else:
    print("\n--- Attempting SMTP Connection ---")
    try:
        print(f"Connecting to {server}:{port}...")
        smtp = smtplib.SMTP(server, int(port))
        smtp.set_debuglevel(1)  # Show communication
        
        print("EHLO...")
        smtp.ehlo()
        
        if use_tls == 'True':
            print("Starting TLS...")
            smtp.starttls()
            smtp.ehlo()
            
        print("Logging in...")
        smtp.login(username, password)
        print("Login Successful!")
        
        print("Sending Test Email...")
        msg = MIMEText("This is a test email from the raw SMTP diagnostic script.")
        msg['Subject'] = "SMTP Test"
        msg['From'] = sender
        msg['To'] = username
        
        smtp.sendmail(sender, [username], msg.as_string())
        print("SUCCESS: Email sent successfully via SMTP.")
        
        smtp.quit()
    except Exception as e:
        print(f"\nFAILURE: Connection or Sending Failed.")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
