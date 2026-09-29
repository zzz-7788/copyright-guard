"""Official Alibaba Cloud IQS web search provider backed by Quark search."""

import os
import re
from html import unescape
from urllib.parse import urlsplit

from .base import SearchProvider
from app.utils.url_utils import normalize_url


DEFAULT_ENDPOINT = "iqs.cn-zhangjiakou.aliyuncs.com"


def _plain_text(value):
    if not value:
        return ""
    return unescape(re.sub(r"<[^>]+>", "", str(value))).strip()


def _value(item, name, default=None):
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def parse_iqs_results(items):
    results = []
    seen = set()
    for item in items or []:
        raw_url = str(_value(item, "link", "") or "").strip()
        try:
            url = normalize_url(raw_url)
            parts = urlsplit(url)
        except ValueError:
            continue
        if parts.scheme not in ("http", "https") or not parts.hostname:
            continue
        if parts.username or parts.password or url in seen:
            continue
        results.append({
            "title": _plain_text(_value(item, "title", "")) or url,
            "url": url,
            "domain": parts.hostname.lower(),
            "snippet": _plain_text(
                _value(item, "snippet", "") or _value(item, "summary", "")
            )[:1000],
        })
        seen.add(url)
    return results


class QuarkSearchProvider(SearchProvider):
    """Call Alibaba Cloud Information Query Service UnifiedSearch API."""

    name = "夸克"
    provider_type = "quark_iqs"
    requires_api_key = True
    is_real = True
    credential_key = "aliyun_iqs_access_key"

    def __init__(self, access_key_id=None, access_key_secret=None, endpoint=None):
        self.access_key_id = (
            access_key_id or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
        ).strip()
        self.access_key_secret = (
            access_key_secret or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
        ).strip()
        self.endpoint = (endpoint or DEFAULT_ENDPOINT).strip()

    def search(self, query, work=None):
        query = query.strip()
        if not query:
            return []
        if len(query) > 500:
            raise ValueError("夸克 IQS 搜索关键词不能超过 500 个字符。")
        if not self.access_key_id or not self.access_key_secret:
            raise RuntimeError(
                "未配置夸克 IQS 的 AccessKey ID 和 AccessKey Secret。"
                "请在设置 → API 服务中添加“夸克 IQS 搜索”，再绑定到夸克来源。"
            )
        try:
            from alibabacloud_iqs20241111 import models
            from alibabacloud_iqs20241111.client import Client
            from alibabacloud_tea_openapi import models as open_api_models
        except ImportError as exc:
            raise RuntimeError(
                "缺少阿里云 IQS SDK，请重新安装 requirements.txt 或使用新版 EXE。"
            ) from exc

        try:
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
            )
            config.endpoint = self.endpoint
            client = Client(config)
            request = models.UnifiedSearchRequest(
                body=models.UnifiedSearchInput(
                    query=query,
                    engine_type="Generic",
                    time_range="NoLimit",
                    contents=models.RequestContents(
                    main_text=False,
                    markdown_text=False,
                    rich_main_body=False,
                    summary=False,
                    rerank_score=True,
                    ),
                    # IQS UnifiedSearch 没有传统页码参数；一次取满 50 条候选，
                    # 由搜索页排除可信/原创站点后保留前 20 条。
                    advanced_params={"numResults": "50"},
                )
            )
            response = client.unified_search(request)
            return parse_iqs_results(_value(response.body, "page_items", []))
        except Exception as exc:
            code = getattr(exc, "code", "")
            data = getattr(exc, "data", None) or {}
            message = data.get("message") if isinstance(data, dict) else ""
            detail = message or str(exc)
            if code:
                detail = f"{code}: {detail}"
            raise RuntimeError(f"夸克 IQS 搜索 API 请求失败：{detail}") from exc
