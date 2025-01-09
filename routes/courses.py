from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from models import Course, UserCourse
from extensions import db
import stripe
from config import Config

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')

@courses_bp.route('/catalog')
def catalog():
    courses = Course.query.all()
    return render_template('courses/catalog.html', courses=courses)

@courses_bp.route('/<int:course_id>')
def view(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('courses/view.html', course=course)

@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    if course.is_premium:
        stripe.api_key = Config.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.title,
                    },
                    'unit_amount': int(course.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('courses.enrollment_success', course_id=course.id, _external=True),
            cancel_url=url_for('courses.view', course_id=course.id, _external=True),
        )
        return jsonify({'id': session.id})

    enrollment = UserCourse(user_id=current_user.id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    return redirect(url_for('courses.view', course_id=course_id))

@courses_bp.route('/<int:course_id>/enrollment/success')
@login_required
def enrollment_success(course_id):
    enrollment = UserCourse(user_id=current_user.id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    flash('Successfully enrolled in the course!', 'success')
    return redirect(url_for('courses.view', course_id=course_id))