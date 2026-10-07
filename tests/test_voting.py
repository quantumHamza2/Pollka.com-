import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import main
from fastapi import HTTPException

class VotingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "db.sqlite"
        connection = sqlite3.connect(self.path)
        connection.executescript("""CREATE TABLE users(id INTEGER PRIMARY KEY, role TEXT);
        CREATE TABLE polls(id INTEGER PRIMARY KEY, created_by INTEGER, is_active INTEGER, poll_type TEXT);
        CREATE TABLE poll_options(id INTEGER PRIMARY KEY, poll_id INTEGER);
        CREATE TABLE votes(poll_id INTEGER, option_id INTEGER, user_id INTEGER, rank_order INTEGER);
        INSERT INTO users VALUES(1, 'user'),(2, 'user');
        INSERT INTO polls VALUES(1,1,1,'multiple');
        INSERT INTO poll_options VALUES(10,1),(11,1);
        INSERT INTO votes VALUES(1,10,1,1);""")
        connection.close()
        def get_db():
            conn = sqlite3.connect(self.path); conn.row_factory = sqlite3.Row; return conn
        self.patch = patch.object(main, "get_db", get_db); self.patch.start()
    def tearDown(self): self.patch.stop(); self.temp.cleanup()
    def test_invalid_vote_preserves_existing_vote(self):
        for choices in ([], [10,10], [99]):
            with self.assertRaises(HTTPException):
                main.cast_vote(1, main.VoteRequest(user_id=1, option_ids=choices))
        with sqlite3.connect(self.path) as conn:
            self.assertEqual(conn.execute("SELECT option_id FROM votes").fetchall(), [(10,)])
    def test_replace_vote(self):
        main.cast_vote(1, main.VoteRequest(user_id=1, option_ids=[11]))
        with sqlite3.connect(self.path) as conn:
            self.assertEqual(conn.execute("SELECT option_id FROM votes").fetchall(), [(11,)])
    def test_nonowner_cannot_reopen(self):
        with self.assertRaises(HTTPException) as raised: main.reopen_poll(1, 2)
        self.assertEqual(raised.exception.status_code,403)
