#!/usr/bin/env python3
"""draft-sync-check.py — 待发布稿是否已经落后于定稿正文。

用法：
    python3 draft-sync-check.py <定稿正文.md> <待发布稿目录 或 article.md>

为什么需要它：发布稿生成器（如 `story draft`）的自校只在**生成那一刻**跑。正文后来又改了，
已经生成的待发布稿不会跟着变，也没有任何东西会提醒——发出去才发现发的是旧稿。

判法：两边都归一化（丢掉标题行 `#`／图 `![`／【前排说明】整段／`---` 分隔线／全部空白）
后逐字比；不一致时报字数差与首处差异。退出码：0＝一致，1＝落后，2＝用法或文件问题。

注意：改标题、换图这类**结构性**差异归一化后会被忽略；报不一致＝正文变过而稿没重出。
说明段若不以空行结束，也可能被误判为落后——宁可重出一遍。
"""
import pathlib
import re
import sys

DROP_LINE = (re.compile(r'^#'), re.compile(r'^!\['), re.compile(r'^-{3,}\s*$'))
NOTE_START = '【前排说明】'


def _is_note_start(stripped: str) -> bool:
    """前排说明可能独占一行，也可能挂在 `#` 标题行上。"""
    if stripped.startswith(NOTE_START):
        return True
    return stripped.startswith('#') and NOTE_START in stripped


def normalize(text: str) -> str:
    """丢掉发布头（标题／图／前排说明段／分隔线）后压掉全部空白。"""
    kept = []
    skipping_note = False
    for line in text.splitlines():
        stripped = line.strip()
        if skipping_note:
            if not stripped:            # 说明段以空行结束
                skipping_note = False
            continue
        if _is_note_start(stripped):
            skipping_note = True
            continue
        if any(p.match(stripped) for p in DROP_LINE):
            continue
        kept.append(line)
    return re.sub(r'\s+', '', ''.join(kept))


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, draft = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    if draft.is_dir():
        draft = draft / 'article.md'
    for path in (src, draft):
        if not path.exists():
            print(f'✗ 找不到文件：{path}')
            return 2
    a = normalize(src.read_text(encoding='utf-8'))
    b = normalize(draft.read_text(encoding='utf-8'))
    if a == b:
        print(f'✓ 一致（{len(a)} 字）：{src.name} == {draft.name}')
        return 0
    at = 0
    for x, y in zip(a, b):
        if x != y:
            break
        at += 1
    print(f'✗ 不一致：正文 {len(a)} 字 / 待发布稿 {len(b)} 字（差 {len(b) - len(a):+d}）')
    print(f'  首处差异 @{at}：正文「{a[max(0, at - 25):at + 25]}」｜稿「{b[max(0, at - 25):at + 25]}」')
    print('  → 正文动过就重出。')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
