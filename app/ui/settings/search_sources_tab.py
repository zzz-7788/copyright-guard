from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QCheckBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QAbstractItemView,
)

from app.ui.widgets.common import Card


class SearchSourcesTab(QWidget):
    """
    搜索来源设置。

    负责：
    - 显示搜索来源
    - 添加自定义搜索来源
    - 编辑搜索来源
    - 绑定 API Service
    - 启用 / 禁用搜索来源
    """

    def __init__(self, db):
        super().__init__()

        self.db = db

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        layout.setSpacing(16)

        card = Card(
            "Search Sources / 搜索来源"
        )

        # ==========================================
        # Header
        # ==========================================

        top = QHBoxLayout()

        description = QLabel(
            "管理搜索页面中可使用的搜索来源，"
            "并绑定 API 服务。"
        )

        description.setObjectName(
            "muted"
        )

        description.setWordWrap(True)

        add_button = QPushButton(
            "＋ 添加搜索来源"
        )

        add_button.setObjectName(
            "primaryButton"
        )

        add_button.clicked.connect(
            self.open_add_source_dialog
        )

        top.addWidget(description)
        top.addStretch()
        top.addWidget(add_button)

        card.body.addLayout(top)

        # ==========================================
        # Table
        # ==========================================

        self.sources_table = (
            QTableWidget()
        )

        self.sources_table.setColumnCount(
            6
        )

        self.sources_table.setHorizontalHeaderLabels(
            [
                "搜索来源",
                "显示名称",
                "API 服务",
                "状态",
                "类型",
                "操作",
            ]
        )

        self.sources_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.sources_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        header = (
            self.sources_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        card.body.addWidget(
            self.sources_table
        )

        refresh_button = QPushButton(
            "刷新"
        )

        refresh_button.clicked.connect(
            self.refresh_sources
        )

        card.body.addWidget(
            refresh_button
        )

        layout.addWidget(card)
        layout.addStretch()

        self.refresh_sources()

    # =========================================================
    # Refresh
    # =========================================================

    def refresh_sources(self):
        sources = (
            self.db.list_search_sources()
        )

        self.sources_table.setRowCount(
            len(sources)
        )

        for row, source in enumerate(
            sources
        ):
            self.sources_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    source.get(
                        "name",
                        "",
                    )
                ),
            )

            self.sources_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    source.get(
                        "display_name",
                        "",
                    )
                ),
            )

            service_name = (
                source.get(
                    "api_service_name"
                )
                or "未配置"
            )

            self.sources_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    service_name
                ),
            )

            status = (
                "● 启用"
                if source.get("enabled")
                else "○ 禁用"
            )

            self.sources_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    status
                ),
            )

            source_type = (
                "内置"
                if source.get(
                    "is_builtin"
                )
                else "自定义"
            )

            self.sources_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    source_type
                ),
            )

            config_button = QPushButton(
                "配置"
            )

            source_id = source["id"]

            config_button.clicked.connect(
                lambda checked=False,
                sid=source_id:
                    self.open_edit_source_dialog(
                        sid
                    )
            )

            self.sources_table.setCellWidget(
                row,
                5,
                config_button,
            )

    # =========================================================
    # Add Source
    # =========================================================

    def open_add_source_dialog(self):
        dialog = QDialog(self)

        dialog.setWindowTitle(
            "添加搜索来源"
        )

        dialog.resize(
            480,
            260,
        )

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        name = QLineEdit()

        name.setPlaceholderText(
            "例如：Example Search"
        )

        display_name = QLineEdit()

        display_name.setPlaceholderText(
            "例如：Example"
        )

        source_key = QLineEdit()

        source_key.setPlaceholderText(
            "第三方 API 中的来源标识，"
            "例如 example"
        )

        service_combo = QComboBox()

        service_combo.addItem(
            "未配置",
            None,
        )

        services = (
            self.db.list_api_services()
        )

        for service in services:
            service_combo.addItem(
                service["name"],
                service["id"],
            )

        enabled = QCheckBox("启用")
        enabled.setChecked(True)

        form.addRow(
            "名称",
            name,
        )

        form.addRow(
            "显示名称",
            display_name,
        )

        form.addRow(
            "API 服务",
            service_combo,
        )

        form.addRow(
            "来源标识",
            source_key,
        )

        form.addRow(
            "",
            enabled,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(buttons)

        if (
            dialog.exec()
            != QDialog.Accepted
        ):
            return

        source_name = (
            name.text().strip()
        )

        if not source_name:
            QMessageBox.warning(
                self,
                "无法添加",
                "请输入搜索来源名称。",
            )
            return

        try:
            self.db.add_search_source(
                {
                    "name":
                        source_name,

                    "display_name":
                        display_name
                        .text()
                        .strip(),

                    "api_service_id":
                        service_combo
                        .currentData(),

                    "source_key":
                        source_key
                        .text()
                        .strip(),

                    "enabled":
                        enabled
                        .isChecked(),
                }
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "添加失败",
                str(exc),
            )
            return

        self.refresh_sources()

        QMessageBox.information(
            self,
            "添加成功",
            "搜索来源已添加。",
        )

    # =========================================================
    # Edit Source
    # =========================================================

    def open_edit_source_dialog(
        self,
        source_id,
    ):
        source = (
            self.db.get_search_source(
                source_id
            )
        )

        if not source:
            QMessageBox.warning(
                self,
                "无法配置",
                "没有找到这个搜索来源。",
            )
            return

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "配置搜索来源"
        )

        dialog.resize(
            500,
            320,
        )

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        # ------------------------------------------
        # Name
        # ------------------------------------------

        name = QLineEdit(
            source.get(
                "name",
                "",
            )
        )

        if source.get(
            "is_builtin"
        ):
            name.setReadOnly(True)

        # ------------------------------------------
        # Display Name
        # ------------------------------------------

        display_name = QLineEdit(
            source.get(
                "display_name",
                "",
            )
        )

        # ------------------------------------------
        # API Service
        # ------------------------------------------

        service_combo = QComboBox()

        service_combo.addItem(
            "未配置",
            None,
        )

        services = (
            self.db.list_api_services()
        )

        for service in services:
            if not service.get(
                "enabled"
            ):
                continue

            service_combo.addItem(
                service["name"],
                service["id"],
            )

        current_service_id = (
            source.get(
                "api_service_id"
            )
        )

        if current_service_id:
            index = (
                service_combo.findData(
                    current_service_id
                )
            )

            if index >= 0:
                service_combo.setCurrentIndex(
                    index
                )

        # ------------------------------------------
        # Source Key
        # ------------------------------------------

        source_key = QLineEdit(
            source.get(
                "source_key",
                "",
            )
        )

        source_key.setPlaceholderText(
            "Provider 中使用的来源标识"
        )

        # ------------------------------------------
        # Enabled
        # ------------------------------------------

        enabled = QCheckBox(
            "启用这个搜索来源"
        )

        enabled.setChecked(
            bool(
                source.get("enabled")
            )
        )

        form.addRow(
            "名称",
            name,
        )

        form.addRow(
            "显示名称",
            display_name,
        )

        form.addRow(
            "API 服务",
            service_combo,
        )

        form.addRow(
            "来源标识",
            source_key,
        )

        form.addRow(
            "",
            enabled,
        )

        layout.addLayout(form)

        note = QLabel(
            "搜索来源决定 Search 页面显示什么；"
            "API 服务决定该来源通过哪个 "
            "Provider 执行真实搜索。"
        )

        note.setObjectName(
            "muted"
        )

        note.setWordWrap(True)

        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(buttons)

        if (
            dialog.exec()
            != QDialog.Accepted
        ):
            return

        new_name = (
            name.text().strip()
        )

        if not new_name:
            QMessageBox.warning(
                self,
                "无法保存",
                "搜索来源名称不能为空。",
            )
            return

        try:
            self.db.update_search_source(
                source_id,
                {
                    "name":
                        new_name,

                    "display_name":
                        display_name
                        .text()
                        .strip(),

                    "api_service_id":
                        service_combo
                        .currentData(),

                    "source_key":
                        source_key
                        .text()
                        .strip(),

                    "enabled":
                        enabled
                        .isChecked(),
                },
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "保存失败",
                str(exc),
            )
            return

        self.refresh_sources()

        QMessageBox.information(
            self,
            "已保存",
            "搜索来源配置已更新。",
        )

    # =========================================================
    # External refresh
    # =========================================================

    def refresh(self):
        """
        给 SettingsPage 调用的统一刷新接口。
        """
        self.refresh_sources()