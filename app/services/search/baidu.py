import os
from urllib.parse import urlparse

import requests

from .base import SearchProvider


class BaiduSearchProvider(SearchProvider):
    """
    百度真实搜索 Provider。

    API Key 优先级：

    1. Settings / SQLite 传入
    2. BAIDU_SEARCH_API_KEY 环境变量

    Endpoint 优先级：

    1. Settings / SQLite 传入
    2. 默认百度搜索 Endpoint
    """

    name = "百度"

    provider_type = "api"
    requires_api_key = True
    is_real = True

    credential_key = (
        "baidu_search_api_key"
    )

    DEFAULT_API_URL = (
        "https://qianfan.baidubce.com"
        "/v2/ai_search/web_search"
    )

    def __init__(
        self,
        api_key=None,
        endpoint=None,
    ):
        # -----------------------------------------
        # API Key
        # -----------------------------------------

        self.api_key = (
            api_key
            or os.getenv(
                "BAIDU_SEARCH_API_KEY",
                "",
            )
        ).strip()

        # -----------------------------------------
        # Endpoint
        # -----------------------------------------

        self.api_url = (
            endpoint
            or self.DEFAULT_API_URL
        ).strip()

    def search(
        self,
        query: str,
        work=None,
    ):
        if not self.api_key:
            raise RuntimeError(
                "未配置百度搜索 API Key。"
                "请在 Settings → API 服务中配置，"
                "或设置环境变量 "
                "BAIDU_SEARCH_API_KEY。"
            )

        query = query.strip()

        if not query:
            return []

        # 百度接口查询长度保护
        query = query[:70]

        headers = {
            "Authorization":
                f"Bearer {self.api_key}",
            "Content-Type":
                "application/json",
        }

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ],
            "search_source":
                "baidu_search_v2",
            "resource_type_filter": [
                {
                    "type": "web",
                    "top_k": 20,
                }
            ],
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )

        except requests.RequestException as exc:
            raise RuntimeError(
                f"百度搜索网络请求失败：{exc}"
            ) from exc

        if response.status_code != 200:
            raise RuntimeError(
                "百度搜索 API 请求失败："
                f"HTTP "
                f"{response.status_code} "
                f"{response.text[:300]}"
            )

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "百度搜索 API 返回了无效 JSON。"
            ) from exc

        if data.get("code"):
            raise RuntimeError(
                "百度搜索 API 错误："
                f'{data.get("code")} '
                f'{data.get("message", "")}'
            )

        references = data.get(
            "references",
            [],
        )

        results = []

        for item in references:
            url = item.get(
                "url",
                "",
            ).strip()

            if not url:
                continue

            title = (
                item.get("title")
                or url
            ).strip()

            snippet = (
                item.get("content")
                or item.get("snippet")
                or item.get("abstract")
                or ""
            ).strip()

            domain = urlparse(
                url
            ).netloc

            results.append(
                {
                    "title": title,
                    "url": url,
                    "domain": domain,
                    "snippet": snippet,
                }
            )

        return results