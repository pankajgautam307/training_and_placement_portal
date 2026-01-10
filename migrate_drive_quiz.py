import sqlite3
import os

db_path = os.path.join('instance', 'tpo_portal.db')

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(placement_drives)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'quiz_id' not in columns:
            print("Adding quiz_id column to placement_drives...")
            cursor.execute("ALTER TABLE placement_drives ADD COLUMN quiz_id INTEGER REFERENCES quizzes(id)")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'quiz_id' already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
