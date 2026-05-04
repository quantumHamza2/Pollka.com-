import sqlite3
import random

conn = sqlite3.connect("pollka.db")
cursor = conn.cursor()

# ---------- CLEAR OLD DATA ----------
cursor.execute("DELETE FROM students")
cursor.execute("DELETE FROM subjects")
cursor.execute("DELETE FROM preferences")
cursor.execute("DELETE FROM allocations")

# ---------- STUDENTS (20) ----------
students = [
    ("student1", "password", "Rishabh Jha", 9.7),
    ("student2", "password", "Priya Sharma", 8.5),
    ("student3", "password", "Arjun Mehta", 7.3),
    ("student4", "password", "Neha Kapoor", 9.2),
    ("student5", "password", "Rahul Verma", 8.9),
    ("student6", "password", "Ananya Iyer", 9.5),
    ("student7", "password", "Karan Malhotra", 7.8),
    ("student8", "password", "Sneha Reddy", 8.2),
    ("student9", "password", "Vikram Singh", 6.9),
    ("student10", "password", "Meera Nair", 9.1),
    ("student11", "password", "Aditya Gupta", 8.0),
    ("student12", "password", "Pooja Sharma", 7.5),
    ("student13", "password", "Rohan Das", 8.7),
    ("student14", "password", "Ishita Jain", 9.3),
    ("student15", "password", "Yash Patel", 7.9),
    ("student16", "password", "Simran Kaur", 8.4),
    ("student17", "password", "Arnav Mishra", 9.6),
    ("student18", "password", "Tanya Bose", 8.1),
    ("student19", "password", "Kabir Khan", 7.2),
    ("student20", "password", "Divya Menon", 9.0),
]

cursor.executemany(
    "INSERT INTO students (username, password, name, cgpa) VALUES (?, ?, ?, ?)",
    students
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

# ---------- GENERATE RANDOM PREFERENCES ----------
cursor.execute("SELECT id FROM students")
student_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT id FROM subjects")
subject_ids = [row[0] for row in cursor.fetchall()]

preferences = []


conn.commit()
conn.close()

print("Realistic seed data inserted successfully")