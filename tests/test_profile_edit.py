import unittest
from app import create_app, db
from config import Config
from models import Student
from flask_login import login_user

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True

class ProfileEditTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a pending student
        self.student = Student(
            roll_no='P101',
            name='Pending Student',
            email='pending@e.com',
            mobile='9876543210',
            department='IT',
            semester=5,
            is_email_verified=True,
            is_password_changed=True,
            status='Pending'
        )
        self.student.set_password('password')
        db.session.add(self.student)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_edit_profile_pending(self):
        client = self.app.test_client()
        with client:
            # Login
            client.post('/student/login', data={'roll_no': 'P101', 'password': 'password'})
            
            # Edit Profile Data
            data = {
                'name': 'Pending Student Updated',
                'fathers_name': 'New Father',
                'college_name': 'New College',
                'mobile': '9876543211',
                'department': 'CS',
                'semester': 6,
                'metric_type': 'cgpa',
                'cgpa': 9.0,
                'backlogs': 0,
                'skills': 'Python',
                'projects_internship': 'Project A'
            }
            
            # Debug form validation
            from forms import StudentProfileForm
            from werkzeug.datastructures import MultiDict
            form = StudentProfileForm(formdata=MultiDict(data))
            if not form.validate():
                print("Form Errors:", form.errors)
                
            # Submit form
            # Debug: Check logic if it fails
            response = client.post('/student/profile/edit', data=data, follow_redirects=True)
            
            if b'Profile updated successfully' not in response.data:
                 print(response.data.decode('utf-8'))
                 # Also try to print form errors from context if possible, or just parse HTML
                 
            # Check for success
            self.assertIn(b'Profile updated successfully', response.data)
            
            # Verify DB Update
            s = Student.query.filter_by(roll_no='P101').first()
            self.assertEqual(s.fathers_name, 'New Father')
            self.assertEqual(s.college_name, 'New College')
            self.assertEqual(s.department, 'CS')

if __name__ == '__main__':
    unittest.main()
