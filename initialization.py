from datetime import datetime, timedelta
from extensions import db
from models import User, Project, Editathon, EditathonJury, Article, Mark, EditathonStat

def create_tables(app):
    try:
        with app.app_context():
            db.create_all()
            print("✅ Tables created/verified successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

def auto_import_data(app):
    """Auto-import all finished editathons from sample data if database is empty."""
    try:
      with app.app_context():
        # Check if data already exists
        if Editathon.query.count() > 0:
            print("ℹ️ Database already has editathons, skipping auto-import")
            return
    except Exception as e:
        print(f"⚠️ auto_import_data skipped — DB not ready: {e}")
        return
    with app.app_context():
        
        print("📥 Auto-importing finished editathons...")
        try:
            # ========== 1. CREATE ALL USERS ==========
            users_to_create = [
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
                {"username": "Nicholas0", "role": "participant", "email": "nicholas0@wikifountain.org"},
                {"username": "SDGB1217", "role": "participant", "email": "sdgb1217@wikifountain.org"},
                {"username": "Spiderpig662", "role": "participant", "email": "spiderpig@wikifountain.org"},
                {"username": "Alperen", "role": "participant", "email": "alperen@wikifountain.org"},
            ]
            
            users_dict = {}
            for user_data in users_to_create:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=f"imported_{user_data['username'].lower()}",
                    role=user_data["role"],
                    is_active=True
                )
                db.session.add(user)
                users_dict[user_data["username"]] = user
            db.session.flush()
            
            # ========== 2. CREATE PROJECT ==========
            organizer = users_dict["WikiFountainAdmin"]
            project = Project(
                name="Wikipedia Asian Month",
                description="Annual Wikipedia Asian Month editathon focusing on Asian content",
                created_by=organizer.id
            )
            db.session.add(project)
            db.session.flush()
            
            # ========== 3. IMPORT WAM 2024 ==========
            wam2024 = Editathon(
                code="WAM2024", name="Wikipedia Asian Month 2024",
                description="Wikipedia Asian Month 2024 - Completed editathon",
                project_id=project.id, language="en",
                start_date=datetime(2024, 11, 1), end_date=datetime(2024, 11, 30),
                wiki_domain="en.wikipedia.org", status="completed", min_marks_needed=1,
                is_published=True, created_by=organizer.id
            )
            db.session.add(wam2024); db.session.flush()
            
            for jury_name in ["Haoreima", "MSG17", "Narutolovehinata5", "SuperHamster", "ZI Jony"]:
                db.session.add(EditathonJury(editathon_id=wam2024.id, user_id=users_dict[jury_name].id, role="main"))
            
            wam2024_articles = [
                {"title": "Mala Honnatti", "author": "Abishe", "points": 1, "jury": "ZI Jony"},
                {"title": "Geetha Kailasam", "author": "Abishe", "points": 1, "jury": "MSG17"},
                {"title": "Sean Wijesinghe", "author": "Abishe", "points": 1, "jury": "MSG17"},
                {"title": "Emma Sarepta Yule", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
                {"title": "Mary Sallom", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
                {"title": "Elise Grilli", "author": "Penny Richards", "points": 1, "jury": "MSG17"},
            ]
            
            for art_data in wam2024_articles:
                article = Article(
                    editathon_id=wam2024.id, title=art_data["title"],
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{art_data['title'].replace(' ', '_')}",
                    submitted_by=users_dict[art_data["author"]].id, status="accepted",
                    points=art_data["points"], submitted_at=datetime(2024, 11, 30, 12, 0)
                )
                db.session.add(article); db.session.flush()
                db.session.add(Mark(
                    article_id=article.id, jury_id=users_dict[art_data["jury"]].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8}, total_score=art_data["points"],
                    comments="Accepted", decision="accept", marked_at=datetime(2024, 11, 30, 13, 0)
                ))
            
            db.session.add(EditathonStat(
                editathon_id=wam2024.id, total_articles=len(wam2024_articles), total_participants=2,
                total_points=sum(a["points"] for a in wam2024_articles),
                avg_score=sum(a["points"] for a in wam2024_articles) / len(wam2024_articles)
            ))
            
            # ========== 4. IMPORT WAM 2025 ==========
            wam2025 = Editathon(
                code="WAM2025", name="Wikipedia Asian Month 2025",
                description="Wikipedia Asian Month 2025 - Completed editathon",
                project_id=project.id, language="en",
                start_date=datetime(2025, 11, 1), end_date=datetime(2025, 11, 30),
                wiki_domain="en.wikipedia.org", status="completed", min_marks_needed=1,
                is_published=True, created_by=organizer.id
            )
            db.session.add(wam2025); db.session.flush()
            
            for jury_name in ["MSG17", "Narutolovehinata5", "ZI Jony"]:
                db.session.add(EditathonJury(editathon_id=wam2025.id, user_id=users_dict[jury_name].id, role="main"))
            
            wam2025_articles = [
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
            
            for art_data in wam2025_articles:
                article = Article(
                    editathon_id=wam2025.id, title=art_data["title"],
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{art_data['title'].replace(' ', '_')}",
                    submitted_by=users_dict[art_data["author"]].id,
                    status="accepted" if art_data["points"] > 0 else "rejected",
                    points=art_data["points"], submitted_at=datetime(2025, 11, 30, 12, 0)
                )
                db.session.add(article); db.session.flush()
                db.session.add(Mark(
                    article_id=article.id, jury_id=users_dict[art_data["jury"]].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8}, total_score=art_data["points"],
                    comments="Accepted" if art_data["points"] > 0 else "Rejected",
                    decision="accept" if art_data["points"] > 0 else "reject",
                    marked_at=datetime(2025, 11, 30, 13, 0)
                ))
            
            db.session.add(EditathonStat(
                editathon_id=wam2025.id, total_articles=len(wam2025_articles), total_participants=2,
                total_points=sum(a["points"] for a in wam2025_articles),
                avg_score=sum(a["points"] for a in wam2025_articles) / len(wam2025_articles)
            ))
            
            # ========== 5. IMPORT WLR 2025 ==========
            wlr2025 = Editathon(
                code="WLR2025", name="Wiki Loves Ramadan 2025",
                description="Wiki Loves Ramadan 2025 - Completed editathon",
                project_id=project.id, language="en",
                start_date=datetime(2025, 2, 25), end_date=datetime(2025, 4, 15),
                wiki_domain="en.wikipedia.org", status="completed", is_published=True,
                created_by=organizer.id
            )
            db.session.add(wlr2025); db.session.flush()
            db.session.add(EditathonJury(editathon_id=wlr2025.id, user_id=users_dict["ZI Jony"].id, role="main"))
            
            wlr_articles = [
                ('Min968', 'Ramadan traditions in Muslim countries', 88),
                ('ZI Jony', 'Islamic calligraphy during Ramadan', 92),
                ('MisawaSakura', 'Ramadan food traditions', 85),
                ('Nicholas0', 'Mosque architecture and Ramadan', 87),
                ('SDGB1217', 'Ramadan charity and community service', 90),
            ]
            for author_name, title, points in wlr_articles:
                article = Article(
                    editathon_id=wlr2025.id, title=title,
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    submitted_by=users_dict[author_name].id, status='accepted', points=points,
                    submitted_at=datetime(2025, 3, 1)
                )
                db.session.add(article); db.session.flush()
                db.session.add(Mark(
                    article_id=article.id, jury_id=users_dict["ZI Jony"].id,
                    criteria_scores={"quality": 8, "sources": 7, "coverage": 8}, total_score=points,
                    decision="accept", marked_at=datetime(2025, 3, 2)
                ))
            
            # ========== 6. IMPORT WIR 2024 ==========
            wir2024 = Editathon(
                code="WIR2024", name="Women in Red Translation Contest 2024",
                description="Women in Red 2024 - Completed editathon",
                project_id=project.id, language="en",
                start_date=datetime(2024, 7, 1), end_date=datetime(2024, 10, 1),
                wiki_domain="en.wikipedia.org", status="completed", is_published=True,
                created_by=users_dict["Spiderpig662"].id
            )
            db.session.add(wir2024); db.session.flush()
            
            wir_articles = [
                ('Min968', 'Marie Curie biography (translated)', 90),
                ('MisawaSakura', 'Malala Yousafzai story (translated)', 88),
            ]
            for author_name, title, points in wir_articles:
                article = Article(
                    editathon_id=wir2024.id, title=title,
                    wikipedia_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    submitted_by=users_dict[author_name].id, status='accepted', points=points,
                    submitted_at=datetime(2024, 7, 15)
                )
                db.session.add(article); db.session.flush()

            # ========== 7. IMPORT FAF 2024 ==========
            faf2024 = Editathon(
                code="FAF2024", name="Feminism and Folklore 2024",
                description="Feminism and Folklore 2024 - Completed editathon",
                project_id=project.id, language="en",
                start_date=datetime(2024, 2, 1), end_date=datetime(2024, 3, 31),
                wiki_domain="en.wikipedia.org", status="completed", is_published=True,
                created_by=users_dict["Alperen"].id
            )
            db.session.add(faf2024); db.session.flush()
            db.session.add(EditathonJury(editathon_id=faf2024.id, user_id=users_dict["Haoreima"].id, role="main"))
            
            article = Article(
                editathon_id=faf2024.id, title='Feminist themes in Japanese folklore',
                wikipedia_url="https://en.wikipedia.org/wiki/Feminist_themes_in_Japanese_folklore",
                submitted_by=users_dict["Alperen"].id, status='accepted', points=92,
                submitted_at=datetime(2024, 3, 29)
            )
            db.session.add(article); db.session.flush()
            db.session.add(Mark(
                article_id=article.id, jury_id=users_dict["Haoreima"].id,
                criteria_scores={"quality": 9, "sources": 8, "coverage": 9}, total_score=92,
                decision="accept", marked_at=datetime(2024, 3, 30)
            ))
            
            db.session.commit()
            print("✅ Auto-import completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Auto-import failed: {e}")

def test_connection(app):
    try:
        with app.app_context():
            from models import User
            user_count = User.query.count()
            print("✅ Connected to Database successfully!")
            print(f"   📊 Users in database: {user_count}")
    except Exception as e:
        print(f"⚠️ Database not reachable at startup (will retry on first request): {e}")
