"""
GameDev Journey - Authentication Blueprint & Session Management
Handles Email-based Sign Up, Login, Logout, Username Management, and Current User State.
Ensures every new user starts with an empty profile.
"""

import re
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')

def generate_unique_username(cursor, email, requested_username=None):
    """Generate a clean, unique URL-safe username from email or requested name."""
    if requested_username and USERNAME_REGEX.match(requested_username):
        base = requested_username.lower()
    else:
        prefix = email.split('@')[0]
        base = re.sub(r'[^a-zA-Z0-9_-]', '', prefix).lower()
        if len(base) < 3:
            base = f"dev_{base}"
        base = base[:20]

    candidate = base
    counter = 1
    while True:
        existing = cursor.execute("SELECT id FROM users WHERE username = ?", (candidate,)).fetchone()
        if not existing:
            return candidate
        candidate = f"{base}_{counter}"
        counter += 1

def login_required(view):
    """Decorator to require login on protected API endpoints."""
    from functools import wraps
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized. Please log in.'}), 401
        return view(**kwargs)
    return wrapped_view

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user account with an email and password."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    custom_username = (data.get('username') or '').strip()

    if not email or not EMAIL_REGEX.match(email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    if custom_username and not USERNAME_REGEX.match(custom_username):
        return jsonify({'error': 'Username must be 3-30 alphanumeric characters, hyphens, or underscores.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if email is already registered
    existing = cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'An account with this email address already exists.'}), 409

    # Generate secure salted hash and unique username
    password_hash = generate_password_hash(password)
    username = generate_unique_username(cursor, email, custom_username)

    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, username) VALUES (?, ?, ?)",
            (email, password_hash, username)
        )
        user_id = cursor.lastrowid

        # Initialize profile completely empty as required
        cursor.execute("""
            INSERT INTO profiles (
                user_id, profile_name, professional_title, about_me, 
                career_goal, education, skills_json, experience_json, 
                certifications_json, other_details, github_url, linkedin_url, itchio_url
            ) VALUES (?, '', '', '', '', '', '[]', '[]', '[]', '', '', '', '')
        """, (user_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to create account: {str(e)}'}), 500

    conn.close()

    # Automatically set session
    session.permanent = True
    session['user_id'] = user_id
    session['email'] = email
    session['username'] = username

    return jsonify({
        'message': 'Account created successfully.',
        'user': {
            'id': user_id,
            'email': email,
            'username': username
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate an existing user with email and password."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id, email, password_hash, username FROM users WHERE email = ?", (email,)).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        conn.close()
        return jsonify({'error': 'Invalid email address or password.'}), 401

    username = user['username']
    # If legacy user has empty username, generate one
    if not username:
        username = generate_unique_username(cursor, user['email'])
        cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user['id']))
        conn.commit()

    profile = cursor.execute("SELECT profile_name FROM profiles WHERE user_id = ?", (user['id'],)).fetchone()
    conn.close()

    session.permanent = True
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['username'] = username

    return jsonify({
        'message': 'Login successful.',
        'user': {
            'id': user['id'],
            'email': user['email'],
            'username': username,
            'profile_name': profile['profile_name'] if profile else ''
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear session data on logout."""
    session.clear()
    return jsonify({'message': 'Logged out successfully.'}), 200

@auth_bp.route('/me', methods=['GET'])
def me():
    """Get currently logged-in user profile metadata."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200

    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id, email, username, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        session.clear()
        return jsonify({'authenticated': False}), 200

    username = user['username']
    if not username:
        username = generate_unique_username(cursor, user['email'])
        cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user['id']))
        conn.commit()
        session['username'] = username

    profile = cursor.execute("SELECT profile_name, professional_title FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    return jsonify({
        'authenticated': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'username': username,
            'created_at': user['created_at'],
            'profile_name': profile['profile_name'] if profile else '',
            'professional_title': profile['professional_title'] if profile else ''
        }
    }), 200

@auth_bp.route('/username', methods=['PUT'])
@login_required
def update_username():
    """Allow account owner to update their unique public profile username slug."""
    user_id = session['user_id']
    data = request.get_json() or {}
    new_username = (data.get('username') or '').strip().lower()

    if not new_username or not USERNAME_REGEX.match(new_username):
        return jsonify({'error': 'Username must be 3-30 alphanumeric characters, hyphens, or underscores.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    existing = cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': f'The username "{new_username}" is already taken.'}), 409

    cursor.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
    conn.commit()
    conn.close()

    session['username'] = new_username

    return jsonify({
        'message': 'Username updated successfully.',
        'username': new_username,
        'public_url': f"/profile/{new_username}"
    }), 200
