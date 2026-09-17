from typing import Dict, Type

from .base import SearchProvider
from .mock import MockSearchProvider
from .baidu import BaiduSearchProvider


SEARCH_ENGINES = [
    "必应",
    "百度",
    "搜狗",
    "360",
    "夸克",
    "UC",
    "QQ",
    "DuckDuckGo",
]


class SearchProviderRegistry:
    """
    Copyright Guard 搜索 Provider 注册中心。

    当前 V0.2：
    - 未接入真实搜索的来源继续使用 Mock
    - 百度可以从数据库绑定的 API Service 创建真实 Provider
    """

    def __init__(self):
        self._providers: Dict[
            str,
            Type[SearchProvider]
        ] = {}

    def register(
        self,
        engine_name: str,
        provider_class: Type[SearchProvider],
    ):
        self._providers[engine_name] = provider_class

    def get(
        self,
        engine_name: str,
        db=None,
    ) -> SearchProvider:
        """
        获取搜索来源对应的 Provider。

        如果传入 db：
        优先读取 search_sources -> api_services 的绑定配置。

        如果没有数据库配置：
        回退到原来的静态 Registry。
        """

        # ==========================================
        # V0.2 数据库配置
        # ==========================================

        if db is not None:
            sources = db.list_search_sources()

            source = next(
                (
                    item
                    for item in sources
                    if item["name"] == engine_name
                ),
                None,
            )

            if source:
                service_id = source.get(
                    "api_service_id"
                )

                if service_id:
                    service = db.get_api_service(
                        service_id
                    )

                    if service and service.get(
                        "enabled"
                    ):
                        provider_type = service.get(
                            "provider_type",
                            "",
                        )

                        # --------------------------
                        # 百度官方 API
                        # --------------------------

                        if provider_type == "baidu":
                            return BaiduSearchProvider(
                                api_key=service.get(
                                    "api_key",
                                    "",
                                ),
                                endpoint=service.get(
                                    "endpoint",
                                    "",
                                ),
                            )

        # ==========================================
        # 静态 Registry 回退
        # ==========================================

        provider_class = self._providers.get(
            engine_name
        )

        if provider_class is None:
            raise ValueError(
                f"未找到搜索 Provider: {engine_name}"
            )

        return provider_class()

    def has(
        self,
        engine_name: str,
    ) -> bool:
        return engine_name in self._providers

    def available_engines(self):
        return list(
            self._providers.keys()
        )

    def get_provider_class(
        self,
        engine_name: str,
    ):
        return self._providers.get(
            engine_name
        )

    def get_engine_info(
        self,
        engine_name: str,
        db=None,
    ):
        """
        返回搜索来源当前状态。
        """

        # ==========================================
        # 数据库状态
        # ==========================================

        if db is not None:
            sources = db.list_search_sources()

            source = next(
                (
                    item
                    for item in sources
                    if item["name"] == engine_name
                ),
                None,
            )

            if source:
                service_id = source.get(
                    "api_service_id"
                )

                service = (
                    db.get_api_service(service_id)
                    if service_id
                    else None
                )

                return {
                    "engine": engine_name,
                    "registered": True,
                    "enabled": bool(
                        source.get("enabled")
                    ),
                    "api_service_id":
                        service_id,
                    "api_service_name":
                        (
                            service.get("name")
                            if service
                            else None
                        ),
                    "provider_type":
                        (
                            service.get(
                                "provider_type"
                            )
                            if service
                            else "mock"
                        ),
                    "credential_configured":
                        bool(
                            service
                            and service.get(
                                "api_key"
                            )
                        ),
                    "is_real":
                        bool(service),
                }

        # ==========================================
        # 静态状态
        # ==========================================

        provider_class = (
            self.get_provider_class(
                engine_name
            )
        )

        if provider_class is None:
            return {
                "engine": engine_name,
                "registered": False,
                "provider": None,
            }

        return {
            "engine": engine_name,
            "registered": True,
            "provider":
                provider_class.__name__,
            "provider_type": getattr(
                provider_class,
                "provider_type",
                "unknown",
            ),
            "requires_api_key": getattr(
                provider_class,
                "requires_api_key",
                False,
            ),
            "is_real": getattr(
                provider_class,
                "is_real",
                False,
            ),
            "credential_key": getattr(
                provider_class,
                "credential_key",
                None,
            ),
        }

    def get_all_engine_info(
        self,
        db=None,
    ):
        return [
            self.get_engine_info(
                engine,
                db=db,
            )
            for engine in SEARCH_ENGINES
        ]


search_provider_registry = (
    SearchProviderRegistry()
)


# ==============================================
# 默认 Mock
# ==============================================

for engine in SEARCH_ENGINES:
    search_provider_registry.register(
        engine,
        MockSearchProvider,
    )


# ==============================================
# 百度静态回退
#
# 如果数据库没有绑定 API Service，
# 仍然允许 BaiduSearchProvider 使用环境变量。
# ==============================================

search_provider_registry.register(
    "百度",
    BaiduSearchProvider,
)