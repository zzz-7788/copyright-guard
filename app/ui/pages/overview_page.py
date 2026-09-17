from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QTableWidget,QTableWidgetItem,QHeaderView
from app.ui.widgets.common import StatCard, Card

class OverviewPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,24)
        lay.setSpacing(18)
        title = QLabel("概览  Overview")
        title.setObjectName("pageTitle")
        lay.addWidget(title)

        row = QHBoxLayout()
        self.cards = [StatCard(x) for x in ["扫描页面","疑似页面","已处理","已举报"]]
        for card in self.cards:
            row.addWidget(card)
        lay.addLayout(row)

        card = Card("按作品统计")
        self.table = QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["作品","疑似页面","已举报","状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        card.body.addWidget(self.table)
        lay.addWidget(card,1)
        self.refresh()

    def refresh(self):
        for card, value in zip(self.cards, self.db.stats()):
            card.value.setText(str(value))
        works = self.db.list_works()
        results = self.db.list_results()
        reports = self.db.list_reports()
        self.table.setRowCount(len(works))
        for i, work in enumerate(works):
            potential = sum(r["work_id"] == work["id"] and r["status"] == "potential" for r in results)
            reported = sum(r["work_id"] == work["id"] for r in reports)
            vals = [work["title"], str(potential), str(reported), "Active"]
            for j, value in enumerate(vals):
                self.table.setItem(i,j,QTableWidgetItem(value))
