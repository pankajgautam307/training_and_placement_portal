from app import app
from extensions import db
from models import Student, Backlog

with app.app_context():
    # Target user Ahjghh (ID 5)
    s = Student.query.get(5)
    if s:
        print(f"Injecting backlogs for: {s.name} (ID: {s.id})")
        
        # Clear existing
        Backlog.query.filter_by(student_id=s.id).delete()
        
        # Add backlogs
        b1 = Backlog(student_id=s.id, subject_name="Maths-3", semester=3)
        b2 = Backlog(student_id=s.id, subject_name="Digital Logic", semester=3)
        db.session.add(b1)
        db.session.add(b2)
        
        s.backlogs = 2
        # Ensure CGPA cleared
        s.cgpa = 0 
        
        db.session.commit()
        print("✓ Injected 2 backlogs for Ahjghh.")
    else:
        print("User ID 5 not found.")
