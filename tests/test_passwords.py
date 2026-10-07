import unittest
from passwords import hash_password, verify_password
class PasswordTests(unittest.TestCase):
    def test_hash_and_wrong_password(self):
        value = hash_password("test-password")
        self.assertNotEqual(value, "test-password")
        self.assertTrue(verify_password("test-password", value))
        self.assertFalse(verify_password("wrong", value))
    def test_legacy_and_malformed(self):
        self.assertTrue(verify_password("demo", "demo"))
        self.assertFalse(verify_password("demo", "pbkdf2_sha256$broken"))
