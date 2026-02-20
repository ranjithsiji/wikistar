from flask import Flask
from config import Config
from extensions import db, cors, oauth
from routes.main import main_bp
from routes.auth import auth_bp
from routes.editathons import editathons_bp
from routes.articles import articles_bp
from routes.users import users_bp
import os
from initialization import create_tables, auto_import_data, test_connection

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, supports_credentials=True)
    oauth.init_app(app)

    # Register MediaWiki OAuth 2.0 client
    oauth.register(
        name='mediawiki',
        client_id=app.config.get('MW_CLIENT_ID'),
        client_secret=app.config.get('MW_CLIENT_SECRET'),
        authorize_url='https://meta.wikimedia.org/w/rest.php/oauth2/authorize',
        access_token_url='https://meta.wikimedia.org/w/rest.php/oauth2/access_token',
        client_kwargs={
            'scope': 'openid profile',
            'headers': {
                'User-Agent': 'WikiSTAR/1.0 (https://github.com/alphaf42/Starkforge_reviewtool; alphaf42@example.org)'
            }
        },
    )
    print("✅ MediaWiki OAuth 2.0 enabled")

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(editathons_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(users_bp)

    # Database initialization
    test_connection(app)
    create_tables(app)
    auto_import_data(app)

    return app
