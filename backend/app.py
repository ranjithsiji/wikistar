from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql

app = Flask(__name__)

# MariaDB connection - using your exact password
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maria123@localhost:3306/wikipedia_editathons'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Routes for your EXISTING tables
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

# Get all data from wikipedia_asian_month_2025
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

# Get all data from wiki_loves_ramadan_2025
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

# Get all data from women_in_red_translation_contest_2024
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

# Get all data from feminism_and_folklore_2024
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

# Get user statistics
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

# Add new article to any table
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
            # Test connection by counting records in each table
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
    print("🚀 Backend running with your EXISTING MariaDB tables!")
    print("📊 Home: http://localhost:5000")
    print("🏆 Wikipedia Asian Month: http://localhost:5000/api/wikipedia_asian_month_2025")
    print("🌙 Wiki Loves Ramadan: http://localhost:5000/api/wiki_loves_ramadan_2025")
    print("👩 Women in Red: http://localhost:5000/api/women_in_red_2024")
    print("📚 Feminism & Folklore: http://localhost:5000/api/feminism_folklore_2024")
    print("👤 User stats: http://localhost:5000/api/user/Min968")
    app.run(debug=True, port=5000)