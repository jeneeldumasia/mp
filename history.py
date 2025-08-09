# history.py

import json
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime, Qt, QDate
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame)
from PyQt5.QtGui import QFont

# --- MODIFIED: This is now a QWidget for a tab, not a QDialog ---
class HistoryTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left side for the list of sales
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_panel)

        # Right side for totals
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignTop)

        # --- Left Panel Contents ---
        date_label = QLabel("Select Date:")
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.dateChanged.connect(self.update_all_data)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Time", "Items", "Total (₹)", "Payment"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)

        left_layout.addWidget(date_label)
        left_layout.addWidget(self.date_edit)
        left_layout.addWidget(self.history_table)

        # --- Right Panel Contents ---
        totals_label = QLabel("Summary")
        totals_label.setFont(QFont("Arial", 16, QFont.Bold))

        self.daily_total_label = QLabel("Day's Total: ₹0.00")
        self.daily_total_label.setFont(QFont("Arial", 14))

        self.weekly_total_label = QLabel("This Week's Total: ₹0.00")
        self.weekly_total_label.setFont(QFont("Arial", 14))
        self.weekly_total_label.setWordWrap(True)

        right_layout.addWidget(totals_label)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.daily_total_label)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.weekly_total_label)

        main_layout.addWidget(left_panel, 3) # 3 parts width
        main_layout.addWidget(right_panel, 1) # 1 part width

        self.update_all_data()

    def update_all_data(self):
        """A single method to refresh all data on the screen."""
        self.populate_history()
        self.calculate_weekly_total()

    def populate_history(self):
        """Fetches data and populates the history table and daily total."""
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        daily_total = 0
        try:
            sales_data = self.db.get_sales_for_date(selected_date)
            self.history_table.setRowCount(len(sales_data))

            for row_idx, sale in enumerate(sales_data):
                timestamp, items_json, total_amount, payment_method = sale
                daily_total += total_amount
                datetime_obj = QDateTime.fromString(timestamp, "yyyy-MM-dd HH:mm:ss")
                time_str = datetime_obj.toString("h:mm AP")
                items_summary = ", ".join([f"{item['quantity']}x {item['name']}" for item in json.loads(items_json)])

                self.history_table.setItem(row_idx, 0, QTableWidgetItem(time_str))
                self.history_table.setItem(row_idx, 1, QTableWidgetItem(items_summary))
                self.history_table.setItem(row_idx, 2, QTableWidgetItem(f"{total_amount:.2f}"))
                self.history_table.setItem(row_idx, 3, QTableWidgetItem(payment_method))
            
            self.daily_total_label.setText(f"Day's Total: ₹{daily_total:.2f}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while fetching history: {e}")

    def calculate_weekly_total(self):
        """Calculates total sales for the current week (Mon-Sun)."""
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        end_of_week = start_of_week + timedelta(days=6) # Sunday

        week_total = 0
        try:
            sales_data = self.db.get_sales_for_date_range(
                start_of_week.strftime("%Y-%m-%d"),
                end_of_week.strftime("%Y-%m-%d")
            )
            for sale in sales_data:
                week_total += sale[0]
            
            week_range_str = f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')}"
            self.weekly_total_label.setText(f"This Week's Total\n({week_range_str}):\n₹{week_total:.2f}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred calculating weekly total: {e}")

    def refresh_data(self):
        """Public method to allow parent to refresh data when tab is shown."""
        self.update_all_data()