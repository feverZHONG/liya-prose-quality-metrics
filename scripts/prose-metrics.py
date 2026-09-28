#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prose-metrics — 稿子「平不平」的量尺（对话占比 / 节奏带宽 / 对话宽度）

为什么要有：内容对不对靠读，**平不平只能靠量**。
用户说「没情绪起伏」「对话量不够」「描写太少」时，先跑这个把数字摆出来，
再对着 references/prose-quality-baselines.md 定改哪一项——
比凭感觉加形容词靠谱得多。

用法:
    python3 prose-metrics.py <article.md>          # 单篇（整篇 + 按 --- 分节）
    python3 prose-metrics.py <稿1.md> <稿2.md>
    python3 prose-metrics.py <dir>                 # 目录：递归找 article.md

四个数一起看（只看一个会把稿子改成对话流水帐）:
    CJK / 去空白      —— 篇幅
    对话占比          —— 成稿区间 42–50%
    句长标准差        —— 节奏带宽；低于 ~9 = 全篇一个速度 = 「平」
    台词 ≥16字占比    —— 对话宽度；趋近 0 = 全是 4–8 字的确认句
    （附带：台词含逗号/破折号 28–41%、含省略号 12–28%）
"""

import re
import statistics as st
import sys
from pathlib import Path

CJK = re.compile(r'[\u4e00-\u9fff]')
QUOTE = re.compile(r'「[^」]*」|“[^”]*”')   # 稿内用「」，B站成品稿用“”——两种都要认（2026-09-19 修：原来只认「」，跑已发布篇得 0）
MARKS = "，。？！…—、"

# 成稿基线（01–15 已发布篇落盘稿，量法同本脚本）
BASE = {
    '对话占比': (0.42, 0.50),
    '句长标准差': (11.9, 19.0),
    '台词≥16字占比': (0.18, 0.25),
    '台词含逗号/破折号': (0.28, 0.41),
    '台词含省略号': (0.12, 0.28),
}

# 标点谱基线（每千汉字，01–15 已发布篇实测区间）
PUNCT_BASE = {
    '，': (22.7, 80.6),
    '。': (45.8, 99.2),
    '？': (0.4, 7.9),
    '！': (0.0, 2.6),
    '…': (0.0, 24.5),
    '—': (6.4, 28.1),
    '、': (0.4, 7.6),
}
# 逗号+句号占比上限：全篇靠这两样说话就是「平」（已发布篇 73–81%）
FLAT_RATIO = 0.85


def strip_meta(text: str) -> str:
    """去掉标题行/图引用/引用块/署名行，只留正文"""
    keep = []
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            keep.append('')          # 保留空行——段数/段均句（分行体检）要用
            continue
        if s.startswith('#') or s.startswith('!') or s.startswith('>'):
            continue
        if s.startswith('文字：') or s.startswith('大纲/校对') or s.startswith('发布时间'):
            continue
        keep.append(line)
    return '\n'.join(keep)


def metrics(body: str) -> dict:
    plain = re.sub(r'\s', '', body)
    dlg = QUOTE.findall(body)
    lens = [len(x) - 2 for x in dlg]                # 去掉两个引号
    sents = [s for s in re.split(r'[。！？…]+', body) if re.sub(r'\s', '', s)]
    sl = [len(re.sub(r'\s', '', s)) for s in sents]
    n = len(dlg)
    cjk = len(CJK.findall(body)) or 1
    punct = {m: round(body.count(m) * 1000 / cjk, 1) for m in MARKS}
    flat = (body.count('，') + body.count('。')) / max(sum(body.count(m) for m in MARKS), 1)
    # 叙述句 / 台词 分开算（短句癖=两头都能碎）
    narr = QUOTE.sub('\n', body)
    ns = [s for s in re.split(r'[。！？…—]+|[；]', narr) if re.sub(r'[，、：]', '', s)]
    nl = [len(re.sub(r'\s', '', s)) for s in ns]
    # 短句（去碎片）：切句后剔掉「只含引号」与「纯归属语」的碎片，再统计
    _S = [x for x in re.split(r'[。！？…]+', re.sub(r'\s', '', body)) if re.sub(r'[，、：]', '', x)]
    _K = []
    for _x in _S:
        _core = re.sub(r'[「」“”，。！？…—、：]', '', _x)
        if not _core or re.fullmatch(r'(她|阁下|他)(说|问|答|道)', _core):
            continue
        _K.append(len(re.sub(r'[^\u4e00-\u9fff]', '', _x)))
    # 重复台词（路径依赖）：同一句被反复用
    from collections import Counter as _C
    _cnt = _C([x.strip() for x in dlg if x.strip()])
    _rep = [(k, v) for k, v in _cnt.items() if v >= 3]
    # 归属语密度：她／阁下／他 + 说/问/答/回/道/喊/叫/应
    # ⚠️ 2026-09-20 修：此前只数「说」，漏掉问/答/回/道——实测 01 节 2 处 → 真数 8 处
    _TAG = re.compile(r'(?:她|他|阁下|莉娅)(?:忽然|又|才|先|跟着|接着|说完|低下去|说得)?(?:说|问|答|回|道|喊|叫|应)')
    _tl = _TAG.findall(body)
    tags = len(_tl)
    # ⚠️ 2026-09-20 加：单标签分布——**总量达标 ≠ 单标签达标**
    # （上-3「她说」×5、总量只有 2.1/千字，看着没事就混过去了）
    from collections import Counter as _TC
    _td = _TC(_tl)
    # 段落粒度（分行）：一段几句、单句段占比
    # ⚠️ 2026-09-20 修：段＝**非空行**（已发布篇是单换行分段；按空行切会把整篇算成一段）
    ps = [x.strip() for x in body.split('\n') if x.strip()]
    # ⚠️ 2026-09-20 修：拆分前先剔引号——否则「谢谢。」会因收尾的」被算成两句，
    #    段均句虚高、"一行一句"被盖住（同一节曾显示 段均句 2.47／单句段 4%，真数 1.86／54%）
    pc = [max(len([y for y in re.split(r'[。！？…]+', re.sub(r'[「」“”]', '', x))
                  if re.sub(r'[\s，、：]', '', y)]), 1) for x in ps]
    return {
        'CJK': len(CJK.findall(body)),
        '去空白': len(plain),
        '对话占比': sum(len(x) for x in dlg) / max(len(plain), 1),
        '对话条数': n,
        '台词均长': st.mean(lens) if lens else 0.0,
        '台词≤5字占比': (sum(1 for x in lens if x <= 5) / n) if n else 0.0,
        '台词≥16字占比': (sum(1 for x in lens if x >= 16) / n) if n else 0.0,
        '台词含逗号/破折号': (sum(1 for x in dlg if '，' in x or '——' in x) / n) if n else 0.0,
        '台词含省略号': (sum(1 for x in dlg if '……' in x) / n) if n else 0.0,
        '句长标准差': st.pstdev(sl) if len(sl) > 1 else 0.0,
        '最长句': max(sl) if sl else 0,
        '叙述均长': st.mean(nl) if nl else 0.0,
        '叙述≤5字占比': (sum(1 for x in nl if x <= 5) / len(nl)) if nl else 0.0,
        '台词句号密度': (sum(x.count('。') for x in dlg) * 100 / max(sum(len(x) - 2 for x in dlg), 1)),
        '句均长去碎片': st.mean(_K) if _K else 0.0,
        '短句比去碎片': (sum(1 for x in _K if x <= 5) / len(_K)) if _K else 0.0,
        '重复台词种数': len(_rep),
        '最高重复': _rep[:3],
        '归属语': tags,
        '归属语密度': tags * 1000 / cjk,
        '归属语每百条': tags * 100 / n if n else 0.0,
        '单标签最高': max(_td.values()) if _td else 0,
        '归属语分布': _td.most_common(5),
        '段数': len(ps),
        '段均句': st.mean(pc) if pc else 0.0,
        '单句段占比': (sum(1 for c in pc if c == 1) / len(pc)) if pc else 0.0,
        '标点谱': punct,
        '逗句占比': flat,
    }


def flag(key: str, val) -> str:
    if key not in BASE:
        return ''
    lo, _hi = BASE[key]
    return '✅' if val >= lo else ('⚠️' if val >= lo * 0.8 else '❌')


def report(path: Path):
    body = strip_meta(path.read_text(encoding='utf-8'))
    print(f'\n=== {path.name} ===')
    sections = [s for s in re.split(r'\n---\n', body) if CJK.search(s)]
    rows = [('全篇', body)] + ([(f'节{i + 1}', s) for i, s in enumerate(sections)] if len(sections) > 1 else [])
    for name, seg in rows:
        m = metrics(seg)
        print(
            f"{name:<4} CJK{m['CJK']:5d} 去空白{m['去空白']:5d} | "
            f"对话{m['对话占比'] * 100:5.1f}%{flag('对话占比', m['对话占比'])} "
            f"条{m['对话条数']:3d} 均长{m['台词均长']:4.1f} "
            f"≥16字{m['台词≥16字占比'] * 100:3.0f}%{flag('台词≥16字占比', m['台词≥16字占比'])} "
            f"逗号{m['台词含逗号/破折号'] * 100:3.0f}% "
            f"省略{m['台词含省略号'] * 100:3.0f}% | "
            f"句长标准差{m['句长标准差']:4.1f}{flag('句长标准差', m['句长标准差'])} 最长句{m['最长句']:3d}"
        )
        warn = ''
        if m['逗句占比'] > FLAT_RATIO:
            warn += f"  ⚠️偏平（逗+句 {m['逗句占比'] * 100:.0f}% > {FLAT_RATIO * 100:.0f}%）"
        if m['CJK'] >= 400 and m['标点谱']['？'] < 2.0:
            warn += '  ⚠️问号少（<2/千字）'
        if m['叙述≤5字占比'] > 0.26:
            warn += f"  ⚠️叙述碎（≤5字 {m['叙述≤5字占比'] * 100:.0f}% > 26%）"
        if m['CJK'] >= 400 and m['台词均长'] < 9.0:
            warn += f"  ⚠️台词短（均长 {m['台词均长']:.1f} < 9）"
        if MODE == 'short' and m['段均句'] < 2.4:
            warn += f"  ⚠️分行碎（段均句 {m['段均句']:.1f} < 2.4，一句一行）"
        if MODE == 'long':
            if m['归属语密度'] > 8:
                warn += f"  ⚠️标签泛滥（归属语 {m['归属语密度']:.1f}/千字 > 8，长篇口径）"
            if m['单标签最高'] > 3:
                warn += f"  ⚠️单标签重复（{m['归属语分布'][0][0]} ×{m['单标签最高']} > 3/节）"
            if m['CJK'] >= 400 and m['段均句'] < 2.0:
                warn += f"  ⚠️分行碎（段均句 {m['段均句']:.2f} < 2.0；已发布对话密篇 2.0–2.4）"
            if m['CJK'] >= 400 and m['单句段占比'] > 0.50:
                warn += f"  ⚠️一行一句（单句段 {m['单句段占比']*100:.0f}% > 50%；已发布均值 41%）"
            if m['CJK'] >= 400 and m['归属语'] >= 3 and m['归属语每百条'] > 20:
                top = re.findall(r'(?:她|他|阁下|莉娅)(?:又说|又回|忽然|又|才|先|跟着|接着|说完)?(?:说|问|答|回|道|喊|叫|应)', body)
                warn += f"  ⚠️标签扎堆（{m['归属语']} 处／每百条 {m['归属语每百条']:.0f}，已发布 ≤21）"
            if m['CJK'] >= 400 and m['台词均长'] < 10.5:
                warn += f"  ⚠️台词偏短（均长 {m['台词均长']:.1f} < 10.5，长篇口径）"
            if m['CJK'] >= 400 and m['台词≥16字占比'] < 0.18:
                warn += f"  ⚠️台词宽度不足（≥16字 {m['台词≥16字占比']*100:.0f}% < 18%，长篇口径）"
        print('     标点谱(每千字) ' + ' '.join(f"{k}{v}" for k, v in m['标点谱'].items())
              + f" | 逗+句{m['逗句占比'] * 100:3.0f}%{warn}")
        print(f"     短句体检：叙述均长 {m['叙述均长']:.1f}（基线 19.2）≤5字 {m['叙述≤5字占比'] * 100:.0f}%（≤26）"
              f" | 台词均长 {m['台词均长']:.1f}（10.3–13.5）≤5字 {m['台词≤5字占比'] * 100:.0f}%（≤50）")
        print(f"     句号体检：台词句号密度 {m['台词句号密度']:.1f}/百字（已发布 8.9，区间 0–12.0；≈100÷台词均长，台词越短越密）")
        _seg_note = '基线 3.0；**长篇口径不报警**（戏剧式天然一句一行）' if MODE == 'long' else '基线 3.0'
        print(f"     分行体检：{m['段数']} 段（{m['CJK'] / max(m['段数'], 1):.0f} 字/段）段均句 {m['段均句']:.2f}（{_seg_note}）单句段 {m['单句段占比'] * 100:.0f}%（已发布均值 41%，区间 25–65%）")
        print(f"     归属语：{m['归属语']} 处｜{m['归属语密度']:.1f}/千字（已发布 3.3）｜每百条台词 {m['归属语每百条']:.1f}（已发布 10.8）｜**同一标签 ≤3 次/节**")
        print(f"     短句(去碎片)：句均长 {m['句均长去碎片']:.1f}（已发布 12.8）｜≤5字 {m['短句比去碎片'] * 100:.1f}%（已发布 28.4，区间 15.7–44）")
        if m['重复台词种数']:
            print(f"     路径依赖：同一句出现 ≥3 次的台词 {m['重复台词种数']} 种 {m['最高重复']}（已发布 0.3 种）")
    if MODE == 'long':
        print('口径：**长篇本源篇**（戏剧式）——段均句不报警；另看：对话占比 42–50% ｜ 台词均长 ≥10.5 ｜ 台词≥16字 18–25% ｜ **归属语 ≤8/千字**（>8＝标签泛滥）｜ 句长σ 11.9–19.0')
    else:
        print('口径：短篇故事（系列 01–21）——基线：对话占比 42–50% ｜ 句长标准差 11.9–19.0 ｜ 台词≥16字 18–25% ｜ 含逗号 28–41% ｜ 含省略 12–28%')
    print('标点谱基线(每千汉字)：' + ' ｜ '.join(f"{k}{lo}–{hi}" for k,(lo,hi) in PUNCT_BASE.items()) + f' ｜ 逗+句 ≤{FLAT_RATIO*100:.0f}%')


MODE = 'short'   # 'short' = 短篇故事（系列 01–21，氛围式）｜'long' = 长篇本源篇（戏剧式）


def main():
    global MODE
    argv = sys.argv[1:]
    if '--long' in argv:
        MODE = 'long'
    if not argv:
        print(__doc__)
        sys.exit(1)
    targets = []
    for arg in [a for a in argv if a != '--long']:
        p = Path(arg)
        if p.is_dir():
            targets += sorted(p.rglob('article.md')) or sorted(p.glob('*.md')) or sorted(p.glob('*.txt'))
        elif p.exists():
            targets.append(p)
        else:
            print(f'找不到：{arg}')
    if not targets:
        print('没找到可量的稿子。')
        return
    for t in targets:
        report(t)


if __name__ == '__main__':
    main()
