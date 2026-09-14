"""
GameDev Journey - Main Flask Web Application
Provides real authentication, strict data persistence with SQLite, user data isolation,
zero-hallucination PDF resume parsing, video streaming, dynamic counters, REST APIs,
and public read-only profiles with granular visibility controls.
"""

import os
import json
import uuid
from datetime import timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, session, send_from_directory, abort

from database import init_db, get_db
from auth import auth_bp, login_required
from resume_parser import extract_raw_text, analyze_resume_strictly

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'mkv'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}
ALLOWED_DOC_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'gamedev-journey-cyber-secret-key-2026')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB max for gameplay videos
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Register Blueprints
app.register_blueprint(auth_bp)

# Ensure upload folders exist
for folder in ['resumes', 'videos', 'certificates', 'gdd']:
    os.makedirs(os.path.join(UPLOAD_FOLDER, folder), exist_ok=True)

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

# Initialize SQLite tables and migrations
init_db()

# -------------------------------------------------------------
# Frontend SPA & Public Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    """Serve the single-page application shell (Auth / Dashboard)."""
    return render_template('index.html')

@app.route('/profile/<username>')
def public_profile_page(username):
    """
    Public Read-Only Portfolio Route.
    Accessible to visitors, recruiters, and studios without requiring login.
    """
    clean_username = username.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id, username FROM users WHERE username = ?", (clean_username,)).fetchone()
    
    if not user:
        conn.close()
        return render_template('public_portfolio.html', found=False, username=clean_username), 404

    profile = cursor.execute("""
        SELECT profile_name, professional_title, about_me, career_goal, education,
               skills_json, github_url, linkedin_url, itchio_url
        FROM profiles WHERE user_id = ?
    """, (user['id'],)).fetchone()
    conn.close()

    prof_dict = dict(profile) if profile else {}
    dev_name = prof_dict.get('profile_name') or clean_username
    dev_title = prof_dict.get('professional_title') or 'Game Developer'
    about = prof_dict.get('about_me') or 'Game Developer Career Portfolio'

    og_meta = {
        'title': f"{dev_name} — {dev_title} | GameDev Journey",
        'description': about[:160],
        'username': clean_username,
        'url': request.base_url
    }

    return render_template('public_portfolio.html', found=True, username=clean_username, og=og_meta)

