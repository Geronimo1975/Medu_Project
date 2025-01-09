import os
from flask import Flask
from config import Config
from extensions import db, login_manager, babel

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)

    login_manager.login_view = 'auth.login'

    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.courses import courses_bp
    from routes.forum import forum_bp
    from routes.quiz import quiz_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(dashboard_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app

app = create_app()

@login_manager.user_loader
def load_user(id):
    from models import User
    return User.query.get(int(id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)