# API Documentation

## Authentication

All API endpoints require OAuth authentication except for public endpoints.

## Endpoints

### Authentication
- `GET /login` - Initiate OAuth login
- `GET /logout` - Logout current user
- `GET /oauth-callback` - OAuth callback endpoint

### Editathons
- `GET /api/editathons` - List all editathons
- `POST /api/editathons` - Create new editathon
- `GET /api/editathons/{id}` - Get editathon details
- `PUT /api/editathons/{id}` - Update editathon
- `DELETE /api/editathons/{id}` - Delete editathon

### Articles
- `GET /api/articles` - List articles
- `POST /api/articles` - Submit new article
- `GET /api/articles/{id}` - Get article details
- `PUT /api/articles/{id}/review` - Submit article review

### Users
- `GET /api/users/current` - Get current user info
- `GET /api/users/{id}/stats` - Get user statistics

## Response Format

All API responses follow this format:

```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message"
}
```