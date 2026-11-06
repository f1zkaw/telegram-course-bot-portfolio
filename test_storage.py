import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

from storage import Storage
from services import daily_available, valid_checkout


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Storage(Path(self.temp.name) / "test.db")
        self.db.init_db()
        self.db.touch_user(123, "demo_user")

    def tearDown(self):
        self.temp.cleanup()

    def test_user_created_without_access(self):
        user = self.db.get_user(123)
        self.assertFalse(user["has_access"])
        self.assertEqual(user["current_lesson"], 0)
        self.assertIsNone(self.db.get_user(999))

    def test_demo_access_and_lesson_progress(self):
        self.db.set_access(123)
        self.db.set_lesson(123, 2)
        user = self.db.get_user(123)
        self.assertTrue(user["has_access"])
        self.assertEqual(user["current_lesson"], 2)

    def test_idempotent_payment(self):
        self.assertTrue(self.db.record_payment(123, 10000, "RUB", "test-charge-1"))
        self.assertFalse(self.db.record_payment(123, 10000, "RUB", "test-charge-1"))
        self.assertTrue(self.db.get_user(123)["has_access"])

    def test_request_saved(self):
        self.db.save_request(123, "Public demo question")
        with self.db._connect() as db:
            value = db.execute("SELECT content FROM requests").fetchone()[0]
        self.assertEqual(value, "Public demo question")

    def test_last_daily_is_stored(self):
        time = datetime.now(timezone.utc).isoformat()
        self.db.set_last_daily(123, time)
        self.assertEqual(self.db.get_user(123)["last_daily_message_at"], time)


class LogicTests(unittest.TestCase):
    def test_daily_cooldown(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertTrue(daily_available(None, now)[0])
        self.assertFalse(daily_available((now - timedelta(hours=23)).isoformat(), now)[0])
        self.assertTrue(daily_available((now - timedelta(hours=24)).isoformat(), now)[0])

    def test_invoice_validation(self):
        self.assertTrue(valid_checkout("demo_course_123", 123, 10000, "RUB", 10000, "RUB"))
        self.assertFalse(valid_checkout("demo_course_999", 123, 10000, "RUB", 10000, "RUB"))
        self.assertFalse(valid_checkout("demo_course_123", 123, 1, "RUB", 10000, "RUB"))
        self.assertFalse(valid_checkout("demo_course_123", 123, 10000, "USD", 10000, "RUB"))


if __name__ == "__main__":
    unittest.main()
