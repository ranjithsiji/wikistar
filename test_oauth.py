from authlib.integrations.flask_client import OAuth
from flask import Flask

app = Flask(__name__)
oauth = OAuth(app)
oauth.register(
    name='mediawiki',
    client_id='123',
    client_secret='123',
    authorize_url='https://meta.wikimedia.org/w/rest.php/oauth2/authorize',
    access_token_url='https://meta.wikimedia.org/w/rest.php/oauth2/access_token',
)

with app.app_context():
    try:
        oauth.mediawiki.get('oauth2/resource/profile')
    except Exception as e:
        import traceback
        traceback.print_exc()

