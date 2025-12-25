"""
Simplified import script for all 4 editathons
Run: python import_editathons.py
"""
from datetime import datetime, timedelta
from app import app, db, User, Project, Editathon, Article, EditathonJury, Mark, EditathonStat


EDITATHONS_DATA = [
    {
        "code": "WAM2024",
        "name": "Wikipedia Asian Month 2024",
        "start": datetime(2024, 11, 1),
        "end": datetime(2024, 11, 30),
        "jury": ["Haoreima", "MSG17", "Narutolovehinata5", "SuperHamster", "ZI Jony"],
        "articles": [
            {"title": "Mala Honnatti", "author": "Abishe", "points": 1, "jury": "ZI Jony"},
            {"title": "Geetha Kailasam", "author": "Abishe", "points": 1, "jury": "MSG17"},
            {"title": "Sean Wijesinghe", "author": "Abishe", "points": 1, "jury": "MSG17"},
            {"title": "Emma Sarepta Yule", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
            {"title": "Mary Sallom", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
            {"title": "Elise Grilli", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
        ]
    },
    {
        "code": "WAM2025",
        "name": "Wikipedia Asian Month 2025",
        "start": datetime(2025, 11, 1),
        "end": datetime(2025, 11, 30),
        "jury": ["MSG17", "Narutolovehinata5", "ZI Jony"],
        "articles": [
            {"title": "Mao Kun", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Zhang Bi (calligrapher)", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Wang Shenzhong", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Hou (title 侯)", "author": "Min968", "points": 0, "jury": "ZI Jony"},
            {"title": "Minggadari", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Fish-Scale Registers", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Three-pillar accounting system", "author": "Min968", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Ira Sukrungruang", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Frances Cha", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Farida Sulaiman", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
        ]
    },
    {
        "code": "WLR2025",
        "name": "Wiki Loves Ramadan 2025",
        "start": datetime(2025, 3, 1),
        "end": datetime(2025, 3, 31),
        "jury": ["MSG17", "Haoreima"],
        "articles": [
            {"title": "Ramadan traditions", "author": "Abishe", "points": 1, "jury": "MSG17"},
            {"title": "Islamic calendar", "author": "Min968", "points": 1, "jury": "Haoreima"},
        ]
    },
    {
        "code": "WIR2024",
        "name": "Women in Red 2024",
        "start": datetime(2024, 3, 1),
        "end": datetime(2024, 3, 31),
        "jury": ["Narutolovehinata5"],
        "articles": [
            {"title": "Female mathematician", "author": "MisawaSakura", "points": 1, "jury": "Narutolovehinata5"},
            {"title": "Historical women writer", "author": "Penny Richards", "points": 1, "jury": "Narutolovehinata5"},
        ]
    },
    {
        "code": "FAF2024",
        "name": "Feminism and Folklore 2024",
        "start": datetime(2024, 6, 1),
        "end": datetime(2024, 6, 30),
        "jury": ["SuperHamster"],
        "articles": [
            {"title": "Feminist folklore traditions", "author": "Abishe", "points": 1, "jury": "SuperHamster"},
        ]
    }
]

USERS_DATA = [
    {"username": "WikiFountainAdmin", "role": "admin", "email": "admin@wikifountain.org"},
    {"username": "Haoreima", "role": "jury", "email": "haoreima@wikifountain.org"},
    {"username": "MSG17", "role": "jury", "email": "msg17@wikifountain.org"},
    {"username": "Narutolovehinata5", "role": "jury", "email": "narutolovehinata5@wikifountain.org"},
    {"username": "SuperHamster", "role": "jury", "email": "superhamster@wikifountain.org"},
    {"username": "ZI Jony", "role": "jury", "email": "zijony@wikifountain.org"},
    {"username": "Abishe", "role": "participant", "email": "abishe@wikifountain.org"},
    {"username": "Penny Richards", "role": "participant", "email": "penny@wikifountain.org"},
    {"username": "Min968", "role": "participant", "email": "min968@wikifountain.org"},
    {"username": "MisawaSakura", "role": "participant", "email": "misawasakura@wikifountain.org"},
]


def import_all_editathons():
    """Import all 4 editathons with articles and jury marks"""
    
    with app.app_context():
        print("🚀 IMPORTING ALL EDITATHONS")
        print("=" * 60)
        
        # Create users
        print("\n👥 Creating users...")
        users_dict = {}
        for user_data in USERS_DATA:
            user = User.query.filter_by(username=user_data["username"]).first()
            if not user:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=f"imported_{user_data['username'].lower()}",
                    role=user_data["role"],
                    is_active=True
                )
                db.session.add(user)
                print(f"  ✅ {user_data['username']} ({user_data['role']})")
            users_dict[user_data["username"]] = user
        
        db.session.flush()
        
        # Create project
        print("\n🏗️ Creating project...")
        project = Project.query.filter_by(name="Wikipedia Editathons").first()
        if not project:
            project = Project(
                name="Wikipedia Editathons",
                description="Collection of Wikipedia editathons",
                created_by=users_dict["WikiFountainAdmin"].id
            )
            db.session.add(project)
            db.session.flush()
            print(f"  ✅ Wikipedia Editathons project")
        
        # Import each editathon
        total_articles = 0
        
        for editathon_data in EDITATHONS_DATA:
            code = editathon_data["code"]
            print(f"\n📅 {code}: {editathon_data['name']}")
            
            # Create editathon
            editathon = Editathon.query.filter_by(code=code).first()
            if not editathon:
                editathon = Editathon(
                    code=code,
                    name=editathon_data["name"],
                    description=f"{editathon_data['name']} - Completed editathon",
                    project_id=project.id,
                    language="en",
                    start_date=editathon_data["start"],
                    end_date=editathon_data["end"],
                    wiki_domain="en.wikipedia.org",
                    status="completed",
                    min_marks_needed=1,
                    is_published=True,
                    created_by=users_dict["WikiFountainAdmin"].id
                )
                db.session.add(editathon)
                db.session.flush()
            
            # Assign jury
            for jury_name in editathon_data["jury"]:
                existing = EditathonJury.query.filter_by(
                    editathon_id=editathon.id,
                    user_id=users_dict[jury_name].id
                ).first()
                if not existing:
                    db.session.add(EditathonJury(
                        editathon_id=editathon.id,
                        user_id=users_dict[jury_name].id,
                        role="main"
                    ))
            
            # Import articles
            article_count = 0
            total_points = 0
            participants = set()
            
            for article_data in editathon_data["articles"]:
                author = users_dict[article_data["author"]]
                article = Article(
                    editathon_id=editathon.id,
                    title=article_data["title"],
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{article_data['title'].replace(' ', '_')}",
                    submitted_by=author.id,
                    status="accepted" if article_data["points"] > 0 else "rejected",
                    points=article_data["points"],
                    notes="",
                    submitted_at=editathon_data["start"] + timedelta(days=15)
                )
                db.session.add(article)
                db.session.flush()
                
                # Add jury mark
                jury_user = users_dict[article_data["jury"]]
                mark = Mark(
                    article_id=article.id,
                    jury_id=jury_user.id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8},
                    total_score=article_data["points"],
                    comments="Accepted" if article_data["points"] > 0 else "Rejected",
                    decision="accept" if article_data["points"] > 0 else "reject",
                    marked_at=editathon_data["start"] + timedelta(days=16)
                )
                db.session.add(mark)
                
                article_count += 1
                total_points += article_data["points"]
                participants.add(article_data["author"])
                total_articles += 1
            
            # Create statistics
            stats = EditathonStat.query.get(editathon.id)
            if not stats:
                stats = EditathonStat(editathon_id=editathon.id)
                db.session.add(stats)
            
            stats.total_articles = article_count
            stats.total_participants = len(participants)
            stats.total_points = total_points
            stats.avg_score = total_points / article_count if article_count > 0 else 0
            
            print(f"  ✅ Articles: {article_count} | Points: {total_points} | Participants: {len(participants)}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print(f"🎉 COMPLETE! Imported {total_articles} articles across 5 editathons")
        print("=" * 60)


if __name__ == "__main__":
    import_all_editathons()
