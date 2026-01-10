from flask import Flask
from config import Config
from extensions import db, bcrypt, mail, login_manager, csrf, migrate
from models import AdminUser

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from blueprints.auth import auth_bp
    from blueprints.student import student_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return "File too large. Maximum size is 64MB.", 413

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    from models import Student, AdminUser
    model, real_id = user_id.split('-', 1)
    if model == 'S':
        return Student.query.get(int(real_id))
    if model == 'A':
        return AdminUser.query.get(int(real_id))
    return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not AdminUser.query.filter_by(username='tpo').first():
            admin = AdminUser(username='tpo', email='tpo@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
