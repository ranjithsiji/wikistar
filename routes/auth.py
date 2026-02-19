from flask import Blueprint, jsonify, redirect, session, url_for, current_app
from extensions import db, oauth
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login')
def login():
    if not current_app.config.get('OAUTH_ENABLED'):
        # For dev mode, auto-login as TestUser
        username = 'TestParticipant'
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=f"{username}@local.dev", password_hash="dev_pass", role='participant')
            db.session.add(user)
            db.session.commit()
            
        session['user'] = {'username': user.username, 'id': user.id, 'role': user.role}
        return redirect('/')
    
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
        # Create new user if they don't exist
        user = User(
            username=username,
            email=f"{username}@wikipedia.org", # Placeholder
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
    # Return both user data and dev_mode status
    # dev_mode is true if OAuth is disabled
    dev_mode = not current_app.config.get('OAUTH_ENABLED')
    
    return jsonify({
        "user": user_data,
        "dev_mode": dev_mode
    })

@auth_bp.route('/api/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Dev routes for easy testing of different roles
@auth_bp.route('/api/dev-login/<role>')
def dev_login_role(role):
    if current_app.config.get('OAUTH_ENABLED'):
        return "Dev login disabled in production", 403
    
    roles_map = {
        'admin': {'username': 'DevAdmin', 'role': 'admin'},
        'jury': {'username': 'DevJury', 'role': 'jury'},
        'participant': {'username': 'DevUser', 'role': 'participant'}
    }
    
    if role not in roles_map:
        return "Invalid role", 400
        
    user_info = roles_map[role]
    user = User.query.filter_by(username=user_info['username']).first()
    if not user:
        user = User(
            username=user_info['username'],
            email=f"{user_info['username']}@local.dev",
            password_hash="dev_pass",
            role=user_info['role']
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Sync role
        user.role = user_info['role']
        db.session.commit()

    session['user'] = {
        'id': user.id,
        'username': user.username,
        'role': user.role
    }
    return redirect('/')
