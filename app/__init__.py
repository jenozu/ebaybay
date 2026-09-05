from pathlib import Path

from flask import Flask

from .config import Config, configure_logging, validate_production_config
from .extensions import csrf, db, migrate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    validate_production_config(app.config)
    configure_logging(app.config)

    app.config["UPLOAD_DIR"] = Path(app.config["UPLOAD_DIR"])
    app.config["EBAY_TOKEN_PATH"] = Path(app.config["EBAY_TOKEN_PATH"])
    app.config["BACKUP_DIR"] = Path(app.config["BACKUP_DIR"])
    app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from . import auth, listings, main, oauth
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(listings.bp)
    app.register_blueprint(oauth.bp)

    return app
