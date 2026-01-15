import unittest
from app import create_app, db
from config import Config
from models import Student, EmailLog, AdminUser
from unittest.mock import patch, MagicMock

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class EmailApprovalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Admin
        self.admin = AdminUser(username='admin', email='admin@test.com', role='TPO')
        self.admin.set_password('pass')
        db.session.add(self.admin)
        
        # Create Student
        self.student = Student(
            roll_no='123', name='Test Student', email='test@student.com',
            mobile='9999999999', department='CSE', semester=1,
            tenth_marks=90, twelfth_marks=90, cgpa=9.0, backlogs=0
        )
        self.student.set_password('password')
        self.student.status = 'Pending'
        db.session.add(self.student)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    @patch('blueprints.admin.send_email')
    def test_approve_student_calls_send_email(self, mock_send_email):
        # Setup mock to return True
        mock_send_email.return_value = True
        
        # Action: Approve student
        response = self.client.post(f'/admin/student/{self.student.id}/status', data={'status': 'Approved'}, follow_redirects=True)
        
        # Assertions
        mock_send_email.assert_called_once()
        args, _ = mock_send_email.call_args
        self.assertIn('Welcome to the Training & Placement Portal', args[0])
        self.assertEqual(args[1], ['test@student.com'])
        
        # Check DB Log
        log = EmailLog.query.filter_by(student_id=self.student.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'Success')
        
if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(EmailApprovalTestCase)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
