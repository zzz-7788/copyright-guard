# Copyright Guard V0.2

Copyright Guard 是一个面向文字创作者的桌面工具，用于搜索、收集和导出互联网上的疑似盗文页面。

> 一键搜索、整理并导出疑似盗文链接。

Copyright Guard 只帮助用户发现和整理可能存在问题的页面，不对页面是否构成侵权作出法律判断。

## 主要功能

### 搜索疑似页面

- 根据作品信息生成和管理搜索关键词
- 支持多个搜索来源
- 百度搜索已接入真实搜索 API
- 搜索任务支持并发执行
- 自动保存和去重搜索结果
- 支持手动添加疑似页面 URL
- 支持结果筛选和状态管理

当前预置搜索来源：

- Bing
- 百度
- 搜狗
- 360
- 夸克
- UC
- QQ
- DuckDuckGo

其中百度已接入真实搜索 API，夸克已接入阿里云 IQS 官方 API，其他来源仍使用明确标记的模拟结果。

### 作品与资料

可以保存：

- 作品名称
- 作者
- 原创链接
- 作品相关信息
- 可选的权属或证明材料

这些信息保存在本机 SQLite 数据库中。

### 已收集 / 举报池

搜索结果可以加入举报池统一管理。

Copyright Guard 会根据页面域名和搜索来源尝试进行平台分类，用户也可以手动修改分类。

当前版本主要用于：

- 集中查看已收集的疑似页面
- 按平台整理页面
- 打开原页面进行人工确认
- 移除不需要的页面
- 导出整理结果

### Excel 导出

举报池中的页面可以一键导出为 `.xlsx` 文件。

导出内容包括：

- 作品
- 原创链接
- 疑似页面链接
- 页面网站
- 平台
- 状态
- 收集时间

每个疑似页面占一行，方便后续保存、整理或用于投诉材料准备。

## 数据与隐私

Copyright Guard 的用户数据保存在本机。

源码开发模式默认数据库：

```text
data/copyright_guard.db
```

Windows 打包版本默认数据库：

```text
%LOCALAPPDATA%\CopyrightGuard\copyright_guard.db
```

数据库不会被打包进发布的 EXE。

API Key 也不会硬编码或随 EXE 分发。使用需要 API Key 的搜索服务时，需要用户自行配置相应凭据。

请不要将包含个人 API Key、作品资料或其他私人信息的数据库文件公开发布。

## Windows 版本

V0.2 可以使用 PyInstaller 打包为 Windows 单文件程序：

```text
CopyrightGuard.exe
```

普通用户无需安装 Python、Conda 或项目依赖，直接运行 EXE 即可。

首次运行时，程序会自动创建本地数据库。

## 从源码运行

推荐使用 Python 3.11。

```bash
pip install -r requirements.txt
python main.py
```

项目当前主要依赖：

- PySide6
- requests
- openpyxl

## 当前技术栈

- Python
- PySide6
- SQLite
- requests
- openpyxl
- PyInstaller（Windows 打包）

## 当前限制

Copyright Guard V0.2 仍处于早期版本。

当前需要注意：

- 百度已接入真实搜索 API，夸克已接入阿里云 IQS 官方 API，其他预置来源尚未接入真实搜索
- 搜索结果仅代表可能相关的页面，不代表已经确认侵权
- 软件不会绕过 CAPTCHA、登录、身份验证或网站访问限制
- 当前版本不以自动提交版权投诉作为主要功能
- 最终是否构成侵权以及是否进行投诉，应由用户自行核实和决定

## 项目结构

```text
copyright_guard/
├── main.py
├── app/
│   ├── core/
│   ├── services/
│   │   ├── search/
│   │   └── reporting/
│   ├── ui/
│   ├── utils/
│   └── resources/
├── data/
├── requirements.txt
├── README.md
└── AGENTS.md
```

## Status

**V0.2 — Windows desktop prototype**

当前核心流程：

```text
添加作品
  ↓
搜索疑似盗文
  ↓
勾选需要的结果
  ↓
加入举报池
  ↓
查看已收集页面
  ↓
导出 Excel
```

### 网站排除名单

在「设置 → 网站」填写排除规则（每行一个，或用中英文逗号、分号分隔），
勾选「启用排除名单」并保存。也可以粘贴完整 HTTP/HTTPS 网址，保存时提取域名。
例如 `example.com` 匹配自身以及 `www.example.com`，不匹配 `otherexample.com`。
填写 `www.example.com` 则只匹配该域名及其下级子域名。
也可以直接填写 `jjwxc`、`/videos/`、`f?kw=` 等关键词、路径或查询参数片段；
这类规则只要出现在结果网址中就会匹配，因此 `news`、`game` 等短词可能排除较多结果。

默认关闭；启用时至少需要一个有效网站。新搜索结果会跳过匹配的网站，适合排除百度百科、
晋江等可信或原创发布站点。已有搜索结果（含手动添加）仅在搜索页隐藏，关闭后可恢复显示，举报池不受影响。
排除名单只按返回链接的域名筛选，不解析跳转链接，也不判断页面内容是否相关。

### 多轮搜索结果

搜索页默认只显示“疑似页面”。同一作品再次开始搜索时，上一批尚未加入举报池的结果会自动标记为“已忽略”；
已经加入举报池的结果和其他作品的结果不会被修改。需要复查旧结果时，可将状态筛选切换为“已忽略”或“全部”。

### 夸克信源（CleverSee）API 搜索

夸克来源使用阿里云 CleverSee/IQS 的 `GenericAdvanced` 联网搜索接口，不抓取夸克网页。

1. 在阿里云 CleverSee/IQS 控制台开通联网搜索，并创建 API Key。
2. 在「设置 → API 服务」添加服务，Provider 选择 `Quark Source (CleverSee) API`。
3. 只在 API Key 中填写控制台生成的密钥，API Secret 留空。Endpoint 留空时使用
   `https://cloud-iqs.aliyuncs.com/search/unified`，保存后可点击「测试」。
4. 在「设置 → 搜索来源」配置“夸克”，绑定刚创建的 API 服务并启用。
5. 在「搜索」勾选夸克后搜索。结果会先经过网站排除名单，再保存到结果列表。

夸克与百度采用相同的操作流程：点击“开始搜索”后调用 API，返回结果直接显示在下方疑似页面列表中。

当前使用 `GenericAdvanced` 引擎，每个关键词请求约 50 条候选结果，排除名单域名后最多保留 20 条；
不请求网页正文和增强摘要。实际可用额度、计费和限流由阿里云 CleverSee 服务决定。
API Key 当前保存在本机 SQLite，尚未加密，请勿上传数据库文件。
