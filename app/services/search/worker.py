from PySide6.QtCore import (
    QObject,
    QRunnable,
    Signal,
    Slot,
)


class SearchWorkerSignals(QObject):
    """
    SearchWorker 与 GUI 主线程之间的信号。

    参数：
    engine_name
    query
    result / error
    """

    result = Signal(
        str,
        str,
        list,
    )

    error = Signal(
        str,
        str,
        str,
    )

    finished = Signal(
        str,
        str,
    )


class SearchWorker(QRunnable):
    """
    在 QThreadPool 中执行一个搜索任务。

    一个 Worker =
    一个搜索来源 × 一个关键词。

    Worker：
    - 不操作 UI
    - 不写 SQLite
    - 只负责调用 Provider
    """

    def __init__(
        self,
        engine_name,
        provider,
        query,
        work,
    ):
        super().__init__()

        self.engine_name = engine_name
        self.provider = provider
        self.query = query
        self.work = work

        self.signals = SearchWorkerSignals()

    @Slot()
    def run(self):
        try:
            results = self.provider.search(
                self.query,
                self.work,
            )

            normalized_results = []

            for result in results or []:
                item = dict(result)

                item["sources"] = [
                    self.engine_name
                ]

                item["work_id"] = (
                    self.work["id"]
                )

                normalized_results.append(
                    item
                )

            self.signals.result.emit(
                self.engine_name,
                self.query,
                normalized_results,
            )

        except Exception as exc:
            self.signals.error.emit(
                self.engine_name,
                self.query,
                str(exc),
            )

        finally:
            self.signals.finished.emit(
                self.engine_name,
                self.query,
            )