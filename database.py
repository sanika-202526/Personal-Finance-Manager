
import sqlite3

# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect("finance.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Create database tables
def create_tables():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL
                CHECK(transaction_type IN ('Income', 'Expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL CHECK(monthly_limit > 0),
            month TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE,
            UNIQUE(user_id, category, month)
        )
    """)

    conn.commit()
    conn.close()

    print("Database and tables created successfully!")


if __name__ == "__main__":
    create_tables()
