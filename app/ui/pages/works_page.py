from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QSizePolicy,
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


class WorksPage(QWidget):
    def __init__(
        self,
        db,
        on_changed=None,
    ):
        super().__init__()

        self.db = db
        self.on_changed = on_changed
        self.current_id = None

        self.material_rows = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(
            24,
            24,
            24,
            24,
        )
        lay.setSpacing(16)

        # =====================================================
        # Page title
        # =====================================================

        title = QLabel(
            "作品与资料  Works & Materials"
        )
        title.setObjectName(
            "pageTitle"
        )
        lay.addWidget(title)

        # =====================================================
        # Work selector
        # =====================================================

        top = QHBoxLayout()

        self.selector = QComboBox()

        new_btn = QPushButton(
            "＋ 新建作品"
        )

        top.addWidget(
            self.selector,
            1,
        )
        top.addWidget(
            new_btn
        )

        lay.addLayout(top)

        # =====================================================
        # Scrollable content
        # =====================================================

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(16)

        scroll.setWidget(
            content
        )

        lay.addWidget(
            scroll,
            1,
        )

        # =====================================================
        # Work information
        # =====================================================

        card = Card(
            "作品资料"
        )

        form = QFormLayout()

        self.fields = {}

        for key, label in [
            (
                "title",
                "作品名称",
            ),
            (
                "author",
                "作者 / 笔名",
            ),
            (
                "original_url",
                "Original URL",
            ),
            (
                "characters",
                "主要角色",
            ),
            (
                "aliases",
                "别名 / 曾用名",
            ),
            (
                "keywords",
                "自定义搜索关键词",
            ),
            (
                "rights_holder",
                "版权所有人",
            ),
            (
                "contact",
                "联系方式",
            ),
        ]:
            edit = QLineEdit()

            self.fields[key] = edit

            form.addRow(
                label,
                edit,
            )

        self.description = QTextEdit()
        self.description.setMaximumHeight(
            90
        )

        # 旧 evidence 字段暂时继续保留，
        # 防止历史数据丢失。
        self.evidence = QLineEdit()

        form.addRow(
            "作品说明",
            self.description,
        )

        form.addRow(
            "旧版证据备注",
            self.evidence,
        )

        card.body.addLayout(form)

        save = QPushButton(
            "保存作品资料"
        )
        save.setObjectName(
            "primaryButton"
        )

        card.body.addWidget(save)

        content_layout.addWidget(
            card
        )


        # =====================================================
        # Reusable materials
        # =====================================================

        self.material_card = Card(
            "可复用权属材料"
        )

        material_note = QLabel(
            "这些材料与当前作品绑定，可在百度、微信、"
            "搜狗等举报流程中重复使用。"
        )
        material_note.setWordWrap(True)

        self.material_card.body.addWidget(
            material_note
        )

        self.materials_layout = QVBoxLayout()
        self.materials_layout.setSpacing(
            10
        )

        self.material_card.body.addLayout(
            self.materials_layout
        )

        for material_type, name in MATERIAL_SLOTS:
            self.create_material_slot(
                material_type,
                name,
            )

        # -----------------------------------------------------
        # Other materials
        # -----------------------------------------------------

        other_header = QHBoxLayout()

        other_title = QLabel(
            "其他材料"
        )

        other_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.add_other_btn = QPushButton(
            "＋ 添加其他材料"
        )

        other_header.addWidget(
            other_title
        )

        other_header.addStretch()

        other_header.addWidget(
            self.add_other_btn
        )

        self.material_card.body.addLayout(
            other_header
        )

        self.other_materials_layout = (
            QVBoxLayout()
        )

        self.other_materials_layout.setSpacing(
            8
        )

        self.material_card.body.addLayout(
            self.other_materials_layout
        )

        content_layout.addWidget(
            self.material_card
        )


        # =====================================================
        # Signals
        # =====================================================

        self.selector.currentIndexChanged.connect(
            self.load_current
        )

        new_btn.clicked.connect(
            self.new_work
        )

        save.clicked.connect(
            self.save
        )

        self.add_other_btn.clicked.connect(
            self.add_other_material
        )

        self.refresh()

    # =========================================================
    # Material slots
    # =========================================================

    def create_material_slot(
        self,
        material_type,
        name,
    ):
        row = QHBoxLayout()

        label = QLabel(name)
        label.setMinimumWidth(140)
        label.setMinimumHeight(36)

        status = QLabel(
            "未配置"
        )
        status.setMinimumHeight(36)

        status.setWordWrap(True)

        select_btn = QPushButton(
            "选择文件"
        )

        remove_btn = QPushButton(
            "移除"
        )

        remove_btn.setEnabled(
            False
        )

        row.addWidget(
            label
        )

        row.addWidget(
            status,
            1,
        )

        row.addWidget(
            select_btn
        )

        row.addWidget(
            remove_btn
        )

        self.materials_layout.addLayout(
            row
        )

        key = (
            material_type,
            name,
        )

        self.material_rows[key] = {
            "type": material_type,
            "name": name,
            "status": status,
            "select_btn": select_btn,
            "remove_btn": remove_btn,
            "material_id": None,
            "file_path": "",
        }

        select_btn.clicked.connect(
            lambda checked=False,
            k=key:
            self.select_slot_file(k)
        )

        remove_btn.clicked.connect(
            lambda checked=False,
            k=key:
            self.remove_slot_material(k)
        )

    def select_slot_file(
        self,
        key,
    ):
        if not self.current_id:
            QMessageBox.warning(
                self,
                "提示",
                "请先保存作品，再添加权属材料。",
            )
            return

        row = self.material_rows[
            key
        ]

        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "选择权属证明材料",
                "",
                (
                    "支持的文件 "
                    "(*.pdf *.png *.jpg *.jpeg);;"
                    "PDF 文件 (*.pdf);;"
                    "图片 (*.png *.jpg *.jpeg);;"
                    "所有文件 (*)"
                ),
            )
        )

        if not file_path:
            return

        old_id = row[
            "material_id"
        ]

        if old_id:
            self.db.update_work_material(
                old_id,
                {
                    "material_type":
                        row["type"],
                    "name":
                        row["name"],
                    "file_path":
                        file_path,
                    "description":
                        "",
                },
            )
        else:
            self.db.add_work_material(
                work_id=self.current_id,
                material_type=row["type"],
                name=row["name"],
                file_path=file_path,
            )

        self.refresh_materials()

    def remove_slot_material(
        self,
        key,
    ):
        row = self.material_rows[
            key
        ]

        material_id = row[
            "material_id"
        ]

        if not material_id:
            return

        answer = QMessageBox.question(
            self,
            "移除材料",
            (
                f"确定从作品资料中移除"
                f"“{row['name']}”吗？\n\n"
                "只会移除 Copyright Guard "
                "中的材料记录，不会删除电脑上的原文件。"
            ),
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.db.delete_work_material(
            material_id
        )

        self.refresh_materials()

    # =========================================================
    # Other materials
    # =========================================================

    def add_other_material(
        self,
    ):
        if not self.current_id:
            QMessageBox.warning(
                self,
                "提示",
                "请先保存作品，再添加其他材料。",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            "添加其他材料"
        )

        layout = QVBoxLayout(
            dialog
        )

        form = QFormLayout()

        name_edit = QLineEdit()

        path_row = QHBoxLayout()

        path_edit = QLineEdit()
        path_edit.setReadOnly(
            True
        )

        browse_btn = QPushButton(
            "选择文件"
        )

        path_row.addWidget(
            path_edit,
            1,
        )

        path_row.addWidget(
            browse_btn
        )

        description_edit = QLineEdit()

        form.addRow(
            "材料名称",
            name_edit,
        )

        form.addRow(
            "文件",
            path_row,
        )

        form.addRow(
            "备注",
            description_edit,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            |
            QDialogButtonBox.StandardButton.Cancel
        )

        layout.addWidget(
            buttons
        )

        def choose_file():
            file_path, _ = (
                QFileDialog.getOpenFileName(
                    dialog,
                    "选择材料文件",
                    "",
                    (
                        "支持的文件 "
                        "(*.pdf *.png *.jpg *.jpeg);;"
                        "所有文件 (*)"
                    ),
                )
            )

            if file_path:
                path_edit.setText(
                    file_path
                )

        browse_btn.clicked.connect(
            choose_file
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        name = (
            name_edit.text().strip()
        )

        file_path = (
            path_edit.text().strip()
        )

        if not name:
            QMessageBox.warning(
                self,
                "提示",
                "请输入材料名称。",
            )
            return

        if not file_path:
            QMessageBox.warning(
                self,
                "提示",
                "请选择材料文件。",
            )
            return

        self.db.add_work_material(
            work_id=self.current_id,
            material_type="other",
            name=name,
            file_path=file_path,
            description=(
                description_edit
                .text()
                .strip()
            ),
        )

        self.refresh_materials()

    def clear_other_materials(
        self,
    ):
        while (
            self.other_materials_layout.count()
        ):
            item = (
                self.other_materials_layout
                .takeAt(0)
            )

            widget = item.widget()

            if widget:
                widget.deleteLater()

            child_layout = (
                item.layout()
            )

            if child_layout:
                self.clear_layout(
                    child_layout
                )

    def clear_layout(
        self,
        layout,
    ):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

            child_layout = item.layout()

            if child_layout:
                self.clear_layout(
                    child_layout
                )

    def add_other_material_row(
        self,
        material,
    ):
        row = QHBoxLayout()

        name = QLabel(
            material["name"]
        )

        file_name = QLabel(
            Path(
                material["file_path"]
            ).name
        )

        file_name.setToolTip(
            material["file_path"]
        )

        remove_btn = QPushButton(
            "移除"
        )

        row.addWidget(
            name
        )

        row.addWidget(
            file_name,
            1,
        )

        row.addWidget(
            remove_btn
        )

        self.other_materials_layout.addLayout(
            row
        )

        remove_btn.clicked.connect(
            lambda checked=False,
            material_id=material["id"]:
            self.remove_other_material(
                material_id
            )
        )

    def remove_other_material(
        self,
        material_id,
    ):
        answer = QMessageBox.question(
            self,
            "移除材料",
            (
                "确定移除这份材料吗？\n\n"
                "不会删除电脑上的原文件。"
            ),
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.db.delete_work_material(
            material_id
        )

        self.refresh_materials()

    # =========================================================
    # Refresh materials
    # =========================================================

    def refresh_materials(
        self,
    ):
        for row in (
            self.material_rows.values()
        ):
            row[
                "material_id"
            ] = None

            row[
                "file_path"
            ] = ""

            row[
                "status"
            ].setText(
                "未配置"
            )

            row[
                "status"
            ].setToolTip(
                ""
            )

            row[
                "select_btn"
            ].setText(
                "选择文件"
            )

            row[
                "remove_btn"
            ].setEnabled(
                False
            )

        self.clear_other_materials()

        if not self.current_id:
            return

        materials = (
            self.db.list_work_materials(
                self.current_id
            )
        )

        for material in materials:
            key = (
                material[
                    "material_type"
                ],
                material[
                    "name"
                ],
            )

            if key in self.material_rows:
                row = (
                    self.material_rows[
                        key
                    ]
                )

                row[
                    "material_id"
                ] = material[
                    "id"
                ]

                row[
                    "file_path"
                ] = material[
                    "file_path"
                ]

                row[
                    "status"
                ].setText(
                    "✓ "
                    + Path(
                        material[
                            "file_path"
                        ]
                    ).name
                )

                row[
                    "status"
                ].setToolTip(
                    material[
                        "file_path"
                    ]
                )

                row[
                    "select_btn"
                ].setText(
                    "更换"
                )

                row[
                    "remove_btn"
                ].setEnabled(
                    True
                )

            else:
                self.add_other_material_row(
                    material
                )

    # =========================================================
    # Works
    # =========================================================

    def refresh(self):
        old = self.current_id

        self.selector.blockSignals(
            True
        )

        self.selector.clear()

        for work in (
            self.db.list_works()
        ):
            self.selector.addItem(
                work["title"],
                work["id"],
            )

        self.selector.blockSignals(
            False
        )

        if old:
            idx = (
                self.selector.findData(
                    old
                )
            )

            if idx >= 0:
                self.selector.setCurrentIndex(
                    idx
                )

        if self.selector.count():
            self.load_current()
        else:
            self.new_work()

    def load_current(self):
        work_id = (
            self.selector.currentData()
        )

        if not work_id:
            return

        self.current_id = work_id

        work = self.db.get_work(
            work_id
        )

        if not work:
            return

        for key, edit in (
            self.fields.items()
        ):
            edit.setText(
                work.get(
                    key,
                    "",
                )
            )

        self.description.setPlainText(
            work.get(
                "description",
                "",
            )
        )

        self.evidence.setText(
            work.get(
                "evidence",
                "",
            )
        )

        self.refresh_materials()

    def new_work(self):
        self.current_id = None

        self.selector.blockSignals(
            True
        )

        self.selector.setCurrentIndex(
            -1
        )

        self.selector.blockSignals(
            False
        )

        for edit in (
            self.fields.values()
        ):
            edit.clear()

        self.description.clear()
        self.evidence.clear()

        self.refresh_materials()

        self.fields[
            "title"
        ].setFocus()

    def save(self):
        if not (
            self.fields[
                "title"
            ]
            .text()
            .strip()
        ):
            QMessageBox.warning(
                self,
                "提示",
                "请输入作品名称。",
            )
            return

        data = {
            key:
            edit.text().strip()
            for key, edit
            in self.fields.items()
        }

        data.update(
            id=self.current_id,
            description=(
                self.description
                .toPlainText()
                .strip()
            ),
            evidence=(
                self.evidence
                .text()
                .strip()
            ),
        )

        self.current_id = (
            self.db.save_work(
                data
            )
        )

        self.refresh()

        if self.on_changed:
            self.on_changed()

        QMessageBox.information(
            self,
            "已保存",
            "作品资料已保存。",
        )