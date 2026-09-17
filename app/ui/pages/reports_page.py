import webbrowser

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QScrollArea,
)

from app.ui.widgets.common import Card
from app.ui.reporting.baidu_prepare_dialog import (
    BaiduPrepareDialog,
)
from app.ui.reporting.work_select_dialog import (
    WorkSelectDialog,
)

PLATFORM_LABELS = {
    "unclassified": "未分类",
    "quark": "夸克",
    "baidu_search": "百度搜索",
    "baidu_netdisk": "百度网盘",
    "wechat_official": "微信公众号",
    "sogou": "搜狗",
    "other": "其他",
}


STATUS_LABELS = {
    "pending": "待处理",
    "processing": "处理中",
    "submitted": "已提交",
    "closed": "已关闭",
}


class ReportsPage(QWidget):
    def __init__(self, db):
        super().__init__()

        self.db = db

        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            24,
            24,
            24,
            24,
        )
        outer.setSpacing(16)

        # =============================================
        # 标题
        # =============================================

        title = QLabel("举报  Reports")
        title.setObjectName("pageTitle")

        outer.addWidget(title)

        note = QLabel(
            "举报池会按照侵权平台自动分组。"
            "搜索来源、页面网站和举报平台彼此独立；"
            "平台识别结果可以由作者手动修改。"
            "最终举报提交始终由作者确认。"
        )

        note.setObjectName("muted")
        note.setWordWrap(True)

        outer.addWidget(note)

        # =============================================
        # 顶部统计
        # =============================================

        summary_card = Card(
            "REPORT POOL / 举报池"
        )

        summary_row = QHBoxLayout()

        self.total_label = QLabel(
            "举报池 0 条"
        )

        self.pending_label = QLabel(
            "待处理 0 条"
        )

        self.platform_label = QLabel(
            "0 个平台"
        )

        summary_row.addWidget(
            self.total_label
        )

        summary_row.addSpacing(24)

        summary_row.addWidget(
            self.pending_label
        )

        summary_row.addSpacing(24)

        summary_row.addWidget(
            self.platform_label
        )

        summary_row.addStretch()

        refresh_btn = QPushButton(
            "刷新"
        )

        refresh_btn.clicked.connect(
            self.refresh
        )

        summary_row.addWidget(
            refresh_btn
        )

        summary_card.body.addLayout(
            summary_row
        )

        outer.addWidget(
            summary_card
        )

        # =============================================
        # 举报池内容
        # =============================================

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.NoFrame
        )

        content = QWidget()

        self.box = QVBoxLayout(
            content
        )

        self.box.setSpacing(16)

        scroll.setWidget(
            content
        )

        outer.addWidget(
            scroll,
            1,
        )

        self.refresh()

    # =============================================
    # Layout 清理
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

    # =============================================
    # 页面刷新
    # =============================================

    def refresh(self):
        self.clear_layout(
            self.box
        )

        items = (
            self.db.list_report_pool()
        )

        # ---------------------------------------------
        # 顶部统计
        # ---------------------------------------------

        total = len(items)

        pending = sum(
            1
            for item in items
            if item["status"] == "pending"
        )

        active_platforms = {
            item["platform"]
            for item in items
            if item["platform"]
            != "unclassified"
        }

        self.total_label.setText(
            f"举报池 {total} 条"
        )

        self.pending_label.setText(
            f"待处理 {pending} 条"
        )

        self.platform_label.setText(
            f"{len(active_platforms)} 个平台"
        )

        # ---------------------------------------------
        # 空状态
        # ---------------------------------------------

        if not items:
            empty = QLabel(
                "举报池目前为空。\n\n"
                "请先在 Search 页面选择疑似页面，"
                "然后点击“加入举报池”。"
            )

            empty.setObjectName(
                "muted"
            )

            empty.setWordWrap(True)

            self.box.addWidget(
                empty
            )

            self.box.addStretch()

            return

        # ---------------------------------------------
        # 按平台分组
        # ---------------------------------------------

        groups = {}

        for item in items:
            platform = (
                item.get("platform")
                or "unclassified"
            )

            groups.setdefault(
                platform,
                [],
            ).append(item)

        # 希望常用平台保持固定顺序
        platform_order = [
            "quark",
            "baidu_search",
            "baidu_netdisk",
            "wechat_official",
            "sogou",
            "other",
            "unclassified",
        ]

        ordered_platforms = []

        for platform in platform_order:
            if platform in groups:
                ordered_platforms.append(
                    platform
                )

        # 兼容未来新增的平台值
        for platform in groups:
            if (
                platform
                not in ordered_platforms
            ):
                ordered_platforms.append(
                    platform
                )

        # ---------------------------------------------
        # 创建平台区域
        # ---------------------------------------------

        for platform in ordered_platforms:
            platform_items = groups[
                platform
            ]

            self.add_platform_group(
                platform,
                platform_items,
            )

        self.box.addStretch()

    # =============================================
    # 平台分组
    # =============================================

    def add_platform_group(
        self,
        platform,
        items,
    ):
        card = Card(
            PLATFORM_LABELS.get(
                platform,
                platform,
            ).upper()
        )

        # ---------------------------------------------
        # 平台标题
        # ---------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            f'{PLATFORM_LABELS.get(platform, platform)}'
            f'    {len(items)} 条'
        )

        title.setObjectName(
            "resultTitle"
        )

        header.addWidget(
            title
        )

        header.addStretch()

        if platform == "unclassified":
            assign_btn = QPushButton(
                "批量指定平台"
            )

            assign_btn.clicked.connect(
                lambda checked=False,
                rows=items:
                self.assign_group_platform(
                    rows
                )
            )

            header.addWidget(
                assign_btn
            )

        else:
            process_btn = QPushButton(
                f"处理"
                f"{PLATFORM_LABELS.get(platform, platform)}"
                f"投诉"
            )

            process_btn.setObjectName(
                "primaryButton"
            )

            process_btn.clicked.connect(
                lambda checked=False,
                p=platform,
                rows=items:
                self.process_platform(
                    p,
                    rows,
                )
            )

            header.addWidget(
                process_btn
            )

        card.body.addLayout(
            header
        )

        # ---------------------------------------------
        # 平台下的 URL
        # ---------------------------------------------

        for item in items:
            card.body.addWidget(
                self.build_pool_item(
                    item
                )
            )

        self.box.addWidget(
            card
        )

    # =============================================
    # 单条举报池记录
    # =============================================

    def build_pool_item(
        self,
        item,
    ):
        frame = QFrame()

        frame.setObjectName(
            "resultCard"
        )

        layout = QVBoxLayout(
            frame
        )

        # ---------------------------------------------
        # 作品
        # ---------------------------------------------

        work_title = (
            item.get("work_title")
            or "未命名作品"
        )

        title = QLabel(
            work_title
        )

        title.setObjectName(
            "resultTitle"
        )

        layout.addWidget(
            title
        )

        # ---------------------------------------------
        # URL
        # ---------------------------------------------

        url = QLabel(
            item["url"]
        )

        url.setObjectName(
            "linkLabel"
        )

        url.setWordWrap(True)

        layout.addWidget(
            url
        )

        # ---------------------------------------------
        # Meta
        # ---------------------------------------------

        status = STATUS_LABELS.get(
            item["status"],
            item["status"],
        )

        domain = (
            item.get("domain")
            or ""
        )

        meta = QLabel(
            f"状态：{status}"
            f"    页面网站：{domain}"
        )

        meta.setObjectName(
            "muted"
        )

        layout.addWidget(
            meta
        )

        # ---------------------------------------------
        # 操作
        # ---------------------------------------------

        row = QHBoxLayout()

        row.addStretch()
        # ---------------------------------------------
        # 平台纠错入口
        # ---------------------------------------------

        if item["platform"] in (
            "unclassified",
            "other",
        ):
            change_btn = QPushButton(
                "修改平台"
            )

            change_btn.clicked.connect(
                lambda checked=False,
                pool_id=item["id"],
                current=item["platform"]:
                self.open_platform_editor(
                    pool_id,
                    current,
                )
            )

            row.addWidget(
                change_btn
            )
        open_btn = QPushButton(
            "打开页面"
        )

        remove_btn = QPushButton(
            "移出举报池"
        )

        open_btn.clicked.connect(
            lambda checked=False,
            u=item["url"]:
            webbrowser.open(u)
        )

        remove_btn.clicked.connect(
            lambda checked=False,
            pool_id=item["id"]:
            self.remove_item(
                pool_id
            )
        )

        row.addWidget(
            open_btn
        )

        row.addWidget(
            remove_btn
        )

        layout.addLayout(
            row
        )

        return frame

    # =============================================
    # 修改单条平台
    # =============================================
    def open_platform_editor(
        self,
        pool_id,
        current_platform,
    ):
        dialog = QMessageBox(
            self
        )

        dialog.setWindowTitle(
            "修改平台"
        )

        dialog.setText(
            "请选择这个页面实际所属的举报平台。"
        )

        buttons = {}

        choices = [
            ("夸克", "quark"),
            ("百度搜索", "baidu_search"),
            ("百度网盘", "baidu_netdisk"),
            ("微信公众号", "wechat_official"),
            ("搜狗", "sogou"),
            ("其他", "other"),
        ]

        for label, platform in choices:
            button = dialog.addButton(
                label,
                QMessageBox.ActionRole,
            )

            buttons[button] = platform

        dialog.addButton(
            "取消",
            QMessageBox.RejectRole,
        )

        dialog.exec()

        clicked = dialog.clickedButton()

        platform = buttons.get(
            clicked
        )

        if not platform:
            return

        if platform == current_platform:
            return

        self.change_platform(
            pool_id,
            platform,
        )

    def change_platform(
        self,
        pool_id,
        platform,
    ):
        self.db.update_report_pool_platform(
            pool_id,
            platform,
        )

        self.refresh()

    # =============================================
    # 未分类 → 批量指定平台
    # =============================================

    def assign_group_platform(
        self,
        items,
    ):
        if not items:
            return

        dialog = QMessageBox(
            self
        )

        dialog.setWindowTitle(
            "批量指定平台"
        )

        dialog.setText(
            "请选择要把当前“未分类”页面"
            "统一指定到的平台。"
        )

        buttons = {}

        choices = [
            ("夸克", "quark"),
            ("百度搜索", "baidu_search"),
            ("百度网盘", "baidu_netdisk"),
            ("微信公众号", "wechat_official"),
            ("搜狗", "sogou"),
            ("其他", "other"),
        ]

        for label, platform in choices:
            button = dialog.addButton(
                label,
                QMessageBox.ActionRole,
            )

            buttons[button] = platform

        dialog.addButton(
            "取消",
            QMessageBox.RejectRole,
        )

        dialog.exec()

        clicked = (
            dialog.clickedButton()
        )

        platform = buttons.get(
            clicked
        )

        if not platform:
            return

        for item in items:
            self.db.update_report_pool_platform(
                item["id"],
                platform,
            )

        self.refresh()

    # =============================================
    # 移出举报池
    # =============================================

    def remove_item(
        self,
        pool_id,
    ):
        answer = QMessageBox.question(
            self,
            "移出举报池",
            "确定将这个页面移出举报池吗？\n\n"
            "搜索结果本身不会被删除。",
        )

        if answer != QMessageBox.Yes:
            return

        self.db.delete_report_pool_item(
            pool_id
        )

        self.refresh()

    # =============================================
    # 平台处理入口
    # =============================================

    def process_platform(
        self,
        platform,
        items,
    ):
        # ---------------------------------------------
        # 百度搜索
        # ---------------------------------------------

        if platform == "baidu_search":
            self.process_baidu_search(
                items
            )
            return

        # ---------------------------------------------
        # 其他平台暂时保持占位
        # ---------------------------------------------

        label = PLATFORM_LABELS.get(
            platform,
            platform,
        )

        QMessageBox.information(
            self,
            f"{label}投诉",
            f"当前共有 {len(items)} 条"
            f"{label}页面待处理。\n\n"
            "当前平台的投诉准备流程"
            "尚未接入。\n\n"
            "当前版本不会自动提交举报。",
        )


    def process_baidu_search(
        self,
        items,
    ):
        if not items:
            return

        # ---------------------------------------------
        # 按作品分组
        # ---------------------------------------------

        work_groups = {}

        for item in items:
            work_id = item.get(
                "work_id"
            )

            if not work_id:
                continue

            work_groups.setdefault(
                work_id,
                [],
            ).append(item)

        if not work_groups:
            QMessageBox.warning(
                self,
                "百度搜索投诉",
                "当前举报池记录没有关联作品，"
                "无法准备投诉。",
            )
            return

        # ---------------------------------------------
        # 获取作品
        # ---------------------------------------------

        works = self.db.list_works()

        # ---------------------------------------------
        # 单作品：直接处理
        # 多作品：先选择作品
        # ---------------------------------------------

        if len(work_groups) == 1:
            work_id = next(
                iter(work_groups)
            )

        else:
            select_dialog = WorkSelectDialog(
                work_groups=work_groups,
                works=works,
                parent=self,
            )

            result = select_dialog.exec()

            if not result:
                return

            work_id = (
                select_dialog.selected_work_id
            )

            if not work_id:
                return

        work_items = work_groups.get(
            work_id,
            [],
        )

        if not work_items:
            QMessageBox.warning(
                self,
                "百度搜索投诉",
                "当前作品没有可处理的"
                "百度搜索投诉页面。",
            )
            return

        work = next(
            (
                row
                for row in works
                if row["id"] == work_id
            ),
            None,
        )

        if not work:
            QMessageBox.warning(
                self,
                "百度搜索投诉",
                "没有找到对应的作品记录。",
            )
            return

        # ---------------------------------------------
        # 打开百度投诉准备弹窗
        # ---------------------------------------------

        dialog = BaiduPrepareDialog(
            db=self.db,
            work=work,
            items=work_items,
            parent=self,
        )

        dialog.exec()