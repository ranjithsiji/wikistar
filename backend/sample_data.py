from app import create_app
from database import db
from models import Editathon, Article, User, Mark
from datetime import datetime

app = create_app()

def insert_sample_data():
    with app.app_context():
        try:
            # --- Users ---
            users = [
                User(username='Min968', role='participant'),
                User(username='MisawaSakura', role='participant'),
                User(username='Nicholas0', role='participant'),
                User(username='SDGB1217', role='participant'),
                User(username='Ainty Painty', role='participant'),
                User(username='Spiderpig662', role='participant'),
                User(username='MumphingSquirrel', role='participant'),
                User(username='Alperen', role='participant'),
                User(username='Narutolovehinata5', role='judge'),
                User(username='ZI Jony', role='judge'),
                User(username='Haoreima', role='judge')
            ]
            
            # Add users if they don't exist
            for user in users:
                existing = User.query.filter_by(username=user.username).first()
                if not existing:
                    db.session.add(user)
            
            db.session.commit()
            
            # Get user IDs
            user_map = {u.username: u.id for u in User.query.all()}
            print(f"✅ Created/Found {len(user_map)} users")

            # --- Wikipedia Asian Month 2025 ---
            wam = Editathon.query.filter_by(name='Wikipedia Asian Month 2025').first()
            if not wam:
                wam = Editathon(
                    name='Wikipedia Asian Month 2025', 
                    status='finished',
                    start_date=datetime(2025, 11, 1), 
                    end_date=datetime(2025, 11, 30),
                    created_by=user_map['Min968']
                )
                db.session.add(wam)
                db.session.commit()
                print("✅ Created Wikipedia Asian Month 2025")

            # Articles for WAM
            wam_articles_data = [
                # Min968
                {'user': 'Min968', 'title': 'Four-leg bookkeeping', 'date': (2025,11,26,2,10), 'points': 25, 'notes': 'Narutolovehinata5: 1+1 accepted'},
                {'user': 'Min968', 'title': 'Four-pillar accounting system', 'date': (2025,11,25,21,47), 'points': None, 'notes': None},
                {'user': 'Min968', 'title': 'Three-leg bookkeeping', 'date': (2025,11,25,5,35), 'points': None, 'notes': None},
                {'user': 'Min968', 'title': 'Dragon Gate bookkeeping', 'date': (2025,11,24,10,31), 'points': None, 'notes': None},
                {'user': 'Min968', 'title': 'Twice taxation system', 'date': (2025,11,20,17,4), 'points': 1, 'notes': 'Narutolovehinata5: 1+1 accepted'},
                
                # MisawaSakura
                {'user': 'MisawaSakura', 'title': 'Kyoko Yonemoto', 'date': (2025,11,25,1,47), 'points': None, 'notes': None},
                {'user': 'MisawaSakura', 'title': 'Ahn Myeong Chul', 'date': (2025,11,24,20,5), 'points': None, 'notes': None},
                {'user': 'MisawaSakura', 'title': 'Ko Yong Suk', 'date': (2025,11,24,4,13), 'points': None, 'notes': None},
                
                # Nicholas0
                {'user': 'Nicholas0', 'title': 'Blazing Fists', 'date': (2025,11,26,3,19), 'points': None, 'notes': None},
                {'user': 'Nicholas0', 'title': 'Wonder Seven', 'date': (2025,11,5,1,2), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted; Narutolovehinata5: 1+1 accepted'},
                {'user': 'Nicholas0', 'title': 'Horror Hotline... Big Head Monster', 'date': (2025,11,1,3,56), 'points': 1, 'notes': 'Narutolovehinata5: 1+1 accepted'},
                {'user': 'Nicholas0', 'title': 'Spy with My Face', 'date': (2025,11,1,2,57), 'points': 1, 'notes': 'Narutolovehinata5: 1+1 accepted'},
            ]

            for article_data in wam_articles_data:
                existing = Article.query.filter_by(title=article_data['title'], editathon_id=wam.id).first()
                if not existing:
                    article = Article(
                        user_id=user_map[article_data['user']],
                        editathon_id=wam.id,
                        title=article_data['title'],
                        article_added=datetime(*article_data['date']),
                        points=article_data['points'],
                        jury_notes=article_data['notes']
                    )
                    db.session.add(article)
            
            db.session.commit()
            print(f"✅ Added {len(wam_articles_data)} articles for Wikipedia Asian Month")

            # --- Wiki Loves Ramadan 2025 ---
            wlr = Editathon.query.filter_by(name='Wiki Loves Ramadan 2025').first()
            if not wlr:
                wlr = Editathon(
                    name='Wiki Loves Ramadan 2025', 
                    status='finished',
                    start_date=datetime(2025, 2, 25), 
                    end_date=datetime(2025, 4, 15),
                    created_by=user_map['SDGB1217']
                )
                db.session.add(wlr)
                db.session.commit()
                print("✅ Created Wiki Loves Ramadan 2025")

            # Articles for WLR
            wlr_articles_data = [
                # SDGB1217
                {'user': 'SDGB1217', 'title': 'Elham Youssefian', 'date': (2025,4,14,14,22), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'SDGB1217', 'title': 'Asia Tawfiq Wahbi', 'date': (2025,4,14,13,58), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'SDGB1217', 'title': 'Hinda Abdi Mohamoud', 'date': (2025,4,14,13,45), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'SDGB1217', 'title': 'Shamaa Mohammed', 'date': (2025,4,14,13,33), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'SDGB1217', 'title': 'Souad Kassim Mohamed', 'date': (2025,4,14,13,26), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                
                # Ainty Painty
                {'user': 'Ainty Painty', 'title': 'Ramadan in Indonesia', 'date': (2025,4,15,3,27), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'Ainty Painty', 'title': 'Ramadan in Australia', 'date': (2025,4,14,14,51), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'Ainty Painty', 'title': 'Ramadan in Canada', 'date': (2025,4,14,4,19), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'Ainty Painty', 'title': 'Ramadan in Afghanistan', 'date': (2025,4,13,17,18), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
                {'user': 'Ainty Painty', 'title': 'Ramadan in Maldives', 'date': (2025,4,13,16,13), 'points': 1, 'notes': 'ZI Jony: 1+1 accepted'},
            ]

            for article_data in wlr_articles_data:
                existing = Article.query.filter_by(title=article_data['title'], editathon_id=wlr.id).first()
                if not existing:
                    article = Article(
                        user_id=user_map[article_data['user']],
                        editathon_id=wlr.id,
                        title=article_data['title'],
                        article_added=datetime(*article_data['date']),
                        points=article_data['points'],
                        jury_notes=article_data['notes']
                    )
                    db.session.add(article)
            
            db.session.commit()
            print(f"✅ Added {len(wlr_articles_data)} articles for Wiki Loves Ramadan")

            # --- Women in Red 2024 ---
            wir = Editathon.query.filter_by(name='Women in Red Translation Contest 2024').first()
            if not wir:
                wir = Editathon(
                    name='Women in Red Translation Contest 2024', 
                    status='finished',
                    start_date=datetime(2024, 7, 1), 
                    end_date=datetime(2024, 10, 1),
                    created_by=user_map['Spiderpig662']
                )
                db.session.add(wir)
                db.session.commit()
                print("✅ Created Women in Red 2024")

            # Articles for Women in Red
            wir_articles_data = [
                {'user': 'Spiderpig662', 'title': 'Ulrikke Dahl', 'date': (2024,9,30,22,56), 'points': None, 'notes': None},
                {'user': 'MumphingSquirrel', 'title': 'Laure Hayman', 'date': (2024,9,29,19,36), 'points': None, 'notes': None},
            ]

            for article_data in wir_articles_data:
                existing = Article.query.filter_by(title=article_data['title'], editathon_id=wir.id).first()
                if not existing:
                    article = Article(
                        user_id=user_map[article_data['user']],
                        editathon_id=wir.id,
                        title=article_data['title'],
                        article_added=datetime(*article_data['date']),
                        points=article_data['points'],
                        jury_notes=article_data['notes']
                    )
                    db.session.add(article)
            
            db.session.commit()
            print(f"✅ Added {len(wir_articles_data)} articles for Women in Red")

            # --- Feminism and Folklore 2024 ---
            faf = Editathon.query.filter_by(name='Feminism and Folklore 2024').first()
            if not faf:
                faf = Editathon(
                    name='Feminism and Folklore 2024', 
                    status='finished',
                    start_date=datetime(2024, 2, 1), 
                    end_date=datetime(2024, 3, 31),
                    created_by=user_map['Alperen']
                )
                db.session.add(faf)
                db.session.commit()
                print("✅ Created Feminism and Folklore 2024")

            # Articles for Feminism and Folklore
            faf_articles_data = [
                {'user': 'Alperen', 'title': 'Marianne Wellershoff', 'date': (2024,3,29,17,22), 'points': 0, 'notes': 'Haoreima: 0not accepted'},
            ]

            for article_data in faf_articles_data:
                existing = Article.query.filter_by(title=article_data['title'], editathon_id=faf.id).first()
                if not existing:
                    article = Article(
                        user_id=user_map[article_data['user']],
                        editathon_id=faf.id,
                        title=article_data['title'],
                        article_added=datetime(*article_data['date']),
                        points=article_data['points'],
                        jury_notes=article_data['notes']
                    )
                    db.session.add(article)
            
            db.session.commit()
            print(f"✅ Added {len(faf_articles_data)} articles for Feminism and Folklore")

            print("\n🎉 All sample data inserted successfully!")
            print("📊 Summary:")
            print(f"   - Users: {User.query.count()}")
            print(f"   - Editathons: {Editathon.query.count()}")
            print(f"   - Articles: {Article.query.count()}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    insert_sample_data()