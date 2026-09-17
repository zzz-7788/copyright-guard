import webbrowser
from urllib.parse import urlparse
from datetime import datetime
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QComboBox,QCheckBox,QLineEdit,
    QPushButton,QProgressBar,QScrollArea,QFrame,QMessageBox,QDialog,QFormLayout,QMenu
)
from app.ui.widgets.common import Card
from app.services.search.registry import search_provider_registry
from app.services.search.worker import SearchWorker

STATUS_LABEL = {"potential":"疑似页面","confirmed":"已确认","ignored":"已忽略","reported":"已举报"}

class AddPageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加页面")
        self.resize(520,190)
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://example.com/page")
        self.title = QLineEdit()
        self.status = QComboBox()
        for key, value in STATUS_LABEL.items():
            self.status.addItem(value, key)
        form.addRow("网站 URL", self.url)
        form.addRow("页面标题", self.title)
        form.addRow("状态", self.status)
        lay.addLayout(form)
        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("取消")
        add = QPushButton("添加页面")
        add.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject)
        add.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(add)
        lay.addLayout(row)

class ResultCard(QFrame):
    def __init__(self, result, page):
        super().__init__()

        self.result = result
        self.page = page

        self.setObjectName("resultCard")

        lay = QVBoxLayout(self)

        # ---------------------------------------------
        # 标题 + 选择框
        # ---------------------------------------------

        title_row = QHBoxLayout()

        self.select_box = QCheckBox()
        self.select_box.setToolTip(
            "选择此页面加入举报池"
        )

        self.select_box.setChecked(
            result["id"] in self.page.selected_result_ids
        )

        self.select_box.toggled.connect(
            lambda checked:
            self.page.set_result_selected(
                result["id"],
                checked,
            )
        )

        title = QLabel(result["title"])
        title.setObjectName("resultTitle")

        title_row.addWidget(self.select_box)
        title_row.addWidget(title, 1)

        lay.addLayout(title_row)

        url = QLabel(result["url"])
        url.setObjectName("linkLabel")
        url.setWordWrap(True)
        lay.addWidget(url)

        meta = QLabel(
            f'{STATUS_LABEL.get(result["status"], result["status"])}    '
            f'来源：{result["sources"] or "手动添加"}    '
            f'发现于 {result["found_at"]}'
        )
        meta.setObjectName("muted")
        lay.addWidget(meta)

        if result.get("snippet"):
            snippet = QLabel(result["snippet"])
            snippet.setObjectName("muted")
            snippet.setWordWrap(True)
            lay.addWidget(snippet)

        row = QHBoxLayout()
        row.addStretch()
        open_btn = QPushButton("打开页面")
        mark_btn = QPushButton("标记")
        report_btn = QPushButton("加入举报池")
        delete_btn = QPushButton("删除")
        open_btn.clicked.connect(lambda: webbrowser.open(result["url"]))
        mark_btn.clicked.connect(self.show_mark_menu)
        report_btn.clicked.connect(self.report)
        delete_btn.clicked.connect(self.delete)
        for btn in [open_btn,mark_btn,report_btn,delete_btn]:
            row.addWidget(btn)
        lay.addLayout(row)

    def show_mark_menu(self):
        menu = QMenu(self)
        for label, status in [("疑似页面","potential"),("已确认","confirmed"),("已忽略","ignored")]:
            action = menu.addAction(label)
            action.triggered.connect(lambda checked=False, s=status: self.set_status(s))
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def set_status(self, status):
        self.page.db.update_result_status(self.result["id"], status)
        self.page.refresh_results()
        self.page.changed()

    def report(self):
        pool_id = (
            self.page.db.add_result_to_report_pool(
                self.result["id"]
            )
        )

        QMessageBox.information(
            self,
            "已加入举报池",
            "该页面已加入举报池。\n\n"
            "之后可以在 Reports 中按平台统一处理。",
        )

        self.page.changed()

    def delete(self):
        if QMessageBox.question(self,"删除","确定删除这个页面记录吗？") == QMessageBox.Yes:
            self.page.db.delete_result(self.result["id"])
            self.page.refresh_results()
            self.page.changed()

