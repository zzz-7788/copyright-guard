import sqlite3
from pathlib import Path
from datetime import datetime
from app.utils.url_utils import normalize_url

class Database:
    def __init__(self, db_path=None):
        if db_path:
            self.path = Path(db_path)
        else:
            self.path = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "copyright_guard.db"
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.init_schema()
        self.migrate_schema()
        self.migrate_normalized_urls()
        self.seed()

    def connect(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    # =========================================================
    # Database schema
    # =========================================================

    def init_schema(self):
        with self.connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS works(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT DEFAULT '',
                    original_url TEXT DEFAULT '',
                    characters TEXT DEFAULT '',
                    aliases TEXT DEFAULT '',
                    keywords TEXT DEFAULT '',
                    rights_holder TEXT DEFAULT '',
                    contact TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    evidence TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
                -- =============================================
                -- V0.2: Reusable Work Materials
                -- =============================================

                CREATE TABLE IF NOT EXISTS work_materials(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    work_id INTEGER NOT NULL,

                    -- first_publish / authorization /
                    -- statement / contract / other
                    material_type TEXT NOT NULL DEFAULT 'other',

                    name TEXT NOT NULL,

                    file_path TEXT NOT NULL,

                    description TEXT DEFAULT '',

                    created_at TEXT NOT NULL,

                    FOREIGN KEY(work_id)
                        REFERENCES works(id)
                );

                CREATE TABLE IF NOT EXISTS search_results(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_id INTEGER,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    domain TEXT DEFAULT '',
                    snippet TEXT DEFAULT '',
                    sources TEXT DEFAULT '',
                    status TEXT DEFAULT 'potential',
                    found_at TEXT NOT NULL,

                    UNIQUE(work_id, url)
                );

                CREATE TABLE IF NOT EXISTS reports(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id INTEGER,
                    work_id INTEGER,
                    website TEXT DEFAULT '',
                    infringing_url TEXT DEFAULT '',
                    method TEXT DEFAULT 'manual',
                    status TEXT DEFAULT 'pending',
                    report_url TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    submitted_at TEXT DEFAULT ''
                );

                -- =============================================
                -- V0.2: Report Pool
                -- =============================================

                CREATE TABLE IF NOT EXISTS report_pool(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- 如果来自搜索结果，记录原 result_id。
                    -- 手动/批量导入时可以为空。
                    result_id INTEGER,

                    work_id INTEGER NOT NULL,

                    url TEXT NOT NULL,
                    domain TEXT DEFAULT '',

                    -- quark / baidu_search / baidu_netdisk /
                    -- wechat_official / sogou / other / unclassified
                    platform TEXT DEFAULT 'unclassified',

                    -- search / manual / import
                    source_type TEXT DEFAULT 'search',

                    -- pending / processing / submitted / closed
                    status TEXT DEFAULT 'pending',

                    created_at TEXT NOT NULL,

                    UNIQUE(work_id, url)
                );
                CREATE TABLE IF NOT EXISTS settings(
                    key TEXT PRIMARY KEY,
                    value TEXT DEFAULT ''
                );

                -- =============================================
                -- V0.2: API Services
                -- =============================================

                CREATE TABLE IF NOT EXISTS api_services(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,

                    -- Provider 类型
                    -- baidu / custom / future providers
                    provider_type TEXT NOT NULL DEFAULT 'custom',

                    api_key TEXT DEFAULT '',

                    endpoint TEXT DEFAULT '',

                    -- none / bearer / api_key
                    auth_type TEXT DEFAULT 'bearer',

                    enabled INTEGER NOT NULL DEFAULT 1,

                    created_at TEXT NOT NULL
                );

                -- =============================================
                -- V0.2: Search Sources
                -- =============================================

                CREATE TABLE IF NOT EXISTS search_sources(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL UNIQUE,

                    display_name TEXT DEFAULT '',

                    -- 绑定到哪个 API Service
                    api_service_id INTEGER,

                    -- 第三方 API 内部可能需要的来源标识
                    -- 例如 baidu / quark / bing
                    source_key TEXT DEFAULT '',

                    enabled INTEGER NOT NULL DEFAULT 1,

                    is_builtin INTEGER NOT NULL DEFAULT 0,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY(api_service_id)
                        REFERENCES api_services(id)
                );
                """
            )

    def migrate_schema(self):
        """
        数据库结构迁移。

        V0.2:
        search_results 从全局 URL 唯一：
            UNIQUE(url)

        改为作品内 URL 唯一：
            UNIQUE(work_id, url)
        """

        with self.connect() as con:
            indexes = con.execute(
                "PRAGMA index_list(search_results)"
            ).fetchall()

            needs_migration = False

            for index in indexes:
                index_name = index["name"]

                columns = con.execute(
                    f'PRAGMA index_info("{index_name}")'
                ).fetchall()

                column_names = [
                    column["name"]
                    for column in columns
                ]

                # 旧数据库：
                # url TEXT NOT NULL UNIQUE
                if column_names == ["url"]:
                    needs_migration = True
                    break

            if not needs_migration:
                return

            print(
                "[Database] Migrating search_results "
                "UNIQUE(url) -> UNIQUE(work_id, url)"
            )

            con.execute("PRAGMA foreign_keys=OFF")

            con.executescript(
                """
                BEGIN;

                ALTER TABLE search_results
                RENAME TO search_results_old;

                CREATE TABLE search_results(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_id INTEGER,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    domain TEXT DEFAULT '',
                    snippet TEXT DEFAULT '',
                    sources TEXT DEFAULT '',
                    status TEXT DEFAULT 'potential',
                    found_at TEXT NOT NULL,

                    UNIQUE(work_id, url)
                );

                INSERT INTO search_results(
                    id,
                    work_id,
                    title,
                    url,
                    domain,
                    snippet,
                    sources,
                    status,
                    found_at
                )
                SELECT
                    id,
                    work_id,
                    title,
                    url,
                    domain,
                    snippet,
                    sources,
                    status,
                    found_at
                FROM search_results_old;

                DROP TABLE search_results_old;

                COMMIT;
                """
            )

            con.execute("PRAGMA foreign_keys=ON")

            print(
                "[Database] Migration completed."
            )

    def migrate_normalized_urls(self):
        """
        将已有 search_results URL 安全迁移为规范化 URL。

        同一作品中，如果多个旧 URL 规范化后相同：
        - 保留最早记录的 ID
        - 合并 sources
        - 保留优先级更高的 status
        - 更新 reports.result_id
        - 重建 search_results，避免 UNIQUE 冲突

        migration 通过 settings 标记，只执行一次。
        """

        migration_key = "migration_normalized_urls_v1"

        status_priority = {
            "potential": 0,
            "ignored": 1,
            "confirmed": 2,
            "reported": 3,
        }

        with self.connect() as con:
            done = con.execute(
                """
                SELECT value
                FROM settings
                WHERE key=?
                """,
                (migration_key,),
            ).fetchone()

            if done and done["value"] == "1":
                return

            print(
                "[Database] Migrating existing URLs "
                "to normalized form..."
            )

            rows = con.execute(
                """
                SELECT *
                FROM search_results
                ORDER BY id ASC
                """
            ).fetchall()

            # -------------------------------------------------
            # 1. 在内存中完成 URL 规范化与重复合并
            # -------------------------------------------------

            grouped = {}
            old_to_keep = {}

            for row in rows:
                row = dict(row)

                normalized_url = normalize_url(
                    row["url"]
                )

                # 如果规范化失败，保留历史 URL，
                # 避免 migration 丢失已有数据。
                if not normalized_url:
                    normalized_url = row["url"]

                key = (
                    row["work_id"],
                    normalized_url,
                )

                if key not in grouped:
                    row["url"] = normalized_url

                    grouped[key] = {
                        "row": row,
                        "sources": set(
                            filter(
                                None,
                                row["sources"].split(" · "),
                            )
                        ),
                    }

                    old_to_keep[row["id"]] = row["id"]
                    continue

                # 已存在相同 normalized URL
                group = grouped[key]
                keep_row = group["row"]

                old_to_keep[row["id"]] = keep_row["id"]

                # 合并搜索来源
                group["sources"].update(
                    filter(
                        None,
                        row["sources"].split(" · "),
                    )
                )

                # 保留优先级更高的状态
                current_status = keep_row["status"]
                incoming_status = row["status"]

                if (
                    status_priority.get(
                        incoming_status,
                        0,
                    )
                    >
                    status_priority.get(
                        current_status,
                        0,
                    )
                ):
                    keep_row["status"] = incoming_status

            # -------------------------------------------------
            # 2. 整理最终记录
            # -------------------------------------------------

            final_rows = []

            for group in grouped.values():
                row = group["row"]

                row["sources"] = " · ".join(
                    sorted(group["sources"])
                )

                final_rows.append(row)

            # -------------------------------------------------
            # 3. 事务内重建 search_results
            # -------------------------------------------------

            try:
                con.execute("BEGIN")

                con.execute(
                    """
                    CREATE TABLE search_results_normalized(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        work_id INTEGER,
                        title TEXT NOT NULL,
                        url TEXT NOT NULL,
                        domain TEXT DEFAULT '',
                        snippet TEXT DEFAULT '',
                        sources TEXT DEFAULT '',
                        status TEXT DEFAULT 'potential',
                        found_at TEXT NOT NULL,

                        UNIQUE(work_id, url)
                    )
                    """
                )

                for row in final_rows:
                    con.execute(
                        """
                        INSERT INTO search_results_normalized
                        (
                            id,
                            work_id,
                            title,
                            url,
                            domain,
                            snippet,
                            sources,
                            status,
                            found_at
                        )
                        VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            row["id"],
                            row["work_id"],
                            row["title"],
                            row["url"],
                            row["domain"],
                            row["snippet"],
                            row["sources"],
                            row["status"],
                            row["found_at"],
                        ),
                    )

                # ---------------------------------------------
                # 4. 举报记录重新绑定到保留的 result ID
                # ---------------------------------------------

                for old_id, keep_id in old_to_keep.items():
                    if old_id == keep_id:
                        continue

                    con.execute(
                        """
                        UPDATE reports
                        SET result_id=?
                        WHERE result_id=?
                        """,
                        (
                            keep_id,
                            old_id,
                        ),
                    )

                # ---------------------------------------------
                # 5. 用新表替换旧表
                # ---------------------------------------------

                con.execute(
                    "DROP TABLE search_results"
                )

                con.execute(
                    """
                    ALTER TABLE search_results_normalized
                    RENAME TO search_results
                    """
                )

                # ---------------------------------------------
                # 6. 写入 migration 标记
                # ---------------------------------------------

                con.execute(
                    """
                    INSERT INTO settings(key, value)
                    VALUES(?, '1')
                    ON CONFLICT(key)
                    DO UPDATE SET
                        value='1'
                    """,
                    (migration_key,),
                )

                con.commit()

            except Exception:
                con.rollback()
                raise

            print(
                "[Database] URL normalization "
                "migration completed."
            )
    # =========================================================
    # Seed
    # =========================================================

    def seed(self):
        with self.connect() as con:

            # -------------------------------------------------
            # Demo work
            # -------------------------------------------------

            if (
                con.execute(
                    "SELECT COUNT(*) FROM works"
                ).fetchone()[0]
                == 0
            ):
                con.execute(
                    """
                    INSERT INTO works
                    (
                        title,
                        author,
                        original_url,
                        characters,
                        aliases,
                        keywords,
                        rights_holder,
                        contact,
                        description,
                        evidence,
                        created_at
                    )
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        "我的小说 A",
                        "作者名",
                        "https://example.org/original",
                        "林舟, 苏晚",
                        "小舟",
                        "原创小说, 主要角色名",
                        "作者名",
                        "author@example.com",
                        "原创网络小说示例作品",
                        "",
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),
                    ),
                )

            # -------------------------------------------------
            # Default search sources
            # -------------------------------------------------

            default_sources = [
                ("必应", "Bing", "bing"),
                ("百度", "Baidu", "baidu"),
                ("搜狗", "Sogou", "sogou"),
                ("360", "360 Search", "360"),
                ("夸克", "Quark", "quark"),
                ("UC", "UC", "uc"),
                ("QQ", "QQ", "qq"),
                (
                    "DuckDuckGo",
                    "DuckDuckGo",
                    "duckduckgo",
                ),
            ]

            for name, display_name, source_key in default_sources:
                con.execute(
                    """
                    INSERT OR IGNORE INTO search_sources
                    (
                        name,
                        display_name,
                        source_key,
                        enabled,
                        is_builtin,
                        created_at
                    )
                    VALUES(?,?,?,?,?,?)
                    """,
                    (
                        name,
                        display_name,
                        source_key,
                        1,
                        1,
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),
                    ),
                )

    # =========================================================
    # Works
    # =========================================================

    def list_works(self):
        with self.connect() as con:
            return [
                dict(r)
                for r in con.execute(
                    "SELECT * FROM works ORDER BY id DESC"
                )
            ]

    def get_work(self, work_id):
        with self.connect() as con:
            r = con.execute(
                "SELECT * FROM works WHERE id=?",
                (work_id,),
            ).fetchone()

            return dict(r) if r else None

    def save_work(self, data):
        fields = [
            "title",
            "author",
            "original_url",
            "characters",
            "aliases",
            "keywords",
            "rights_holder",
            "contact",
            "description",
            "evidence",
        ]

        with self.connect() as con:
            if data.get("id"):
                con.execute(
                    "UPDATE works SET "
                    + ",".join(
                        f"{f}=?" for f in fields
                    )
                    + " WHERE id=?",
                    [data.get(f, "") for f in fields]
                    + [data["id"]],
                )

                return data["id"]

            sql = (
                "INSERT INTO works("
                + ",".join(fields)
                + ",created_at) VALUES("
                + ",".join("?" for _ in fields)
                + ",?)"
            )

            cur = con.execute(
                sql,
                [data.get(f, "") for f in fields]
                + [
                    datetime.now().isoformat(
                        timespec="seconds"
                    )
                ],
            )

            return cur.lastrowid

    # =========================================================
    # Work Materials
    # =========================================================

    def add_work_material(
        self,
        work_id,
        material_type,
        name,
        file_path,
        description="",
    ):
        """
        为作品添加一份可复用的权属证明材料。
        """

        if not work_id:
            raise ValueError(
                "work_id is required."
            )

        if not name.strip():
            raise ValueError(
                "Material name is required."
            )

        if not file_path.strip():
            raise ValueError(
                "Material file path is required."
            )

        with self.connect() as con:
            cur = con.execute(
                """
                INSERT INTO work_materials
                (
                    work_id,
                    material_type,
                    name,
                    file_path,
                    description,
                    created_at
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    work_id,
                    material_type or "other",
                    name.strip(),
                    file_path.strip(),
                    description.strip(),
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

            return cur.lastrowid

    def list_work_materials(
        self,
        work_id,
        material_type=None,
    ):
        """
        获取某一本作品已经保存的材料。
        """

        sql = """
            SELECT *
            FROM work_materials
            WHERE work_id=?
        """

        params = [work_id]

        if material_type:
            sql += """
                AND material_type=?
            """

            params.append(
                material_type
            )

        sql += """
            ORDER BY
                material_type ASC,
                id ASC
        """

        with self.connect() as con:
            return [
                dict(row)
                for row in con.execute(
                    sql,
                    params,
                )
            ]

    def update_work_material(
        self,
        material_id,
        data,
    ):
        """
        修改一份已有作品材料。
        """

        with self.connect() as con:
            con.execute(
                """
                UPDATE work_materials
                SET
                    material_type=?,
                    name=?,
                    file_path=?,
                    description=?
                WHERE id=?
                """,
                (
                    data.get(
                        "material_type",
                        "other",
                    ),
                    data.get(
                        "name",
                        "",
                    ).strip(),
                    data.get(
                        "file_path",
                        "",
                    ).strip(),
                    data.get(
                        "description",
                        "",
                    ).strip(),
                    material_id,
                ),
            )

    def delete_work_material(
        self,
        material_id,
    ):
        """
        删除一份作品材料记录。

        这里只删除数据库记录，
        不删除用户电脑上的原始文件。
        """

        with self.connect() as con:
            con.execute(
                """
                DELETE FROM work_materials
                WHERE id=?
                """,
                (material_id,),
            )
    # =========================================================
    # Search Results
    # =========================================================

    def add_result(self, result):
        normalized_url = normalize_url(
            result.get("url", "")
        )

        if not normalized_url:
            raise ValueError(
                "Search result URL is empty."
            )

        # 不直接修改 Provider 返回的原始 dict
        result = dict(result)
        result["url"] = normalized_url

        with self.connect() as con:
            old = con.execute(
                """
                SELECT *
                FROM search_results
                WHERE work_id=? AND url=?
                """,
                (
                    result.get("work_id"),
                    result["url"],
                ),
            ).fetchone()

            if old:
                sources = set(
                    filter(
                        None,
                        old["sources"].split(" · "),
                    )
                )

                sources.update(
                    result.get("sources", [])
                )

                con.execute(
                    """
                    UPDATE search_results
                    SET sources=?
                    WHERE id=?
                    """,
                    (
                        " · ".join(
                            sorted(sources)
                        ),
                        old["id"],
                    ),
                )

                return old["id"]

            cur = con.execute(
                """
                INSERT INTO search_results
                (
                    work_id,
                    title,
                    url,
                    domain,
                    snippet,
                    sources,
                    status,
                    found_at
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    result.get("work_id"),
                    result["title"],
                    result["url"],
                    result.get("domain", ""),
                    result.get("snippet", ""),
                    " · ".join(
                        result.get("sources", [])
                    ),
                    result.get(
                        "status",
                        "potential",
                    ),
                    result.get(
                        "found_at",
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    ),
                ),
            )

            return cur.lastrowid

    def list_results(self, work_id=None):
        with self.connect() as con:
            if work_id:
                rows = con.execute(
                    """
                    SELECT *
                    FROM search_results
                    WHERE work_id=?
                    ORDER BY id DESC
                    """,
                    (work_id,),
                )
            else:
                rows = con.execute(
                    """
                    SELECT *
                    FROM search_results
                    ORDER BY id DESC
                    """
                )

            return [dict(r) for r in rows]

    def update_result_status(
        self,
        result_id,
        status,
    ):
        with self.connect() as con:
            con.execute(
                """
                UPDATE search_results
                SET status=?
                WHERE id=?
                """,
                (status, result_id),
            )

    def delete_result(self, result_id):
        with self.connect() as con:
            con.execute(
                """
                DELETE FROM search_results
                WHERE id=?
                """,
                (result_id,),
            )

    # =========================================================
    # Reports
    # =========================================================

    def create_report_from_result(
        self,
        result_id,
    ):
        with self.connect() as con:
            r = con.execute(
                """
                SELECT *
                FROM search_results
                WHERE id=?
                """,
                (result_id,),
            ).fetchone()

            if not r:
                return

            exists = con.execute(
                """
                SELECT id
                FROM reports
                WHERE result_id=?
                """,
                (result_id,),
            ).fetchone()

            if not exists:
                con.execute(
                    """
                    INSERT INTO reports
                    (
                        result_id,
                        work_id,
                        website,
                        infringing_url,
                        method,
                        status,
                        created_at
                    )
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        r["id"],
                        r["work_id"],
                        r["domain"],
                        r["url"],
                        "manual",
                        "pending",
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),
                    ),
                )

            con.execute(
                """
                UPDATE search_results
                SET status='reported'
                WHERE id=?
                """,
                (result_id,),
            )

    def list_reports(self):
        with self.connect() as con:
            return [
                dict(r)
                for r in con.execute(
                    """
                    SELECT
                        reports.*,
                        works.title AS work_title
                    FROM reports
                    LEFT JOIN works
                        ON works.id=reports.work_id
                    ORDER BY reports.id DESC
                    """
                )
            ]

    # =========================================================
    # Report Pool
    # =========================================================
    def detect_report_platform(
        self,
        result,
    ):
        """
        自动判断举报池中的目标平台。

        优先级：
        1. URL / domain 明确的平台
        2. 搜索来源提供的平台上下文
        3. 无法可靠判断 -> unclassified
        """

        if not result:
            return "unclassified"

        if not isinstance(result, dict):
            result = dict(result)

        url = (
            result.get("url", "")
            or ""
        ).lower()

        domain = (
            result.get("domain", "")
            or ""
        ).lower()

        sources = (
            result.get("sources", "")
            or ""
        )

        # =============================================
        # 1. URL / domain 明确识别
        # =============================================

        # 微信公众号
        if (
            domain == "mp.weixin.qq.com"
            or "mp.weixin.qq.com" in url
        ):
            return "wechat_official"

        # 百度网盘
        if (
            domain == "pan.baidu.com"
            or "pan.baidu.com" in url
        ):
            return "baidu_netdisk"

        # 百度自身页面
        if (
            domain == "baidu.com"
            or domain.endswith(".baidu.com")
        ):
            return "baidu_search"

        # =============================================
        # 2. 搜索来源辅助判断
        # =============================================

        source_names = {
            item.strip().lower()
            for item in sources.split(" · ")
            if item.strip()
        }

        if (
            "夸克" in source_names
            or "quark" in source_names
        ):
            return "quark"

        if (
            "搜狗" in source_names
            or "sogou" in source_names
        ):
            return "sogou"

        # =============================================
        # 3. 无法可靠判断
        # =============================================

        return "unclassified"
    
    def add_to_report_pool(
        self,
        work_id,
        url,
        result_id=None,
        domain="",
        platform="unclassified",
        source_type="manual",
    ):
        """
        向举报池加入一条侵权链接。

        同一作品下相同 URL 只保留一条。
        """

        normalized_url = normalize_url(url)

        if not normalized_url:
            raise ValueError(
                "Report pool URL is empty."
            )

        with self.connect() as con:
            old = con.execute(
                """
                SELECT *
                FROM report_pool
                WHERE work_id=? AND url=?
                """,
                (
                    work_id,
                    normalized_url,
                ),
            ).fetchone()

            if old:
                # 如果旧记录仍然是未分类，
                # 而这次已经识别出了明确平台，
                # 自动补全平台信息。
                if (
                    old["platform"]
                    == "unclassified"
                    and platform
                    and platform
                    != "unclassified"
                ):
                    con.execute(
                        """
                        UPDATE report_pool
                        SET platform=?
                        WHERE id=?
                        """,
                        (
                            platform,
                            old["id"],
                        ),
                    )

                return old["id"]

            cur = con.execute(
                """
                INSERT INTO report_pool
                (
                    result_id,
                    work_id,
                    url,
                    domain,
                    platform,
                    source_type,
                    status,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    result_id,
                    work_id,
                    normalized_url,
                    domain,
                    platform or "unclassified",
                    source_type,
                    "pending",
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

            return cur.lastrowid

    def add_result_to_report_pool(
        self,
        result_id,
        platform=None,
    ):
        """
        将一条 Search Result 加入举报池。

        platform:
        - None: 自动识别
        - 指定值: 使用调用方明确指定的平台
        """

        with self.connect() as con:
            result = con.execute(
                """
                SELECT *
                FROM search_results
                WHERE id=?
                """,
                (result_id,),
            ).fetchone()

        if not result:
            return None

        result = dict(result)

        # 调用方没有明确指定平台时，
        # 根据搜索结果上下文自动判断。
        if platform is None:
            platform = (
                self.detect_report_platform(
                    result
                )
            )

        return self.add_to_report_pool(
            work_id=result["work_id"],
            url=result["url"],
            result_id=result["id"],
            domain=result["domain"],
            platform=platform,
            source_type="search",
        )

    def add_results_to_report_pool(
        self,
        result_ids,
        platform=None,
    ):
        """
        批量将 Search Results 加入举报池。

        platform:
        - None: 每条结果分别自动识别
        - 指定值: 全部使用指定平台

        返回：
        {
            "added": [...],
            "failed": [...]
        }
        """

        added = []
        failed = []

        for result_id in result_ids:
            try:
                pool_id = (
                    self.add_result_to_report_pool(
                        result_id,
                        platform=platform,
                    )
                )

                if pool_id is not None:
                    added.append(
                        pool_id
                    )

            except Exception as exc:
                failed.append(
                    {
                        "result_id": result_id,
                        "error": str(exc),
                    }
                )

        return {
            "added": added,
            "failed": failed,
        }

    def list_report_pool(
        self,
        work_id=None,
        platform=None,
        status=None,
    ):
        """
        获取举报池。

        默认按照：
        platform -> created_at

        排序，方便 Reports 页面直接按平台分组。
        """

        sql = """
            SELECT
                report_pool.*,
                works.title AS work_title
            FROM report_pool
            LEFT JOIN works
                ON works.id=report_pool.work_id
            WHERE 1=1
        """

        params = []

        if work_id is not None:
            sql += """
                AND report_pool.work_id=?
            """
            params.append(work_id)

        if platform:
            sql += """
                AND report_pool.platform=?
            """
            params.append(platform)

        if status:
            sql += """
                AND report_pool.status=?
            """
            params.append(status)

        sql += """
            ORDER BY
                report_pool.platform ASC,
                report_pool.created_at DESC
        """

        with self.connect() as con:
            return [
                dict(row)
                for row in con.execute(
                    sql,
                    params,
                )
            ]

    def update_report_pool_platform(
        self,
        pool_id,
        platform,
    ):
        """
        修改一条举报池记录所属平台。
        """

        with self.connect() as con:
            con.execute(
                """
                UPDATE report_pool
                SET platform=?
                WHERE id=?
                """,
                (
                    platform or "unclassified",
                    pool_id,
                ),
            )

    def update_report_pool_status(
        self,
        pool_id,
        status,
    ):
        with self.connect() as con:
            con.execute(
                """
                UPDATE report_pool
                SET status=?
                WHERE id=?
                """,
                (
                    status,
                    pool_id,
                ),
            )

    def delete_report_pool_item(
        self,
        pool_id,
    ):
        with self.connect() as con:
            con.execute(
                """
                DELETE FROM report_pool
                WHERE id=?
                """,
                (pool_id,),
            )

    # =========================================================
    # Statistics
    # =========================================================

    def stats(self):
        with self.connect() as con:
            return (
                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM search_results
                    """
                ).fetchone()[0],

                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM search_results
                    WHERE status='potential'
                    """
                ).fetchone()[0],

                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM search_results
                    WHERE status IN (
                        'confirmed',
                        'ignored',
                        'reported'
                    )
                    """
                ).fetchone()[0],

                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM reports
                    """
                ).fetchone()[0],
            )

    # =========================================================
    # General Settings
    # =========================================================

    def set_setting(
        self,
        key,
        value,
    ):
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO settings(key,value)
                VALUES(?,?)
                ON CONFLICT(key)
                DO UPDATE SET
                    value=excluded.value
                """,
                (key, value),
            )

    def get_setting(
        self,
        key,
        default="",
    ):
        with self.connect() as con:
            r = con.execute(
                """
                SELECT value
                FROM settings
                WHERE key=?
                """,
                (key,),
            ).fetchone()

            return r["value"] if r else default

    # =========================================================
    # API Services
    # =========================================================

    def list_api_services(self):
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT *
                FROM api_services
                ORDER BY id ASC
                """
            )

            return [dict(r) for r in rows]

    def get_api_service(
        self,
        service_id,
    ):
        with self.connect() as con:
            r = con.execute(
                """
                SELECT *
                FROM api_services
                WHERE id=?
                """,
                (service_id,),
            ).fetchone()

            return dict(r) if r else None

    def add_api_service(
        self,
        data,
    ):
        with self.connect() as con:
            cur = con.execute(
                """
                INSERT INTO api_services
                (
                    name,
                    provider_type,
                    api_key,
                    endpoint,
                    auth_type,
                    enabled,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    data.get(
                        "name",
                        "API Service",
                    ),
                    data.get(
                        "provider_type",
                        "custom",
                    ),
                    data.get(
                        "api_key",
                        "",
                    ),
                    data.get(
                        "endpoint",
                        "",
                    ),
                    data.get(
                        "auth_type",
                        "bearer",
                    ),
                    1 if data.get(
                        "enabled",
                        True,
                    ) else 0,
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

            return cur.lastrowid

    def update_api_service(
        self,
        service_id,
        data,
    ):
        with self.connect() as con:
            con.execute(
                """
                UPDATE api_services
                SET
                    name=?,
                    provider_type=?,
                    api_key=?,
                    endpoint=?,
                    auth_type=?,
                    enabled=?
                WHERE id=?
                """,
                (
                    data.get("name", ""),
                    data.get(
                        "provider_type",
                        "custom",
                    ),
                    data.get(
                        "api_key",
                        "",
                    ),
                    data.get(
                        "endpoint",
                        "",
                    ),
                    data.get(
                        "auth_type",
                        "bearer",
                    ),
                    1 if data.get(
                        "enabled",
                        True,
                    ) else 0,
                    service_id,
                ),
            )

    def delete_api_service(
        self,
        service_id,
    ):
        with self.connect() as con:

            # 先解除搜索来源绑定
            con.execute(
                """
                UPDATE search_sources
                SET api_service_id=NULL
                WHERE api_service_id=?
                """,
                (service_id,),
            )

            con.execute(
                """
                DELETE FROM api_services
                WHERE id=?
                """,
                (service_id,),
            )

    # =========================================================
    # Search Sources
    # =========================================================

    def list_search_sources(
        self,
        enabled_only=False,
    ):
        with self.connect() as con:

            sql = """
                SELECT
                    search_sources.*,
                    api_services.name
                        AS api_service_name,
                    api_services.provider_type
                        AS provider_type
                FROM search_sources
                LEFT JOIN api_services
                    ON api_services.id
                    = search_sources.api_service_id
            """

            if enabled_only:
                sql += """
                    WHERE search_sources.enabled=1
                """

            sql += """
                ORDER BY
                    search_sources.is_builtin DESC,
                    search_sources.id ASC
            """

            return [
                dict(r)
                for r in con.execute(sql)
            ]

    def get_search_source(
        self,
        source_id,
    ):
        with self.connect() as con:
            r = con.execute(
                """
                SELECT *
                FROM search_sources
                WHERE id=?
                """,
                (source_id,),
            ).fetchone()

            return dict(r) if r else None

    def add_search_source(
        self,
        data,
    ):
        with self.connect() as con:
            cur = con.execute(
                """
                INSERT INTO search_sources
                (
                    name,
                    display_name,
                    api_service_id,
                    source_key,
                    enabled,
                    is_builtin,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    data["name"],
                    data.get(
                        "display_name",
                        "",
                    ),
                    data.get(
                        "api_service_id",
                    ),
                    data.get(
                        "source_key",
                        "",
                    ),
                    1 if data.get(
                        "enabled",
                        True,
                    ) else 0,
                    0,
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
                ),
            )

            return cur.lastrowid

    def update_search_source(
        self,
        source_id,
        data,
    ):
        with self.connect() as con:
            con.execute(
                """
                UPDATE search_sources
                SET
                    name=?,
                    display_name=?,
                    api_service_id=?,
                    source_key=?,
                    enabled=?
                WHERE id=?
                """,
                (
                    data.get("name", ""),
                    data.get(
                        "display_name",
                        "",
                    ),
                    data.get(
                        "api_service_id",
                    ),
                    data.get(
                        "source_key",
                        "",
                    ),
                    1 if data.get(
                        "enabled",
                        True,
                    ) else 0,
                    source_id,
                ),
            )

    def delete_search_source(
        self,
        source_id,
    ):
        with self.connect() as con:
            source = con.execute(
                """
                SELECT is_builtin
                FROM search_sources
                WHERE id=?
                """,
                (source_id,),
            ).fetchone()

            if not source:
                return False

            # 默认 8 个搜索来源不允许删除
            if source["is_builtin"]:
                return False

            con.execute(
                """
                DELETE FROM search_sources
                WHERE id=?
                """,
                (source_id,),
            )

            return True

    def bind_search_source(
        self,
        source_id,
        api_service_id,
    ):
        with self.connect() as con:
            con.execute(
                """
                UPDATE search_sources
                SET api_service_id=?
                WHERE id=?
                """,
                (
                    api_service_id,
                    source_id,
                ),
            )