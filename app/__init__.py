from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.depot import depot_bp
    from app.routes.downloads import downloads_bp
    from app.routes.tokens import tokens_bp
    from app.routes.health import health_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(depot_bp)
    app.register_blueprint(downloads_bp)
    app.register_blueprint(tokens_bp)
    app.register_blueprint(health_bp)

    return app