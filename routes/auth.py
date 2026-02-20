from flask import Blueprint, jsonify, redirect, session, url_for, current_app
from extensions import db, oauth
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login')
def login():
    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.mediawiki.authorize_redirect(redirect_uri)

@auth_bp.route('/oauth-callback')
def callback():
    token = oauth.mediawiki.authorize_access_token()
    resp = oauth.mediawiki.get('oauth2/resource/profile', token=token)
    profile = resp.json()

    username = profile.get('username')
    if not username:
        return "Failed to fetch username from MediaWiki", 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=f"{username}@wikipedia.org",
            password_hash="oauth_user",
            role='participant'
        )
        db.session.add(user)
        db.session.commit()

    session['user'] = {
        'id': user.id,
        'username': user.username,
        'role': user.role
    }

    return redirect('/')

@auth_bp.route('/api/me')
def get_current_user():
    user_data = session.get('user')
    return jsonify({"user": user_data})

@auth_bp.route('/api/logout')
def logout():
    session.pop('user', None)
    return redirect('/')
