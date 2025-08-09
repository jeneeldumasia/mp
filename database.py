# database.py

import sqlite3
import json
from datetime import datetime
from settings import DB_NAME

class Database:
    # ... (previous methods __init__, create_tables, get_menu_items, save_sale remain the same) ...
    def __init__(self):
        try:
            self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            self.create_tables()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None

    def create_tables(self):
        if not self.conn:
            return
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS menu (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        price REAL NOT NULL
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        items TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        payment_method TEXT NOT NULL
                    )
                """)
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM menu")
                if cursor.fetchone()[0] == 0:
                    self.conn.execute("INSERT INTO menu (name, price) VALUES (?, ?)", ("Pav Bhaji", 80.00))
                    self.conn.execute("INSERT INTO menu (name, price) VALUES (?, ?)", ("Pulao", 90.00))
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def get_menu_items(self):
        if not self.conn:
            return []
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT name, price FROM menu ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching menu items: {e}")
            return []

    def save_sale(self, bill_details):
        if not self.conn:
            return False
        try:
            with self.conn:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                items_json = json.dumps(bill_details['items'])
                self.conn.execute(
                    "INSERT INTO sales (timestamp, items, total_amount, payment_method) VALUES (?, ?, ?, ?)",
                    (timestamp, items_json, bill_details['final_total'], bill_details['payment_method'])
                )
            return True
        except sqlite3.Error as e:
            print(f"Error saving sale: {e}")
            return False

    def get_sales_for_date(self, date_str):
        if not self.conn:
            return []
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT timestamp, items, total_amount, payment_method FROM sales WHERE date(timestamp) = ? ORDER BY timestamp DESC",
                    (date_str,)
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching sales for date {date_str}: {e}")
            return []
            
    # --- NEW METHOD ---
    def get_sales_for_date_range(self, start_date, end_date):
        """Fetches sales records between two dates (inclusive)."""
        if not self.conn:
            return []
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT total_amount FROM sales WHERE date(timestamp) BETWEEN ? AND ?",
                    (start_date, end_date)
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching sales for range {start_date}-{end_date}: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()