import mysql.connector
from mysql.connector import Error
import hashlib
import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import *
from tkinter import ttk

# MySQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Db123@#**',
    'database': 'grp_demo'
}

DATE_FORMAT = "%Y-%m-%d"

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
        
        # Create expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_user_by_username(username: str):
    """Get user from database by username"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, password FROM users WHERE username = %s", (username,))
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
        cursor.execute("SELECT id, username, email, password FROM users WHERE email = %s", (email,))
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
        return True
    except Error as e:
        print(f"Error registering user: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def login_user_db(username_or_email: str, password: str) -> tuple:
    """Authenticate user login by username or email"""
    # Try username first
    user = get_user_by_username(username_or_email)
    
    # If not found, try email
    if not user:
        user = get_user_by_email(username_or_email)
    
    # Verify password
    if user and user[3] == hash_password(password):  # user[3] is password
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
            "SELECT id, description, amount, date FROM expenses WHERE user_id = %s ORDER BY date DESC",
            (user_id,)
        )
        expenses = cursor.fetchall()
        return [{"id": e[0], "description": e[1], "amount": float(e[2]), "date": e[3]} for e in expenses]
    except Error as e:
        print(f"Error fetching expenses: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def add_expense_db(user_id: int, description: str, amount: float, exp_date: str) -> bool:
    """Add a new expense to the database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, description, amount, date) VALUES (%s, %s, %s, %s)",
            (user_id, description, round(amount, 2), exp_date)
        )
        connection.commit()
        return True
    except Error as e:
        print(f"Error adding expense: {e}")
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

