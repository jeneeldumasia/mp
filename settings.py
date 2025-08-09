# settings.py

import sqlite3
# --- ADDED: Import Qt for alignment constants ---
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QHBoxLayout, QFrame)
from PyQt5.QtGui import QFont

# --- Application-wide Constants ---
APP_NAME = "MISTY PAV BHAJI"
DB_NAME = "shop_data.db"
DEFAULT_PASSWORD = "1234"
GST_RATE_PERCENT = 5

# --- MODIFIED: This is now a QWidget for a tab ---
class SettingsTab(QWidget):
    def __init__(self, db_conn, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self.main_layout = QVBoxLayout(self)
        self.is_unlocked = False
        self.init_ui()

    def init_ui(self):
        # Create two main containers (widgets)
        self.lock_widget = QWidget()
        self.settings_widget = QWidget()
        
        # --- Setup the Lock Screen ---
        lock_layout = QVBoxLayout(self.lock_widget)
        lock_layout.addStretch()
        lock_label = QLabel("Please enter password to unlock settings.")
        lock_label.setFont(QFont("Arial", 14))
        lock_label.setAlignment(Qt.AlignCenter) # This line now works correctly
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.unlock_settings) # Unlock on Enter key
        unlock_button = QPushButton("Unlock")
        unlock_button.clicked.connect(self.unlock_settings)
        
        lock_layout.addWidget(lock_label)
        lock_layout.addWidget(self.password_input)
        lock_layout.addWidget(unlock_button)
        lock_layout.addStretch()

        # --- Setup the actual Settings Screen ---
        settings_layout = QVBoxLayout(self.settings_widget)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Item Name", "Price (₹)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("Add New Item")
        self.remove_button = QPushButton("Remove Selected Item")
        self.save_button = QPushButton("Save Changes")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.add_button.clicked.connect(self.add_item)
        self.remove_button.clicked.connect(self.remove_item)
        self.save_button.clicked.connect(self.save_changes)

        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.remove_button)
        btn_layout.addWidget(self.save_button)
        
        settings_layout.addWidget(QLabel("Manage Menu Items"))
        settings_layout.addWidget(self.table)
        settings_layout.addLayout(btn_layout)

        # Add both widgets to the main layout and show the lock screen
        self.main_layout.addWidget(self.lock_widget)
        self.main_layout.addWidget(self.settings_widget)
        self.settings_widget.hide()

    def unlock_settings(self):
        if self.password_input.text() == DEFAULT_PASSWORD:
            self.is_unlocked = True
            self.lock_widget.hide()
            self.settings_widget.show()
            self.load_menu_items()
        else:
            QMessageBox.warning(self, "Error", "Incorrect password.")
            self.password_input.clear()

    def lock_settings(self):
        """Public method to re-lock the settings when the tab is changed."""
        if self.is_unlocked:
            self.password_input.clear()
            self.settings_widget.hide()
            self.lock_widget.show()
            self.is_unlocked = False

    def load_menu_items(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT name, price FROM menu ORDER BY name")
            items = cursor.fetchall()
            
            self.table.setRowCount(len(items))
            for row_idx, item in enumerate(items):
                self.table.setItem(row_idx, 0, QTableWidgetItem(item[0]))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(item[1])))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not load menu items: {e}")

    def add_item(self):
        self.table.insertRow(self.table.rowCount())

    def remove_item(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an item to remove.")
            return
        self.table.removeRow(current_row)

    def save_changes(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM menu")
            
            for row in range(self.table.rowCount()):
                name_item = self.table.item(row, 0)
                price_item = self.table.item(row, 1)

                if not name_item or not price_item or not name_item.text() or not price_item.text():
                    continue

                name = name_item.text().strip()
                price_text = price_item.text().strip()

                if not name:
                    QMessageBox.warning(self, "Validation Error", f"Item name in row {row + 1} cannot be empty.")
                    return

                try:
                    price = float(price_text)
                    if price <= 0:
                        raise ValueError
                except ValueError:
                    QMessageBox.warning(self, "Validation Error", f"Invalid price '{price_text}' in row {row + 1}. Please enter a positive number.")
                    return

                cursor.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (name, price))

            self.db_conn.commit()
            QMessageBox.information(self, "Success", "Menu updated successfully! Please restart to see changes on the billing screen.")
        except sqlite3.Error as e:
            self.db_conn.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save changes: {e}")