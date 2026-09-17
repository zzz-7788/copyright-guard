import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.core.database import Database
from app.ui.main_window import MainWindow

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path

def get_database_path():
    # 源码开发环境继续使用项目内原来的数据库
    if not getattr(sys, "frozen", False):
        return None

    # PyInstaller 打包后的 Windows EXE
    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:
        data_dir = (
            Path(local_app_data)
            / "CopyrightGuard"
        )
    else:
        data_dir = (
            Path.home()
            / "CopyrightGuard"
        )

    data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        data_dir
        / "copyright_guard.db"
    )

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Copyright Guard")
    qss = resource_path(
        "app/resources/styles/theme.qss"
    )
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
    db_path = get_database_path()
    db = Database(db_path=db_path)

    window = MainWindow(db)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
