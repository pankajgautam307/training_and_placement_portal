from app import create_app, db
from models import AdminUser

def init_db():
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
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
