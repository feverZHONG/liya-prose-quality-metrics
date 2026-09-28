#!/usr/bin/env python3
"""冒号归属审计（**只列不判**）：把每一处「描述＋冒号→台词」连冒号前那段描述列出来，供人逐条核。

用法:
    python3 colon-audit.py <稿.md|目录>            # 列全部
    python3 colon-audit.py <稿.md> --tail 40       # 冒号前描述只留末尾 40 字（默认 30）
    python3 colon-audit.py <稿.md> --dup           # 另附：≥10 字重复片段（复制残句候选）

判据（机器判不了归属，只把该看的摆出来）：
    冒号左边那段描述的主体，必须是**紧接着说话的那个人**。
    「A 的动作 ＋ ： ＋ B 的话」＝错位，读者只会认成 A 说的。
    三种换落法：B 的话在前＋逗号跟它自己的描述 ／ 把 A 的描述挪回 A 自己那句 ／ 断段。
    ⚠️ 高发形态＝**整段「旋转一格」**：一整段里每句的描述都挂到了下一句上，
       把描述往后挪一位就全对了（看着合理、读着全错）。

本脚本**只读、只打印**——脚本禁止参与编写（改写一律逐处手写）。
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def lines_of(text: str):
    return [(i + 1, x.strip()) for i, x in enumerate(text.split("\n")) if x.strip()]


def _norm_quotes(s: str) -> str:
    """判定前统一引号字形（“”→「」），1:1 字符替换，行号与列位置不变。
    ⚠️ 不归一化＝对全篇用弯引号的稿子直接报 0 处（假绿）——2026-09-23 糖霜 ch20 实测：
    脚本报「0 处」、实际躺着 29 处。story.py 已修过同一个盲区，这里是它的副本。"""
    return s.replace("“", "「").replace("”", "」")


def colon_rows(lines, tail: int = 30):
    """每处「描述＋冒号→台词」：返回 (行号, 冒号前那段描述, 台词首句)。
    判定行已统一引号；报告的引文仍贴原文，行号与列位置不变。"""
    rows = []
    for ln, x in lines:
        xj = _norm_quotes(x)
        for m in re.finditer("「", xj):
            pre = xj[:m.start()]
            if not pre.rstrip().endswith("："):
                continue
            lead = re.split(r"[。！？…」]", pre.rstrip()[:-1])[-1].strip()
            rows.append((ln, lead, x[m.start():m.start() + 26]))
    return rows


def dup_fragments(text: str, n: int = 10, top: int = 20):
    """≥n 字的片段出现 ≥2 次 → 复制残句／回声候选（只列，判归人）"""
    body = re.sub(r"\s", "", text)
    if len(body) < n:
        return []
    c = Counter(body[i:i + n] for i in range(len(body) - n + 1))
    seen, out = [], []
    for s, k in c.most_common():
        if k < 2 or s in seen:
            continue
        if any(s in t for t in seen):
            continue
        seen.append(s)
        out.append((s, k))
        if len(out) >= top:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description="冒号归属审计（只列不判）")
    ap.add_argument("target", help="稿.md 或目录")
    ap.add_argument("--tail", type=int, default=30, help="冒号前描述保留末尾多少字（默认 30）")
    ap.add_argument("--dup", action="store_true", help="另附 ≥10 字重复片段候选")
    a = ap.parse_args()
    p = Path(a.target)
    files = [p] if p.is_file() else sorted(p.rglob("*.md"))
    total = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        rows = colon_rows(lines_of(text))
        print(f"\n=== {f.name}：「描述＋冒号→台词」{len(rows)} 处 ===")
        for ln, lead, q in rows:
            shown = lead if len(lead) <= a.tail else "…" + lead[-a.tail:]
            print(f"  L{ln:<5} {shown}  →  {q}")
        total += len(rows)
        if a.dup:
            dups = dup_fragments(text)
            print(f"  —— 重复片段候选（≥10 字出现 ≥2 次）：{len(dups)} 条")
            for s, k in dups:
                print(f"     ×{k}  {s}")
    print(f"\n共 {total} 处。逐条问一句：冒号左边那段描述，是不是紧接着说话的这个人的？")
    print("不是＝错位（「A 的动作 ＋ ： ＋ B 的话」）→ 三种换落法：台词在前＋逗号跟自己的描述／描述挪回它自己那句／断段。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
