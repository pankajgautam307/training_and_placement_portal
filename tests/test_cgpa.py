import unittest
from app import create_app, db
from config import Config
from models import Student

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class CGCGTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_cgpa_field(self):
        # Create student with CGPA
        student = Student(
            roll_no='101',
            name='Test Student',
            email='test@example.com',
            mobile='1234567890',
            department='IT',
            semester=1,
            cgpa=8.5,
            password_hash='hash'
        )
        db.session.add(student)
        db.session.commit()
        
        # Retrieve and verify
        s = Student.query.filter_by(roll_no='101').first()
        self.assertIsNotNone(s)
        self.assertEqual(s.cgpa, 8.5)
        # Verify aggregate_cpi does not exist (will raise AttributeError if code tries to access it, but here checking model dict)
        self.assertTrue(hasattr(s, 'cgpa'))
        self.assertFalse(hasattr(s, 'aggregate_cpi'))

if __name__ == '__main__':
    unittest.main()
