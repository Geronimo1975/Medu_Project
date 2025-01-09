from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import User, Course, Quiz, QuizAttempt, LearningPath, LearningPathItem
from extensions import db
from sqlalchemy import func
import json

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')

def calculate_user_strengths(user_id):
    """Calculate user's strong subjects based on quiz performance"""
    strengths = QuizAttempt.query.join(Quiz).with_entities(
        Quiz.course_id,
        func.avg(QuizAttempt.score).label('avg_score')
    ).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.completed_at.isnot(None)
    ).group_by(Quiz.course_id).all()
    
    return {str(course_id): float(score) for course_id, score in strengths}

def generate_learning_path(user_id):
    """Generate personalized learning path based on user performance and preferences"""
    user = User.query.get(user_id)
    strengths = calculate_user_strengths(user_id)
    
    # Get courses the user hasn't taken yet
    enrolled_courses = [uc.course_id for uc in user.courses]
    available_courses = Course.query.filter(
        ~Course.id.in_(enrolled_courses) if enrolled_courses else True
    ).all()
    
    # Create new learning path
    learning_path = LearningPath(
        user_id=user_id,
        title=f"Personalized Path for {user.username}",
        description="Generated based on your performance and interests",
        difficulty_level="intermediate"
    )
    db.session.add(learning_path)
    
    # Add courses to path based on prerequisites and user performance
    for i, course in enumerate(available_courses):
        # Check if user has completed prerequisites
        if course.prerequisites:
            prereqs = json.loads(course.prerequisites)
            if not all(str(prereq_id) in strengths and strengths[str(prereq_id)] >= 70 
                      for prereq_id in prereqs):
                continue
        
        path_item = LearningPathItem(
            path_id=learning_path.id,
            course_id=course.id,
            order=i+1,
            required=True
        )
        db.session.add(path_item)
    
    db.session.commit()
    return learning_path

@recommendations_bp.route('/')
@login_required
def index():
    """Show user's recommended learning paths"""
    learning_paths = LearningPath.query.filter_by(user_id=current_user.id).all()
    return render_template('recommendations/index.html', 
                         learning_paths=learning_paths)

@recommendations_bp.route('/generate', methods=['POST'])
@login_required
def create_recommendation():
    """Generate new learning path recommendations"""
    learning_path = generate_learning_path(current_user.id)
    return jsonify({
        'message': 'Learning path generated successfully',
        'path_id': learning_path.id
    }), 201

@recommendations_bp.route('/<int:path_id>')
@login_required
def view_path(path_id):
    """View specific learning path details"""
    learning_path = LearningPath.query.get_or_404(path_id)
    if learning_path.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    path_items = LearningPathItem.query.filter_by(path_id=path_id)\
        .order_by(LearningPathItem.order).all()
    
    return render_template('recommendations/view.html',
                         learning_path=learning_path,
                         path_items=path_items)
