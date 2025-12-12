# Wikipedia Editathon Review Tool

A comprehensive web application for managing Wikipedia editathons, featuring a beautiful dashboard, personal cabinet, and jury evaluation system.

![Editathon Dashboard](https://img.shields.io/badge/Editathon-Review_Tool-blue)
![Vue.js](https://img.shields.io/badge/Frontend-Vue.js-green)
![Flask](https://img.shields.io/badge/Backend-Flask-red)
![MariaDB](https://img.shields.io/badge/Database-MariaDB-orange)

## 🌟 Features

###  Personal Cabinet
- **Participation Tab**: View editathons you've participated in with leaderboards
- **Evaluation Tab**: Jury dashboard with pending article counts
- **Created Tab**: Manage editathons you've created
- **Approval Tab**: Admin panel for editathon approvals

### 📊 Editathon Dashboard
- Interactive leaderboard with expandable user details
- Real-time statistics (Users, Articles, Marks, Pending reviews)
- Article submission system
- Jury evaluation interface with full-screen review mode

### 👥 User Management
- Personal statistics and achievements
- Role-based access (Participant, Jury, Admin)
- User activity tracking across multiple editathons

### 🎯 Jury System
- Collaborative article evaluation
- Point awarding system (0-1 points)
- Comment and feedback system
- Review status tracking

##  Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- MariaDB/MySQL
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Wiki-For-All-Technical/Starkforge_reviewtool.git
cd Starkforge_reviewtool
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python setup_mariadb.py
python app.py
```

3. **Frontend Setup** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

4. **Access the Application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000


## 🗄️ Database Schema

The application uses MariaDB with the following main tables:
- `wikipedia_asian_month_2025` - Asian Month editathon articles
- `wiki_loves_ramadan_2025` - Ramadan-themed content
- `women_in_red_translation_contest_2024` - Women in Red translations
- `feminism_and_folklore_2024` - Feminism and folklore articles

Each table contains:
- User submissions with article metadata
- Jury evaluations and points
- Review comments and status

## 🔧 API Endpoints

### Editathon Management
- `GET /api/editathons` - List all editathons
- `GET /api/editathon/:id` - Get editathon details
- `POST /api/editathon/:id/submit` - Submit new article
- `POST /api/editathon/:id/judge` - Evaluate article

### User Management
- `GET /api/personal-cabinet/:username` - User statistics and data
- `GET /api/user/:username` - User profile information

### Data Access
- `GET /api/wikipedia_asian_month_2025` - Asian Month data
- `GET /api/wiki_loves_ramadan_2025` - Ramadan data
- And other editathon-specific endpoints

## 🎨 UI Components

### Personal Cabinet Features
- **Tab-based Navigation**: Easy switching between different views
- **Leaderboard Display**: Real-time ranking of participants
- **Pending Review Counter**: Visual indicators for jury work
- **Responsive Design**: Works on desktop and mobile devices

### Dashboard Features
- **Expandable User Rows**: Click to view detailed article submissions
- **Modal Interfaces**: Clean popup forms for submissions and evaluations
- **Real-time Statistics**: Live updates of editathon metrics
- **Multi-language Support**: Malayalam content compatibility

## 🔄 Workflow

1. **Participant Workflow**
   - Browse available editathons
   - Submit articles for review
   - Track personal statistics
   - View evaluation results

2. **Jury Workflow**
   - Access unreviewed articles list
   - Evaluate articles with points and comments
   - Monitor review progress
   - Collaborate with other jury members

3. **Admin Workflow**
   - Create and manage editathons
   - Assign jury members
   - Approve editathon submissions
   - Monitor overall progress

