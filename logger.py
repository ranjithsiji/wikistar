from extensions import db
from models import AuditLog
from flask import request

def log_activity(user_id, action, entity_type=None, entity_id=None, details=None):
    try:
        ip_addr = request.remote_addr if request else None
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to log activity: {str(e)}")
