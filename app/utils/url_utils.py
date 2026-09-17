from urllib.parse import (
    urlsplit,
    urlunsplit,
    parse_qsl,
    urlencode,
)


# 常见追踪参数。
# 这些参数通常不会改变页面实际内容。
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "yclid",
    "_ga",
    "_gl",
    "mc_cid",
    "mc_eid",
}


def is_tracking_param(name):
    """
    判断 query 参数是否属于常见追踪参数。
    """

    name = name.lower()

    # Google Analytics / 广告常见参数
    if name.startswith("utm_"):
        return True

    return name in TRACKING_PARAMS


def normalize_url(url):
    """
    对 URL 进行保守规范化。

    规则：
    1. 去除首尾空格
    2. scheme / hostname 转为小写
    3. 删除 fragment (#...)
    4. 删除常见追踪参数
    5. 保留可能影响页面内容的 query 参数
    6. 去除非根路径末尾的 /
    7. 去除默认端口 :80 / :443

    不做：
    - 不强制 http -> https
    - 不删除所有 query 参数
    - 不改变实际页面路径
    """

    if not url:
        return ""

    url = url.strip()

    try:
        parts = urlsplit(url)
    except ValueError:
        return url

    scheme = parts.scheme.lower()

    hostname = (
        parts.hostname.lower()
        if parts.hostname
        else ""
    )

    # ---------------------------------------------
    # Port
    # ---------------------------------------------

    try:
        port = parts.port
    except ValueError:
        port = None

    if (
        (scheme == "http" and port == 80)
        or
        (scheme == "https" and port == 443)
    ):
        port = None

    # ---------------------------------------------
    # Netloc
    # ---------------------------------------------

    netloc = hostname

    if port:
        netloc = f"{hostname}:{port}"

    # 极少数 URL 可能包含用户名密码。
    # 搜索结果一般不会出现，但这里尽量保留。
    if parts.username:
        userinfo = parts.username

        if parts.password:
            userinfo += f":{parts.password}"

        netloc = f"{userinfo}@{netloc}"

    # ---------------------------------------------
    # Path
    # ---------------------------------------------

    path = parts.path or "/"

    if path != "/":
        path = path.rstrip("/")

    # ---------------------------------------------
    # Query
    # ---------------------------------------------

    query_items = parse_qsl(
        parts.query,
        keep_blank_values=True,
    )

    filtered_query = [
        (key, value)
        for key, value in query_items
        if not is_tracking_param(key)
    ]

    query = urlencode(
        filtered_query,
        doseq=True,
    )

    # ---------------------------------------------
    # Fragment
    # ---------------------------------------------

    fragment = ""

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            query,
            fragment,
        )
    )