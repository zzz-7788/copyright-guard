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
from app.services.search.baidu import BaiduSearchProvider


class ApiServicesTab(QWidget):
    """
    API 服务设置。

    负责：
    - API Service 列表
    - 添加 API Service
    - 编辑 API Service
    - 测试 API Service
    - 删除 API Service
    """

    def __init__(
        self,
        db,
        on_services_changed=None,
    ):
        super().__init__()

        self.db = db
        self.on_services_changed = (
            on_services_changed
        )

        self.build_ui()

    # =========================================================
    # UI
    # =========================================================

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
            "API Services / API 服务"
        )

        top = QHBoxLayout()

        description = QLabel(
            "API Key 在这里统一管理。"
            "一个 API 服务可以被多个搜索来源使用。"
        )
        description.setObjectName("muted")
        description.setWordWrap(True)

        add_button = QPushButton(
            "＋ 添加 API 服务"
        )
        add_button.setObjectName(
            "primaryButton"
        )
        add_button.clicked.connect(
            self.open_add_api_dialog
        )

        top.addWidget(description)
        top.addStretch()
        top.addWidget(add_button)

        card.body.addLayout(top)

        # ==========================================
        # Table
        # ==========================================

        self.api_table = QTableWidget()

        self.api_table.setColumnCount(6)

        self.api_table.setHorizontalHeaderLabels(
            [
                "服务名称",
                "Provider",
                "Endpoint",
                "API Key",
                "状态",
                "操作",
            ]
        )

        self.api_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.api_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        header = (
            self.api_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        card.body.addWidget(
            self.api_table
        )

        refresh_button = QPushButton(
            "刷新"
        )
        refresh_button.clicked.connect(
            self.refresh
        )

        card.body.addWidget(
            refresh_button
        )

        layout.addWidget(card)
        layout.addStretch()

        self.refresh()

    # =========================================================
    # Refresh
    # =========================================================

    def refresh(self):
        services = (
            self.db.list_api_services()
        )

        self.api_table.setRowCount(
            len(services)
        )

        for row, service in enumerate(
            services
        ):
            self.api_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    service.get(
                        "name",
                        "",
                    )
                ),
            )

            self.api_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    service.get(
                        "provider_type",
                        "",
                    )
                ),
            )

            self.api_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    service.get(
                        "endpoint",
                        "",
                    )
                ),
            )

            api_key = service.get(
                "api_key",
                "",
            )

            masked_key = (
                "••••••••"
                if api_key
                else "未配置"
            )

            self.api_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    masked_key
                ),
            )

            status = (
                "● 启用"
                if service.get(
                    "enabled"
                )
                else "○ 禁用"
            )

            self.api_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    status
                ),
            )

            # ======================================
            # Actions
            # ======================================

            actions = QWidget()

            actions_layout = QHBoxLayout(
                actions
            )

            actions_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )
            actions_layout.setSpacing(6)

            edit_button = QPushButton(
                "编辑"
            )
            test_button = QPushButton(
                "测试"
            )
            delete_button = QPushButton(
                "删除"
            )

            service_id = service["id"]

            edit_button.clicked.connect(
                lambda checked=False,
                sid=service_id:
                    self.open_edit_api_dialog(
                        sid
                    )
            )

            test_button.clicked.connect(
                lambda checked=False,
                sid=service_id:
                    self.test_api_service(
                        sid
                    )
            )

            delete_button.clicked.connect(
                lambda checked=False,
                sid=service_id:
                    self.delete_api_service(
                        sid
                    )
            )

            actions_layout.addWidget(
                edit_button
            )
            actions_layout.addWidget(
                test_button
            )
            actions_layout.addWidget(
                delete_button
            )

            self.api_table.setCellWidget(
                row,
                5,
                actions,
            )

    # =========================================================
    # Notify
    # =========================================================

    def notify_services_changed(self):
        """
        API Service 发生变化后通知外部组件。

        目前主要用于刷新 SearchSourcesTab。
        """

        if self.on_services_changed:
            self.on_services_changed()

    # =========================================================
    # Add
    # =========================================================

    def open_add_api_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(
            "添加 API 服务"
        )
        dialog.resize(520, 340)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        name = QLineEdit()
        name.setPlaceholderText(
            "例如：百度千帆"
        )

        provider = QComboBox()

        provider.addItem(
            "Custom API",
            "custom",
        )

        provider.addItem(
            "Baidu Search API",
            "baidu",
        )

        endpoint = QLineEdit()
        endpoint.setPlaceholderText(
            "https://api.example.com/search"
        )

        api_key = QLineEdit()
        api_key.setEchoMode(
            QLineEdit.Password
        )
        api_key.setPlaceholderText(
            "输入 API Key"
        )

        show_key = QCheckBox(
            "显示 API Key"
        )

        def toggle_key(checked):
            api_key.setEchoMode(
                QLineEdit.Normal
                if checked
                else QLineEdit.Password
            )

        show_key.toggled.connect(
            toggle_key
        )

        auth = QComboBox()

        auth.addItem(
            "Bearer Token",
            "bearer",
        )
        auth.addItem(
            "API Key",
            "api_key",
        )
        auth.addItem(
            "None",
            "none",
        )

        enabled = QCheckBox("启用")
        enabled.setChecked(True)

        form.addRow(
            "服务名称",
            name,
        )
        form.addRow(
            "Provider",
            provider,
        )
        form.addRow(
            "Endpoint",
            endpoint,
        )
        form.addRow(
            "API Key",
            api_key,
        )
        form.addRow(
            "",
            show_key,
        )
        form.addRow(
            "认证方式",
            auth,
        )
        form.addRow(
            "",
            enabled,
        )

        layout.addLayout(form)

        note = QLabel(
            "注意：V0.2 当前会将 API Key "
            "保存在本机 SQLite。"
            "输入框隐藏并不代表数据库中的 "
            "Key 已加密。"
        )
        note.setObjectName("muted")
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

        service_name = (
            name.text().strip()
        )

        if not service_name:
            QMessageBox.warning(
                self,
                "无法添加",
                "请输入 API 服务名称。",
            )
            return

        try:
            self.db.add_api_service(
                {
                    "name":
                        service_name,

                    "provider_type":
                        provider.currentData(),

                    "api_key":
                        api_key.text().strip(),

                    "endpoint":
                        endpoint.text().strip(),

                    "auth_type":
                        auth.currentData(),

                    "enabled":
                        enabled.isChecked(),
                }
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "添加失败",
                str(exc),
            )
            return

        self.refresh()
        self.notify_services_changed()

        QMessageBox.information(
            self,
            "添加成功",
            "API 服务已添加。",
        )

    # =========================================================
    # Edit
    # =========================================================

    def open_edit_api_dialog(
        self,
        service_id,
    ):
        service = (
            self.db.get_api_service(
                service_id
            )
        )

        if not service:
            QMessageBox.warning(
                self,
                "无法编辑",
                "没有找到这个 API 服务。",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            "编辑 API 服务"
        )
        dialog.resize(520, 360)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        name = QLineEdit(
            service.get(
                "name",
                "",
            )
        )

        provider = QComboBox()

        provider.addItem(
            "Custom API",
            "custom",
        )
        provider.addItem(
            "Baidu Search API",
            "baidu",
        )

        provider_index = (
            provider.findData(
                service.get(
                    "provider_type",
                    "custom",
                )
            )
        )

        if provider_index >= 0:
            provider.setCurrentIndex(
                provider_index
            )

        endpoint = QLineEdit(
            service.get(
                "endpoint",
                "",
            )
        )

        api_key = QLineEdit(
            service.get(
                "api_key",
                "",
            )
        )

        api_key.setEchoMode(
            QLineEdit.Password
        )

        show_key = QCheckBox(
            "显示 API Key"
        )

        def toggle_key(checked):
            api_key.setEchoMode(
                QLineEdit.Normal
                if checked
                else QLineEdit.Password
            )

        show_key.toggled.connect(
            toggle_key
        )

        auth = QComboBox()

        auth.addItem(
            "Bearer Token",
            "bearer",
        )
        auth.addItem(
            "API Key",
            "api_key",
        )
        auth.addItem(
            "None",
            "none",
        )

        auth_index = auth.findData(
            service.get(
                "auth_type",
                "bearer",
            )
        )

        if auth_index >= 0:
            auth.setCurrentIndex(
                auth_index
            )

        enabled = QCheckBox("启用")

        enabled.setChecked(
            bool(
                service.get(
                    "enabled"
                )
            )
        )

        form.addRow(
            "服务名称",
            name,
        )
        form.addRow(
            "Provider",
            provider,
        )
        form.addRow(
            "Endpoint",
            endpoint,
        )
        form.addRow(
            "API Key",
            api_key,
        )
        form.addRow(
            "",
            show_key,
        )
        form.addRow(
            "认证方式",
            auth,
        )
        form.addRow(
            "",
            enabled,
        )

        layout.addLayout(form)

        note = QLabel(
            "API Key 当前保存在本机 SQLite 中，"
            "输入框隐藏不代表数据库内容已经加密。"
        )
        note.setObjectName("muted")
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

        service_name = (
            name.text().strip()
        )

        if not service_name:
            QMessageBox.warning(
                self,
                "无法保存",
                "API 服务名称不能为空。",
            )
            return

        try:
            self.db.update_api_service(
                service_id,
                {
                    "name":
                        service_name,

                    "provider_type":
                        provider.currentData(),

                    "api_key":
                        api_key.text().strip(),

                    "endpoint":
                        endpoint.text().strip(),

                    "auth_type":
                        auth.currentData(),

                    "enabled":
                        enabled.isChecked(),
                },
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "保存失败",
                str(exc),
            )
            return

        self.refresh()
        self.notify_services_changed()

        QMessageBox.information(
            self,
            "已保存",
            "API 服务已更新。",
        )

    # =========================================================
    # Test
    # =========================================================

    def test_api_service(
        self,
        service_id,
    ):
        service = (
            self.db.get_api_service(
                service_id
            )
        )

        if not service:
            QMessageBox.warning(
                self,
                "测试失败",
                "没有找到这个 API 服务。",
            )
            return

        if not service.get("enabled"):
            QMessageBox.warning(
                self,
                "服务已禁用",
                "请先启用这个 API 服务。",
            )
            return

        provider_type = service.get(
            "provider_type",
            "",
        )

        if provider_type == "baidu":
            try:
                provider = (
                    BaiduSearchProvider(
                        api_key=service.get(
                            "api_key",
                            "",
                        ),
                        endpoint=service.get(
                            "endpoint",
                            "",
                        ),
                    )
                )

                results = provider.search(
                    "Copyright Guard 测试"
                )

            except Exception as exc:
                QMessageBox.critical(
                    self,
                    "连接失败",
                    (
                        "百度搜索 API "
                        "测试失败：\n\n"
                        f"{exc}"
                    ),
                )
                return

            QMessageBox.information(
                self,
                "连接成功",
                (
                    "百度搜索 API "
                    "可以正常访问。\n\n"
                    f"本次返回 "
                    f"{len(results)} "
                    "个搜索结果。"
                ),
            )
            return

        if provider_type == "custom":
            QMessageBox.information(
                self,
                "暂不支持测试",
                (
                    "这是一个 Custom API 服务。\n\n"
                    "当前还没有对应的请求/响应 "
                    "Adapter，因此不能仅凭 "
                    "Endpoint 和 API Key "
                    "执行连接测试。"
                ),
            )
            return

        QMessageBox.warning(
            self,
            "未知 Provider",
            (
                "当前版本不支持 Provider："
                f"{provider_type}"
            ),
        )

    # =========================================================
    # Delete
    # =========================================================

    def delete_api_service(
        self,
        service_id,
    ):
        service = (
            self.db.get_api_service(
                service_id
            )
        )

        if not service:
            return

        answer = QMessageBox.question(
            self,
            "删除 API 服务",
            (
                f'确定删除“{service["name"]}”吗？\n\n'
                "绑定到该服务的搜索来源"
                "会自动变为“未配置”。"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.db.delete_api_service(
                service_id
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "删除失败",
                str(exc),
            )
            return

        self.refresh()
        self.notify_services_changed()

        QMessageBox.information(
            self,
            "已删除",
            "API 服务已删除。",
        )