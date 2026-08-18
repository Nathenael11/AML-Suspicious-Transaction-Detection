"""
AML Shield Flask Application Factory.

Initializes application instance, configures logging, registers blueprints,
and pre-warms the XGBoost model wrapper.
"""

import os
from flask import Flask
from app.utils import setup_logging
from app.routes import bp as main_bp, get_model

def create_app(test_config=None):
    """Application factory for AML Shield Web Application."""
    # Determine base directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(app_dir)
    
    templates_dir = os.path.join(root_dir, 'templates')
    static_dir = os.path.join(root_dir, 'static')
    
    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir
    )
    
    # Secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aml-shield-production-secret-key-2026')
    
    if test_config:
        app.config.update(test_config)

    # Initialize logging setup
    setup_logging()
    
    # Register blueprints
    app.register_blueprint(main_bp)

    # Pre-warm XGBoost model instance inside app context
    with app.app_context():
        get_model()

    return app
