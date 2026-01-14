from app import app
from extensions import db
from models import Student, Backlog

with app.app_context():
    # Find the logged in student (assuming session cookie... but here we just pick the first one or specific roll no)
    # We'll just pick the first student for testing logic
    s = Student.query.first()
    if s:
        print(f"Testing with Student: {s.name} (ID: {s.id})")
        print(f"Current Backlogs Count: {s.backlogs}")
        
        # Clear existing backlogs for clean test
        Backlog.query.filter_by(student_id=s.id).delete()
        
        # Add a test backlog
        b1 = Backlog(student_id=s.id, subject_name="Applied Math", semester=2)
        b2 = Backlog(student_id=s.id, subject_name="Data Structures", semester=3)
        db.session.add(b1)
        db.session.add(b2)
        
        # Update student count
        s.backlogs = 2
        s.metric_type = 'backlogs' # This field doesn't exist in DB, only form, but we rely on backlogs>0 logic
        
        db.session.commit()
        print("✓ Injected 2 test backlogs.")
        print(f"Verify List: {[b.subject_name for b in s.backlogs_list]}")
    else:
        print("No student found to test.")
