from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'coordinator', 'jury', 'user', 'participant'), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Editathon(db.Model):
    __tablename__ = 'editathons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    language = db.Column(db.String(10), default='en')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    wiki_domain = db.Column(db.String(100), default='en.wikipedia.org')
    status = db.Column(db.Enum('draft', 'pending', 'active', 'completed', 'archived', 'rejected'), default='draft')
    min_marks_needed = db.Column(db.Integer, default=1)
    marks_config = db.Column(db.JSON)
    is_published = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    wikipedia_url = db.Column(db.String(1000))
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'improved'), default='pending')
    points = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    submitted_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    last_modified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class EditathonJury(db.Model):
    __tablename__ = 'editathon_jury'
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('main', 'secondary'), default='main')
    added_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    jury_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criteria_scores = db.Column(db.JSON, nullable=False)
    total_score = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text)
    decision = db.Column(db.Enum('accept', 'reject', 'needs_work'), default='needs_work')
    marked_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)
    condition_text = db.Column(db.Text)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class EditathonRule(db.Model):
    __tablename__ = 'editathon_rules'
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('rules.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class EditathonStat(db.Model):
    __tablename__ = 'editathon_stats'
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), primary_key=True)
    total_articles = db.Column(db.Integer, default=0)
    total_participants = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    avg_score = db.Column(db.Numeric(5, 2), default=0)
    last_updated = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
