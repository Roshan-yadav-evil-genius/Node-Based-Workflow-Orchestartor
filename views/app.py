"""
Flask Application Factory
Creates and configures the Flask application.
"""

from flask import Flask
from pathlib import Path

from .routes import register_blueprints
from .services import create_services


def create_app(project_root: Path = None) -> Flask:
    """
    Application factory for creating Flask app.
    
    Args:
        project_root: Optional project root path.
                     Defaults to NewDesign folder.
    
    Returns:
        Configured Flask application.
    """
    # Get the views directory for template and static folders
    views_dir = Path(__file__).parent
    
    # Create Flask app with template and static folders
    app = Flask(
        __name__, 
        template_folder=str(views_dir / 'templates'),
        static_folder=str(views_dir / 'static')
    )
    
    # Initialize services and store in app extensions
    services = create_services(project_root)
    app.extensions['services'] = services
    
    # Register blueprints
    register_blueprints(app)
    
    return app


def run_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = True):
    """
    Run the Flask development server.
    
    Args:
        host: Host to bind to.
        port: Port to listen on.
        debug: Enable debug mode.
    """
    app = create_app()
    app.run(host=host, port=port, debug=debug)

