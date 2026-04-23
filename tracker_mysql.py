import mysql.connector
from mysql.connector import Error
import hashlib
import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
import random

# MySQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Db123@#**',
    'database': 'grp_demo'
}

DATE_FORMAT = "%Y-%m-%d"

# Categories with Icons
EXPENSE_CATEGORIES = [
    {"name": "Food", "icon": "🍔", "color": "#FF6B6B"},
    {"name": "Transport", "icon": "🚗", "color": "#4ECDC4"},
    {"name": "Shopping", "icon": "🛍️", "color": "#45B7D1"},
    {"name": "Bills", "icon": "💸", "color": "#96CEB4"},
    {"name": "Entertainment", "icon": "🎬", "color": "#FFEAA7"},
    {"name": "Healthcare", "icon": "🏥", "color": "#DDA0DD"},
    {"name": "Education", "icon": "📚", "color": "#98D8C8"},
    {"name": "Other", "icon": "📦", "color": "#B0BEC5"}
]

INCOME_CATEGORIES = [
    {"name": "Salary", "icon": "💰", "color": "#27ae60"},
    {"name": "Freelance", "icon": "💻", "color": "#3498db"},
    {"name": "Investment", "icon": "📈", "color": "#f39c12"},
    {"name": "Gift", "icon": "🎁", "color": "#e74c3c"},
    {"name": "Other", "icon": "📦", "color": "#95a5a6"}
]

# Motivational Quotes
MOTIVATIONAL_QUOTES = [
    "💰 Save money today for a better tomorrow!",
    "🎯 Every penny saved is a step towards freedom!",
    "📊 Track your expenses, track your success!",
    "💪 Small savings today, big wealth tomorrow!",
    "🌟 Financial freedom starts with one expense at a time!",
    "🎉 Your future self will thank you for saving today!",
    "💡 Smart spending = Smart saving!",
    "🏆 You're doing great! Keep tracking your expenses!"
]

