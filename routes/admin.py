from flask import Blueprint, jsonify, request, session
from extensions import db
from models import User, Editathon, Article, AuditLog, Project
from sqlalchemy import desc

admin_bp = Blueprint('admin', __name__)

def is_admin():
    user_data = session.get('user')
    return user_data and user_data.get('role') == 'admin'

@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    
    total_users = User.query.count()
    total_campaigns = Editathon.query.count()
    total_articles = Article.query.count()
    pending_campaigns = Editathon.query.filter_by(status='draft').count()

    return jsonify({
        "total_users": total_users,
        "total_campaigns": total_campaigns,
        "total_articles": total_articles,
        "pending_campaigns": pending_campaigns
    })

@admin_bp.route('/api/admin/logs', methods=['GET'])
def get_logs():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    logs = AuditLog.query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset).all()
    
    result = []
    for log in logs:
        user = User.query.get(log.user_id) if log.user_id else None
        result.append({
            'id': log.id,
            'username': user.username if user else 'System',
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'details': log.details,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat() if log.created_at else None
        })
    
    total_logs = AuditLog.query.count()
    
    return jsonify({
        "logs": result,
        "total": total_logs
    })

@admin_bp.route('/api/admin/articles', methods=['GET'])
def get_all_articles():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    
    articles = Article.query.order_by(desc(Article.submitted_at)).all()
    result = []
    for article in articles:
        user = User.query.get(article.submitted_by)
        editathon = Editathon.query.get(article.editathon_id)
        result.append({
            'id': article.id,
            'title': article.title,
            'editathon_name': editathon.name if editathon else 'Unknown',
            'editathon_id': editathon.id if editathon else None,
            'submitted_by': user.username if user else 'Unknown',
            'status': article.status,
            'points': article.points,
            'submitted_at': article.submitted_at.isoformat() if article.submitted_at else None
        })
    return jsonify(result)

@admin_bp.route('/api/admin/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    try:
        article = Article.query.get(article_id)
        if not article: return jsonify({"error": "Article not found"}), 404
        
        # Log this before we delete
        from logger import log_activity
        log_activity(session['user']['id'], 'delete', 'article', article.id, {'title': article.title})
        
        # We need to drop marks related to the article first, if any, or let cascading handles it
        from models import Mark
        Mark.query.filter_by(article_id=article.id).delete()
        
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Article deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/admin/campaigns', methods=['GET'])
def get_all_campaigns():
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    try:
        from models import EditathonJury, EditathonStat
        from datetime import date
        editathons = Editathon.query.order_by(desc(Editathon.created_at)).all()
        result = []
        today = date.today()
        for e in editathons:
            creator = User.query.get(e.created_by)
            project = Project.query.get(e.project_id) if e.project_id else None
            stats = EditathonStat.query.filter_by(editathon_id=e.id).first()
            jury_count = EditathonJury.query.filter_by(editathon_id=e.id).count()
            article_count = Article.query.filter_by(editathon_id=e.id).count()
            
            # Compute effective running status
            if e.status == 'active' and e.start_date and e.end_date:
                if today < e.start_date:
                    effective_status = 'upcoming'
                elif today > e.end_date:
                    effective_status = 'completed'
                else:
                    effective_status = 'running'
            else:
                effective_status = e.status

            result.append({
                'id': e.id,
                'code': e.code,
                'name': e.name,
                'description': e.description,
                'status': e.status,
                'effective_status': effective_status,
                'language': e.language,
                'wiki_domain': e.wiki_domain,
                'project': project.name if project else None,
                'start_date': e.start_date.isoformat() if e.start_date else None,
                'end_date': e.end_date.isoformat() if e.end_date else None,
                'created_by': creator.username if creator else 'Unknown',
                'created_at': e.created_at.isoformat() if e.created_at else None,
                'article_count': article_count,
                'jury_count': jury_count,
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/admin/campaigns/<int:campaign_id>', methods=['PATCH'])
def admin_update_campaign(campaign_id):
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    try:
        editathon = Editathon.query.get(campaign_id)
        if not editathon:
            return jsonify({"error": "Campaign not found"}), 404
        data = request.json
        
        if 'name' in data: editathon.name = data['name']
        if 'description' in data: editathon.description = data['description']
        if 'status' in data and data['status'] in ['draft', 'active', 'completed', 'archived', 'rejected']:
            editathon.status = data['status']
            if data['status'] == 'active':
                editathon.is_published = True
        if 'start_date' in data and data['start_date']:
            from datetime import datetime
            editathon.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data and data['end_date']:
            from datetime import datetime
            editathon.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'language' in data: editathon.language = data['language']

        db.session.commit()
        from logger import log_activity
        log_activity(session['user']['id'], 'admin_update', 'editathon', editathon.id, {'changes': data})
        return jsonify({"success": True, "message": f"Campaign '{editathon.name}' updated"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/admin/campaigns/<int:campaign_id>', methods=['DELETE'])
def admin_delete_campaign(campaign_id):
    if not is_admin():
        return jsonify({"error": "Admin access required"}), 403
    try:
        from models import Mark, EditathonJury, EditathonRule, EditathonStat
        editathon = Editathon.query.get(campaign_id)
        if not editathon:
            return jsonify({"error": "Campaign not found"}), 404
        
        name = editathon.name
        Mark.query.filter(Mark.article_id.in_(
            db.session.query(Article.id).filter_by(editathon_id=campaign_id)
        )).delete(synchronize_session='fetch')
        Article.query.filter_by(editathon_id=campaign_id).delete()
        EditathonJury.query.filter_by(editathon_id=campaign_id).delete()
        EditathonRule.query.filter_by(editathon_id=campaign_id).delete()
        EditathonStat.query.filter_by(editathon_id=campaign_id).delete()
        db.session.delete(editathon)
        db.session.commit()
        
        from logger import log_activity
        log_activity(session['user']['id'], 'admin_delete', 'editathon', campaign_id, {'name': name})
        return jsonify({"success": True, "message": f"Campaign '{name}' deleted permanently"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
