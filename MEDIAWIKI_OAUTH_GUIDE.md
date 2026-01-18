# MediaWiki OAuth Integration Guide

This guide provides comprehensive instructions for integrating MediaWiki OAuth authentication into the Wikimedia Editathon Review Tool.

## Overview

MediaWiki OAuth allows users to authenticate using their Wikipedia/MediaWiki accounts without sharing their passwords. This integration provides seamless access to Wikipedia APIs and user authentication.

## 1. MediaWiki OAuth Setup

### Step 1: Create OAuth Consumer

1. **Visit MediaWiki OAuth Registration**
   - Go to https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose
   - Log in with your MediaWiki account

2. **Fill Application Details**
   ```
   Application name: Wikimedia Editathon Review Tool
   Application version: 1.0
   Application description: A tool for reviewing and managing Wikipedia editathons
   ```

3. **Set OAuth Configuration**
   ```
   OAuth "callback" URL: http://localhost:5000/auth/mediawiki/callback
   Allow consumer to specify a callback in requests: Yes
   Applicable grants: Basic rights
   ```

4. **Request Additional Grants**
   - Read your watchlist
   - Read your own private data
   - Create, edit, and move pages
   - Upload new files

5. **Submit and Get Credentials**
   - After approval, you'll receive:
     - Consumer key
     - Consumer secret

### Step 2: Configure Application

Add to your backend `.env` file:
```env
MEDIAWIKI_CONSUMER_KEY=your_consumer_key_here
MEDIAWIKI_CONSUMER_SECRET=your_consumer_secret_here
MEDIAWIKI_BASE_URL=https://en.wikipedia.org/w/api.php
OAUTH_CALLBACK_URL=http://localhost:5000/auth/mediawiki/callback
```

## 2. Backend Implementation

### Install Required Dependencies

Add to `requirements.txt`:
```
requests-oauthlib==1.3.1
oauthlib==3.2.2
mwparserfromhell==0.6.4
```

### OAuth Service Implementation

Create `backend/services/mediawiki_oauth.py`:

```python
import os
import requests
from requests_oauthlib import OAuth1Session
from flask import session, request, redirect, url_for, current_app
import json

class MediaWikiOAuth:
    def __init__(self):
        self.consumer_key = os.getenv('MEDIAWIKI_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MEDIAWIKI_CONSUMER_SECRET')
        self.base_url = os.getenv('MEDIAWIKI_BASE_URL', 'https://en.wikipedia.org/w/api.php')
        self.oauth_base_url = 'https://en.wikipedia.org/w/index.php'
        
    def get_request_token(self):
        """Step 1: Get request token"""
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            callback_uri=os.getenv('OAUTH_CALLBACK_URL')
        )
        
        request_token_url = f"{self.oauth_base_url}?title=Special:OAuth/initiate"
        
        try:
            fetch_response = oauth.fetch_request_token(request_token_url)
            session['oauth_token'] = fetch_response.get('oauth_token')
            session['oauth_token_secret'] = fetch_response.get('oauth_token_secret')
            return fetch_response
        except Exception as e:
            current_app.logger.error(f"Error getting request token: {e}")
            return None
    
    def get_authorization_url(self, request_token):
        """Step 2: Get authorization URL"""
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=request_token['oauth_token']
        )
        
        authorization_url = oauth.authorization_url(
            f"{self.oauth_base_url}?title=Special:OAuth/authorize"
        )
        return authorization_url
    
    def get_access_token(self, oauth_verifier):
        """Step 3: Get access token"""
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=session.get('oauth_token'),
            resource_owner_secret=session.get('oauth_token_secret'),
            verifier=oauth_verifier
        )
        
        access_token_url = f"{self.oauth_base_url}?title=Special:OAuth/token"
        
        try:
            oauth_tokens = oauth.fetch_access_token(access_token_url)
            return oauth_tokens
        except Exception as e:
            current_app.logger.error(f"Error getting access token: {e}")
            return None
    
    def get_user_info(self, access_token, access_token_secret):
        """Get user information using access token"""
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        params = {
            'action': 'query',
            'meta': 'userinfo',
            'uiprop': 'blockinfo|groups|implicitgroups|rights|changeablegroups|options|editcount|ratelimits|email',
            'format': 'json'
        }
        
        try:
            response = oauth.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Error getting user info: {e}")
            return None
    
    def make_api_request(self, access_token, access_token_secret, params):
        """Make authenticated API request to MediaWiki"""
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        try:
            response = oauth.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"API request error: {e}")
            return None
    
    def get_user_contributions(self, access_token, access_token_secret, username, limit=50):
        """Get user contributions"""
        params = {
            'action': 'query',
            'list': 'usercontribs',
            'ucuser': username,
            'uclimit': limit,
            'ucprop': 'ids|title|timestamp|comment|size|flags|tags',
            'format': 'json'
        }
        
        return self.make_api_request(access_token, access_token_secret, params)
    
    def get_page_info(self, access_token, access_token_secret, titles):
        """Get page information"""
        params = {
            'action': 'query',
            'titles': titles,
            'prop': 'info|revisions',
            'inprop': 'url|length|watchers',
            'rvprop': 'content|timestamp|user|comment',
            'format': 'json'
        }
        
        return self.make_api_request(access_token, access_token_secret, params)
```

