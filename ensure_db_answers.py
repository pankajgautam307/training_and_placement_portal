from app import create_app, db
from sqlalchemy import text

def check_and_migrate():
    app = create_app()
    with app.app_context():
        # Use SQLAlchemy to execute raw SQL, safer for path resolution
        try:
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("SELECT answers FROM quiz_attempts LIMIT 1"))
                    print("Column 'answers' already exists.")
                except Exception:
                    print("Adding missing column: quiz_attempts.answers")
                    conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN answers TEXT"))
                    conn.commit()
                    print("Migration complete.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    check_and_migrate()
