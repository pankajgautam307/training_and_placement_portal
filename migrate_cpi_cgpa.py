import sqlite3

def migrate():
    conn = sqlite3.connect('instance/tpo_portal.db')
    cursor = conn.cursor()

    try:
        # Rename column in students table
        print("Renaming aggregate_cpi to cgpa in students table...")
        cursor.execute("ALTER TABLE students RENAME COLUMN aggregate_cpi TO cgpa")
        
        # Rename column in placement_drives table
        print("Renaming criteria_cpi to criteria_cgpa in placement_drives table...")
        cursor.execute("ALTER TABLE placement_drives RENAME COLUMN criteria_cpi TO criteria_cgpa")

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
