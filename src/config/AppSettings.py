
from flask_cors import CORS  # Optional: For Cross-Origin Resource Sharing
import logging
from flask_jwt_extended import JWTManager

from src.Helpers.PipelineMonitor import PipelineMonitor, PipelineStatus
from src.Modules.Integration.FileWatcherService import ConfigManager, MonitoredFileWatcher
from src.Modules.Profiling.ProfilerCoordinator import MonitoredProfilerCoordinator
from src.config.DBModelsConfig import db
from src.Modules.Auth.AuthService import AuthService
from src.config.PipeLineMonitorDecl import pipelineMonitor
from src.config.ProfilerConfig import init_profiler
import threading


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

    # Initialize Pipeline Monitor
    # pipeline_monitor = PipelineMonitor()
    app.pipeline_monitor = pipelineMonitor

    try:
        # Initialize the monitored file watcher
        watcher_config = ConfigManager(
            watch_folder=config.getConfig()["watcher"]["watcher_folder"],
            failed_folder=config.getConfig()["watcher"]["failed_folder"],
            check_interval=config.getConfig()["watcher"]["check_interval"]
        )

        # Create and start monitored file watcher in a separate thread
        watcher = MonitoredFileWatcher(app, watcher_config, pipelineMonitor)
        watcher_thread = threading.Thread(target=watcher.watch, daemon=True)
        watcher_thread.start()

        # Store watcher instances in app context
        app.file_watcher = watcher
        app.watcher_thread = watcher_thread

        logger.info("File watcher initialized and started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize file watcher: {str(e)}")
        pipelineMonitor.update_pipeline_state(
            "file_watcher",
            PipelineStatus.ERROR,
            error_message=f"Failed to initialize: {str(e)}"
        )

    # Initialize and start the monitored profiler
    try:
        profiler = MonitoredProfilerCoordinator(
            github_token=config.getConfig()["profiler"]["github_token"],
            google_api_key=config.getConfig()["profiler"]["google_api_key"],
            monitor=pipelineMonitor
        )
        profiler.start_scheduling()
        app.profiler = profiler
        logger.info("Profiler schedules initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize profiler schedules: {str(e)}")
        pipelineMonitor.update_pipeline_state(
            "scheduler",
            PipelineStatus.ERROR,
                error_message=f"Failed to initialize: {str(e)}"
        )

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

    logging.info("Application initialized with database URI: %s", db_uri)

    # Register Blueprints (controllers)
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Register custom error handling
    for error, handler in error_handlers:
        app.register_error_handler(error, handler)

    return app
