# settings.py
import sqlite3
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFormLayout, QDoubleSpinBox)
from PyQt5.QtGui import QFont

class SettingsTab(QWidget):
    config_changed = pyqtSignal() # General signal that settings have changed

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.main_layout = QVBoxLayout(self)
        self.is_unlocked = False
        self.init_ui()

    def init_ui(self):
        self.lock_widget = QWidget()
        self.settings_widget = QWidget()
        
        # Lock Screen UI (remains the same)
        lock_layout = QVBoxLayout(self.lock_widget)
        lock_layout.addStretch()
        lock_label = QLabel("Please enter password to unlock settings.")
        lock_label.setFont(QFont("Arial", 14))
        lock_label.setAlignment(Qt.AlignCenter)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.unlock_settings)
        unlock_button = QPushButton("Unlock")
        unlock_button.clicked.connect(self.unlock_settings)
        lock_layout.addWidget(lock_label)
        lock_layout.addWidget(self.password_input)
        lock_layout.addWidget(unlock_button)
        lock_layout.addStretch()

        # --- MODIFIED: Expanded Settings Screen ---
        settings_layout = QVBoxLayout(self.settings_widget)
        
        # Using QFormLayout for a clean look
        form_layout = QFormLayout()
        self.shop_name_input = QLineEdit()
        self.gst_rate_spinbox = QDoubleSpinBox()
        self.gst_rate_spinbox.setRange(0.0, 100.0)
        self.gst_rate_spinbox.setSuffix(" %")
        self.currency_symbol_input = QLineEdit()
        self.bill_footer_input = QLineEdit()
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Shop Name:", self.shop_name_input)
        form_layout.addRow("GST/Tax Rate:", self.gst_rate_spinbox)
        form_layout.addRow("Currency Symbol:", self.currency_symbol_input)
        form_layout.addRow("Bill Footer Message:", self.bill_footer_input)
        form_layout.addRow("New Password:", self.new_password_input)
        form_layout.addRow("Confirm New Password:", self.confirm_password_input)
        
        settings_layout.addLayout(form_layout)
        settings_layout.addSpacing(20)

        # Menu editor (remains the same)
        settings_layout.addWidget(QLabel("Manage Menu Items"))
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Item Name", "Price (₹)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        settings_layout.addWidget(self.table)
        
        # Buttons (remain the same)
        add_button = QPushButton("Add New Item")
        add_button.clicked.connect(lambda: self.table.insertRow(self.table.rowCount()))
        remove_button = QPushButton("Remove Selected Item")
        remove_button.clicked.connect(lambda: self.table.removeRow(self.table.currentRow()))
        self.save_button = QPushButton("Save All Changes")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.save_button.clicked.connect(self.save_all_changes)

        settings_layout.addWidget(add_button)
        settings_layout.addWidget(remove_button)
        settings_layout.addWidget(self.save_button)

        self.main_layout.addWidget(self.lock_widget)
        self.main_layout.addWidget(self.settings_widget)
        self.settings_widget.hide()

    def unlock_settings(self):
        # --- MODIFIED: Fetches password from DB ---
        saved_password = self.db.get_config_value('password', '1234')
        if self.password_input.text() == saved_password:
            self.is_unlocked = True
            self.lock_widget.hide()
            self.settings_widget.show()
            self.load_all_settings()
        else:
            QMessageBox.warning(self, "Error", "Incorrect password.")
            self.password_input.clear()

    def load_all_settings(self):
        """Loads all settings from the DB into the UI fields."""
        self.shop_name_input.setText(self.db.get_config_value('shop_name', 'My Shop'))
        self.gst_rate_spinbox.setValue(float(self.db.get_config_value('gst_rate', '5.0')))
        self.currency_symbol_input.setText(self.db.get_config_value('currency_symbol', '₹'))
        self.bill_footer_input.setText(self.db.get_config_value('bill_footer', ''))
        # Clear password fields
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        self.load_menu_items()

    def save_all_changes(self):
        """Saves all general settings and menu items to the DB."""
        try:
            # --- Save general settings ---
            self.db.set_config_value('shop_name', self.shop_name_input.text())
            self.db.set_config_value('gst_rate', str(self.gst_rate_spinbox.value()))
            self.db.set_config_value('currency_symbol', self.currency_symbol_input.text())
            self.db.set_config_value('bill_footer', self.bill_footer_input.text())

            # --- Password change logic ---
            new_pass = self.new_password_input.text()
            confirm_pass = self.confirm_password_input.text()
            if new_pass: # Only change password if a new one is entered
                if new_pass == confirm_pass:
                    self.db.set_config_value('password', new_pass)
                else:
                    QMessageBox.warning(self, "Password Mismatch", "The new passwords do not match. Password was not updated.")
            
            # --- Save menu items ---
            self.save_menu_items()

            QMessageBox.information(self, "Success", "All changes have been saved!\nSome changes may require a restart to apply everywhere.")
            self.config_changed.emit() # Notify main window

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving: {e}")

    # ... (lock_settings, load_menu_items, save_menu_items etc.)
    def lock_settings(self):
        if self.is_unlocked:
            self.password_input.clear()
            self.settings_widget.hide()
            self.lock_widget.show()
            self.is_unlocked = False

    def load_menu_items(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT name, price FROM menu ORDER BY name")
            items = cursor.fetchall()
            self.table.setRowCount(0) # Clear table before loading
            for row_idx, item in enumerate(items):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(item[0]))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(item[1])))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not load menu items: {e}")
            
    def save_menu_items(self):
        # This is separated for clarity
        with self.db.conn:
            self.db.conn.execute("DELETE FROM menu")
            for row in range(self.table.rowCount()):
                name = self.table.item(row, 0).text().strip()
                price_text = self.table.item(row, 1).text().strip()
                if not name or not price_text: continue
                self.db.conn.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (name, float(price_text)))