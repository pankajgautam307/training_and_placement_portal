from app import create_app, db
import models
from models import AdminUser, Student


def init_db():
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Schema Migration: Add 'backlogs' column to 'students' if missing (for existing deployments)
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if inspector.has_table('students'):
            columns = [col['name'] for col in inspector.get_columns('students')]
            if 'backlogs' not in columns:
                print("Migrating: Adding 'backlogs' column to 'students' table...")
                with db.engine.connect() as conn:
                    # Generic SQL works for both SQLite and Postgres for simple column add
                    conn.execute(text("ALTER TABLE students ADD COLUMN backlogs INTEGER DEFAULT 0"))
                    conn.commit()
                print("Migration: 'backlogs' column added.")
            else:
                print("Schema Check: 'backlogs' column already exists.")

        print("Checking for default admin user...")
        if not AdminUser.query.filter_by(username='tpo').first():
            print("Creating default admin user 'tpo'...")
            admin = AdminUser(username='tpo', email='tpo@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created.")
        else:
            print("Default admin already exists.")
            
if __name__ == '__main__':
    init_db()
