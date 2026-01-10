import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Student, AdminUser, Company, PlacementDrive, Quiz, JobApplication, Question
from datetime import datetime, timedelta

from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_METHODS = []

class TestQuizAccess(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create Admin
            admin = AdminUser(username='admin', email='admin@test.com')
            admin.set_password('admin')
            db.session.add(admin)
            
            # Create Student
            student = Student(
                roll_no='S101', name='Test Student', email='student@test.com',
                mobile='1234567890', department='IT', semester=1,
                status='Approved',
                is_password_changed=True,
                is_email_verified=True
            )
            student.set_password('password')
            db.session.add(student)
            
            # Create Company
            company = Company(name='Test Corp')
            db.session.add(company)
            db.session.commit()
            
            # Create Drive
            self.drive = PlacementDrive(
                company_id=company.id,
                job_title='Software Engineer',
                deadline=datetime.utcnow() + timedelta(days=10)
            )
            db.session.add(self.drive)
            db.session.commit()
            
            self.student_id = student.id
            self.drive_id = self.drive.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        if os.path.exists('test.db'):
            os.remove('test.db')

    def login_student(self):
        response = self.client.post('/student/login', data={
            'roll_no': 'S101',
            'password': 'password'
        }, follow_redirects=True)
        if b'Dashboard' not in response.data and b'Manage' not in response.data:
             print("Login Student Failed. Response substring:")
             print(response.data[:500])
             print("Flashed messages?")
        return response

    def login_admin(self):
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=True)
        if b'Dashboard' not in response.data and b'Admin' not in response.data:
             print("Login Admin Failed. Response substring:")
             print(response.data[:500])
        return response

    def test_quiz_creation_linking(self):
        """Test Admin can create a quiz linked to a drive"""
        self.login_admin()
        
        # Create Quiz via Form
        response = self.client.post('/admin/quiz/new', data={
            'title': 'Linked Quiz',
            'time_limit': 30,
            'drive_id': self.drive_id,
            'is_live': 'y' # Checkbox sends 'y' or similar if checked usually, or just presence
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        with self.app.app_context():
            quiz = Quiz.query.first()
            self.assertIsNotNone(quiz)
            self.assertEqual(quiz.drive_id, self.drive_id)
            self.assertTrue(quiz.is_live)

    def test_student_access_denied_not_applied(self):
        """Test student cannot see/access quiz if not applied to drive"""
        # 1. Create Linked Quiz (Live)
        with self.app.app_context():
            quiz = Quiz(title='Test Quiz', drive_id=self.drive_id, is_live=True)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id
            
        self.login_student()
        
        # Check List
        response = self.client.get('/student/quizzes')
        self.assertNotIn(b'Test Quiz', response.data)
        
        # Try Direct Access
        response = self.client.get(f'/student/quiz/{quiz_id}/start', follow_redirects=True)
        self.assertIn(b'Access Denied', response.data)

    def test_student_access_denied_not_live(self):
        """Test student cannot access if applied but quiz not live"""
        # 1. Apply to Drive
        with self.app.app_context():
            app = JobApplication(student_id=self.student_id, drive_id=self.drive_id)
            db.session.add(app)
            
            # Create Quiz (Not Live)
            quiz = Quiz(title='Test Quiz', drive_id=self.drive_id, is_live=False)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id
            
        self.login_student()
        
        # Check List
        response = self.client.get('/student/quizzes')
        self.assertNotIn(b'Test Quiz', response.data)
        
        # Try Direct Access
        response = self.client.get(f'/student/quiz/{quiz_id}/start', follow_redirects=True)
        self.assertIn(b'not live yet', response.data)

    def test_student_access_allowed(self):
        """Test student CAN access if applied and quiz is live"""
        # 1. Apply to Drive & Make Quiz Live
        with self.app.app_context():
            # Ensure fresh session state
            app = JobApplication(student_id=self.student_id, drive_id=self.drive_id)
            db.session.add(app)
            
            quiz = Quiz(title='Live Quiz', drive_id=self.drive_id, is_live=True)
            # Add a question so we can start it properly
            q = Question(quiz_id=1, question_text='Q1', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A', marks=1)
            quiz.questions.append(q)
            
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id
            
        self.login_student()
        
        # Check List
        response = self.client.get('/student/quizzes')
        self.assertIn(b'Live Quiz', response.data)
        
        # Try Direct Access
        response = self.client.get(f'/student/quiz/{quiz_id}/start')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Start Assessment', response.data) # or whatever is on the start page

    def test_schedule_logic(self):
        """Test future scheduled quiz logic"""
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        
        with self.app.app_context():
             # Applied student
             app = JobApplication(student_id=self.student_id, drive_id=self.drive_id)
             db.session.add(app)
             
             quiz = Quiz(title='Future Quiz', drive_id=self.drive_id, is_live=False, live_at=future)
             db.session.add(quiz)
             db.session.commit()
             quiz_id = quiz.id
             
        self.login_student()
        response = self.client.get('/student/quizzes')
        self.assertNotIn(b'Future Quiz', response.data)
        
        # Update to past
        with self.app.app_context():
            quiz = Quiz.query.get(quiz_id)
            quiz.live_at = now - timedelta(minutes=1)
            db.session.commit()
            
        response = self.client.get('/student/quizzes')
        self.assertIn(b'Future Quiz', response.data)

if __name__ == '__main__':
    unittest.main()
