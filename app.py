
from flask import Flask
from marshmallow import ValidationError

# from api.config import config
from src.config.AppSettings import Config, createApp

# Import controllers
from src.Controllers.AuthController import AUTH_CONTROLLER


# Import error custom handling
from src.Helpers.ErrorHandling import handleValidationError, handleGenericError


def main():
    # Custom error handling
    error_handlers = [
        # (500, handle_generic_error),
        (Exception, handleGenericError),
        (ValidationError, handleValidationError),
    ]

    # Blueprints
    blueprints = [AUTH_CONTROLLER,]

    # Load configuration
    config = Config()
    app = createApp(
        Flask(__name__),
        config,
        blueprints=blueprints,
        error_handlers=error_handlers
    )

    try:
        options = {
            "host": config.getConfig()["server"]["ip"],
            "port": config.getConfig()["server"]["port"],
            "debug": config.getConfig()["server"]["debug"]
        }

        app.run(**options)

    except KeyError as e:
        print(f"Configuration error: Missing {e} in the configuration.")
        exit(1)


if __name__ == '__main__':
    main()