def show_menu(user_id: int, username: str, email: str):
    menu_root = Tk()
    menu_root.title("Expense Tracker Dashboard")
    menu_root.geometry("1000x700")
    menu_root.resizable(True, True)
    
    # Colors
    PRIMARY_COLOR = "#3498db"
    DANGER_COLOR = "#e74c3c"
    SUCCESS_COLOR = "#27ae60"
    HEADER_COLOR = "#2c3e50"
    BG_COLOR = "#ecf0f1"
    TEXT_COLOR = "#2c3e50"
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Main background
    menu_root.config(bg=BG_COLOR)
    
    # Header Frame
    header_frame = Frame(menu_root, bg=HEADER_COLOR, height=80)
    header_frame.pack(fill=X)
    
    header_title = Label(header_frame, text="💰 Expense Tracker", font=("Arial", 24, "bold"), 
                        bg=HEADER_COLOR, fg="white")
    header_title.pack(pady=(10, 0))
    
    header_subtitle = Label(header_frame, text=f"Welcome, {username}! Track your expenses easily", 
                           font=("Arial", 11), bg=HEADER_COLOR, fg="lightgray")
    header_subtitle.pack(pady=(0, 10))
    
    # Main content with scrollbar
    main_container = Frame(menu_root, bg=BG_COLOR)
    main_container.pack(expand=True, fill=BOTH)
    
    # Create canvas for scrolling
    canvas = Canvas(main_container, bg=BG_COLOR, highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas, bg=BG_COLOR)

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
    center_container = Frame(scrollable_frame, bg=BG_COLOR)
    center_container.pack(expand=True, fill=BOTH)
    
    # Content wrapper with fixed width for centering
    content_wrapper = Frame(center_container, bg=BG_COLOR)
    content_wrapper.pack(expand=True, fill=BOTH, padx=40, pady=20)
    
    # Stats Section
    stats_frame = Frame(content_wrapper, bg=BG_COLOR)
    stats_frame.pack(fill=X, pady=15)
    
    def create_stat_card(parent, title, value_var, icon):
        card = Frame(parent, bg="white", relief=RAISED, bd=0)
        card.pack(side=LEFT, padx=10, fill=BOTH, expand=True)
        
        icon_label = Label(card, text=icon, font=("Arial", 20), bg="white")
        icon_label.pack(pady=(10, 5))
        
        title_label = Label(card, text=title, font=("Arial", 10), bg="white", fg="gray")
        title_label.pack()
        
        value_label = Label(card, textvariable=value_var, font=("Arial", 16, "bold"), 
                           bg="white", fg=PRIMARY_COLOR)
        value_label.pack(pady=(5, 10))
        
        return card
    
    total_var = StringVar(value="₱0.00")
    count_var = StringVar(value="0")
    avg_var = StringVar(value="₱0.00")
    
    create_stat_card(stats_frame, "Total Spent", total_var, "📊")
    create_stat_card(stats_frame, "Total Entries", count_var, "📝")
    create_stat_card(stats_frame, "Average", avg_var, "📈")
    
    # Input Section
    input_frame = Frame(content_wrapper, bg="white", relief=RAISED, bd=1)
    input_frame.pack(fill=X, pady=15)
    
    Label(input_frame, text="Add New Expense", font=("Arial", 12, "bold"), 
         bg="white", fg=TEXT_COLOR).pack(anchor=W, padx=15, pady=(10, 0))
    
    input_inner = Frame(input_frame, bg="white")
    input_inner.pack(fill=X, padx=15, pady=10)
    
    Label(input_inner, text="Description:", bg="white", fg=TEXT_COLOR, font=("Arial", 9)).pack(anchor=W)
    description_var = StringVar()
    Entry(input_inner, textvariable=description_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    Label(input_inner, text="Amount:", bg="white", fg=TEXT_COLOR, font=("Arial", 9)).pack(anchor=W)
    amount_var = StringVar()
    Entry(input_inner, textvariable=amount_var, font=("Arial", 10), 
         bd=1, relief=SUNKEN).pack(fill=X, pady=(0, 10))
    
    status_var = StringVar()
    
    def add_expense_action():
        description = description_var.get().strip()
        amount_str = amount_var.get().strip()
        if not description:
            status_var.set("❌ Description cannot be blank")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            status_var.set("❌ Amount must be a positive number")
            return
        
        if add_expense_db(user_id, description, amount, date.today().strftime(DATE_FORMAT)):
            status_var.set("✅ Expense added successfully!")
            description_var.set("")
            amount_var.set("")
            update_display()
        else:
            status_var.set("❌ Failed to add expense")
    
    btn_frame = Frame(input_inner, bg="white")
    btn_frame.pack(fill=X)
    
    add_btn = Button(btn_frame, text="➕ Add Expense", command=add_expense_action, 
                    bg=PRIMARY_COLOR, fg="white", font=("Arial", 10, "bold"), 
                    padx=20, pady=8, relief=FLAT, cursor="hand2")
    add_btn.pack(side=LEFT, padx=(0, 10))
    
    status_label = Label(btn_frame, textvariable=status_var, bg="white", 
                        fg=SUCCESS_COLOR, font=("Arial", 9))
    status_label.pack(side=LEFT)
    
    # Filter Buttons
    filter_frame = Frame(content_wrapper, bg="white", relief=RAISED, bd=1)
    filter_frame.pack(fill=X, pady=15)
    
    Label(filter_frame, text="Filter by Period", font=("Arial", 12, "bold"), 
         bg="white", fg=TEXT_COLOR).pack(anchor=W, padx=15, pady=(10, 0))
    
    button_container = Frame(filter_frame, bg="white")
    button_container.pack(fill=X, padx=15, pady=10)
    
    current_filter = {"period": "all"}
    
    def filter_by_period(period):
        current_filter["period"] = period
        update_period_buttons()
        update_display()
    
    def update_period_buttons():
        for btn in period_buttons:
            if btn.period == current_filter["period"]:
                btn.config(bg=PRIMARY_COLOR, fg="white")
            else:
                btn.config(bg="white", fg=PRIMARY_COLOR, bd=1, relief=SUNKEN)
    
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
    
    # Expenses Table
    table_frame = Frame(content_wrapper, bg="white", relief=RAISED, bd=1)
    table_frame.pack(fill=BOTH, expand=True, pady=15)
    
    Label(table_frame, text="Your Expenses", font=("Arial", 12, "bold"), 
         bg="white", fg=TEXT_COLOR).pack(anchor=W, padx=15, pady=(10, 0))
    
    table_container = Frame(table_frame, bg="white")
    table_container.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    columns = ("Date", "Description", "Amount", "Action")
    expense_table = ttk.Treeview(table_container, columns=columns, height=12, show="headings")
    
    for col in columns:
        expense_table.heading(col, text=col)
        expense_table.column(col, width=150 if col != "Amount" else 100)
    
    scrollbar_table = ttk.Scrollbar(table_container, orient=VERTICAL, command=expense_table.yview)
    expense_table.configure(yscroll=scrollbar_table.set)
    
    expense_table.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar_table.pack(side=RIGHT, fill=Y)
    
    def get_filtered_expenses():
        expenses = get_user_expenses(user_id)
        today = date.today()
        
        if current_filter["period"] == "week":
            start, end = get_week_range(today)
            return [e for e in expenses if parse_date(e["date"]) >= start]
        elif current_filter["period"] == "month":
            start, end = get_month_range(today)
            return [e for e in expenses if parse_date(e["date"]) >= start]
        elif current_filter["period"] == "lastweek":
            start, end = get_week_range(today)
            start = start - timedelta(days=7)
            end = start + timedelta(days=6)
            return [e for e in expenses if start <= parse_date(e["date"]) <= end]
        elif current_filter["period"] == "lastmonth":
            start, end = get_last_month_range(today)
            return [e for e in expenses if start <= parse_date(e["date"]) <= end]
        else:
            return expenses
    
    def update_display():
        for item in expense_table.get_children():
            expense_table.delete(item)
        
        expenses = get_filtered_expenses()
        
        if not expenses:
            expense_table.insert("", END, values=("No expenses", "found for this period", "", ""))
        else:
            for i, exp in enumerate(sorted(expenses, key=lambda x: x["date"], reverse=True)):
                expense_table.insert("", END, values=(
                    exp["date"],
                    exp["description"],
                    f"₱{exp['amount']:.2f}",
                    "🗑️ Delete"
                ), iid=exp["id"])
        
        # Update stats
        total = sum(e["amount"] for e in expenses)
        count = len(expenses)
        avg = total / count if count > 0 else 0
        
        total_var.set(f"₱{total:.2f}")
        count_var.set(str(count))
        avg_var.set(f"₱{avg:.2f}")
    
    def on_table_click(event):
        selection = expense_table.selection()
        if not selection:
            return
        
        col = expense_table.identify_column(event.x)
        if col == "#4":  # Action column
            item_id = selection[0]
            if delete_expense_db(int(item_id)):
                update_display()
    
    expense_table.bind("<Button-1>", on_table_click)
    
    # Action Buttons
    action_frame = Frame(content_wrapper, bg=BG_COLOR)
    action_frame.pack(fill=X, pady=15)
    
    def logout_action():
        menu_root.destroy()
    
    logout_btn = Button(action_frame, text="🚪 Logout", command=logout_action,
                       bg=DANGER_COLOR, fg="white", font=("Arial", 10, "bold"),
                       padx=20, pady=8, relief=FLAT, cursor="hand2")
    logout_btn.pack(side=RIGHT)
    
    # Initialize display
    update_display()
    menu_root.mainloop()

def run_login_gui():
    # Initialize database first
    init_database()

    login_result = {"user_id": None, "username": None, "email": None}

    root = Tk()
    root.title("💰 Expense Tracker - Login")
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
        result = login_user_db(username, password)
        if result:
            login_result["user_id"] = result[0]
            login_result["username"] = result[1]
            login_result["email"] = result[2]
            root.destroy()
        else:
            status_var.set("❌ Invalid username or password")
            status_label.after(4000, lambda: status_var.set(""))

    login_btn = Button(button_frame, text="🔓  LOGIN", command=handle_login,
                      bg=PRIMARY, fg="white", font=("Segoe UI", 11, "bold"),
                      padx=20, pady=10, relief=FLAT, cursor="hand2", bd=0)
    login_btn.pack(fill=X)

    # Register Section
    register_frame = Frame(center_frame, bg=BG_LIGHT)
    register_frame.pack(fill=X, padx=10, pady=20)

    reg_frame_label = Label(register_frame, text="Don't have an account?", font=("Segoe UI", 10),
         bg=BG_LIGHT, fg="#7f8c8d")
    reg_frame_label.pack()

    def open_register():
        register_window = Toplevel(root)
        register_window.title("💰 Expense Tracker - Register")
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

        # ID
        Label(reg_form_inner, text="ID", font=("Segoe UI", 10, "bold"), 
             bg=CARD_BG, fg=PRIMARY_DARK).pack(anchor=W, pady=(0, 5))
        reg_id_var = StringVar()
        reg_id_entry = Entry(reg_form_inner, textvariable=reg_id_var, 
                            font=("Segoe UI", 11), bd=1, relief=SUNKEN)
        reg_id_entry.pack(fill=X, ipady=8)

        # Username
        Label(reg_form_inner, text="Username", font=("Segoe UI", 10, "bold"), 
             bg=CARD_BG, fg=PRIMARY_DARK).pack(anchor=W, pady=(15, 5))
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
            id_value = reg_id_var.get().strip()
            username = reg_username_var.get().strip()
            email = reg_email_var.get().strip()
            password = reg_password_var.get()
            confirm = reg_confirm_var.get()
            
            if not username:
                reg_status_var.set("❌ Username cannot be blank")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))
                return
            if not email:
                reg_status_var.set("❌ Email cannot be blank")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))
                return
            if "@" not in email or "." not in email:
                reg_status_var.set("❌ Invalid email format")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))
                return
            if len(password) < 6:
                reg_status_var.set("❌ Password must be at least 6 characters")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))
                return
            if password != confirm:
                reg_status_var.set("❌ Passwords do not match")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))
                return
            
            if user_exists(username, email):
                reg_status_var.set("❌ Username or email already exists")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))
                return
            
            if register_user_db(username, email, password):
                reg_status_var.set("✅ Registration successful! Closing...")
                register_window.after(2000, register_window.destroy)
            else:
                reg_status_var.set("❌ Registration failed. Please try again.")
                reg_status_label.after(3000, lambda: reg_status_var.set(""))

        reg_submit_btn = Button(reg_btn_frame, text="✓  REGISTER", command=handle_register,
                               bg=PRIMARY, fg="white", font=("Segoe UI", 11, "bold"),
                               padx=20, pady=10, relief=FLAT, cursor="hand2", bd=0)
        reg_submit_btn.pack(fill=X)

    register_btn = Button(register_frame, text="📝  SIGN UP", command=open_register,
                         bg=PRIMARY, fg="white", font=("Segoe UI", 10, "bold"),
                         padx=20, pady=8, relief=FLAT, cursor="hand2", bd=0)
    register_btn.pack(pady=(10, 0))

    root.mainloop()

    if login_result["user_id"]:
        show_menu(login_result["user_id"], login_result["username"], login_result["email"])

if __name__ == "__main__":
    run_login_gui()
