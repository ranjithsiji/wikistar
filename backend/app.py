from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# MariaDB database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maria123@localhost/editathons'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== EXISTING TABLE ROUTES ==========
@app.route('/api/wikipedia_asian_month_2025', methods=['GET'])
def get_wikipedia_asian_month():
    try:
        result = db.session.execute(db.text('SELECT * FROM wikipedia_asian_month_2025'))
        articles = []
        for row in result:
            articles.append({
                'id': row[0],
                'user_name': row[1],
                'article_title': row[2],
                'article_added': row[3].isoformat() if row[3] else None,
                'points': row[4],
                'jury_notes': row[5]
            })
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wiki_loves_ramadan_2025', methods=['GET'])
def get_wiki_loves_ramadan():
    try:
        result = db.session.execute(db.text('SELECT * FROM wiki_loves_ramadan_2025'))
        articles = []
        for row in result:
            articles.append({
                'id': row[0],
                'user_name': row[1],
                'article_title': row[2],
                'article_added': row[3].isoformat() if row[3] else None,
                'points': row[4],
                'jury_notes': row[5]
            })
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/women_in_red_2024', methods=['GET'])
def get_women_in_red():
    try:
        result = db.session.execute(db.text('SELECT * FROM women_in_red_translation_contest_2024'))
        articles = []
        for row in result:
            articles.append({
                'id': row[0],
                'user_name': row[1],
                'article_title': row[2],
                'article_added': row[3].isoformat() if row[3] else None,
                'points': row[4],
                'jury_notes': row[5]
            })
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/feminism_folklore_2024', methods=['GET'])
def get_feminism_folklore():
    try:
        result = db.session.execute(db.text('SELECT * FROM feminism_and_folklore_2024'))
        articles = []
        for row in result:
            articles.append({
                'id': row[0],
                'user_name': row[1],
                'article_title': row[2],
                'article_added': row[3].isoformat() if row[3] else None,
                'points': row[4],
                'jury_notes': row[5]
            })
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== HOME ROUTE ==========
@app.route('/')
def home():
    return jsonify({
        "message": "✅ Editathon Backend Connected to MariaDB",
        "status": "success",
        "database": "MariaDB",
        "tables": [
            "wikipedia_asian_month_2025",
            "wiki_loves_ramadan_2025",
            "women_in_red_translation_contest_2024",
            "feminism_and_folklore_2024"
        ]
    })

# ========== FRONTEND API ROUTES ==========

