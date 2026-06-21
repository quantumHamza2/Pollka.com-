import sqlite3
import random

conn = sqlite3.connect("pollka.db")
cursor = conn.cursor()

# ---------- CLEAR OLD DATA ----------
cursor.execute("DELETE FROM votes")
cursor.execute("DELETE FROM poll_options")
cursor.execute("DELETE FROM polls")
cursor.execute("DELETE FROM allocations")
cursor.execute("DELETE FROM preferences")
cursor.execute("DELETE FROM subjects")
cursor.execute("DELETE FROM users")

# Reset polling status
cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('polling_open', 'true')")

# ---------- USERS (20 students + 1 admin) ----------
students = [
    ("student1", "password", "Rishabh Jha", "rishabh@pollka.com", "user", 9.7),
    ("student2", "password", "Priya Sharma", "priya@pollka.com", "user", 8.5),
    ("student3", "password", "Arjun Mehta", "arjun@pollka.com", "user", 7.3),
    ("student4", "password", "Neha Kapoor", "neha@pollka.com", "user", 9.2),
    ("student5", "password", "Rahul Verma", "rahul@pollka.com", "user", 8.9),
    ("student6", "password", "Ananya Iyer", "ananya@pollka.com", "user", 9.5),
    ("student7", "password", "Karan Malhotra", "karan@pollka.com", "user", 7.8),
    ("student8", "password", "Sneha Reddy", "sneha@pollka.com", "user", 8.2),
    ("student9", "password", "Vikram Singh", "vikram@pollka.com", "user", 6.9),
    ("student10", "password", "Meera Nair", "meera@pollka.com", "user", 9.1),
    ("student11", "password", "Aditya Gupta", "aditya@pollka.com", "user", 8.0),
    ("student12", "password", "Pooja Sharma", "pooja@pollka.com", "user", 7.5),
    ("student13", "password", "Rohan Das", "rohan@pollka.com", "user", 8.7),
    ("student14", "password", "Ishita Jain", "ishita@pollka.com", "user", 9.3),
    ("student15", "password", "Yash Patel", "yash@pollka.com", "user", 7.9),
    ("student16", "password", "Simran Kaur", "simran@pollka.com", "user", 8.4),
    ("student17", "password", "Arnav Mishra", "arnav@pollka.com", "user", 9.6),
    ("student18", "password", "Tanya Bose", "tanya@pollka.com", "user", 8.1),
    ("student19", "password", "Kabir Khan", "kabir@pollka.com", "user", 7.2),
    ("student20", "password", "Divya Menon", "divya@pollka.com", "user", 9.0),
]

cursor.executemany(
    "INSERT INTO users (username, password, display_name, email, role, cgpa) VALUES (?, ?, ?, ?, ?, ?)",
    students
)

# Admin user
cursor.execute(
    "INSERT INTO users (username, password, display_name, email, role) VALUES (?, ?, ?, ?, ?)",
    ("admin", "admin123", "Admin", "admin@pollka.com", "admin")
)

# ---------- SUBJECTS (10) ----------
subjects = [
    ("Advanced Algorithms", 5),
    ("Machine Learning", 4),
    ("Database Systems", 6),
    ("Computer Networks", 5),
    ("Software Engineering", 6),
    ("Artificial Intelligence", 4),
    ("Cyber Security", 3),
    ("Cloud Computing", 5),
    ("Data Science", 4),
    ("Operating Systems", 5),
]

cursor.executemany(
    "INSERT INTO subjects (name, total_seats) VALUES (?, ?)",
    subjects
)

# ---------- GENERATE STUDENT PREFERENCES ----------
cursor.execute("SELECT id FROM users WHERE role='user'")
student_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT id FROM subjects")
subject_ids = [row[0] for row in cursor.fetchall()]

preferences = []
for sid in student_ids:
    num_prefs = random.randint(3, 5)
    chosen = random.sample(subject_ids, num_prefs)
    for order, subj_id in enumerate(chosen, start=1):
        preferences.append((sid, subj_id, order))