### Authentication Routes

Add to `backend/app.py`:

```python
from services.mediawiki_oauth import MediaWikiOAuth

# Initialize OAuth service
oauth_service = MediaWikiOAuth()

@app.route('/auth/mediawiki/login')
def mediawiki_login():
    """Initiate MediaWiki OAuth login"""
    request_token = oauth_service.get_request_token()
    if not request_token:
        return jsonify({'error': 'Failed to get request token'}), 500
    
    authorization_url = oauth_service.get_authorization_url(request_token)
    return redirect(authorization_url)

@app.route('/auth/mediawiki/callback')
def mediawiki_callback():
    """Handle MediaWiki OAuth callback"""
    oauth_verifier = request.args.get('oauth_verifier')
    if not oauth_verifier:
        return jsonify({'error': 'No verifier provided'}), 400
    
    # Get access token
    access_tokens = oauth_service.get_access_token(oauth_verifier)
    if not access_tokens:
        return jsonify({'error': 'Failed to get access token'}), 500
    
    # Get user info
    user_info = oauth_service.get_user_info(
        access_tokens['oauth_token'],
        access_tokens['oauth_token_secret']
    )
    
    if not user_info:
        return jsonify({'error': 'Failed to get user info'}), 500
    
    # Extract user data
    userinfo_data = user_info.get('query', {}).get('userinfo', {})
    username = userinfo_data.get('name')
    user_id = userinfo_data.get('id')
    user_groups = userinfo_data.get('groups', [])
    
    # Store in session
    session['user_id'] = user_id
    session['username'] = username
    session['access_token'] = access_tokens['oauth_token']
    session['access_token_secret'] = access_tokens['oauth_token_secret']
    session['user_groups'] = user_groups
    
    # Create or update user in database
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=f"{username}@mediawiki.org",  # Placeholder email
            password_hash="oauth",  # Mark as OAuth user
            role='participant'
        )
        db.session.add(user)
        db.session.commit()
    
    # Redirect to frontend
    return redirect(f"http://localhost:5173/dashboard")

@app.route('/auth/logout')
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/user/current')
def get_current_user():
    """Get current authenticated user"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'username': session['username'],
        'user_id': session.get('user_id'),
        'groups': session.get('user_groups', []),
        'authenticated': True
    })
```

## 3. Frontend Integration

### OAuth Login Component

Create `frontend/src/components/MediaWikiLogin.vue`:

