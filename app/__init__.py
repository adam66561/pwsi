from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/static")
    app.config.from_object(config_class)
    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.calculator import calculator_bp
    from app.routes.pension import pension_bp
    from app.routes.admin import admin_bp
    from app.routes.reports import reports_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(calculator_bp, url_prefix="/api/calculator")
    app.register_blueprint(pension_bp, url_prefix="/api/pension")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    with app.app_context():
        from app import models  # noqa: F401
        from app.services.seed import seed_database

        db.create_all()
        seed_database()

    return app
