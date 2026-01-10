from app import create_app, db
import sqlalchemy as sa

app = create_app()

with app.app_context():
    # Use raw SQL for SQLite ALTER TABLE
    with db.engine.connect() as conn:
        try:
            conn.execute(sa.text("ALTER TABLE students ADD COLUMN resume_data_path VARCHAR(200)"))
            print("Successfully added resume_data_path column to students table.")
        except Exception as e:
            print(f"Error (column might already exist): {e}")
