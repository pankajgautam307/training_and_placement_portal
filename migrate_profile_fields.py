from app import create_app
import extensions
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with extensions.db.engine.connect() as connection:
            connection.execute(text("ALTER TABLE students ADD COLUMN profile_photo VARCHAR(120)"))
            connection.execute(text("ALTER TABLE students ADD COLUMN resume_path VARCHAR(200)"))
            connection.commit()
        print("Successfully added profile_photo and resume_path columns.")
    except Exception as e:
        print(f"Error adding columns (they might already exist): {e}")
