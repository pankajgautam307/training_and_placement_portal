import unittest
from app import create_app, db
from config import Config
from models import AdminUser, Company, PlacementDrive

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class DriveEditTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.admin = AdminUser(username='admin', email='admin@test.com')
        self.admin.set_password('pass')
        db.session.add(self.admin)
        
        self.company = Company(name='Test Corp')
        db.session.add(self.company)
        db.session.commit()
        
        # Create initial drive
        self.drive = PlacementDrive(
            company_id=self.company.id,
            job_title='Initial Title',
            job_description='Desc',
            salary='5 LPA'
        )
        db.session.add(self.drive)
        db.session.commit()
        
        self.client = self.app.test_client()
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'pass'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_edit_drive(self):
        # 1. Check Edit Page Load
        resp = self.client.get(f'/admin/drive/{self.drive.id}/edit')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Edit Placement Drive', resp.data)
        self.assertIn(b'Initial Title', resp.data)
        
        # 2. Update Drive
        resp = self.client.post(f'/admin/drive/{self.drive.id}/edit', data={
            'company_id': self.company.id,
            'job_title': 'Updated Title',
            'job_description': 'New Desc',
            'salary': '10 LPA',
            'quiz_id': 0 # No quiz
        }, follow_redirects=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Placement Drive updated successfully', resp.data)
        self.assertIn(b'Updated Title', resp.data)
        
        # Verify DB
        updated_drive = PlacementDrive.query.get(self.drive.id)
        self.assertEqual(updated_drive.job_title, 'Updated Title')
        self.assertEqual(updated_drive.salary, '10 LPA')

if __name__ == '__main__':
    unittest.main()
