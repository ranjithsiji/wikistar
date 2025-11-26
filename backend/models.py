from database import db
from datetime import datetime
import json

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(40), default='user')  # 'admin' or 'juror' or 'user'

class Editathon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    code = db.Column(db.String(64))
    project = db.Column(db.String(32))
    description = db.Column(db.Text)
    startDate = db.Column(db.DateTime)
    endDate = db.Column(db.DateTime)
    consensualVote = db.Column(db.Boolean, default=False)
    hiddenMarks = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='draft')
    createdBy = db.Column(db.Integer)  # user id

class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathon.id'), nullable=False)
    type = db.Column(db.String(80))
    config = db.Column(db.Text)  # json string
    optional = db.Column(db.Boolean, default=False)
    showInJuryTool = db.Column(db.Boolean, default=True)

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer)
    articleId = db.Column(db.String(200))
    user_id = db.Column(db.Integer)
    decision = db.Column(db.Boolean)  # yes/no
    points = db.Column(db.Float, default=0.0)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MarkConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathon.id'), nullable=False)
    type = db.Column(db.String(80))
    title = db.Column(db.String(250))
    config = db.Column(db.Text)  # json string
    optional = db.Column(db.Boolean, default=False)
    showInJuryTool = db.Column(db.Boolean, default=True)
