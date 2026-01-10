import unittest
from app import create_app, db
from config import Config
from models import Student, Company

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class SkillMatchTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_student_skill_match(self):
        # Create Students
        s1 = Student(roll_no='101', name='Python dev', email='s1@test.com', mobile='1234567890', department='IT', semester=1, password_hash='hash', skills='Python, Django, SQL', status='Approved')
        s2 = Student(roll_no='102', name='Java dev', email='s2@test.com', mobile='0987654321', department='CS', semester=1, password_hash='hash', skills='Java, Spring, SQL', status='Approved')
        db.session.add_all([s1, s2])
        db.session.commit()
        
        # Test Search Logic (Basic simulation of what's in the route)
        skills_query = 'Python'
        results = []
        required_skills = [s.strip() for s in skills_query.split(',') if s.strip()]
        
        all_students = Student.query.filter_by(status='Approved').all()
        scored_students = []
        
        for student in all_students:
            student_skills = [s.strip().lower() for s in (student.skills or '').split(',')]
            score = 0
            for req in required_skills:
                if any(req.lower() in s for s in student_skills):
                    score += 1
            if score > 0:
                scored_students.append(student)
                
        self.assertEqual(len(scored_students), 1)
        self.assertEqual(scored_students[0].name, 'Python dev')

    def test_company_skill_match(self):
        # Create Companies
        c1 = Company(name='PyCorp', required_skills='Python, Flask', average_salary=10.0, location='Bangalore')
        
        c2 = Company(name='JavaCorp', required_skills='Java, Spring', average_salary=8.0, location='Pune')
        db.session.add_all([c1, c2])
        db.session.commit()
        
        # Test Search logic
        skills_query = 'Python'
        location_query = 'Bangalore'
        min_salary = 9.0
        
        # Filter DB level
        query = Company.query
        if location_query:
            query = query.filter(Company.location.ilike(f'%{location_query}%'))
        if min_salary > 0:
            query = query.filter(Company.average_salary >= min_salary)
            
        companies = query.all()
        self.assertEqual(len(companies), 1)
        self.assertEqual(companies[0].name, 'PyCorp')
        
        # Check skill match
        required_skills = [s.strip() for s in skills_query.split(',') if s.strip()]
        score = 0
        comp_skills = [s.strip().lower() for s in (companies[0].required_skills or '').split(',')]
        for req in required_skills:
             if any(req.lower() in s for s in comp_skills):
                 score += 1
        self.assertEqual(score, 1)

if __name__ == '__main__':
    unittest.main()
