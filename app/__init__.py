from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from urllib.parse import quote_plus  # Used to safely encode password

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Get database connection details from environment variables (set by Ansible)
    db_host = os.getenv('DATABASE_HOST')
    db_port = os.getenv('DATABASE_PORT', '5432')
    db_name = os.getenv('DATABASE_NAME')
    db_user = os.getenv('DATABASE_USER')
    db_password = os.getenv('DATABASE_PASSWORD')

    if db_host and db_user and db_name and db_password:
        # Build secure PostgreSQL URI using the real RDS values
        # quote_plus ensures special characters in password are handled correctly
        encoded_password = quote_plus(db_password)
        database_uri = (
            f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
        )
    else:
        # Fallback for local development when env vars are not set
        database_uri = 'postgresql://taskapp_user:taskapp_password@localhost:5432/taskapp'

    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Secret key for sessions / JWT (use a strong random value in production)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    db.init_app(app)
    CORS(app)

    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        # Only create tables and seed in development
        if os.getenv('FLASK_ENV') != 'production':
            db.create_all()

            # Seed default users only if the table is empty
            from app.models import User
            from werkzeug.security import generate_password_hash

            if User.query.count() == 0:
                users = [
                    User(username='admin', password_hash=generate_password_hash('admin123')),
                    User(username='user', password_hash=generate_password_hash('user123')),
                ]
                for user in users:
                    db.session.add(user)
                db.session.commit()
                print("Seeded default users")

    return app
