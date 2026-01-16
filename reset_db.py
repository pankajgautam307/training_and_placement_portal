from app import create_app, db
from init_db import init_db

app = create_app()

def reset_db():
    print("WARNING: This will DELETE ALL DATA in the database.")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("All tables dropped.")
        
        print("Re-initializing database...")
        # init_db() logic is partly inside the function but also calls create_app again. 
        # We can just call db.create_all() and the admin creation logic here or call init_db
        
        # Calling init_db function from the module
        # Note: init_db.py's init_db() creates its own app context, so we step out or just let it run.
    
    print("Running init_db to set up schema and default admin...")
    init_db()
    print("Database reset complete.")

if __name__ == "__main__":
    reset_db()
