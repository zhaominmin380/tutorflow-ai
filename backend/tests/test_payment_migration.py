import os
import unittest
from pathlib import Path

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "20260811_0003_payment_billing.py"


class PaymentMigrationTest(unittest.TestCase):
    def test_existing_payment_guards_are_present(self) -> None:
        migration = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("UPDATE payments AS p", migration)
        self.assertIn("student_id IS NULL", migration)
        self.assertIn("amount <= 0", migration)
        self.assertIn("status = 'paid' AND paid_at IS NULL", migration)
        self.assertIn("fk_payments_student_id_students", migration)
        self.assertIn("ck_payments_amount_positive", migration)

    @unittest.skipUnless(
        os.getenv("PAYMENT_MIGRATION_DATABASE_URL"),
        "Set PAYMENT_MIGRATION_DATABASE_URL to a disposable PostgreSQL database to run migration integration tests.",
    )
    def test_existing_postgres_payment_is_backfilled(self) -> None:
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, text

        database_url = os.environ["PAYMENT_MIGRATION_DATABASE_URL"]
        backend_dir = Path(__file__).resolve().parents[1]
        config = Config(str(backend_dir / "alembic.ini"))
        previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = database_url
        engine = create_engine(database_url)

        try:
            command.downgrade(config, "base")
            command.upgrade(config, "20260803_0002")
            with engine.begin() as connection:
                user_id = connection.execute(
                    text(
                        """
                        INSERT INTO users (email, password_hash, name)
                        VALUES ('migration-test@example.com', 'hash', 'Migration Test')
                        RETURNING id
                        """
                    )
                ).scalar_one()
                student_id = connection.execute(
                    text(
                        """
                        INSERT INTO students (user_id, name, is_active)
                        VALUES (:user_id, 'Migration Student', true)
                        RETURNING id
                        """
                    ),
                    {"user_id": user_id},
                ).scalar_one()
                lesson_id = connection.execute(
                    text(
                        """
                        INSERT INTO lessons (student_id, start_time, duration_minutes, status)
                        VALUES (:student_id, '2026-08-01T09:00:00+00:00', 60, 'completed')
                        RETURNING id
                        """
                    ),
                    {"student_id": student_id},
                ).scalar_one()
                connection.execute(
                    text(
                        """
                        INSERT INTO payments (lesson_id, amount, status, paid_at)
                        VALUES (:lesson_id, 1200.00, 'paid', '2026-08-01T10:00:00+00:00')
                        """
                    ),
                    {"lesson_id": lesson_id},
                )

            command.upgrade(config, "head")
            with engine.connect() as connection:
                payment = connection.execute(
                    text("SELECT student_id, status, paid_at FROM payments WHERE lesson_id = :lesson_id"),
                    {"lesson_id": lesson_id},
                ).one()
            self.assertEqual(payment.student_id, student_id)
            self.assertEqual(payment.status, "paid")
            self.assertIsNotNone(payment.paid_at)
        finally:
            command.downgrade(config, "base")
            engine.dispose()
            if previous_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = previous_database_url


if __name__ == "__main__":
    unittest.main()
