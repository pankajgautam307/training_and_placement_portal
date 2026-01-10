import unittest
import io
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from config import Config
from models import AdminUser, Student, Company, PlacementDrive, JobApplication
from datetime import datetime, date

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Test limit

class FullFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Default Admin
        admin = AdminUser(username='tpo', email='tpo@example.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, client, email, password, role='student'):
        endpoint = 'auth.student_login' if role == 'student' else 'auth.admin_login'
        if role == 'admin':
            resp = client.post('/admin/login', data=dict(
                username='tpo',
                password=password
            ), follow_redirects=True)
            if b'Dashboard' not in resp.data:
                print("Admin Login Failed:")
                # print(resp.data.decode('utf-8')) # Too noisy
            return resp
        else:
            resp = client.post('/student/login', data=dict(
                roll_no=email, # Passing roll_no as first arg in test calls
                password=password
            ), follow_redirects=True)
            return resp

    def test_full_placement_cycle(self):
        client = self.app.test_client()
        
        # 1. Student Registration
        resp = client.post('/student/register', data=dict(
            name='Test Student',
            roll_no='101',
            email='student@test.com',
            mobile='9999999999',
            password='password123',
            confirm_password='password123',
            gender='Male',
            department='IT',
            semester=6,
            tenth_marks=85.5,
            twelfth_marks=88.2,
            cgpa=9.0,
            address='Test Address',
            skills='Python, Flask',
            projects_internship='Demo Project'
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(Student.query.filter_by(roll_no='101').first())
        
        # 2. Admin Login & Approval
        self.login(client, 'tpo', 'admin123', role='admin')
        student = Student.query.filter_by(roll_no='101').first()
        # Approve via POST to edit_student
        resp = client.post(f'/admin/student/{student.id}/edit', data=dict(
            name=student.name,
            email=student.email,
            roll_no=student.roll_no,
            mobile=student.mobile,
            gender='Male',
            department=student.department,
            semester=student.semester,
            tenth_marks=student.tenth_marks,
            twelfth_marks=student.twelfth_marks,
            cgpa=student.cgpa,
            status='Approved'
        ), follow_redirects=True)
        
        student = Student.query.get(student.id)
        if student.status != 'Approved':
            print("Form Validation Failed. Response:")
            print(resp.data.decode('utf-8'))
            
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(student.status, 'Approved')
        
        # 3. Create Company & Drive
        resp = client.post('/admin/companies', data=dict(
            name='Tech Corp',
            website='https://tech.com',
            industry='IT',
            location='Remote',
            about='Great company'
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        company = Company.query.filter_by(name='Tech Corp').first()
        
        resp = client.post('/admin/drive/new', data=dict(
            company_id=company.id,
            job_title='Software Engineer',
            job_description='Develop Python apps',
            criteria_10th=60,
            criteria_12th=60,
            criteria_cgpa=7.0,
            salary='10 LPA',
            deadline=date(2027, 12, 31),
            drive_date=date(2028, 1, 1), # Changed to date
            allowed_branches='IT, CS'
        ), follow_redirects=True)
        
        drive = PlacementDrive.query.filter_by(job_title='Software Engineer').first()
        if not drive:
             print("Drive Creation Failed. Response:")
             print(resp.data.decode('utf-8'))
        self.assertIsNotNone(drive)
        
        # Logout Admin
        client.get('/auth/logout', follow_redirects=True)
        
        # 4. Student Login & Apply
        # Helper login using hardcoded '101' for now, verifying flow
        self.login(client, '101', 'password123', role='student')
        
        # Check Dashboard (Photo/Resume Links check)
        resp = client.get('/student/dashboard')
        self.assertIn(b'Profile Summary', resp.data)
        
        # Mock File Upload (Edit Profile)
        # Using io.BytesIO for fake files
        data = dict(
            mobile='8888888888',
            profile_photo=(io.BytesIO(b"fakeimage"), 'photo.jpg'),
            resume=(io.BytesIO(b"%PDF-1.4 fake pdf"), 'resume.pdf')
        )
        # Need to include all required fields for form validation? 
        # StudentProfileForm usually populates from obj. We just send changed/new fields.
        # But WTForms might require fields if not 'Optional'.
        # Let's try sending just the files + required text fields if validation fails.
        # Actually form is bound to obj, so existing values should be there. 
        # But in a POST request, only submitted data is processed.
        # So we include other fields or rely on partial updates if implemented (our logic handles individual fields, but form validation requires valid data).
        # We'll send full data to be safe.
        full_data = dict(
            email='student@test.com', # Readonly, validator might ignore or check consistency
            mobile='8888888888',
            address='New Address',
            skills='Python, Java',
            projects_internship='Updated Project',
            tenth_marks=90,
            twelfth_marks=90,
            cgpa=9.0,
            profile_photo=(io.BytesIO(b"fakeimage"), 'photo.jpg'),
            resume=(io.BytesIO(b"%PDF-1.4 fake pdf"), 'resume.pdf')
        )
        
        resp = client.post('/student/profile/edit', data=full_data, follow_redirects=True, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        
        # Since student is 'Approved', this creates a request, DOES NOT update immediately (except files).
        # Check files updated
        student = Student.query.get(student.id)
        self.assertTrue('photo.jpg' in student.profile_photo)
        self.assertTrue('resume.pdf' in student.resume_path)
        
        # Apply for Drive
        resp = client.post(f'/student/drive/{drive.id}/apply', follow_redirects=True)
        self.assertIn(b'Successfully applied', resp.data)
        
        # 5. Resume Generation
        with unittest.mock.patch('xhtml2pdf.pisa.CreatePDF') as mock_create_pdf:
            mock_create_pdf.return_value = type('obj', (object,), {'err': 0})
            
            resp = client.post('/student/resume/generate', data={'template': 'modern'})
            # Should return PDF
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.mimetype, 'application/pdf')

if __name__ == '__main__':
    unittest.main()
