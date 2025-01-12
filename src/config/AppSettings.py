import yaml
import os
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Optional: For Cross-Origin Resource Sharing
import logging
from flask_jwt_extended import JWTManager

from src.config.DBModelsConfig import db
from src.Modules.Auth.AuthService import AuthService


class Config:
    def __init__(self):
        self.cached = 0
        # Update the file path if necessary
        self.file = os.path.join(os.path.dirname(__file__), 'config.yaml')
        self.config = {}

    def getConfig(self):
        # Check the modification time of the file
        stamp = os.stat(self.file).st_mtime

        # Load the config file if it has been modified since last load
        if stamp != self.cached:
            self.cached = stamp

            try:
                # Using a context manager to open the file
                with open(self.file, 'r') as f:
                    self.config = yaml.safe_load(f)  # Load the YAML configuration
            except FileNotFoundError:
                print(f"Configuration file '{self.file}' not found.")
                self.config = {}  # Or handle it as needed
            except yaml.YAMLError as exc:
                print(f"Error parsing YAML file: {exc}")
                self.config = {}  # Or handle it as needed

        return self.config


def createApp(flask_app, config, blueprints=None, error_handlers=None):
    """Create and configure the Flask application."""

    # db = SQLAlchemy()

    if blueprints is None:
        blueprints = []

    # Initialize Flask app
    app = flask_app

    # Load configuration
    db_uri = config.getConfig()["database"]["uri"]
    if not db_uri:
        raise ValueError("Database URI is not set in the configuration.")

    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.getConfig()["database"]["track_modifications"]
    app.config['JWT_SECRET_KEY'] = config.getConfig()["jwt"]["secret_key"]
    jwt = JWTManager(app)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Create all tables
    with app.app_context():
        db.create_all()
        auth_service = AuthService()
        try:
            auth_service.initialize_admin_user("admin@gmail.com", "admin1")
        except Exception as e:
            print(f"Failed to initialize admin user: {str(e)}")



    # Optional: Configure CORS
    CORS(app)

    # Optional: Configure logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Application initialized with database URI: %s", db_uri)

    # Register Blueprints (controllers)
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Register custom error handling
    for error, handler in error_handlers:
        app.register_error_handler(error, handler)

    return app
