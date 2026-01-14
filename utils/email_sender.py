import os
import requests
from flask import current_app
from extensions import mail
from flask_mail import Message

def send_email(subject, recipients, body, html=None):
    """
    Send email using either SMTP (Flask-Mail) or HTTP API (e.g. Mailtrap/Resend)
    based on configuration.
    """
    
    # Check for API Token - if present, prefer API (for Production/Railway)
    api_token = current_app.config.get('MAIL_API_TOKEN')
    api_url = current_app.config.get('MAIL_API_URL')
    
    if api_token and api_url:
        try:
            print(f"DEBUG: Attempting to send email via API to {recipients}")
            
            # Prepare payload for generic API (Mailtrap style default)
            # Adapt this structure if using SendGrid/Resend specific endpoints
             
            # Mailtrap / Resend / Generic JSON structure
            # Note: Mailtrap expects "from" object, "to" list of objects.
            
            sender_email = current_app.config.get('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')
            
            # Determine Payload Format based on API Provider
            if 'resend.com' in api_url:
                # Resend Format: "from" is string, "to" is list of strings
                payload = {
                    "from": "onboarding@resend.dev", # Default for Resend Free Tier if not configured otherwise
                    "to": recipients,
                    "subject": subject,
                    "text": body,
                    "html": html or body
                }
                # If the user has explicitly set a sender that ISN'T the default env var (which might be their gmail), 
                # we try to use it, but warn them.
                # Actually, for Resend to work with a custom domain, it must be verified.
                # If MAIL_DEFAULT_SENDER is set to something custom, try it.
                if current_app.config.get('MAIL_DEFAULT_SENDER'):
                     payload['from'] = current_app.config.get('MAIL_DEFAULT_SENDER')
                
            else:
                # Mailtrap / Default Format
                payload = {
                    "from": {"email": sender_email, "name": "TPO Portal"},
                    "to": [{"email": r} for r in recipients],
                    "subject": subject,
                    "text": body,
                    "html": html or body
                }
            
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            print(f"DEBUG: Sending to API: {api_url}")
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code in [200, 201, 202]:
                print(f"SUCCESS: Email sent via API. ID: {response.text}")
                return True
            else:
                print(f"ERROR: API Sending failed. Status: {response.status_code}, Body: {response.text}")
                return False
                
        except Exception as e:
            print(f"EXCEPTION: API Email sending error: {e}")
            return False
            
    else:
        # Fallback to SMTP (Flask-Mail) - Default for Localhost
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body,
                html=html
            )
            mail.send(msg)
            print(f"SUCCESS: Email sent via SMTP to {recipients}")
            return True
        except Exception as e:
            print(f"ERROR: SMTP Email sending error: {e}")
            return False
