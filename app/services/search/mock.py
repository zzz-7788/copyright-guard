from urllib.parse import quote

from .base import SearchProvider


class MockSearchProvider(SearchProvider):
    name = "Mock"
    provider_type = "mock"
    requires_api_key = False
    is_real = False
    credential_key = None

    def search(self, query: str, work=None):
        title = (work or {}).get("title", "原创作品")
        encoded = quote(query[:40])

        domains = [
            "reader-demo.example",
            "novel-mirror.example",
            "text-index.example",
        ]

        return [
            {
                "title": f"{title} - 搜索示例结果 {i + 1}",
                "url": f"https://{domain}/search/{encoded}/{i + 1}",
                "domain": domain,
                "snippet": (
                    "V0.1 MockProvider 生成的演示结果，"
                    "不代表真实网页或侵权判断。"
                ),
            }
            for i, domain in enumerate(domains)
        ]