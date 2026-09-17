import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.core.database import Database
from app.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Copyright Guard")
    qss = Path(__file__).parent / "app" / "resources" / "styles" / "theme.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
    window = MainWindow(Database())
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
