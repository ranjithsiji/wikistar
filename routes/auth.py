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
    try:
        from authlib.integrations.base_client.errors import OAuthError
        try:
            token = oauth.mediawiki.authorize_access_token()
        except OAuthError as e:
            print(f"⚠️ OAuth Error during access token exchange: {e.error} / {e.description}")
            return f"Auth Error: {e.description}", 400

        resp = oauth.mediawiki.get('oauth2/resource/profile', token=token)
        
        # In case the response is not valid JSON
        try:
            profile = resp.json()
        except Exception:
            print(f"⚠️ Failed to parse JSON from MediaWiki Profile Endpoint. Response body: {resp.text}")
            return "Failed to parse profile response from MediaWiki", 500

        username = profile.get('username')
        if not username:
            print(f"⚠️ Username missing from profile. Profile data: {profile}")
            return "Failed to fetch username from MediaWiki", 400

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=f"{username.replace(' ', '_')}@wikipedia.org",
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return "Internal Server Error during login. Check server logs for details.", 500

@auth_bp.route('/api/me')
def get_current_user():
    user_data = session.get('user')
    return jsonify({"user": user_data})

@auth_bp.route('/api/logout')
def logout():
    session.pop('user', None)
    return redirect('/')
