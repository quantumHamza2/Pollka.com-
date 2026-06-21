import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "pollka.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ──────────────── MODELS ────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str
    email: Optional[str] = None

class CreatePollRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    poll_type: str = "single"
    options: list[str]

class VoteRequest(BaseModel):
    user_id: int
    option_ids: list[int]

class PreferenceRequest(BaseModel):
    student_id: int
    preferences: list[int]

class CreateSubjectRequest(BaseModel):
    name: str
    total_seats: int

class EditSubjectRequest(BaseModel):
    name: str
    total_seats: int

class PollingStatusRequest(BaseModel):
    open: bool


# ══════════════════════════════════════
#  AUTH
# ══════════════════════════════════════
@app.post("/register")
def register(data: RegisterRequest):
    conn = get_db()
    cursor = conn.cursor()
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username=?", (data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already taken")
    cursor.execute(
        "INSERT INTO users (username, password, display_name, email, role) VALUES (?, ?, ?, ?, 'user')",
        (data.username, data.password, data.display_name, data.email)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "success", "id": new_id, "name": data.display_name}


@app.post("/login")
def login(data: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (data.username, data.password)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "status": "success",
            "id": user["id"],
            "name": user["display_name"],
            "role": user["role"],
            "cgpa": user["cgpa"],
            "email": user["email"]
        }
    return {"status": "fail"}


# ══════════════════════════════════════
#  POLLS — CRUD
# ══════════════════════════════════════
@app.get("/polls")
def get_polls():
    """List all polls with vote counts and creator info."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, u.display_name AS creator_name,
               (SELECT COUNT(DISTINCT v.user_id) FROM votes v WHERE v.poll_id = p.id) AS total_voters
        FROM polls p
        JOIN users u ON u.id = p.created_by
        ORDER BY p.created_at DESC
    """)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        poll = dict(row)
        # Get options with vote counts
        cursor.execute("""
            SELECT po.id, po.option_text,
                   (SELECT COUNT(*) FROM votes v WHERE v.option_id = po.id) AS vote_count
            FROM poll_options po WHERE po.poll_id = ?
            ORDER BY po.id
        """, (poll["id"],))
        poll["options"] = [dict(o) for o in cursor.fetchall()]
        result.append(poll)
    conn.close()
    return result


@app.post("/polls")
def create_poll(data: CreatePollRequest, user_id: int):
    if len(data.options) < 2:
        raise HTTPException(status_code=400, detail="Poll needs at least 2 options")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO polls (title, description, poll_type, created_by) VALUES (?, ?, ?, ?)",
        (data.title, data.description, data.poll_type, user_id)
    )
    poll_id = cursor.lastrowid
    for opt in data.options:
        cursor.execute(
            "INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)",
            (poll_id, opt.strip())
        )
    conn.commit()
    conn.close()
    return {"status": "created", "poll_id": poll_id}


