import unittest
from app import create_app, db
from config import Config
from models import Student

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True # Don't actually send emails

class EmailVerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registration_requires_verification(self):
        client = self.app.test_client()
        data = {
            'roll_no': 'E101',
            'name': 'Email Student',
            'fathers_name': 'Test Father',
            'college_name': 'Test College',
            'email': 'email@e.com',
            'mobile': '9876543210',
            'department': 'IT',
            'semester': 5,
            'password': 'password',
            'confirm_password': 'password',
            'metric_type': 'cgpa',
            'cgpa': 8.5,
            'gender': 'Male',
            'backlogs': '' 
        }
        # Debug form validation
        from forms import StudentRegistrationForm
        from werkzeug.datastructures import MultiDict
        form = StudentRegistrationForm(formdata=MultiDict(data))
        if not form.validate():
            print("Form Errors:", form.errors)

        # 1. Register
        response = client.post('/student/register', data=data, follow_redirects=True)
        # Should show message about verification
        if b'Please verify your email' not in response.data:
            print(response.data.decode('utf-8'))
        self.assertIn(b'Please verify your email', response.data)
        
        student = Student.query.filter_by(roll_no='E101').first()
        self.assertIsNotNone(student)
        self.assertFalse(student.is_email_verified)
        
        # 2. Try Login (Should fail/redirect)
        login_data = {'roll_no': 'E101', 'password': 'password'}
        response = client.post('/student/login', data=login_data, follow_redirects=True)
        # Should be redirected back to login or show warning
        self.assertIn(b'Please verify your email address', response.data)
        
        # 3. Simulate Verification
        student.is_email_verified = True
        db.session.commit()
        
        # 4. Try Login Again (Should succeed)
        response = client.post('/student/login', data=login_data, follow_redirects=True)
        self.assertIn(b'Dashboard', response.data) # Assuming dashboard text

if __name__ == '__main__':
    unittest.main()
