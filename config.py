import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    # Use DATABASE_URL if available, else SQLite. Handle Postgres specialized URL from some PaaS (postgres:// -> postgresql://)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///tpo_portal.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail config
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    # Add SSL support (needed for Port 465)
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # API Email Config (Mailtrap/Resend) for Production
    # Default URL is for Mailtrap (as requested), but can be overridden for Resend etc.
    MAIL_API_TOKEN = os.getenv('MAIL_API_TOKEN')
    MAIL_API_URL = os.getenv('MAIL_API_URL', 'https://send.api.mailtrap.io/api/send')
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64MB max limit
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
