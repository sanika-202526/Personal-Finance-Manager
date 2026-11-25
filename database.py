
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


# Connect to Neon PostgreSQL database
def get_db_connection():

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured!")

    conn = psycopg.connect(database_url)

    return conn


# Create database tables
def create_tables():

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL
                    CHECK(transaction_type IN ('Income', 'Expense')),
                amount DOUBLE PRECISION NOT NULL
                    CHECK(amount > 0),
                category TEXT NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
        """)

        # Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                monthly_limit DOUBLE PRECISION NOT NULL
                    CHECK(monthly_limit > 0),
                month TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,
                UNIQUE(user_id, category, month)
            )
        """)

        conn.commit()
        print("PostgreSQL database and tables created successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
