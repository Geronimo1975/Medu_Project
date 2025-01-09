from flask import Blueprint, render_template
from models import Course

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_courses = Course.query.limit(6).all()
    return render_template('home.html', courses=featured_courses)
