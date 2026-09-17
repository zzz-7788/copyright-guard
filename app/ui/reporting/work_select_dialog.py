from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)

from app.ui.widgets.common import Card


class WorkSelectDialog(QDialog):
    def __init__(
        self,
        work_groups,
        works,
        parent=None,
    ):
        super().__init__(parent)

        self.work_groups = work_groups
        self.works = works

        self.selected_work_id = None

        self.setWindowTitle(
            "选择要处理的作品"
        )

        self.resize(
            700,
            500,
        )

        self.build_ui()

    # =============================================
    # UI
    # =============================================

    def build_ui(self):
        outer = QVBoxLayout(self)

        outer.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        outer.setSpacing(16)

        # -----------------------------------------
        # 标题
        # -----------------------------------------

        title = QLabel(
            "选择要处理的作品"
        )

        title.setObjectName(
            "pageTitle"
        )

        outer.addWidget(
            title
        )

        note = QLabel(
            "当前百度搜索举报池中包含多个作品。"
            "请选择本次要准备投诉的作品。"
        )

        note.setObjectName(
            "muted"
        )

        note.setWordWrap(
            True
        )

        outer.addWidget(
            note
        )

        # -----------------------------------------
        # Scroll
        # -----------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        content = QFrame()

        self.content_layout = QVBoxLayout(
            content
        )

        self.content_layout.setSpacing(
            12
        )

        scroll.setWidget(
            content
        )

        outer.addWidget(
            scroll,
            1,
        )

        # -----------------------------------------
        # 作品列表
        # -----------------------------------------

        work_map = {
            work["id"]: work
            for work in self.works
        }

        for work_id, items in (
            self.work_groups.items()
        ):
            work = work_map.get(
                work_id
            )

            if not work:
                continue

            self.add_work_card(
                work,
                items,
            )

        self.content_layout.addStretch()

        # -----------------------------------------
        # Footer
        # -----------------------------------------

        footer = QHBoxLayout()

        footer.addStretch()

        cancel_btn = QPushButton(
            "取消"
        )

        cancel_btn.clicked.connect(
            self.reject
        )

        footer.addWidget(
            cancel_btn
        )

        outer.addLayout(
            footer
        )

    # =============================================
    # 作品卡片
    # =============================================

    def add_work_card(
        self,
        work,
        items,
    ):
        card = Card(
            "WORK / 作品"
        )

        row = QHBoxLayout()

        # -----------------------------------------
        # 左侧信息
        # -----------------------------------------

        info = QVBoxLayout()

        title = QLabel(
            work.get("title")
            or "未命名作品"
        )

        title.setObjectName(
            "resultTitle"
        )

        info.addWidget(
            title
        )

        original_url = (
            work.get("original_url")
            or "未配置原作品 URL"
        )

        url_label = QLabel(
            original_url
        )

        url_label.setObjectName(
            "muted"
        )

        url_label.setWordWrap(
            True
        )

        info.addWidget(
            url_label
        )

        count_label = QLabel(
            f"百度搜索待投诉页面："
            f"{len(items)} 条"
        )

        count_label.setObjectName(
            "muted"
        )

        info.addWidget(
            count_label
        )

        row.addLayout(
            info,
            1,
        )

        # -----------------------------------------
        # 处理按钮
        # -----------------------------------------

        process_btn = QPushButton(
            "处理"
        )

        process_btn.setObjectName(
            "primaryButton"
        )

        process_btn.clicked.connect(
            lambda checked=False,
            work_id=work["id"]:
            self.select_work(
                work_id
            )
        )

        row.addWidget(
            process_btn
        )

        card.body.addLayout(
            row
        )

        self.content_layout.addWidget(
            card
        )

    # =============================================
    # 选择作品
    # =============================================

    def select_work(
        self,
        work_id,
    ):
        self.selected_work_id = (
            work_id
        )

        self.accept()