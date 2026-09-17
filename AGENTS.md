# Copyright Guard — Codex Project Instructions

## Goal
Build a free, open-source desktop assistant for authors:
Original work -> discovery/search -> suspected pages -> author review -> reporting task -> official reporting page.

## Stack
Python + PySide6 + SQLite.
Real search providers and Playwright-assisted reporting come after V0.1.

## Main navigation
1. 概览 / Overview
2. 搜索 / Search
3. 作品与资料 / Works & Materials
4. 举报 / Reports
5. 设置 / Settings

## Search sources
The UI must contain exactly:
必应 / Bing, 百度 / Baidu, 搜狗 / Sogou, 360, 夸克 / Quark, UC, QQ, DuckDuckGo.

V0.1 uses MockSearchProvider. Never present mock data as live search results.

## Terminology
Use neutral labels:
- Potential / 疑似页面
- Confirmed / 已确认
- Ignored / 已忽略
- Reported / 已举报

Do not make legal infringement determinations.

## Automation constraints
Future browser automation must:
- keep the author in control before final complaint submission;
- not bypass CAPTCHA, login/access controls, verification, or anti-bot systems;
- respect laws, website terms, and reasonable rate limits;
- pause for user action when authentication/verification is required.

## Engineering
Inspect existing code before changing it.
Keep QSS centralized.
Keep services independent from UI.
Preserve working functionality.
Run syntax/tests/application checks when possible.
Summarize changed files and limitations after edits.
