import sqlite3
import os

def migrate():
    db_path = os.path.join('instance', 'placement_portal.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns if they don't exist
    columns = [
        ('drive_id', 'INTEGER REFERENCES placement_drives(id)'),
        ('is_live', 'BOOLEAN DEFAULT 0'),
        ('live_at', 'DATETIME')
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE quizzes ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
