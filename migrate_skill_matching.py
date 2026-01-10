import sqlite3

def migrate():
    db_path = 'instance/tpo_portal.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding required_skills and average_salary to companies table...")
        
        # Check if columns exist (basic check, though 'add column' usually fails if exists)
        try:
            cursor.execute("ALTER TABLE companies ADD COLUMN required_skills TEXT")
            print("Added required_skills column.")
        except sqlite3.OperationalError as e:
            print(f"Skipped required_skills: {e}")
            
        try:
            cursor.execute("ALTER TABLE companies ADD COLUMN average_salary FLOAT DEFAULT 0.0")
            print("Added average_salary column.")
        except sqlite3.OperationalError as e:
            print(f"Skipped average_salary: {e}")
            
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
