# Starkforge Wiki-For-All Review Tool

A comprehensive tool for managing and reviewing Wikipedia editathons with Vue.js frontend and Flask backend.

## 📋 Project Overview

This tool helps manage Wikipedia editathons by providing:
- Editathon creation and management
- Article submission and review system
- Jury management and voting
- Statistical analysis of editathon performance
- Multi-language support

## 🏗️ Project Structure

```
Starkforge_reviewtool/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database initialization
│   ├── requirements.txt    # Python dependencies
│   └── routes/             # API routes
│       ├── auth.py         # Authentication endpoints
│       ├── editathons.py   # Editathon management
│       ├── mark.py         # Voting and marking system
│       ├── rules.py        # Rule management
│       └── stats.py        # Statistics and analytics
│
├── frontend/               # Vue.js frontend application
│   ├── src/
│   │   ├── components/     # Vue components
│   │   │   ├── GeneralTab.vue      # Editathon general settings
│   │   │   ├── RulesTab.vue        # Rule configuration
│   │   │   ├── MarksTab.vue        # Voting/marking system
│   │   │   ├── TemplateTab.vue     # Template management
│   │   │   ├── JuryTab.vue         # Jury management
│   │   │   ├── EditathonCard.vue   # Editathon display
│   │   │   ├── ArticleTable.vue    # Article listing
│   │   │   └── VotePanel.vue       # Voting interface
│   │   ├── views/          # Page components
│   │   │   ├── Home.vue            # Dashboard
│   │   │   ├── CreateEditathon.vue # Editathon creation
│   │   │   ├── EditathonDetail.vue # Editathon details
│   │   │   └── JudgeView.vue       # Judging interface
│   │   ├── services/       # API services
│   │   ├── assets/         # Styles and configuration
│   │   └── router.js       # Vue Router configuration
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite build configuration
│
└── instance/               # Instance-specific files
    └── dev_data.db         # SQLite database (development)
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- Python 3.8+
- npm or yarn

### Backend Setup
```bash
cd Starkforge_reviewtool/backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the backend server
python app.py
```
Backend runs on http://localhost:4000

### Frontend Setup
```bash
cd Starkforge_reviewtool/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend runs on http://localhost:5173

## 🎯 Features

### Editathon Management
- Create and configure new editathons
- Set time periods and rules
- Manage jury members
- Configure evaluation criteria

### Article Review System
- Submit articles for review
- Multiple voting systems (toggle, radio, numeric)
- Real-time voting interface
- Consensus-based decision making

### Jury & Voting
- Multi-juror support
- Hidden/anonymous voting options
- Vote tracking and statistics
- Result compilation

### Analytics & Reporting
- Editathon performance metrics
- Article acceptance/rejection rates
- Timeline visualizations
- Export capabilities

## 🔧 Configuration

### Backend Environment Variables
Create a `.env` file in the backend directory:
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/dev_data.db
SECRET_KEY=your-secret-key-here
```

### Frontend Configuration
API endpoints are configured in `src/assets/api.js` and `src/services/api.js`

## 📊 Database Schema

Key models include:
- **Editathons**: Editathon events with configurations
- **Articles**: Submitted articles for review
- **Users/Jury**: Review panel members
- **Votes/Marks**: Evaluation results
- **Rules**: Editathon-specific guidelines

## 🛠️ Development

### Adding New Features
1. Backend: Add routes in `routes/` directory
2. Frontend: Create Vue components in `src/components/`
3. Update database models in `models.py` if needed
4. Test API endpoints and frontend integration

### Code Style
- Backend: Follow PEP 8 standards
- Frontend: Use Vue 3 composition API
- Consistent naming conventions

## 📝 API Documentation

### Key Endpoints
- `GET /api/editathons` - List all editathons
- `POST /api/editathons` - Create new editathon
- `GET /api/editathons/:id` - Get editathon details
- `POST /api/editathons/:id/articles` - Submit article
- `POST /api/vote` - Submit vote

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request


---

**Note**: This is a development version. For production deployment, ensure proper security configurations and database setup.
