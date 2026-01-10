import sqlite3

def migrate():
    db_path = 'instance/tpo_portal.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding email to companies table...")
        try:
            cursor.execute("ALTER TABLE companies ADD COLUMN email VARCHAR(120)")
            print("Added email column.")
        except sqlite3.OperationalError as e:
            print(f"Skipped email: {e}")
            
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
