from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QCheckBox,
    QMessageBox,
    QTabWidget,
)

from app.ui.widgets.common import Card

from app.ui.settings.search_sources_tab import (
    SearchSourcesTab,
)

from app.ui.settings.api_services_tab import (
    ApiServicesTab,
)


class SettingsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("设置  Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.tabs = QTabWidget()

        self.general_tab = QWidget()
        self.sources_tab = SearchSourcesTab(
            self.db
        )

        self.api_tab = ApiServicesTab(
            self.db,
            on_services_changed=(
                self.sources_tab.refresh
            ),
        )
        self.websites_tab = QWidget()
        self.browser_tab = QWidget()
        self.data_tab = QWidget()

        self.tabs.addTab(self.general_tab, "常规")
        self.tabs.addTab(self.sources_tab, "搜索来源")
        self.tabs.addTab(self.api_tab, "API 服务")
        self.tabs.addTab(self.websites_tab, "网站")
        self.tabs.addTab(self.browser_tab, "浏览器")
        self.tabs.addTab(self.data_tab, "数据")

        layout.addWidget(self.tabs)

        self.build_general_tab()
        self.build_websites_tab()
        self.build_browser_tab()
        self.build_data_tab()

    # =========================================================
    # General
    # =========================================================

    def build_general_tab(self):
        layout = QVBoxLayout(self.general_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        card = Card("General / 常规")

        note = QLabel(
            "Copyright Guard 的基础设置。"
            "搜索服务、网站和浏览器配置请使用对应的设置页。"
        )
        note.setObjectName("muted")
        note.setWordWrap(True)

        card.body.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()



    # =========================================================
    # Websites
    # =========================================================

    def build_websites_tab(self):
        layout = QVBoxLayout(self.websites_tab)
        layout.setContentsMargins(16, 16, 16, 16)

        card = Card("Websites / 网站")

        form = QFormLayout()

        self.whitelist = QLineEdit(
            self.db.get_setting(
                "whitelist",
                "example.org",
            )
        )

        self.whitelist.setPlaceholderText(
            "example.org, mysite.com"
        )

        form.addRow(
            "网站白名单",
            self.whitelist,
        )

        card.body.addLayout(form)

        save = QPushButton("保存")
        save.clicked.connect(
            self.save_websites
        )

        card.body.addWidget(save)

        layout.addWidget(card)
        layout.addStretch()

    def save_websites(self):
        self.db.set_setting(
            "whitelist",
            self.whitelist.text().strip(),
        )

        QMessageBox.information(
            self,
            "已保存",
            "网站设置已保存。",
        )

    # =========================================================
    # Browser
    # =========================================================

    def build_browser_tab(self):
        layout = QVBoxLayout(self.browser_tab)
        layout.setContentsMargins(16, 16, 16, 16)

        card = Card("Browser / 浏览器")

        self.system_browser = QCheckBox(
            "使用系统默认浏览器打开网页"
        )
        self.system_browser.setChecked(True)

        card.body.addWidget(
            self.system_browser
        )

        note = QLabel(
            "后续版本将在这里加入指定浏览器、"
            "Playwright 举报辅助浏览器以及"
            "登录/CAPTCHA 暂停策略。"
        )

        note.setObjectName("muted")
        note.setWordWrap(True)

        card.body.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()

    # =========================================================
    # Data
    # =========================================================

    def build_data_tab(self):
        layout = QVBoxLayout(self.data_tab)
        layout.setContentsMargins(16, 16, 16, 16)

        card = Card("Data / 数据")

        path_label = QLabel(
            f"SQLite 数据库：\n{self.db.path}"
        )

        path_label.setObjectName("muted")
        path_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        card.body.addWidget(path_label)

        note = QLabel(
            "后续版本可在这里加入数据库备份、"
            "导出和恢复功能。"
        )

        note.setObjectName("muted")
        note.setWordWrap(True)

        card.body.addWidget(note)

        layout.addWidget(card)
        layout.addStretch()