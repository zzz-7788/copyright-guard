"""Website exclusion-list parsing and matching, independent of the UI."""

import re
from urllib.parse import unquote, urlsplit


COMMON_DOMAIN_SUFFIXES = {
    "com", "net", "org", "cn", "gov", "edu", "fm", "me", "club",
    "io", "tv", "cc", "co", "info", "biz", "app", "xyz", "top",
}


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
    rules = []
    for entry in re.split(r"[\s,，;；]+", text.strip()):
        if not entry:
            continue
        rule = entry.strip().casefold()
        if "://" in rule or rule.startswith("//"):
            try:
                rule = website_host(rule)
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f"无效规则：{entry}（{exc}）") from exc
        elif any(char in rule for char in "*\x00\r\n") or len(rule) > 200:
            raise ValueError(f"无效规则：{entry}")
        else:
            # Keep complete domains normalized, while allowing entries such as
            # ``jjwxc``, ``/videos/`` and ``f?kw=`` as URL fragments.
            try:
                if "/" not in rule and "?" not in rule and "=" not in rule:
                    rule = website_host(rule)
            except (ValueError, UnicodeError):
                pass
        if rule not in rules:
            rules.append(rule)
    return tuple(rules)


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
            return cls(True)  # Invalid configuration excludes no valid domain.

    def allows(self, url):
        if not self.enabled:
            return True
        try:
            host = website_host(url)
        except (ValueError, UnicodeError):
            return False
        decoded_url = unquote(str(url)).casefold()
        for rule in self.domains:
            normalized_rule = rule.casefold()
            domain_rule = (
                "." in normalized_rule
                and "/" not in normalized_rule
                and "?" not in normalized_rule
                and "=" not in normalized_rule
            )
            complete_domain = normalized_rule.rsplit(".", 1)[-1] in COMMON_DOMAIN_SUFFIXES
            if domain_rule and (
                host == normalized_rule
                or host.endswith("." + normalized_rule)
                or (not complete_domain and host.startswith(normalized_rule + "."))
            ):
                return False
            if not domain_rule and normalized_rule in decoded_url:
                return False
        return True

    def select(self, results, limit=20):
        """Return up to ``limit`` non-excluded results and the excluded count."""
        kept = []
        excluded = 0
        for result in results or []:
            if not self.allows(result.get("url", "")):
                excluded += 1
            elif len(kept) < limit:
                kept.append(result)
        return kept, excluded
