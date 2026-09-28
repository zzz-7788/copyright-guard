"""Website allowlist parsing and matching, independent of the UI."""

import re
from urllib.parse import urlsplit


def website_host(value):
    value = value.strip()
    parts = urlsplit(value if "://" in value or value.startswith("//") else "//" + value)
    if parts.scheme and parts.scheme.lower() not in ("http", "https"):
        raise ValueError("仅支持 HTTP/HTTPS 网站")
    if parts.username is not None or parts.password is not None:
        raise ValueError("网址不能包含用户名或密码")
    _ = parts.port  # Validate port syntax.
    host = (parts.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
    labels = host.split(".")
    if len(host) > 253 or len(labels) < 2 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        raise ValueError("请输入完整域名，例如 example.com")
    return host


def parse_whitelist(text):
    domains = []
    for entry in re.split(r"[\s,，;；]+", text.strip()):
        if not entry:
            continue
        try:
            host = website_host(entry)
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f"无效网站：{entry}（{exc}）") from exc
        if host not in domains:
            domains.append(host)
    return tuple(domains)


class WebsiteFilter:
    def __init__(self, enabled=False, domains=()):
        self.enabled = enabled
        self.domains = tuple(domains)

    @classmethod
    def from_database(cls, db):
        enabled = db.get_setting("whitelist_enabled", "0") == "1"
        if not enabled:
            return cls()
        try:
            return cls(True, parse_whitelist(db.get_setting("whitelist", "")))
        except ValueError:
            return cls(True)  # Invalid enabled configuration must not allow everything.

    def allows(self, url):
        if not self.enabled:
            return True
        try:
            host = website_host(url)
        except (ValueError, UnicodeError):
            return False
        return any(host == domain or host.endswith("." + domain) for domain in self.domains)
