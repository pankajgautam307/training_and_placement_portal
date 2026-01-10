from app import create_app, db
from models import Quiz, Question, QuizAttempt

def migrate():
    app = create_app()
    with app.app_context():
        try:
            print("Creating quiz tables...")
            db.create_all()
            print("Migration completed successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == '__main__':
    migrate()
