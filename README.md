# Wikimedia Editathon Review Tool

A comprehensive web application for managing and reviewing Wikipedia editathons, built with Flask backend and Vue.js frontend.

## 🌟 Features

- **Editathon Management**: Create, configure, and manage Wikipedia editathons
- **User Authentication**: Support for multiple user roles (admin, jury, participant)
- **Article Review System**: Comprehensive review and scoring system for articles
- **Real-time Dashboard**: Track progress and statistics
- **MediaWiki Integration**: OAuth integration with Wikipedia/MediaWiki
- **Multi-language Support**: Support for different Wikipedia language editions
- **Jury System**: Collaborative review process with multiple judges
- **Rule Engine**: Flexible rule configuration for different editathon types

## 🏗️ Architecture

### Backend (Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: MariaDB/MySQL
- **API**: RESTful API endpoints
- **Authentication**: Session-based + MediaWiki OAuth

### Frontend (Vue.js)
- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite
- **Styling**: Bootstrap 5
- **Charts**: Chart.js for data visualization
- **HTTP Client**: Axios for API communication

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- MariaDB/MySQL 8.0+
- Git

## 🚀 Quick Start

### Backend Setup

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   - Create a MariaDB database named `wikifountain`
   - Update database credentials in `app.py`

5. **Initialize database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Run backend**
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

## 📁 Project Structure

```
Starkforge_reviewtool/
├── app.py              # Main Flask application (serves API & Frontend)
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── cleanup_db.py       # Database utilities
├── import_editathons.py # Data import scripts
├── frontend/           # Vue.js frontend source
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/         # Page views
│   │   ├── services/      # API services
│   │   └── router/        # Vue Router configuration
│   ├── package.json       # Node.js dependencies
│   └── vite.config.mjs    # Vite configuration
└── instance/              # Instance-specific files (OAuth credentials)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FLASK_ENV=development
DATABASE_URL=mysql+pymysql://username:password@localhost/wikifountain
MEDIAWIKI_CONSUMER_KEY=your_mediawiki_consumer_key
MEDIAWIKI_CONSUMER_SECRET=your_mediawiki_consumer_secret
SECRET_KEY=your_secret_key_here
```

### Database Configuration

The application uses MariaDB/MySQL. Update the database URI in `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/database_name'
```

## 🔐 Authentication & Authorization

### User Roles

- **Admin**: Full system access, can create and manage editathons
- **Jury**: Can review and score articles
- **Participant**: Can submit articles and view results

### MediaWiki OAuth Integration

The application supports OAuth integration with MediaWiki for seamless Wikipedia authentication.

## 📊 Key Components

### Editathon Management
- Create and configure editathons
- Set rules and scoring criteria
- Manage participants and jury members
- Track progress in real-time

### Article Review System
- Multi-criteria evaluation
- Collaborative jury review
- Automated rule checking
- Detailed feedback and scoring

### Dashboard & Analytics
- Real-time statistics
- Progress tracking
- Performance metrics
- Visual charts and graphs

## 🛠️ Development

### Running in Development Mode

**Backend** (Port 5000):
```bash
cd backend
python app.py
```

**Frontend** (Port 5173):
```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend**:
```bash
npm run build
```

The built files will be in the `dist/` directory.

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/user` - Get current user

### Editathons
- `GET /api/editathons` - List editathons
- `POST /api/editathons` - Create editathon
- `GET /api/editathons/{id}` - Get editathon details
- `PUT /api/editathons/{id}` - Update editathon

### Articles
- `GET /api/articles` - List articles
- `POST /api/articles` - Add article
- `GET /api/articles/{id}` - Get article details

### Reviews
- `POST /api/reviews` - Submit review
- `GET /api/reviews/{editathon_id}` - Get reviews for editathon

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Docker Deployment

1. **Build Docker images**
   ```bash
   docker-compose build
   ```

2. **Run containers**
   ```bash
   docker-compose up -d
   ```

### Manual Deployment

1. **Backend**: Deploy Flask app using Gunicorn
2. **Frontend**: Serve built files using Nginx
3. **Database**: Set up MariaDB with proper configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

## 🔗 Useful Links

- [MediaWiki OAuth Documentation](https://www.mediawiki.org/wiki/OAuth)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Vue.js Documentation](https://vuejs.org/)
- [Bootstrap Documentation](https://getbootstrap.com/)