# -------------------------------------------------------------
# Public Read-Only Profile API (Unauthenticated Access)
# -------------------------------------------------------------
@app.route('/api/public/profile/<username>', methods=['GET'])
def get_public_profile(username):
    """
    Public API: Returns ONLY public profile information and items marked is_public = 1.
    Strictly excludes passwords, emails, private files, and sensitive records.
    """
    clean_username = username.strip().lower()
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute("SELECT id, username FROM users WHERE username = ?", (clean_username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': f'Operative profile "{clean_username}" not found.'}), 404

    user_id = user['id']

    # Fetch profile
    profile_row = cursor.execute("""
        SELECT profile_name, professional_title, about_me, career_goal, education,
               skills_json, other_details, github_url, linkedin_url, itchio_url
        FROM profiles WHERE user_id = ?
    """, (user_id,)).fetchone()

    profile = dict(profile_row) if profile_row else {}
    try:
        profile['skills'] = json.loads(profile.get('skills_json') or '[]')
    except Exception:
        profile['skills'] = []

    # Fetch Game Jams (all jams public by nature of portfolio)
    jams_rows = cursor.execute("""
        SELECT id, jam_name, event_platform, date, game_created, role, description, jam_link
        FROM game_jams WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    game_jams = [dict(r) for r in jams_rows]

    # Fetch Gameplay Videos where is_public = 1
    vid_rows = cursor.execute("""
        SELECT id, title, description, filename, file_size, created_at
        FROM gameplay_videos WHERE user_id = ? AND is_public = 1
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    videos = []
    for r in vid_rows:
        v = dict(r)
        v['stream_url'] = f"/api/public/uploads/videos/{clean_username}/{v['filename']}"
        videos.append(v)

    # Fetch Achievements where is_public = 1
    ach_rows = cursor.execute("""
        SELECT id, title, description, date, organization, category, certificate_filename, created_at
        FROM achievements WHERE user_id = ? AND is_public = 1
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    achievements = []
    for r in ach_rows:
        a = dict(r)
        if a.get('certificate_filename'):
            a['certificate_url'] = f"/api/public/uploads/certificates/{clean_username}/{a['certificate_filename']}"
        else:
            a['certificate_url'] = None
        achievements.append(a)

    # Fetch GDD Document ONLY IF is_public = 1
    gdd_row = cursor.execute("""
        SELECT id, title, filename, file_size, uploaded_at
        FROM gdd_documents WHERE user_id = ? AND is_public = 1
        ORDER BY uploaded_at DESC LIMIT 1
    """, (user_id,)).fetchone()

    gdd = None
    if gdd_row:
        gdd = dict(gdd_row)
        gdd['view_url'] = f"/api/public/uploads/gdd/{clean_username}/{gdd['filename']}"

    # Calculate dynamic stats
    xp = 0
    if profile:
        if profile.get('profile_name'): xp += 500
        if profile.get('professional_title'): xp += 400
        if profile.get('about_me'): xp += 500
        if profile.get('career_goal'): xp += 400
        if profile.get('education'): xp += 500
        xp += len(profile.get('skills', [])) * 100
        if profile.get('github_url'): xp += 250
        if profile.get('linkedin_url'): xp += 250
        if profile.get('itchio_url'): xp += 250

    xp += len(game_jams) * 600
    xp += len(achievements) * 500
    xp += len(videos) * 750
    if gdd: xp += 1000

    level = max(1, 1 + (xp // 1000))
    current_level_xp = xp % 1000
    next_level_xp = 1000

    conn.close()

    return jsonify({
        'username': clean_username,
        'profile': profile,
        'game_jams': game_jams,
        'videos': videos,
        'achievements': achievements,
        'gdd': gdd,
        'stats': {
            'xp': xp,
            'level': level,
            'current_level_xp': current_level_xp,
            'next_level_xp': next_level_xp,
            'total_game_jams': len(game_jams),
            'total_achievements': len(achievements),
            'total_videos': len(videos),
            'has_gdd': gdd is not None
        }
    }), 200

# -------------------------------------------------------------
# Public File Serving (Streams only files marked is_public = 1)
# -------------------------------------------------------------
@app.route('/api/public/uploads/<category>/<username>/<filename>')
def serve_public_user_file(category, username, filename):
    """
    Public file streaming: Verifies that the requested file belongs to username
    AND that the corresponding database record is explicitly marked is_public = 1.
    If private (is_public = 0), returns 403 Forbidden.
    """
    clean_username = username.strip().lower()
    safe_category = secure_filename(category)
    safe_filename = secure_filename(filename)

    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id FROM users WHERE username = ?", (clean_username,)).fetchone()
    if not user:
        conn.close()
        abort(404)

    user_id = user['id']
    is_public = False

    if safe_category == 'videos':
        row = cursor.execute("SELECT is_public FROM gameplay_videos WHERE user_id = ? AND filename = ?", (user_id, safe_filename)).fetchone()
        if row and row['is_public'] == 1:
            is_public = True
    elif safe_category == 'certificates':
        row = cursor.execute("SELECT is_public FROM achievements WHERE user_id = ? AND certificate_filename = ?", (user_id, safe_filename)).fetchone()
        if row and row['is_public'] == 1:
            is_public = True
    elif safe_category == 'gdd':
        row = cursor.execute("SELECT is_public FROM gdd_documents WHERE user_id = ? AND filename = ?", (user_id, safe_filename)).fetchone()
        if row and row['is_public'] == 1:
            is_public = True

    conn.close()

    if not is_public:
        return jsonify({'error': 'Access denied. This file has not been made public by the owner.'}), 403

    user_folder = os.path.join(UPLOAD_FOLDER, safe_category, str(user_id))
    if not os.path.exists(os.path.join(user_folder, safe_filename)):
        abort(404)

    return send_from_directory(user_folder, safe_filename)

# -------------------------------------------------------------
# Secure Authenticated File Delivery (Private Owner Access)
# -------------------------------------------------------------
@app.route('/api/uploads/<category>/<int:user_id>/<filename>')
def serve_user_file(category, user_id, filename):
    """
    Strict file server: Ensures User A cannot access User B's private uploads.
    """
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Unauthorized. Please log in.'}), 401
        
    if current_user_id != user_id:
        return jsonify({'error': 'Access denied to another user\'s private file.'}), 403

    safe_category = secure_filename(category)
    safe_filename = secure_filename(filename)
    user_folder = os.path.join(UPLOAD_FOLDER, safe_category, str(user_id))

    if not os.path.exists(os.path.join(user_folder, safe_filename)):
        abort(404)

    return send_from_directory(user_folder, safe_filename)

# -------------------------------------------------------------
# Visibility Toggle API (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/visibility/<category>/<int:item_id>', methods=['PATCH'])
@login_required
def toggle_visibility(category, item_id):
    """Toggle Public / Private visibility on videos, achievements, or GDD."""
    user_id = session['user_id']
    data = request.get_json() or {}
    new_status = 1 if data.get('is_public') else 0

    conn = get_db()
    cursor = conn.cursor()

    if category == 'videos':
        cursor.execute("UPDATE gameplay_videos SET is_public = ? WHERE id = ? AND user_id = ?", (new_status, item_id, user_id))
    elif category == 'achievements':
        cursor.execute("UPDATE achievements SET is_public = ? WHERE id = ? AND user_id = ?", (new_status, item_id, user_id))
    elif category == 'gdd':
        cursor.execute("UPDATE gdd_documents SET is_public = ? WHERE id = ? AND user_id = ?", (new_status, item_id, user_id))
    else:
        conn.close()
        return jsonify({'error': 'Invalid category for visibility toggle.'}), 400

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Item not found or unauthorized.'}), 404

    conn.commit()
    conn.close()

    status_str = "Public" if new_status == 1 else "Private"
    return jsonify({
        'message': f"Visibility set to {status_str}.",
        'is_public': new_status == 1
    }), 200

# -------------------------------------------------------------
# Personal Profile API (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    user_row = cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    username = user_row['username'] if user_row else ''

    row = cursor.execute("""
        SELECT profile_name, professional_title, about_me, career_goal, education,
               skills_json, experience_json, certifications_json, other_details,
               github_url, linkedin_url, itchio_url, updated_at
        FROM profiles WHERE user_id = ?
    """, (user_id,)).fetchone()

    conn.close()
    if not row:
        return jsonify({'error': 'Profile not found.'}), 404

    profile = dict(row)
    profile['username'] = username
    profile['public_url'] = f"/profile/{username}" if username else ''
    try:
        profile['skills'] = json.loads(profile.get('skills_json') or '[]')
    except Exception:
        profile['skills'] = []

    return jsonify({'profile': profile}), 200

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    user_id = session['user_id']
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    profile_name = data.get('profile_name', '').strip()
    professional_title = data.get('professional_title', '').strip()
    about_me = data.get('about_me', '').strip()
    career_goal = data.get('career_goal', '').strip()
    education = data.get('education', '').strip()
    other_details = data.get('other_details', '').strip()
    github_url = data.get('github_url', '').strip()
    linkedin_url = data.get('linkedin_url', '').strip()
    itchio_url = data.get('itchio_url', '').strip()

    skills = data.get('skills', [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(',') if s.strip()]
    skills_json = json.dumps(skills)

    cursor.execute("""
        UPDATE profiles SET
            profile_name = ?,
            professional_title = ?,
            about_me = ?,
            career_goal = ?,
            education = ?,
            skills_json = ?,
            other_details = ?,
            github_url = ?,
            linkedin_url = ?,
            itchio_url = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        profile_name, professional_title, about_me, career_goal, education,
        skills_json, other_details, github_url, linkedin_url, itchio_url, user_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Profile updated successfully.',
        'profile': {
            'profile_name': profile_name,
            'professional_title': professional_title,
            'about_me': about_me,
            'career_goal': career_goal,
            'education': education,
            'skills': skills,
            'other_details': other_details,
            'github_url': github_url,
            'linkedin_url': linkedin_url,
            'itchio_url': itchio_url
        }
    }), 200

@app.route('/api/profile/name', methods=['PUT'])
@login_required
def update_profile_name():
    """Quick dedicated endpoint for Profile Name editing."""
    user_id = session['user_id']
    data = request.get_json() or {}
    new_name = (data.get('profile_name') or '').strip()

    if not new_name:
        return jsonify({'error': 'Profile name cannot be blank.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET profile_name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (new_name, user_id))
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Profile name updated successfully.',
        'profile_name': new_name
    }), 200

# -------------------------------------------------------------
# Resume Upload + AI Zero-Hallucination Extraction
# -------------------------------------------------------------
@app.route('/api/resume/upload', methods=['POST'])
@login_required
def upload_resume():
    user_id = session['user_id']

    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided.'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    if not allowed_file(file.filename, ALLOWED_DOC_EXTENSIONS):
        return jsonify({'error': 'Only PDF resumes are supported.'}), 400

    user_dir = os.path.join(UPLOAD_FOLDER, 'resumes', str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)

    try:
        raw_text = extract_raw_text(file_path)
    except Exception as e:
        return jsonify({'error': f'Failed to parse PDF: {str(e)}'}), 400

    if not raw_text or len(raw_text.strip()) == 0:
        return jsonify({'error': 'Could not extract any readable text from this PDF. Please ensure it is not a scanned image.'}), 400

    extracted_data = analyze_resume_strictly(raw_text)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resumes (user_id, filename, file_path, raw_text, parsed_json)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, original_filename, file_path, raw_text, json.dumps(extracted_data)))
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Resume uploaded successfully.',
        'resume_id': resume_id,
        'filename': original_filename,
        'extracted': extracted_data
    }), 200

