from flask import Flask, jsonify, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pymysql
from flask_cors import CORS
import json
import ast
import sys
import os
from sqlalchemy import func

# Add Oauth to sys.path
from flask_mwoauth import MWOAuth
# from oauth_utils import patch_requests_for_oauth, test_mediawiki_connectivity

app = Flask(__name__)
# Enable CORS for frontend-backend communication (cookies needed for OAuth session)
CORS(app, supports_credentials=True)

# MariaDB database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maria123@localhost/wikifountain'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wikifountain.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Optional host/scheme override for OAuth callback generation
server_name = os.environ.get('SERVER_NAME')
if server_name:
    app.config['SERVER_NAME'] = server_name
    app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'http')

db = SQLAlchemy(app)

def format_project_label(raw_value: str | None) -> str:
    """Convert stored project identifier/domain into a human-friendly label."""
    if not raw_value:
        return "Wikipedia"

    domain = str(raw_value).strip()
    if not domain:
        return "Wikipedia"

    lowered = domain.lower()
    parts = lowered.split('.')
    first_part = parts[0] if parts else lowered
    second_level = parts[-2] if len(parts) >= 2 else lowered

    project_map = {
        'wikipedia': 'Wikipedia',
        'wiktionary': 'Wiktionary',
        'wikibooks': 'Wikibooks',
        'wikiquote': 'Wikiquote',
        'wikinews': 'Wikinews',
        'wikiversity': 'Wikiversity',
        'wikivoyage': 'Wikivoyage',
        'wikisource': 'Wikisource',
        'wikidata': 'Wikidata',
        'wikifunctions': 'Wikifunctions',
        'wikimediafoundation': 'Wikimedia Foundation',
        'metawiki': 'MetaWiki',
        'meta': 'MetaWiki',
        'wikicommons': 'Wikimedia Commons'
    }

    if second_level == 'wikimedia':
        meta_map = {
            'meta': 'MetaWiki',
            'commons': 'Wikimedia Commons',
            'incubator': 'Wikimedia Incubator'
        }
        if first_part in meta_map:
            return meta_map[first_part]
        return 'Wikimedia'

    if second_level in project_map:
        return project_map[second_level]

    cleaned = second_level.replace('-', ' ').replace('_', ' ').strip()
    if cleaned:
        return cleaned.title()

    return domain.title()

# ========== OAuth Configuration ==========
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

# Load OAuth credentials
creds_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'instance', 'Oauth', 'flask-mwoauth', 'credentials.do_not_commit.json')
)
consumer_key = os.environ.get('OAUTH_CONSUMER_KEY')
consumer_secret = os.environ.get('OAUTH_CONSUMER_SECRET')
OAUTH_ENABLED = os.environ.get('OAUTH_ENABLED', 'false').lower() == 'true'

try:
    if (not consumer_key or not consumer_secret) and os.path.exists(creds_path):
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            consumer_key = consumer_key or creds.get('consumer_key')
            consumer_secret = consumer_secret or creds.get('consumer_secret')
except Exception as e:
    print(f"Error loading credentials: {e}")

if OAUTH_ENABLED:
    if not consumer_key or not consumer_secret:
        print("WARNING: OAuth credentials not found. OAuth will not work.")
        consumer_key = 'dummy_key'
        consumer_secret = 'dummy_secret'

    mwoauth = MWOAuth(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        default_return_to='auth_success'
    )
    # Register without prefix so callback stays at /oauth-callback to match your consumer
    app.register_blueprint(mwoauth.bp)
    print("✅ OAuth enabled")
else:
    print("⚠️ OAuth disabled for development. Set OAUTH_ENABLED=true to enable.")
    # Add simple test login endpoint for development
    @app.route('/login')
    def dev_login():
        from flask import session
        session['mwoauth_username'] = 'TestUser'
        return redirect('http://localhost:5173/')
    
    @app.route('/oauth-callback')
    def dev_callback():
        return redirect('http://localhost:5173/')

# ========== SQLAlchemy Models for New Schema ==========

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'jury', 'participant'), default='participant')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Project Model
class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# Editathon Model
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
    status = db.Column(db.Enum('draft', 'active', 'completed', 'archived'), default='draft')
    min_marks_needed = db.Column(db.Integer, default=1)
    marks_config = db.Column(db.JSON)
    is_published = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Article Model
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

# Jury Assignment Model
class EditathonJury(db.Model):
    __tablename__ = 'editathon_jury'
    
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum('main', 'secondary'), default='main')
    added_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# Marks Model
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

# Rules Model
class Rule(db.Model):
    __tablename__ = 'rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)
    condition_text = db.Column(db.Text)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# Editathon Rules Model
class EditathonRule(db.Model):
    __tablename__ = 'editathon_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('rules.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# Audit Log Model
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

# Statistics Model
class EditathonStat(db.Model):
    __tablename__ = 'editathon_stats'
    
    editathon_id = db.Column(db.Integer, db.ForeignKey('editathons.id'), primary_key=True)
    total_articles = db.Column(db.Integer, default=0)
    total_participants = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    avg_score = db.Column(db.Numeric(5, 2), default=0)
    last_updated = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# ========== OAuth Routes ==========
@app.route('/auth_success')
def auth_success():
    username = mwoauth.get_current_user(True)
    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            # Create new user
            new_user = User(
                username=username,
                email=f"{username}@wikipedia.org", # Placeholder
                password_hash="oauth_user", # Placeholder
                role='participant'
            )
            db.session.add(new_user)
            db.session.commit()
    
    # Redirect to frontend
    # Assuming frontend is running on port 5173 (Vite default)
    return redirect("http://localhost:5173/")

@app.route('/api/me')
def get_current_user_api():
    username = mwoauth.get_current_user(True)
    if not username:
        return jsonify({"user": None})
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "email": user.email
            }
        })
    return jsonify({"user": {"username": username}})

@app.route('/api/login')
def api_login():
    return redirect(url_for('mwoauth.login'))

@app.route('/api/logout')
def api_logout():
    return redirect(url_for('mwoauth.logout'))

# ========== NEW SCHEMA API ROUTES ==========

# ========== HOME ROUTE ==========
@app.route('/')
def home():
    return jsonify({
        "message": "✅ Editathon Backend Connected to MariaDB (WikiFountain Schema)",
        "status": "success",
        "database": "wikifountain",
        "schema_version": "2.0",
        "tables": [
            "users",
            "projects",
            "editathons",
            "articles",
            "editathon_jury",
            "marks",
            "rules",
            "editathon_rules",
            "audit_logs",
            "editathon_stats"
        ]
    })

