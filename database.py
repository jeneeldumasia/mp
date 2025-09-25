# database.py
import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("shop_data.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        if not self.conn: return
        try:
            with self.conn:
                # Menu and Sales tables remain the same
                self.conn.execute("CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, price REAL NOT NULL)")
                self.conn.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, items TEXT NOT NULL, total_amount REAL NOT NULL, payment_method TEXT NOT NULL)")
                
                # Expanded config table
                self.conn.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

                # --- ADDED: Seed all default settings ---
                default_configs = {
                    'shop_name': 'Misty Pavbhaji',
                    'password': '1234',
                    'gst_rate': '5.0',
                    'currency_symbol': '₹',
                    'bill_footer': 'Thank you! Visit Again!'
                }
                for key, value in default_configs.items():
                    self.conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))

                # Populate default menu items if empty
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM menu")
                if cursor.fetchone()[0] == 0:
                    self.conn.execute("INSERT INTO menu (name, price) VALUES (?, ?)", ("Pav Bhaji", 80.00))
                    self.conn.execute("INSERT INTO menu (name, price) VALUES (?, ?)", ("Pulao", 90.00))
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def get_config_value(self, key, default_value=None):
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else default_value
        except sqlite3.Error as e:
            print(f"Error fetching config value for {key}: {e}")
            return default_value

    def set_config_value(self, key, value):
        try:
            with self.conn:
                self.conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
            return True
        except sqlite3.Error as e:
            print(f"Error setting config value for {key}: {e}")
            return False
            
    # ... (all other database methods remain the same)
    def get_menu_items(self):
        # ...
        if not self.conn: return []
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT name, price FROM menu ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching menu items: {e}")
            return []

    def save_sale(self, bill_details):
        # ...
        if not self.conn: return False
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
        # ...
        if not self.conn: return []
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
            
    def get_sales_for_date_range(self, start_date, end_date):
        # ...
        if not self.conn: return []
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
        # ...
        if self.conn: self.conn.close()