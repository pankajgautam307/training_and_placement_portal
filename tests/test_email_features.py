import unittest
from app import create_app, db
from config import Config
from models import DriveInvitation, Company, AdminUser
from flask_mail import Mail

# Mock mail sending
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True # Don't actually send

class EmailFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Admin
        admin = AdminUser(username='admin', email='admin@test.com', role='TPO')
        admin.set_password('pass')
        db.session.add(admin)
        
        # Company with Email
        self.company = Company(
            name='Email Corp',
            email='recruiter@emailcorp.com',
            required_skills='Python',
            average_salary=15.0
        )
        db.session.add(self.company)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_invite_company_sends_email(self):
        with self.app.test_request_context():
            # Using record_messages to capture sent emails
            from extensions import mail
            with mail.record_messages() as outbox:
                response = self.client.post(f'/admin/invite/{self.company.id}', data={
                    'subject': 'Drive Invite',
                    'message': 'Please come.'
                }, follow_redirects=True)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(outbox), 1)
                self.assertEqual(outbox[0].subject, 'Drive Invite')
                self.assertIn('recruiter@emailcorp.com', outbox[0].recipients)
                self.assertIn('Invitation sent to Email Corp', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
