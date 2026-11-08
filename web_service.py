import os
import sqlite3
import uuid
from flask import Flask, request, jsonify, g, send_from_directory

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "videos.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL;")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                video_url TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        db.commit()

init_db()

def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name).strip("_") or "video"

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files or 'company_name' not in request.form:
        return jsonify({"error": "Missing file or company_name"}), 400

    file = request.files['file']
    company_name = request.form['company_name']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    ext = os.path.splitext(file.filename)[1] or '.webm'
    safe_name = _safe_filename(company_name) + ext
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(file_path)

    video_url = request.host_url.rstrip('/') + '/media/' + safe_name

    db = get_db()
    cur = db.execute("SELECT id FROM videos WHERE company_name = ?", (company_name,))
    row = cur.fetchone()

    if row:
        db.execute(
            "UPDATE videos SET file_path = ?, video_url = ?, updated_at = datetime('now') WHERE company_name = ?",
            (file_path, video_url, company_name)
        )
    else:
        db.execute(
            "INSERT INTO videos (company_name, file_path, video_url) VALUES (?, ?, ?)",
            (company_name, file_path, video_url)
        )
    db.commit()

    return jsonify({"company_name": company_name, "video_url": video_url}), 200

@app.route('/get_video_url', methods=['GET'])
def get_video_url():
    company_name = request.args.get('company_name')
    if not company_name:
        return jsonify({"error": "company_name is required"}), 400

    db = get_db()
    cur = db.execute("SELECT video_url FROM videos WHERE company_name = ?", (company_name,))
    row = cur.fetchone()

    if row:
        return jsonify({"company_name": company_name, "video_url": row["video_url"]}), 200
    else:
        return jsonify({"error": "Company not found"}), 404

@app.route('/media/<filename>')
def serve_media(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 8000))
    app.run(host=host, port=port, threaded=True)