from app import create_app, db
from models import Student, Quiz, QuizAttempt, JobApplication
from datetime import datetime

app = create_app()

with app.app_context():
    # Simulate Student 2 (Tanu)
    student_id = 2
    student = Student.query.get(student_id)
    if not student:
        print(f"Student {student_id} not found!")
        exit()
        
    print(f"Checking for Student: {student.name} (ID: {student.id})")
    
    # 1. Get Applied Drive IDs
    applied_drive_ids = [app.drive_id for app in student.applications]
    print(f"Applied Drive IDs: {applied_drive_ids}")
    
    # 2. Query Quizzes
    if not applied_drive_ids:
        print("No applied drives.")
    else:
        quizzes_query = Quiz.query.filter(Quiz.drive_id.in_(applied_drive_ids))
        all_quizzes = quizzes_query.all()
        print(f"Found {len(all_quizzes)} potential quizzes linked to applied drives.")
        
        now = datetime.now()
        print(f"Current Time: {now}")
        
        for quiz in all_quizzes:
            print(f"  Quiz ID: {quiz.id}, Title: {quiz.title}, DriveID: {quiz.drive_id}")
            print(f"  Live: {quiz.is_live}, LiveAt: {quiz.live_at}")
            
            is_live_now = quiz.is_live or (quiz.live_at and quiz.live_at <= now)
            print(f"  Is Live Now? {is_live_now}")
            
            if is_live_now:
                attempt = QuizAttempt.query.filter_by(student_id=student.id, quiz_id=quiz.id).first()
                print(f"  Attempt Found? {attempt}")
                
                if attempt:
                    print("  -> SHOW SCORE")
                else:
                    print("  -> SHOW START BUTTON")
            else:
                print("  -> HIDDEN (Not Live)")
