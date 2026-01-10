from app import create_app, db
from models import Quiz, QuizAttempt, Student
from datetime import datetime

app = create_app()

with app.app_context():
    # 1. Setup Quiz with 80% passing
    quiz = Quiz.query.first()
    if not quiz:
        print("No quiz found.")
        exit()
        
    quiz.pass_percentage = 80.0
    db.session.commit()
    print(f"Set Quiz {quiz.id} pass_percentage to 80.0")
    
    # 2. Simulate Attempt (Score 60% - Fail)
    # Assume 10 questions, each 1 mark. Total 10.
    # Score 6.
    total_marks = 10
    score_fail = 6
    
    # Logic test (mimicking student.py)
    percentage_fail = (score_fail / total_marks * 100)
    required = quiz.pass_percentage
    passed_fail = percentage_fail >= required
    
    print(f"Attempt 1: Score {score_fail}/{total_marks} ({percentage_fail}%) Required: {required}% -> Passed? {passed_fail}")
    if passed_fail:
        print("FAILURE: Should have failed.")
    else:
        print("SUCCESS: Correctly failed.")

    # 3. Simulate Attempt (Score 90% - Pass)
    score_pass = 9
    percentage_pass = (score_pass / total_marks * 100)
    passed_pass = percentage_pass >= required
    
    print(f"Attempt 2: Score {score_pass}/{total_marks} ({percentage_pass}%) Required: {required}% -> Passed? {passed_pass}")
    if passed_pass:
        print("SUCCESS: Correctly passed.")
    else:
        print("FAILURE: Should have passed.")
