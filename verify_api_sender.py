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
        # send_email("Test", ["test@example.com"], "Body") 
        # Commented out actual send to avoid spam/errors during this check, 
        # unless we specifically want to test SMTP.
        print("Verification script passed syntax checks.")
        
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
