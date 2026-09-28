#!/usr/bin/env python3
"""并段 CLI：把「一句话一行」的稿子并成「段＝一拍」。

用法:
    python3 merge-paragraphs.py <稿.md|目录>            # 预览（不动文件）
    ※ --write 已停用（阁下 2026-09-22：脚本只做统计，禁止参与编写）——只出预览与相邻段建议
    python3 merge-paragraphs.py <稿.md> --max-s 6 --max-c 150

规则（`43` 三条 + 实测补的三道保险，2026-09-19 全篇验证）:
  ① 叙述段 → 紧随台词段、② 台词段 → 紧随叙述段、③ 叙述段 → 叙述段：并
  保险 1 ★ 引号接引号＝换人，一律断开
        （上一段以 」收＋下一段以 「 起；或下一段以 「 起而上一段里已有 「）
        —— 只看「是不是纯台词段」拦不住：链条会先并(叙述+台词)、再把结果和纯台词段并起来
  保险 2 点破拍保护：单句且短（叙述 ≤16 字／台词 ≤12 字）不并
  保险 3 换拍词开头即断：后来／过了一会儿／第二天／再往前／又走／走到／回去／出门／天…
限制: 每段 ≤max-s 句、≤max-c 字（默认 6/150；`43` 当年是 4/110，对话密的稿子要用宽一点）

量尺口径差：本脚本的段均句比 prose-metrics.py 高 0.1 左右（切句集不同）。
**报数用 prose-metrics.py**，本脚本只用来找可并的相邻段。
"""
import argparse
import re
import sys
from pathlib import Path

Q = re.compile(r'^「[^」]*」$')
BREAK = re.compile(r'^(后来|过了一会儿|再过了一会儿|第二天|第三天|再往前|又走|走到|回去|出门|天|早上|傍晚|夜里|灯|等)')
PUNCH_Q = 12      # 台词点破拍上限（字）
PUNCH_N = 16      # 叙述点破拍上限（字）


def sents(t: str):
    return [x for x in re.split(r'(?<=[。！？…])', t) if x.strip()]


def nchar(t: str) -> int:
    return len(re.sub(r'\s', '', t))


def punch(t: str) -> bool:
    s = sents(t)
    if len(s) != 1:
        return False
    return nchar(t) <= (PUNCH_Q if "「" in t else PUNCH_N)


ATTR = re.compile(r'(?:她|他|阁下|莉娅)(?:忽然|又|才|先|跟着|接着|说完)?(?:说|问|答|回|道|喊|叫|应)')


def merge_body(body: str, max_s: int, max_c: int, weave: bool = False, dialogues: bool = False) -> str:
    out = []
    for b in body.split("\n\n"):
        cur = b.strip()
        if not cur:
            continue
        if out and out[-1] != "---" and cur != "---":
            prev = out[-1]
            # 保险 1：引号接缝＝换人
            cut = (prev.rstrip().endswith("」") and cur.startswith("「")) \
                or (cur.startswith("「") and "「" in prev)
            # --weave：上一段是「叙述夹着台词」的混合段时，允许把紧随的台词并进来
            #   （v8–v11 的「编织」手法；只在句数/字数不超限、且上一段确实有叙述时放开）
            if weave and cut and cur.startswith("「") and "「" in prev:
                has_narr = bool(re.sub(r'「[^」]*」', '', prev).strip())
                if has_narr:
                    cut = False
            # --dialogues：两句台词并一段（段＝一拍）——说话人分得清才并：
            #   ① 上一段带归属语，或本段自带归属/动作锚；或
            #   ② 短问答（两段合起来 ≤24 字）：交替次序自明，读者跟得上（快问答并一段）
            if dialogues and cut and cur.startswith("「"):
                if ATTR.search(prev) or ATTR.search(cur) or (nchar(prev) + nchar(cur) <= 24):
                    cut = False
            if (not cut and not punch(prev) and not punch(cur) and not BREAK.match(cur)
                    and len(sents(prev)) + len(sents(cur)) <= max_s
                    and nchar(prev) + nchar(cur) <= max_c):
                out[-1] = prev + cur
                continue
        out.append(cur)
    return "\n\n".join(out)


def stat(t: str):
    bl = [b for b in t.split("\n\n") if b.strip()]
    n = sum(len(sents(b)) for b in bl)
    return len(bl), (n / len(bl) if bl else 0), (sum(1 for b in bl if len(sents(b)) == 1) / len(bl) * 100 if bl else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--write", action="store_true", help="落盘（默认只预览）")
    ap.add_argument("--max-s", type=int, default=6)
    ap.add_argument("--max-c", type=int, default=150)
    ap.add_argument("--weave", action="store_true",
                    help="放开保险 1：上一段是「叙述夹台词」的混合段时，允许把紧随的台词并进来（编织手法）")
    ap.add_argument("--dialogues", action="store_true",
                    help="允许台词段接台词段（段＝一拍）；前提是归属分得清（上一段带归属语，或本段自带锚）")
    a = ap.parse_args()
    if a.write:
        print("✗ --write 已停用（阁下 2026-09-22：脚本只做统计，禁止参与编写）。")
        print("  并段／调序／清标点一律逐段手写；本脚本只出预览与建议。")
        return 2
    t = Path(a.target)
    files = [t] if t.is_file() else sorted(t.rglob("*.md"))
    for f in files:
        src = f.read_text(encoding="utf-8")
        new = "\n---\n".join(merge_body(x.strip(), a.max_s, a.max_c, a.weave, a.dialogues) for x in src.split("\n---\n"))
        if not new.endswith("\n"):
            new += "\n"
        b, af = stat(src), stat(new)
        print(f"{f.name}: 段 {b[0]}→{af[0]}｜段均句 {b[1]:.2f}→{af[1]:.2f}｜单句段 {af[2]:.0f}%")
    print("（预览模式：只看不写——脚本不改写正文）")


if __name__ == "__main__":
    sys.exit(main())