```vue
<template>
  <div class="mediawiki-login">
    <div v-if="!isAuthenticated" class="login-section">
      <h3>Login with Wikipedia</h3>
      <p>Connect your Wikipedia account to participate in editathons</p>
      <button @click="loginWithMediaWiki" class="btn btn-primary">
        <i class="fab fa-wikipedia-w"></i>
        Login with Wikipedia
      </button>
    </div>
    
    <div v-else class="user-info">
      <h4>Welcome, {{ user.username }}!</h4>
      <p>Connected to Wikipedia</p>
      <button @click="logout" class="btn btn-outline-secondary">
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api.js'

const router = useRouter()
const isAuthenticated = ref(false)
const user = ref(null)

const loginWithMediaWiki = () => {
  // Redirect to backend OAuth endpoint
  window.location.href = 'http://localhost:5000/auth/mediawiki/login'
}

const logout = async () => {
  try {
    await api.post('/auth/logout')
    isAuthenticated.value = false
    user.value = null
    router.push('/')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

const checkAuthStatus = async () => {
  try {
    const response = await api.get('/api/user/current')
    isAuthenticated.value = true
    user.value = response.data
  } catch (error) {
    isAuthenticated.value = false
    user.value = null
  }
}

onMounted(() => {
  checkAuthStatus()
})
</script>

<style scoped>
.mediawiki-login {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
}

.login-section {
  text-align: center;
}

.user-info {
  text-align: center;
}

.btn {
  padding: 10px 20px;
  margin: 5px;
}
</style>
```

### API Service Updates

Update `frontend/src/services/api.js`:

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000',
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  }
})

// Response interceptor for handling auth errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login if unauthorized
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// Specific API functions
export const authAPI = {
  getCurrentUser: () => api.get('/api/user/current'),
  logout: () => api.post('/auth/logout')
}

export const editathonAPI = {
  getAll: () => api.get('/api/editathons'),
  getById: (id) => api.get(`/api/editathons/${id}`),
  create: (data) => api.post('/api/editathons', data),
  update: (id, data) => api.put(`/api/editathons/${id}`, data)
}

export const wikipediaAPI = {
  getUserContributions: (username) => api.get(`/api/wikipedia/contributions/${username}`),
  getPageInfo: (titles) => api.post('/api/wikipedia/pages', { titles }),
  searchPages: (query) => api.get(`/api/wikipedia/search?q=${query}`)
}
```

## 4. Wikipedia API Integration

### Backend Wikipedia API Service

Create `backend/services/wikipedia_api.py`:

```python
import requests
from flask import session, current_app
from services.mediawiki_oauth import MediaWikiOAuth

class WikipediaAPI:
    def __init__(self):
        self.oauth_service = MediaWikiOAuth()
        self.base_url = "https://en.wikipedia.org/w/api.php"
    
    def _get_auth_tokens(self):
        """Get OAuth tokens from session"""
        access_token = session.get('access_token')
        access_token_secret = session.get('access_token_secret')
        
        if not access_token or not access_token_secret:
            raise Exception('User not authenticated with MediaWiki')
        
        return access_token, access_token_secret
    
    def get_page_content(self, page_title, language='en'):
        """Get page content"""
        access_token, access_token_secret = self._get_auth_tokens()
        
        params = {
            'action': 'query',
            'format': 'json',
            'titles': page_title,
            'prop': 'revisions|info',
            'rvprop': 'content|timestamp|user|comment|ids',
            'inprop': 'url|length|watchers'
        }
        
        return self.oauth_service.make_api_request(
            access_token, access_token_secret, params
        )
    
    def get_page_history(self, page_title, limit=50):
        """Get page revision history"""
        access_token, access_token_secret = self._get_auth_tokens()
        
        params = {
            'action': 'query',
            'format': 'json',
            'titles': page_title,
            'prop': 'revisions',
            'rvprop': 'ids|timestamp|user|comment|size|flags',
            'rvlimit': limit
        }
        
        return self.oauth_service.make_api_request(
            access_token, access_token_secret, params
        )
    
    def search_pages(self, query, limit=20):
        """Search for pages"""
        access_token, access_token_secret = self._get_auth_tokens()
        
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': limit,
            'srprop': 'size|wordcount|timestamp|snippet'
        }
        
        return self.oauth_service.make_api_request(
            access_token, access_token_secret, params
        )
    
    def get_user_contributions(self, username, start_date=None, end_date=None, limit=500):
        """Get user contributions within date range"""
        access_token, access_token_secret = self._get_auth_tokens()
        
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'usercontribs',
            'ucuser': username,
            'uclimit': limit,
            'ucprop': 'ids|title|timestamp|comment|size|flags|sizediff',
            'ucdir': 'newer'
        }
        
        if start_date:
            params['ucstart'] = start_date.isoformat()
        if end_date:
            params['ucend'] = end_date.isoformat()
        
        return self.oauth_service.make_api_request(
            access_token, access_token_secret, params
        )
    
    def get_page_views(self, page_title, start_date, end_date):
        """Get page view statistics"""
        # Note: Page views API doesn't require authentication
        pageviews_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents"
        
        url = f"{pageviews_url}/{page_title}/daily/{start_date}/{end_date}"
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'WikiEditathonTool/1.0 (https://github.com/your-repo)'
            })
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Error getting page views: {e}")
            return None

