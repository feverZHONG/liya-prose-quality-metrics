# 稿子质量的量化体检与修法

> 稿子读起来「平」怎么办——**先量再改**。对话占比 · 句长 σ · 台词宽度 · 标点谱 · 段均句，量完对着九种「平」逐条修。
> 适用任何长篇叙事稿（小说 / 短篇 / 说书稿）。全套 7 个工具**纯标准库**，不依赖任何本机环境。

## 这是什么

核心主张一句话：**「平」不是感觉，是可以量的**。用户说「没情绪起伏」「对话量不够」「描写太少」「还能多写点」时——别凭感觉加形容词，先跑一次量尺，把五行体检摆出来，再对着基线说「平在哪一项」。

### 两条口径（入门第一件事）

短篇与长篇的区别只有一处，但很关键：

| | 短篇口径 | 长篇口径（`--long`） |
|:---|:---|:---|
| 段均句 | < 2.4 报警（「一句一行」是病） | **不报警**（戏剧式天然一句一行）；改看台词均长 ≥16、对话占比 14–30% |
| 参考项 | 见 `references/prose-quality-baselines.md` | 句长 σ 24–36、归属语 ≤3/千字、问号 ≤5/千字 |

**量任何一篇之前先定它是哪一套**——拿短篇基线去量长篇，会把「并段」当成优化，恰好把对话的标记并掉、让读者搞混。

### 铁律（编号稳定，别重排）

`0` 先定「量什么」｜`1` 先量再改｜`2` 五行一起看｜`3` 交付带数字（按整屏报）｜`4` 加厚＝加事件或行为，不是加形容词｜`5` 加厚与补长台词是一件事｜`6` 外部评估先核对再改｜`8` 「把 X 压一下」先分清是哪种压｜`9` 口述的构思回原料查证｜`10` 待拍项要分级

**一条最贵的教训**：脚本只做统计，**禁止参与编写**。量尺答得了「有多少、在哪」，答不了「对不对」——实测一篇稿子五条红线全绿，正文里仍躺着 8 处重复残句与说话人错位（机器数的是 `「` 的个数，数不出这句话是谁说的）。**绿灯只是「没踩这五条」，不是「稿子对了」。**

### 工作流

`0 定口径` → `1 量`（五行体检）→ `2 诊断`（八种「平」，**一次只改一种**）→ `3 改`（对着诊断改）→ `4 重量`（交付前四件套，缺一件不算改完）→ `5 母题账` / `6 承接账`

```bash
python3 scripts/prose-metrics.py <稿.md|目录>          # 量尺：按 --- 分节，每节五行体检 + 基线对照
python3 scripts/colon-audit.py <稿.md>                 # 冒号归属审计（只列不判）
python3 scripts/crosscheck-duplicates.py <稿.md>       # 逐句撞车：本稿 ←→ 全库语料（≥14 字重合）
python3 scripts/corpus-band.py <语料目录…>             # 定带/改带之前先跑：一行一篇出形态分布
```

## 工具（7 个，纯标准库）

| 脚本 | 干什么 |
|:---|:---|
| `prose-metrics.py` | **量尺**：对话占比 / 句长 σ / 台词宽度 / 标点谱 / 段均句 + 基线对照，`--long` 切长篇口径 |
| `merge-paragraphs.py` | 并段 CLI（段＝一拍；预览默认，`--write` 已停用——脚本禁止参与编写） |
| `colon-audit.py` | 冒号归属审计：每处「描述＋冒号→台词」的冒号前描述连台词首句列出，只摆给人核 |
| `crosscheck-duplicates.py` | 跨篇逐句撞车扫描（量尺只看本稿内部，同句在别篇用过它零命中） |
| `corpus-band.py` | 定带／改带之前先跑：一行一篇出「段数｜引号样式｜段均轮次｜单一形态｜同型连续」 |
| `draft-sync-check.py` | 待发布稿是否已落后于定稿正文（归一化后逐字比） |
| `normalize-md.py` | 结构修回：并段后把图行与 `---` 从粘连里拆出来（**唯一允许落盘的结构例外**，不碰一个字） |

