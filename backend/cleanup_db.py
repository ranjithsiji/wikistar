import sys
sys.path.insert(0, '.')
from app import app, db, User, Editathon, Article, Mark, EditathonJury, Project, Rule, EditathonRule, EditathonStat, AuditLog

with app.app_context():
    # Clear all tables in correct order (foreign keys first)
    tables = [
        (Mark, 'marks'),
        (AuditLog, 'audit_logs'),
        (EditathonRule, 'editathon_rules'),
        (EditathonJury, 'editathon_jury'),
        (EditathonStat, 'editathon_stats'),
        (Article, 'articles'),
        (Rule, 'rules'),
        (Editathon, 'editathons'),
        (Project, 'projects'),
        (User, 'users'),
    ]
    
    for table_class, table_name in tables:
        count = table_class.query.count()
        if count > 0:
            table_class.query.delete()
            print(f"✅ Cleared {count} {table_name} records")
    
    db.session.commit()
    print("\n✅ Database cleared successfully!")
    print(f"Users: {User.query.count()}")
    print(f"Editathons: {Editathon.query.count()}")
    print(f"Articles: {Article.query.count()}")
