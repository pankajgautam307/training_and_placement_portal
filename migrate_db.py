from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN is_password_changed BOOLEAN DEFAULT 0"))
            print("Added is_password_changed column")
        except Exception as e:
            print(f"Error adding is_password_changed: {e}")
            
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN is_email_verified BOOLEAN DEFAULT 0"))
            print("Added is_email_verified column")
        except Exception as e:
            print(f"Error adding is_email_verified: {e}")

        conn.commit()