# ========== FRONTEND API ROUTES ==========

# 1. Personal Cabinet - Get User Statistics (Updated for New Schema)
@app.route('/api/personal-cabinet/<username>', methods=['GET'])
def get_personal_cabinet(username):
    try:
        # Get user from new database
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get user's articles
        user_articles = Article.query.filter_by(submitted_by=user.id).all()

        # Group articles by editathon
        articles_by_editathon = {}
        for article in user_articles:
            editathon = Editathon.query.get(article.editathon_id)
            if not editathon:
                continue
            if editathon.id not in articles_by_editathon:
                articles_by_editathon[editathon.id] = {
                    'editathon': editathon,
                    'articles': []
                }
            articles_by_editathon[editathon.id]['articles'].append(article)

        # Build response
        articles_data = []
        total_points = 0
        
        for entry in articles_by_editathon.values():
            editathon = entry['editathon']
            articles = entry['articles']
            for article in articles:
                articles_data.append({
                    'editathon': editathon.name,
                    'editathon_code': editathon.code,
                    'article_title': article.title,
                    'points': article.points,
                    'notes': article.notes,
                    'submitted_date': article.submitted_at.isoformat() if article.submitted_at else None,
                    'status': article.status
                })
                total_points += article.points or 0

        # Get created editathons
        created_editathons = Editathon.query.filter_by(created_by=user.id).all()
        created_data = [
            {
                'id': editathon.id,
                'name': editathon.name,
                'description': editathon.description,
                'status': editathon.status,
                'start_date': editathon.start_date.isoformat() if editathon.start_date else None,
                'end_date': editathon.end_date.isoformat() if editathon.end_date else None
            }
            for editathon in created_editathons
        ]

        # Get jury assignments
        jury_assignments = EditathonJury.query.filter_by(user_id=user.id).all()
        participated_as_jury = [
            {
                'editathon_id': assignment.editathon_id,
                'editathon_name': Editathon.query.get(assignment.editathon_id).name if Editathon.query.get(assignment.editathon_id) else 'Unknown',
                'role': assignment.role
            }
            for assignment in jury_assignments
        ]

        participated_response = []
        for entry in articles_by_editathon.values():
            editathon = entry['editathon']

            project_obj = Project.query.get(editathon.project_id) if getattr(editathon, 'project_id', None) else None
            project_label = format_project_label(project_obj.name if project_obj else None)

            scoreboard_rows = (
                db.session.query(
                    User.username,
                    func.coalesce(func.sum(Article.points), 0).label('total_points')
                )
                .join(User, Article.submitted_by == User.id)
                .filter(Article.editathon_id == editathon.id)
                .group_by(User.username)
                .order_by(func.coalesce(func.sum(Article.points), 0).desc())
                .all()
            )

            scoreboard = []
            user_rank = None
            user_points = 0
            for idx, row in enumerate(scoreboard_rows, start=1):
                points_value = float(row.total_points or 0)
                scoreboard.append({
                    'rank': idx,
                    'username': row.username,
                    'points': points_value
                })
                if row.username == user.username:
                    user_rank = idx
                    user_points = points_value

            participated_response.append({
                'id': editathon.id,
                'name': editathon.name,
                'description': editathon.description,
                'status': editathon.status,
                'start_date': editathon.start_date.isoformat() if editathon.start_date else None,
                'end_date': editathon.end_date.isoformat() if editathon.end_date else None,
                'language': editathon.language,
                'project': project_label,
                'project_domain': project_obj.name if project_obj else None,
                'scoreboard': scoreboard[:5],
                'user_summary': {
                    'rank': user_rank,
                    'points': user_points
                }
            })

        return jsonify({
            'username': user.username,
            'role': user.role,
            'stats': {
                'articles_submitted': len(user_articles),
                'editathons_participated': len(participated_response),
                'editathons_created': len(created_editathons),
                'total_points': total_points,
                'jury_assignments': len(jury_assignments)
            },
            'participated_editathons': participated_response,
            'created_editathons': created_data,
            'jury_assignments': participated_as_jury,
            'articles': articles_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Editathon Dashboard - Get Editathon Details
@app.route('/api/editathon/<editathon_id>', methods=['GET'])
def get_editathon_dashboard(editathon_id):
    try:
        # Get editathon from new schema
        editathon = Editathon.query.get(editathon_id)
        if not editathon:
            return jsonify({"error": "Editathon not found"}), 404

        project_obj = Project.query.get(editathon.project_id) if editathon.project_id else None
        project_label = format_project_label(project_obj.name if project_obj else None)
        
        # Get all articles for this editathon
        articles = Article.query.filter_by(editathon_id=editathon_id).all()
        
        # Calculate statistics
        users = set()
        total_articles = len(articles)
        total_points = 0
        articles_without_marks = 0
        
        # Build leaderboard
        user_stats = {}
        unreviewed_articles_mapped = []
        
        for article in articles:
            # Get article author
            author = User.query.get(article.submitted_by)
            if not author:
                continue
                
            username = author.username
            users.add(username)
            
            # Get marks for this article
            marks = Mark.query.filter_by(article_id=article.id).all()
            reviews = []
            article_total_score = 0
            
            for mark in marks:
                jury = User.query.get(mark.jury_id)
                if jury:
                    reviews.append({
                        'juror': jury.username,
                        'decision': mark.decision,
                        'points': mark.total_score,
                        'comment': mark.comments or ''
                    })
                    article_total_score += mark.total_score
            
            # Calculate average score if there are marks
            if marks:
                article.points = article_total_score // len(marks)
            else:
                articles_without_marks += 1
            
            total_points += article.points or 0
            
            # Build user statistics
            if username not in user_stats:
                user_stats[username] = {
                    'articles_count': 0,
                    'total_points': 0,
                    'articles': []
                }
            
            user_stats[username]['articles_count'] += 1
            user_stats[username]['total_points'] += article.points or 0
            
            # Map article to frontend format
            article_for_frontend = {
                'id': article.id,
                'title': article.title,
                'author': username,
                'addedOn': article.submitted_at.isoformat() if article.submitted_at else None,
                'points': article.points,
                'reviews': reviews,
                'words': 150,   # Default values (could be fetched from Wikipedia API)
                'bytes': 2500,
                'preview': f'Preview for {article.title}',
                'status': article.status
            }
            user_stats[username]['articles'].append(article_for_frontend)
            
            # Add to unreviewed if no marks
            if not marks:
                unreviewed_articles_mapped.append(article_for_frontend)
        
        # Build leaderboard
        leaderboard = [
            {
                'id': i+1,
                'username': username,
                'articlesCount': stats['articles_count'],
                'totalPoints': stats['total_points'],
                'articles': stats['articles']
            }
            for i, (username, stats) in enumerate(user_stats.items())
        ]
        leaderboard.sort(key=lambda x: x['totalPoints'], reverse=True)
        
        # Get jury members
        jury_assignments = EditathonJury.query.filter_by(editathon_id=editathon_id).all()
        juries = []
        for assignment in jury_assignments:
            user = User.query.get(assignment.user_id)
            if user:
                juries.append({
                    'id': user.id,
                    'username': user.username
                })
        
        # Fetch rules linked to this editathon
        def parse_condition(condition_text):
            if not condition_text:
                return {}
            try:
                return json.loads(condition_text)
            except Exception:
                try:
                    return ast.literal_eval(condition_text)
                except Exception:
                    return {}

        rules = []
        linked_rules = EditathonRule.query.filter_by(editathon_id=editathon_id, is_active=True).all()
        for er in linked_rules:
            rule = Rule.query.get(er.rule_id)
            if rule:
                rules.append({
                    'id': rule.id,
                    'type': rule.rule_type or rule.name,
                    'config': parse_condition(rule.condition_text),
                    'description': rule.description or '',
                    'optional': False,
                    'showInJuryTool': True
                })

        return jsonify({
            'editathon': {
                'id': editathon.id,
                'name': editathon.name,
                'status': editathon.status,
                'description': editathon.description,
                'wiki_language': editathon.language,
                'project': project_label,
                'project_domain': project_obj.name if project_obj else None,
                'rules': rules
            },
            'stats': {
                'users': len(users),
                'articles': total_articles,
                'marks': total_articles - articles_without_marks,
                'withoutMarks': articles_without_marks,
                'totalPoints': total_points
            },
            'juries': juries,
            'leaderboard': leaderboard,
            'unreviewed_articles': unreviewed_articles_mapped
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Get All Editathons for Homepage
@app.route('/api/editathons', methods=['GET'])
def get_all_editathons():
    try:
        editathons = Editathon.query.all()
        result = []
        for editathon in editathons:
            stats = EditathonStat.query.get(editathon.id)
            project_obj = Project.query.get(editathon.project_id) if editathon.project_id else None
            project_label = format_project_label(project_obj.name if project_obj else None)
            
            # Get jury members
            jury_assignments = EditathonJury.query.filter_by(editathon_id=editathon.id).all()
            juries = []
            for assignment in jury_assignments:
                user = User.query.get(assignment.user_id)
                if user:
                    juries.append({
                        'id': user.id,
                        'username': user.username,
                        'role': assignment.role
                    })
            
            result.append({
                'id': editathon.id,
                'code': editathon.code,
                'name': editathon.name,
                'description': editathon.description,
                'startDate': editathon.start_date.isoformat() if editathon.start_date else None,
                'endDate': editathon.end_date.isoformat() if editathon.end_date else None,
                'status': editathon.status,
                'language': editathon.language,
                'project': project_label,
                'project_domain': project_obj.name if project_obj else None,
                'article_count': stats.total_articles if stats else 0,
                'user_count': stats.total_participants if stats else 0,
                'juries': juries
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. Submit Article to Editathon (New Schema)
@app.route('/api/editathon/<editathon_id>/submit', methods=['POST'])
def submit_article(editathon_id):
    try:
        data = request.json
        
        # Find user
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Find editathon
        editathon = Editathon.query.get(editathon_id)
        if not editathon:
            return jsonify({"error": "Editathon not found"}), 404
        
        # Create article
        article = Article(
            editathon_id=editathon.id,
            title=data['article_title'],
            wikipedia_url=data.get('wikipedia_url'),
            submitted_by=user.id,
            status='pending'
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            "message": f"Article '{article.title}' submitted successfully",
            "article_id": article.id,
            "success": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 5. Judge Article - Add Marks (New Schema)
@app.route('/api/editathon/<editathon_id>/judge', methods=['POST'])
def judge_article(editathon_id):
    try:
        data = request.json
        
        # Find jury user
        jury_user = User.query.filter_by(username=data.get('reviewer', 'Unknown')).first()
        if not jury_user:
            return jsonify({"error": "Jury user not found"}), 404
        
        # Find article by title
        article = Article.query.filter_by(
            editathon_id=editathon_id,
            title=data['article_title']
        ).first()
        
        if not article:
            return jsonify({"error": "Article not found"}), 404
        
        # Check if jury is assigned to this editathon
        jury_assignment = EditathonJury.query.filter_by(
            editathon_id=editathon_id,
            user_id=jury_user.id
        ).first()
        
        if not jury_assignment and jury_user.role != 'admin':
            return jsonify({"error": "Jury not assigned to this editathon"}), 403
        
        # Create or update mark
        mark = Mark.query.filter_by(
            article_id=article.id,
            jury_id=jury_user.id
        ).first()
        
        points = data.get('points', 0)
        decision = data.get('decision', 'accepted')
        comment = data.get('comment', '')
        
        if mark:
            mark.criteria_scores = {"total": points}
            mark.total_score = points
            mark.comments = comment
            mark.decision = 'accept' if decision == 'accepted' else 'reject'
        else:
            mark = Mark(
                article_id=article.id,
                jury_id=jury_user.id,
                criteria_scores={"total": points},
                total_score=points,
                comments=comment,
                decision='accept' if decision == 'accepted' else 'reject'
            )
            db.session.add(mark)
        
        # Update article points and status
        article.points = points
        article.status = 'accepted' if decision == 'accepted' else 'rejected'
        
        db.session.commit()
        
        return jsonify({
            "message": f"Article '{article.title}' judged with {points} points",
            "success": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 6. Create New Editathon (New Schema)
@app.route('/api/editathons/create', methods=['POST'])
def create_new_editathon():
    try:
        data = request.json
        print(f"Received data keys: {list(data.keys())}")  # Debug print
        
        # Validate required fields
        required_fields = ['title', 'startDate', 'endDate', 'createdBy']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Find creator user
        creator = User.query.filter_by(username=data.get('createdBy')).first()
        if not creator:
            return jsonify({"error": "Creator user not found"}), 404
        
        # Parse dates
        try:
            from datetime import datetime
            start_date = datetime.strptime(data.get('startDate'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('endDate'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Find or create project
        project = None
        if data.get('project'):
            project = Project.query.filter_by(name=data.get('project')).first()
            if not project:
                project = Project(
                    name=data.get('project'),
                    description=f"Project for {data.get('project')}",
                    created_by=creator.id
                )
                db.session.add(project)
                db.session.flush()  # Get project ID
        
        # Process marks configuration (convert to JSON-safe format)
        marks_data = data.get('marks', [])
        if marks_data:
            # Convert marks to simple dict for storage
            marks_config = {
                'marks': marks_data,
                'hidden_marks': data.get('hiddenMarks', False),
                'consensual_vote': data.get('consensualVote', False)
            }
        else:
            marks_config = None
        
        # Generate code if not provided
        code = data.get('code')
        if not code:
            code = f"editathon-{int(datetime.now().timestamp())}"
        
        # Create editathon with all frontend data
        editathon = Editathon(
            code=code,
            name=data.get('title'),
            description=data.get('description', ''),
            project_id=project.id if project else None,
            language=data.get('wiki_language', 'en'),
            start_date=start_date,
            end_date=end_date,
            wiki_domain=f"{data.get('wiki_language', 'en')}.wikipedia.org",
            status='draft',  # Always start as draft
            min_marks_needed=data.get('minSize', 1),
            marks_config=marks_config,
            is_published=False,
            created_by=creator.id
        )
        
        db.session.add(editathon)
        db.session.flush()  # Get editathon ID
        
        # Add jury members if provided
        jury_data = data.get('jury', [])
        print(f"Processing jury data: {jury_data}")  # Debug print
        if jury_data and isinstance(jury_data, list):
            for jury_member in jury_data:
                if isinstance(jury_member, dict) and jury_member.get('username'):
                    username = jury_member['username']
                    jury_user = User.query.filter_by(username=username).first()
                    
                    # Create user if they don't exist
                    if not jury_user:
                        print(f"Creating new jury user: {username}")  # Debug print
                        jury_user = User(
                            username=username,
                            email=f"{username}@wikipedia.org",  # Default email
                            password_hash='oauth_user',  # Placeholder for OAuth users
                            role='jury'
                        )
                        db.session.add(jury_user)
                        db.session.flush()  # Get user ID
                    
                    print(f"Adding jury assignment for user {username} (ID: {jury_user.id})")  # Debug print
                    jury_assignment = EditathonJury(
                        editathon_id=editathon.id,
                        user_id=jury_user.id,
                        role='main'
                    )
                    db.session.add(jury_assignment)
        
        # Store rules in a separate table (create simple rules storage)
        rules_data = data.get('rules', [])
        if rules_data and isinstance(rules_data, list):
            for rule_data in rules_data:
                if isinstance(rule_data, dict) and rule_data.get('type'):
                    rule = Rule(
                        name=rule_data.get('type', 'Rule'),
                        rule_type=rule_data.get('type', 'custom'),
                        condition_text=str(rule_data.get('config', {})),
                        description=rule_data.get('description', ''),
                        created_by=creator.id
                    )
                    db.session.add(rule)
                    db.session.flush()
                    
                    # Link rule to editathon
                    editathon_rule = EditathonRule(
                        editathon_id=editathon.id,
                        rule_id=rule.id,
                        is_active=True
                    )
                    db.session.add(editathon_rule)
        
        # Initialize statistics
        stats = EditathonStat(
            editathon_id=editathon.id,
            total_articles=0,
            total_participants=0,
            total_points=0,
            avg_score=0
        )
        db.session.add(stats)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Editathon created successfully",
            "id": editathon.id,
            "code": editathon.code,
            "name": editathon.name,
            "status": editathon.status
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating editathon: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get Draft Editathons for Approval (Admin only)
@app.route('/api/editathons/pending', methods=['GET'])
def get_pending_editathons():
    try:
        # Get draft editathons (waiting for approval)
        pending_editathons = Editathon.query.filter_by(status='draft').all()
        result = []
        for editathon in pending_editathons:
            creator = User.query.get(editathon.created_by)
            result.append({
                'id': editathon.id,
                'code': editathon.code,
                'name': editathon.name,
                'description': editathon.description,
                'language': editathon.language,
                'start_date': editathon.start_date.isoformat() if editathon.start_date else None,
                'end_date': editathon.end_date.isoformat() if editathon.end_date else None,
                'created_by': creator.username if creator else 'Unknown',
                'status': editathon.status
            })
        
        return jsonify({
            "success": True,
            "editathons": result,
            "count": len(result)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Approve Editathon (Admin only)
@app.route('/api/editathon/<editathon_id>/approve', methods=['POST'])
def approve_editathon(editathon_id):
    try:
        editathon = Editathon.query.get(editathon_id)
        if not editathon:
            return jsonify({"error": "Editathon not found"}), 404
        
        editathon.status = 'active'
        editathon.is_published = True
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Editathon '{editathon.name}' approved successfully",
            "status": "active"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Reject Editathon (Admin only)
@app.route('/api/editathon/<editathon_id>/reject', methods=['POST'])
def reject_editathon(editathon_id):
    try:
        data = request.json
        reason = data.get('reason', 'No reason provided') if data else 'No reason provided'
        
        editathon = Editathon.query.get(editathon_id)
        if not editathon:
            return jsonify({"error": "Editathon not found"}), 404
        
        editathon.status = 'rejected'
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Editathon '{editathon.name}' rejected. Reason: {reason}",
            "status": "rejected"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Get User's Pending Editathons
@app.route('/api/user/<username>/pending-editathons', methods=['GET'])
def get_user_pending_editathons(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get draft editathons created by this user (waiting for approval)
        pending_editathons = Editathon.query.filter_by(
            created_by=user.id, 
            status='draft'
        ).all()
        
        result = []
        for editathon in pending_editathons:
            result.append({
                'id': editathon.id,
                'code': editathon.code,
                'name': editathon.name,
                'description': editathon.description,
                'language': editathon.language,
                'start_date': editathon.start_date.isoformat() if editathon.start_date else None,
                'end_date': editathon.end_date.isoformat() if editathon.end_date else None,
                'status': editathon.status
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Submit article (new schema)
@app.route('/api/articles', methods=['POST'])
def submit_article_to_editathon():
    try:
        data = request.json
        
        # Find user
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Find editathon
        editathon = Editathon.query.filter_by(code=data['editathon_code']).first()
        if not editathon:
            return jsonify({"error": "Editathon not found"}), 404
        
        # Create article
        article = Article(
            editathon_id=editathon.id,
            title=data['title'],
            wikipedia_url=data.get('wikipedia_url'),
            submitted_by=user.id,
            status='pending'
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            "message": f"Article '{article.title}' submitted successfully",
            "article_id": article.id,
            "success": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Add marks (new schema)
@app.route('/api/marks', methods=['POST'])
def add_marks():
    try:
        data = request.json
        
        # Find jury user
        jury_user = User.query.filter_by(username=data['jury_username']).first()
        if not jury_user or jury_user.role != 'jury':
            return jsonify({"error": "Jury user not found or not authorized"}), 403
        
        # Find article
        article = Article.query.get(data['article_id'])
        if not article:
            return jsonify({"error": "Article not found"}), 404
        
        # Check if jury is assigned to this editathon
        jury_assignment = EditathonJury.query.filter_by(
            editathon_id=article.editathon_id,
            user_id=jury_user.id
        ).first()
        if not jury_assignment:
            return jsonify({"error": "Jury not assigned to this editathon"}), 403
        
        # Create or update mark
        mark = Mark.query.filter_by(
            article_id=article.id,
            jury_id=jury_user.id
        ).first()
        
        if mark:
            mark.criteria_scores = data['criteria_scores']
            mark.total_score = data['total_score']
            mark.comments = data.get('comments')
            mark.decision = data['decision']
        else:
            mark = Mark(
                article_id=article.id,
                jury_id=jury_user.id,
                criteria_scores=data['criteria_scores'],
                total_score=data['total_score'],
                comments=data.get('comments'),
                decision=data['decision']
            )
            db.session.add(mark)
        
        db.session.commit()
        
        return jsonify({
            "message": "Marks added successfully",
            "mark_id": mark.id,
            "success": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Create tables function
def create_tables():
    try:
        with app.app_context():
            db.create_all()
            print("✅ Tables created/verified successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

# Auto-import finished editathons on startup
def auto_import_data():
    """Auto-import all finished editathons from sample data on startup"""
    from datetime import datetime, timedelta
    
    with app.app_context():
        print("\n🔄 Auto-importing finished editathons...")
        
        # Check if data already exists - skip only if WAM2025 already exists
        if Editathon.query.filter_by(code='WAM2025').first():
            print("⚠️ Data already exists. Skipping import.")
            return
        
        try:
            # ========== 1. CREATE ALL USERS ==========
            users_to_create = [
                # Admin & Organizers
                {"username": "WikiFountainAdmin", "role": "admin", "email": "admin@wikifountain.org"},
                
                # Jury
                {"username": "Haoreima", "role": "jury", "email": "haoreima@wikifountain.org"},
                {"username": "MSG17", "role": "jury", "email": "msg17@wikifountain.org"},
                {"username": "Narutolovehinata5", "role": "jury", "email": "narutolovehinata5@wikifountain.org"},
                {"username": "SuperHamster", "role": "jury", "email": "superhamster@wikifountain.org"},
                {"username": "ZI Jony", "role": "jury", "email": "zijony@wikifountain.org"},
                
                # Participants
                {"username": "Min968", "role": "participant", "email": "min968@wikifountain.org"},
                {"username": "MisawaSakura", "role": "participant", "email": "misawasakura@wikifountain.org"},
                {"username": "Nicholas0", "role": "participant", "email": "nicholas0@wikifountain.org"},
                {"username": "SDGB1217", "role": "participant", "email": "sdgb1217@wikifountain.org"},
                {"username": "Ainty Painty", "role": "participant", "email": "ainty@wikifountain.org"},
                {"username": "Spiderpig662", "role": "participant", "email": "spiderpig@wikifountain.org"},
                {"username": "MumphingSquirrel", "role": "participant", "email": "mumph@wikifountain.org"},
                {"username": "Alperen", "role": "participant", "email": "alperen@wikifountain.org"},
                {"username": "Abishe", "role": "participant", "email": "abishe@wikifountain.org"},
                {"username": "Penny Richards", "role": "participant", "email": "penny@wikifountain.org"},
            ]
            
            users_dict = {}
            for user_data in users_to_create:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=f"imported_{user_data['username'].lower()}",
                    role=user_data["role"],
                    is_active=True
                )
                db.session.add(user)
                users_dict[user_data["username"]] = user
            
            db.session.flush()
            print(f"  ✅ Created {len(users_dict)} users")
            
            # ========== 2. CREATE PROJECT ==========
            project = Project(
                name="Wikipedia Editathons",
                description="Collection of finished Wikipedia editathons",
                created_by=users_dict["WikiFountainAdmin"].id
            )
            db.session.add(project)
            db.session.flush()
            print("  ✅ Created project")
            
            # ========== 3. IMPORT EDITATHON 1: WIKIPEDIA ASIAN MONTH 2025 ==========
            wam2025 = Editathon(
                code="WAM2025",
                name="Wikipedia Asian Month 2025",
                description="Wikipedia Asian Month 2025 - Completed editathon",
                project_id=project.id,
                language="en",
                start_date=datetime(2025, 11, 1),
                end_date=datetime(2025, 11, 30),
                wiki_domain="en.wikipedia.org",
                status="completed",
                is_published=True,
                created_by=users_dict["WikiFountainAdmin"].id
            )
            db.session.add(wam2025)
            db.session.flush()
            
            # Jury for WAM2025
            for jury_name in ["Narutolovehinata5", "ZI Jony", "MSG17"]:
                db.session.add(EditathonJury(
                    editathon_id=wam2025.id,
                    user_id=users_dict[jury_name].id,
                    role="main"
                ))
            
            # Articles for WAM2025 (from setup_mariadb.py)
            wam2025_articles = [
                ('Min968', 'History of Korean cuisine', datetime(2025, 11, 1, 10, 0), 85, 'Excellent coverage'),
                ('MisawaSakura', 'Japanese tea ceremony', datetime(2025, 11, 2, 14, 30), 92, 'Comprehensive article'),
                ('Nicholas0', 'Traditional Mongolian clothing', datetime(2025, 11, 3, 9, 15), 78, 'Good research'),
                ('SDGB1217', 'Filipino martial arts', datetime(2025, 11, 4, 16, 45), 88, 'Well-structured'),
                ('Min968', 'Chinese calligraphy techniques', datetime(2025, 11, 5, 11, 20), 90, 'Outstanding'),
                ('MisawaSakura', 'Vietnamese traditional music', datetime(2025, 11, 6, 13, 10), 85, 'Good coverage'),
                ('Nicholas0', 'Thai Buddhist temples', datetime(2025, 11, 7, 15, 30), 82, 'Solid research'),
                ('SDGB1217', 'Indonesian batik patterns', datetime(2025, 11, 8, 10, 45), 87, 'Beautiful article'),
                ('Min968', 'Singaporean street food', datetime(2025, 11, 9, 12, 15), 89, 'Excellent documentation'),
                ('MisawaSakura', 'Cambodian Angkor Wat history', datetime(2025, 11, 10, 14, 20), 91, 'Comprehensive'),
                ('Nicholas0', 'Malaysian traditional games', datetime(2025, 11, 11, 16, 30), 80, 'Good introduction'),
                ('SDGB1217', 'Burmese pagoda festivals', datetime(2025, 11, 12, 11, 45), 86, 'Well-researched'),
            ]
            
            wam2025_points = 0
            wam2025_participants = set()
            for author_name, title, submitted_at, points, notes in wam2025_articles:
                author = users_dict[author_name]
                article = Article(
                    editathon_id=wam2025.id,
                    title=title,
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    submitted_by=author.id,
                    status='accepted' if points > 0 else 'rejected',
                    points=points,
                    notes=notes,
                    submitted_at=submitted_at
                )
                db.session.add(article)
                db.session.flush()
                
                wam2025_points += points
                wam2025_participants.add(author_name)
                
                # Add mark from jury
                jury_name = "Narutolovehinata5" if points > 0 else "ZI Jony"
                mark = Mark(
                    article_id=article.id,
                    jury_id=users_dict[jury_name].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8},
                    total_score=points,
                    comments=notes,
                    decision="accept" if points > 0 else "reject",
                    marked_at=submitted_at + timedelta(hours=1)
                )
                db.session.add(mark)
            
            stats = EditathonStat(
                editathon_id=wam2025.id,
                total_articles=len(wam2025_articles),
                total_participants=len(wam2025_participants),
                total_points=wam2025_points,
                avg_score=wam2025_points / len(wam2025_articles) if wam2025_articles else 0
            )
            db.session.add(stats)
            print(f"  ✅ Imported {len(wam2025_articles)} articles for WAM2025")
            
            # ========== 4. IMPORT EDITATHON 2: WIKI LOVES RAMADAN 2025 ==========
            wlr2025 = Editathon(
                code="WLR2025",
                name="Wiki Loves Ramadan 2025",
                description="Wiki Loves Ramadan 2025 - Completed editathon",
                project_id=project.id,
                language="en",
                start_date=datetime(2025, 2, 25),
                end_date=datetime(2025, 4, 15),
                wiki_domain="en.wikipedia.org",
                status="completed",
                is_published=True,
                created_by=users_dict["WikiFountainAdmin"].id
            )
            db.session.add(wlr2025)
            db.session.flush()
            
            # Jury for WLR2025
            for jury_name in ["ZI Jony"]:
                db.session.add(EditathonJury(
                    editathon_id=wlr2025.id,
                    user_id=users_dict[jury_name].id,
                    role="main"
                ))
            
            # Articles for WLR2025
            wlr2025_articles = [
                ('Min968', 'Ramadan traditions in Muslim countries', datetime(2025, 2, 25, 10, 0), 88, 'Comprehensive overview'),
                ('ZI Jony', 'Islamic calligraphy during Ramadan', datetime(2025, 2, 26, 14, 30), 92, 'Beautiful examples'),
                ('MisawaSakura', 'Ramadan food traditions', datetime(2025, 2, 27, 9, 15), 85, 'Excellent coverage'),
                ('Nicholas0', 'Mosque architecture and Ramadan', datetime(2025, 2, 28, 16, 45), 87, 'Good analysis'),
                ('SDGB1217', 'Ramadan charity and community service', datetime(2025, 3, 1, 11, 20), 90, 'Outstanding'),
                ('Min968', 'Ramadan in modern times', datetime(2025, 3, 2, 13, 10), 86, 'Contemporary'),
                ('ZI Jony', 'Ramadan moon sighting traditions', datetime(2025, 3, 3, 15, 30), 89, 'Detailed'),
                ('MisawaSakura', 'Family gatherings during Ramadan', datetime(2025, 3, 4, 10, 45), 84, 'Heartwarming'),
                ('Nicholas0', 'Ramadan shopping and markets', datetime(2025, 3, 5, 12, 15), 82, 'Economic aspects'),
                ('SDGB1217', 'Ramadan literature and poetry', datetime(2025, 3, 6, 14, 20), 91, 'Literary analysis'),
            ]
            
            wlr2025_points = 0
            wlr2025_participants = set()
            for author_name, title, submitted_at, points, notes in wlr2025_articles:
                author = users_dict[author_name]
                article = Article(
                    editathon_id=wlr2025.id,
                    title=title,
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    submitted_by=author.id,
                    status='accepted',
                    points=points,
                    notes=notes,
                    submitted_at=submitted_at
                )
                db.session.add(article)
                db.session.flush()
                
                wlr2025_points += points
                wlr2025_participants.add(author_name)
                
                mark = Mark(
                    article_id=article.id,
                    jury_id=users_dict["ZI Jony"].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8},
                    total_score=points,
                    comments=notes,
                    decision="accept",
                    marked_at=submitted_at + timedelta(hours=1)
                )
                db.session.add(mark)
            
            stats = EditathonStat(
                editathon_id=wlr2025.id,
                total_articles=len(wlr2025_articles),
                total_participants=len(wlr2025_participants),
                total_points=wlr2025_points,
                avg_score=wlr2025_points / len(wlr2025_articles)
            )
            db.session.add(stats)
            print(f"  ✅ Imported {len(wlr2025_articles)} articles for WLR2025")
            
            # ========== 5. IMPORT EDITATHON 3: WOMEN IN RED 2024 ==========
            wir2024 = Editathon(
                code="WIR2024",
                name="Women in Red Translation Contest 2024",
                description="Women in Red 2024 - Completed editathon",
                project_id=project.id,
                language="en",
                start_date=datetime(2024, 7, 1),
                end_date=datetime(2024, 10, 1),
                wiki_domain="en.wikipedia.org",
                status="completed",
                is_published=True,
                created_by=users_dict["Spiderpig662"].id
            )
            db.session.add(wir2024)
            db.session.flush()
            
            wir2024_articles = [
                ('Min968', 'Marie Curie biography (translated)', datetime(2024, 7, 1, 10, 0), 90, 'Excellent translation'),
                ('MisawaSakura', 'Malala Yousafzai story (translated)', datetime(2024, 7, 15, 14, 30), 88, 'Well-translated'),
            ]
            
            wir2024_points = 0
            for author_name, title, submitted_at, points, notes in wir2024_articles:
                author = users_dict[author_name]
                article = Article(
                    editathon_id=wir2024.id,
                    title=title,
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    submitted_by=author.id,
                    status='accepted',
                    points=points,
                    notes=notes,
                    submitted_at=submitted_at
                )
                db.session.add(article)
                db.session.flush()
                
                wir2024_points += points
            
            stats = EditathonStat(
                editathon_id=wir2024.id,
                total_articles=len(wir2024_articles),
                total_participants=len(set([a[0] for a in wir2024_articles])),
                total_points=wir2024_points,
                avg_score=wir2024_points / len(wir2024_articles)
            )
            db.session.add(stats)
            print(f"  ✅ Imported {len(wir2024_articles)} articles for WIR2024")
            
            # ========== 6. IMPORT EDITATHON 4: FEMINISM AND FOLKLORE 2024 ==========
            faf2024 = Editathon(
                code="FAF2024",
                name="Feminism and Folklore 2024",
                description="Feminism and Folklore 2024 - Completed editathon",
                project_id=project.id,
                language="en",
                start_date=datetime(2024, 2, 1),
                end_date=datetime(2024, 3, 31),
                wiki_domain="en.wikipedia.org",
                status="completed",
                is_published=True,
                created_by=users_dict["Alperen"].id
            )
            db.session.add(faf2024)
            db.session.flush()
            
            # Jury for FAF2024
            db.session.add(EditathonJury(
                editathon_id=faf2024.id,
                user_id=users_dict["Haoreima"].id,
                role="main"
            ))
            
            faf2024_articles = [
                ('Alperen', 'Feminist themes in Japanese folklore', datetime(2024, 3, 29, 17, 22), 92, 'Outstanding analysis'),
            ]
            
            for author_name, title, submitted_at, points, notes in faf2024_articles:
                author = users_dict[author_name]
                article = Article(
                    editathon_id=faf2024.id,
                    title=title,
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    submitted_by=author.id,
                    status='accepted',
                    points=points,
                    notes=notes,
                    submitted_at=submitted_at
                )
                db.session.add(article)
                db.session.flush()
                
                mark = Mark(
                    article_id=article.id,
                    jury_id=users_dict["Haoreima"].id,
                    criteria_scores={"quality": 9, "sources": 8, "coverage": 9},
                    total_score=points,
                    comments=notes,
                    decision="accept",
                    marked_at=submitted_at + timedelta(hours=1)
                )
                db.session.add(mark)
            
            stats = EditathonStat(
                editathon_id=faf2024.id,
                total_articles=len(faf2024_articles),
                total_participants=1,
                total_points=92,
                avg_score=92
            )
            db.session.add(stats)
            print(f"  ✅ Imported {len(faf2024_articles)} articles for FAF2024")
            
            db.session.commit()
            print("\n✅ All finished editathons imported automatically!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during auto-import: {e}")
            raise

# Auto-import finished editathons on startup
def auto_import_finished_editathons():
    """Automatically import finished editathons if database is empty"""
    from datetime import timedelta
    
    try:
        with app.app_context():
            # Check if data already exists
            existing_editathons = Editathon.query.count()
            if existing_editathons > 0:
                print("ℹ️  Database already has editathons, skipping auto-import")
                return
            
            print("📥 Auto-importing finished editathons...")
            
            # ========== 1. CREATE ALL USERS ==========
            users_to_create = [
                {"username": "WikiFountainAdmin", "role": "admin", "email": "admin@wikifountain.org"},
                {"username": "Haoreima", "role": "jury", "email": "haoreima@wikifountain.org"},
                {"username": "MSG17", "role": "jury", "email": "msg17@wikifountain.org"},
                {"username": "Narutolovehinata5", "role": "jury", "email": "narutolovehinata5@wikifountain.org"},
                {"username": "SuperHamster", "role": "jury", "email": "superhamster@wikifountain.org"},
                {"username": "ZI Jony", "role": "jury", "email": "zijony@wikifountain.org"},
                {"username": "Abishe", "role": "participant", "email": "abishe@wikifountain.org"},
                {"username": "Penny Richards", "role": "participant", "email": "penny@wikifountain.org"},
                {"username": "Min968", "role": "participant", "email": "min968@wikifountain.org"},
                {"username": "MisawaSakura", "role": "participant", "email": "misawasakura@wikifountain.org"},
            ]
            
            users_dict = {}
            for user_data in users_to_create:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=f"imported_{user_data['username'].lower()}",
                    role=user_data["role"],
                    is_active=True
                )
                db.session.add(user)
                users_dict[user_data["username"]] = user
            
            db.session.flush()
            
            # ========== 2. CREATE PROJECT ==========
            organizer = users_dict["WikiFountainAdmin"]
            project = Project(
                name="Wikipedia Asian Month",
                description="Annual Wikipedia Asian Month editathon focusing on Asian content",
                created_by=organizer.id
            )
            db.session.add(project)
            db.session.flush()
            
            # ========== 3. IMPORT WAM 2024 ==========
            wam2024 = Editathon(
                code="WAM2024",
                name="Wikipedia Asian Month 2024",
                description="Wikipedia Asian Month 2024 - Completed editathon",
                project_id=project.id,
                language="en",
                start_date=datetime(2024, 11, 1),
                end_date=datetime(2024, 11, 30),
                wiki_domain="en.wikipedia.org",
                status="completed",
                min_marks_needed=1,
                is_published=True,
                created_by=organizer.id
            )
            db.session.add(wam2024)
            db.session.flush()
            
            # Assign jury for WAM2024
            for jury_name in ["Haoreima", "MSG17", "Narutolovehinata5", "SuperHamster", "ZI Jony"]:
                db.session.add(EditathonJury(
                    editathon_id=wam2024.id,
                    user_id=users_dict[jury_name].id,
                    role="main"
                ))
            
            # Add articles for WAM2024
            wam2024_articles = [
                {"title": "Mala Honnatti", "author": "Abishe", "points": 1, "jury": "ZI Jony"},
                {"title": "Geetha Kailasam", "author": "Abishe", "points": 1, "jury": "MSG17"},
                {"title": "Sean Wijesinghe", "author": "Abishe", "points": 1, "jury": "MSG17"},
                {"title": "Emma Sarepta Yule", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
                {"title": "Mary Sallom", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
                {"title": "Elise Grilli", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
            ]
            
            for art_data in wam2024_articles:
                article = Article(
                    editathon_id=wam2024.id,
                    title=art_data["title"],
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{art_data['title'].replace(' ', '_')}",
                    submitted_by=users_dict[art_data["author"]].id,
                    status="accepted",
                    points=art_data["points"],
                    submitted_at=datetime(2024, 11, 30, 12, 0)
                )
                db.session.add(article)
                db.session.flush()
                
                mark = Mark(
                    article_id=article.id,
                    jury_id=users_dict[art_data["jury"]].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8},
                    total_score=art_data["points"],
                    comments="Accepted",
                    decision="accept",
                    marked_at=datetime(2024, 11, 30, 13, 0)
                )
                db.session.add(mark)
            
            stats_2024 = EditathonStat(
                editathon_id=wam2024.id,
                total_articles=len(wam2024_articles),
                total_participants=2,
                total_points=sum(a["points"] for a in wam2024_articles),
                avg_score=sum(a["points"] for a in wam2024_articles) / len(wam2024_articles)
            )
            db.session.add(stats_2024)
            
            # ========== 4. IMPORT WAM 2025 ==========
            wam2025 = Editathon(
                code="WAM2025",
                name="Wikipedia Asian Month 2025",
                description="Wikipedia Asian Month 2025 - Completed editathon",
                project_id=project.id,
                language="en",
                start_date=datetime(2025, 11, 1),
                end_date=datetime(2025, 11, 30),
                wiki_domain="en.wikipedia.org",
                status="completed",
                min_marks_needed=1,
                is_published=True,
                created_by=organizer.id
            )
            db.session.add(wam2025)
            db.session.flush()
            
            # Assign jury for WAM2025
            for jury_name in ["MSG17", "Narutolovehinata5", "ZI Jony"]:
                db.session.add(EditathonJury(
                    editathon_id=wam2025.id,
                    user_id=users_dict[jury_name].id,
                    role="main"
                ))
            
            # Add articles for WAM2025
            wam2025_articles = [
                {"title": "Mao Kun", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Zhang Bi (calligrapher)", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Wang Shenzhong", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Hou (title 侯)", "author": "Min968", "points": 0, "jury": "ZI Jony"},
                {"title": "Minggadari", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Fish-Scale Registers", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Three-pillar accounting system", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Ira Sukrungruang", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Frances Cha", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
                {"title": "Farida Sulaiman", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
            ]
            
            for art_data in wam2025_articles:
                article = Article(
                    editathon_id=wam2025.id,
                    title=art_data["title"],
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{art_data['title'].replace(' ', '_')}",
                    submitted_by=users_dict[art_data["author"]].id,
                    status="accepted" if art_data["points"] > 0 else "rejected",
                    points=art_data["points"],
                    submitted_at=datetime(2025, 11, 30, 12, 0)
                )
                db.session.add(article)
                db.session.flush()
                
                mark = Mark(
                    article_id=article.id,
                    jury_id=users_dict[art_data["jury"]].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8},
                    total_score=art_data["points"],
                    comments="Accepted" if art_data["points"] > 0 else "Rejected",
                    decision="accept" if art_data["points"] > 0 else "reject",
                    marked_at=datetime(2025, 11, 30, 13, 0)
                )
                db.session.add(mark)
            
            stats_2025 = EditathonStat(
                editathon_id=wam2025.id,
                total_articles=len(wam2025_articles),
                total_participants=2,
                total_points=sum(a["points"] for a in wam2025_articles),
                avg_score=sum(a["points"] for a in wam2025_articles) / len(wam2025_articles)
            )
            db.session.add(stats_2025)
            
            db.session.commit()
            
            print("✅ Auto-import completed successfully!")
            print(f"   • WAM 2024: {len(wam2024_articles)} articles")
            print(f"   • WAM 2025: {len(wam2025_articles)} articles")
            
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Auto-import skipped or failed: {e}")

# Test database connection
def test_connection():
    try:
        with app.app_context():
            # Test connection by fetching user count
            user_count = User.query.count()
            print("✅ Connected to Database successfully!")
            print(f"   📊 Users in database: {user_count}")
            
            # Show all tables
            # result = db.session.execute(db.text("SHOW TABLES"))
            # tables = [row[0] for row in result]
            # print(f"   📋 Available tables: {', '.join(tables)}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

test_connection()

# Initialize tables
create_tables()

# Auto-import finished editathons
auto_import_data()

if __name__ == '__main__':
    print("🚀 Backend running with WikiFountain Schema!")
    print("📊 Home: http://localhost:5000")
    print("👤 Personal Cabinet: http://localhost:5000/api/personal-cabinet/Min968") 
    print("📈 Editathon Dashboard: http://localhost:5000/api/editathon/1")
    print("🏠 All Editathons: http://localhost:5000/api/editathons")
    print("\n📋 Available endpoints:")
    print("   GET  /api/personal-cabinet/<username> - Get user statistics")
    print("   GET  /api/editathons - List all editathons")
    print("   GET  /api/editathon/<id> - Get editathon dashboard")
    print("   POST /api/editathons/create - Create new editathon")
    print("   POST /api/editathon/<id>/submit - Submit article to editathon")
    print("   POST /api/editathon/<id>/judge - Judge article")
    print("   POST /api/articles - Submit article (alternative)")
    print("   POST /api/marks - Add jury marks")
    
    app.run(debug=True, port=5000)