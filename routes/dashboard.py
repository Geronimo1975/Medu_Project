from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import QuizAttempt, UserCourse, Course
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # Get quiz performance statistics
    quiz_stats = QuizAttempt.query.with_entities(
        func.avg(QuizAttempt.score).label('average_score'),
        func.count(QuizAttempt.id).label('total_attempts')
    ).filter_by(user_id=current_user.id).first()

    # Get course progress
    enrolled_courses = UserCourse.query.filter_by(user_id=current_user.id).all()
    course_progress = []
    for enrollment in enrolled_courses:
        course = Course.query.get(enrollment.course_id)
        total_quizzes = len(course.quizzes)
        completed_quizzes = QuizAttempt.query.join(Quiz).filter(
            QuizAttempt.user_id == current_user.id,
            Quiz.course_id == course.id,
            QuizAttempt.completed_at.isnot(None)
        ).count()
        
        progress = {
            'course': course,
            'progress': (completed_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0,
            'completed_quizzes': completed_quizzes,
            'total_quizzes': total_quizzes
        }
        course_progress.append(progress)

    # Get performance by language
    language_performance = QuizAttempt.query.join(Quiz).with_entities(
        Quiz.language,
        func.avg(QuizAttempt.score).label('average_score'),
        func.count(QuizAttempt.id).label('attempts')
    ).filter(
        QuizAttempt.user_id == current_user.id
    ).group_by(Quiz.language).all()

    # Get recent performance trend (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    performance_trend = QuizAttempt.query.filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.completed_at >= thirty_days_ago
    ).order_by(QuizAttempt.completed_at).all()

    return render_template('dashboard/index.html',
                         quiz_stats=quiz_stats,
                         course_progress=course_progress,
                         language_performance=language_performance,
                         performance_trend=performance_trend)
