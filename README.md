# Personal Finance & Expense Analytics System

A web-based Personal Finance Management application developed using Python and Flask. It helps users manage their income and expenses, monitor monthly budgets, and understand their spending patterns through visual analytics and financial reports.

## Features

- **User Authentication:** User registration, login and logout.
- **Transaction Management:** Add, view, edit and delete income and expense records.
- **Financial Dashboard:** View total income, total expenses and account balance.
- **Expense Analytics:** Visualize spending patterns using charts.
- **Monthly Budget Management:** Set category-wise budgets and monitor spending.
- **Monthly Financial Reports:** View monthly income, expenses and net savings.
- **CSV Export:** Download transaction records as a CSV file.
- **Database Management:** Store user and financial records using SQLite.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Pandas
- Matplotlib

## Project Structure

```text
PersonalFinanceSystem/
│
├── app.py
├── database.py
├── finance.db
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transactions.html
│   ├── budget.html
│   └── reports.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── images/
│
└── README.md
```

## Installation and Setup

1. Clone or download this repository.
2. Open the project folder in VS Code.
3. Create a virtual environment:

```bash
python -m venv .venv
```

4. Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

5. Install the required libraries:

```bash
pip install flask pandas matplotlib
```

6. Run the application:

```bash
python app.py
```

7. Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## Project Objective

The objective of this project is to develop a simple and user-friendly financial management system that helps individuals track their daily transactions, manage budgets and analyze their financial activities.

## Future Enhancements

- Savings goal tracking.
- PDF financial report generation.
- Improved data visualization.
- Expense prediction and financial insights.

---

**Developed as a Python Web Development Project.**