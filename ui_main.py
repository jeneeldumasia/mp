# ui_main.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QRadioButton, QSpinBox, QCheckBox, 
                             QMessageBox, QFrame, QGridLayout, QLineEdit, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QDoubleValidator, QIcon

from billing import BillLogic
from database import Database
from history import HistoryTab
from settings import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.load_config() # --- ADDED: Load settings on startup
        self.init_ui()
    
    def load_config(self):
        """Loads configuration from the database into instance variables."""
        self.shop_name = self.db.get_config_value('shop_name', 'My Shop')
        self.gst_rate = float(self.db.get_config_value('gst_rate', '5.0'))
        self.currency_symbol = self.db.get_config_value('currency_symbol', '₹')
        self.bill_footer = self.db.get_config_value('bill_footer', 'Thank You!')
    
    def init_ui(self):
        self.setWindowTitle(self.shop_name) # Use loaded shop name
        self.setGeometry(100, 100, 1200, 700)
        try:
            self.setWindowIcon(QIcon("logo.ico"))
        except Exception:
            print("Warning: 'logo.ico' not found.")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # --- MODIFIED: Pass the database object, not the connection ---
        self.billing_tab = self.create_billing_tab()
        self.history_tab_widget = HistoryTab(self.db)
        self.settings_tab_widget = SettingsTab(self.db)
        
        # --- MODIFIED: Connect to the new general signal ---
        self.settings_tab_widget.config_changed.connect(self.on_config_changed)

        self.tabs.addTab(self.billing_tab, "Billing")
        self.tabs.addTab(self.history_tab_widget, "History")
        self.tabs.addTab(self.settings_tab_widget, "Settings")
        
        self.tabs.currentChanged.connect(self.on_tab_change)

    def on_config_changed(self):
        """Reloads config and updates UI when settings are saved."""
        self.load_config()
        self.setWindowTitle(self.shop_name)
        self.gst_checkbox.setText(f"Apply GST ({self.gst_rate}%)")
        self.update_totals() # Recalculate bill with new GST rate if needed
        # Note: Some changes like menu item prices require a restart to reflect on the billing screen buttons.
        # This could be improved further with more signals, but a restart is a simple and reliable solution for now.

    # ... (The create_billing_tab method needs to use the loaded config values)
    def create_billing_tab(self):
        billing_widget = QWidget()
        # ... (rest of the layout setup is the same) ...
        main_layout = QHBoxLayout(billing_widget)
        self.bill = BillLogic()
        self.current_total = 0.0
        left_panel = QFrame(); left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_panel); left_layout.setAlignment(Qt.AlignTop)
        right_panel = QFrame(); right_panel.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(left_panel, 1); main_layout.addWidget(right_panel, 2)
        menu_label = QLabel("MENU"); menu_label.setFont(QFont("Arial", 18, QFont.Bold)); left_layout.addWidget(menu_label)
        menu_items = self.db.get_menu_items()
        menu_grid = QGridLayout()
        row, col = 0, 0
        for name, price in menu_items:
            # --- MODIFIED: Use loaded currency symbol ---
            btn = QPushButton(f"{name}\n{self.currency_symbol}{price:.2f}")
            btn.setMinimumHeight(80)
            btn.clicked.connect(lambda _, n=name, p=price: self.add_item_to_bill(n, p))
            menu_grid.addWidget(btn, row, col)
            col += 1
            if col > 1: col = 0; row += 1
        left_layout.addLayout(menu_grid)
        
        # --- All other widgets are the same, but we will update their text ---
        bill_label = QLabel("CURRENT BILL"); bill_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.bill_table = QTableWidget(); self.bill_table.setColumnCount(5); self.bill_table.setHorizontalHeaderLabels(["Item", "Price", "Qty", "Total", ""])
        self.bill_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.bill_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.bill_table.setEditTriggers(QTableWidget.NoEditTriggers)
        totals_grid = QGridLayout()
        self.subtotal_label = QLabel(f"Subtotal: {self.currency_symbol}0.00")
        self.discount_label = QLabel(f"Discount: {self.currency_symbol}0.00")
        self.gst_label = QLabel(f"GST: {self.currency_symbol}0.00")
        self.total_label = QLabel(f"TOTAL: {self.currency_symbol}0.00")
        self.total_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #D32F2F;")
        totals_grid.addWidget(self.subtotal_label, 0, 0); totals_grid.addWidget(self.discount_label, 1, 0)
        totals_grid.addWidget(self.gst_label, 2, 0); totals_grid.addWidget(self.total_label, 3, 0, alignment=Qt.AlignLeft)
        cash_frame = QFrame(); cash_frame.setFrameShape(QFrame.StyledPanel)
        cash_layout = QVBoxLayout(cash_frame)
        self.cash_received_input = QLineEdit(); self.cash_received_input.setPlaceholderText("Enter cash received...")
        self.cash_received_input.setValidator(QDoubleValidator(0, 100000, 2))
        self.cash_received_input.textChanged.connect(self.calculate_change)
        quick_cash_layout = QHBoxLayout()
        for amount in [100, 200, 500]:
            btn = QPushButton(f"{self.currency_symbol}{amount}"); btn.clicked.connect(lambda _, a=amount: self.cash_received_input.setText(str(a))); quick_cash_layout.addWidget(btn)
        self.change_due_label = QLabel(f"Change Due: {self.currency_symbol}0.00")
        self.change_due_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #388E3C;")
        cash_layout.addWidget(QLabel("Cash Received:")); cash_layout.addWidget(self.cash_received_input); cash_layout.addLayout(quick_cash_layout); cash_layout.addWidget(self.change_due_label)
        controls_layout = QHBoxLayout()
        self.discount_spinbox = QSpinBox(); self.discount_spinbox.setSuffix("%"); self.discount_spinbox.setRange(0, 100); self.discount_spinbox.valueChanged.connect(self.update_totals)
        # --- MODIFIED: Use loaded GST rate in checkbox label ---
        self.gst_checkbox = QCheckBox(f"Apply GST ({self.gst_rate}%)")
        self.gst_checkbox.stateChanged.connect(self.update_totals)
        self.cash_radio = QRadioButton("Cash"); self.upi_radio = QRadioButton("UPI"); self.cash_radio.setChecked(True)
        controls_layout.addWidget(QLabel("Discount:")); controls_layout.addWidget(self.discount_spinbox); controls_layout.addWidget(self.gst_checkbox); controls_layout.addStretch(); controls_layout.addWidget(self.cash_radio); controls_layout.addWidget(self.upi_radio)
        action_layout = QHBoxLayout(); self.new_bill_button = QPushButton("New Bill (Clear)"); self.save_print_button = QPushButton("SAVE & COMPLETE"); self.save_print_button.setStyleSheet("background-color: #1976D2; color: white; padding: 10px;")
        self.new_bill_button.clicked.connect(self.clear_bill); self.save_print_button.clicked.connect(self.process_sale); action_layout.addWidget(self.new_bill_button); action_layout.addWidget(self.save_print_button)
        right_layout.addWidget(bill_label); right_layout.addWidget(self.bill_table, 1); right_layout.addLayout(totals_grid); right_layout.addWidget(cash_frame); right_layout.addLayout(controls_layout); right_layout.addLayout(action_layout)
        return billing_widget

    # ... (update_totals needs to use self.gst_rate)
    def update_totals(self):
        discount = self.discount_spinbox.value()
        gst_applied = self.gst_checkbox.isChecked()
        # --- MODIFIED: Pass loaded GST rate to billing logic ---
        totals = self.bill.calculate_totals(discount, gst_applied, self.gst_rate)
        # --- MODIFIED: Use loaded currency symbol in all labels ---
        self.subtotal_label.setText(f"Subtotal: {self.currency_symbol}{totals['subtotal']:.2f}")
        self.discount_label.setText(f"Discount ({discount}%): {self.currency_symbol}{totals['discount_amount']:.2f}")
        self.gst_label.setText(f"GST ({self.gst_rate}%): {self.currency_symbol}{totals['gst_amount']:.2f}")
        self.total_label.setText(f"TOTAL: {self.currency_symbol}{totals['final_total']:.2f}")
        self.current_total = totals['final_total']
        self.calculate_change()

    # ... (calculate_change needs to use currency symbol)
    def calculate_change(self):
        try:
            cash_received_text = self.cash_received_input.text()
            if not cash_received_text:
                self.change_due_label.setText(f"Change Due: {self.currency_symbol}0.00")
                return
            cash_received = float(cash_received_text)
            change = cash_received - self.current_total
            self.change_due_label.setText(f"Change Due: {self.currency_symbol}{change:.2f}")
            self.change_due_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#D32F2F' if change < 0 else '#388E3C'};")
        except ValueError:
            self.change_due_label.setText(f"Change Due: {self.currency_symbol}--.--")

    # ... (print_bill needs to use loaded config values)
    def print_bill(self, bill_details):
        bill_text = f"{self.shop_name}\n" # Use loaded shop name
        bill_text += "--------------------------------\n"
        for item in bill_details['items']:
            line = f"{item['name']} (x{item['quantity']})"
            # Use loaded currency symbol
            price_str = f"{self.currency_symbol}{item['price'] * item['quantity']:.2f}"
            bill_text += f"{line:<20}{price_str:>10}\n"
        bill_text += "--------------------------------\n"
        bill_text += f"{'Subtotal:':<20}{self.currency_symbol}{bill_details['subtotal']:.2f}\n"
        # ... and so on for discount, gst, total...
        bill_text += f"================================\n"
        bill_text += f"{'TOTAL:':<20}{self.currency_symbol}{bill_details['final_total']:.2f}\n"
        bill_text += "================================\n"
        bill_text += f"Payment: {bill_details['payment_method']}\n\n"
        bill_text += f"{self.bill_footer}\n" # Use loaded footer
        QMessageBox.information(self, "Print Preview", f"Bill saved successfully!\n\n--- Bill Content ---\n{bill_text}")

    # ... (All other methods like closeEvent, add_item_to_bill, etc., are mostly the same)
    def on_tab_change(self, index):
        if index == 1: self.history_tab_widget.refresh_data()
        elif self.settings_tab_widget.is_unlocked: self.settings_tab_widget.lock_settings()
    
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm Exit', "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: self.db.close(); event.accept()
        else: event.ignore()

    def add_item_to_bill(self, name, price):
        self.bill.add_item(name, price); self.update_bill_display(); self.update_totals()

    def update_bill_display(self):
        items = self.bill.get_bill_items(); self.bill_table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self.bill_table.setItem(row_idx, 0, QTableWidgetItem(item['name']))
            self.bill_table.setItem(row_idx, 1, QTableWidgetItem(f"{item['price']:.2f}"))
            self.bill_table.setItem(row_idx, 2, QTableWidgetItem(str(item['quantity'])))
            self.bill_table.setItem(row_idx, 3, QTableWidgetItem(f"{item['price'] * item['quantity']:.2f}"))
            btn_layout = QHBoxLayout(); plus_btn = QPushButton("+"); minus_btn = QPushButton("-"); plus_btn.setFixedSize(25, 25); minus_btn.setFixedSize(25, 25)
            plus_btn.clicked.connect(lambda _, n=item['name']: self.change_quantity(n, 1)); minus_btn.clicked.connect(lambda _, n=item['name']: self.change_quantity(n, -1))
            btn_layout.addWidget(minus_btn); btn_layout.addWidget(plus_btn); btn_layout.setContentsMargins(0, 0, 0, 0); btn_widget_container = QWidget(); btn_widget_container.setLayout(btn_layout)
            self.bill_table.setCellWidget(row_idx, 4, btn_widget_container)
    
    def change_quantity(self, item_name, change):
        self.bill.update_quantity(item_name, change); self.update_bill_display(); self.update_totals()

    def clear_bill(self):
        self.bill.clear_bill(); self.discount_spinbox.setValue(0); self.gst_checkbox.setChecked(False); self.cash_received_input.clear()
        self.update_bill_display(); self.update_totals()

    def process_sale(self):
        if not self.bill.get_bill_items(): QMessageBox.warning(self, "Empty Bill", "Cannot process an empty bill."); return
        totals = self.bill.calculate_totals(self.discount_spinbox.value(), self.gst_checkbox.isChecked(), self.gst_rate)
        payment_method = "UPI" if self.upi_radio.isChecked() else "Cash"
        bill_details = { "items": self.bill.get_bill_items(), "payment_method": payment_method, **totals }
        if not self.db.save_sale(bill_details): QMessageBox.critical(self, "Database Error", "Failed to save the sale."); return
        self.print_bill(bill_details)
        self.clear_bill()