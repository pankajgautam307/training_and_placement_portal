from app import create_app
from extensions import db
import models

app = create_app()
with app.app_context():
    print("Tables in metadata:", db.metadata.tables.keys())
