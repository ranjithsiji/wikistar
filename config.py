import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:maria123@localhost/wikifountain')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth
    SERVER_NAME_ENV = os.environ.get('SERVER_NAME')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    
    OAUTH_ENABLED = os.environ.get('OAUTH_ENABLED', 'false').lower() == 'true'
    MW_CLIENT_ID = os.environ.get('MW_CLIENT_ID')
    MW_CLIENT_SECRET = os.environ.get('MW_CLIENT_SECRET')
    MW_METADATA_URL = os.environ.get('MW_METADATA_URL', 'https://meta.wikimedia.org/w/rest.php/oauth2/discovery')
