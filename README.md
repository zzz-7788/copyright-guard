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

其中百度已经接入真实搜索服务，其他来源目前仍处于适配阶段。

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

- 百度已经接入真实搜索服务，其他预置搜索来源尚未全部接入真实搜索服务
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
