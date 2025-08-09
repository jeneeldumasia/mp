# main.py

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from ui_main import MainWindow

def main():
    """The main entry point of the application."""
    app = QApplication(sys.argv)
    
    # --- Global Stylesheet for a better look and feel ---
    # This makes the UI more friendly for non-technical users.
    app.setStyleSheet("""
        QWidget {
            font-size: 14pt;
        }
        QPushButton {
            padding: 10px;
            background-color: #E0E0E0;
            border: 1px solid #BDBDBD;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #D6D6D6;
        }
        QPushButton:pressed {
            background-color: #C0C0C0;
        }
        QTableWidget {
            font-size: 12pt;
        }
        QLineEdit, QSpinBox {
            padding: 5px;
        }
        QMainWindow {
            background-color: #FAFAFA;
        }
    """)
    
    # Set a default font
    QApplication.setFont(QFont("Segoe UI", 10))

    try:
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        # A final catch-all for any unexpected errors during startup.
        print(f"An unexpected error occurred: {e}")
        # In a production app, you might log this to a file.
        # For the user, we can show a simple message.
        from PyQt5.QtWidgets import QMessageBox
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setText("A critical error occurred and the application must close.")
        error_box.setInformativeText(str(e))
        error_box.setWindowTitle("Application Error")
        error_box.exec_()

if __name__ == '__main__':
    main()