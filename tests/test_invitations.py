import unittest
from app import create_app, db
from config import Config
from models import DriveInvitation, Company, AdminUser

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class InvitationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Admin
        admin = AdminUser(username='admin', email='admin@test.com', role='TPO')
        admin.set_password('password')
        db.session.add(admin)
        
        # Create Company
        company = Company(name='Test Corp', required_skills='Python', average_salary=12.0)
        db.session.add(company)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'password'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_send_invitation(self):
        # Initial count
        self.assertEqual(DriveInvitation.query.count(), 0)
        
        # Send Invite
        response = self.client.post('/admin/invite/1', data={
            'subject': 'Test Invite',
            'message': 'Please come.'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DriveInvitation.query.count(), 1)
        invite = DriveInvitation.query.first()
        self.assertEqual(invite.subject, 'Test Invite')
        self.assertEqual(invite.company.name, 'Test Corp')

    def test_invitation_list(self):
        # Create Dummy Invite
        inv = DriveInvitation(company_id=1, subject='List Test', message='Body')
        db.session.add(inv)
        db.session.commit()
        
        response = self.client.get('/admin/invitations')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'List Test', response.data)

if __name__ == '__main__':
    unittest.main()
