import signal
import threading

from flask import Flask, send_from_directory
from marshmallow import ValidationError

from src.Controllers.AdminController import ADMIN_CONTROLLER
# from api.config import config
from src.config.AppSettings import createApp

# Import controllers
from src.Controllers.AuthController import AUTH_CONTROLLER
from src.Controllers.ScheduleMonitorController import MONITOR_CONTROLLER


# Import error custom handling
from src.Helpers.ErrorHandling import handleValidationError, handleGenericError
from src.config.ConfigBase import Config

def init_signal_handlers(app):
    def handle_shutdown(signum, frame):
        app.logger.info("Received shutdown signal")
        if hasattr(app, 'pipeline_manager'):
            try:
                # Only attempt shutdown from main thread
                if threading.current_thread() == threading.main_thread():
                    app.pipeline_manager.stop_all()
            except Exception as e:
                app.logger.error(f"Error during shutdown: {str(e)}")

    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)


def main():
    # Custom error handling
    error_handlers = [
        # (500, handle_generic_error),
        (Exception, handleGenericError),
        (ValidationError, handleValidationError),
    ]

    # Blueprints
    blueprints = [AUTH_CONTROLLER,MONITOR_CONTROLLER, ADMIN_CONTROLLER]

    # Load configuration
    config = Config()
    app = createApp(
        Flask(__name__),
        config,
        blueprints=blueprints,
        error_handlers=error_handlers
    )

    init_signal_handlers(app)

    # Dashboard routes
    @app.route('/')
    def dashboard():
        return send_from_directory('src/static', 'index.html')

    @app.route('/<path:filename>')
    def static_files(filename):
        return send_from_directory('src/static', filename)

    try:
        options = {
            "host": config.getConfig()["server"]["ip"],
            "port": config.getConfig()["server"]["port"],
            "debug": config.getConfig()["server"]["debug"],
            "use_reloader": False
        }

        app.run(**options)

    except KeyError as e:
        print(f"Configuration error: Missing {e} in the configuration.")
        exit(1)


if __name__ == '__main__':
    main()
