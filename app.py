from flask import Flask
from config import Config
from extensions import db, cors, oauth
from routes.main import main_bp
from routes.auth import auth_bp
from routes.editathons import editathons_bp
from routes.articles import articles_bp
from routes.users import users_bp
from initialization import create_tables, auto_import_data, test_connection


from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')
    app.config.from_object(config_class)
    
    # Trust reverse proxy headers (Toolforge router)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, supports_credentials=True)
    oauth.init_app(app)

    # Register MediaWiki OAuth 2.0 client
    # authorize_url and access_token_url are derived from OAUTH_MWURI
    mwuri = app.config.get('OAUTH_MWURI', 'https://meta.wikimedia.org')
    oauth.register(
        name='mediawiki',
        client_id=app.config.get('CONSUMER_KEY'),
        client_secret=app.config.get('CONSUMER_SECRET'),
        authorize_url=f'{mwuri}/w/rest.php/oauth2/authorize',
        access_token_url=f'{mwuri}/w/rest.php/oauth2/access_token',
        client_kwargs={
            'headers': {
                'User-Agent': 'WikiSTAR/1.0 (https://wikistar.toolforge.org)'
            }
        },
    )
    print(f"✅ MediaWiki OAuth 2.0 → {mwuri}")

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(editathons_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(users_bp)

    # Database initialisation (errors are non-fatal on startup)
    test_connection(app)
    create_tables(app)
    auto_import_data(app)

    return app

# Expose app for Gunicorn / Toolforge
app = create_app()
