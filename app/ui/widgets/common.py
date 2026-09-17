from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class Card(QFrame):
    def __init__(self, title=None):
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18,18,18,18)
        self.body.setSpacing(12)
        if title:
            label = QLabel(title)
            label.setObjectName("sectionTitle")
            self.body.addWidget(label)

class StatCard(Card):
    def __init__(self, label):
        super().__init__()
        self.value = QLabel("0")
        self.value.setObjectName("statValue")
        caption = QLabel(label)
        caption.setObjectName("muted")
        self.body.addWidget(self.value)
        self.body.addWidget(caption)