# 1. Personal Cabinet - Get User Statistics
@app.route('/api/personal-cabinet/<username>', methods=['GET'])
def get_personal_cabinet(username):
    try:
        # Get user's articles across all tables
        tables = [
            'wikipedia_asian_month_2025',
            'wiki_loves_ramadan_2025',
            'women_in_red_translation_contest_2024',
            'feminism_and_folklore_2024'
        ]

        user_articles = []
        total_articles = 0
        total_points = 0
        participated_editathons = set()

        for table in tables:
            result = db.session.execute(
                db.text(f'SELECT article_title, points, jury_notes, article_added FROM {table} WHERE user_name = :username'),
                {'username': username}
            )

            for row in result:
                user_articles.append({
                    'editathon': table.replace('_', ' ').title(),
                    'table_name': table,
                    'article_title': row[0],
                    'points': row[1],
                    'jury_notes': row[2],
                    'submitted_date': row[3].isoformat() if row[3] else None,
                    'status': 'reviewed' if row[1] is not None else 'pending'
                })
                total_articles += 1
                if row[1]:
                    total_points += row[1]
                participated_editathons.add(table)

        # Mock created editathons
        created_editathons = []
        if username == 'Min968':
            created_editathons = [
                {
                    'id': 1,
                    'name': 'Wikipedia Asian Month 2025',
                    'description': 'Annual Wikipedia Asian Month editathon',
                    'status': 'finished',
                    'start_date': '2025-11-01',
                    'end_date': '2025-11-30'
                }
            ]

        return jsonify({
            'username': username,
            'stats': {
                'participated': len(participated_editathons),
                'created': len(created_editathons),
                'articles': total_articles,
                'points': total_points
            },
            'participated_editathons': [
                {
                    'id': i+1,
                    'name': editathon.replace('_', ' ').title(),
                    'description': f'Articles from {editathon}',
                    'status': 'finished',
                    'start_date': '2025-01-01',
                    'end_date': '2025-12-31'
                }
                for i, editathon in enumerate(participated_editathons)
            ],
            'created_editathons': created_editathons,
            'articles': user_articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Editathon Dashboard - Get Editathon Details
@app.route('/api/editathon/<editathon_id>', methods=['GET'])
def get_editathon_dashboard(editathon_id):
    try:
        # Map frontend IDs to actual table names
        table_mapping = {
            '1': 'wikipedia_asian_month_2025',
            '2': 'wiki_loves_ramadan_2025',
            '3': 'women_in_red_translation_contest_2024', 
            '4': 'feminism_and_folklore_2024'
        }
        
        table_name = table_mapping.get(editathon_id)
        if not table_name:
            return jsonify({"error": "Editathon not found"}), 404
        
        # Get all articles for this editathon
        result = db.session.execute(db.text(f'SELECT * FROM {table_name}'))
        
        articles = []
        users = set()
        total_articles = 0
        total_points = 0
        articles_without_marks = 0
        
        for row in result:
            article_data = {
                'id': row[0],
                'user_name': row[1],
                'article_title': row[2],
                'article_added': row[3].isoformat() if row[3] else None,
                'points': row[4],
                'jury_notes': row[5],
                'status': 'reviewed' if row[4] is not None else 'pending'
            }
            articles.append(article_data)
            users.add(row[1])
            total_articles += 1
            if row[4] is not None:
                total_points += row[4]
            else:
                articles_without_marks += 1
        
        # Calculate leaderboard
        user_stats = {}
        for article in articles:
            username = article['user_name']
            if username not in user_stats:
                user_stats[username] = {
                    'articles_count': 0,
                    'total_points': 0,
                    'articles': []
                }

            user_stats[username]['articles_count'] += 1
            if article['points'] is not None:
                user_stats[username]['total_points'] += article['points']

            # Map database fields to frontend expected fields
            article_for_frontend = {
                'id': article['id'],
                'title': article['article_title'],  # Map article_title to title
                'author': article['user_name'],     # Map user_name to author
                'addedOn': article['article_added'],
                'points': article['points'],
                'reviews': [],  # Initialize empty reviews array
                'words': 150,   # Default values
                'bytes': 2500,  # Default values
                'preview': f'Preview for {article["article_title"]}'
            }
            user_stats[username]['articles'].append(article_for_frontend)
        
        leaderboard = [
            {
                'id': i+1,
                'username': username,
                'articlesCount': stats['articles_count'],
                'totalPoints': stats['total_points'],
                'articles': stats['articles']
            }
            for i, (username, stats) in enumerate(user_stats.items())
        ]
        
        # Sort by points descending
        leaderboard.sort(key=lambda x: x['totalPoints'], reverse=True)
        
        # Get editathon info
        editathon_info = {
            '1': {
                'name': 'Wikipedia Asian Month 2025',
                'description': 'Annual Wikipedia Asian Month editathon focusing on Asian content',
                'juries': ['Narutolovehinata5', 'ZI Jony']
            },
            '2': {
                'name': 'Wiki Loves Ramadan 2025',
                'description': 'Ramadan-themed content creation contest', 
                'juries': ['ZI Jony']
            },
            '3': {
                'name': 'Women in Red Translation Contest 2024',
                'description': 'Translation contest for women-related articles',
                'juries': []
            },
            '4': {
                'name': 'Feminism and Folklore 2024',
                'description': 'Creating articles about feminism and folklore',
                'juries': ['Haoreima']
            }
        }
        
        info = editathon_info.get(editathon_id, {})
        
        # Map unreviewed articles to frontend format
        unreviewed_articles_mapped = []
        for article in articles:
            if article['points'] is None:
                unreviewed_articles_mapped.append({
                    'id': article['id'],
                    'title': article['article_title'],  # Map article_title to title
                    'author': article['user_name'],     # Map user_name to author
                    'addedOn': article['article_added'],
                    'points': article['points'],
                    'reviews': [],  # Initialize empty reviews array
                    'words': 150,   # Default values
                    'bytes': 2500,  # Default values
                    'preview': f'Preview for {article["article_title"]}'
                })

        return jsonify({
            'editathon': {
                'id': editathon_id,
                'name': info.get('name', table_name.replace('_', ' ').title()),
                'status': 'finished',
                'description': info.get('description', f'Dashboard for {table_name}')
            },
            'stats': {
                'users': len(users),
                'articles': total_articles,
                'marks': total_articles - articles_without_marks,
                'withoutMarks': articles_without_marks,
                'totalPoints': total_points
            },
            'juries': [{'id': i+1, 'username': jury} for i, jury in enumerate(info.get('juries', []))],
            'leaderboard': leaderboard,
            'unreviewed_articles': unreviewed_articles_mapped
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Get All Editathons for Homepage
@app.route('/api/editathons', methods=['GET'])
def get_all_editathons():
    try:
        # Get actual statistics from database
        tables = [
            'wikipedia_asian_month_2025',
            'wiki_loves_ramadan_2025',
            'women_in_red_translation_contest_2024',
            'feminism_and_folklore_2024'
        ]

        editathons_data = []

        for i, table in enumerate(tables):
            # Get article count for this editathon
            result = db.session.execute(db.text(f'SELECT COUNT(*) FROM {table}'))
            article_count = result.scalar()

            # Get unique user count
            result = db.session.execute(db.text(f'SELECT COUNT(DISTINCT user_name) FROM {table}'))
            user_count = result.scalar()

            # Map table names to display names and dates
            editathon_info = {
                'wikipedia_asian_month_2025': {
                    'name': 'Wikipedia Asian Month 2025',
                    'description': 'Annual Wikipedia Asian Month editathon focusing on Asian content',
                    'startDate': '2025-11-01T00:00:00',
                    'endDate': '2025-11-30T23:59:59',
                    'juries': ['Narutolovehinata5', 'ZI Jony']
                },
                'wiki_loves_ramadan_2025': {
                    'name': 'Wiki Loves Ramadan 2025',
                    'description': 'Ramadan-themed content creation contest',
                    'startDate': '2025-02-25T00:00:00',
                    'endDate': '2025-04-15T23:59:59',
                    'juries': ['ZI Jony']
                },
                'women_in_red_translation_contest_2024': {
                    'name': 'Women in Red Translation Contest 2024',
                    'description': 'Translation contest for women-related articles',
                    'startDate': '2024-07-01T00:00:00',
                    'endDate': '2024-10-01T23:59:59',
                    'juries': []
                },
                'feminism_and_folklore_2024': {
                    'name': 'Feminism and Folklore 2024',
                    'description': 'Creating articles about feminism and folklore',
                    'startDate': '2024-02-01T00:00:00',
                    'endDate': '2024-03-31T23:59:59',
                    'juries': ['Haoreima']
                }
            }

            info = editathon_info.get(table, {})

            editathons_data.append({
                'id': i + 1,
                'name': info.get('name', table.replace('_', ' ').title()),
                'description': info.get('description', f'Articles from {table}'),
                'startDate': info.get('startDate', '2024-01-01T00:00:00'),
                'endDate': info.get('endDate', '2024-12-31T23:59:59'),
                'status': 'finished',
                'article_count': article_count,
                'user_count': user_count,
                'juries': [{'id': j+1, 'username': jury} for j, jury in enumerate(info.get('juries', []))]
            })

        return jsonify(editathons_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. Submit Article to Editathon
@app.route('/api/editathon/<editathon_id>/submit', methods=['POST'])
def submit_article(editathon_id):
    try:
        data = request.json
        table_mapping = {
            '1': 'wikipedia_asian_month_2025',
            '2': 'wiki_loves_ramadan_2025',
            '3': 'women_in_red_translation_contest_2024',
            '4': 'feminism_and_folklore_2024'
        }
        
        table_name = table_mapping.get(editathon_id)
        if not table_name:
            return jsonify({"error": "Editathon not found"}), 404
        
        query = f"INSERT INTO {table_name} (user_name, article_title, article_added) VALUES (:user_name, :article_title, NOW())"
        
        db.session.execute(
            db.text(query),
            {
                'user_name': data['username'],
                'article_title': data['article_title']
            }
        )
        db.session.commit()
        
        return jsonify({
            "message": f"Article '{data['article_title']}' submitted to {table_name}", 
            "success": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 5. Judge Article - Update Points
@app.route('/api/editathon/<editathon_id>/judge', methods=['POST'])
def judge_article(editathon_id):
    try:
        data = request.json
        table_mapping = {
            '1': 'wikipedia_asian_month_2025',
            '2': 'wiki_loves_ramadan_2025', 
            '3': 'women_in_red_translation_contest_2024',
            '4': 'feminism_and_folklore_2024'
        }
        
        table_name = table_mapping.get(editathon_id)
        if not table_name:
            return jsonify({"error": "Editathon not found"}), 404
        
        query = f"UPDATE {table_name} SET points = :points, jury_notes = :jury_notes WHERE article_title = :article_title"
        
        db.session.execute(
            db.text(query),
            {
                'points': data['points'],
                'jury_notes': data['comment'],
                'article_title': data['article_title']
            }
        )
        db.session.commit()
        
        return jsonify({
            "message": f"Article '{data['article_title']}' judged with {data['points']} points",
            "success": True 
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 6. Get user statistics (existing route)
@app.route('/api/user/<username>', methods=['GET'])
def get_user_stats(username):
    try:
        # Query across all tables for this user
        tables = [
            'wikipedia_asian_month_2025',
            'wiki_loves_ramadan_2025', 
            'women_in_red_translation_contest_2024',
            'feminism_and_folklore_2024'
        ]
        
        user_data = []
        total_articles = 0
        total_points = 0
        
        for table in tables:
            result = db.session.execute(
                db.text(f'SELECT article_title, points, jury_notes FROM {table} WHERE user_name = :username'),
                {'username': username}
            )
            
            for row in result:
                user_data.append({
                    'table': table,
                    'article_title': row[0],
                    'points': row[1],
                    'jury_notes': row[2]
                })
                total_articles += 1
                if row[1]:
                    total_points += row[1]
        
        return jsonify({
            'username': username,
            'total_articles': total_articles,
            'total_points': total_points,
            'articles': user_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 7. Add new article to any table (existing route)
@app.route('/api/add_article', methods=['POST'])
def add_article():
    try:
        data = request.json
        table_name = data['table_name']
        user_name = data['user_name']
        article_title = data['article_title']
        article_added = data.get('article_added', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        points = data.get('points')
        jury_notes = data.get('jury_notes')
        
        query = f"""
        INSERT INTO {table_name} (user_name, article_title, article_added, points, jury_notes) 
        VALUES (:user_name, :article_title, :article_added, :points, :jury_notes)
        """
        
        db.session.execute(
            db.text(query),
            {
                'user_name': user_name,
                'article_title': article_title,
                'article_added': article_added,
                'points': points,
                'jury_notes': jury_notes
            }
        )
        db.session.commit()
        
        return jsonify({"message": f"Article added to {table_name}", "success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Test database connection
def test_connection():
    try:
        with app.app_context():
            tables = [
                'wikipedia_asian_month_2025',
                'wiki_loves_ramadan_2025',
                'women_in_red_translation_contest_2024',
                'feminism_and_folklore_2024'
            ]

            print("✅ Connected to MariaDB successfully!")
            for table in tables:
                result = db.session.execute(db.text(f'SELECT COUNT(*) FROM {table}'))
                count = result.scalar()
                print(f"   📊 {table}: {count} articles")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

test_connection()

if __name__ == '__main__':
    print("🚀 Backend running with Personal Cabinet & Dashboard support!")
    print("📊 Home: http://localhost:5000")
    print("👤 Personal Cabinet: http://localhost:5000/api/personal-cabinet/Min968") 
    print("📈 Editathon Dashboard: http://localhost:5000/api/editathon/1")
    print("🏠 All Editathons: http://localhost:5000/api/editathons")
    print("\n📋 Available endpoints:")
    print("   GET  /api/personal-cabinet/<username>")
    print("   GET  /api/editathons") 
    print("   GET  /api/editathon/<id>")
    print("   POST /api/editathon/<id>/submit")
    print("   POST /api/editathon/<id>/judge")
    app.run(debug=True, port=5000)