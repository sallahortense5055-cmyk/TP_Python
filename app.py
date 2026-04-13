from flask import Flask
from flask_cors import CORS
from extensions import db, migrate
from config import Config
import models  # noqa


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)  # autorise les requêtes depuis le navigateur

    db.init_app(app)
    migrate.init_app(app, db)

    from routes import main
    app.register_blueprint(main)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)