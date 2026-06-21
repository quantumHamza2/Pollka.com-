import sqlite3

conn = sqlite3.connect("pollka.db")
cursor = conn.cursor()

# Enable foreign key support
cursor.execute("PRAGMA foreign_keys = ON")

# ──────────────── GENERAL USERS ────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    password        TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    email           TEXT,
    role            TEXT DEFAULT 'user',
    cgpa            REAL,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# ──────────────── POLLS ────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS polls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT,
    poll_type       TEXT DEFAULT 'single',
    created_by      INTEGER NOT NULL,
    is_active       INTEGER DEFAULT 1,
    deadline        TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
)
""")

# ──────────────── POLL OPTIONS ────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS poll_options (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id         INTEGER NOT NULL,
    option_text     TEXT NOT NULL,
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
)
""")

# ──────────────── VOTES ────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id         INTEGER NOT NULL,
    option_id       INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    rank_order      INTEGER,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES poll_options(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# ──────────────── SUBJECT ALLOCATION (preserved) ────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    total_seats INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    preference_order INTEGER NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
""")

# Insert default polling status
cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('polling_open', 'true')")

conn.commit()
conn.close()

print("Database created successfully")