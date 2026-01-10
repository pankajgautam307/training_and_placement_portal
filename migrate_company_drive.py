from app import create_app, db
from models import Company, PlacementDrive

app = create_app()

with app.app_context():
    try:
        Company.__table__.create(db.engine)
        print("Created table 'companies'.")
    except Exception as e:
        print(f"Error creating 'companies': {e}")
        
    try:
        PlacementDrive.__table__.create(db.engine)
        print("Created table 'placement_drives'.")
    except Exception as e:
        print(f"Error creating 'placement_drives': {e}")
