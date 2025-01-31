from flask import Flask
from flask_cors import CORS  # Optional: For Cross-Origin Resource Sharing
import logging
from flask_jwt_extended import JWTManager
from src.Modules.Candidate.Relationships import init_models
from src.PipeLines.Integration.EmailWatcher.EmailWatcherPipeLine import EmailMonitorConfig, EmailMonitorPipeline
from src.PipeLines.Integration.FileWatcher.FileWatcherService import FileWatcherPipelineConfig, FileWatcherPipeline
from src.PipeLines.PipeLineManagement.PipeLineManager import PipelineManager
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.CreateProfile.ProfileCreationPipeline import ProfileCreationConfig, \
    ProfileCreationPipeline
from src.PipeLines.Profiling.DataScraping.GitHubScrap.GitHubScrapingPipeline import GitHubScrapingConfig, \
    GitHubScrapingPipeline
from src.PipeLines.Profiling.DataScraping.GoogleScrap.GoogleScrapingPipeline import GoogleScrapingConfig, \
    GoogleScrapingPipeline
from src.PipeLines.Profiling.DataScraping.LinkedInScrap.LinkedInScrapper import LinkedInScrapingConfig, \
    LinkedInScrapingPipeline
from src.PipeLines.Profiling.TextExtraction.TextExtractionPipeline import TextExtractionPipelineConfig, \
    TextExtractionPipeline
from src.config.DBModelsConfig import db
from src.Modules.Auth.AuthService import AuthService
import threading


def init_pipelines(app: Flask, config: dict):
    print("my configs: ", config)
    """Initialize and start pipeline system"""
    monitor = PipelineMonitor()
    manager = PipelineManager(app)  # Pass app to manager

    # Add Email Monitor pipeline configuration and initialization

    # Register and add LinkedIn scraper pipeline
    # linkedin_scraping_config = LinkedInScrapingConfig(
    #     name="linkedin_scraping",
    #     batch_size=config["profiler"]["batch_size"],
    #     process_interval=config["profiler"]["intervals"]["linkedin_scraping"] * 60,  # Convert to seconds
    #     linkedin_email=config["profiler"]["linkedin_credentials"]["email"],
    #     linkedin_password=config["profiler"]["linkedin_credentials"]["password"],
    #     headless=True
    # )
    # linkedin_pipeline = LinkedInScrapingPipeline(app, linkedin_scraping_config, monitor)
    # manager.register_pipeline(linkedin_pipeline)

    # Register and add profile creation pipeline
    profile_creation_config = ProfileCreationConfig(
        name="profile_creation",
        batch_size=config["profiler"]["batch_size"],
        process_interval=config["profiler"]["intervals"]["profile_creation"] * 60,  # Convert to seconds
        technical_weight=config["profiler"]["scoring"]["weights"]["technical"],
        experience_weight=config["profiler"]["scoring"]["weights"]["experience"],
        github_weight=config["profiler"]["scoring"]["weights"]["github"],
        min_passing_score=config["profiler"]["scoring"]["min_passing_score"]
    )
    profile_creation_pipeline = ProfileCreationPipeline(app, profile_creation_config, monitor)
    manager.register_pipeline(profile_creation_pipeline)

    # Register and add email watcher pipeline
    email_monitor_config = EmailMonitorConfig(
        name="email_monitor",
        batch_size=config["email_pipe_line"]["batch_size"],
        process_interval=config["email_pipe_line"]["check_interval"] * 60,  # Convert minutes to seconds
        start_date="2025-01-20",
        end_date="2025-03-20",
        email_folder=config["email_pipe_line"]["folder"],
        attachment_types=config["email_pipe_line"]["allowed_attachments"]
    )
    email_monitor_pipeline = EmailMonitorPipeline(app, email_monitor_config, monitor)
    manager.register_pipeline(email_monitor_pipeline)

    # Register and add github scrapper pipeline
    github_scraping_config = GitHubScrapingConfig(
        name="github_scraping",
        batch_size=config["profiler"]["batch_size"],
        process_interval=config["profiler"]["intervals"]["github_scraping"] * 60,
        github_token=config["profiler"]["github_token"]
    )
    github_pipeline = GitHubScrapingPipeline(app, github_scraping_config, monitor)
    manager.register_pipeline(github_pipeline)

    # Register and add google scrapper pipeline
    google_scraping_config = GoogleScrapingConfig(
        name="google_scraping",
        batch_size=config["profiler"]["batch_size"],
        process_interval=config["profiler"]["intervals"]["google_scraping"] * 60,
        api_key=config["profiler"]["google_api_key"],
        google_url=config["profiler"]["google_search_url"]
    )
    google_pipeline = GoogleScrapingPipeline(app, google_scraping_config, monitor)
    manager.register_pipeline(google_pipeline)

    # Register and add text extraction pipeline
    text_extraction_config = TextExtractionPipelineConfig(
        name="text_extraction",
        batch_size=config["profiler"]["batch_size"],
        process_interval=config["profiler"]["intervals"]["text_extraction"] * 60,
        resume_path=config["assets"]["resume"],
        json_resume_path=config["assets"]["json_resume"],
    )
    text_pipeline = TextExtractionPipeline(app, text_extraction_config, monitor)
    manager.register_pipeline(text_pipeline)

    # Register and add file watcher pipeline
    file_watcher_config = FileWatcherPipelineConfig(
        name="file_watcher",
        batch_size=10,  # Process up to 10 XML files per batch
        process_interval=config["watcher"]["check_interval"] * 60,  # Convert minutes to seconds
        watch_folder=config["watcher"]["watcher_folder"],
        failed_folder=config["watcher"]["failed_folder"],
        resume_path=config["assets"]["resume"],
    )
    file_watcher_pipeline = FileWatcherPipeline(app, file_watcher_config, monitor)
    manager.register_pipeline(file_watcher_pipeline)

    # Store pipeline components in app context
    app.pipeline_monitor = monitor
    app.pipeline_manager = manager

    # Start pipelines immediately
    with app.app_context():
        manager.start_all()

    return app

def createApp(flask_app, config, blueprints=None, error_handlers=None):
    """Create and configure the Flask application."""

    # db = SQLAlchemy()

    if blueprints is None:
        blueprints = []

    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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
    init_models()
    # Create all tables
    with app.app_context():
        db.create_all()
        try:
            auth_service = AuthService()
            auth_service.initialize_admin_user("admin@gmail.com", "admin1")
        except Exception as e:
            print(f"Failed to initialize admin user: {str(e)}")
        finally:
            app = init_pipelines(app, config.getConfig())

    @app.teardown_appcontext
    def cleanup(exception=None):
        # Skip cleanup if we're in a background thread
        if hasattr(app, 'pipeline_manager') and threading.current_thread() != threading.main_thread():
            return
        if hasattr(app, 'pipeline_manager'):
            try:
                app.pipeline_manager.stop_all()
            except Exception as e:
                app.logger.warning(f"Cleanup error: {str(e)}")

    # Optional: Configure CORS
    CORS(app)

    logging.info("Application initialized with database URI: %s", db_uri)

    # Register Blueprints (controllers)
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Register custom error handling
    for error, handler in error_handlers:
        app.register_error_handler(error, handler)

    return app
