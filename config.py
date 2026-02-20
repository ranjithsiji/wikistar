import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:maria123@localhost/wikifountain')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    # MediaWiki OAuth 2.0
    MW_CLIENT_ID = os.environ.get('MW_CLIENT_ID')
    MW_CLIENT_SECRET = os.environ.get('MW_CLIENT_SECRET')
