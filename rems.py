import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import hashlib
import json
import os

# MySQL connector import
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror(
        "Missing Dependency",
        "mysql-connector-python is not installed.\n\n"
        "Run:  pip install mysql-connector-python\n\nThen restart the app.")
    raise SystemExit

# Config file for DB credentials 
CONFIG_FILE = "rems_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"host": "localhost", "port": "3306",
            "user": "root", "password": "", "database": "ReMS_DB"}

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

DB_CFG = load_config()

#DB connection helper

def get_db():
    conn = mysql.connector.connect(
        host=DB_CFG["host"],
        port=int(DB_CFG.get("port", 3306)),
        user=DB_CFG["user"],
        password=DB_CFG["password"],
        database=DB_CFG["database"],
        autocommit=False
    )
    return conn

def test_connection(cfg: dict):
    try:
        c = mysql.connector.connect(
            host=cfg["host"], port=int(cfg.get("port", 3306)),
            user=cfg["user"], password=cfg["password"])
        c.close()
        return True, ""
    except MySQLError as e:
        return False, str(e)

#Schema + seed data 

def init_db():
    base = mysql.connector.connect(
        host=DB_CFG["host"], port=int(DB_CFG.get("port", 3306)),
        user=DB_CFG["user"], password=DB_CFG["password"])
    cur = base.cursor()
    db_name = DB_CFG["database"]

    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute(f"USE `{db_name}`")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id       INT AUTO_INCREMENT PRIMARY KEY,
            username      VARCHAR(50)  NOT NULL UNIQUE,
            email         VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role          ENUM('Admin','Customer') DEFAULT 'Customer',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            prod_id     INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100) NOT NULL,
            description TEXT,
            price       DECIMAL(10,2) NOT NULL CHECK (price >= 0),
            stock_qty   INT NOT NULL DEFAULT 0,
            category    VARCHAR(50)
        ) ENGINE=InnoDB
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Orders (
            order_id     INT AUTO_INCREMENT PRIMARY KEY,
            user_id      INT,
            order_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount DECIMAL(10,2),
            status       ENUM('Pending','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Order_Items (
            item_id           INT AUTO_INCREMENT PRIMARY KEY,
            order_id          INT,
            prod_id           INT,
            quantity          INT NOT NULL,
            price_at_purchase DECIMAL(10,2),
            FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (prod_id)  REFERENCES Products(prod_id) ON DELETE SET NULL
        ) ENGINE=InnoDB
    """)

    base.commit()

    # Seed admin
    pw = hash_password("admin123")
    try:
        cur.execute(
            "INSERT INTO Users (username,email,password_hash,role) VALUES (%s,%s,%s,%s)",
            ("admin", "admin@rems.com", pw, "Admin"))
        base.commit()
    except MySQLError:
        pass

    # Seed products
    sample = [
        ("Wireless Headphones",  "High-quality over-ear headphones",     89.99, 25, "Electronics"),
        ("Running Shoes",        "Lightweight athletic footwear",         59.99, 40, "Footwear"),
        ("Coffee Maker",         "12-cup programmable coffee maker",      49.99, 15, "Appliances"),
        ("Python Programming Book", "Learn Python from scratch",          39.99,  3, "Books"),
        ("Yoga Mat",             "Non-slip premium yoga mat",             29.99, 50, "Fitness"),
        ("Bluetooth Speaker",    "Portable waterproof speaker",           39.99, 20, "Electronics"),
        ("Leather Wallet",       "Slim RFID-blocking wallet",             24.99,  0, "Accessories"),
        ("Desk Lamp",            "LED adjustable desk lamp",              34.99,  8, "Office"),
        ("Protein Powder",       "Whey protein chocolate flavor 2kg",     54.99, 12, "Fitness"),
        ("Mechanical Keyboard",  "RGB backlit mechanical keyboard",       99.99,  7, "Electronics"),
    ]
    for prod in sample:
        try:
            cur.execute(
                "INSERT INTO Products (name,description,price,stock_qty,category) "
                "VALUES (%s,%s,%s,%s,%s)", prod)
        except MySQLError:
            pass
    base.commit()
    cur.close(); base.close()

#  Utility functions for auth and hashing

def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

def register_user(username, email, plain_pw, role="Customer"):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Users (username,email,password_hash,role) VALUES (%s,%s,%s,%s)",
            (username, email, hash_password(plain_pw), role))
        conn.commit()
        return True, "Registration successful!"
    except MySQLError:
        return False, "Username or email already exists."
    finally:
        cur.close(); conn.close()

def login_user(username, plain_pw):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user and user["password_hash"] == hash_password(plain_pw):
            return user
        return None
    finally:
        cur.close(); conn.close()


#  DESIGN TOKENS

BG        = "#F0F4F8"
SIDEBAR   = "#1E293B"
ACCENT    = "#3B82F6"
ACCENT2   = "#10B981"
DANGER    = "#EF4444"
WARNING   = "#F59E0B"
TEXT_DARK = "#1E293B"
TEXT_MID  = "#64748B"
WHITE     = "#FFFFFF"
CARD_BG   = "#FFFFFF"
HEADER_BG = "#1E293B"

FONT_H1   = ("Segoe UI", 20, "bold")
FONT_H2   = ("Segoe UI", 14, "bold")
FONT_H3   = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_SM   = ("Segoe UI",  9)

def styled_button(parent, text, command, bg=ACCENT, fg=WHITE, width=16, **kw):
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     font=FONT_BODY, relief="flat", cursor="hand2",
                     activebackground=bg, activeforeground=fg,
                     width=width, padx=8, pady=6, **kw)

def label_entry(parent, label_text, row, show=None, bg=WHITE):
    tk.Label(parent, text=label_text, bg=bg, fg=TEXT_DARK,
             font=FONT_BODY).grid(row=row, column=0, sticky="w", padx=10, pady=6)
    var = tk.StringVar()
    tk.Entry(parent, textvariable=var, font=FONT_BODY, show=show,
             relief="solid", bd=1, width=28).grid(
                 row=row, column=1, padx=10, pady=6, sticky="ew")
    return var

def section_title(parent, text, bg=BG):
    tk.Label(parent, text=text, bg=bg, fg=TEXT_DARK,
             font=FONT_H2).pack(anchor="w", padx=20, pady=(18, 6))


#  DB CONFIGURATION DIALOG

class DBConfigDialog(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("MySQL Database Configuration – ReMS")
        self.geometry("500x430")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.grab_set()
        self.on_success = on_success
        self._build()

    def _build(self):
        tk.Label(self, text="🗄  MySQL Connection Setup",
                 bg=WHITE, fg=TEXT_DARK, font=FONT_H2).pack(pady=(20, 4))
        tk.Label(self, text="Enter your MySQL server credentials to continue.",
                 bg=WHITE, fg=TEXT_MID, font=FONT_BODY).pack(pady=(0, 14))

        form = tk.Frame(self, bg=WHITE)
        form.pack(padx=50)

        cfg = DB_CFG
        self.vars = {
            "host":     tk.StringVar(value=cfg.get("host",     "localhost")),
            "port":     tk.StringVar(value=cfg.get("port",     "3306")),
            "user":     tk.StringVar(value=cfg.get("user",     "root")),
            "password": tk.StringVar(value=cfg.get("password", "")),
            "database": tk.StringVar(value=cfg.get("database", "ReMS_DB")),
        }
        field_defs = [
            ("Host",         "host",     None),
            ("Port",         "port",     None),
            ("MySQL User",   "user",     None),
            ("Password",     "password", "•"),
            ("Database Name","database", None),
        ]
        for i, (lbl, key, show) in enumerate(field_defs):
            tk.Label(form, text=lbl, bg=WHITE, font=FONT_BODY,
                     anchor="w", width=14).grid(row=i, column=0, sticky="w", pady=6)
            tk.Entry(form, textvariable=self.vars[key], font=FONT_BODY,
                     show=show, relief="solid", bd=1, width=26).grid(
                         row=i, column=1, padx=8, pady=6)

        self.status = tk.Label(self, text="", bg=WHITE, font=FONT_SM)
        self.status.pack(pady=4)

        btn_row = tk.Frame(self, bg=WHITE)
        btn_row.pack(pady=8)
        styled_button(btn_row, "Test Connection",   self._test,    bg="#64748B", width=18).pack(side="left", padx=6)
        styled_button(btn_row, "Connect & Launch →", self._connect, bg=ACCENT2,  width=20).pack(side="left", padx=6)

        tk.Label(self, text="The database & all tables are created automatically on first run.",
                 bg=WHITE, fg=TEXT_MID, font=FONT_SM, wraplength=420).pack(pady=(4, 16))

    def _cfg(self):
        return {k: v.get().strip() if k != "password" else v.get()
                for k, v in self.vars.items()}

    def _test(self):
        self.status.config(text="Testing connection…", fg=TEXT_MID)
        self.update()
        ok, msg = test_connection(self._cfg())
        self.status.config(
            text="✅  Connection successful!" if ok else f"❌  {msg}",
            fg=ACCENT2 if ok else DANGER)

    def _connect(self):
        cfg = self._cfg()
        ok, msg = test_connection(cfg)
        if not ok:
            messagebox.showerror("Connection Failed",
                f"Cannot connect to MySQL:\n\n{msg}"); return
        global DB_CFG
        DB_CFG = cfg
        save_config(cfg)
        try:
            init_db()
        except MySQLError as e:
            messagebox.showerror("DB Init Error", str(e)); return
        self.destroy()
        self.on_success()


#  MAIN APPLICATION

class ReMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ReMS – Retail eCommerce Management System  |  MySQL")
        self.geometry("1100x700")
        self.minsize(960, 640)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.withdraw()

        self.current_user = None
        self.cart         = {}

        DBConfigDialog(self, on_success=self._after_db)

    def _after_db(self):
        self.deiconify()
        self.show_login()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_login(self):
        self.clear(); self.cart = {}; self.current_user = None
        LoginPage(self)

    def show_register(self):
        self.clear(); RegisterPage(self)

    def show_main(self):
        self.clear()
        if self.current_user["role"] == "Admin":
            AdminApp(self)
        else:
            CustomerApp(self)


#  AUTH PAGES

class LoginPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.master = master
        self._build()

    def _build(self):
        left = tk.Frame(self, bg=HEADER_BG, width=380)
        left.pack(side="left", fill="y"); left.pack_propagate(False)

        tk.Label(left, text="ReMS", bg=HEADER_BG, fg=WHITE,
                 font=("Segoe UI", 42, "bold")).place(relx=0.5, rely=0.35, anchor="center")
        tk.Label(left, text="Retail eCommerce\nManagement System",
                 bg=HEADER_BG, fg="#94A3B8",
                 font=("Segoe UI", 13)).place(relx=0.5, rely=0.47, anchor="center")
        tk.Label(left, text="🗄  MySQL Backend  ·  Python Tkinter",
                 bg=HEADER_BG, fg=ACCENT2,
                 font=FONT_SM).place(relx=0.5, rely=0.57, anchor="center")
        tk.Label(left, text="SRS Implementation  v1.0",
                 bg=HEADER_BG, fg="#475569",
                 font=FONT_SM).place(relx=0.5, rely=0.93, anchor="center")

        right = tk.Frame(self, bg=WHITE)
        right.pack(side="left", fill="both", expand=True)
        form = tk.Frame(right, bg=WHITE)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Welcome Back", bg=WHITE, fg=TEXT_DARK,
                 font=FONT_H1).grid(row=0, column=0, columnspan=2, pady=(0, 4))
        tk.Label(form, text="Sign in to your account", bg=WHITE, fg=TEXT_MID,
                 font=FONT_BODY).grid(row=1, column=0, columnspan=2, pady=(0, 20))

        self.uvar = label_entry(form, "Username", 2)
        self.pvar = label_entry(form, "Password", 3, show="•")

        styled_button(form, "Login", self._login, bg=ACCENT, width=32).grid(
            row=4, column=0, columnspan=2, pady=(16, 6), ipady=4)

        tk.Label(form, text="Don't have an account?",
                 bg=WHITE, fg=TEXT_MID, font=FONT_SM).grid(row=5, column=0, columnspan=2)
        reg = tk.Label(form, text="Register here", bg=WHITE, fg=ACCENT,
                       font=(FONT_SM[0], FONT_SM[1], "underline"), cursor="hand2")
        reg.grid(row=6, column=0, columnspan=2, pady=(2, 0))
        reg.bind("<Button-1>", lambda e: self.master.show_register())

        tk.Label(form, text="Demo  ▸  admin / admin123",
                 bg=WHITE, fg=WARNING, font=FONT_SM).grid(
                     row=7, column=0, columnspan=2, pady=(14, 0))

    def _login(self):
        u, p = self.uvar.get().strip(), self.pvar.get().strip()
        if not u or not p:
            messagebox.showwarning("Input", "Enter username and password."); return
        try:
            user = login_user(u, p)
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        if user:
            self.master.current_user = user
            self.master.show_main()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


class RegisterPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=WHITE)
        self.pack(fill="both", expand=True)
        self.master = master
        self._build()

    def _build(self):
        form = tk.Frame(self, bg=WHITE)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Create Account", bg=WHITE, fg=TEXT_DARK,
                 font=FONT_H1).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        self.uname = label_entry(form, "Username", 1)
        self.email = label_entry(form, "Email",    2)
        self.pw    = label_entry(form, "Password", 3, show="•")
        self.pw2   = label_entry(form, "Confirm",  4, show="•")

        styled_button(form, "Register", self._register,
                      bg=ACCENT2, width=32).grid(
                          row=5, column=0, columnspan=2, pady=(16, 6), ipady=4)
        styled_button(form, "← Back to Login", self.master.show_login,
                      bg="#E2E8F0", fg=TEXT_DARK, width=32).grid(
                          row=6, column=0, columnspan=2, ipady=2)

    def _register(self):
        u  = self.uname.get().strip()
        em = self.email.get().strip()
        p  = self.pw.get()
        p2 = self.pw2.get()
        if not all([u, em, p, p2]):
            messagebox.showwarning("Input", "All fields required."); return
        if p != p2:
            messagebox.showwarning("Password", "Passwords do not match."); return
        if len(p) < 6:
            messagebox.showwarning("Password", "Minimum 6 characters."); return
        try:
            ok, msg = register_user(u, em, p)
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        if ok:
            messagebox.showinfo("Success", msg); self.master.show_login()
        else:
            messagebox.showerror("Error", msg)


#  CUSTOMER APPLICATION

class CustomerApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.master = master
        self.cart   = master.cart
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=HEADER_BG, height=56)
        nav.pack(fill="x"); nav.pack_propagate(False)
        tk.Label(nav, text="🛒  ReMS", bg=HEADER_BG, fg=WHITE,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20)
        tk.Button(nav, text="Logout", command=self.master.show_login,
                  bg="#334155", fg=WHITE, relief="flat", font=FONT_SM,
                  cursor="hand2", padx=12, pady=4).pack(side="right", padx=12, pady=10)
        tk.Label(nav, text=f"Hi, {self.master.current_user['username']}",
                 bg=HEADER_BG, fg="#94A3B8", font=FONT_BODY).pack(side="right", padx=6)

        tab_bar = tk.Frame(self, bg=SIDEBAR)
        tab_bar.pack(fill="x")
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)

        self.tabs = {}
        for label, cmd in [("🏠 Shop", self.show_shop),
                            ("🛒 Cart", self.show_cart),
                            ("📦 My Orders", self.show_orders)]:
            b = tk.Button(tab_bar, text=label, command=cmd,
                          bg=SIDEBAR, fg="#94A3B8", relief="flat",
                          font=FONT_BODY, padx=20, pady=8, cursor="hand2",
                          activebackground=ACCENT, activeforeground=WHITE)
            b.pack(side="left")
            self.tabs[label] = b
        self.show_shop()

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _highlight(self, label):
        for k, b in self.tabs.items():
            b.configure(bg=SIDEBAR, fg="#94A3B8")
        self.tabs[label].configure(bg=ACCENT, fg=WHITE)

    # ── SHOP ──────────────────────────────────────────────────────────────
    def show_shop(self):
        self._clear(); self._highlight("🏠 Shop")

        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=20, pady=(14, 6))
        tk.Label(top, text="Browse Products", bg=BG, fg=TEXT_DARK,
                 font=FONT_H2).pack(side="left")
        self.search_var = tk.StringVar()
        self.cat_var    = tk.StringVar(value="All")

        tk.Entry(top, textvariable=self.search_var, font=FONT_BODY,
                 relief="solid", bd=1, width=22).pack(side="right", padx=4)
        tk.Label(top, text="Search:", bg=BG, font=FONT_BODY).pack(side="right")

        try:
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT DISTINCT category FROM Products ORDER BY category")
            cats = ["All"] + [r[0] for r in cur.fetchall() if r[0]]
            cur.close(); conn.close()
        except MySQLError:
            cats = ["All"]

        ttk.Combobox(top, textvariable=self.cat_var, values=cats,
                     state="readonly", width=14).pack(side="right", padx=(0, 4))
        tk.Label(top, text="Category:", bg=BG, font=FONT_BODY).pack(side="right")
        styled_button(top, "Search", self._load_products, width=8).pack(side="right", padx=(0, 6))

        outer = tk.Frame(self.content, bg=BG)
        outer.pack(fill="both", expand=True, padx=10, pady=4)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.grid_frame = tk.Frame(canvas, bg=BG)
        self.grid_win   = canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self.grid_win, width=e.width))
        self._load_products()

    def _load_products(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        search = self.search_var.get().strip()
        cat    = self.cat_var.get()
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            if cat == "All":
                cur.execute("SELECT * FROM Products WHERE name LIKE %s ORDER BY name",
                            (f"%{search}%",))
            else:
                cur.execute(
                    "SELECT * FROM Products WHERE name LIKE %s AND category=%s ORDER BY name",
                    (f"%{search}%", cat))
            rows = cur.fetchall()
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return

        COLS = 3
        for i, p in enumerate(rows):
            self._product_card(self.grid_frame, p, *divmod(i, COLS))
        if not rows:
            tk.Label(self.grid_frame, text="No products found.",
                     bg=BG, fg=TEXT_MID, font=FONT_H3).grid(row=0, column=0, padx=30, pady=30)

    def _product_card(self, parent, p, row, col):
        chip_map = {"Electronics": "#DBEAFE", "Footwear": "#D1FAE5",
                    "Books": "#FEF3C7", "Fitness": "#FCE7F3",
                    "Appliances": "#EDE9FE", "Accessories": "#FEE2E2", "Office": "#E0F2FE"}
        card = tk.Frame(parent, bg=CARD_BG, bd=0,
                        highlightbackground="#E2E8F0", highlightthickness=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        cat = p.get("category") or "General"
        tk.Label(card, text=cat, bg=chip_map.get(cat, "#F1F5F9"),
                 fg=TEXT_MID, font=FONT_SM, padx=6, pady=2).pack(
                     anchor="w", padx=10, pady=(10, 4))
        tk.Label(card, text=p["name"], bg=CARD_BG, fg=TEXT_DARK,
                 font=FONT_H3, wraplength=200, justify="left").pack(anchor="w", padx=10)
        tk.Label(card, text=p.get("description") or "", bg=CARD_BG,
                 fg=TEXT_MID, font=FONT_SM, wraplength=200, justify="left").pack(
                     anchor="w", padx=10, pady=(2, 6))
        tk.Label(card, text=f"${float(p['price']):.2f}", bg=CARD_BG,
                 fg=ACCENT, font=FONT_H2).pack(anchor="w", padx=10)

        sq = int(p["stock_qty"])
        if sq == 0:   badge, bcol = "Out of Stock",          DANGER
        elif sq <= 5: badge, bcol = f"Low Stock: {sq} left", WARNING
        else:         badge, bcol = f"In Stock ({sq})",       ACCENT2
        tk.Label(card, text=badge, bg=CARD_BG, fg=bcol, font=FONT_SM).pack(
            anchor="w", padx=10, pady=(2, 8))

        styled_button(card,
                      "Add to Cart" if sq > 0 else "Unavailable",
                      lambda pid=p["prod_id"], n=p["name"], pr=float(p["price"]):
                          self._add_to_cart(pid, n, pr),
                      bg=ACCENT if sq > 0 else "#CBD5E1", width=22,
                      state="normal" if sq > 0 else "disabled").pack(padx=10, pady=(0, 12))

    def _add_to_cart(self, prod_id, name, price):
        if prod_id in self.cart:
            self.cart[prod_id]["qty"] += 1
        else:
            self.cart[prod_id] = {"name": name, "price": price, "qty": 1}
        total = sum(v["qty"] for v in self.cart.values())
        messagebox.showinfo("Added ✓", f"'{name}' added!\nTotal items in cart: {total}")

    # ── CART ──────────────────────────────────────────────────────────────
    def show_cart(self):
        self._clear(); self._highlight("🛒 Cart")
        section_title(self.content, "🛒 Shopping Cart")
        if not self.cart:
            tk.Label(self.content, text="Your cart is empty.",
                     bg=BG, fg=TEXT_MID, font=FONT_H3).pack(pady=40)
            styled_button(self.content, "← Continue Shopping",
                          self.show_shop, bg="#E2E8F0", fg=TEXT_DARK).pack()
            return

        cols = ("Product", "Unit Price", "Qty", "Subtotal")
        tree = ttk.Treeview(self.content, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180 if col == "Product" else 120, anchor="center")
        tree.column("Product", anchor="w")
        tree.pack(fill="x", padx=20, pady=10)
        self._cart_tree = tree
        self._refresh_cart()

        row = tk.Frame(self.content, bg=BG)
        row.pack(padx=20, pady=6, fill="x")
        styled_button(row, "Remove Selected", self._remove_sel, bg=DANGER, width=18).pack(
            side="left", padx=(0, 8))
        styled_button(row, "Clear Cart", self._clear_cart, bg="#64748B", width=14).pack(side="left")

        total = sum(v["price"] * v["qty"] for v in self.cart.values())
        tk.Label(self.content, text=f"Order Total:  ${total:.2f}",
                 bg=BG, fg=TEXT_DARK, font=FONT_H2).pack(anchor="e", padx=24, pady=6)
        styled_button(self.content, "Proceed to Checkout →",
                      self._checkout, bg=ACCENT2, width=24).pack(anchor="e", padx=24, pady=4)

    def _refresh_cart(self):
        self._cart_tree.delete(*self._cart_tree.get_children())
        for pid, item in self.cart.items():
            self._cart_tree.insert("", "end", iid=str(pid),
                values=(item["name"], f"${item['price']:.2f}",
                        item["qty"], f"${item['price']*item['qty']:.2f}"))

    def _remove_sel(self):
        for iid in self._cart_tree.selection():
            self.cart.pop(int(iid), None)
        self.show_cart()

    def _clear_cart(self):
        if messagebox.askyesno("Clear Cart", "Remove all items?"):
            self.cart.clear(); self.show_cart()

    def _checkout(self):
        if not self.cart:
            messagebox.showinfo("Cart", "Cart is empty."); return
        CheckoutDialog(self)

    # ── MY ORDERS ─────────────────────────────────────────────────────────
    def show_orders(self):
        self._clear(); self._highlight("📦 My Orders")
        section_title(self.content, "📦 My Order History")

        uid = self.master.current_user["user_id"]
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM Orders WHERE user_id=%s ORDER BY order_date DESC", (uid,))
            orders = cur.fetchall()
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return

        if not orders:
            tk.Label(self.content, text="No orders yet. Start shopping!",
                     bg=BG, fg=TEXT_MID, font=FONT_H3).pack(pady=40); return

        outer = tk.Frame(self.content, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=10)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        sc_map = {"Pending": WARNING, "Shipped": ACCENT,
                  "Delivered": ACCENT2, "Cancelled": DANGER}
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            for order in orders:
                oid = order["order_id"]
                cur.execute("""SELECT oi.quantity, oi.price_at_purchase, p.name
                               FROM Order_Items oi
                               JOIN Products p ON oi.prod_id=p.prod_id
                               WHERE oi.order_id=%s""", (oid,))
                items = cur.fetchall()
                sc = sc_map.get(order["status"], TEXT_MID)

                card = tk.Frame(inner, bg=CARD_BG, bd=0,
                                highlightbackground="#E2E8F0", highlightthickness=1)
                card.pack(fill="x", pady=6)
                hdr = tk.Frame(card, bg=CARD_BG)
                hdr.pack(fill="x", padx=14, pady=(10, 4))
                tk.Label(hdr, text=f"Order #{oid}", bg=CARD_BG, fg=TEXT_DARK,
                         font=FONT_H3).pack(side="left")
                tk.Label(hdr, text=order["status"], bg=sc, fg=WHITE,
                         font=FONT_SM, padx=8, pady=2).pack(side="right")
                tk.Label(hdr,
                         text=f"  {str(order['order_date'])[:10]}  |  "
                              f"${float(order['total_amount']):.2f}",
                         bg=CARD_BG, fg=TEXT_MID, font=FONT_SM).pack(side="left", padx=14)
                for it in items:
                    tk.Label(card,
                             text=f"  • {it['name']}  × {it['quantity']}  "
                                  f"@ ${float(it['price_at_purchase']):.2f}",
                             bg=CARD_BG, fg=TEXT_MID, font=FONT_SM).pack(anchor="w", padx=20)
                tk.Frame(card, height=6, bg=CARD_BG).pack()
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e))


class CheckoutDialog(tk.Toplevel):
    def __init__(self, cust_app):
        super().__init__(cust_app)
        self.title("Checkout")
        self.geometry("480x430")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.grab_set()
        self.app = cust_app
        self._build()

    def _build(self):
        tk.Label(self, text="Checkout", bg=WHITE, fg=TEXT_DARK,
                 font=FONT_H1).pack(pady=(20, 10))

        cart  = self.app.cart
        total = sum(v["price"] * v["qty"] for v in cart.values())

        frame = tk.Frame(self, bg=WHITE)
        frame.pack(fill="x", padx=30)
        for item in cart.values():
            tk.Label(frame,
                     text=f"• {item['name']}  × {item['qty']}  =  "
                          f"${item['price']*item['qty']:.2f}",
                     bg=WHITE, fg=TEXT_DARK, font=FONT_BODY).pack(anchor="w")

        tk.Frame(self, height=1, bg="#E2E8F0").pack(fill="x", padx=30, pady=8)
        tk.Label(self, text=f"Order Total:  ${total:.2f}",
                 bg=WHITE, fg=ACCENT, font=FONT_H2).pack()
        tk.Label(self, text="Select Payment Method",
                 bg=WHITE, fg=TEXT_DARK, font=FONT_H3).pack(pady=(14, 4))

        self.pay_var = tk.StringVar(value="Credit Card")
        for opt in ["Credit Card", "Debit Card", "PayPal", "Cash on Delivery"]:
            tk.Radiobutton(self, text=opt, variable=self.pay_var, value=opt,
                           bg=WHITE, font=FONT_BODY).pack(anchor="w", padx=40)

        styled_button(self, "Place Order ✓", self._place_order,
                      bg=ACCENT2, width=26).pack(pady=(16, 4))
        styled_button(self, "Cancel", self.destroy,
                      bg="#E2E8F0", fg=TEXT_DARK, width=26).pack()

    def _place_order(self):
        cart  = self.app.cart
        uid   = self.app.master.current_user["user_id"]
        total = sum(v["price"] * v["qty"] for v in cart.values())

        conn = get_db(); cur = conn.cursor()
        try:
            conn.start_transaction()

            # Lock rows & validate stock (MySQL FOR UPDATE = atomic)
            for pid, item in cart.items():
                cur.execute(
                    "SELECT stock_qty FROM Products WHERE prod_id=%s FOR UPDATE", (pid,))
                row = cur.fetchone()
                if not row or row[0] < item["qty"]:
                    raise Exception(f"Insufficient stock for '{item['name']}'")

            cur.execute(
                "INSERT INTO Orders (user_id,total_amount,status) VALUES (%s,%s,%s)",
                (uid, total, "Pending"))
            oid = cur.lastrowid

            for pid, item in cart.items():
                cur.execute(
                    "INSERT INTO Order_Items "
                    "(order_id,prod_id,quantity,price_at_purchase) VALUES (%s,%s,%s,%s)",
                    (oid, pid, item["qty"], item["price"]))
                cur.execute(
                    "UPDATE Products SET stock_qty = stock_qty - %s WHERE prod_id=%s",
                    (item["qty"], pid))

            conn.commit()
            cart.clear()
            self.destroy()
            messagebox.showinfo("Order Placed ✓",
                f"Order #{oid} placed!\nTotal: ${total:.2f}\n"
                f"Payment: {self.pay_var.get()}\n\nTrack it in 'My Orders'.")
            self.app.show_orders()
        except Exception as ex:
            conn.rollback()
            messagebox.showerror("Order Failed", str(ex))
        finally:
            cur.close(); conn.close()

#  ADMIN APPLICATION

class AdminApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.master = master
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=HEADER_BG, height=56)
        nav.pack(fill="x"); nav.pack_propagate(False)
        tk.Label(nav, text="ReMS  Admin Panel", bg=HEADER_BG, fg=WHITE,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20)
        tk.Label(nav, text="🗄 MySQL", bg=HEADER_BG, fg=ACCENT2,
                 font=FONT_BODY).pack(side="left")
        tk.Button(nav, text="Logout", command=self.master.show_login,
                  bg="#334155", fg=WHITE, relief="flat", font=FONT_SM,
                  cursor="hand2", padx=12, pady=4).pack(side="right", padx=12, pady=10)
        tk.Label(nav, text=f"👤 {self.master.current_user['username']}",
                 bg=HEADER_BG, fg="#94A3B8", font=FONT_BODY).pack(side="right", padx=6)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        sidebar = tk.Frame(body, bg=SIDEBAR, width=200)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.nav_btns = {}
        menu = [("📊 Dashboard",  self.show_dashboard),
                ("📦 Inventory",  self.show_inventory),
                ("🛒 Orders",     self.show_orders),
                ("👥 Users",      self.show_users),
                ("⚠️ Low Stock",  self.show_low_stock)]
        tk.Frame(sidebar, height=20, bg=SIDEBAR).pack()
        for label, cmd in menu:
            b = tk.Button(sidebar, text=label, command=cmd,
                          bg=SIDEBAR, fg="#94A3B8", relief="flat",
                          font=FONT_BODY, anchor="w", padx=20, pady=10,
                          cursor="hand2", activebackground=ACCENT,
                          activeforeground=WHITE, width=18)
            b.pack(fill="x")
            self.nav_btns[label] = b
        self.show_dashboard()

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _highlight(self, label):
        for k, b in self.nav_btns.items():
            b.configure(bg=SIDEBAR, fg="#94A3B8")
        self.nav_btns[label].configure(bg=ACCENT, fg=WHITE)

    # ── DASHBOARD ─────────────────────────────────────────────────────────
    def show_dashboard(self):
        self._clear(); self._highlight("📊 Dashboard")
        section_title(self.content, "📊 Analytics Dashboard")

        try:
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM Orders WHERE status!='Cancelled'")
            total_sales = float(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM Orders");                    total_orders = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Users WHERE role='Customer'"); total_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Products");                  total_prods  = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Products WHERE stock_qty<=5"); low_stock   = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Orders WHERE status='Pending'"); pending   = cur.fetchone()[0]
            cur.execute("""SELECT o.order_id,u.username,o.total_amount,o.status,o.order_date
                           FROM Orders o JOIN Users u ON o.user_id=u.user_id
                           ORDER BY o.order_date DESC LIMIT 8""")
            recent = cur.fetchall()
            cur.execute("""SELECT p.category,
                                  COALESCE(SUM(oi.quantity*oi.price_at_purchase),0) AS rev
                           FROM Products p
                           LEFT JOIN Order_Items oi ON p.prod_id=oi.prod_id
                           GROUP BY p.category ORDER BY rev DESC""")
            cat_sales = cur.fetchall()
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return

        # KPI cards
        kpi_row = tk.Frame(self.content, bg=BG)
        kpi_row.pack(fill="x", padx=20, pady=4)
        for title, val, color in [
                ("Total Revenue",  f"${total_sales:,.2f}", ACCENT),
                ("Total Orders",   str(total_orders),       ACCENT2),
                ("Customers",      str(total_users),         "#8B5CF6"),
                ("Products",       str(total_prods),         "#F59E0B"),
                ("Low Stock",      str(low_stock),           DANGER),
                ("Pending Orders", str(pending),             WARNING)]:
            card = tk.Frame(kpi_row, bg=color, width=145, height=90)
            card.pack(side="left", padx=5, pady=6); card.pack_propagate(False)
            tk.Label(card, text=val,   bg=color, fg=WHITE, font=FONT_H1).pack(pady=(14, 0))
            tk.Label(card, text=title, bg=color, fg=WHITE, font=FONT_SM).pack()

        cols = tk.Frame(self.content, bg=BG)
        cols.pack(fill="both", expand=True, padx=20, pady=6)
        left  = tk.Frame(cols, bg=BG); left.pack(side="left",  fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(cols, bg=BG); right.pack(side="left", fill="both", expand=True)

        # Recent orders
        tk.Label(left, text="Recent Orders", bg=BG, fg=TEXT_DARK, font=FONT_H3).pack(anchor="w")
        col_defs = ("ID", "Customer", "Total", "Status", "Date")
        tree = ttk.Treeview(left, columns=col_defs, show="headings", height=7)
        for col in col_defs:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")
        tree.column("Customer", width=120)
        for r in recent:
            tree.insert("", "end",
                values=(r[0], r[1], f"${float(r[2]):.2f}", r[3], str(r[4])[:10]))
        tree.pack(fill="x", pady=4)

        # Category revenue bars
        tk.Label(right, text="Revenue by Category", bg=BG, fg=TEXT_DARK,
                 font=FONT_H3).pack(anchor="w", pady=(0, 4))
        max_rev = max((float(r[1]) for r in cat_sales), default=1) or 1
        for r in cat_sales:
            row_f = tk.Frame(right, bg=BG); row_f.pack(fill="x", pady=2)
            tk.Label(row_f, text=r[0] or "N/A", bg=BG, fg=TEXT_DARK,
                     font=FONT_SM, width=14, anchor="w").pack(side="left")
            bar_w = max(4, int((float(r[1]) / max_rev) * 160))
            tk.Frame(row_f, bg=ACCENT, width=bar_w, height=16).pack(side="left")
            tk.Label(row_f, text=f"  ${float(r[1]):.0f}",
                     bg=BG, fg=TEXT_MID, font=FONT_SM).pack(side="left")

    # ── INVENTORY ─────────────────────────────────────────────────────────
    def show_inventory(self):
        self._clear(); self._highlight("📦 Inventory")

        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=20, pady=(14, 4))
        tk.Label(top, text="📦 Product Inventory", bg=BG, fg=TEXT_DARK,
                 font=FONT_H2).pack(side="left")
        styled_button(top, "+ Add Product", self._add_product,
                      bg=ACCENT2, width=14).pack(side="right")

        cols = ("ID", "Name", "Category", "Price", "Stock", "Description")
        tree = ttk.Treeview(self.content, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col, command=lambda c=col: self._sort(tree, c, False))
            tree.column(col, width=100, anchor="center")
        tree.column("Name",        width=160, anchor="w")
        tree.column("Description", width=220, anchor="w")

        vsb = ttk.Scrollbar(self.content, orient="vertical",   command=tree.yview)
        hsb = ttk.Scrollbar(self.content, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True, padx=20, pady=4)
        self._inv_tree = tree
        self._load_inventory()

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(padx=20, pady=6, anchor="w")
        styled_button(btns, "Edit",    self._edit_product,   bg=ACCENT,    width=12).pack(side="left", padx=(0, 6))
        styled_button(btns, "Delete",  self._delete_product, bg=DANGER,    width=12).pack(side="left", padx=(0, 6))
        styled_button(btns, "Refresh", self._load_inventory, bg="#64748B",  width=10).pack(side="left")

    def _load_inventory(self):
        tree = self._inv_tree
        tree.delete(*tree.get_children())
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM Products ORDER BY prod_id")
            for p in cur.fetchall():
                sq  = int(p["stock_qty"])
                tag = "low" if 0 < sq <= 5 else ("out" if sq == 0 else "")
                tree.insert("", "end", iid=str(p["prod_id"]), tags=(tag,),
                    values=(p["prod_id"], p["name"], p["category"] or "",
                            f"${float(p['price']):.2f}", sq, p["description"] or ""))
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e))
        tree.tag_configure("low", background="#FEF3C7")
        tree.tag_configure("out", background="#FEE2E2")

    def _sort(self, tree, col, reverse):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0].replace("$", "")), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for i, (_, k) in enumerate(data):
            tree.move(k, "", i)
        tree.heading(col, command=lambda: self._sort(tree, col, not reverse))

    def _add_product(self):    ProductDialog(self, mode="add")

    def _edit_product(self):
        sel = self._inv_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a product first."); return
        pid = int(sel[0])
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM Products WHERE prod_id=%s", (pid,))
            p = cur.fetchone(); cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        ProductDialog(self, mode="edit", product=p)

    def _delete_product(self):
        sel = self._inv_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a product first."); return
        pid = int(sel[0])
        if messagebox.askyesno("Delete", f"Delete product ID {pid}?"):
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute("DELETE FROM Products WHERE prod_id=%s", (pid,))
                conn.commit(); cur.close(); conn.close()
                self._load_inventory()
            except MySQLError as e:
                messagebox.showerror("MySQL Error", str(e))

    # ── ORDERS ────────────────────────────────────────────────────────────
    def show_orders(self):
        self._clear(); self._highlight("🛒 Orders")

        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=20, pady=(14, 4))
        tk.Label(top, text="🛒 Order Management", bg=BG, fg=TEXT_DARK, font=FONT_H2).pack(side="left")
        self._ord_filter = tk.StringVar(value="All")
        ttk.Combobox(top, textvariable=self._ord_filter,
                     values=["All","Pending","Shipped","Delivered","Cancelled"],
                     state="readonly", width=14).pack(side="right", padx=4)
        tk.Label(top, text="Filter:", bg=BG, font=FONT_BODY).pack(side="right")
        styled_button(top, "Apply", self._load_orders, width=8).pack(side="right", padx=(0, 4))

        cols = ("ID", "Customer", "Date", "Total", "Status")
        tree = ttk.Treeview(self.content, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.column("Customer", width=160, anchor="w")

        vsb = ttk.Scrollbar(self.content, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=20, pady=4)
        self._ord_tree = tree
        self._load_orders()

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(padx=20, pady=4, anchor="w")
        for status, color in [("Shipped", ACCENT), ("Delivered", ACCENT2), ("Cancelled", DANGER)]:
            styled_button(btns, f"Mark {status}",
                          lambda s=status: self._update_status(s),
                          bg=color, width=14).pack(side="left", padx=(0, 6))

        tk.Label(self.content, text="Order Items (click row):",
                 bg=BG, fg=TEXT_MID, font=FONT_SM).pack(anchor="w", padx=20)
        self._items_lbl = tk.Label(self.content, text="", bg=BG, fg=TEXT_DARK,
                                   font=FONT_BODY, justify="left")
        self._items_lbl.pack(anchor="w", padx=30, pady=(0, 8))
        tree.bind("<<TreeviewSelect>>", self._on_ord_select)

    def _load_orders(self):
        self._ord_tree.delete(*self._ord_tree.get_children())
        sf = self._ord_filter.get()
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            if sf == "All":
                cur.execute("""SELECT o.*, u.username FROM Orders o
                               JOIN Users u ON o.user_id=u.user_id
                               ORDER BY o.order_date DESC""")
            else:
                cur.execute("""SELECT o.*, u.username FROM Orders o
                               JOIN Users u ON o.user_id=u.user_id
                               WHERE o.status=%s ORDER BY o.order_date DESC""", (sf,))
            rows = cur.fetchall(); cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return

        bg_map = {"Pending":"#FEF3C7","Shipped":"#DBEAFE","Delivered":"#D1FAE5","Cancelled":"#FEE2E2"}
        for r in rows:
            self._ord_tree.insert("", "end", iid=str(r["order_id"]), tags=(r["status"],),
                values=(r["order_id"], r["username"], str(r["order_date"])[:10],
                        f"${float(r['total_amount']):.2f}", r["status"]))
        for s, bg in bg_map.items():
            self._ord_tree.tag_configure(s, background=bg)

    def _on_ord_select(self, e):
        sel = self._ord_tree.selection()
        if not sel: return
        oid = int(sel[0])
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT oi.quantity, oi.price_at_purchase, p.name
                           FROM Order_Items oi JOIN Products p ON oi.prod_id=p.prod_id
                           WHERE oi.order_id=%s""", (oid,))
            items = cur.fetchall(); cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        self._items_lbl.configure(
            text="\n".join(f"  • {it['name']}  × {it['quantity']}  "
                           f"@ ${float(it['price_at_purchase']):.2f}" for it in items)
            or "No items.")

    def _update_status(self, new_status):
        sel = self._ord_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select an order first."); return
        oid = int(sel[0])
        if messagebox.askyesno("Confirm", f"Set Order #{oid} to '{new_status}'?"):
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute("UPDATE Orders SET status=%s WHERE order_id=%s", (new_status, oid))
                conn.commit(); cur.close(); conn.close(); self._load_orders()
            except MySQLError as e:
                messagebox.showerror("MySQL Error", str(e))

    # ── USERS ─────────────────────────────────────────────────────────────
    def show_users(self):
        self._clear(); self._highlight("👥 Users")
        section_title(self.content, "👥 User Management")

        cols = ("ID", "Username", "Email", "Role", "Joined", "Orders")
        tree = ttk.Treeview(self.content, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")
        tree.column("Email", width=200, anchor="w")

        vsb = ttk.Scrollbar(self.content, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=20, pady=4)
        self._usr_tree = tree

        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT u.*,
                                  (SELECT COUNT(*) FROM Orders o WHERE o.user_id=u.user_id) AS ocount
                           FROM Users u ORDER BY u.user_id""")
            for u in cur.fetchall():
                tree.insert("", "end", iid=str(u["user_id"]),
                    values=(u["user_id"], u["username"], u["email"],
                            u["role"], str(u["created_at"])[:10], u["ocount"]))
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e))

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(padx=20, pady=6, anchor="w")
        styled_button(btns, "Toggle Admin/Customer", self._toggle_role,
                      bg=WARNING, fg=WHITE, width=22).pack(side="left", padx=(0, 6))
        styled_button(btns, "Delete User", self._delete_user,
                      bg=DANGER, width=14).pack(side="left")

    def _toggle_role(self):
        sel = self._usr_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a user first."); return
        uid = int(sel[0])
        if uid == self.master.current_user["user_id"]:
            messagebox.showwarning("Error", "Cannot modify your own account."); return
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT role FROM Users WHERE user_id=%s", (uid,))
            new_role = "Admin" if cur.fetchone()["role"] == "Customer" else "Customer"
            if messagebox.askyesno("Confirm", f"Change role to '{new_role}'?"):
                cur.execute("UPDATE Users SET role=%s WHERE user_id=%s", (new_role, uid))
                conn.commit()
            cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        self.show_users()

    def _delete_user(self):
        sel = self._usr_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a user first."); return
        uid = int(sel[0])
        if uid == self.master.current_user["user_id"]:
            messagebox.showwarning("Error", "Cannot delete your own account."); return
        if messagebox.askyesno("Delete", f"Permanently delete User ID {uid}?"):
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute("DELETE FROM Users WHERE user_id=%s", (uid,))
                conn.commit(); cur.close(); conn.close(); self.show_users()
            except MySQLError as e:
                messagebox.showerror("MySQL Error", str(e))

    # ── LOW STOCK ─────────────────────────────────────────────────────────
    def show_low_stock(self):
        self._clear(); self._highlight("⚠️ Low Stock")
        section_title(self.content, "⚠️ Low Stock Alerts")

        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(top, text="Alert threshold (stock ≤):", bg=BG, font=FONT_BODY).pack(side="left")
        self._thresh = tk.IntVar(value=5)
        tk.Spinbox(top, from_=1, to=100, textvariable=self._thresh,
                   width=6, font=FONT_BODY).pack(side="left", padx=6)
        styled_button(top, "Refresh",          self._load_low, width=10).pack(side="left")
        styled_button(top, "Restock Selected", self._restock,  bg=ACCENT2, width=18).pack(side="right")

        cols = ("ID", "Name", "Category", "Stock", "Price", "Status")
        tree = ttk.Treeview(self.content, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")
        tree.column("Name", width=190, anchor="w")

        vsb = ttk.Scrollbar(self.content, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=20, pady=4)
        self._ls_tree = tree
        self._load_low()

    def _load_low(self):
        self._ls_tree.delete(*self._ls_tree.get_children())
        thresh = self._thresh.get()
        try:
            conn = get_db(); cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM Products WHERE stock_qty <= %s ORDER BY stock_qty", (thresh,))
            rows = cur.fetchall(); cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        for p in rows:
            sq     = int(p["stock_qty"])
            status = "Out of Stock" if sq == 0 else f"Low ({sq})"
            tag    = "out" if sq == 0 else "low"
            self._ls_tree.insert("", "end", iid=str(p["prod_id"]), tags=(tag,),
                values=(p["prod_id"], p["name"], p["category"] or "",
                        sq, f"${float(p['price']):.2f}", status))
        self._ls_tree.tag_configure("out", background="#FEE2E2")
        self._ls_tree.tag_configure("low", background="#FEF3C7")

    def _restock(self):
        sel = self._ls_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a product to restock."); return
        pid = int(sel[0])
        qty = simpledialog.askinteger("Restock", "Quantity to add:", minvalue=1)
        if qty:
            try:
                conn = get_db(); cur = conn.cursor()
                cur.execute(
                    "UPDATE Products SET stock_qty = stock_qty + %s WHERE prod_id=%s", (qty, pid))
                conn.commit(); cur.close(); conn.close()
                self._load_low()
                messagebox.showinfo("Restocked", f"Added {qty} units successfully.")
            except MySQLError as e:
                messagebox.showerror("MySQL Error", str(e))


#  PRODUCT CRUD DIALOG

class ProductDialog(tk.Toplevel):
    def __init__(self, admin_app, mode="add", product=None):
        super().__init__(admin_app)
        self.admin_app = admin_app
        self.mode      = mode
        self.product   = product or {}
        self.title("Add Product" if mode == "add" else "Edit Product")
        self.geometry("440x430")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.grab_set()
        self._build()

    def _build(self):
        title = "Add New Product" if self.mode == "add" else f"Edit  ·  {self.product.get('name','')}"
        tk.Label(self, text=title, bg=WHITE, fg=TEXT_DARK, font=FONT_H2).pack(pady=(18, 10))

        form = tk.Frame(self, bg=WHITE)
        form.pack(padx=40, fill="x")

        self.name_var  = tk.StringVar(value=self.product.get("name",      ""))
        self.cat_var   = tk.StringVar(value=self.product.get("category",  ""))
        self.price_var = tk.StringVar(value=str(self.product.get("price", "")))
        self.stock_var = tk.StringVar(value=str(self.product.get("stock_qty", "")))
        self.desc_var  = tk.StringVar(value=self.product.get("description",""))

        for i, (lbl, var) in enumerate([
                ("Name *",       self.name_var),
                ("Category",     self.cat_var),
                ("Price ($) *",  self.price_var),
                ("Stock Qty *",  self.stock_var),
                ("Description",  self.desc_var)]):
            tk.Label(form, text=lbl, bg=WHITE, font=FONT_BODY,
                     anchor="w", width=14).grid(row=i, column=0, sticky="w", pady=6)
            tk.Entry(form, textvariable=var, font=FONT_BODY,
                     relief="solid", bd=1, width=24).grid(row=i, column=1, padx=8, pady=6)

        btn_row = tk.Frame(self, bg=WHITE)
        btn_row.pack(pady=16)
        styled_button(btn_row, "💾 Save",  self._save,    bg=ACCENT2,      width=14).pack(side="left", padx=6)
        styled_button(btn_row, "Cancel", self.destroy, bg="#E2E8F0", fg=TEXT_DARK, width=10).pack(side="left")

    def _save(self):
        name = self.name_var.get().strip()
        cat  = self.cat_var.get().strip()
        desc = self.desc_var.get().strip()
        if not name:
            messagebox.showwarning("Input", "Product name is required."); return
        try:
            price = float(self.price_var.get())
            stock = int(self.stock_var.get())
            if price < 0 or stock < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Input", "Price/Stock must be valid non-negative numbers."); return
        try:
            conn = get_db(); cur = conn.cursor()
            if self.mode == "add":
                cur.execute(
                    "INSERT INTO Products (name,description,price,stock_qty,category) "
                    "VALUES (%s,%s,%s,%s,%s)", (name, desc, price, stock, cat))
            else:
                cur.execute(
                    "UPDATE Products SET name=%s,description=%s,price=%s,"
                    "stock_qty=%s,category=%s WHERE prod_id=%s",
                    (name, desc, price, stock, cat, self.product["prod_id"]))
            conn.commit(); cur.close(); conn.close()
        except MySQLError as e:
            messagebox.showerror("MySQL Error", str(e)); return
        self.admin_app._load_inventory()
        self.destroy()

#  ENTRY POINT

if __name__ == "__main__":
    app = ReMSApp()
    app.mainloop()