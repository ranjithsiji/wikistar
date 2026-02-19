from flask import Blueprint, jsonify, send_from_directory, current_app
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return send_from_directory(current_app.static_folder, 'index.html')

@main_bp.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists(current_app.static_folder + '/' + path):
        return send_from_directory(current_app.static_folder, path)
    else:
        return send_from_directory(current_app.static_folder, 'index.html')

@main_bp.route('/api/status')
def api_status():
    return jsonify({
        "message": "✅ Editathon Backend Connected to MariaDB (WikiFountain Schema)",
        "status": "success",
        "database": "wikifountain",
        "schema_version": "2.0",
        "tables": [
            "users",
            "projects",
            "editathons",
            "articles",
            "editathon_jury",
            "marks",
            "rules",
            "editathon_rules",
            "audit_logs",
            "editathon_stats"
        ]
    })
