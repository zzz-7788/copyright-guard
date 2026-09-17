from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QStackedWidget
from app.ui.pages.overview_page import OverviewPage
from app.ui.pages.search_page import SearchPage
from app.ui.pages.works_page import WorksPage
from app.ui.pages.reports_page import ReportsPage
from app.ui.pages.settings_page import SettingsPage

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Copyright Guard")
        self.resize(1180,820)
        self.setMinimumSize(900,650)

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0,0,0,0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("header")
        h = QVBoxLayout(header)
        h.setContentsMargins(24,14,24,10)

        top = QHBoxLayout()
        brand = QLabel("Copyright Guard")
        brand.setObjectName("brand")
        ready = QLabel("● Ready")
        ready.setObjectName("ready")
        top.addWidget(brand)
        top.addStretch()
        top.addWidget(ready)
        h.addLayout(top)

        nav = QHBoxLayout()
        self.buttons = []
        for i, label in enumerate(["概览","搜索","作品与资料","举报","设置"]):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setObjectName("navButton")
            button.clicked.connect(lambda checked=False, index=i: self.go(index))
            nav.addWidget(button)
            self.buttons.append(button)
        nav.addStretch()
        h.addLayout(nav)
        outer.addWidget(header)

        self.stack = QStackedWidget()
        self.overview = OverviewPage(db)
        self.search = SearchPage(db, self.refresh_all)
        self.works = WorksPage(db, self.refresh_all)
        self.reports = ReportsPage(db)
        self.settings = SettingsPage(db)
        for page in [self.overview,self.search,self.works,self.reports,self.settings]:
            self.stack.addWidget(page)
        outer.addWidget(self.stack,1)
        self.go(0)

    def go(self, index):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        if index == 0:
            self.overview.refresh()
        elif index == 1:
            self.search.refresh_works()
            self.search.refresh_results()
        elif index == 3:
            self.reports.refresh()

    def refresh_all(self):
        self.overview.refresh()
        self.search.refresh_works()
        self.search.refresh_results()
        self.reports.refresh()
