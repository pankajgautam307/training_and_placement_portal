from app import create_app, db
from models import DriveInvitation

def migrate():
    app = create_app()
    with app.app_context():
        try:
            print("Creating drive_invitations table...")
            db.create_all() # This creates all tables that don't exist
            print("Migration completed successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == '__main__':
    migrate()
