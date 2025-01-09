from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from models import Quiz, Question, QuizAttempt, Course
from extensions import db
import os
from datetime import datetime

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

@quiz_bp.route('/generate', methods=['POST'])
@login_required
def generate_quiz():
    """Generate a new quiz using AI"""
    course_id = request.form.get('course_id')
    language = request.form.get('language', 'en')
    topic = request.form.get('topic')
    difficulty = request.form.get('difficulty', 'medium')
    
    course = Course.query.get_or_404(course_id)
    
    # Create new quiz
    quiz = Quiz(
        title=f"Quiz on {topic}",
        description=f"AI generated quiz about {topic}",
        course_id=course_id,
        language=language,
        difficulty=difficulty
    )
    db.session.add(quiz)
    db.session.commit()
    
    return jsonify({
        'message': 'Quiz created successfully',
        'quiz_id': quiz.id
    }), 201

@quiz_bp.route('/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    """View a specific quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz/view.html', quiz=quiz)

@quiz_bp.route('/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start a quiz attempt"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Create new attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        started_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()
    
    return jsonify({
        'message': 'Quiz attempt started',
        'attempt_id': attempt.id
    })

@quiz_bp.route('/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    """Submit quiz answers"""
    quiz = Quiz.query.get_or_404(quiz_id)
    answers = request.get_json()
    
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first_or_404()
    
    # Calculate score
    total_questions = len(quiz.questions)
    correct_answers = 0
    for question in quiz.questions:
        if str(question.id) in answers and answers[str(question.id)] == question.correct_answer:
            correct_answers += 1
    
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Update attempt
    attempt.score = score
    attempt.answers = answers
    attempt.completed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Quiz submitted successfully',
        'score': score
    })

@quiz_bp.route('/<int:quiz_id>/results')
@login_required
def quiz_results(quiz_id):
    """View quiz results"""
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).order_by(QuizAttempt.completed_at.desc()).first_or_404()
    
    return render_template('quiz/results.html', quiz=quiz, attempt=attempt)
