from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """
    所有搜索 Provider 的统一基类。
    """

    # 显示名称
    name = "Base"

    # Provider 类型，例如 api / mock / browser
    provider_type = "unknown"

    # 是否需要 API Key
    requires_api_key = False

    # 是否已经是真实搜索 Provider
    is_real = False

    # Settings 中保存凭据时使用的 key
    credential_key = None

    @abstractmethod
    def search(self, query: str, work=None):
        raise NotImplementedError

    def get_info(self):
        """
        给 Settings / Search UI 使用的 Provider 信息。
        """
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "requires_api_key": self.requires_api_key,
            "is_real": self.is_real,
            "credential_key": self.credential_key,
        }