import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QTextEdit,
    QApplication,
)

from app.ui.widgets.common import Card


MATERIAL_SLOTS = [
    (
        "first_publish",
        "首发平台截图",
    ),
    (
        "authorization",
        "晋江小说授权书",
    ),
    (
        "statement",
        "晋江盖章声明",
    ),
    (
        "contract",
        "签约合同首页",
    ),
    (
        "contract",
        "签约合同尾页",
    ),
]


BAIDU_REPORT_URL = (
    "https://newcopyright.baidu.com/"
)


class BaiduPrepareDialog(QDialog):
    def __init__(
        self,
        db,
        work,
        items,
        parent=None,
    ):
        super().__init__(parent)

        self.db = db
        self.work = work
        self.items = items or []

        self.setWindowTitle(
            "百度搜索投诉准备"
        )

        self.resize(
            1000,
            700,
        )

        self.build_ui()
        self.load_data()

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
            "百度搜索投诉准备"
        )

        title.setObjectName(
            "pageTitle"
        )

        outer.addWidget(title)

        note = QLabel(
            "这里汇总本次百度搜索投诉所需的信息。"
            "已有材料会自动从 Works & Materials 读取；"
            "未配置材料仅作提示，不会阻止继续处理。"
            "最终投诉提交仍由作者确认。"
        )

        note.setObjectName(
            "muted"
        )

        note.setWordWrap(True)

        outer.addWidget(note)

        # -----------------------------------------
        # Scroll
        # -----------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        content = QWidget()

        self.content_layout = QVBoxLayout(
            content
        )

        self.content_layout.setSpacing(16)

        scroll.setWidget(
            content
        )

        outer.addWidget(
            scroll,
            1,
        )

        # -----------------------------------------
        # 作品
        # -----------------------------------------

        work_card = Card(
            "WORK / 当前作品"
        )

        self.work_title_label = QLabel()

        self.work_title_label.setObjectName(
            "resultTitle"
        )

        work_card.body.addWidget(
            self.work_title_label
        )

        original_title = QLabel(
            "原作品 URL"
        )

        original_title.setObjectName(
            "muted"
        )

        work_card.body.addWidget(
            original_title
        )

        self.original_url_label = QLabel()

        self.original_url_label.setObjectName(
            "linkLabel"
        )

        self.original_url_label.setWordWrap(
            True
        )

        work_card.body.addWidget(
            self.original_url_label
        )

        self.content_layout.addWidget(
            work_card
        )

        # -----------------------------------------
        # 待投诉 URL
        # -----------------------------------------

        urls_card = Card(
            "INFRINGING URLS / 待投诉页面"
        )

        self.url_count_label = QLabel()

        self.url_count_label.setObjectName(
            "muted"
        )

        urls_card.body.addWidget(
            self.url_count_label
        )

        self.urls_box = QVBoxLayout()

        self.urls_box.setSpacing(8)

        urls_card.body.addLayout(
            self.urls_box
        )

        copy_urls_btn = QPushButton(
            "复制全部待投诉 URL"
        )

        copy_urls_btn.clicked.connect(
            self.copy_urls
        )

        urls_card.body.addWidget(
            copy_urls_btn,
            alignment=Qt.AlignRight,
        )

        self.content_layout.addWidget(
            urls_card
        )

        # -----------------------------------------
        # 投诉说明
        # -----------------------------------------

        description_card = Card(
            "DESCRIPTION / 投诉说明"
        )

        description_note = QLabel(
            "以下内容仅作为投诉信息准备，"
            "提交前可以根据实际情况修改。"
        )

        description_note.setObjectName(
            "muted"
        )

        description_note.setWordWrap(
            True
        )

        description_card.body.addWidget(
            description_note
        )

        self.description_edit = QTextEdit()

        self.description_edit.setMinimumHeight(
            150
        )

        description_card.body.addWidget(
            self.description_edit
        )

        self.content_layout.addWidget(
            description_card
        )

        # -----------------------------------------
        # 权属材料
        # -----------------------------------------

        materials_card = Card(
            "MATERIALS / 已有作品材料"
        )

        materials_note = QLabel(
            "这里显示当前作品已经保存的可复用材料。"
            "“未配置”不会阻止继续投诉；"
            "实际需要哪些材料，以官方投诉页面当前要求为准。"
        )

        materials_note.setObjectName(
            "muted"
        )

        materials_note.setWordWrap(
            True
        )

        materials_card.body.addWidget(
            materials_note
        )

        self.materials_box = QVBoxLayout()

        self.materials_box.setSpacing(8)

        materials_card.body.addLayout(
            self.materials_box
        )

        self.content_layout.addWidget(
            materials_card
        )

        self.content_layout.addStretch()

        # -----------------------------------------
        # 底部按钮
        # -----------------------------------------

        footer = QHBoxLayout()

        self.selection_label = QLabel()

        self.selection_label.setObjectName(
            "muted"
        )

        footer.addWidget(
            self.selection_label
        )

        footer.addStretch()

        close_btn = QPushButton(
            "关闭"
        )

        close_btn.clicked.connect(
            self.reject
        )

        copy_btn = QPushButton(
            "复制投诉信息"
        )

        copy_btn.clicked.connect(
            self.copy_all_information
        )

        open_btn = QPushButton(
            "打开百度投诉入口"
        )

        open_btn.setObjectName(
            "primaryButton"
        )

        open_btn.clicked.connect(
            self.open_baidu_report
        )

        footer.addWidget(
            close_btn
        )

        footer.addWidget(
            copy_btn
        )

        footer.addWidget(
            open_btn
        )

        outer.addLayout(
            footer
        )

    # =============================================
    # 加载数据
    # =============================================

    def load_data(self):
        title = (
            self.work.get("title")
            or "未命名作品"
        )

        original_url = (
            self.work.get("original_url")
            or "未配置"
        )

        self.work_title_label.setText(
            title
        )

        self.original_url_label.setText(
            original_url
        )

        self.load_urls()
        self.load_description()
        self.load_materials()

        self.selection_label.setText(
            f"本次共 {len(self.items)} 个待投诉页面"
        )

    # =============================================
    # URL
    # =============================================

    def load_urls(self):
        self.clear_layout(
            self.urls_box
        )

        self.url_count_label.setText(
            f"共 {len(self.items)} 条"
        )

        for index, item in enumerate(
            self.items,
            start=1,
        ):
            url = item.get(
                "url",
                "",
            )

            label = QLabel(
                f"{index}. {url}"
            )

            label.setObjectName(
                "linkLabel"
            )

            label.setWordWrap(
                True
            )

            self.urls_box.addWidget(
                label
            )

    def get_urls(self):
        urls = []

        for item in self.items:
            url = (
                item.get("url")
                or ""
            ).strip()

            if url:
                urls.append(url)

        return urls

    # =============================================
    # 投诉说明
    # =============================================

    def load_description(self):
        title = (
            self.work.get("title")
            or "当前作品"
        )

        count = len(
            self.get_urls()
        )

        text = (
            f"本人为作品《{title}》的权利人"
            "或已获得相应授权。"
            f"现发现以下 {count} 个页面"
            "可能存在未经授权使用作品内容的情况。"
            "请平台根据相关规则进行核实处理。"
        )

        self.description_edit.setPlainText(
            text
        )

    # =============================================
    # Materials
    # =============================================

    def load_materials(self):
        self.clear_layout(
            self.materials_box
        )

        work_id = self.work.get(
            "id"
        )

        materials = []

        if work_id:
            materials = (
                self.db.list_work_materials(
                    work_id
                )
            )

        material_map = {}

        for material in materials:
            key = (
                material.get(
                    "material_type"
                ),
                material.get(
                    "name"
                ),
            )

            material_map[key] = material

        for (
            material_type,
            material_name,
        ) in MATERIAL_SLOTS:

            material = material_map.get(
                (
                    material_type,
                    material_name,
                )
            )

            row = QHBoxLayout()

            name_label = QLabel(
                material_name
            )

            row.addWidget(
                name_label
            )

            row.addStretch()

            if material:
                file_path = (
                    material.get(
                        "file_path"
                    )
                    or ""
                )

                file_name = (
                    file_path
                    .replace("\\", "/")
                    .split("/")[-1]
                )

                status = QLabel(
                    f"✓ 已配置    {file_name}"
                )

            else:
                status = QLabel(
                    "○ 未配置"
                )

            status.setObjectName(
                "muted"
            )

            row.addWidget(
                status
            )

            self.materials_box.addLayout(
                row
            )

        # 其他材料
        other_materials = [
            material
            for material in materials
            if material.get(
                "material_type"
            ) == "other"
        ]

        for material in other_materials:
            row = QHBoxLayout()

            name = (
                material.get("name")
                or "其他材料"
            )

            name_label = QLabel(
                name
            )

            row.addWidget(
                name_label
            )

            row.addStretch()

            file_path = (
                material.get(
                    "file_path"
                )
                or ""
            )

            file_name = (
                file_path
                .replace("\\", "/")
                .split("/")[-1]
            )

            status = QLabel(
                f"✓ 已配置    {file_name}"
            )

            status.setObjectName(
                "muted"
            )

            row.addWidget(
                status
            )

            self.materials_box.addLayout(
                row
            )

    # =============================================
    # Copy
    # =============================================

    def copy_urls(self):
        urls = self.get_urls()

        text = "\n".join(
            urls
        )

        QApplication.clipboard().setText(
            text
        )

    def copy_all_information(self):
        title = (
            self.work.get("title")
            or ""
        )

        original_url = (
            self.work.get(
                "original_url"
            )
            or ""
        )

        urls = "\n".join(
            self.get_urls()
        )

        description = (
            self.description_edit
            .toPlainText()
            .strip()
        )

        text = (
            f"作品：{title}\n\n"
            f"原作品 URL：\n"
            f"{original_url}\n\n"
            f"待投诉 URL：\n"
            f"{urls}\n\n"
            f"投诉说明：\n"
            f"{description}"
        )

        QApplication.clipboard().setText(
            text
        )

    # =============================================
    # 百度
    # =============================================

    def open_baidu_report(self):
        webbrowser.open(
            BAIDU_REPORT_URL
        )

    # =============================================
    # Helper
    # =============================================

    def clear_layout(
        self,
        layout,
    ):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

            elif item.layout():
                self.clear_layout(
                    item.layout()
                )