@app.get("/polls/{poll_id}")
def get_poll(poll_id: int):
    """Get poll details with options, votes, and whether each user has voted."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, u.display_name AS creator_name
        FROM polls p
        JOIN users u ON u.id = p.created_by
        WHERE p.id = ?
    """, (poll_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    poll = dict(row)

    # Get options with vote counts
    cursor.execute("""
        SELECT po.id, po.option_text,
               (SELECT COUNT(*) FROM votes v WHERE v.option_id = po.id) AS vote_count
        FROM poll_options po WHERE po.poll_id = ?
        ORDER BY po.id
    """, (poll_id,))
    poll["options"] = [dict(o) for o in cursor.fetchall()]

    # Total unique voters
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM votes WHERE poll_id=?", (poll_id,))
    poll["total_voters"] = cursor.fetchone()[0]

    conn.close()
    return poll


@app.delete("/polls/{poll_id}")
def delete_poll(poll_id: int, user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT created_by FROM polls WHERE id=?", (poll_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    # Check ownership (owner or admin)
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    user_row = cursor.fetchone()
    if row["created_by"] != user_id and (not user_row or user_row["role"] != "admin"):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor.execute("DELETE FROM polls WHERE id=?", (poll_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@app.post("/polls/{poll_id}/close")
def close_poll(poll_id: int, user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT created_by FROM polls WHERE id=?", (poll_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    user_row = cursor.fetchone()
    if row["created_by"] != user_id and (not user_row or user_row["role"] != "admin"):
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor.execute("UPDATE polls SET is_active=0 WHERE id=?", (poll_id,))
    conn.commit()
    conn.close()
    return {"status": "closed"}


@app.post("/polls/{poll_id}/reopen")
def reopen_poll(poll_id: int, user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT created_by FROM polls WHERE id=?", (poll_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    cursor.execute("UPDATE polls SET is_active=1 WHERE id=?", (poll_id,))
    conn.commit()
    conn.close()
    return {"status": "reopened"}


# ══════════════════════════════════════
#  VOTING
# ══════════════════════════════════════
@app.post("/polls/{poll_id}/vote")
def cast_vote(poll_id: int, data: VoteRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Check poll exists and is active
    cursor.execute("SELECT * FROM polls WHERE id=?", (poll_id,))
    poll = cursor.fetchone()
    if not poll:
        conn.close()
        raise HTTPException(status_code=404, detail="Poll not found")
    if not poll["is_active"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Poll is closed")

    # Remove previous votes by this user on this poll
    cursor.execute("DELETE FROM votes WHERE poll_id=? AND user_id=?", (poll_id, data.user_id))

    # Validate options belong to this poll
    for opt_id in data.option_ids:
        cursor.execute("SELECT id FROM poll_options WHERE id=? AND poll_id=?", (opt_id, poll_id))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail=f"Option {opt_id} does not belong to this poll")

    # Single choice — only 1 option allowed
    if poll["poll_type"] == "single" and len(data.option_ids) != 1:
        conn.close()
        raise HTTPException(status_code=400, detail="Single-choice poll: select exactly one option")

    for i, opt_id in enumerate(data.option_ids):
        cursor.execute(
            "INSERT INTO votes (poll_id, option_id, user_id, rank_order) VALUES (?, ?, ?, ?)",
            (poll_id, opt_id, data.user_id, i + 1)
        )

    conn.commit()
    conn.close()
    return {"status": "voted"}


@app.get("/polls/{poll_id}/my-vote/{user_id}")
def get_my_vote(poll_id: int, user_id: int):
    """Get the current user's vote(s) for a specific poll."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT option_id FROM votes WHERE poll_id=? AND user_id=? ORDER BY rank_order",
        (poll_id, user_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row["option_id"] for row in rows]


@app.get("/my-polls/{user_id}")
def get_my_polls(user_id: int):
    """Get polls created by a specific user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
               (SELECT COUNT(DISTINCT v.user_id) FROM votes v WHERE v.poll_id = p.id) AS total_voters
        FROM polls p
        WHERE p.created_by = ?
        ORDER BY p.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        poll = dict(row)
        cursor.execute("""
            SELECT po.id, po.option_text,
                   (SELECT COUNT(*) FROM votes v WHERE v.option_id = po.id) AS vote_count
            FROM poll_options po WHERE po.poll_id = ?
            ORDER BY po.id
        """, (poll["id"],))
        poll["options"] = [dict(o) for o in cursor.fetchall()]
        result.append(poll)
    conn.close()
    return result


# ══════════════════════════════════════
#  SUBJECT ALLOCATION (preserved)
# ══════════════════════════════════════
@app.get("/subjects")
def get_subjects():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/subjects")
def create_subject(data: CreateSubjectRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subjects (name, total_seats) VALUES (?, ?)",
        (data.name, data.total_seats)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "created", "id": new_id}


@app.put("/subjects/{subject_id}")
def update_subject(subject_id: int, data: EditSubjectRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE subjects SET name=?, total_seats=? WHERE id=?",
        (data.name, data.total_seats, subject_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Subject not found")
    conn.commit()
    conn.close()
    return {"status": "updated"}


@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM preferences WHERE subject_id=?", (subject_id,))
    cursor.execute("DELETE FROM allocations WHERE subject_id=?", (subject_id,))
    cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Subject not found")
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@app.get("/preferences/{student_id}")
def get_preferences(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT subject_id FROM preferences WHERE student_id=? ORDER BY preference_order ASC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row["subject_id"] for row in rows]


@app.post("/preferences")
def save_preferences(data: PreferenceRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM preferences WHERE student_id=?", (data.student_id,))
    for i, subject_id in enumerate(data.preferences):
        cursor.execute(
            "INSERT INTO preferences (student_id, subject_id, preference_order) VALUES (?, ?, ?)",
            (data.student_id, subject_id, i + 1)
        )
    conn.commit()
    conn.close()
    return {"status": "saved"}


@app.get("/polling-status")
def get_polling_status():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='polling_open'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"open": row["value"] == "true"}
    return {"open": True}


@app.post("/polling-status")
def set_polling_status(data: PollingStatusRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('polling_open', ?)",
        ("true" if data.open else "false",)
    )
    conn.commit()
    conn.close()
    return {"open": data.open}


@app.post("/allocate")
def run_allocation():
    """
    Preference-order-first CGPA-tiebreaker allocation algorithm.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM allocations")

    cursor.execute("SELECT id, total_seats FROM subjects")
    seat_map = {row["id"]: row["total_seats"] for row in cursor.fetchall()}

    cursor.execute("SELECT MAX(preference_order) as max_ord FROM preferences")
    row = cursor.fetchone()
    max_depth = row["max_ord"] if row["max_ord"] else 0

    allocated_students = set()

    for round_num in range(1, max_depth + 1):
        cursor.execute("""
            SELECT p.student_id, p.subject_id, u.cgpa
            FROM preferences p
            JOIN users u ON u.id = p.student_id
            WHERE p.preference_order = ?
            ORDER BY u.cgpa DESC
        """, (round_num,))
        round_rows = cursor.fetchall()

        by_subject = {}
        for row in round_rows:
            if row["student_id"] in allocated_students:
                continue
            sid = row["subject_id"]
            if sid not in by_subject:
                by_subject[sid] = []
            by_subject[sid].append({
                "student_id": row["student_id"],
                "cgpa": row["cgpa"]
            })

        for subject_id, students in by_subject.items():
            available = seat_map.get(subject_id, 0)
            if available <= 0:
                continue
            for student in students:
                if available <= 0:
                    break
                if student["student_id"] not in allocated_students:
                    cursor.execute(
                        "INSERT INTO allocations (student_id, subject_id) VALUES (?, ?)",
                        (student["student_id"], subject_id)
                    )
                    allocated_students.add(student["student_id"])
                    seat_map[subject_id] -= 1
                    available -= 1

    conn.commit()
    conn.close()
    return {"status": "allocation complete"}


@app.get("/results")
def get_results():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.id          AS student_id,
            u.display_name AS student_name,
            u.cgpa,
            sub.id        AS subject_id,
            sub.name      AS subject_name
        FROM users u
        LEFT JOIN allocations a  ON a.student_id = u.id
        LEFT JOIN subjects sub   ON sub.id = a.subject_id
        WHERE u.role = 'user'
        ORDER BY u.cgpa DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/result/{student_id}")
def get_student_result(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sub.id AS subject_id, sub.name AS subject_name
        FROM allocations a
        JOIN subjects sub ON sub.id = a.subject_id
        WHERE a.student_id = ?
    """, (student_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"allocated": True, "subject_id": row["subject_id"], "subject_name": row["subject_name"]}
    return {"allocated": False}


@app.post("/clear-allocations")
def clear_allocations():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM allocations")
    conn.commit()
    conn.close()
    return {"status": "cleared"}