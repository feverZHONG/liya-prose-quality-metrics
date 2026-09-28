#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""crosscheck-duplicates.py — 逐句撞车扫描（本稿 ←→ 全库已发布语料）

为什么需要它：量尺／扫雷／归零项命令／冒号审计**都只看本稿内部**——同一句话在别的篇目里
已经用过，它们一个字都不报（实测新篇里照样躺着旧篇的原句）；人工通读几十篇必漏。
句子层的跨篇复用只能靠机器扫，**扫完再人判**。

用法：
    python3 crosscheck-duplicates.py <本稿.md>
    python3 crosscheck-duplicates.py <本稿.md> --against <目录或文件或 glob …>
    python3 crosscheck-duplicates.py <本稿.md> --min 12        # 连续重合多少字算撞车（默认 14）

不给 --against 时：按数据根自动收集（环境变量 LIYA_DATA_ROOT → 本脚本上级含 skills/ 的那层
→ 家目录），扫 `archive/**/article.md` 并排除本稿自身。--against 给目录时：先找该目录下的
`article.md`，找不到才退回该目录下所有 `*.md`（免得把大纲／规则档当语料扫出假命中）。

判读（命中 ≠ 必须改）：
    ① 同一拍同一个动作被原样搬来 → 改（路径依赖）
    ② 行当名物（咖啡名／器具名）、常见短说法 → 不算，用 --min 卡
    ③ 只报句子层：动作节拍（同一个应答动作出现十余次）与句式层的复用要另派一路读同族旧篇
"""

import argparse
import glob
import os
import re
import sys

CJK = re.compile(r"[\u4e00-\u9fff]")
STRIP = re.compile(r"[「」“”\s]")
SKIP_PREFIX = ("#", "![", ">", "---", "**", "|", "- ", "* ")


def find_root():
    p = os.path.abspath(os.path.dirname(__file__))
    cands = [os.environ["LIYA_DATA_ROOT"]] if os.environ.get("LIYA_DATA_ROOT") else []
    while True:
        cands.append(p)
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    cands.append(os.path.expanduser("~"))   # 兜底不再写死作者路径（换环境设 LIYA_DATA_ROOT）
    for c in cands:
        if os.path.isdir(os.path.join(c, "skills")):
            return c
    sys.exit("找不到数据根：设 LIYA_DATA_ROOT，或从仓库里跑")


def body(path):
    """正文体：去标题行／图行／引用行／分隔线／表格行／列表行。"""
    keep = []
    for ln in open(path, encoding="utf-8"):
        t = ln.strip()
        if not t or t.startswith(SKIP_PREFIX):
            continue
        keep.append(t)
    return "\n".join(keep)


def sentences(text):
    """按句末标点切句，去引号空白；只留含汉字、长度 ≥8 的句。"""
    out = []
    for s in re.split(r"(?<=[。！？…；])", STRIP.sub("", text)):
        s = s.strip()
        if len(s) >= 8 and CJK.search(s):
            out.append(s)
    return out


def collect(against):
    if not against:
        return sorted(glob.glob(os.path.join(find_root(), "archive", "**", "article.md"), recursive=True))
    out = set()
    for pat in against:
        if os.path.isdir(pat):
            arts = glob.glob(os.path.join(pat, "**", "article.md"), recursive=True)
            out.update(arts or glob.glob(os.path.join(pat, "**", "*.md"), recursive=True))
        else:
            out.update(glob.glob(pat))
    return sorted(out)


def scan(target, others, clean, mn):
    grams = {}
    for p in others:
        txt = clean[p]
        for i in range(len(txt) - mn + 1):
            grams.setdefault(txt[i:i + mn], []).append((p, i))
    hits = []
    for s in sentences(body(target)):
        best = {}
        for i in range(len(s) - mn + 1):
            for p, j in grams.get(s[i:i + mn], ()):
                txt = clean[p]
                n = 0
                while i + n < len(s) and j + n < len(txt) and s[i + n] == txt[j + n]:
                    n += 1
                if n > best.get(p, (0, ""))[0]:
                    best[p] = (n, txt[j:j + n])
        for p, (n, frag) in best.items():
            hits.append((n, os.path.basename(os.path.dirname(p)) or os.path.basename(p), frag, s))
    hits.sort(key=lambda x: -x[0])
    return hits


def main():
    ap = argparse.ArgumentParser(description="逐句撞车扫描（本稿 vs 全库语料）")
    ap.add_argument("target", help="本稿路径（.md）")
    ap.add_argument("--against", nargs="*", help="语料：目录／文件／glob（不给则按数据根自动收集）")
    ap.add_argument("--min", type=int, default=14, help="连续重合多少字算撞车（默认 14）")
    a = ap.parse_args()

    target = os.path.abspath(a.target)
    if not os.path.isfile(target):
        sys.exit("找不到本稿：%s" % target)
    corpus = [p for p in collect(a.against) if os.path.abspath(p) != target]
    if not corpus:
        sys.exit("语料为空：用 --against 指定，或确认数据根下有 archive/**/article.md")
    clean = {p: STRIP.sub("", body(p)) for p in corpus}

    hits = scan(target, corpus, clean, a.min)
    print("=== %s ←→ 语料 %d 篇｜连续 ≥%d 字重合：%d 处 ===" % (
        os.path.basename(os.path.dirname(target)) or os.path.basename(target),
        len(corpus), a.min, len(hits)))
    if not hits:
        print("  ✅ 零命中（同句／长片段都没搬过）")
    for n, oname, frag, s in hits:
        print("  [%d 字] ←→ %s" % (n, oname))
        print("       语料：…%s…" % frag)
        print("       本稿：%s%s" % (s[:60], "…" if len(s) > 60 else ""))
    print("\n判读：同一拍同一个动作被搬来＝改；行当名物／常见短说法＝不算（调 --min）；"
          "动作节拍与句式层的复用本工具看不见，要另派一路读同族旧篇。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
