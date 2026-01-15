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
    
    # Check for Override Recipient (Testing/Sandbox)
    override_email = current_app.config.get('MAIL_OVERRIDE_RECIPIENT')
    if override_email:
        original_recipients = ", ".join(recipients)
        subject = f"[TEST OVERRIDE -> {original_recipients}] {subject}"
        recipients = [override_email]
        print(f"DEBUG: Email Override Enabled. Redirecting to {override_email}")
    
    
    if api_token:
        try:
            # Smart Auto-Detection for Resend
            # Resend keys typically start with 're_'
            is_resend = 'resend.com' in api_url or api_token.startswith('re_')
            
            # If token looks like Resend but URL is default (Mailtrap), switch to Resend URL automatically
            if api_token.startswith('re_') and 'resend.com' in api_url:
                print("DEBUG: Detected Resend Token URL. Switching to Resend API URL.")
                api_url = 'https://api.resend.com/emails'
                is_resend = True

            print(f"DEBUG: Attempting to send email via API to {recipients}. Provider: {'Resend' if is_resend else 'Other'}")
            
            sender_email = current_app.config.get('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')
            
            if is_resend:
                # Resend Specific Logic
                final_sender = "onboarding@resend.dev" # Default safe sender
                
                # Check if user provided sender is safe (not a public domain that requires verification)
                # If they have a custom domain verified, they should use it.
                # If they try to use gmail/yahoo, it will fail, so we force the default.
                unsafe_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
                if sender_email:
                    domain = sender_email.split('@')[-1].lower() if '@' in sender_email else ''
                    if domain and domain not in unsafe_domains:
                        final_sender = sender_email
                    else:
                        print(f"WARN: Sender '{sender_email}' is a public domain. Forcing 'onboarding@resend.dev' for Resend compatibility.")
                
                payload = {
                    "from": final_sender,
                    "to": recipients,
                    "subject": subject,
                    "text": body,
                    "html": html or body
                }
                
            else:
                # Mailtrap / Default Logic
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
            
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code in [200, 201, 202]:
                print(f"SUCCESS: Email sent via API. ID: {response.text}")
                return True, "Email sent successfully."
            else:
                error_msg = f"API Sending failed. Status: {response.status_code}, Response: {response.text}"
                print(f"ERROR: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"API Email sending error: {str(e)}"
            print(f"EXCEPTION: {error_msg}")
            return False, error_msg
            
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
            return True, "Email sent successfully via SMTP."
        except Exception as e:
            error_msg = f"SMTP Email sending error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return False, error_msg
