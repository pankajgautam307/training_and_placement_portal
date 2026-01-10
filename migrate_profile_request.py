from app import create_app, db
from models import ProfileUpdateRequest

app = create_app()

with app.app_context():
    # Create the table if it doesn't exist
    try:
        ProfileUpdateRequest.__table__.create(db.engine)
        print("Created table 'profile_update_requests'.")
    except Exception as e:
        print(f"Error (table might exist): {e}")
