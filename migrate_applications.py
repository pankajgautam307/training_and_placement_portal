from app import create_app, db
from models import JobApplication

app = create_app()

with app.app_context():
    try:
        JobApplication.__table__.create(db.engine)
        print("Created table 'job_applications'.")
    except Exception as e:
        print(f"Error creating 'job_applications': {e}")
