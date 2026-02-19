from flask import Blueprint, jsonify
from extensions import db
from models import User, Article, Editathon, Project, EditathonJury
from utils import format_project_label
from sqlalchemy import func

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/personal-cabinet/<username>', methods=['GET'])
def get_personal_cabinet(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user: return jsonify({"error": "User not found"}), 404

        user_articles = Article.query.filter_by(submitted_by=user.id).all()
        articles_by_editathon = {}
        for article in user_articles:
            editathon = Editathon.query.get(article.editathon_id)
            if not editathon: continue
            if editathon.id not in articles_by_editathon:
                articles_by_editathon[editathon.id] = {'editathon': editathon, 'articles': []}
            articles_by_editathon[editathon.id]['articles'].append(article)

        articles_data = []
        total_points = 0
        for entry in articles_by_editathon.values():
            editathon = entry['editathon']
            for article in entry['articles']:
                articles_data.append({
                    'editathon': editathon.name, 'editathon_code': editathon.code, 'article_title': article.title,
                    'points': article.points, 'notes': article.notes,
                    'submitted_date': article.submitted_at.isoformat() if article.submitted_at else None, 'status': article.status
                })
                total_points += article.points or 0

        created_editathons = Editathon.query.filter_by(created_by=user.id).all()
        created_data = [{
            'id': e.id, 'name': e.name, 'description': e.description, 'status': e.status, 'language': e.language,
            'start_date': e.start_date.isoformat() if e.start_date else None, 'end_date': e.end_date.isoformat() if e.end_date else None
        } for e in created_editathons]

        jury_assignments = EditathonJury.query.filter_by(user_id=user.id).all()
        participated_as_jury = [{
            'editathon_id': a.editathon_id,
            'editathon_name': Editathon.query.get(a.editathon_id).name if Editathon.query.get(a.editathon_id) else 'Unknown',
            'role': a.role
        } for a in jury_assignments]

        participated_response = []
        for entry in articles_by_editathon.values():
            editathon = entry['editathon']
            project_obj = Project.query.get(editathon.project_id) if getattr(editathon, 'project_id', None) else None
            project_label = format_project_label(project_obj.name if project_obj else None)

            scoreboard_rows = (
                db.session.query(User.username, func.coalesce(func.sum(Article.points), 0).label('total_points'))
                .join(User, Article.submitted_by == User.id).filter(Article.editathon_id == editathon.id)
                .group_by(User.username).order_by(func.coalesce(func.sum(Article.points), 0).desc()).all()
            )

            scoreboard = []
            user_rank, user_points = None, 0
            for idx, row in enumerate(scoreboard_rows, start=1):
                points_value = float(row.total_points or 0)
                scoreboard.append({'rank': idx, 'username': row.username, 'points': points_value})
                if row.username == user.username: user_rank, user_points = idx, points_value

            participated_response.append({
                'id': editathon.id, 'name': editathon.name, 'description': editathon.description, 'status': editathon.status,
                'start_date': editathon.start_date.isoformat() if editathon.start_date else None,
                'end_date': editathon.end_date.isoformat() if editathon.end_date else None,
                'language': editathon.language, 'project': project_label, 'project_domain': project_obj.name if project_obj else None,
                'scoreboard': scoreboard[:5], 'user_summary': {'rank': user_rank, 'points': user_points}
            })

        return jsonify({
            'username': user.username, 'role': user.role,
            'stats': {
                'articles_submitted': len(user_articles), 'editathons_participated': len(participated_response),
                'editathons_created': len(created_editathons), 'total_points': total_points, 'jury_assignments': len(jury_assignments)
            },
            'participated_editathons': participated_response, 'created_editathons': created_data,
            'jury_assignments': participated_as_jury, 'articles': articles_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_bp.route('/api/user/<username>/pending-editathons', methods=['GET'])
def get_user_pending_editathons(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user: return jsonify({"error": "User not found"}), 404
        pending = Editathon.query.filter_by(created_by=user.id, status='draft').all()
        return jsonify([{
            'id': e.id, 'code': e.code, 'name': e.name, 'description': e.description, 'language': e.language,
            'start_date': e.start_date.isoformat() if e.start_date else None,
            'end_date': e.end_date.isoformat() if e.end_date else None, 'status': e.status
        } for e in pending])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
