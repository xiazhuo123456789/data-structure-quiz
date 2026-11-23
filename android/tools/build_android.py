#!/usr/bin/env python3
"""把桌面版单文件页面复制进 Android assets。

用法：
    python android/tools/build_android.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_HTML = PROJECT_ROOT / "app" / "index.html"
BANK_JSON = PROJECT_ROOT / "src" / "题库_数据结构1-5章.json"
ANDROID_ASSETS = PROJECT_ROOT / "android" / "app" / "src" / "main" / "assets"


def main() -> int:
    if not SOURCE_HTML.exists():
        raise SystemExit(f"找不到页面：{SOURCE_HTML}")
    if not BANK_JSON.exists():
        raise SystemExit(f"找不到题库：{BANK_JSON}")

    bank = json.loads(BANK_JSON.read_text(encoding="utf-8"))
    questions = bank.get("questions", [])
    if len(questions) != 155:
        raise SystemExit(f"题库题量异常：{len(questions)}，预期 155（125 章节题 + 30 随堂练习）")

    ANDROID_ASSETS.mkdir(parents=True, exist_ok=True)
    target = ANDROID_ASSETS / "index.html"
    shutil.copyfile(SOURCE_HTML, target)

    html = target.read_text(encoding="utf-8")
    for marker in ("dsq.bank.v1", "dsq.session.v1", "dsq.wrong.v1", "dsq.history.v1"):
        if marker not in html:
            raise SystemExit(f"页面缺少存储键：{marker}")
    if "https://github.com/xiazhuo123456789" not in html:
        raise SystemExit("页面缺少 GitHub 入口")

    data = target.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"已复制：{target}")
    print(f"大小：{len(data):,} 字节")
    print(f"SHA256：{sha}")
    print(f"题库：{len(questions)} 题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
