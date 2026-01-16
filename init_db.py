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

            if 'is_password_changed' not in columns:
                print("Migrating: Adding 'is_password_changed' column to 'students' table...")
                with db.engine.connect() as conn:
                    # Postgres/SQLite compatible BOOLEAN/INTEGER handling might vary but SQLAlchemy handles db.Boolean as BOOLEAN or INTEGER.
                    # Text SQL needs specific type. BOOLEAN is standard SQL, works in Postgres and SQLite (as numeric).
                    conn.execute(text("ALTER TABLE students ADD COLUMN is_password_changed BOOLEAN DEFAULT 0"))
                    conn.commit()
                print("Migration: 'is_password_changed' column added.")

            if 'is_email_verified' not in columns:
                print("Migrating: Adding 'is_email_verified' column to 'students' table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE students ADD COLUMN is_email_verified BOOLEAN DEFAULT 0"))
                    conn.commit()
                print("Migration: 'is_email_verified' column added.")

        # Schema Migration: Add 'contact_number' column to 'companies'
        if inspector.has_table('companies'):
            columns = [col['name'] for col in inspector.get_columns('companies')]
            if 'contact_number' not in columns:
                print("Migrating: Adding 'contact_number' column to 'companies' table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN contact_number VARCHAR(15)"))
                    conn.commit()
                print("Migration: 'contact_number' column added.")
            else:
                print("Schema Check: 'contact_number' column already exists.")

        print("Checking for default admin user...")
        default_user = app.config['ADMIN_USERNAME']
        if not AdminUser.query.filter_by(username=default_user).first():
            print(f"Creating default admin user '{default_user}'...")
            admin = AdminUser(username=default_user, email=app.config['ADMIN_EMAIL'])
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print("Default admin created.")
        else:
            print("Default admin already exists.")
            
if __name__ == '__main__':
    init_db()
