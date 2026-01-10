from app import create_app, db
from models import Quiz, PlacementDrive, JobApplication, Student
from datetime import datetime

app = create_app()

with app.app_context():
    print(f"Current Time: {datetime.now()}")
    print("--- QUIZZES ---")
    for q in Quiz.query.all():
        print(f"ID: {q.id}, Title: {q.title}, DriveID: {q.drive_id}, Live: {q.is_live}, LiveAt: {q.live_at}")

    print("\n--- DRIVES ---")
    for d in PlacementDrive.query.all():
        print(f"ID: {d.id}, Job: {d.job_title}, Company: {d.company.name}")

    print("\n--- APPLICATIONS ---")
    for a in JobApplication.query.all():
        print(f"Student: {a.student_id}, Drive: {a.drive_id}")
        
    print("\n--- STUDENTS ---")
    for s in Student.query.all():
        print(f"ID: {s.id}, Name: {s.name}")

    print("\n--- ATTEMPTS ---")
    from models import QuizAttempt
    for qa in QuizAttempt.query.all():
        print(f"Student: {qa.student_id}, Quiz: {qa.quiz_id}, Score: {qa.score}")
