from flask import Blueprint, jsonify, send_from_directory, current_app
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/', defaults={'path': ''})
@main_bp.route('/<path:path>')
def serve_spa(path):
    """
    Serve the Vue SPA.
    - Real static files (JS, CSS, images, etc.) are served directly.
    - Any URL that is NOT a real file AND NOT an API route returns index.html
      so Vue Router handles client-side navigation.
    """
    # Let API blueprints handle their own 404s
    if path.startswith('api/'):
        return jsonify({"error": "API route not found"}), 404

    static_dir = current_app.static_folder  # frontend/dist
    full_path = os.path.join(static_dir, path)

    # Serve the real file if it physically exists (JS, CSS, images, fonts, etc.)
    if path and os.path.isfile(full_path):
        return send_from_directory(static_dir, path)

    # Fall back to Vue SPA entry point for ALL other paths
    return send_from_directory(static_dir, 'index.html')


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
