"""Database manager: SQLite schema, CRUD operations for all tables."""

import sqlite3
import threading
import json
from typing import Optional
from utils.constants import DEFAULT_CATEGORIES
from utils.helpers import today_str, current_month_year


class DatabaseManager:
    """Thread-safe SQLite database operations."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        with self._lock:
            c = self.conn.cursor()
            c.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    icon TEXT DEFAULT 'other',
                    color TEXT DEFAULT '#6C7B95',
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category_id INTEGER NOT NULL,
                    merchant TEXT,
                    description TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT,
                    is_recurring INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                );

                CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
                CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category_id);

                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    amount_borrowed REAL NOT NULL,
                    amount_paid REAL DEFAULT 0,
                    remaining REAL NOT NULL,
                    status TEXT DEFAULT 'active',
                    due_date TEXT,
                    interest_rate REAL DEFAULT 0,
                    notes TEXT,
                    date TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);

                CREATE TABLE IF NOT EXISTS loan_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_loan_payments_loan ON loan_payments(loan_id);

                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    monthly_limit REAL NOT NULL,
                    month_year TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    UNIQUE(category_id, month_year)
                );

                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    action_type TEXT,
                    action_data TEXT,
                    timestamp TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    is_recurring INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE INDEX IF NOT EXISTS idx_income_date ON income(date);
            """)
            self.conn.commit()

    def _insert_default_categories(self):
        with self._lock:
            c = self.conn.cursor()
            for name, icon, color in DEFAULT_CATEGORIES:
                c.execute(
                    "INSERT OR IGNORE INTO categories (name, icon, color, is_default) VALUES (?, ?, ?, 1)",
                    (name, icon, color),
                )
            self.conn.commit()

    def initialize_defaults(self):
        self._insert_default_categories()

    # --- Settings ---
    def get_setting(self, key: str) -> Optional[str]:
        with self._lock:
            row = self.conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str):
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now', 'localtime'))",
                (key, value),
            )
            self.conn.commit()

    # --- Categories ---
    def get_categories(self) -> list[dict]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def get_category_by_name(self, name: str) -> Optional[dict]:
        with self._lock:
            # Exact match
            row = self.conn.execute(
                "SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()
            if row:
                return dict(row)
            # Partial match (e.g., "food" matches "Food & Dining")
            row = self.conn.execute(
                "SELECT * FROM categories WHERE LOWER(name) LIKE ? LIMIT 1",
                (f"%{name.lower()}%",),
            ).fetchone()
            if row:
                return dict(row)
        # Fuzzy match
        categories = self.get_categories()
        from utils.helpers import fuzzy_match
        cat_names = [c["name"] for c in categories]
        matched = fuzzy_match(name, cat_names, threshold=55)
        if matched:
            return next((c for c in categories if c["name"] == matched), None)
        return None

    def get_category_id(self, name: str) -> int:
        cat = self.get_category_by_name(name)
        if cat:
            return cat["id"]
        # Default to "Other"
        other = self.get_category_by_name("Other")
        return other["id"] if other else 1

    # --- Expenses ---
    def add_expense(self, amount: float, category_id: int, description: str,
                    date: str, merchant: str = None, time: str = None,
                    notes: str = None) -> int:
        with self._lock:
            c = self.conn.execute(
                """INSERT INTO expenses (amount, category_id, merchant, description, date, time, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (amount, category_id, merchant, description, date, time, notes),
            )
            self.conn.commit()
            return c.lastrowid

    def get_expenses(self, start_date: str = None, end_date: str = None,
                     category_id: int = None, limit: int = 50) -> list[dict]:
        with self._lock:
            query = """SELECT e.*, c.name as category_name, c.color as category_color
                       FROM expenses e JOIN categories c ON e.category_id = c.id WHERE 1=1"""
            params = []
            if start_date:
                query += " AND e.date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND e.date <= ?"
                params.append(end_date)
            if category_id:
                query += " AND e.category_id = ?"
                params.append(category_id)
            query += " ORDER BY e.date DESC, e.created_at DESC LIMIT ?"
            params.append(limit)
            rows = self.conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def search_expenses(self, description_like: str = None, amount: float = None,
                        date: str = None, limit: int = 10) -> list[dict]:
        with self._lock:
            query = """SELECT e.*, c.name as category_name FROM expenses e
                       JOIN categories c ON e.category_id = c.id WHERE 1=1"""
            params = []
            if description_like:
                query += " AND (LOWER(e.description) LIKE ? OR LOWER(e.merchant) LIKE ?)"
                like = f"%{description_like.lower()}%"
                params.extend([like, like])
            if amount is not None:
                query += " AND e.amount = ?"
                params.append(amount)
            if date:
                query += " AND e.date = ?"
                params.append(date)
            query += " ORDER BY e.date DESC LIMIT ?"
            params.append(limit)
            rows = self.conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def delete_expense(self, expense_id: int) -> bool:
        with self._lock:
            c = self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            return c.rowcount > 0

    def update_expense(self, expense_id: int, **kwargs) -> bool:
        allowed = {"amount", "category_id", "merchant", "description", "date", "time", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        with self._lock:
            sets = ", ".join(f"{k} = ?" for k in updates)
            sets += ", updated_at = datetime('now', 'localtime')"
            vals = list(updates.values()) + [expense_id]
            c = self.conn.execute(f"UPDATE expenses SET {sets} WHERE id = ?", vals)
            self.conn.commit()
            return c.rowcount > 0

    def get_expense_summary(self, start_date: str, end_date: str) -> dict:
        with self._lock:
            rows = self.conn.execute(
                """SELECT c.name, c.color, SUM(e.amount) as total, COUNT(e.id) as count
                   FROM expenses e JOIN categories c ON e.category_id = c.id
                   WHERE e.date >= ? AND e.date <= ?
                   GROUP BY c.id ORDER BY total DESC""",
                (start_date, end_date),
            ).fetchall()
            return {
                "categories": [dict(r) for r in rows],
                "total": sum(r["total"] for r in rows),
            }

    def get_daily_totals(self, start_date: str, end_date: str) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT date, SUM(amount) as total FROM expenses
                   WHERE date >= ? AND date <= ? GROUP BY date ORDER BY date""",
                (start_date, end_date),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_total_spent(self, start_date: str, end_date: str) -> float:
        with self._lock:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date <= ?",
                (start_date, end_date),
            ).fetchone()
            return row["total"]

    # --- Loans ---
    def add_loan(self, platform: str, amount_borrowed: float, date: str,
                 due_date: str = None, interest_rate: float = 0,
                 notes: str = None) -> int:
        with self._lock:
            c = self.conn.execute(
                """INSERT INTO loans (platform, amount_borrowed, amount_paid, remaining, status, due_date, interest_rate, notes, date)
                   VALUES (?, ?, 0, ?, 'active', ?, ?, ?, ?)""",
                (platform, amount_borrowed, amount_borrowed, due_date, interest_rate, notes, date),
            )
            self.conn.commit()
            return c.lastrowid

    def get_loans(self, status: str = None) -> list[dict]:
        with self._lock:
            if status:
                rows = self.conn.execute(
                    "SELECT * FROM loans WHERE status = ? ORDER BY date DESC", (status,)
                ).fetchall()
            else:
                rows = self.conn.execute(
                    "SELECT * FROM loans ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, date DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def find_loan_by_platform(self, platform_name: str) -> Optional[dict]:
        with self._lock:
            # Exact match first
            row = self.conn.execute(
                "SELECT * FROM loans WHERE LOWER(platform) = LOWER(?) AND status = 'active'",
                (platform_name,),
            ).fetchone()
            if row:
                return dict(row)
        # Fuzzy match
        loans = self.get_loans(status="active")
        if not loans:
            return None
        from utils.helpers import fuzzy_match
        platforms = [l["platform"] for l in loans]
        matched = fuzzy_match(platform_name, platforms, threshold=60)
        if matched:
            return next((l for l in loans if l["platform"] == matched), None)
        return None

    def add_loan_payment(self, loan_id: int, amount: float, date: str,
                         notes: str = None) -> int:
        with self._lock:
            c = self.conn.execute(
                "INSERT INTO loan_payments (loan_id, amount, date, notes) VALUES (?, ?, ?, ?)",
                (loan_id, amount, date, notes),
            )
            # Update loan balance
            self.conn.execute(
                """UPDATE loans SET
                   amount_paid = amount_paid + ?,
                   remaining = amount_borrowed - (amount_paid + ?),
                   updated_at = datetime('now', 'localtime')
                   WHERE id = ?""",
                (amount, amount, loan_id),
            )
            # Check if fully paid
            loan = self.conn.execute("SELECT remaining FROM loans WHERE id = ?", (loan_id,)).fetchone()
            if loan and loan["remaining"] <= 0:
                self.conn.execute(
                    "UPDATE loans SET status = 'paid', remaining = 0 WHERE id = ?",
                    (loan_id,),
                )
            self.conn.commit()
            return c.lastrowid

    def get_loan_payments(self, loan_id: int) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM loan_payments WHERE loan_id = ? ORDER BY date DESC",
                (loan_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_total_loan_balance(self) -> float:
        with self._lock:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(remaining), 0) as total FROM loans WHERE status = 'active'"
            ).fetchone()
            return row["total"]

    def get_active_loan_count(self) -> int:
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) as count FROM loans WHERE status = 'active'"
            ).fetchone()
            return row["count"]

    # --- Budgets ---
    def set_budget(self, category_id: int, monthly_limit: float, month_year: str) -> int:
        with self._lock:
            c = self.conn.execute(
                """INSERT OR REPLACE INTO budgets (category_id, monthly_limit, month_year)
                   VALUES (?, ?, ?)""",
                (category_id, monthly_limit, month_year),
            )
            self.conn.commit()
            return c.lastrowid

    def get_budgets(self, month_year: str) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT b.*, c.name as category_name, c.color as category_color,
                   COALESCE((SELECT SUM(e.amount) FROM expenses e
                             WHERE e.category_id = b.category_id
                             AND strftime('%%Y-%%m', e.date) = b.month_year), 0) as spent
                   FROM budgets b JOIN categories c ON b.category_id = c.id
                   WHERE b.month_year = ? ORDER BY c.name""",
                (month_year,),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Chat History ---
    def add_chat_message(self, role: str, message: str,
                         action_type: str = None, action_data: str = None) -> int:
        with self._lock:
            c = self.conn.execute(
                "INSERT INTO chat_history (role, message, action_type, action_data) VALUES (?, ?, ?, ?)",
                (role, message, action_type, action_data),
            )
            self.conn.commit()
            return c.lastrowid

    def get_chat_history(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    def clear_chat_history(self):
        with self._lock:
            self.conn.execute("DELETE FROM chat_history")
            self.conn.commit()

    # --- Analytics ---
    def get_top_merchants(self, start_date: str, end_date: str, limit: int = 5) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT merchant, SUM(amount) as total, COUNT(*) as count
                   FROM expenses WHERE merchant IS NOT NULL
                   AND date >= ? AND date <= ?
                   GROUP BY LOWER(merchant) ORDER BY total DESC LIMIT ?""",
                (start_date, end_date, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_spending_trend(self, months: int = 6) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT strftime('%%Y-%%m', date) as month, SUM(amount) as total
                   FROM expenses GROUP BY month ORDER BY month DESC LIMIT ?""",
                (months,),
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    # --- Income ---
    def add_income(self, amount: float, source: str, date: str,
                   description: str = None, is_recurring: bool = False,
                   notes: str = None) -> int:
        with self._lock:
            c = self.conn.execute(
                """INSERT INTO income (amount, source, description, date, is_recurring, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (amount, source, description, date, 1 if is_recurring else 0, notes),
            )
            self.conn.commit()
            return c.lastrowid

    def get_income(self, start_date: str = None, end_date: str = None,
                   limit: int = 50) -> list[dict]:
        with self._lock:
            query = "SELECT * FROM income WHERE 1=1"
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)
            rows = self.conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def search_income(self, source_like: str = None, amount: float = None,
                      date: str = None, limit: int = 10) -> list[dict]:
        with self._lock:
            query = "SELECT * FROM income WHERE 1=1"
            params = []
            if source_like:
                query += " AND (LOWER(source) LIKE ? OR LOWER(description) LIKE ?)"
                like = f"%{source_like.lower()}%"
                params.extend([like, like])
            if amount is not None:
                query += " AND amount = ?"
                params.append(amount)
            if date:
                query += " AND date = ?"
                params.append(date)
            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)
            rows = self.conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def update_income(self, income_id: int, **kwargs) -> bool:
        allowed = {"amount", "source", "description", "date", "is_recurring", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        with self._lock:
            sets = ", ".join(f"{k} = ?" for k in updates)
            sets += ", updated_at = datetime('now', 'localtime')"
            vals = list(updates.values()) + [income_id]
            c = self.conn.execute(f"UPDATE income SET {sets} WHERE id = ?", vals)
            self.conn.commit()
            return c.rowcount > 0

    def delete_income(self, income_id: int) -> bool:
        with self._lock:
            c = self.conn.execute("DELETE FROM income WHERE id = ?", (income_id,))
            self.conn.commit()
            return c.rowcount > 0

    def get_total_income(self, start_date: str, end_date: str) -> float:
        with self._lock:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM income WHERE date >= ? AND date <= ?",
                (start_date, end_date),
            ).fetchone()
            return row["total"]

    def get_monthly_income_summary(self, months: int = 6) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT strftime('%%Y-%%m', date) as month, SUM(amount) as total
                   FROM income GROUP BY month ORDER BY month DESC LIMIT ?""",
                (months,),
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    # --- Rename Operations ---
    def rename_expense(self, old_name: str, new_name: str) -> int:
        with self._lock:
            like = f"%{old_name.lower()}%"
            c = self.conn.execute(
                """UPDATE expenses SET description = REPLACE(description, ?, ?),
                   merchant = CASE WHEN LOWER(merchant) LIKE ? THEN ? ELSE merchant END,
                   updated_at = datetime('now', 'localtime')
                   WHERE LOWER(description) LIKE ? OR LOWER(merchant) LIKE ?""",
                (old_name, new_name, like, new_name, like, like),
            )
            self.conn.commit()
            return c.rowcount

    def rename_category(self, old_name: str, new_name: str) -> bool:
        cat = self.get_category_by_name(old_name)
        if not cat:
            return False
        with self._lock:
            c = self.conn.execute(
                "UPDATE categories SET name = ? WHERE id = ?",
                (new_name, cat["id"]),
            )
            self.conn.commit()
            return c.rowcount > 0

    def rename_loan_platform(self, old_name: str, new_name: str) -> int:
        with self._lock:
            like = f"%{old_name.lower()}%"
            c = self.conn.execute(
                """UPDATE loans SET platform = ?,
                   updated_at = datetime('now', 'localtime')
                   WHERE LOWER(platform) LIKE ?""",
                (new_name, like),
            )
            self.conn.commit()
            return c.rowcount

    def checkpoint(self):
        """Flush WAL journal to the main database file."""
        with self._lock:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def close(self):
        with self._lock:
            # Checkpoint WAL before closing so the .db file has all data
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self.conn.close()
