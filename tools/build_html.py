#!/usr/bin/env python3
"""把题库 JSON 注入 HTML 模板，生成 app/index.html。

用法：
    python tools/build_html.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "app.template.html"
BANK = ROOT / "src" / "题库_数据结构1-5章.json"
OUTPUT = ROOT / "app" / "index.html"
PLACEHOLDER = "/*__BANK__*/ null"


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"模板里找不到占位符：{PLACEHOLDER}")

    bank = json.loads(BANK.read_text(encoding="utf-8"))
    questions = bank.get("questions", [])
    print(f"题库：{len(questions)} 题")

    html = template.replace(
        PLACEHOLDER,
        json.dumps(bank, ensure_ascii=False, separators=(",", ":")),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8", newline="\n")
    print(f"已生成：{OUTPUT}（{OUTPUT.stat().st_size} 字节）")


if __name__ == "__main__":
    main()
