"""
Routes Package
Flask blueprints for pages and API endpoints.
"""

from .pages import pages_bp
from .api import api_bp


def register_blueprints(app):
    """
    Register all blueprints with the Flask app.
    
    Args:
        app: Flask application instance.
    """
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)


__all__ = [
    'pages_bp',
    'api_bp',
    'register_blueprints',
]

