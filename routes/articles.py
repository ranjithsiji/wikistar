from flask import Blueprint, jsonify, request
from extensions import db
from models import User, Editathon, Article, Mark, EditathonJury, Rule, EditathonRule

articles_bp = Blueprint('articles', __name__)

@articles_bp.route('/api/editathon/<editathon_id>/submit', methods=['POST'])
def submit_article(editathon_id):
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        if not user: return jsonify({"error": "User not found"}), 404
        editathon = Editathon.query.get(editathon_id)
        if not editathon: return jsonify({"error": "Editathon not found"}), 404
        
        is_jury = EditathonJury.query.filter_by(editathon_id=editathon_id, user_id=user.id).first() is not None
        if is_jury:
            prevent_rule = db.session.query(Rule).join(EditathonRule).filter(
                EditathonRule.editathon_id == editathon_id,
                EditathonRule.is_active == True,
                Rule.rule_type == 'prevent_judge_submission'
            ).first()
            if prevent_rule:
                return jsonify({"error": "Jury members cannot submit articles for this editathon"}), 403
        
        article = Article(
            editathon_id=editathon.id, title=data['article_title'],
            wikipedia_url=data.get('wikipedia_url'), submitted_by=user.id, status='pending'
        )
        db.session.add(article); db.session.commit()
        return jsonify({"message": f"Article '{article.title}' submitted successfully", "article_id": article.id, "success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@articles_bp.route('/api/articles', methods=['POST'])
def submit_article_alt():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        if not user: return jsonify({"error": "User not found"}), 404
        editathon = Editathon.query.filter_by(code=data['editathon_code']).first()
        if not editathon: return jsonify({"error": "Editathon not found"}), 404
        
        article = Article(
            editathon_id=editathon.id, title=data['title'],
            wikipedia_url=data.get('wikipedia_url'), submitted_by=user.id, status='pending'
        )
        db.session.add(article); db.session.commit()
        return jsonify({"message": f"Article '{article.title}' submitted successfully", "article_id": article.id, "success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@articles_bp.route('/api/editathon/<editathon_id>/judge', methods=['POST'])
def judge_article(editathon_id):
    try:
        data = request.json
        jury_user = User.query.filter_by(username=data.get('reviewer', 'Unknown')).first()
        if not jury_user: return jsonify({"error": "Jury user not found"}), 404
        article = Article.query.filter_by(editathon_id=editathon_id, title=data['article_title']).first()
        if not article: return jsonify({"error": "Article not found"}), 404
        
        jury_assignment = EditathonJury.query.filter_by(editathon_id=editathon_id, user_id=jury_user.id).first()
        if not jury_assignment and jury_user.role != 'admin':
            return jsonify({"error": "Jury not assigned to this editathon"}), 403
        
        mark = Mark.query.filter_by(article_id=article.id, jury_id=jury_user.id).first()
        points = data.get('points', 0)
        decision = data.get('decision', 'accepted')
        comment = data.get('comment', '')
        
        if mark:
            mark.criteria_scores = {"total": points}; mark.total_score = points
            mark.comments = comment; mark.decision = 'accept' if decision == 'accepted' else 'reject'
        else:
            mark = Mark(
                article_id=article.id, jury_id=jury_user.id, criteria_scores={"total": points},
                total_score=points, comments=comment, decision='accept' if decision == 'accepted' else 'reject'
            )
            db.session.add(mark)
        
        article.points = points
        article.status = 'accepted' if decision == 'accepted' else 'rejected'
        db.session.commit()
        return jsonify({"message": f"Article '{article.title}' judged with {points} points", "success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@articles_bp.route('/api/marks', methods=['POST'])
def add_marks():
    try:
        data = request.json
        jury_user = User.query.filter_by(username=data['jury_username']).first()
        if not jury_user or jury_user.role != 'jury': return jsonify({"error": "Jury user not found"}), 403
        article = Article.query.get(data['article_id'])
        if not article: return jsonify({"error": "Article not found"}), 404
        
        mark = Mark.query.filter_by(article_id=article.id, jury_id=jury_user.id).first()
        if mark:
            mark.criteria_scores = data['criteria_scores']; mark.total_score = data['total_score']
            mark.comments = data.get('comments'); mark.decision = data['decision']
        else:
            mark = Mark(
                article_id=article.id, jury_id=jury_user.id, criteria_scores=data['criteria_scores'],
                total_score=data['total_score'], comments=data.get('comments'), decision=data['decision']
            )
            db.session.add(mark)
        db.session.commit()
        return jsonify({"message": "Marks added successfully", "mark_id": mark.id, "success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@articles_bp.route('/api/jury-review', methods=['POST'])
def jury_review_toggle():
    try:
        data = request.json
        article_id = data.get('article_id'); jury_username = data.get('jury_username')
        checked = data.get('checked', True)
        if not article_id or not jury_username: return jsonify({"error": "Missing params"}), 400
        article = Article.query.get(article_id)
        jury_user = User.query.filter_by(username=jury_username).first()
        if not article or not jury_user: return jsonify({"error": "Not found"}), 404
        
        mark = Mark.query.filter_by(article_id=article.id, jury_id=jury_user.id).first()
        if checked:
            if mark: mark.decision = 'accept'
            else:
                mark = Mark(article_id=article.id, jury_id=jury_user.id, criteria_scores={}, total_score=0, decision='accept')
                db.session.add(mark)
        elif mark:
            db.session.delete(mark)
        db.session.commit()
        return jsonify({"success": True, "checked": checked})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@articles_bp.route('/api/editathon/<int:editathon_id>/jury-reviews', methods=['GET'])
def get_jury_reviews(editathon_id):
    try:
        articles = Article.query.filter_by(editathon_id=editathon_id).all()
        result = {}
        for article in articles:
            marks = Mark.query.filter_by(article_id=article.id).all()
            result[article.id] = [User.query.get(m.jury_id).username for m in marks if User.query.get(m.jury_id)]
        return jsonify({"reviews": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
