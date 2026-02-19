from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
cors = CORS()
oauth = OAuth()
