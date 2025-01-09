from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, login_manager
from werkzeug.security import generate_password_hash
from models import User, Course, UserCourse, ForumPost, ForumReply
from app import db, app
import stripe

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')
courses = Blueprint('courses', __name__, url_prefix='/courses')
forum = Blueprint('forum', __name__, url_prefix='/forum')

@main.route('/')
def index():
    featured_courses = Course.query.limit(6).all()
    return render_template('home.html', courses=featured_courses)

# Auth routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid email or password')
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))

        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# Course routes
@courses.route('/catalog')
def catalog():
    courses = Course.query.all()
    return render_template('courses/catalog.html', courses=courses)

@courses.route('/<int:course_id>')
def view(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('courses/view.html', course=course)

@courses.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    if course.is_premium:
        stripe.api_key = app.config['STRIPE_SECRET_KEY']
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

# Forum routes
@forum.route('/')
def index():
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    return render_template('forum/index.html', posts=posts)

@forum.route('/post/<int:post_id>')
def view_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return render_template('forum/post.html', post=post)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))