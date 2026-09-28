#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""normalize-md.py — 稿子 markdown 结构规范化（并段／批量改写之后必跑）

唯一允许落盘的结构例外：**只碰 markdown 结构（图行／空行／`---`），一个字都不动**；落盘前先看 diff。
为什么还要它：早年的并段脚本把结构挤坏过——
  ① 图片行与紧随的文字并成一行：`![x](images/y.jpg)「第一句……」`
  ② `---` 与上下段落粘住：`……回去。\n---` 在 markdown 里被解析成 **setext 标题**，
     等于稿子里凭空多出一个 H2（「只有开头一个大标题」的规矩当场破掉）
它在「段均句」那一项上是对的，但结构得单独修回来。

用法:
  python3 normalize-md.py <稿.md>            # 预览：只打印会改什么
  python3 normalize-md.py <稿.md> --write    # 落盘（newline="\n"）

规则（只动结构，不动一个字）:
  1. `![…](…)` 后紧跟文字 → 拆成「图行 / 空行 / 文字」
  2. 行尾粘着 `---` → 拆开
  3. `---` 后紧跟文字 → 拆开
  4. 独立的 `---` 前后各补一个空行
  5. 连续空行折成一个
"""
import re
import sys


def normalize(text: str):
    fixes = {"图行": 0, "---前": 0, "---后": 0, "---空行": 0}
    out = []
    for ln in text.split("\n"):
        m = re.match(r"^(!\[[^\]]*\]\([^)]*\))[ \t]*(\S.*)$", ln)
        if m:
            out += [m.group(1), "", m.group(2)]
            fixes["图行"] += 1
            continue
        m = re.match(r"^(.*\S)[ \t]*---[ \t]*$", ln)
        if m and not ln.lstrip().startswith("---"):
            out += [m.group(1), "", "---"]
            fixes["---前"] += 1
            continue
        m = re.match(r"^---[ \t]*(\S.*)$", ln)
        if m:
            out += ["---", "", m.group(1)]
            fixes["---后"] += 1
            continue
        out.append(ln)

    res = []
    for ln in out:
        if ln.strip() == "---":
            if res and res[-1].strip():
                res.append("")
                fixes["---空行"] += 1
            res.append("---")
            res.append("")
        else:
            res.append(ln)
    s = re.sub(r"\n{3,}", "\n\n", "\n".join(res))
    if not s.endswith("\n"):
        s += "\n"
    return s, fixes


def main():
    args = [a for a in sys.argv[1:] if a != "--write"]
    if len(args) != 1:
        print(__doc__)
        return 2
    path = args[0]
    write = "--write" in sys.argv
    src = open(path, encoding="utf-8", newline="").read()
    dst, fixes = normalize(src)
    changed = sum(fixes.values())
    if not changed and src == dst:
        print(f"{path}: 结构已是干净的，无需改动")
        return 0
    print(f"{path}: 修 {changed} 处 " + "｜".join(f"{k} {v}" for k, v in fixes.items() if v))
    if write:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dst)
        print("已落盘（next：复跑 prose-metrics.py 确认段均句没掉）")
    else:
        print("（预览模式；加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
