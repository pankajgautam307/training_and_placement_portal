import unittest
from app import create_app, db
from config import Config
from models import AdminUser

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(self.app is None)

    def test_index_redirects(self):
        client = self.app.test_client()
        response = client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Login', response.data)

    def test_admin_creation(self):
        admin = AdminUser(username='testadmin', email='test@example.com')
        admin.set_password('testpass')
        db.session.add(admin)
        db.session.commit()
        self.assertIsNotNone(AdminUser.query.filter_by(username='testadmin').first())

if __name__ == '__main__':
    unittest.main()
