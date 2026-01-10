from app import create_app, db
from sqlalchemy import text

def check_and_migrate():
    app = create_app()
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("SELECT pass_percentage FROM quizzes LIMIT 1"))
                    print("Column 'pass_percentage' already exists.")
                except Exception:
                    print("Adding missing column: quizzes.pass_percentage")
                    conn.execute(text("ALTER TABLE quizzes ADD COLUMN pass_percentage FLOAT DEFAULT 50.0"))
                    conn.commit()
                    print("Migration complete.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    check_and_migrate()
