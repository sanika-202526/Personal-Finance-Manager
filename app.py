from dotenv import load_dotenv
import csv
import io
import os
import pandas as pd
import matplotlib

from datetime import date, datetime

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import create_tables, get_db_connection

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is not configured!")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

# Create database tables when the application starts
create_tables()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# User registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not username or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, (username, email, password_hash))

            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))

        except Exception:
            conn.rollback()
            flash("Email already registered or registration failed.")

        finally:
            conn.close()

    return render_template("register.html")


# User login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = %s", (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):

            session.clear()
            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# Financial Analytics Dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_type, amount, category, date
        FROM transactions
        WHERE user_id = %s
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(
        rows,
        columns=["transaction_type", "amount", "category", "date"]
    )

    # Calculate financial summary
    total_income = df.loc[
        df["transaction_type"] == "Income", "amount"
    ].sum()

    total_expenses = df.loc[
        df["transaction_type"] == "Expense", "amount"
    ].sum()

    balance = total_income - total_expenses

    # Prepare chart folder
    image_folder = os.path.join(
        app.root_path, "static", "images"
    )
    os.makedirs(image_folder, exist_ok=True)

    user_id = session["user_id"]

    expense_chart = None
    monthly_chart = None

    # Expense category pie chart
    expenses = df[df["transaction_type"] == "Expense"]

    if not expenses.empty:

        category_data = expenses.groupby("category")["amount"].sum()

        plt.figure(figsize=(7, 5))
        plt.pie(
            category_data,
            labels=category_data.index,
            autopct="%1.1f%%",
            startangle=90
        )

        plt.title("Expense Distribution by Category")
        plt.tight_layout()

        chart_name = f"expense_chart_{user_id}.png"
        plt.savefig(os.path.join(image_folder, chart_name))
        plt.close()

        expense_chart = chart_name

    # Monthly income vs expense bar chart
    if not df.empty:

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        if not df.empty:

            df["month"] = df["date"].dt.to_period("M").astype(str)

            monthly_data = df.pivot_table(
                index="month",
                columns="transaction_type",
                values="amount",
                aggfunc="sum",
                fill_value=0
            )

            monthly_data = monthly_data.reindex(
                columns=["Income", "Expense"],
                fill_value=0
            )

            plt.figure(figsize=(9, 5))
            monthly_data.plot(kind="bar", ax=plt.gca())

            plt.title("Monthly Income vs Expenses")
            plt.xlabel("Month")
            plt.ylabel("Amount (₹)")
            plt.xticks(rotation=45)
            plt.tight_layout()

            chart_name = f"monthly_chart_{user_id}.png"
            plt.savefig(os.path.join(image_folder, chart_name))
            plt.close()

            monthly_chart = chart_name

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        expense_chart=expense_chart,
        monthly_chart=monthly_chart
    )


