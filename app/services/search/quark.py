"""CleverSee web search provider using Quark-oriented GenericAdvanced sources."""

import os
import re
from html import unescape
from urllib.parse import urlsplit

import requests

from .base import SearchProvider
from app.utils.url_utils import normalize_url


DEFAULT_ENDPOINT = "https://cloud-iqs.aliyuncs.com/search/unified"
LEGACY_ENDPOINT = "iqs.cn-zhangjiakou.aliyuncs.com"


def _plain_text(value):
    if not value:
        return ""
    return unescape(re.sub(r"<[^>]+>", "", str(value))).strip()


def parse_iqs_results(items):
    results = []
    seen = set()
    for item in items or []:
        raw_url = str(item.get("link", "") or "").strip()
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
            "title": _plain_text(item.get("title", "")) or url,
            "url": url,
            "domain": parts.hostname.lower(),
            "snippet": _plain_text(
                item.get("snippet", "") or item.get("summary", "")
            )[:1000],
        })
        seen.add(url)
    return results


class QuarkSearchProvider(SearchProvider):
    """Call CleverSee UnifiedSearch with the Quark-oriented advanced engine."""

    name = "夸克信源（CleverSee）"
    provider_type = "quark_iqs"
    requires_api_key = True
    is_real = True
    credential_key = "cleversee_api_key"

    def __init__(self, api_key=None, endpoint=None):
        self.api_key = (
            api_key
            or os.getenv("CLEVERSEE_API_KEY", "")
            or os.getenv("ALIYUN_IQS_API_KEY", "")
        ).strip()
        configured_endpoint = (endpoint or "").strip()
        self.endpoint = (
            DEFAULT_ENDPOINT
            if not configured_endpoint or configured_endpoint == LEGACY_ENDPOINT
            else configured_endpoint
        )

    def search(self, query, work=None):
        query = query.strip()
        if not query:
            return []
        if len(query) > 500:
            raise ValueError("夸克信源搜索关键词不能超过 500 个字符。")
        if not self.api_key:
            raise RuntimeError(
                "未配置 CleverSee API Key。"
                "请在设置 → API 服务中添加“夸克信源（CleverSee）”，再绑定到夸克来源。"
            )

        payload = {
            "query": query,
            "engineType": "GenericAdvanced",
            "timeRange": "NoLimit",
            "contents": {
                "mainText": False,
                "markdownText": False,
                "richMainBody": False,
                "summary": False,
                "rerankScore": True,
            },
            "advancedParams": {"numResults": "50"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"CleverSee 搜索网络请求失败：{exc}") from exc

        if response.status_code not in (200, 201):
            raise RuntimeError(
                "CleverSee 搜索 API 请求失败："
                f"HTTP {response.status_code} {response.text[:300]}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("CleverSee 搜索 API 返回了无效 JSON。") from exc

        return parse_iqs_results(data.get("pageItems", []))
