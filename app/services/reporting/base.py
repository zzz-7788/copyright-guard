from abc import ABC, abstractmethod

class ReportingAdapter(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_report_entry(self, url: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def prepare_report(self, case: dict) -> dict:
        raise NotImplementedError
