from flask import Flask
from config import Config
from extensions import mail

app = Flask(__name__)
app.config.from_object(Config)
mail.init_app(app)

print("Attempting to import email_sender...")
try:
    from utils.email_sender import send_email
    print("Import successful.")
    
    with app.app_context():
        # Dry run - checking if function accepts args
        # This will try to send via SMTP if API vars are missing, which might fail or succeed depending on .env
        # We just want to ensure code path doesn't crash immediately.
        print("Calling send_email...")
        print("Calling send_email...")
        # Use a safe test email or the one from config
        recipient = app.config.get('MAIL_OVERRIDE_RECIPIENT') or app.config.get('MAIL_USERNAME') or "test@example.com"
        success, msg = send_email("Test Subject", [recipient], "Test Body") 
        print(f"Send Result: {success} - {msg}")
        print("Verification script passed syntax checks.")
        
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