cursor.executemany(
    "INSERT INTO preferences (student_id, subject_id, preference_order) VALUES (?, ?, ?)",
    preferences
)

# ---------- SAMPLE POLLS ----------
# Get admin user id
cursor.execute("SELECT id FROM users WHERE username='admin'")
admin_id = cursor.fetchone()[0]

# Get some student ids for poll creators
cursor.execute("SELECT id FROM users WHERE username IN ('student1', 'student6', 'student14')")
creator_ids = [row[0] for row in cursor.fetchall()]

sample_polls = [
    {
        "title": "Best Programming Language for 2026?",
        "description": "Vote for your favorite programming language this year. Which one do you think leads the industry?",
        "poll_type": "single",
        "created_by": creator_ids[0],
        "options": ["Python", "JavaScript", "Rust", "Go", "TypeScript", "Java"]
    },
    {
        "title": "What topics should our next hackathon cover?",
        "description": "Select all the topics you'd like to see at the upcoming college hackathon. Multiple selections allowed!",
        "poll_type": "multiple",
        "created_by": creator_ids[1],
        "options": ["AI/ML", "Web3 & Blockchain", "IoT & Hardware", "Mobile Apps", "Cybersecurity", "Game Development"]
    },
    {
        "title": "Favorite Study Spot on Campus?",
        "description": "Where do you focus best? Cast your vote!",
        "poll_type": "single",
        "created_by": creator_ids[2],
        "options": ["Library", "Cafeteria", "Computer Lab", "Hostel Room", "Garden Area"]
    },
    {
        "title": "Should the college extend library hours?",
        "description": "The library currently closes at 9 PM. Should we push for extended hours during exam season?",
        "poll_type": "single",
        "created_by": admin_id,
        "options": ["Yes, until midnight", "Yes, 24/7 during exams", "No, current hours are fine", "Only on weekends"]
    },
    {
        "title": "Best Elective You've Taken?",
        "description": "Share your experience — which elective was the most valuable?",
        "poll_type": "single",
        "created_by": creator_ids[0],
        "options": ["Machine Learning", "Cyber Security", "Cloud Computing", "Data Science", "AI", "Software Engineering"]
    },
]

for poll in sample_polls:
    cursor.execute(
        "INSERT INTO polls (title, description, poll_type, created_by, is_active) VALUES (?, ?, ?, ?, 1)",
        (poll["title"], poll["description"], poll["poll_type"], poll["created_by"])
    )
    poll_id = cursor.lastrowid
    for opt_text in poll["options"]:
        cursor.execute(
            "INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)",
            (poll_id, opt_text)
        )

# ---------- GENERATE SOME SAMPLE VOTES ----------
cursor.execute("SELECT id FROM polls")
poll_ids = [row[0] for row in cursor.fetchall()]

for poll_id in poll_ids:
    cursor.execute("SELECT id FROM poll_options WHERE poll_id=?", (poll_id,))
    option_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT poll_type FROM polls WHERE id=?", (poll_id,))
    poll_type = cursor.fetchone()[0]

    # Random subset of users vote on each poll
    voters = random.sample(student_ids, random.randint(8, 16))
    for voter_id in voters:
        if poll_type == "multiple":
            # Vote for 1-3 options
            chosen_opts = random.sample(option_ids, random.randint(1, min(3, len(option_ids))))
            for opt_id in chosen_opts:
                cursor.execute(
                    "INSERT INTO votes (poll_id, option_id, user_id) VALUES (?, ?, ?)",
                    (poll_id, opt_id, voter_id)
                )
        else:
            # Single choice — vote for one option
            opt_id = random.choice(option_ids)
            cursor.execute(
                "INSERT INTO votes (poll_id, option_id, user_id) VALUES (?, ?, ?)",
                (poll_id, opt_id, voter_id)
            )

conn.commit()

# Summary
cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM polls")
poll_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM votes")
vote_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM preferences")
pref_count = cursor.fetchone()[0]

conn.close()

print(f"Seed data inserted: {user_count} users, {poll_count} polls, {vote_count} votes, {pref_count} subject preferences")