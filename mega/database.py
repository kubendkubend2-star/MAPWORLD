"""
GameDev Journey - Database Manager & Schema Initialization
Uses SQLite with WAL mode, foreign keys enabled, and clean table definitions.
Includes auto-migration for public profiles and visibility controls.
"""

import sqlite3
import os
import re

DB_PATH = os.environ.get('GAMEDEV_DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'gamedev.db'))

def get_db():
    """Create and return a database connection with Row factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def migrate_db(conn):
    """Safely migrate schema to add username and is_public columns if missing."""
    cursor = conn.cursor()
    
    # Check columns in users table
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [row['name'] for row in cursor.fetchall()]
    if 'username' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT DEFAULT ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username COLLATE NOCASE)")
        
        # Populate initial usernames from email for any existing users
        cursor.execute("SELECT id, email FROM users")
        for u in cursor.fetchall():
            email_prefix = u['email'].split('@')[0]
            clean_username = re.sub(r'[^a-zA-Z0-9_-]', '', email_prefix).lower()
            if len(clean_username) < 3:
                clean_username = f"dev_{clean_username}_{u['id']}"
            else:
                clean_username = f"{clean_username}_{u['id']}"
            cursor.execute("UPDATE users SET username = ? WHERE id = ?", (clean_username, u['id']))

    # Check is_public in gameplay_videos
    cursor.execute("PRAGMA table_info(gameplay_videos)")
    video_cols = [row['name'] for row in cursor.fetchall()]
    if 'is_public' not in video_cols:
        cursor.execute("ALTER TABLE gameplay_videos ADD COLUMN is_public INTEGER DEFAULT 1")

    # Check is_public in achievements
    cursor.execute("PRAGMA table_info(achievements)")
    ach_cols = [row['name'] for row in cursor.fetchall()]
    if 'is_public' not in ach_cols:
        cursor.execute("ALTER TABLE achievements ADD COLUMN is_public INTEGER DEFAULT 1")

    # Check is_public in gdd_documents (Default 0: private by default to protect game IP)
    cursor.execute("PRAGMA table_info(gdd_documents)")
    gdd_cols = [row['name'] for row in cursor.fetchall()]
    if 'is_public' not in gdd_cols:
        cursor.execute("ALTER TABLE gdd_documents ADD COLUMN is_public INTEGER DEFAULT 0")

    # Check is_public in resumes
    cursor.execute("PRAGMA table_info(resumes)")
    res_cols = [row['name'] for row in cursor.fetchall()]
    if 'is_public' not in res_cols:
        cursor.execute("ALTER TABLE resumes ADD COLUMN is_public INTEGER DEFAULT 1")

    conn.commit()

def init_db():
    """Initialize all tables in SQLite and apply migrations."""
    conn = get_db()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            username TEXT UNIQUE COLLATE NOCASE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            profile_name TEXT DEFAULT '',
            professional_title TEXT DEFAULT '',
            about_me TEXT DEFAULT '',
            career_goal TEXT DEFAULT '',
            education TEXT DEFAULT '',
            skills_json TEXT DEFAULT '[]',
            experience_json TEXT DEFAULT '[]',
            certifications_json TEXT DEFAULT '[]',
            other_details TEXT DEFAULT '',
            github_url TEXT DEFAULT '',
            linkedin_url TEXT DEFAULT '',
            itchio_url TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS game_jams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            jam_name TEXT NOT NULL,
            event_platform TEXT DEFAULT '',
            date TEXT DEFAULT '',
            game_created TEXT DEFAULT '',
            role TEXT DEFAULT '',
            description TEXT DEFAULT '',
            jam_link TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            date TEXT DEFAULT '',
            organization TEXT DEFAULT '',
            category TEXT DEFAULT '',
            certificate_filename TEXT DEFAULT '',
            certificate_path TEXT DEFAULT '',
            is_public INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS gameplay_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            is_public INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS gdd_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            is_public INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            parsed_json TEXT DEFAULT '{}',
            is_public INTEGER DEFAULT 1,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        migrate_db(conn)
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database schema successfully initialized and migrated.")
