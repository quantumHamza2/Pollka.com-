from fastapi import FastAPI, HTTPException
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory polling state (resets on server restart — store in DB if persistence needed)
polling_open = True


import os
import sqlite3

def get_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "pollka.db")

    print("USING DB:", DB_PATH)

    conn = sqlite3.connect(DB_PATH)   # ✅ THIS LINE ONLY
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────── MODELS ────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class PreferenceRequest(BaseModel):
    student_id: int
    preferences: list[int]

class UpdateSeatRequest(BaseModel):
    total_seats: int

class CreateSubjectRequest(BaseModel):
    name: str
    total_seats: int

class EditSubjectRequest(BaseModel):
    name: str
    total_seats: int

class PollingStatusRequest(BaseModel):
    open: bool


# ──────────────── SUBJECTS ────────────────
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
    # Also remove any preferences and allocations for this subject
    cursor.execute("DELETE FROM preferences WHERE subject_id=?", (subject_id,))
    cursor.execute("DELETE FROM allocations WHERE subject_id=?", (subject_id,))
    cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Subject not found")
    conn.commit()
    conn.close()
    return {"status": "deleted"}


# ──────────────── AUTH ────────────────
@app.post("/login")
def login(data: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM students WHERE username=? AND password=?",
        (data.username, data.password)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "status": "success",
            "id": user["id"],
            "name": user["name"],
            "cgpa": user["cgpa"]
        }
    return {"status": "fail"}


# ──────────────── PREFERENCES ────────────────
@app.get("/preferences/{student_id}")
def get_preferences(student_id: int):
    """Returns the student's saved preference subject IDs in order."""
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


# ──────────────── POLLING STATUS ────────────────
@app.get("/polling-status")
def get_polling_status():
    return {"open": polling_open}


@app.post("/polling-status")
def set_polling_status(data: PollingStatusRequest):
    global polling_open
    polling_open = data.open
    return {"open": polling_open}


# ──────────────── ALLOCATION ────────────────
@app.post("/allocate")
def run_allocation():
    """
    Correct preference-order-first CGPA-tiebreaker algorithm:
      Round 1: All students' 1st choice processed, sorted by CGPA desc.
               Top CGPA students get seats first.
      Round 2: Remaining unallocated students' 2nd choice processed, CGPA sorted.
      ...and so on until all rounds are exhausted.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Clear previous allocations
    cursor.execute("DELETE FROM allocations")

    # Load seat capacity
    cursor.execute("SELECT id, total_seats FROM subjects")
    seat_map = {row["id"]: row["total_seats"] for row in cursor.fetchall()}

    # Find max preference depth
    cursor.execute("SELECT MAX(preference_order) as max_ord FROM preferences")
    row = cursor.fetchone()
    max_depth = row["max_ord"] if row["max_ord"] else 0

    allocated_students = set()

    for round_num in range(1, max_depth + 1):
        # Get all (student, subject) pairs for this preference round,
        # for students not yet allocated, sorted by CGPA descending
        cursor.execute("""
            SELECT p.student_id, p.subject_id, s.cgpa
            FROM preferences p
            JOIN students s ON s.id = p.student_id
            WHERE p.preference_order = ?
            ORDER BY s.cgpa DESC
        """, (round_num,))
        round_rows = cursor.fetchall()

        # Group by subject
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

        # Allocate seats per subject (already CGPA-sorted from DB query)
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


# ──────────────── RESULTS ────────────────
@app.get("/results")
def get_results():
    """Returns ALL students with their allocation status (allocated or not)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.id          AS student_id,
            s.name        AS student_name,
            s.cgpa,
            sub.id        AS subject_id,
            sub.name      AS subject_name
        FROM students s
        LEFT JOIN allocations a  ON a.student_id = s.id
        LEFT JOIN subjects sub   ON sub.id = a.subject_id
        ORDER BY s.cgpa DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/result/{student_id}")
def get_student_result(student_id: int):
    """Returns one student's allocation result."""
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