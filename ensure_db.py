import sqlite3
import os

def check_and_migrate():
    db_path = os.path.join('instance', 'placement_portal.db')
    if not os.path.exists(db_path):
        print("Database not found. If running for first time, app will create it on startup.")
        # But we can force create it if we want, or rely on app.py
        # app.py's create_all() creates it with CURRENT models.
        # So if we run app logic (e.g. via shell), it will be fine.
        from app import app, db
        with app.app_context():
            db.create_all()
            print("Database created with current schema.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Check Company Email
    try:
        cursor.execute("SELECT email FROM companies LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding missing column: companies.email")
        try:
             cursor.execute("ALTER TABLE companies ADD COLUMN email VARCHAR(120)")
        except:
             print("Failed to add companies.email")

    # 2. Check Quiz Columns
    try:
        cursor.execute("SELECT drive_id, is_live, live_at FROM quizzes LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding missing columns to quizzes")
        try:
             cursor.execute("ALTER TABLE quizzes ADD COLUMN drive_id INTEGER REFERENCES placement_drives(id)")
             cursor.execute("ALTER TABLE quizzes ADD COLUMN is_live BOOLEAN DEFAULT 0")
             cursor.execute("ALTER TABLE quizzes ADD COLUMN live_at DATETIME")
        except Exception as e:
             print(f"Failed to add quiz columns: {e}")

    conn.commit()
    conn.close()
    print("Verification complete.")

if __name__ == "__main__":
    check_and_migrate()
