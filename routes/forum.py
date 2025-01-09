from flask import Blueprint, render_template
from models import ForumPost

forum_bp = Blueprint('forum', __name__, url_prefix='/forum')

@forum_bp.route('/')
def index():
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    return render_template('forum/index.html', posts=posts)

@forum_bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return render_template('forum/post.html', post=post)