# View all transactions
@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_id, transaction_type, amount,
               category, description, date
        FROM transactions
        WHERE user_id = %s
        ORDER BY date DESC, transaction_id DESC
    """, (session["user_id"],))

    all_transactions = cursor.fetchall()
    conn.close()

    return render_template(
        "transactions.html",
        transactions=all_transactions
    )


# Add a new transaction
@app.route("/add_transaction", methods=["POST"])
def add_transaction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    transaction_type = request.form["transaction_type"]
    amount = request.form["amount"]
    category = request.form["category"]
    description = request.form.get("description", "").strip()
    transaction_date = request.form["date"]

    try:
        amount = float(amount)
        transaction_date = datetime.strptime(
            transaction_date, "%Y-%m-%d"
        ).date()

        if amount <= 0:
            flash("Amount must be greater than zero.")
            return redirect(url_for("transactions"))

        if transaction_type not in ["Income", "Expense"]:
            flash("Invalid transaction type.")
            return redirect(url_for("transactions"))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO transactions
                (user_id, transaction_type, amount,
                 category, description, date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                session["user_id"],
                transaction_type,
                amount,
                category,
                description,
                transaction_date
            ))

            conn.commit()
            flash("Transaction added successfully!")

        except Exception:
            conn.rollback()
            flash("Could not add transaction. Please check the details.")

        finally:
            conn.close()

    except ValueError:
        flash("Please enter a valid amount and date.")

    return redirect(url_for("transactions"))


# Edit an existing transaction
@app.route("/edit_transaction/<int:transaction_id>",
           methods=["GET", "POST"])
def edit_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        transaction_type = request.form["transaction_type"]
        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form.get("description", "").strip()
        transaction_date = request.form["date"]

        try:
            amount = float(amount)
            transaction_date = datetime.strptime(
                transaction_date, "%Y-%m-%d"
            ).date()

            if amount <= 0 or transaction_type not in ["Income", "Expense"]:
                flash("Please enter valid transaction details.")
            else:
                cursor.execute("""
                    UPDATE transactions
                    SET transaction_type = %s, amount = %s,
                        category = %s, description = %s, date = %s
                    WHERE transaction_id = %s AND user_id = %s
                """, (
                    transaction_type, amount, category,
                    description, transaction_date, transaction_id,
                    session["user_id"]
                ))

                if cursor.rowcount == 1:
                    conn.commit()
                    flash("Transaction updated successfully!")
                else:
                    flash("Transaction not found.")

                conn.close()
                return redirect(url_for("transactions"))

        except ValueError:
            flash("Please enter a valid amount and date.")

    cursor.execute("""
        SELECT transaction_id, transaction_type, amount,
               category, description, date
        FROM transactions
        WHERE transaction_id = %s AND user_id = %s
    """, (transaction_id, session["user_id"]))

    transaction = cursor.fetchone()
    conn.close()

    if transaction is None:
        flash("Transaction not found.")
        return redirect(url_for("transactions"))

    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )


# Delete a transaction
@app.route("/delete_transaction/<int:transaction_id>",
           methods=["POST"])
def delete_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE transaction_id = %s AND user_id = %s
    """, (transaction_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Transaction deleted successfully!")

    return redirect(url_for("transactions"))


# Budget Management Page
@app.route("/budget", methods=["GET", "POST"])
def budget():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    current_month = date.today().strftime("%Y-%m")

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        category = request.form["category"]
        monthly_limit = request.form["monthly_limit"]

        try:
            monthly_limit = float(monthly_limit)

            if monthly_limit <= 0:
                flash("Budget must be greater than zero.")
            else:
                cursor.execute("""
                    INSERT INTO budgets
                    (user_id, category, monthly_limit, month)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(user_id, category, month)
                    DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
                """, (user_id, category, monthly_limit, current_month))

                conn.commit()
                flash("Budget saved successfully!")

        except ValueError:
            flash("Please enter a valid budget amount.")

        finally:
            conn.close()

        return redirect(url_for("budget"))

    cursor.execute("""
        SELECT b.category, b.monthly_limit,
               COALESCE(SUM(t.amount), 0) AS spent
        FROM budgets b
        LEFT JOIN transactions t
            ON b.user_id = t.user_id
            AND b.category = t.category
            AND t.transaction_type = 'Expense'
            AND TO_CHAR(t.date, 'YYYY-MM') = b.month
        WHERE b.user_id = %s AND b.month = %s
        GROUP BY b.budget_id
        ORDER BY b.category
    """, (user_id, current_month))

    budget_data = cursor.fetchall()
    conn.close()

    return render_template(
        "budget.html",
        budgets=budget_data,
        current_month=current_month
    )


# Export transactions as CSV
@app.route("/export_csv")
def export_csv():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_type, amount, category, description, date
        FROM transactions
        WHERE user_id = %s
        ORDER BY date DESC
    """, (session["user_id"],))

    transactions = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Transaction Type",
        "Amount",
        "Category",
        "Description",
        "Date"
    ])

    for transaction in transactions:
        writer.writerow(transaction)

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = (
        "attachment; filename=transactions.csv"
    )

    return response


# Monthly financial reports
@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            TO_CHAR(date, 'YYYY-MM') AS month,
            SUM(CASE
                WHEN transaction_type = 'Income' THEN amount
                ELSE 0
            END) AS total_income,
            SUM(CASE
                WHEN transaction_type = 'Expense' THEN amount
                ELSE 0
            END) AS total_expenses
        FROM transactions
        WHERE user_id = %s
        GROUP BY TO_CHAR(date, 'YYYY-MM')
        ORDER BY month DESC
    """, (session["user_id"],))

    monthly_data = cursor.fetchall()
    conn.close()

    return render_template(
        "reports.html",
        monthly_data=monthly_data
    )


# Logout
@app.route("/logout")
def logout():

    session.clear()
    flash("You have logged out successfully.")

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
