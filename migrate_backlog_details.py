"""
Migration script to create backlogs table for detailed backlog tracking
"""
import sqlite3
from pathlib import Path

# Get database path
db_path = Path(__file__).parent / 'instance' / 'tpo.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Create backlogs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backlogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_name VARCHAR(100) NOT NULL,
            semester INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    print("✓ Created 'backlogs' table successfully")
    
except Exception as e:
    print(f"✗ Error creating backlogs table: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nMigration completed!")
