#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把《数据结构（C语言版）第1-5章习题册》一类的 Word 习题册转换成答题系统可导入的 JSON 题库。
用法：
    python docx转题库.py 习题册.docx -o 题库.json
依赖：pip install python-docx
"""
import argparse
import json
import re
import sys

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

SECTION_TYPES = {
    "选择题": "choice",
    "填空题": "blank",
    "判断题": "judge",
    "简答与计算分析题": "short",
    "算法设计题": "algo",
}

Q_RE = re.compile(r"^(\d+)\s*\.\s*(\d+)\s*[.、．]?\s*(.*)$")
OPT_RE = re.compile(r"^([A-H])[\.、．]\s*(.*)$")
BLANK_RE = re.compile(r"_{3,}")


def iter_blocks(document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield "p", Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield "tbl", Table(child, document)


def table_rows(tb):
    rows = []
    for r in tb.rows:
        cells = [c.text.strip() for c in r.cells]
        rows.append(cells)
    return rows


def parse(path):
    document = docx.Document(path)
    chapters = []
    cur_chapter = None
    cur_section = None
    questions = []
    appendix = []
    q = None
    in_appendix = False

    def flush():
        nonlocal q
        if q is not None:
            finish(q)
            questions.append(q)
            q = None

    def finish(item):
        """整理答案、解析与空位。"""
        item["stem"] = item["stem"].strip()
        item["answer"] = item.get("answer", "").strip()
        item["explanation"] = item.get("explanation", "").strip()
        item["typeTitle"] = item.get("typeTitle", "")
        if item["type"] == "blank":
            blanks = len(BLANK_RE.findall(item["stem"]))
            parts = [p.strip() for p in re.split(r"[；;]", item["answer"]) if p.strip()]
            if blanks and len(parts) == blanks:
                item["blanks"] = blanks
                item["answerParts"] = parts
            else:
                item["blanks"] = 1
                item["answerParts"] = [item["answer"]]
        elif item["type"] == "choice":
            ans = re.sub(r"[^A-H]", "", item["answer"].upper())
            item["answerKey"] = ans[:1]
        elif item["type"] == "judge":
            a = item["answer"]
            item["answerKey"] = "T" if ("√" in a or "对" in a or "正确" in a) and "错" not in a else "F"
        # 去掉题干首部的题号残渣

    for kind, obj in iter_blocks(document):
        if kind == "p":
            text = obj.text.strip()
            if not text:
                continue
            style = (obj.style.name or "").lower()
            if style.startswith("toc"):
                continue
            # 章节标题
            m = re.match(r"^第\s*(\d+)\s*章", text)
            if m and "Heading" in (obj.style.name or ""):
                flush()
                cur_chapter = {"no": int(m.group(1)), "title": text}
                chapters.append(cur_chapter)
                cur_section = None
                in_appendix = False
                continue
            if text.startswith("附录"):
                flush()
                in_appendix = True
                cur_section = None
                appendix.append({"kind": "h1", "text": text})
                continue
            # 题型标题
            m = re.match(r"^[一二三四五六七八九十]+、\s*(.+)$", text)
            if m and ("Heading" in (obj.style.name or "")):
                flush()
                cur_section = m.group(1).strip()
                if in_appendix:
                    appendix.append({"kind": "h2", "text": text})
                continue

            if in_appendix:
                appendix.append({"kind": "p", "text": text})
                continue

            # 新题目
            m = Q_RE.match(text)
            if m:
                flush()
                q = {
                    "chapter": cur_chapter["no"] if cur_chapter else 0,
                    "chapterTitle": cur_chapter["title"] if cur_chapter else "",
                    "type": SECTION_TYPES.get(cur_section or "", "short"),
                    "typeTitle": cur_section or "",
                    "no": f"{m.group(1)}.{m.group(2)}",
                    "stem": m.group(3).strip(),
                    "options": [],
                    "code": "",
                    "answer": "",
                    "explanation": "",
                    "blocks": [],
                }
                continue
            if q is None:
                continue
            if text.startswith("【答案】"):
                q["answer"] = text[len("【答案】"):].strip()
                continue
            if text.startswith("【解析】"):
                body = text[len("【解析】"):].strip()
                q["explanation"] = (q["explanation"] + "\n" + body).strip()
                continue
            if q["answer"]:
                q["explanation"] = (q["explanation"] + "\n" + text).strip()
                continue
            # 答案之前：选项或题干补充
            mo = OPT_RE.match(text)
            if mo and q["type"] == "choice":
                q["options"].append({"key": mo.group(1), "text": mo.group(2).strip()})
            else:
                tail = "\n" + text
                q["stem"] = (q["stem"] + tail).strip()
        else:
            rows = table_rows(obj)
            if not rows:
                continue
            if in_appendix:
                appendix.append({"kind": "table", "rows": rows})
                continue
            if q is None:
                continue
            single = len(rows) == 1 and len(rows[0]) == 1
            if single and not q["answer"] and not q["code"]:
                q["code"] = rows[0][0]
                continue
            # 解析流中的代码块或表格，按顺序用 [BLOCK:k] 占位
            blocks = q.setdefault("blocks", [])
            if single:
                blocks.append({"type": "code", "text": rows[0][0]})
            else:
                blocks.append({"type": "table", "rows": rows})
            marker = f"\n[BLOCK:{len(blocks) - 1}]\n"
            if q["answer"]:
                q["explanation"] = (q["explanation"] + marker).strip()
            else:
                q["stem"] = (q["stem"] + marker).strip()
    flush()

    bank = {
        "meta": {
            "title": "数据结构（C语言版）第1—5章习题册",
            "source": path.split("\\")[-1].split("/")[-1],
            "count": len(questions),
            "schema": "ds-quiz-bank-v1",
        },
        "chapters": chapters,
        "questions": questions,
        "appendix": appendix,
    }
    return bank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("-o", "--output", default="题库.json")
    args = ap.parse_args()
    bank = parse(args.docx)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)
    print(f"已生成 {args.output}：{bank['meta']['count']} 题")
    for ch in bank["chapters"]:
        rows = [q for q in bank["questions"] if q["chapter"] == ch["no"]]
        print(f"  {ch['title']}: {len(rows)} 题")


if __name__ == "__main__":
    sys.exit(main())