# Add routes to app.py
wikipedia_api = WikipediaAPI()

@app.route('/api/wikipedia/page/<path:title>')
def get_wikipedia_page(title):
    """Get Wikipedia page content"""
    try:
        data = wikipedia_api.get_page_content(title)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wikipedia/search')
def search_wikipedia():
    """Search Wikipedia pages"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20)
    
    try:
        data = wikipedia_api.search_pages(query, limit)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wikipedia/contributions/<username>')
def get_user_contributions(username):
    """Get user contributions"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # Convert date strings to datetime objects if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        data = wikipedia_api.get_user_contributions(username, start_dt, end_dt)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 5. Security Considerations

### Secure Token Storage

```python
# In production, use secure session configuration
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### Environment Variables

```bash
# Production environment variables
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
MEDIAWIKI_CONSUMER_KEY=your-production-consumer-key
MEDIAWIKI_CONSUMER_SECRET=your-production-consumer-secret
OAUTH_CALLBACK_URL=https://yourdomain.com/auth/mediawiki/callback
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

@app.route('/api/wikipedia/search')
@limiter.limit("10 per minute")
def search_wikipedia():
    # ... implementation
```

## 6. Testing OAuth Integration

### Test OAuth Flow

1. **Start both backend and frontend servers**
2. **Navigate to login page**
3. **Click "Login with Wikipedia"**
4. **Complete OAuth authorization on Wikipedia**
5. **Verify successful redirect and user session**

### Test API Calls

```bash
# Test authenticated endpoint
curl -X GET http://localhost:5000/api/user/current \
  -H "Cookie: session=your_session_cookie"

# Test Wikipedia API integration
curl -X GET http://localhost:5000/api/wikipedia/search?q=Python \
  -H "Cookie: session=your_session_cookie"
```

## 7. Troubleshooting

### Common Issues

1. **OAuth Callback URL Mismatch**
   - Ensure callback URL in MediaWiki matches your application
   - Check for HTTP vs HTTPS mismatches

2. **CORS Issues**
   - Verify CORS configuration allows your frontend domain
   - Check credentials are included in requests

3. **Session Issues**
   - Verify session configuration
   - Check cookie settings for your domain

4. **API Rate Limits**
   - Implement proper rate limiting
   - Handle rate limit responses gracefully

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

## 8. Production Deployment

### Additional Dependencies

```txt
# Add to requirements.txt for production
gunicorn==21.2.0
redis==4.6.0
celery==5.3.1
```

### Production Configuration

```python
# production_config.py
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    MEDIAWIKI_CONSUMER_KEY = os.environ.get('MEDIAWIKI_CONSUMER_KEY')
    MEDIAWIKI_CONSUMER_SECRET = os.environ.get('MEDIAWIKI_CONSUMER_SECRET')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True
```

This comprehensive MediaWiki OAuth integration guide provides everything needed to implement secure Wikipedia authentication in your editathon review tool.