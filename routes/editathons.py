from flask import Blueprint, jsonify, request
from extensions import db
from models import User, Project, Editathon, EditathonJury, EditathonStat, Mark, Article, EditathonRule, Rule
from utils import format_project_label
from datetime import datetime
import json
import ast

editathons_bp = Blueprint('editathons', __name__)

@editathons_bp.route('/api/editathons', methods=['GET'])
def get_all_editathons():
    try:
        editathons = Editathon.query.all()
        result = []
        for editathon in editathons:
            stats = EditathonStat.query.get(editathon.id)
            project_obj = Project.query.get(editathon.project_id) if editathon.project_id else None
            project_label = format_project_label(project_obj.name if project_obj else None)
            
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

@editathons_bp.route('/api/editathons/create', methods=['POST'])
def create_new_editathon():
    try:
        data = request.json
        required_fields = ['title', 'startDate', 'endDate', 'createdBy']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        username = data.get('createdBy')
        creator = User.query.filter_by(username=username).first()
        if not creator:
            # Auto-create user if they don't exist (happens in dev mode or desync)
            creator = User(
                username=username,
                email=f"{username}@local.dev",
                password_hash="auto_created",
                role='admin' # Default to admin if they are creating editathons
            )
            db.session.add(creator)
            db.session.flush()
        
        try:
            start_date = datetime.strptime(data.get('startDate'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('endDate'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
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
                db.session.flush()
        
        marks_data = data.get('marks', [])
        marks_config = {
            'marks': marks_data,
            'hidden_marks': data.get('hiddenMarks', False),
            'consensual_vote': data.get('consensualVote', False)
        } if marks_data else None
        
        code = data.get('code') or f"editathon-{int(datetime.now().timestamp())}"
        
        editathon = Editathon(
            code=code,
            name=data.get('title'),
            description=data.get('description', ''),
            project_id=project.id if project else None,
            language=data.get('wiki_language', 'en'),
            start_date=start_date,
            end_date=end_date,
            wiki_domain=f"{data.get('wiki_language', 'en')}.wikipedia.org",
            status='draft',
            min_marks_needed=data.get('minSize', 1),
            marks_config=marks_config,
            is_published=False,
            created_by=creator.id
        )
        
        db.session.add(editathon)
        db.session.flush()
        
        jury_data = data.get('jury', [])
        if jury_data and isinstance(jury_data, list):
            for jury_member in jury_data:
                if isinstance(jury_member, dict) and jury_member.get('username'):
                    username = jury_member['username']
                    jury_user = User.query.filter_by(username=username).first()
                    if not jury_user:
                        jury_user = User(
                            username=username,
                            email=f"{username}@wikipedia.org",
                            password_hash='oauth_user',
                            role='jury'
                        )
                        db.session.add(jury_user)
                        db.session.flush()
                    
                    db.session.add(EditathonJury(
                        editathon_id=editathon.id,
                        user_id=jury_user.id,
                        role='main'
                    ))
        
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
                    db.session.add(EditathonRule(
                        editathon_id=editathon.id,
                        rule_id=rule.id,
                        is_active=True
                    ))
        
        db.session.add(EditathonStat(
            editathon_id=editathon.id,
            total_articles=0,
            total_participants=0,
            total_points=0,
            avg_score=0
        ))
        
        db.session.commit()
        from logger import log_activity
        log_activity(creator.id, 'create', 'editathon', editathon.id, {'name': editathon.name, 'code': editathon.code})
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
        return jsonify({"error": str(e)}), 500

@editathons_bp.route('/api/editathon/<int:editathon_id>', methods=['GET'])
def get_editathon_dashboard(editathon_id):
    try:
        editathon = Editathon.query.get(editathon_id)
        if not editathon:
            return jsonify({"error": "Editathon not found"}), 404

        project_obj = Project.query.get(editathon.project_id) if editathon.project_id else None
        project_label = format_project_label(project_obj.name if project_obj else None)
        
        articles = Article.query.filter_by(editathon_id=editathon_id).all()
        users = set()
        total_articles = len(articles)
        total_points = 0
        articles_without_marks = 0
        user_stats = {}
        unreviewed_articles_mapped = []
        
        for article in articles:
            author = User.query.get(article.submitted_by)
            if not author: continue
            
            username = author.username
            users.add(username)
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
            
            if marks:
                article.points = article_total_score // len(marks)
            else:
                articles_without_marks += 1
            
            total_points += article.points or 0
            if username not in user_stats:
                user_stats[username] = {'articles_count': 0, 'total_points': 0, 'articles': []}
            
            user_stats[username]['articles_count'] += 1
            user_stats[username]['total_points'] += article.points or 0
            
            article_for_frontend = {
                'id': article.id, 'title': article.title, 'author': username,
                'addedOn': article.submitted_at.isoformat() if article.submitted_at else None,
                'points': article.points, 'reviews': reviews,
                'words': 150, 'bytes': 2500, 'preview': f'Preview for {article.title}',
                'status': article.status
            }
            user_stats[username]['articles'].append(article_for_frontend)
            if not marks:
                unreviewed_articles_mapped.append(article_for_frontend)
        
        leaderboard = [
            {
                'id': i+1, 'username': username,
                'articlesCount': stats['articles_count'],
                'totalPoints': stats['total_points'],
                'articles': stats['articles']
            }
            for i, (username, stats) in enumerate(user_stats.items())
        ]
        leaderboard.sort(key=lambda x: x['totalPoints'], reverse=True)
        
        jury_assignments = EditathonJury.query.filter_by(editathon_id=editathon_id).all()
        juries = []
        for assignment in jury_assignments:
            user = User.query.get(assignment.user_id)
            if user:
                juries.append({'id': user.id, 'username': user.username})
        
        def parse_condition(condition_text):
            if not condition_text: return {}
            try: return json.loads(condition_text)
            except:
                try: return ast.literal_eval(condition_text)
                except: return {}

        rules = []
        linked_rules = EditathonRule.query.filter_by(editathon_id=editathon_id, is_active=True).all()
        for er in linked_rules:
            rule = Rule.query.get(er.rule_id)
            if rule:
                rules.append({
                    'id': rule.id, 'type': rule.rule_type or rule.name,
                    'config': parse_condition(rule.condition_text),
                    'description': rule.description or '', 'optional': False,
                    'showInJuryTool': True
                })

        return jsonify({
            'editathon': {
                'id': editathon.id, 'name': editathon.name, 'code': editathon.code,
                'status': editathon.status, 'description': editathon.description,
                'wiki_language': editathon.language, 'wiki_domain': editathon.wiki_domain,
                'project': project_label, 'project_domain': project_obj.name if project_obj else None,
                'start_date': editathon.start_date.isoformat() if editathon.start_date else None,
                'end_date': editathon.end_date.isoformat() if editathon.end_date else None,
                'marks_config': editathon.marks_config, 'rules': rules,
                'created_by': User.query.get(editathon.created_by).username if User.query.get(editathon.created_by) else 'Unknown'
            },
            'stats': {
                'users': len(users), 'articles': total_articles,
                'marks': total_articles - articles_without_marks,
                'withoutMarks': articles_without_marks, 'totalPoints': total_points
            },
            'juries': juries, 'leaderboard': leaderboard,
            'unreviewed_articles': unreviewed_articles_mapped
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@editathons_bp.route('/api/editathon/<int:editathon_id>', methods=['PUT'])
def update_editathon(editathon_id):
    try:
        editathon = Editathon.query.get(editathon_id)
        if not editathon: return jsonify({"error": "Editathon not found"}), 404
        data = request.json
        if data.get('title'): editathon.name = data['title']
        if data.get('description') is not None: editathon.description = data['description']
        if data.get('wiki_language'):
            editathon.language = data['wiki_language']
            editathon.wiki_domain = f"{data['wiki_language']}.wikipedia.org"
        if data.get('startDate'): editathon.start_date = datetime.strptime(data['startDate'], '%Y-%m-%d').date()
        if data.get('endDate'): editathon.end_date = datetime.strptime(data['endDate'], '%Y-%m-%d').date()
        if data.get('code'): editathon.code = data['code']

        if data.get('project'):
            project = Project.query.filter_by(name=data['project']).first()
            if not project:
                creator = User.query.get(editathon.created_by)
                project = Project(name=data['project'], description=f"Project for {data['project']}", created_by=creator.id if creator else None)
                db.session.add(project)
                db.session.flush()
            editathon.project_id = project.id

        marks_data = data.get('marks', [])
        if marks_data:
            editathon.marks_config = {
                'marks': marks_data,
                'hidden_marks': data.get('hiddenMarks', False),
                'consensual_vote': data.get('consensualVote', False)
            }
        editathon.status = 'draft'

        EditathonJury.query.filter_by(editathon_id=editathon_id).delete()
        jury_data = data.get('jury', [])
        for jury_member in jury_data:
            if isinstance(jury_member, dict) and jury_member.get('username'):
                username = jury_member['username']
                jury_user = User.query.filter_by(username=username).first()
                if not jury_user:
                    jury_user = User(username=username, email=f"{username}@wikipedia.org", password_hash='oauth_user', role='jury')
                    db.session.add(jury_user); db.session.flush()
                db.session.add(EditathonJury(editathon_id=editathon.id, user_id=jury_user.id, role='main'))

        EditathonRule.query.filter_by(editathon_id=editathon_id).delete()
        rules_data = data.get('rules', [])
        creator = User.query.get(editathon.created_by)
        for rule_data in rules_data:
            if isinstance(rule_data, dict) and rule_data.get('type'):
                rule = Rule(
                    name=rule_data.get('type', 'Rule'), rule_type=rule_data.get('type', 'custom'),
                    condition_text=str(rule_data.get('config', {})), description=rule_data.get('description', ''),
                    created_by=creator.id if creator else None
                )
                db.session.add(rule); db.session.flush()
                db.session.add(EditathonRule(editathon_id=editathon.id, rule_id=rule.id, is_active=True))

        db.session.commit()
        from logger import log_activity
        from flask import session
        user_id = session.get('user', {}).get('id')
        if user_id: log_activity(user_id, 'update', 'editathon', editathon.id, {'name': editathon.name})
        return jsonify({"success": True, "id": editathon.id, "status": editathon.status})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@editathons_bp.route('/api/editathon/<int:editathon_id>', methods=['DELETE'])
def delete_editathon(editathon_id):
    try:
        editathon = Editathon.query.get(editathon_id)
        if not editathon: return jsonify({"error": "Editathon not found"}), 404
        Mark.query.filter(Mark.article_id.in_(db.session.query(Article.id).filter_by(editathon_id=editathon_id))).delete(synchronize_session='fetch')
        Article.query.filter_by(editathon_id=editathon_id).delete()
        EditathonJury.query.filter_by(editathon_id=editathon_id).delete()
        EditathonRule.query.filter_by(editathon_id=editathon_id).delete()
        EditathonStat.query.filter_by(editathon_id=editathon_id).delete()
        db.session.delete(editathon); db.session.commit()
        from logger import log_activity
        from flask import session
        user_id = session.get('user', {}).get('id')
        if user_id: log_activity(user_id, 'delete', 'editathon', editathon_id, {'title': editathon.name})
        return jsonify({"success": True, "message": f"Editathon {editathon_id} deleted"})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@editathons_bp.route('/api/editathons/pending', methods=['GET'])
def get_pending_editathons():
    try:
        pending_editathons = Editathon.query.filter_by(status='draft').all()
        result = []
        for editathon in pending_editathons:
            creator = User.query.get(editathon.created_by)
            project_obj = Project.query.get(editathon.project_id) if editathon.project_id else None
            result.append({
                'id': editathon.id, 'code': editathon.code, 'title': editathon.name, 'name': editathon.name,
                'description': editathon.description, 'wiki_language': editathon.language,
                'project': project_obj.name if project_obj else editathon.wiki_domain or 'N/A',
                'startDate': editathon.start_date.isoformat() if editathon.start_date else None,
                'endDate': editathon.end_date.isoformat() if editathon.end_date else None,
                'submissionDate': editathon.created_at.isoformat() if editathon.created_at else None,
                'createdBy': creator.username if creator else 'Unknown', 'status': editathon.status
            })
        return jsonify({"success": True, "editathons": result, "count": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@editathons_bp.route('/api/editathon/<editathon_id>/approve', methods=['POST'])
def approve_editathon(editathon_id):
    try:
        editathon = Editathon.query.get(editathon_id)
        if not editathon: return jsonify({"error": "Editathon not found"}), 404
        editathon.status = 'active'; editathon.is_published = True
        db.session.commit()
        from logger import log_activity
        from flask import session
        user_id = session.get('user', {}).get('id')
        if user_id: log_activity(user_id, 'approve', 'editathon', editathon.id, {'title': editathon.name})
        return jsonify({"success": True, "message": f"Editathon '{editathon.name}' approved successfully", "status": "active"})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@editathons_bp.route('/api/editathon/<editathon_id>/reject', methods=['POST'])
def reject_editathon(editathon_id):
    try:
        data = request.json
        reason = data.get('reason', 'No reason provided') if data else 'No reason provided'
        editathon = Editathon.query.get(editathon_id)
        if not editathon: return jsonify({"error": "Editathon not found"}), 404
        editathon.status = 'rejected'; db.session.commit()
        from logger import log_activity
        from flask import session
        user_id = session.get('user', {}).get('id')
        if user_id: log_activity(user_id, 'reject', 'editathon', editathon.id, {'title': editathon.name, 'reason': reason})
        return jsonify({"success": True, "message": f"Editathon '{editathon.name}' rejected. Reason: {reason}", "status": "rejected"})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500