def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize the MySQL database with required tables"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        # Create users table with additional fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                weekly_budget DECIMAL(10, 2) DEFAULT 0,
                savings_goal DECIMAL(10, 2) DEFAULT 0,
                theme VARCHAR(20) DEFAULT 'light',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create expenses table with category
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                category_icon VARCHAR(10),
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create income table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incomes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                category_icon VARCHAR(10),
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create budget settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                weekly_budget DECIMAL(10, 2) DEFAULT 0,
                monthly_budget DECIMAL(10, 2) DEFAULT 0,
                savings_goal DECIMAL(10, 2) DEFAULT 0,
                savings_goal_name VARCHAR(200),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        connection.commit()
        print("✓ Database tables initialized")
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        connection.close()

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if plain password matches hashed password"""
    return hash_password(plain_password) == hashed_password

def get_user_by_username(username: str):
    """Get user from database by username"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, password, weekly_budget, savings_goal, theme FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_user_by_email(email: str):
    """Get user from database by email"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, password, weekly_budget, savings_goal, theme FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def user_exists(username: str, email: str = None) -> bool:
    """Check if username or email already exists"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        if email:
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        else:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        
        result = cursor.fetchone()
        return result is not None
    except Error as e:
        print(f"Error checking user existence: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def register_user_db(username: str, email: str, password: str) -> bool:
    """Register a new user in the database"""
    if user_exists(username, email):
        return False
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        connection.commit()
        
        # Get the new user's ID
        user_id = cursor.lastrowid
        
        # Create budget settings for new user
        cursor.execute(
            "INSERT INTO budget_settings (user_id) VALUES (%s)",
            (user_id,)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error registering user: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def login_user_db(username_or_email: str, password: str):
    """Authenticate user login by username or email"""
    # Try username first
    user = get_user_by_username(username_or_email)
    
    # If not found, try email
    if not user:
        user = get_user_by_email(username_or_email)
    
    # Verify password
    if user:
        stored_password = user[3]  # password is at index 3
        if verify_password(password, stored_password):
            return (user[0], user[1], user[2])  # Return (id, username, email)
    
    return None

def get_user_expenses(user_id: int):
    """Get all expenses for a user"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, description, amount, category, category_icon, date FROM expenses WHERE user_id = %s ORDER BY date DESC",
            (user_id,)
        )
        expenses = cursor.fetchall()
        return [{"id": e[0], "description": e[1], "amount": float(e[2]), "category": e[3], "icon": e[4], "date": e[5]} for e in expenses]
    except Error as e:
        print(f"Error fetching expenses: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_user_incomes(user_id: int):
    """Get all incomes for a user"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, description, amount, category, category_icon, date FROM incomes WHERE user_id = %s ORDER BY date DESC",
            (user_id,)
        )
        incomes = cursor.fetchall()
        return [{"id": i[0], "description": i[1], "amount": float(i[2]), "category": i[3], "icon": i[4], "date": i[5]} for i in incomes]
    except Error as e:
        print(f"Error fetching incomes: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def add_expense_db(user_id: int, description: str, amount: float, category: str, category_icon: str, exp_date: str) -> bool:
    """Add a new expense to the database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, description, amount, category, category_icon, date) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, description, round(amount, 2), category, category_icon, exp_date)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error adding expense: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_income_db(user_id: int, description: str, amount: float, category: str, category_icon: str, inc_date: str) -> bool:
    """Add a new income to the database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO incomes (user_id, description, amount, category, category_icon, date) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, description, round(amount, 2), category, category_icon, inc_date)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error adding income: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_expense_db(expense_id: int) -> bool:
    """Delete an expense from the database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"Error deleting expense: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_income_db(income_id: int) -> bool:
    """Delete an income from the database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM incomes WHERE id = %s", (income_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"Error deleting income: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def update_budget_settings(user_id: int, weekly_budget: float = None, monthly_budget: float = None, savings_goal: float = None, savings_goal_name: str = None):
    """Update budget settings for user"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if record exists
        cursor.execute("SELECT id FROM budget_settings WHERE user_id = %s", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            updates = []
            params = []
            if weekly_budget is not None:
                updates.append("weekly_budget = %s")
                params.append(weekly_budget)
            if monthly_budget is not None:
                updates.append("monthly_budget = %s")
                params.append(monthly_budget)
            if savings_goal is not None:
                updates.append("savings_goal = %s")
                params.append(savings_goal)
            if savings_goal_name is not None:
                updates.append("savings_goal_name = %s")
                params.append(savings_goal_name)
            
            if updates:
                params.append(user_id)
                cursor.execute(f"UPDATE budget_settings SET {', '.join(updates)} WHERE user_id = %s", params)
        else:
            cursor.execute(
                "INSERT INTO budget_settings (user_id, weekly_budget, monthly_budget, savings_goal, savings_goal_name) VALUES (%s, %s, %s, %s, %s)",
                (user_id, weekly_budget or 0, monthly_budget or 0, savings_goal or 0, savings_goal_name or "")
            )
        
        # Also update users table for backward compatibility
        if weekly_budget is not None:
            cursor.execute("UPDATE users SET weekly_budget = %s WHERE id = %s", (weekly_budget, user_id))
        if savings_goal is not None:
            cursor.execute("UPDATE users SET savings_goal = %s WHERE id = %s", (savings_goal, user_id))
        
        connection.commit()
        return True
    except Error as e:
        print(f"Error updating budget settings: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_budget_settings(user_id: int):
    """Get budget settings for user"""
    connection = get_db_connection()
    if not connection:
        return {"weekly_budget": 0, "monthly_budget": 0, "savings_goal": 0, "savings_goal_name": ""}
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT weekly_budget, monthly_budget, savings_goal, savings_goal_name FROM budget_settings WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            return {"weekly_budget": float(result[0]), "monthly_budget": float(result[1]), 
                    "savings_goal": float(result[2]), "savings_goal_name": result[3] or ""}
        return {"weekly_budget": 0, "monthly_budget": 0, "savings_goal": 0, "savings_goal_name": ""}
    except Error as e:
        print(f"Error fetching budget settings: {e}")
        return {"weekly_budget": 0, "monthly_budget": 0, "savings_goal": 0, "savings_goal_name": ""}
    finally:
        cursor.close()
        connection.close()

def parse_date(date_str: str) -> date:
    try:
        return datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"Please enter a date in {DATE_FORMAT} format.")

def get_week_range(target_date: date) -> tuple:
    start = target_date - timedelta(days=target_date.weekday())
    end = start + timedelta(days=6)
    return start, end

def get_month_range(target_date: date) -> tuple:
    start = target_date.replace(day=1)
    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)
    end = next_month - timedelta(days=1)
    return start, end

def get_last_month_range(today_date: date) -> tuple:
    if today_date.month == 1:
        last_month_date = today_date.replace(year=today_date.year - 1, month=12, day=1)
    else:
        last_month_date = today_date.replace(month=today_date.month - 1, day=1)
    return get_month_range(last_month_date)

def filter_expenses(expenses, start_date: date, end_date: date):
    filtered = []
    for expense in expenses:
        expense_date = parse_date(expense["date"])
        if start_date <= expense_date <= end_date:
            filtered.append(expense)
    return filtered

def calculate_savings(expenses, incomes):
    """Calculate total savings (income - expense)"""
    total_income = sum(i["amount"] for i in incomes)
    total_expense = sum(e["amount"] for e in expenses)
    return total_income - total_expense

def create_category_selection_dialog(parent, title, categories, callback):
    """Create a dialog for category selection"""
    dialog = Toplevel(parent)
    dialog.title(title)
    dialog.geometry("400x300")
    dialog.transient(parent)
    dialog.grab_set()
    
    Label(dialog, text="Select Category", font=("Arial", 14, "bold")).pack(pady=10)
    
    button_frame = Frame(dialog)
    button_frame.pack(pady=20, padx=20)
    
    row = 0
    col = 0
    for cat in categories:
        btn = Button(button_frame, text=f"{cat['icon']} {cat['name']}", 
                    command=lambda c=cat: [callback(c), dialog.destroy()],
                    font=("Arial", 10), bg="#e0e0e0", width=15, height=2)
        btn.grid(row=row, column=col, padx=10, pady=10)
        col += 1
        if col > 2:
            col = 0
            row += 1
    
    Button(dialog, text="Cancel", command=dialog.destroy, bg="#e74c3c", fg="white").pack(pady=10)

def show_menu(user_id: int, username: str, email: str):
    menu_root = Tk()
    menu_root.title("Expense Tracker Pro")
    menu_root.geometry("1200x800")
    menu_root.resizable(True, True)
    
    # Theme variables
    is_dark_mode = False
    
    # Colors for Light Mode
    LIGHT_COLORS = {
        'primary': "#3498db",
        'danger': "#e74c3c",
        'success': "#27ae60",
        'warning': "#f39c12",
        'header': "#2c3e50",
        'bg': "#ecf0f1",
        'card_bg': "#ffffff",
        'text': "#2c3e50",
        'text_secondary': "#7f8c8d",
        'border': "#bdc3c7"
    }
    
    # Colors for Dark Mode
    DARK_COLORS = {
        'primary': "#3498db",
        'danger': "#e74c3c",
        'success': "#27ae60",
        'warning': "#f39c12",
        'header': "#1a1a2e",
        'bg': "#16213e",
        'card_bg': "#0f3460",
        'text': "#ecf0f1",
        'text_secondary': "#bdc3c7",
        'border': "#2c3e50"
    }
    
    colors = LIGHT_COLORS
    
    def toggle_theme():
        nonlocal is_dark_mode, colors
        is_dark_mode = not is_dark_mode
        colors = DARK_COLORS if is_dark_mode else LIGHT_COLORS
        apply_theme()
    
    def apply_theme():
        menu_root.config(bg=colors['bg'])
        header_frame.config(bg=colors['header'])
        header_title.config(bg=colors['header'], fg="white")
        header_subtitle.config(bg=colors['header'], fg="lightgray")
        main_container.config(bg=colors['bg'])
        canvas.config(bg=colors['bg'])
        scrollable_frame.config(bg=colors['bg'])
        center_container.config(bg=colors['bg'])
        content_wrapper.config(bg=colors['bg'])
        stats_frame.config(bg=colors['bg'])
        
        # Update stat cards
        for widget in stats_frame.winfo_children():
            if isinstance(widget, Frame):
                widget.config(bg=colors['card_bg'])
                for child in widget.winfo_children():
                    child.config(bg=colors['card_bg'])
        
        # Update other frames similarly
        input_frame.config(bg=colors['card_bg'])
        filter_frame.config(bg=colors['card_bg'])
        table_frame.config(bg=colors['card_bg'])
        action_frame.config(bg=colors['bg'])
        quote_frame.config(bg=colors['card_bg'])
        quote_label.config(bg=colors['card_bg'], fg=colors['primary'])
    
    # Get budget settings
    budget_settings = get_budget_settings(user_id)
    weekly_budget = budget_settings['weekly_budget']
    savings_goal = budget_settings['savings_goal']
    savings_goal_name = budget_settings['savings_goal_name']
    
    # Get current random quote
    current_quote = random.choice(MOTIVATIONAL_QUOTES)
    
    # Main background
    menu_root.config(bg=colors['bg'])
    
    # Header Frame
    header_frame = Frame(menu_root, bg=colors['header'], height=80)
    header_frame.pack(fill=X)
    
    header_top = Frame(header_frame, bg=colors['header'])
    header_top.pack(fill=X, padx=20, pady=(10, 0))
    
    header_title = Label(header_top, text="💰 Expense Tracker Pro", font=("Arial", 24, "bold"), 
                        bg=colors['header'], fg="white")
    header_title.pack(side=LEFT)
    
    # Theme toggle button
    theme_btn = Button(header_top, text="🌙 Dark Mode" if not is_dark_mode else "☀️ Light Mode", 
                      command=toggle_theme, bg=colors['primary'], fg="white",
                      font=("Arial", 10, "bold"), padx=15, pady=5, relief=FLAT, cursor="hand2")
    theme_btn.pack(side=RIGHT)
    
    header_subtitle = Label(header_frame, text=f"Welcome, {username}! Track your finances like a pro", 
                           font=("Arial", 11), bg=colors['header'], fg="lightgray")
    header_subtitle.pack(pady=(5, 10))
    
    # Wallet/Balance Display
    wallet_frame = Frame(header_frame, bg=colors['success'], height=60)
    wallet_frame.pack(fill=X, pady=(0, 10))
    
    def update_wallet_display():
        expenses = get_user_expenses(user_id)
        incomes = get_user_incomes(user_id)
        total_income = sum(i["amount"] for i in incomes)
        total_expense = sum(e["amount"] for e in expenses)
        balance = total_income - total_expense
        
        wallet_label.config(text=f"💰 Available Balance: ₱{balance:,.2f}")
        
        # Check budget alert
        if weekly_budget > 0:
            # Get current week expenses
            today = date.today()
            start, end = get_week_range(today)
            week_expenses = filter_expenses(expenses, start, end)
            week_total = sum(e["amount"] for e in week_expenses)
            
            if week_total > weekly_budget:
                budget_warning.config(text=f"⚠️ WARNING: Weekly budget exceeded! (₱{week_total:.2f} / ₱{weekly_budget:.2f})", 
                                     bg=colors['danger'], fg="white")
                budget_warning.pack(fill=X, pady=(5, 0))
            else:
                budget_warning.config(text=f"📊 Weekly Budget: ₱{week_total:.2f} / ₱{weekly_budget:.2f} ({(week_total/weekly_budget)*100:.1f}%)",
                                     bg=colors['primary'], fg="white")
                budget_warning.pack(fill=X, pady=(5, 0))
        
        # Update savings goal progress
        if savings_goal > 0:
            savings_progress = (balance / savings_goal) * 100 if savings_goal > 0 else 0
            if savings_progress < 0:
                savings_progress = 0
            savings_progress_bar['value'] = savings_progress
            savings_label.config(text=f"🎯 {savings_goal_name if savings_goal_name else 'Savings Goal'}: ₱{balance:,.2f} / ₱{savings_goal:,.2f} ({savings_progress:.1f}%)")
        
        return balance
    
    wallet_label = Label(wallet_frame, text="💰 Available Balance: ₱0.00", 
                        font=("Arial", 14, "bold"), bg=colors['success'], fg="white")
    wallet_label.pack(pady=10)
    
    budget_warning = Label(wallet_frame, text="", font=("Arial", 10), bg=colors['success'])
    
    # Main content with scrollbar
    main_container = Frame(menu_root, bg=colors['bg'])
    main_container.pack(expand=True, fill=BOTH)
    
    # Create canvas for scrolling
    canvas = Canvas(main_container, bg=colors['bg'], highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas, bg=colors['bg'])

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Enable mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    # Center the content
    center_container = Frame(scrollable_frame, bg=colors['bg'])
    center_container.pack(expand=True, fill=BOTH)
    
    # Content wrapper with fixed width for centering
    content_wrapper = Frame(center_container, bg=colors['bg'])
    content_wrapper.pack(expand=True, fill=BOTH, padx=40, pady=20)
    
    # Stats Section
    stats_frame = Frame(content_wrapper, bg=colors['bg'])
    stats_frame.pack(fill=X, pady=15)
    
    def create_stat_card(parent, title, value_var, icon):
        card = Frame(parent, bg=colors['card_bg'], relief=RAISED, bd=0)
        card.pack(side=LEFT, padx=10, fill=BOTH, expand=True)
        
        icon_label = Label(card, text=icon, font=("Arial", 24), bg=colors['card_bg'])
        icon_label.pack(pady=(10, 5))
        
        title_label = Label(card, text=title, font=("Arial", 10), bg=colors['card_bg'], fg=colors['text_secondary'])
        title_label.pack()
        
        value_label = Label(card, textvariable=value_var, font=("Arial", 16, "bold"), 
                           bg=colors['card_bg'], fg=colors['primary'])
        value_label.pack(pady=(5, 10))
        
        return card
    
    total_expense_var = StringVar(value="₱0.00")
    total_income_var = StringVar(value="₱0.00")
    savings_var = StringVar(value="₱0.00")
    
    create_stat_card(stats_frame, "Total Expenses", total_expense_var, "📊")
    create_stat_card(stats_frame, "Total Income", total_income_var, "💰")
    create_stat_card(stats_frame, "Savings", savings_var, "💎")
    
    # Savings Goal Progress
    if savings_goal > 0:
        savings_frame = Frame(content_wrapper, bg=colors['card_bg'], relief=RAISED, bd=1)
        savings_frame.pack(fill=X, pady=15)
        
        savings_label = Label(savings_frame, text=f"🎯 {savings_goal_name}: Progress", 
                             font=("Arial", 11, "bold"), bg=colors['card_bg'], fg=colors['text'])
        savings_label.pack(anchor=W, padx=15, pady=(10, 5))
        
        savings_progress_bar = ttk.Progressbar(savings_frame, length=400, mode='determinate')
        savings_progress_bar.pack(fill=X, padx=15, pady=5)
        
        savings_percent_label = Label(savings_frame, text="0%", font=("Arial", 9), 
                                      bg=colors['card_bg'], fg=colors['text_secondary'])
        savings_percent_label.pack(anchor=E, padx=15, pady=(0, 10))
    
    # Motivational Quote
    quote_frame = Frame(content_wrapper, bg=colors['card_bg'], relief=RAISED, bd=1)
    quote_frame.pack(fill=X, pady=15)
    
    quote_label = Label(quote_frame, text=f"💌 {current_quote}", font=("Arial", 10, "italic"), 
                       bg=colors['card_bg'], fg=colors['primary'], pady=10)
    quote_label.pack()
    
    # Input Section
    notebook = ttk.Notebook(content_wrapper)
    notebook.pack(fill=X, pady=15)
    
    # Expense Tab
    expense_tab = Frame(notebook, bg=colors['bg'])
    notebook.add(expense_tab, text="💸 Add Expense")
    
    # Income Tab
    income_tab = Frame(notebook, bg=colors['bg'])
    notebook.add(income_tab, text="💰 Add Income")
    
    # Settings Tab
    settings_tab = Frame(notebook, bg=colors['bg'])
    notebook.add(settings_tab, text="⚙️ Settings")
    
    # Expense Tab Content (simplified for brevity - similar to before)
    expense_input_frame = Frame(expense_tab, bg=colors['card_bg'], relief=RAISED, bd=1)
    expense_input_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    Label(expense_input_frame, text="Add New Expense", font=("Arial", 12, "bold"), 
         bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, padx=15, pady=(10, 0))
    
    expense_inner = Frame(expense_input_frame, bg=colors['card_bg'])
    expense_inner.pack(fill=X, padx=15, pady=10)
    
    # Category selection for expense
    Label(expense_inner, text="Category:", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    expense_category_var = StringVar()
    expense_category_icon_var = StringVar()
    
    def select_expense_category():
        def on_category_selected(category):
            expense_category_var.set(category['name'])
            expense_category_icon_var.set(category['icon'])
            expense_category_btn.config(text=f"{category['icon']} {category['name']}")
        
        create_category_selection_dialog(menu_root, "Select Expense Category", EXPENSE_CATEGORIES, on_category_selected)
    
    expense_category_btn = Button(expense_inner, text="📦 Select Category", command=select_expense_category,
                                 bg=colors['primary'], fg="white", font=("Arial", 9), padx=10, pady=5)
    expense_category_btn.pack(anchor=W, pady=(0, 10))
    
    Label(expense_inner, text="Description:", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    expense_description_var = StringVar()
    Entry(expense_inner, textvariable=expense_description_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    Label(expense_inner, text="Amount:", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    expense_amount_var = StringVar()
    Entry(expense_inner, textvariable=expense_amount_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    Label(expense_inner, text="Date (YYYY-MM-DD):", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    expense_date_var = StringVar(value=date.today().strftime(DATE_FORMAT))
    Entry(expense_inner, textvariable=expense_date_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    expense_status_var = StringVar()
    
    def add_expense_action():
        description = expense_description_var.get().strip()
        amount_str = expense_amount_var.get().strip()
        category = expense_category_var.get()
        category_icon = expense_category_icon_var.get()
        exp_date = expense_date_var.get().strip()
        
        if not description:
            expense_status_var.set("❌ Description cannot be blank")
            return
        if not category:
            expense_status_var.set("❌ Please select a category")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            expense_status_var.set("❌ Amount must be a positive number")
            return
        
        if add_expense_db(user_id, description, amount, category, category_icon, exp_date):
            expense_status_var.set("✅ Expense added successfully!")
            expense_description_var.set("")
            expense_amount_var.set("")
            expense_category_var.set("")
            expense_category_icon_var.set("")
            expense_category_btn.config(text="📦 Select Category")
            update_display()
            update_wallet_display()
        else:
            expense_status_var.set("❌ Failed to add expense")
    
    expense_btn_frame = Frame(expense_inner, bg=colors['card_bg'])
    expense_btn_frame.pack(fill=X, pady=(10, 0))
    
    expense_add_btn = Button(expense_btn_frame, text="➕ Add Expense", command=add_expense_action, 
                            bg=colors['primary'], fg="white", font=("Arial", 10, "bold"), 
                            padx=20, pady=8, relief=FLAT, cursor="hand2")
    expense_add_btn.pack(side=LEFT, padx=(0, 10))
    
    expense_status_label = Label(expense_btn_frame, textvariable=expense_status_var, bg=colors['card_bg'], 
                                fg=colors['success'], font=("Arial", 9))
    expense_status_label.pack(side=LEFT)
    
    # Income Tab Content (similar structure - simplified)
    income_input_frame = Frame(income_tab, bg=colors['card_bg'], relief=RAISED, bd=1)
    income_input_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    Label(income_input_frame, text="Add New Income", font=("Arial", 12, "bold"), 
         bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, padx=15, pady=(10, 0))
    
    income_inner = Frame(income_input_frame, bg=colors['card_bg'])
    income_inner.pack(fill=X, padx=15, pady=10)
    
    # Category selection for income
    Label(income_inner, text="Category:", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    income_category_var = StringVar()
    income_category_icon_var = StringVar()
    
    def select_income_category():
        def on_category_selected(category):
            income_category_var.set(category['name'])
            income_category_icon_var.set(category['icon'])
            income_category_btn.config(text=f"{category['icon']} {category['name']}")
        
        create_category_selection_dialog(menu_root, "Select Income Category", INCOME_CATEGORIES, on_category_selected)
    
    income_category_btn = Button(income_inner, text="📦 Select Category", command=select_income_category,
                                bg=colors['primary'], fg="white", font=("Arial", 9), padx=10, pady=5)
    income_category_btn.pack(anchor=W, pady=(0, 10))
    
    Label(income_inner, text="Description:", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    income_description_var = StringVar()
    Entry(income_inner, textvariable=income_description_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    Label(income_inner, text="Amount:", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    income_amount_var = StringVar()
    Entry(income_inner, textvariable=income_amount_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    Label(income_inner, text="Date (YYYY-MM-DD):", bg=colors['card_bg'], fg=colors['text'], font=("Arial", 9)).pack(anchor=W)
    income_date_var = StringVar(value=date.today().strftime(DATE_FORMAT))
    Entry(income_inner, textvariable=income_date_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    income_status_var = StringVar()
    
    def add_income_action():
        description = income_description_var.get().strip()
        amount_str = income_amount_var.get().strip()
        category = income_category_var.get()
        category_icon = income_category_icon_var.get()
        inc_date = income_date_var.get().strip()
        
        if not description:
            income_status_var.set("❌ Description cannot be blank")
            return
        if not category:
            income_status_var.set("❌ Please select a category")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            income_status_var.set("❌ Amount must be a positive number")
            return
        
        if add_income_db(user_id, description, amount, category, category_icon, inc_date):
            income_status_var.set("✅ Income added successfully!")
            income_description_var.set("")
            income_amount_var.set("")
            income_category_var.set("")
            income_category_icon_var.set("")
            income_category_btn.config(text="📦 Select Category")
            update_display()
            update_wallet_display()
        else:
            income_status_var.set("❌ Failed to add income")
    
    income_btn_frame = Frame(income_inner, bg=colors['card_bg'])
    income_btn_frame.pack(fill=X, pady=(10, 0))
    
    income_add_btn = Button(income_btn_frame, text="➕ Add Income", command=add_income_action, 
                           bg=colors['success'], fg="white", font=("Arial", 10, "bold"), 
                           padx=20, pady=8, relief=FLAT, cursor="hand2")
    income_add_btn.pack(side=LEFT, padx=(0, 10))
    
    income_status_label = Label(income_btn_frame, textvariable=income_status_var, bg=colors['card_bg'], 
                               fg=colors['success'], font=("Arial", 9))
    income_status_label.pack(side=LEFT)
    
    # Settings Tab Content
    settings_frame = Frame(settings_tab, bg=colors['card_bg'], relief=RAISED, bd=1)
    settings_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    Label(settings_frame, text="Budget & Goals Settings", font=("Arial", 14, "bold"), 
         bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, padx=15, pady=(15, 5))
    
    settings_inner = Frame(settings_frame, bg=colors['card_bg'])
    settings_inner.pack(fill=X, padx=15, pady=10)
    
    Label(settings_inner, text="Weekly Budget Limit:", bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, pady=(10, 0))
    weekly_budget_var = StringVar(value=str(weekly_budget) if weekly_budget > 0 else "")
    Entry(settings_inner, textvariable=weekly_budget_var, font=("Arial", 10), width=20).pack(anchor=W, pady=(0, 10))
    
    Label(settings_inner, text="Savings Goal Name:", bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, pady=(10, 0))
    savings_goal_name_var = StringVar(value=savings_goal_name)
    Entry(settings_inner, textvariable=savings_goal_name_var, font=("Arial", 10), width=30).pack(anchor=W, pady=(0, 10))
    
    Label(settings_inner, text="Savings Goal Amount:", bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, pady=(10, 0))
    savings_goal_var = StringVar(value=str(savings_goal) if savings_goal > 0 else "")
    Entry(settings_inner, textvariable=savings_goal_var, font=("Arial", 10), width=20).pack(anchor=W, pady=(0, 10))
    
    settings_status_var = StringVar()
    
    def save_settings():
        weekly = float(weekly_budget_var.get()) if weekly_budget_var.get().strip() else 0
        savings = float(savings_goal_var.get()) if savings_goal_var.get().strip() else 0
        savings_name = savings_goal_name_var.get().strip()
        
        if update_budget_settings(user_id, weekly_budget=weekly, savings_goal=savings, savings_goal_name=savings_name):
            settings_status_var.set("✅ Settings saved successfully!")
            messagebox.showinfo("Success", "Budget settings updated!")
        else:
            settings_status_var.set("❌ Failed to save settings")
    
    save_btn = Button(settings_inner, text="💾 Save Settings", command=save_settings,
                     bg=colors['success'], fg="white", font=("Arial", 10, "bold"),
                     padx=20, pady=8, relief=FLAT, cursor="hand2")
    save_btn.pack(anchor=W, pady=(10, 10))
    
    settings_status_label = Label(settings_inner, textvariable=settings_status_var, bg=colors['card_bg'], 
                                 fg=colors['success'], font=("Arial", 9))
    settings_status_label.pack(anchor=W)
    
    # Filter Buttons
    filter_frame = Frame(content_wrapper, bg=colors['card_bg'], relief=RAISED, bd=1)
    filter_frame.pack(fill=X, pady=15)
    
    Label(filter_frame, text="Filter by Period", font=("Arial", 12, "bold"), 
         bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, padx=15, pady=(10, 0))
    
    button_container = Frame(filter_frame, bg=colors['card_bg'])
    button_container.pack(fill=X, padx=15, pady=10)
    
    # Search Section
    search_frame = Frame(content_wrapper, bg=colors['card_bg'], relief=RAISED, bd=1)
    search_frame.pack(fill=X, pady=15)
    
    Label(search_frame, text="🔍 Search Expenses", font=("Arial", 12, "bold"), 
         bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, padx=15, pady=(10, 0))
    
    search_inner = Frame(search_frame, bg=colors['card_bg'])
    search_inner.pack(fill=X, padx=15, pady=10)
    
    search_var = StringVar()
    search_entry = Entry(search_inner, textvariable=search_var, font=("Arial", 10), width=30)
    search_entry.pack(side=LEFT, padx=(0, 10))
    
    def search_expenses():
        search_term = search_var.get().lower()
        for item in expense_table.get_children():
            values = expense_table.item(item)['values']
            if len(values) >= 3 and search_term in str(values[2]).lower():
                expense_table.selection_set(item)
                expense_table.see(item)
            else:
                expense_table.selection_remove(item)
    
    search_btn = Button(search_inner, text="Search", command=search_expenses,
                       bg=colors['primary'], fg="white", font=("Arial", 9),
                       padx=15, pady=5, relief=FLAT, cursor="hand2")
    search_btn.pack(side=LEFT)
    
    current_filter = {"period": "all", "type": "expenses"}
    
    def filter_by_period(period):
        current_filter["period"] = period
        update_period_buttons()
        update_display()
    
    def filter_by_type(record_type):
        current_filter["type"] = record_type
        update_type_buttons()
        update_display()
    
    def update_period_buttons():
        for btn in period_buttons:
            if btn.period == current_filter["period"]:
                btn.config(bg=colors['primary'], fg="white")
            else:
                btn.config(bg=colors['card_bg'], fg=colors['primary'], bd=1, relief=SUNKEN)
    
    def update_type_buttons():
        for btn in type_buttons:
            if btn.type == current_filter["type"]:
                btn.config(bg=colors['primary'], fg="white")
            else:
                btn.config(bg=colors['card_bg'], fg=colors['primary'], bd=1, relief=SUNKEN)
    
    period_buttons = []
    for period_name, period_key in [("All Time", "all"), ("This Week", "week"), 
                                     ("This Month", "month"), ("Last Week", "lastweek"), 
                                     ("Last Month", "lastmonth")]:
        btn = Button(button_container, text=period_name, command=lambda p=period_key: filter_by_period(p),
                    font=("Arial", 9, "bold"), padx=12, pady=6, relief=FLAT, cursor="hand2")
        btn.pack(side=LEFT, padx=5)
        btn.period = period_key
        period_buttons.append(btn)
    
    update_period_buttons()
    
    # Type filter buttons
    type_container = Frame(filter_frame, bg=colors['card_bg'])
    type_container.pack(fill=X, padx=15, pady=(0, 10))
    
    type_buttons = []
    for type_name, type_key in [("💸 Expenses", "expenses"), ("💰 Incomes", "incomes")]:
        btn = Button(type_container, text=type_name, command=lambda t=type_key: filter_by_type(t),
                    font=("Arial", 9, "bold"), padx=12, pady=6, relief=FLAT, cursor="hand2")
        btn.pack(side=LEFT, padx=5)
        btn.type = type_key
        type_buttons.append(btn)
    
    update_type_buttons()
    
    # Records Table
    table_frame = Frame(content_wrapper, bg=colors['card_bg'], relief=RAISED, bd=1)
    table_frame.pack(fill=BOTH, expand=True, pady=15)
    
    Label(table_frame, text="Your Records", font=("Arial", 12, "bold"), 
         bg=colors['card_bg'], fg=colors['text']).pack(anchor=W, padx=15, pady=(10, 0))
    
    table_container = Frame(table_frame, bg=colors['card_bg'])
    table_container.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    columns = ("Date", "Category", "Description", "Amount", "Action")
    expense_table = ttk.Treeview(table_container, columns=columns, height=12, show="headings")
    
    for col in columns:
        expense_table.heading(col, text=col)
        expense_table.column(col, width=150 if col != "Description" else 200)
    
    scrollbar_table = ttk.Scrollbar(table_container, orient=VERTICAL, command=expense_table.yview)
    expense_table.configure(yscroll=scrollbar_table.set)
    
    expense_table.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar_table.pack(side=RIGHT, fill=Y)
    
    def get_filtered_records():
        expenses = get_user_expenses(user_id)
        incomes = get_user_incomes(user_id)
        today = date.today()
        
        if current_filter["type"] == "expenses":
            records = expenses
        else:
            records = incomes
        
        if current_filter["period"] == "week":
            start, end = get_week_range(today)
            return [r for r in records if parse_date(r["date"]) >= start]
        elif current_filter["period"] == "month":
            start, end = get_month_range(today)
            return [r for r in records if parse_date(r["date"]) >= start]
        elif current_filter["period"] == "lastweek":
            start, end = get_week_range(today)
            start = start - timedelta(days=7)
            end = start + timedelta(days=6)
            return [r for r in records if start <= parse_date(r["date"]) <= end]
        elif current_filter["period"] == "lastmonth":
            start, end = get_last_month_range(today)
            return [r for r in records if start <= parse_date(r["date"]) <= end]
        else:
            return records
    
    def update_display():
        for item in expense_table.get_children():
            expense_table.delete(item)
        
        records = get_filtered_records()
        
        if not records:
            expense_table.insert("", END, values=("No records", "found for this period", "", "", ""))
        else:
            for record in sorted(records, key=lambda x: x["date"], reverse=True):
                icon = record.get("icon", "📦")
                category = record.get("category", "Other")
                amount = record["amount"]
                amount_str = f"₱{amount:.2f}"
                
                expense_table.insert("", END, values=(
                    record["date"],
                    f"{icon} {category}",
                    record["description"],
                    amount_str,
                    "🗑️ Delete"
                ), iid=f"{current_filter['type']}_{record['id']}")
        
        # Update stats
        expenses = get_user_expenses(user_id)
        incomes = get_user_incomes(user_id)
        total_expense = sum(e["amount"] for e in expenses)
        total_income = sum(i["amount"] for i in incomes)
        savings = total_income - total_expense
        
        total_expense_var.set(f"₱{total_expense:.2f}")
        total_income_var.set(f"₱{total_income:.2f}")
        savings_var.set(f"₱{savings:.2f}")
        
        # Update savings progress
        if savings_goal > 0:
            progress = (savings / savings_goal) * 100 if savings_goal > 0 else 0
            if progress < 0:
                progress = 0
            savings_progress_bar['value'] = progress
            savings_percent_label.config(text=f"{progress:.1f}%")
    
    def on_table_click(event):
        selection = expense_table.selection()
        if not selection:
            return
        
        col = expense_table.identify_column(event.x)
        if col == "#5":  # Action column
            item_id = selection[0]
            record_type, record_id = item_id.split("_")
            
            if record_type == "expenses":
                if delete_expense_db(int(record_id)):
                    update_display()
                    update_wallet_display()
            else:
                if delete_income_db(int(record_id)):
                    update_display()
                    update_wallet_display()
    
    expense_table.bind("<Button-1>", on_table_click)
    
    # Action Buttons
    action_frame = Frame(content_wrapper, bg=colors['bg'])
    action_frame.pack(fill=X, pady=15)
    
    def refresh_data():
        update_display()
        update_wallet_display()
        messagebox.showinfo("Refresh", "Data refreshed successfully!")
    
    refresh_btn = Button(action_frame, text="🔄 Refresh", command=refresh_data,
                        bg=colors['primary'], fg="white", font=("Arial", 10, "bold"),
                        padx=20, pady=8, relief=FLAT, cursor="hand2")
    refresh_btn.pack(side=LEFT, padx=(0, 10))
    
    def logout_action():
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            menu_root.destroy()
    
    logout_btn = Button(action_frame, text="🚪 Logout", command=logout_action,
                       bg=colors['danger'], fg="white", font=("Arial", 10, "bold"),
                       padx=20, pady=8, relief=FLAT, cursor="hand2")
    logout_btn.pack(side=RIGHT)
    
    # Initialize display
    update_display()
    update_wallet_display()
    menu_root.mainloop()

def run_login_gui():
    # Initialize database first
    init_database()

    login_result = {"user_id": None, "username": None, "email": None}

    root = Tk()
    root.title("💰 Expense Tracker Pro - Login")
    root.geometry("600x700")
    root.minsize(400, 500)
    root.resizable(True, True)
    root.config(bg="#f5f7fa")

    # ===== COLORS =====
    PRIMARY = "#2980b9"
    PRIMARY_DARK = "#1e5f8f"
    PRIMARY_LIGHT = "#3498db"
    ACCENT = "#e74c3c"
    BG_LIGHT = "#f5f7fa"
    CARD_BG = "#ffffff"

    # Center the window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"{root.winfo_width()}x{root.winfo_height()}+{x}+{y}")

    # Main container to center everything
    main_container = Frame(root, bg=BG_LIGHT)
    main_container.pack(expand=True, fill=BOTH)
    
    # Center the content
    center_frame = Frame(main_container, bg=BG_LIGHT)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Logo & Title Section
    logo_label = Label(center_frame, text="💰", font=("Arial", 48, "bold"), bg=BG_LIGHT)
    logo_label.pack(pady=(20, 10))

    title_label = Label(center_frame, text="Expense Tracker Pro", 
                       font=("Arial", 24, "bold"), bg=BG_LIGHT, fg=PRIMARY)
    title_label.pack(pady=(0, 5))

    subtitle_label = Label(center_frame, text="Manage your finances easily", 
                          font=("Arial", 11), bg=BG_LIGHT, fg="#7f8c8d")
    subtitle_label.pack(pady=(0, 30))

    # Form Card
    form_card = Frame(center_frame, bg=CARD_BG, relief=RAISED, bd=0)
    form_card.pack(fill=BOTH, padx=10, pady=10)

    form_inner = Frame(form_card, bg=CARD_BG)
    form_inner.pack(fill=BOTH, padx=20, pady=20)

    # Username
    username_label = Label(form_inner, text="Username or Email", font=("Segoe UI", 10, "bold"), 
         bg=CARD_BG, fg=PRIMARY_DARK)
    username_label.pack(anchor=W, pady=(0, 5))
    username_var = StringVar()
    username_entry = Entry(form_inner, textvariable=username_var, font=("Segoe UI", 11),
                          bd=1, relief=SUNKEN)
    username_entry.pack(fill=X, ipady=8)

    # Password
    password_label = Label(form_inner, text="Password", font=("Segoe UI", 10, "bold"), 
         bg=CARD_BG, fg=PRIMARY_DARK)
    password_label.pack(anchor=W, pady=(15, 5))
    password_var = StringVar()
    password_entry = Entry(form_inner, textvariable=password_var, font=("Segoe UI", 11),
                          show="●", bd=1, relief=SUNKEN)
    password_entry.pack(fill=X, ipady=8)

    # Status Message
    status_var = StringVar()
    status_label = Label(form_inner, textvariable=status_var, fg=ACCENT, 
                        font=("Segoe UI", 9), bg=CARD_BG)
    status_label.pack(pady=(15, 0))

    # Button Container
    button_frame = Frame(form_inner, bg=CARD_BG)
    button_frame.pack(fill=X, pady=(20, 0))

    def handle_login():
        username = username_var.get().strip()
        password = password_var.get()
        
        if not username or not password:
            status_var.set("❌ Please enter username/email and password")
            return
            
        result = login_user_db(username, password)
        if result:
            login_result["user_id"] = result[0]
            login_result["username"] = result[1]
            login_result["email"] = result[2]
            root.destroy()
        else:
            status_var.set("❌ Invalid username/email or password")
            # Clear password field
            password_var.set("")
            password_entry.focus()

    login_btn = Button(button_frame, text="🔓  LOGIN", command=handle_login,
                      bg=PRIMARY, fg="white", font=("Segoe UI", 11, "bold"),
                      padx=20, pady=10, relief=FLAT, cursor="hand2", bd=0)
    login_btn.pack(fill=X)

    # Bind Enter key to login
    root.bind('<Return>', lambda event: handle_login())

    # Register Section
    register_frame = Frame(center_frame, bg=BG_LIGHT)
    register_frame.pack(fill=X, padx=10, pady=20)

    reg_frame_label = Label(register_frame, text="Don't have an account?", font=("Segoe UI", 10),
         bg=BG_LIGHT, fg="#7f8c8d")
    reg_frame_label.pack()

    def open_register():
        register_window = Toplevel(root)
        register_window.title("💰 Expense Tracker Pro - Register")
        register_window.geometry("500x700")
        register_window.minsize(400, 600)
        register_window.resizable(True, True)
        register_window.config(bg=BG_LIGHT)
        
        # Center register window
        register_window.update_idletasks()
        x = (register_window.winfo_screenwidth() // 2) - (register_window.winfo_width() // 2)
        y = (register_window.winfo_screenheight() // 2) - (register_window.winfo_height() // 2)
        register_window.geometry(f"{register_window.winfo_width()}x{register_window.winfo_height()}+{x}+{y}")

        # Register container
        reg_container = Frame(register_window, bg=BG_LIGHT)
        reg_container.pack(expand=True, fill=BOTH, padx=20, pady=30)
        
        # Center the content
        reg_center_frame = Frame(reg_container, bg=BG_LIGHT)
        reg_center_frame.pack(expand=True)

        # Title
        reg_title = Label(reg_center_frame, text="Create Account", 
                         font=("Arial", 24, "bold"), bg=BG_LIGHT, fg=PRIMARY)
        reg_title.pack(pady=(0, 30))

        # Form Card
        reg_form_card = Frame(reg_center_frame, bg=CARD_BG, relief=RAISED, bd=0)
        reg_form_card.pack(fill=BOTH, padx=10, pady=10)

        reg_form_inner = Frame(reg_form_card, bg=CARD_BG)
        reg_form_inner.pack(fill=BOTH, padx=20, pady=20)

        # Username
        Label(reg_form_inner, text="Username", font=("Segoe UI", 10, "bold"), 
             bg=CARD_BG, fg=PRIMARY_DARK).pack(anchor=W, pady=(0, 5))
        reg_username_var = StringVar()
        reg_username_entry = Entry(reg_form_inner, textvariable=reg_username_var, 
                                  font=("Segoe UI", 11), bd=1, relief=SUNKEN)
        reg_username_entry.pack(fill=X, ipady=8)

        # Email
        Label(reg_form_inner, text="Email", font=("Segoe UI", 10, "bold"), 
             bg=CARD_BG, fg=PRIMARY_DARK).pack(anchor=W, pady=(15, 5))
        reg_email_var = StringVar()
        reg_email_entry = Entry(reg_form_inner, textvariable=reg_email_var, 
                               font=("Segoe UI", 11), bd=1, relief=SUNKEN)
        reg_email_entry.pack(fill=X, ipady=8)

        # Password
        Label(reg_form_inner, text="Password", font=("Segoe UI", 10, "bold"), 
             bg=CARD_BG, fg=PRIMARY_DARK).pack(anchor=W, pady=(15, 5))
        reg_password_var = StringVar()
        reg_password_entry = Entry(reg_form_inner, textvariable=reg_password_var, 
                                  font=("Segoe UI", 11), show="●", bd=1, relief=SUNKEN)
        reg_password_entry.pack(fill=X, ipady=8)

        # Confirm Password
        Label(reg_form_inner, text="Confirm Password", font=("Segoe UI", 10, "bold"), 
             bg=CARD_BG, fg=PRIMARY_DARK).pack(anchor=W, pady=(15, 5))
        reg_confirm_var = StringVar()
        reg_confirm_entry = Entry(reg_form_inner, textvariable=reg_confirm_var, 
                                 font=("Segoe UI", 11), show="●", bd=1, relief=SUNKEN)
        reg_confirm_entry.pack(fill=X, ipady=8)

        # Status
        reg_status_var = StringVar()
        reg_status_label = Label(reg_form_inner, textvariable=reg_status_var, 
                                fg=ACCENT, font=("Segoe UI", 9), bg=CARD_BG)
        reg_status_label.pack(pady=(15, 0))

        # Register Button
        reg_btn_frame = Frame(reg_form_inner, bg=CARD_BG)
        reg_btn_frame.pack(fill=X, pady=(20, 0))

        def handle_register():
            username = reg_username_var.get().strip()
            email = reg_email_var.get().strip()
            password = reg_password_var.get()
            confirm = reg_confirm_var.get()
            
            if not username:
                reg_status_var.set("❌ Username cannot be blank")
                return
            if not email:
                reg_status_var.set("❌ Email cannot be blank")
                return
            if "@" not in email or "." not in email:
                reg_status_var.set("❌ Invalid email format")
                return
            if len(password) < 6:
                reg_status_var.set("❌ Password must be at least 6 characters")
                return
            if password != confirm:
                reg_status_var.set("❌ Passwords do not match")
                return
            
            if user_exists(username, email):
                reg_status_var.set("❌ Username or email already exists")
                return
            
            if register_user_db(username, email, password):
                reg_status_var.set("✅ Registration successful! Redirecting to login...")
                reg_status_label.config(fg="green")
                # Close registration window after 2 seconds
                register_window.after(2000, register_window.destroy)
            else:
                reg_status_var.set("❌ Registration failed. Please try again.")

        reg_submit_btn = Button(reg_btn_frame, text="✓  REGISTER", command=handle_register,
                               bg=PRIMARY, fg="white", font=("Segoe UI", 11, "bold"),
                               padx=20, pady=10, relief=FLAT, cursor="hand2", bd=0)
        reg_submit_btn.pack(fill=X)
        
        # Bind Enter key to register
        register_window.bind('<Return>', lambda event: handle_register())

    register_btn = Button(register_frame, text="📝  SIGN UP", command=open_register,
                         bg=PRIMARY, fg="white", font=("Segoe UI", 10, "bold"),
                         padx=20, pady=8, relief=FLAT, cursor="hand2", bd=0)
    register_btn.pack(pady=(10, 0))

    root.mainloop()

    if login_result["user_id"]:
        show_menu(login_result["user_id"], login_result["username"], login_result["email"])

if __name__ == "__main__":
    run_login_gui()