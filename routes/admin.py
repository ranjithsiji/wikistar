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
