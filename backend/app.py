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
        # First, try to fetch editathon metadata (for user-created editathons)
        editathon_meta = None
        wiki_language = 'en'  # Default fallback
        
        try:
            meta_result = db.session.execute(
                db.text("SELECT * FROM editathon_metadata WHERE id = :id"),
                {'id': editathon_id}
            )
            meta_row = meta_result.fetchone()
            if meta_row:
                editathon_meta = meta_row
                wiki_language = meta_row.wiki_language or 'en'
        except:
            pass  # Continue with demo data if metadata table not available
        
        # Map frontend IDs to actual table names (for demo editathons)
        table_mapping = {
            '1': 'wikipedia_asian_month_2025',
            '2': 'wiki_loves_ramadan_2025',
            '3': 'women_in_red_translation_contest_2024', 
            '4': 'feminism_and_folklore_2024'
        }
        
        table_name = table_mapping.get(editathon_id)
        if not table_name and not editathon_meta:
            return jsonify({"error": "Editathon not found"}), 404
        
        # Get all articles for this editathon
        if table_name:
            result = db.session.execute(db.text(f'SELECT * FROM {table_name}'))
        else:
            # For user-created editathons without demo data, return empty articles
            result = []
        
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

            # Parse jury_notes to build reviews array
            reviews = []
            if article['jury_notes']:
                # Format: "Reviewer_Name|decision|points|comment"
                parts = article['jury_notes'].split('|', 3)
                if len(parts) >= 3:
                    reviews.append({
                        'juror': parts[0],
                        'decision': parts[1],
                        'points': int(parts[2]) if parts[2].isdigit() else 0,
                        'comment': parts[3] if len(parts) > 3 else ''
                    })

            # Map database fields to frontend expected fields
            article_for_frontend = {
                'id': article['id'],
                'title': article['article_title'],  # Map article_title to title
                'author': article['user_name'],     # Map user_name to author
                'addedOn': article['article_added'],
                'points': article['points'],
                'reviews': reviews,  # Populate from jury_notes
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
                'name': info.get('name', table_name.replace('_', ' ').title() if table_name else 'Editathon'),
                'status': 'finished',
                'description': info.get('description', f'Dashboard for {table_name}' if table_name else 'Editathon'),
                'wiki_language': wiki_language  # Include wiki_language in response
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

        # Also fetch approved editathons from metadata table
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS editathon_metadata (
                id INT PRIMARY KEY AUTO_INCREMENT,
                title VARCHAR(255) NOT NULL,
                code VARCHAR(100) UNIQUE,
                project VARCHAR(255),
                wiki_language VARCHAR(10),
                description TEXT,
                namespace VARCHAR(50),
                minSize INT,
                maxSize INT,
                startDate DATETIME,
                endDate DATETIME,
                createdBy VARCHAR(255),
                submissionDate DATE,
                consensualVote BOOLEAN,
                hiddenMarks BOOLEAN,
                creatorSubmit BOOLEAN,
                showInJury BOOLEAN,
                status VARCHAR(50),
                rules LONGTEXT,
                marks LONGTEXT,
                jury LONGTEXT,
                template LONGTEXT,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            db.session.execute(db.text(create_table_query))
            db.session.commit()
            
            # Get approved editathons
            result = db.session.execute(
                db.text("SELECT * FROM editathon_metadata WHERE status = 'active' ORDER BY startDate DESC")
            )
            
            for row in result:
                editathons_data.append({
                    'id': row.id,
                    'name': row.title,
                    'description': row.description,
                    'startDate': row.startDate.isoformat() if row.startDate else None,
                    'endDate': row.endDate.isoformat() if row.endDate else None,
                    'status': 'ongoing',
                    'article_count': 0,
                    'user_count': 0,
                    'juries': []
                })
        except Exception as e:
            print(f"Warning: Could not fetch metadata editathons: {e}")

        return jsonify(editathons_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        
        # Store reviewer name and decision in jury_notes
        reviewer_name = data.get('reviewer', 'Unknown')
        decision = data.get('decision', 'accepted')
        points = data.get('points', 0)
        
        # Format jury notes: "Reviewer_Name|decision|points|comment"
        jury_note = f"{reviewer_name}|{decision}|{points}|{data.get('comment', '')}"
        
        query = f"UPDATE {table_name} SET points = :points, jury_notes = :jury_notes WHERE article_title = :article_title"
        
        db.session.execute(
            db.text(query),
            {
                'points': points,
                'jury_notes': jury_note,
                'article_title': data['article_title']
            }
        )
        db.session.commit()
        
        return jsonify({
            "message": f"Article '{data['article_title']}' judged with {points} points",
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

# 8. Create New Editathon
@app.route('/api/editathons/create', methods=['POST'])
def create_new_editathon():
    try:
        data = request.json
        
        # Extract editathon data
        editathon_data = {
            'title': data.get('title'),
            'code': data.get('code'),
            'project': data.get('project'),
            'wiki_language': data.get('wiki_language'),
            'description': data.get('description'),
            'namespace': data.get('namespace'),
            'minSize': data.get('minSize', 0),
            'maxSize': data.get('maxSize', 10000),
            'startDate': data.get('startDate'),
            'endDate': data.get('endDate'),
            'createdBy': data.get('createdBy'),
            'submissionDate': data.get('submissionDate'),
            'consensualVote': data.get('consensualVote', False),
            'hiddenMarks': data.get('hiddenMarks', False),
            'creatorSubmit': data.get('creatorSubmit', False),
            'showInJury': data.get('showInJury', False),
            'status': data.get('status', 'pending'),
            'rules': str(data.get('rules', [])),  # Store as JSON string
            'marks': str(data.get('marks', [])),  # Store as JSON string
            'jury': str(data.get('jury', [])),    # Store as JSON string
            'template': str(data.get('template', {}))  # Store as JSON string
        }
        
        # Create editathon metadata table (if not exists)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS editathon_metadata (
            id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            code VARCHAR(100) UNIQUE,
            project VARCHAR(255),
            wiki_language VARCHAR(10),
            description TEXT,
            namespace VARCHAR(50),
            minSize INT,
            maxSize INT,
            startDate DATETIME,
            endDate DATETIME,
            createdBy VARCHAR(255),
            submissionDate DATE,
            consensualVote BOOLEAN,
            hiddenMarks BOOLEAN,
            creatorSubmit BOOLEAN,
            showInJury BOOLEAN,
            status VARCHAR(50),
            rules LONGTEXT,
            marks LONGTEXT,
            jury LONGTEXT,
            template LONGTEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        db.session.execute(db.text(create_table_query))
        db.session.commit()
        
        # Insert editathon data
        insert_query = """
        INSERT INTO editathon_metadata 
        (title, code, project, wiki_language, description, namespace, minSize, maxSize, 
         startDate, endDate, createdBy, submissionDate, consensualVote, hiddenMarks, 
         creatorSubmit, showInJury, status, rules, marks, jury, template)
        VALUES 
        (:title, :code, :project, :wiki_language, :description, :namespace, :minSize, :maxSize,
         :startDate, :endDate, :createdBy, :submissionDate, :consensualVote, :hiddenMarks,
         :creatorSubmit, :showInJury, :status, :rules, :marks, :jury, :template)
        """
        
        db.session.execute(db.text(insert_query), editathon_data)
        db.session.commit()
        
        # Get the inserted ID
        result = db.session.execute(db.text("SELECT LAST_INSERT_ID()"))
        editathon_id = result.scalar()
        
        return jsonify({
            "success": True,
            "message": "Editathon created successfully and pending approval",
            "id": editathon_id,
            "status": "pending"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 9. Get Pending Editathons for Approval
@app.route('/api/editathons/pending', methods=['GET'])
def get_pending_editathons():
    try:
        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS editathon_metadata (
            id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            code VARCHAR(100) UNIQUE,
            project VARCHAR(255),
            wiki_language VARCHAR(10),
            description TEXT,
            namespace VARCHAR(50),
            minSize INT,
            maxSize INT,
            startDate DATETIME,
            endDate DATETIME,
            createdBy VARCHAR(255),
            submissionDate DATE,
            consensualVote BOOLEAN,
            hiddenMarks BOOLEAN,
            creatorSubmit BOOLEAN,
            showInJury BOOLEAN,
            status VARCHAR(50),
            rules LONGTEXT,
            marks LONGTEXT,
            jury LONGTEXT,
            template LONGTEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.session.execute(db.text(create_table_query))
        db.session.commit()
        
        # Get pending editathons
        result = db.session.execute(
            db.text("SELECT * FROM editathon_metadata WHERE status = 'pending' ORDER BY createdAt DESC")
        )
        
        pending_editathons = []
        for row in result:
            pending_editathons.append({
                'id': row.id,
                'title': row.title,
                'code': row.code,
                'project': row.project,
                'wiki_language': row.wiki_language,
                'description': row.description,
                'namespace': row.namespace,
                'minSize': row.minSize,
                'maxSize': row.maxSize,
                'startDate': row.startDate.isoformat() if row.startDate else None,
                'endDate': row.endDate.isoformat() if row.endDate else None,
                'createdBy': row.createdBy,
                'submissionDate': row.submissionDate.isoformat() if row.submissionDate else None,
                'status': row.status
            })
        
        return jsonify({
            "success": True,
            "editathons": pending_editathons,
            "count": len(pending_editathons)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 10. Approve Editathon
@app.route('/api/editathon/<editathon_id>/approve', methods=['POST'])
def approve_editathon(editathon_id):
    try:
        db.session.execute(
            db.text("UPDATE editathon_metadata SET status = 'active' WHERE id = :id"),
            {'id': editathon_id}
        )
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Editathon approved successfully",
            "status": "active"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 11. Reject Editathon
@app.route('/api/editathon/<editathon_id>/reject', methods=['POST'])
def reject_editathon(editathon_id):
    try:
        data = request.json
        reason = data.get('reason', 'No reason provided') if data else 'No reason provided'
        
        db.session.execute(
            db.text("UPDATE editathon_metadata SET status = 'rejected' WHERE id = :id"),
            {'id': editathon_id}
        )
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Editathon rejected. Reason: {reason}",
            "status": "rejected"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 12. Get User's Pending Editathons
@app.route('/api/user/<username>/pending-editathons', methods=['GET'])
def get_user_pending_editathons(username):
    try:
        # Get pending editathons created by this user
        result = db.session.execute(
            db.text("SELECT * FROM editathon_metadata WHERE createdBy = :username AND status = 'pending' ORDER BY createdAt DESC"),
            {'username': username}
        )
        
        pending_editathons = []
        for row in result:
            pending_editathons.append({
                'id': row.id,
                'title': row.title,
                'code': row.code,
                'project': row.project,
                'wiki_language': row.wiki_language,
                'description': row.description,
                'namespace': row.namespace,
                'minSize': row.minSize,
                'maxSize': row.maxSize,
                'startDate': row.startDate.isoformat() if row.startDate else None,
                'endDate': row.endDate.isoformat() if row.endDate else None,
                'createdBy': row.createdBy,
                'submissionDate': row.submissionDate.isoformat() if row.submissionDate else None,
                'status': row.status,
                'rules': row.rules,
                'marks': row.marks,
                'jury': row.jury,
                'template': row.template
            })
        
        return jsonify(pending_editathons)
        
    except Exception as e:
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
    print("   GET  /api/editathons/pending")
    print("   GET  /api/user/<username>/pending-editathons")
    print("   POST /api/editathon/<id>/submit")
    print("   POST /api/editathon/<id>/judge")
    print("   POST /api/editathons/create")
    print("   POST /api/editathon/<id>/approve")
    print("   POST /api/editathon/<id>/reject")
    app.run(debug=True, port=5000)