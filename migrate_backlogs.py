import sqlite3

def migrate():
    conn = sqlite3.connect('instance/tpo_portal.db')
    cursor = conn.cursor()

    try:
        # Add backlogs column to students table
        print("Adding backlogs column to students table...")
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN backlogs INTEGER DEFAULT 0")
            print("Column 'backlogs' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("Column 'backlogs' already exists.")
            else:
                raise e

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
