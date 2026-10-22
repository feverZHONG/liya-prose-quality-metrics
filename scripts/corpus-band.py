#!/usr/bin/env python3
"""corpus-band.py —— 量「同族已发布语料」的分布带（立/改判据带之前先跑这个）

用法：
    python3 corpus-band.py <目录或文件…>              # 目录会递归找 article.md / 正文.md / 定稿.md
    python3 corpus-band.py <目录> --min-dia 30        # 汇总时只看真对话篇（对话行 ≥30）

口径与 prose-metrics / story vices 一致：**段＝非空行**；轮次＝段内 `「` 的个数。
一行一篇：段数｜引号样式｜对话段｜段均轮次｜多轮段%｜单一形态｜同型连续≥3 处数。
末尾汇总：段均轮次／多轮段／单一形态占比／同型连续 的 min–max 与中位。

⚠️ 它**只统计、不判对错**，也数不出「这句话是谁说的」（同一个人的话被描述断开算两轮、
两个人挤在一段也算两轮）。别拿数字卡稿——先用它跟已发布语料对齐，再决定带（见
references/band-derivation.md §八）。
"""

import os
import re
import statistics as st
import sys
from collections import Counter

NAMES = ("article.md", "正文.md", "定稿.md")
SKIP_PREFIX = ("#", "![", "**", "---", ">", "|")


def kinds_of(x):
    """段落形态（与 story.py 同法）"""
    q = len(re.findall(r"[\u300c\u201c]", x))
    if q == 0:
        return "纯叙述"
    if q == 1 and re.fullmatch(r"[\u300c\u201c][^\u300d\u201d]*[\u300d\u201d][\u3002\uff01\uff1f\u2026]*", x):
        return "纯台词"
    if q >= 3:
        return "台词-叙述-台词"
    if x[0] in "\u300c\u201c":
        return "台词+归属"
    return "描述+台词"


def measure(path):
    txt = open(path, encoding="utf-8").read()
    lines = [x.strip() for x in txt.split("\n")
             if x.strip() and not x.strip().startswith(SKIP_PREFIX)]
    rounds = [len(re.findall("\u300c", x)) for x in lines]
    dia = [r for r in rounds if r > 0]
    multi = sum(1 for r in dia if r >= 2)
    seq = [k for k in (kinds_of(x) for x in lines) if k != "纯叙述"]
    runs, cur, cnt = 0, None, 0
    for k in seq:
        if k == cur:
            cnt += 1
        else:
            if cur and cnt >= 3:
                runs += 1
            cur, cnt = k, 1
    if cur and cnt >= 3:
        runs += 1
    top = Counter(seq).most_common(1)[0] if seq else ("—", 0)
    return dict(段数=len(lines), 对话段=len(dia),
                段均轮次=(sum(dia) / len(dia) if dia else 0.0),
                多轮段=(100 * multi / len(dia) if dia else 0.0),
                单一形态=top[0], 单一形态占比=(100 * top[1] / max(len(seq), 1)),
                同型连续=runs,
                引号=("\u300c" if txt.count("\u300c") >= txt.count("\u201c") else "\u201c"))


def collect(paths):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for n in NAMES:
                    if n in files:
                        out.append(os.path.join(root, n))
    return sorted(set(out))


def main():
    args = list(sys.argv[1:])
    min_dia = 0
    if "--min-dia" in args:
        i = args.index("--min-dia")
        min_dia = int(args[i + 1])
        del args[i:i + 2]
    if not args:
        args = ["."]
    files = collect(args)
    if not files:
        print("✗ 没找到稿子（找 article.md / 正文.md / 定稿.md）")
        return 2
    head = f"{'篇':<34}{'段数':>5}{'引':>3}{'对话段':>6}{'段均轮次':>9}{'多轮段%':>8}{'单一形态':>18}{'同型连≥3':>9}"
    print(head)
    rows = []
    for f in files:
        m = measure(f)
        rows.append((f, m))
        shape = f"{m['单一形态']} {m['单一形态占比']:.0f}%"
        print(f"{os.path.basename(os.path.dirname(f))[:33]:<34}{m['段数']:>5}{m['引号']:>3}{m['对话段']:>6}"
              f"{m['段均轮次']:>9.2f}{m['多轮段']:>8.0f}{shape:>18}{m['同型连续']:>9}")
    real = [m for _f, m in rows if m["对话段"] >= max(min_dia, 1)]
    if min_dia:
        real = [m for _f, m in rows if m["对话段"] >= min_dia]
    if real:
        def span(key, fmt="{:.2f}"):
            vals = [m[key] for m in real]
            return f"min {fmt.format(min(vals))}／max {fmt.format(max(vals))}／中位 {fmt.format(st.median(vals))}"
        print(f"\n汇总（{len(real)} 篇，对话段 ≥ {max(min_dia, 1)}）：")
        print("  段均轮次   " + span("段均轮次"))
        print("  多轮段%    " + span("多轮段", "{:.0f}"))
        print("  单一形态%  " + span("单一形态占比", "{:.0f}"))
        print("  同型连≥3  " + span("同型连续", "{:.0f}"))
    print("\n⚠️ 只统计、不判对错：数不出「这句话是谁说的」；只认「」，引号样式列已一并打出来。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