class SearchPage(QWidget):
    def __init__(self, db, on_data_changed=None):
        super().__init__()
        self.db = db
        self.on_data_changed = on_data_changed
        # 当前勾选的搜索结果 ID
        self.selected_result_ids = set()

        # 当前过滤后实际显示的结果 ID
        self.visible_result_ids = []
        # 从数据库读取当前启用的搜索来源
        self.search_sources = self.db.list_search_sources(
            enabled_only=True
        )

        self.engine_names = [
            source["name"]
            for source in self.search_sources
        ]

        self.active_engines = []

        self.thread_pool = (
            QThreadPool.globalInstance()
        )

            # 多关键词搜索任务状态
        self.pending_tasks = set()
        self.finished_tasks = set()

        self.engine_states = {}
        self.engine_task_total = {}
        self.engine_task_finished = {}
        self.engine_task_errors = {}

        self.search_total = 0
        self.search_errors = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24,24,24,24)
        outer.setSpacing(16)
        title = QLabel("搜索  Search")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(16)

        config = Card("SEARCH CONFIGURATION")
        work_row = QHBoxLayout()
        work_row.addWidget(QLabel("作品"))
        self.work = QComboBox()
        work_row.addWidget(self.work,1)
        config.body.addLayout(work_row)

        self.engine_grid = QGridLayout()
        self.engine_checks = {}

        for i, engine in enumerate(self.engine_names):
            cb = QCheckBox(engine)
            cb.setChecked(True)

            self.engine_checks[engine] = cb

            self.engine_grid.addWidget(
                cb,
                i // 4,
                i % 4,
            )

        config.body.addLayout(
            self.engine_grid
        )

        config.body.addWidget(QLabel("搜索关键词"))

        # 动态关键词区域
        self.queries = []
        self.query_rows = []

        self.query_container = QVBoxLayout()
        self.query_container.setSpacing(8)
        config.body.addLayout(self.query_container)

        # 默认创建 3 个关键词输入框
        for _ in range(3):
            self.add_query_row()

        # 添加关键词按钮
        query_action_row = QHBoxLayout()

        self.add_query_btn = QPushButton("＋ 添加关键词")
        self.add_query_btn.clicked.connect(
            lambda: self.add_query_row()
        )

        query_action_row.addWidget(
            self.add_query_btn
        )
        query_action_row.addStretch()

        config.body.addLayout(
            query_action_row
        )

        self.start = QPushButton("开始搜索")
        self.start.setObjectName("primaryButton")
        config.body.addWidget(self.start)
        lay.addWidget(config)

        activity = Card("SEARCH ACTIVITY")
        self.progress = QProgressBar()
        self.summary = QLabel("等待搜索")
        self.summary.setObjectName("muted")
        self.engine_status = QLabel(
            "\n".join(
                f"○ {engine}  等待中"
                for engine in self.engine_names
            )
        )
        activity.body.addWidget(self.progress)
        activity.body.addWidget(self.summary)
        activity.body.addWidget(self.engine_status)
        lay.addWidget(activity)

        found = Card("FOUND PAGES / 找到的页面")
        toolbar = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部","all")
        for key, value in STATUS_LABEL.items():
            self.status_filter.addItem(value,key)
        self.source_filter = QComboBox()
        self.source_filter.addItem(
            "全部",
            "all",
        )

        for engine in self.engine_names:
            self.source_filter.addItem(
                engine,
                engine,
            )

        self.source_filter.addItem(
            "手动添加",
            "手动添加",
        )
        self.local_search = QLineEdit()
        self.local_search.setPlaceholderText("🔍 搜索结果")
        self.add_btn = QPushButton("＋ 添加页面")
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.source_filter)
        toolbar.addWidget(self.local_search,1)
        toolbar.addWidget(self.add_btn)
        found.body.addLayout(toolbar)
                # =============================================
        # 批量选择 / 举报池操作
        # =============================================

        batch_row = QHBoxLayout()

        self.select_all_btn = QPushButton(
            "全选当前结果"
        )

        self.clear_selection_btn = QPushButton(
            "取消选择"
        )

        self.selection_label = QLabel(
            "已选择 0 条"
        )
        self.selection_label.setObjectName(
            "muted"
        )

        self.add_pool_btn = QPushButton(
            "加入举报池"
        )
        self.add_pool_btn.setObjectName(
            "primaryButton"
        )
        self.add_pool_btn.setEnabled(False)

        batch_row.addWidget(
            self.select_all_btn
        )
        batch_row.addWidget(
            self.clear_selection_btn
        )

        batch_row.addStretch()

        batch_row.addWidget(
            self.selection_label
        )
        batch_row.addWidget(
            self.add_pool_btn
        )

        found.body.addLayout(
            batch_row
        )

        self.results_box = QVBoxLayout()
        found.body.addLayout(self.results_box)
        lay.addWidget(found)

        scroll.setWidget(content)
        outer.addWidget(scroll,1)

        self.start.clicked.connect(self.begin_search)
        self.add_btn.clicked.connect(self.add_manual)
        self.select_all_btn.clicked.connect(
            self.select_all_visible_results
        )

        self.clear_selection_btn.clicked.connect(
            self.clear_result_selection
        )

        self.add_pool_btn.clicked.connect(
            self.add_selected_to_report_pool
        )
        self.status_filter.currentIndexChanged.connect(self.refresh_results)
        self.source_filter.currentIndexChanged.connect(self.refresh_results)
        self.local_search.textChanged.connect(self.refresh_results)
        self.work.currentIndexChanged.connect(self.autofill_queries)

        self.refresh_works()
        self.refresh_results()
    def set_result_selected(
        self,
        result_id,
        checked,
    ):
        """
        更新单条结果的选择状态。
        """

        if checked:
            self.selected_result_ids.add(
                result_id
            )
        else:
            self.selected_result_ids.discard(
                result_id
            )

        self.update_selection_status()

    def update_selection_status(self):
        """
        更新批量操作栏。
        """

        count = len(
            self.selected_result_ids
        )

        self.selection_label.setText(
            f"已选择 {count} 条"
        )

        self.add_pool_btn.setEnabled(
            count > 0
        )

    def select_all_visible_results(self):
        """
        全选当前过滤条件下可见的结果。
        """

        self.selected_result_ids.update(
            self.visible_result_ids
        )

        self.refresh_results()
        self.update_selection_status()

    def clear_result_selection(self):
        """
        清除全部选择。
        """

        self.selected_result_ids.clear()

        self.refresh_results()
        self.update_selection_status()

    def add_selected_to_report_pool(self):
        """
        将当前选择的结果批量加入举报池。
        """

        result_ids = list(
            self.selected_result_ids
        )

        if not result_ids:
            return

        result = (
            self.db.add_results_to_report_pool(
                result_ids
            )
        )

        failed = result.get(
            "failed",
            [],
        )

        success_count = (
            len(result_ids)
            - len(failed)
        )

        if failed:
            QMessageBox.warning(
                self,
                "部分完成",
                f"已处理 {success_count} 条。\n"
                f"{len(failed)} 条加入失败。",
            )
        else:
            QMessageBox.information(
                self,
                "已加入举报池",
                f"已将 {success_count} 条页面"
                f"加入举报池。\n\n"
                "当前暂时归入“未分类”，"
                "之后可以按平台统一整理。",
            )

        self.selected_result_ids.clear()

        self.refresh_results()
        self.update_selection_status()

        self.changed()
    def changed(self):
        if self.on_data_changed:
            self.on_data_changed()

    def showEvent(self, event):
        super().showEvent(event)

        if hasattr(
            self,
            "engine_checks",
        ):
            self.refresh_search_sources()


    def refresh_search_sources(self):
        """
        从数据库重新读取启用的搜索来源。

        用于 Settings 中新增、启用或禁用搜索来源后，
        刷新 Search 页。
        """

        sources = self.db.list_search_sources(
            enabled_only=True
        )

        new_names = [
            source["name"]
            for source in sources
        ]

        # 没变化就不重建
        if new_names == self.engine_names:
            return

        self.search_sources = sources
        self.engine_names = new_names

        # -----------------------------
        # 重建搜索来源复选框
        # -----------------------------

        for checkbox in self.engine_checks.values():
            checkbox.setParent(None)
            checkbox.deleteLater()

        self.engine_checks.clear()

        for i, engine in enumerate(self.engine_names):
            cb = QCheckBox(engine)
            cb.setChecked(True)

            self.engine_checks[engine] = cb

            self.engine_grid.addWidget(
                cb,
                i // 4,
                i % 4,
            )

        # -----------------------------
        # 重建来源过滤器
        # -----------------------------

        old_source = self.source_filter.currentData()

        self.source_filter.blockSignals(True)
        self.source_filter.clear()

        self.source_filter.addItem(
            "全部",
            "all",
        )

        for engine in self.engine_names:
            self.source_filter.addItem(
                engine,
                engine,
            )

        self.source_filter.addItem(
            "手动添加",
            "手动添加",
        )

        index = self.source_filter.findData(
            old_source
        )

        if index >= 0:
            self.source_filter.setCurrentIndex(
                index
            )

        self.source_filter.blockSignals(False)

        # -----------------------------
        # Activity
        # -----------------------------

        self.engine_status.setText(
            "\n".join(
                f"○ {engine}  等待中"
                for engine in self.engine_names
            )
        )

    def refresh_works(self):
        old = self.work.currentData()
        self.work.blockSignals(True)
        self.work.clear()
        for item in self.db.list_works():
            self.work.addItem(item["title"], item["id"])
        self.work.blockSignals(False)
        if old:
            idx = self.work.findData(old)
            if idx >= 0:
                self.work.setCurrentIndex(idx)
        self.autofill_queries()


    def add_query_row(self, text=""):
        row_widget = QWidget()

        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        edit = QLineEdit()
        edit.setPlaceholderText(
            "输入作品标题、角色名、独特句子等"
        )
        edit.setText(text)

        remove_btn = QPushButton("删除")
        remove_btn.setFixedWidth(64)

        row.addWidget(edit, 1)
        row.addWidget(remove_btn)

        self.query_container.addWidget(
            row_widget
        )

        self.queries.append(edit)

        self.query_rows.append(
            (row_widget, edit)
        )

        remove_btn.clicked.connect(
            lambda checked=False,
            widget=row_widget,
            editor=edit:
            self.remove_query_row(
                widget,
                editor,
            )
        )


    def remove_query_row(
        self,
        row_widget,
        edit,
    ):
        # 至少保留一个关键词输入框
        if len(self.queries) <= 1:
            edit.clear()
            return

        if edit in self.queries:
            self.queries.remove(edit)

        self.query_rows = [
            item
            for item in self.query_rows
            if item[0] is not row_widget
        ]

        self.query_container.removeWidget(
            row_widget
        )

        row_widget.deleteLater()

    def autofill_queries(self):
        work_id = self.work.currentData()

        work = (
            self.db.get_work(work_id)
            if work_id
            else None
        )

        if not work:
            return

        title = work["title"]
        author = work["author"]

        character = (
            work["characters"]
            .split(",")[0]
            .strip()
            if work["characters"]
            else ""
        )

        values = [
            f'"{title}"',
            (
                f'"{title}" "{author}"'
                if author
                else f'"{title}"'
            ),
            (
                f'"{character}" "{title}"'
                if character
                else f'"{title}"'
            ),
        ]

        # 保证至少有 3 个输入框
        while len(self.queries) < 3:
            self.add_query_row()

        # 只自动更新前三个默认关键词。
        # 用户自己添加的第 4、5、6... 个不会被覆盖。
        for i, value in enumerate(values):
            self.queries[i].setText(value)

    def begin_search(self):
        # ==============================================
        # 收集搜索来源
        # ==============================================

        self.active_engines = [
            engine
            for engine, checkbox
            in self.engine_checks.items()
            if checkbox.isChecked()
        ]

        # ==============================================
        # 收集关键词
        # ==============================================

        queries = [
            edit.text().strip()
            for edit in self.queries
            if edit.text().strip()
        ]

        # 去掉完全重复的关键词，同时保持顺序
        queries = list(
            dict.fromkeys(queries)
        )

        # ==============================================
        # 当前作品
        # ==============================================

        work_id = self.work.currentData()

        work = (
            self.db.get_work(work_id)
            if work_id
            else None
        )

        if not work:
            QMessageBox.warning(
                self,
                "提示",
                "请先选择作品。",
            )
            return

        if not self.active_engines:
            QMessageBox.warning(
                self,
                "提示",
                "请至少选择一个搜索引擎。",
            )
            return

        if not queries:
            QMessageBox.warning(
                self,
                "提示",
                "请至少输入一个搜索关键词。",
            )
            return

        # ==============================================
        # 初始化任务状态
        # ==============================================

        self.pending_tasks = set()
        self.finished_tasks = set()

        self.search_errors = {}

        self.search_total = (
            len(self.active_engines)
            * len(queries)
        )

        self.engine_states = {
            engine: "waiting"
            for engine in self.active_engines
        }

        self.engine_task_total = {
            engine: len(queries)
            for engine in self.active_engines
        }

        self.engine_task_finished = {
            engine: 0
            for engine in self.active_engines
        }

        self.engine_task_errors = {
            engine: 0
            for engine in self.active_engines
        }

        self.progress.setValue(0)

        self.summary.setText(
            f"开始搜索 · "
            f"0 / {self.search_total} 个任务 · "
            f"{len(self.active_engines)} 个来源 · "
            f"{len(queries)} 个关键词"
        )

        self.start.setEnabled(False)
        self.work.setEnabled(False)
        self.add_query_btn.setEnabled(False)

        for edit in self.queries:
            edit.setEnabled(False)

        self.update_engine_status()

        # ==============================================
        # 创建搜索任务
        # ==============================================

        for engine in self.active_engines:
            try:
                provider = (
                    search_provider_registry.get(
                        engine,
                        db=self.db,
                    )
                )

            except Exception as exc:
                message = str(exc)

                self.engine_states[engine] = (
                    "error"
                )

                # Provider 初始化失败意味着这个来源
                # 对应的全部关键词任务都失败。
                for query in queries:
                    task_key = (
                        engine,
                        query,
                    )

                    self.finished_tasks.add(
                        task_key
                    )

                    self.search_errors[
                        task_key
                    ] = message

                self.engine_task_finished[
                    engine
                ] = len(queries)

                self.engine_task_errors[
                    engine
                ] = len(queries)

                continue

            self.engine_states[engine] = (
                "running"
            )

            # 每一个关键词创建一个独立 Worker
            for query in queries:
                task_key = (
                    engine,
                    query,
                )

                self.pending_tasks.add(
                    task_key
                )

                worker = SearchWorker(
                    engine_name=engine,
                    provider=provider,
                    query=query,
                    work=work,
                )

                worker.signals.result.connect(
                    self.on_search_result
                )

                worker.signals.error.connect(
                    self.on_search_error
                )

                worker.signals.finished.connect(
                    self.on_search_finished
                )

                self.thread_pool.start(
                    worker
                )

        self.update_engine_status()

        # 如果所有 Provider 初始化都失败
        if not self.pending_tasks:
            self.finish_search()

    def on_search_result(
        self,
        engine,
        query,
        results,
    ):
        """
        单个「来源 × 关键词」任务返回结果。
        """

        saved_count = 0

        for result in results:
            try:
                self.db.add_result(
                    result
                )

                saved_count += 1

            except Exception as exc:
                print(
                    f"[Save Error] "
                    f"{engine} / "
                    f"{query}: {exc}"
                )

        self.refresh_results()

        print(
            f"[Search Result] "
            f"{engine} / "
            f"{query}: "
            f"{len(results)} results, "
            f"{saved_count} saved"
        )

    def on_search_error(
        self,
        engine,
        query,
        message,
    ):
        task_key = (
            engine,
            query,
        )

        self.search_errors[
            task_key
        ] = message

        self.engine_task_errors[
            engine
        ] += 1

        print(
            f"[Search Error] "
            f"{engine} / "
            f"{query}: {message}"
        )

    def on_search_finished(
        self,
        engine,
        query,
    ):
        task_key = (
            engine,
            query,
        )

        # 防止重复 finished
        if task_key in self.finished_tasks:
            return

        self.pending_tasks.discard(
            task_key
        )

        self.finished_tasks.add(
            task_key
        )

        self.engine_task_finished[
            engine
        ] += 1

        finished = len(
            self.finished_tasks
        )

        if self.search_total:
            progress = int(
                finished
                / self.search_total
                * 100
            )
        else:
            progress = 0

        self.progress.setValue(
            progress
        )

        engine_done = (
            self.engine_task_finished[
                engine
            ]
        )

        engine_total = (
            self.engine_task_total[
                engine
            ]
        )

        # 这个来源的全部关键词完成
        if engine_done >= engine_total:
            if (
                self.engine_task_errors[
                    engine
                ]
                >= engine_total
            ):
                self.engine_states[
                    engine
                ] = "error"

            elif (
                self.engine_task_errors[
                    engine
                ] > 0
            ):
                self.engine_states[
                    engine
                ] = "partial"

            else:
                self.engine_states[
                    engine
                ] = "done"

        else:
            self.engine_states[
                engine
            ] = "running"

        self.update_engine_status()

        count = len(
            self.db.list_results(
                self.work.currentData()
            )
        )

        self.summary.setText(
            f"{finished} / "
            f"{self.search_total} 个任务 · "
            f"已发现 {count} 个页面"
        )

        if not self.pending_tasks:
            self.finish_search()


    def update_engine_status(self):
        lines = []

        for engine in self.active_engines:
            state = self.engine_states.get(
                engine,
                "waiting",
            )

            done = (
                self.engine_task_finished.get(
                    engine,
                    0,
                )
            )

            total = (
                self.engine_task_total.get(
                    engine,
                    0,
                )
            )

            errors = (
                self.engine_task_errors.get(
                    engine,
                    0,
                )
            )

            if state == "waiting":
                lines.append(
                    f"○ {engine}  等待中 "
                    f"0/{total}"
                )

            elif state == "running":
                lines.append(
                    f"● {engine}  搜索中 "
                    f"{done}/{total}"
                )

            elif state == "done":
                lines.append(
                    f"✓ {engine}  已完成 "
                    f"{done}/{total}"
                )

            elif state == "partial":
                lines.append(
                    f"△ {engine}  已完成 "
                    f"{done}/{total} · "
                    f"{errors} 个失败"
                )

            elif state == "error":
                lines.append(
                    f"✕ {engine}  失败 "
                    f"{done}/{total}"
                )

        self.engine_status.setText(
            "\n".join(lines)
        )


    def finish_search(self):
        self.start.setEnabled(True)
        self.work.setEnabled(True)
        self.add_query_btn.setEnabled(True)

        for edit in self.queries:
            edit.setEnabled(True)

        self.progress.setValue(100)

        count = len(
            self.db.list_results(
                self.work.currentData()
            )
        )

        error_count = len(
            self.search_errors
        )

        success_count = (
            self.search_total
            - error_count
        )

        if error_count:
            self.summary.setText(
                f"搜索完成 · "
                f"{success_count} 成功 / "
                f"{error_count} 失败 · "
                f"共 {self.search_total} 个任务 · "
                f"已保存 {count} 个页面"
            )

        else:
            self.summary.setText(
                f"搜索完成 · "
                f"{self.search_total} / "
                f"{self.search_total} 个任务 · "
                f"已保存 {count} 个页面"
            )

        self.refresh_results()
        self.changed()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def refresh_results(self):
        self.clear_layout(
            self.results_box
        )

        status = (
            self.status_filter.currentData()
        )

        source = (
            self.source_filter.currentData()
        )

        text = (
            self.local_search
            .text()
            .strip()
            .lower()
        )

        self.visible_result_ids = []

        for result in self.db.list_results(
            self.work.currentData()
        ):
            if (
                status != "all"
                and result["status"] != status
            ):
                continue

            if (
                source != "all"
                and source not in (
                    result["sources"] or ""
                )
            ):
                continue

            haystack = (
                f'{result["title"]} '
                f'{result["url"]} '
                f'{result["domain"]}'
            ).lower()

            if text and text not in haystack:
                continue

            self.visible_result_ids.append(
                result["id"]
            )

            self.results_box.addWidget(
                ResultCard(
                    result,
                    self,
                )
            )

        self.results_box.addStretch()

        self.update_selection_status()

    def add_manual(self):
        dialog = AddPageDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        raw = dialog.url.text().strip()
        if not raw:
            return
        if "://" not in raw:
            raw = "https://" + raw
        parsed = urlparse(raw)
        if not parsed.netloc:
            QMessageBox.warning(self,"URL 无效","请输入有效的网站 URL。")
            return
        self.db.add_result({
            "work_id": self.work.currentData(),
            "title": dialog.title.text().strip() or parsed.netloc,
            "url": parsed.geturl(),
            "domain": parsed.netloc,
            "snippet": "用户手动添加的页面。",
            "sources": ["手动添加"],
            "status": dialog.status.currentData(),
            "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.refresh_results()
        self.changed()