⚠️ 脚本不认 `--help`——用法读文件头 docstring（`merge-paragraphs.py --write` 会把 markdown 结构挤坏，详见 `references/pitfalls.md`）。

## 目录

| 路径 | 内容 |
|:---|:---|
| `SKILL.md` | 入口：两条口径、总纲、铁律、工作流、工具与档索引 |
| `references/prose-quality-baselines.md` | 完整基线表 + 九种「平」的逐条修法 |
| `references/metrics-mechanics.md` | 量尺的计数口径、哪个动作动哪个数 |
| `references/corpus-baselines.md` | 基线怎么量出来的（已发布语料 + 引号/排版陷阱） |
| `references/band-derivation.md` | 带怎么定：哪些指标可比、长度型比例的可行解边界 |
| `references/path-dependency.md` | 跨篇／跨节排开才看得见的病（标题字数、节首式样、意象复用） |
| `references/diagnosis-eight-flat.md` | 八种「平」的完整诊断表 |
| `references/fix-playbook.md` | 改法手册（加厚＝加事件或行为） |
| `references/dialogue-craft.md` | 对话层修法（谁在说 × 说多少） |
| `references/solo-scene.md` | 单人戏／独处镜头怎么写 |
| `references/delivery-check.md` | 交付前四件套的详细口径 |
| `references/batch-revision-audit.md` | 多轮批量改过之后的回查与逐节对表 |
| `references/retrofit-pass.md` | 存量稿整轮回头整理 |
| `references/motif-ledger.md` | 母题／物件账、称呼演变、看见渠道账 |
| `references/workflow-details.md` | 定口径／母题账／承接账的详细做法与判例 |
| `references/reference-study.md` | 「去读 X／挑几章细品／再回头对比」的流程 |
| `references/pitfalls.md` | 踩过的坑（每条铁律背后的判例、反例、实测数字） |

**读者须知**：文中出现的 `bin/story`、`bin/style-probe`、`short-stories-liya/`、`gate.json`、`小样/` 都是**作者环境**的项目工具链与项目文件——量尺的判据、阈值与修法与它们无关，照自己的项目替换即可。实测数字里的篇号（`01`／`sh20` 这类）读作「第 N 篇样本」即可。

## 姊妹仓库

- [liya-delegation-and-verification](https://github.com/feverZHONG/liya-delegation-and-verification) —— 委派与验收：把「自报」验成事实（本仓「派审读队」那一套的方法论正本）
- [liya-sillytavern-cards](https://github.com/feverZHONG/liya-sillytavern-cards) · [liya-tavern-card-refinement](https://github.com/feverZHONG/liya-tavern-card-refinement) · [liya-sillytavern-worldbook](https://github.com/feverZHONG/liya-sillytavern-worldbook) —— 酒馆角色卡三件（写卡 / 精修 / 世界书）
- [liya-persona-authoring](https://github.com/feverZHONG/liya-persona-authoring) —— 给 AI agent 写它自己的身份文件
- [liya-subtraction-skill](https://github.com/feverZHONG/liya-subtraction-skill) —— 技能库做减法的方法论（本仓 SKILL.md 的两轮拆薄都出自它）
- [liya-vision-recognition-traps](https://github.com/feverZHONG/liya-vision-recognition-traps) —— 视觉模型识图陷阱：22 条实测陷阱 + 真 OCR 通道 + 两图差分
- [liya-chat-game-referee](https://github.com/feverZHONG/liya-chat-game-referee) · [liya-spy-game](https://github.com/feverZHONG/liya-spy-game) · [liya-sea-turtle-soup](https://github.com/feverZHONG/liya-sea-turtle-soup) —— 聊天里能玩的三件（回合制裁判引擎 / 谁是卧底 / 海龟汤）

## 提思路 / 提修正

- 你那边量出来的基线、别的「平」的形态、脚本改进 → 开 [Issue](https://github.com/feverZHONG/liya-prose-quality-metrics/issues)，写清场景（什么稿、量出什么数、读感哪里不对）
- 想直接改 → Fork + PR

## 许可

MIT —— 拿去用、改、再发，保留版权声明即可。

---

*莉娅（[@feverZHONG](https://github.com/feverZHONG)）· 宇宙美好记录官*
