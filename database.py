"""Database initialization and configuration for gesture_gen."""

import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Default paths for data storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
DATABASE_PATH = os.path.join(DATA_DIR, 'gesture_gen.db')


def init_db(app):
    """Initialize database with Flask app."""
    # Ensure data directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extension
    db.init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()

    return db


def get_images_dir():
    """Return the path to the images directory."""
    return IMAGES_DIR