@app.route('/api/resume/apply', methods=['POST'])
@login_required
def apply_resume_data():
    """Apply verified/edited resume data into the user's active profile."""
    user_id = session['user_id']
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    curr = cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if not curr:
        conn.close()
        return jsonify({'error': 'Profile not found.'}), 404

    profile_name = data.get('profile_name', curr['profile_name'])
    professional_title = data.get('professional_title', curr['professional_title'])
    about_me = data.get('about_me', curr['about_me'])
    education = data.get('education', curr['education'])
    
    new_skills = data.get('skills', [])
    if isinstance(new_skills, list) and new_skills:
        skills_json = json.dumps(new_skills)
    else:
        skills_json = curr['skills_json']

    github_url = data.get('github_url') or curr['github_url']
    linkedin_url = data.get('linkedin_url') or curr['linkedin_url']
    itchio_url = data.get('itchio_url') or curr['itchio_url']

    cursor.execute("""
        UPDATE profiles SET
            profile_name = ?,
            professional_title = ?,
            about_me = ?,
            education = ?,
            skills_json = ?,
            github_url = ?,
            linkedin_url = ?,
            itchio_url = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (profile_name, professional_title, about_me, education, skills_json, github_url, linkedin_url, itchio_url, user_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Profile updated successfully from resume.'}), 200

# -------------------------------------------------------------
# Gameplay Videos API (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/videos', methods=['GET'])
@login_required
def get_videos():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT id, title, description, filename, file_size, is_public, created_at
        FROM gameplay_videos WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()

    videos = []
    for r in rows:
        v = dict(r)
        v['stream_url'] = f"/api/uploads/videos/{user_id}/{v['filename']}"
        videos.append(v)

    return jsonify({'videos': videos}), 200

@app.route('/api/videos', methods=['POST'])
@login_required
def upload_video():
    user_id = session['user_id']

    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided.'}), 400

    file = request.files['video']
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    is_public = 1 if request.form.get('is_public', '1') == '1' else 0

    if not title:
        return jsonify({'error': 'Video title is required.'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected video file.'}), 400

    if not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({'error': f'Unsupported video format. Allowed: {", ".join(ALLOWED_VIDEO_EXTENSIONS)}'}), 400

    user_dir = os.path.join(UPLOAD_FOLDER, 'videos', str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    original_name = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO gameplay_videos (user_id, title, description, filename, file_path, file_size, is_public)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, title, description, unique_filename, file_path, file_size, is_public))
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Gameplay video uploaded successfully.',
        'video': {
            'id': video_id,
            'title': title,
            'description': description,
            'filename': unique_filename,
            'file_size': file_size,
            'is_public': is_public,
            'stream_url': f"/api/uploads/videos/{user_id}/{unique_filename}"
        }
    }), 201

@app.route('/api/videos/<int:video_id>', methods=['PUT'])
@login_required
def edit_video(video_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()

    if not title:
        return jsonify({'error': 'Video title is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("SELECT id FROM gameplay_videos WHERE id = ? AND user_id = ?", (video_id, user_id)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Video not found or access denied.'}), 404

    cursor.execute("""
        UPDATE gameplay_videos SET title = ?, description = ?
        WHERE id = ? AND user_id = ?
    """, (title, description, video_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Video details updated successfully.'}), 200

@app.route('/api/videos/<int:video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    row = cursor.execute("SELECT file_path FROM gameplay_videos WHERE id = ? AND user_id = ?", (video_id, user_id)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Video not found or access denied.'}), 404

    file_path = row['file_path']
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    cursor.execute("DELETE FROM gameplay_videos WHERE id = ? AND user_id = ?", (video_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Gameplay video deleted successfully.'}), 200

# -------------------------------------------------------------
# Game Jams History API (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/game-jams', methods=['GET'])
@login_required
def get_game_jams():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT id, jam_name, event_platform, date, game_created, role, description, jam_link, created_at
        FROM game_jams WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()

    count_row = cursor.execute("SELECT COUNT(*) AS total FROM game_jams WHERE user_id = ?", (user_id,)).fetchone()
    total_count = count_row['total'] if count_row else 0
    conn.close()

    return jsonify({
        'total_game_jams': total_count,
        'game_jams': [dict(r) for r in rows]
    }), 200

@app.route('/api/game-jams', methods=['POST'])
@login_required
def add_game_jam():
    user_id = session['user_id']
    data = request.get_json() or {}

    jam_name = (data.get('jam_name') or '').strip()
    if not jam_name:
        return jsonify({'error': 'Game Jam name is required.'}), 400

    event_platform = (data.get('event_platform') or '').strip()
    date = (data.get('date') or '').strip()
    game_created = (data.get('game_created') or '').strip()
    role = (data.get('role') or '').strip()
    description = (data.get('description') or '').strip()
    jam_link = (data.get('jam_link') or '').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO game_jams (user_id, jam_name, event_platform, date, game_created, role, description, jam_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, jam_name, event_platform, date, game_created, role, description, jam_link))
    jam_id = cursor.lastrowid

    count_row = cursor.execute("SELECT COUNT(*) AS total FROM game_jams WHERE user_id = ?", (user_id,)).fetchone()
    total_count = count_row['total'] if count_row else 0

    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Game Jam added successfully.',
        'jam_id': jam_id,
        'total_game_jams': total_count
    }), 201

@app.route('/api/game-jams/<int:jam_id>', methods=['PUT'])
@login_required
def update_game_jam(jam_id):
    user_id = session['user_id']
    data = request.get_json() or {}

    jam_name = (data.get('jam_name') or '').strip()
    if not jam_name:
        return jsonify({'error': 'Game Jam name is required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id FROM game_jams WHERE id = ? AND user_id = ?", (jam_id, user_id)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Game Jam record not found.'}), 404

    cursor.execute("""
        UPDATE game_jams SET
            jam_name = ?,
            event_platform = ?,
            date = ?,
            game_created = ?,
            role = ?,
            description = ?,
            jam_link = ?
        WHERE id = ? AND user_id = ?
    """, (
        jam_name,
        (data.get('event_platform') or '').strip(),
        (data.get('date') or '').strip(),
        (data.get('game_created') or '').strip(),
        (data.get('role') or '').strip(),
        (data.get('description') or '').strip(),
        (data.get('jam_link') or '').strip(),
        jam_id, user_id
    ))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Game Jam updated successfully.'}), 200

@app.route('/api/game-jams/<int:jam_id>', methods=['DELETE'])
@login_required
def delete_game_jam(jam_id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM game_jams WHERE id = ? AND user_id = ?", (jam_id, user_id))
    count_row = cursor.execute("SELECT COUNT(*) AS total FROM game_jams WHERE user_id = ?", (user_id,)).fetchone()
    total_count = count_row['total'] if count_row else 0
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Game Jam deleted successfully.',
        'total_game_jams': total_count
    }), 200

# -------------------------------------------------------------
# Achievements API (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/achievements', methods=['GET'])
@login_required
def get_achievements():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT id, title, description, date, organization, category, certificate_filename, is_public, created_at
        FROM achievements WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()

    achievements = []
    for r in rows:
        a = dict(r)
        if a.get('certificate_filename'):
            a['certificate_url'] = f"/api/uploads/certificates/{user_id}/{a['certificate_filename']}"
        else:
            a['certificate_url'] = None
        achievements.append(a)

    return jsonify({'achievements': achievements}), 200

@app.route('/api/achievements', methods=['POST'])
@login_required
def add_achievement():
    user_id = session['user_id']

    title = (request.form.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Achievement title is required.'}), 400

    description = (request.form.get('description') or '').strip()
    date = (request.form.get('date') or '').strip()
    organization = (request.form.get('organization') or '').strip()
    category = (request.form.get('category') or 'Milestone').strip()
    is_public = 1 if request.form.get('is_public', '1') == '1' else 0

    cert_filename = ''
    cert_path = ''

    if 'certificate' in request.files:
        file = request.files['certificate']
        if file and file.filename != '':
            if allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOC_EXTENSIONS):
                user_dir = os.path.join(UPLOAD_FOLDER, 'certificates', str(user_id))
                os.makedirs(user_dir, exist_ok=True)
                clean_name = secure_filename(file.filename)
                cert_filename = f"{uuid.uuid4().hex}_{clean_name}"
                cert_path = os.path.join(user_dir, cert_filename)
                file.save(cert_path)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO achievements (user_id, title, description, date, organization, category, certificate_filename, certificate_path, is_public)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, title, description, date, organization, category, cert_filename, cert_path, is_public))
    ach_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Achievement saved successfully.',
        'achievement': {
            'id': ach_id,
            'title': title,
            'description': description,
            'date': date,
            'organization': organization,
            'category': category,
            'is_public': is_public,
            'certificate_url': f"/api/uploads/certificates/{user_id}/{cert_filename}" if cert_filename else None
        }
    }), 201

@app.route('/api/achievements/<int:ach_id>', methods=['PUT'])
@login_required
def edit_achievement(ach_id):
    user_id = session['user_id']
    title = (request.form.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Achievement title is required.'}), 400

    description = (request.form.get('description') or '').strip()
    date = (request.form.get('date') or '').strip()
    organization = (request.form.get('organization') or '').strip()
    category = (request.form.get('category') or 'Milestone').strip()

    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT certificate_filename, certificate_path FROM achievements WHERE id = ? AND user_id = ?", (ach_id, user_id)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Achievement not found.'}), 404

    cert_filename = existing['certificate_filename']
    cert_path = existing['certificate_path']

    if 'certificate' in request.files:
        file = request.files['certificate']
        if file and file.filename != '':
            if allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOC_EXTENSIONS):
                if cert_path and os.path.exists(cert_path):
                    try:
                        os.remove(cert_path)
                    except Exception:
                        pass
                user_dir = os.path.join(UPLOAD_FOLDER, 'certificates', str(user_id))
                os.makedirs(user_dir, exist_ok=True)
                clean_name = secure_filename(file.filename)
                cert_filename = f"{uuid.uuid4().hex}_{clean_name}"
                cert_path = os.path.join(user_dir, cert_filename)
                file.save(cert_path)

    cursor.execute("""
        UPDATE achievements SET
            title = ?,
            description = ?,
            date = ?,
            organization = ?,
            category = ?,
            certificate_filename = ?,
            certificate_path = ?
        WHERE id = ? AND user_id = ?
    """, (title, description, date, organization, category, cert_filename, cert_path, ach_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Achievement updated successfully.'}), 200

@app.route('/api/achievements/<int:ach_id>', methods=['DELETE'])
@login_required
def delete_achievement(ach_id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT certificate_path FROM achievements WHERE id = ? AND user_id = ?", (ach_id, user_id)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Achievement not found.'}), 404

    cert_path = existing['certificate_path']
    if cert_path and os.path.exists(cert_path):
        try:
            os.remove(cert_path)
        except Exception:
            pass

    cursor.execute("DELETE FROM achievements WHERE id = ? AND user_id = ?", (ach_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Achievement deleted successfully.'}), 200

# -------------------------------------------------------------
# My Next Game Project Idea / GDD PDF Storage API (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/gdd', methods=['GET'])
@login_required
def get_gdd():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("""
        SELECT id, title, filename, file_size, is_public, uploaded_at
        FROM gdd_documents WHERE user_id = ?
        ORDER BY uploaded_at DESC LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({'has_gdd': False, 'gdd': None}), 200

    gdd = dict(row)
    gdd['view_url'] = f"/api/uploads/gdd/{user_id}/{gdd['filename']}"
    return jsonify({'has_gdd': True, 'gdd': gdd}), 200

@app.route('/api/gdd', methods=['POST'])
@login_required
def upload_or_replace_gdd():
    user_id = session['user_id']

    if 'gdd' not in request.files:
        return jsonify({'error': 'No GDD PDF file provided.'}), 400

    file = request.files['gdd']
    title = (request.form.get('title') or 'Next Game Project Design Document').strip()
    is_public = 1 if request.form.get('is_public', '0') == '1' else 0

    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    if not allowed_file(file.filename, ALLOWED_DOC_EXTENSIONS):
        return jsonify({'error': 'Only PDF format is supported for Game Design Documents.'}), 400

    user_dir = os.path.join(UPLOAD_FOLDER, 'gdd', str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()
    old = cursor.execute("SELECT id, file_path FROM gdd_documents WHERE user_id = ?", (user_id,)).fetchone()
    if old:
        if old['file_path'] and os.path.exists(old['file_path']):
            try:
                os.remove(old['file_path'])
            except Exception:
                pass
        cursor.execute("DELETE FROM gdd_documents WHERE user_id = ?", (user_id,))

    original_name = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    cursor.execute("""
        INSERT INTO gdd_documents (user_id, title, filename, file_path, file_size, is_public)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, title, unique_filename, file_path, file_size, is_public))
    gdd_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Game Design Document saved successfully.',
        'gdd': {
            'id': gdd_id,
            'title': title,
            'filename': original_name,
            'file_size': file_size,
            'is_public': is_public,
            'view_url': f"/api/uploads/gdd/{user_id}/{unique_filename}"
        }
    }), 201

@app.route('/api/gdd', methods=['DELETE'])
@login_required
def delete_gdd():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    old = cursor.execute("SELECT id, file_path FROM gdd_documents WHERE user_id = ?", (user_id,)).fetchone()
    if not old:
        conn.close()
        return jsonify({'error': 'No GDD document found.'}), 404

    if old['file_path'] and os.path.exists(old['file_path']):
        try:
            os.remove(old['file_path'])
        except Exception:
            pass

    cursor.execute("DELETE FROM gdd_documents WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Game Design Document deleted successfully.'}), 200

# -------------------------------------------------------------
# Dashboard Statistics & Level Calculator (Owner Protected)
# -------------------------------------------------------------
@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    profile = cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    jams_count = cursor.execute("SELECT COUNT(*) AS total FROM game_jams WHERE user_id = ?", (user_id,)).fetchone()['total']
    ach_count = cursor.execute("SELECT COUNT(*) AS total FROM achievements WHERE user_id = ?", (user_id,)).fetchone()['total']
    vid_count = cursor.execute("SELECT COUNT(*) AS total FROM gameplay_videos WHERE user_id = ?", (user_id,)).fetchone()['total']
    gdd_count = cursor.execute("SELECT COUNT(*) AS total FROM gdd_documents WHERE user_id = ?", (user_id,)).fetchone()['total']
    res_count = cursor.execute("SELECT COUNT(*) AS total FROM resumes WHERE user_id = ?", (user_id,)).fetchone()['total']
    conn.close()

    xp = 0
    if profile:
        if profile['profile_name']: xp += 500
        if profile['professional_title']: xp += 400
        if profile['about_me']: xp += 500
        if profile['career_goal']: xp += 400
        if profile['education']: xp += 500
        try:
            skills = json.loads(profile['skills_json'] or '[]')
            xp += len(skills) * 100
        except Exception:
            pass
        if profile['github_url']: xp += 250
        if profile['linkedin_url']: xp += 250
        if profile['itchio_url']: xp += 250

    xp += jams_count * 600
    xp += ach_count * 500
    xp += vid_count * 750
    xp += gdd_count * 1000
    xp += res_count * 500

    level = max(1, 1 + (xp // 1000))
    current_level_xp = xp % 1000
    next_level_xp = 1000

    return jsonify({
        'xp': xp,
        'level': level,
        'current_level_xp': current_level_xp,
        'next_level_xp': next_level_xp,
        'total_game_jams': jams_count,
        'total_achievements': ach_count,
        'total_videos': vid_count,
        'has_gdd': gdd_count > 0,
        'has_resume': res_count > 0
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 GameDev Journey Web App running on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
