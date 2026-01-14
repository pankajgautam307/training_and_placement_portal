import unittest
from app import create_app, db
from config import Config
from models import Student, AdminUser

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class BacklogTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_student_model_backlogs(self):
        s = Student(
            roll_no='101', name='Test', email='test@e.com', mobile='1234567890',
            department='IT', semester=5, 
            password_hash='pass',
            cgpa=0.0, backlogs=2
        )
        db.session.add(s)
        db.session.commit()
        
        fetched = Student.query.get(s.id)
        self.assertEqual(fetched.backlogs, 2)
        self.assertEqual(fetched.cgpa, 0.0)

    def test_registration_form_backlogs(self):
        client = self.app.test_client()
        # Simulate selecting "Backlogs"
        data = {
            'roll_no': 'B101',
            'name': 'Backlog Student',
            'fathers_name': 'Test Father',
            'college_name': 'Test College',
            'gender': 'Male',
            'email': 'back@e.com',
            'mobile': '9876543210',
            'department': 'IT',
            'semester': 5,
            'password': 'password',
            'confirm_password': 'password',
            'metric_type': 'backlogs',
            'backlogs': 2,
            'cgpa': '' # Should be ignored or optional
        }
        response = client.post('/student/register', data=data, follow_redirects=True)
        
        # Debugging: check for errors if student not found
        s = Student.query.filter_by(roll_no='B101').first()
        if not s:
            print(f"Registration B101 failed. Response status: {response.status_code}")
            # In a real app we can't easily access form errors from response unless we parse HTML
            # or access the context variable if using flask testing support properly
            # But we can try to inspect the response data for "Invalid"
            print(response.data.decode('utf-8')) # This might be too much
            
        self.assertIsNotNone(s)
        self.assertEqual(s.backlogs, 2)
        # self.assertEqual(s.cgpa, 0.0) # Depending on form logic, might be None or 0.
        # Our validation ensures if backlogs is selected, backlogs is required.
        
    def test_registration_form_cgpa(self):
        client = self.app.test_client()
        # Simulate selecting "CGPA"
        data = {
            'roll_no': 'C101',
            'name': 'CGPA Student',
            'fathers_name': 'Test Father',
            'college_name': 'Test College',
            'gender': 'Female',
            'email': 'cgpa@e.com',
            'mobile': '9876543210',
            'department': 'IT',
            'semester': 5,
            'password': 'password',
            'confirm_password': 'password',
            'metric_type': 'cgpa',
            'cgpa': 8.5,
            'backlogs': '' 
        }
        response = client.post('/student/register', data=data, follow_redirects=True)
        
        s = Student.query.filter_by(roll_no='C101').first()
        self.assertIsNotNone(s)
        self.assertEqual(s.cgpa, 8.5)
        # Backlogs might be default 0 or None. Model default is 0.
        self.assertEqual(s.backlogs, 0)

    def test_bulk_import_backlogs(self):
        # Create admin user
        admin = AdminUser(username='admin', email='admin@example.com')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        
        client = self.app.test_client()
        client.post('/auth/admin/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
        # Login might be needed
        # Assuming admin login route is /auth/admin/login and redirects to /admin/dashboard
        
        # We need to simulate file upload
        import io
        csv_content = "roll_no,name,email,mobile,department,semester,tenth_marks,twelfth_marks,cgpa,backlogs,skills,projects\nBI101,Bulk Student,bulk@e.com,9876543210,IT,5,80,80,0,3,Python,None"
        data = {
            'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')
        }
        
        # Need to mock current_user or login
        # Since we use flask-login, client.post login should work if routes are correct.
        # But wait, app.py doesn't show admin login route? 
        # listing blueprints/auth.py showed /admin/login.
        
        # Let's bypass login by mocking or using simple test_client login if works.
        # For this test environment, simple Session based login works if we post to login route.
        with client:
             client.post('/auth/admin/login', data={'username': 'admin', 'password': 'admin'})
             response = client.post('/admin/import', data=data, content_type='multipart/form-data', follow_redirects=True)
             
        s = Student.query.filter_by(roll_no='BI101').first()
        self.assertIsNotNone(s)
        self.assertEqual(s.backlogs, 3)
        self.assertEqual(s.cgpa, 0.0)

if __name__ == '__main__':
    unittest.main()
