---
name: expert-packager
display_name: 打包专家 · 专家生成/打包/安装
display_name_en: Expert Packager
description: >-
  生成、校验、安装、打包 WorkBuddy 专家包（Agent 型 / Team 型），产出符合 open.workbuddy.cn 开放平台规范的专家包与插件包，生成后自动安装到专家中心。当用户说「生成专家」「创建专家」「做个专家」「打包专家」「专家打包」「专家上架」「专家包」「专家校验」「导入专家」「修改专家」「打包插件」「开放平台上传」时使用。 也适用于「生成专家包」「专家合规」「编辑专家」「插件打包」「expert package」「package expert」这类说法。
description_zh: >-
  生成/校验/安装/打包 WorkBuddy 专家包，产出符合开放平台规范的专家与插件包
description_en: >-
  Generate, validate, install and package WorkBuddy Expert packages (Agent / Team) compliant with the open.workbuddy.cn platform spec.
category: development
version: 1.3.0
author: 刘玉明
trigger:
  - 打包专家
  - 生成专家
  - 创建专家
  - 做个专家
  - 专家打包
  - 专家上架
  - 生成专家包
  - 专家包
  - 专家校验
  - 专家合规
  - 导入专家
  - 修改专家
  - 编辑专家
  - 打包插件
  - 插件打包
  - 开放平台上传
  - expert package
  - package expert
agent_created: true
---

# 打包专家 · 专家生成/打包/安装 (expert-packager)

把「手写一堆 JSON 和 Markdown、再摆到对的目录、再打成 zip」压成一条命令：
说清想让专家做什么 → 本机专家中心多出一个能直接用的专家 → 需要时分发或上架。

> **交付标准（先看这条）**
> 终点是**WorkBuddy 专家中心「我的专家」里能选到它**。只生成了目录、只产出了一个 zip，都**不算完成**。
> - `new_expert.py` 默认直接生成到专家安装目录 → **生成即就位**
> - `install_expert.py` 先校验再注册，**注册就是安装**——它是生成流程的必做步骤，不是可选项
> - 上架 open.workbuddy.cn：**专家**传插件形态包（`--platform`）；**技能**传技能目录包（默认产出）
> - **本技能自己是个技能，不是专家**：上传时传 `<技能名>/SKILL.md` 那种目录包，
>   不要给它合成 `plugin.json`、不要套 `skills/` 子目录 —— 那样会报「压缩包缺少 SKILL.md 文件」

**以下命令都在本技能目录下执行**（`~/.workbuddy/skills/expert-packager/`）。

## 一、专家有两种形态

| 形态 | `expertType` | 判据 | 产出文件 |
|------|--------------|------|----------|
| **Agent 型** | `agent` | 单一角色就能交付 | `agents/<expert-name>.md` |
| **Team 型** | `team` | 需要多个专业角色协作、有明确分工 | `agents/<team>-team-lead.md` + 各团员 MD |

判据是**结构**，不是用户口吻。用户说「一个专家团」但只有一个角色时，仍按 `agent` 建，并说明理由。
行业分类 `categoryId` 同样按实际能力判定，取自 12 类枚举，不可自造 —— 见 `references/expert-spec.md`。

## 二、工作流程

```
1. 定类型  → 2. 生成骨架 → 3. 生成头像 → 4. 填内容 → 5. 校验 → 6. 安装 → 7. 打包
```

### Step 1 · 生成骨架

```bash
# Agent 型
python scripts/new_expert.py my-expert --type agent

# Team 型（--member 可重复）
python scripts/new_expert.py my-team --type team --member market-analyst --member risk-reviewer
```

- 默认落到专家安装目录（`~/.workbuddy/plugins/marketplaces/my-experts/plugins/`），**不要改到别处**：生成到其他目录专家中心检测不到。
- 用户若要求换个路径，要拒绝并说明「专家必须生成到专家目录才能被检测到」。
- 骨架带 `[TODO]` 占位，后续由你填。加 `--force` 可重建同名目录（仅限含 `.codebuddy-plugin/` 的目录）。
- 想一条命令走完「生成 + 安装」：用 `--meta` 传一份展示字段 JSON，内容完整时脚本会自动校验并安装。

### Step 2 · 生成头像

调 `ImageGen` 生成，`size` 传 `"1024x1024"`，输出到专家包的 `avatars/` 目录（**运行时产物**，本技能内不存在）。

- Agent 型 1 张，文件名 avatars/expert.png
- Team 型 N+1 张：团队整体一张，加主理人与每名团员各一张
- Prompt 必须**从对应 MD 的正文里提取特征**来拼，不要套通用模板；同一团队的风格锚定词与背景色调要一致

超过 500KB 或尺寸不对时压一下（**生成图直接缩放到 512 会带着右下角生成标和不对称留白，务必带上 `--center --clean`**）：

```bash
# 居中裁切 + 清掉右下角生成标 + 缩到 512×512、压到 ≤500KB
python scripts/prepare_avatar.py <专家目录> --center --clean

# 只想看会怎么处理，不落盘
python scripts/prepare_avatar.py <专家目录> --center --clean --dry-run

# 保留原图另存一份（默认原地覆盖）
python scripts/prepare_avatar.py <图片...> --center --clean --out <输出目录>
```

| 开关 | 作用 |
|---|---|
| `--center` | 按圆角方块的真实边界取正方形居中裁切，四边等距 |
| `--clean` | 抹掉右下角的「AI生成 / WORKBUDDY」标（自动检测，没有就不动） |
| `--out <目录>` | 输出到别处，原图保留 |
| `--size` / `--max-kb` | 目标边长 / 体积上限，默认 512 / 500 |

细节见 `references/avatar-spec.md`。

### Step 3 · 填内容

把骨架里的 `[TODO]` **全部**替换掉，一点不剩（残留占位符会被校验判 P0）：

- `.codebuddy-plugin/plugin.json` —— 展示字段：`displayName` / `profession` / `displayDescription` / `categoryId` / `tags` / `quickPrompts` / `defaultInitPrompt` / `avatar` / `author`
- `agents/*.md` —— 角色定义、核心能力、工作流程、输出规范、注意事项
- `README.md` —— 能力边界

写 plugin.json 前读 `references/expert-spec.md`（字段约束 + 模板）；写 Agent MD 前读 `references/agent-md-spec.md`。

**用户给的是资料而不是需求时**（文档、流程、提示词、代码），按其内容转化：

| 资料里的内容 | 变成什么 | 放哪 |
|---|---|---|
| 角色描述、人设 | Agent MD 的角色定义与核心能力 | `agents/<name>.md` |
| 工作流程、操作步骤 | Agent MD 的工作流程章节 | `agents/<name>.md` |
| 输出格式要求 | Agent MD 的输出规范章节 | `agents/<name>.md` |
| API 文档、字段定义、知识库 | 技能 + references | `skills/<skill>/references/` |
| 可执行脚本 | 技能里的脚本 | `skills/<skill>/scripts/` |
| 流程模板、报告模板 | 模板文件 | `templates/` |
| 通用 CLI 工具 | 插件可执行目录 | `bin/` |
| 多角色分工 | Team 型主理人 + 各团员 MD | `agents/` |
| 示例对话 | quickPrompts + defaultInitPrompt | `plugin.json` |

转化质量要求：不丢信息、按标准结构重排、专业术语原样保留、大段资料放 `references/` 而不是塞进 Agent MD 正文。

### Step 4 · 校验

```bash
python scripts/validate_expert.py <专家目录>          # 人读报告
python scripts/validate_expert.py <专家目录> --json    # 机器读
python scripts/validate_expert.py <专家目录> --hide-p2 # 只看要命的
```

同类问题自动聚合（不会逐行刷屏）。退出码：`0` 通过 / `1` 有 P1 / `2` 有 P0。

| 级别 | 含义 | 典型命中 |
|------|------|----------|
| **P0 阻断** | 专家装了也不能用 | 缺 plugin.json、`name` 不是 kebab-case 或与目录名不符、`agents` 文件不存在、`agentName` 与文件名不匹配、Agent MD 缺 frontmatter、残留 `[TODO]`、Team 型缺 `teamInfo` / 无 `lead` |
| **P1 警告** | 上架或功能受影响 | 缺展示字段、`tags`/`quickPrompts` 不是 3 条、`defaultInitPrompt` 与 `quickPrompts[0]` 不一致、`categoryId` 不在枚举、头像缺失或超 500KB、Agent MD 声明了 `tools` |
| **P2 知情** | 建议优化 | 未注册、缺 `author`、缺 `README.md`、缺 `keywords`、头像不是 512×512、`displayDescription` 字数偏离 40-50 |

### Step 5 · 安装（生成流程的必做步骤）

```bash
python scripts/install_expert.py <专家目录>            # 校验 + 注册
python scripts/install_expert.py <专家目录> --dry-run   # 只看会改什么
python scripts/install_expert.py <专家目录> --force     # 有 P1 但确认无碍
```

这一步把专家写进 `my-experts/.codebuddy-plugin/marketplace.json` ——
`my-experts` 是 directory 型市场，**写进清单就等于安装完成**，不需要改 `settings.json`。

- **P0 一律中止**；P1 默认也中止，除非加 `--force`。
- 同名专家已存在时同样要走这一步（幂等更新），保证它可用。
- 装完告诉用户：去专家中心「我的专家」查收，未出现就重启会话。

### Step 6 · 打包（要分发或上架时才做）

```bash
# 本机包：发给同事手动安装 / 本机存档
python scripts/pack_plugin.py <专家目录> --out <输出目录>

# 上架 open.workbuddy.cn —— 专家：插件形态（plugin.json + agents/）
python scripts/pack_plugin.py <专家目录> --platform --out <输出目录>

# 上架 open.workbuddy.cn —— 技能：直接是技能目录包，不需要 --platform
python scripts/pack_plugin.py <技能目录> --out <输出目录>

# 平台报「不接受顶层目录」时
python scripts/pack_plugin.py <专家目录> --platform --flat-root --out <输出目录>

# 只想看会打进哪些文件
python scripts/pack_plugin.py <专家目录> --dry-run
```

打包专家包时会先自动跑一次校验，有 P0（或有 P1 且没加 `--force`）就中止。

**两条上传线连包结构都不一样**（详见 `references/open-platform.md` 第〇节）：

| 打包对象 | 上传包形态 | 平台校验什么 | 本机安装到 |
|---|---|---|---|
| **技能**（有 `SKILL.md`） | **技能目录**：`<技能名>/SKILL.md` + `references/` + `scripts/` + `templates/` | `SKILL.md` 的 frontmatter（`description_zh` / `description_en` / `version` / `author` 必填） | `~/.workbuddy/skills/` |
| **专家**（有 `agents/*.md`） | **插件**：`plugin.json` + `agents/` | `.codebuddy-plugin/plugin.json`（`expertType` / `displayName` / `categoryId`…） | `plugins/marketplaces/my-experts/plugins/` |

`pack_plugin.py` 自动识别类型：技能产出**技能目录包**，专家产出**插件形态包**。

> **本技能自己是技能** —— 上传时用 `pack_plugin.py .` 默认产出的技能目录包即可，
> **不要**给它合成 `plugin.json`、**不要**套 `skills/` 子目录 —— 平台在技能目录根找不到
> `SKILL.md`，会直接报「**压缩包缺少 SKILL.md 文件**」。只有它**产出**的专家才走插件形态。

上传形态与常见报错见 `references/open-platform.md`。

## 三、命令速查

| 目的 | 命令 |
|------|------|
| 建 Agent 型骨架 | `python scripts/new_expert.py <name> --type agent` |
| 建 Team 型骨架 | `python scripts/new_expert.py <name> --type team --member a --member b` |
| 带字段一条命令生成 | `python scripts/new_expert.py <name> --type agent --meta meta.json` |
| 校验 | `python scripts/validate_expert.py <dir>` |
| 安装 / 重新注册 | `python scripts/install_expert.py <dir>` |
| 压头像 / 图标 | `python scripts/prepare_avatar.py <dir> --center --clean` |
| 打本机包 | `python scripts/pack_plugin.py <dir> --out <out>` |
| 打**专家**上架包（插件形态） | `python scripts/pack_plugin.py <专家目录> --platform --out <out>` |
| 打**技能**上传包（技能目录） | `python scripts/pack_plugin.py <技能目录> --out <out>` |
| 环境自检 | `python scripts/setup.py` |

## 四、目录说明

- `scripts/` —— 全部执行逻辑（`_common.py` 是被各脚本 import 的共用库，不单独调用）
- `references/` —— 按需加载：`expert-spec.md`（plugin.json 字段与分类）、`agent-md-spec.md`（Agent MD 结构）、`avatar-spec.md`（头像与 prompt 构建）、`open-platform.md`（打包上传形态与排错）
- `templates/` —— Agent / 主理人 / 团员三种 MD 骨架（`agent.md`、`team-lead.md`、`team-member.md`），`new_expert.py` 会直接读取

核心流程只用标准库。Pillow 仅在压缩头像时用到，属于可选依赖：`python scripts/setup.py --install-pillow`。

## 五、常见坑

1. **生成到了别的地方** —— 专家必须落在 `~/.workbuddy/plugins/marketplaces/my-experts/plugins/`，放别处专家中心扫不到。`new_expert.py` 默认就是这里，别为了「看着方便」改 `--out`。
2. **只建目录不注册就收工** —— 专家中心不会出现它。注册（`install_expert.py`）是生成流程的一部分。
3. **`name` / `agentName` / 目录名 / MD 文件名四者不一致** —— 它们是同一个标识的四种写法，任何一处对不上都会导致专家加载不到。改名只能重建，不支持原地改。
4. **占位符没替换干净** —— `[TODO]` 会被判 P0 并阻断注册。别只改 plugin.json，`agents/*.md` 和 README 也要清。
5. **`tags` 写顺手写了 5 个** —— 固定 3 个，多了要替换而不是追加。
6. **`defaultInitPrompt` 和 `quickPrompts[0]` 文案不一致** —— 二者必须是同一句话，规范要求。
7. **Agent MD 里声明 `tools`** —— 规范明确禁止，写了不生效还会被校验拦下。
8. **主理人文件名用 `team-lead.md`** —— 必须带团队前缀（`my-team-team-lead.md`），否则多个专家团会互相覆盖。
9. **Team 型的 `profession` 与 `displayName` 不一致** —— 规范要求二者相同。
10. **把技能按插件形态上传** —— 打成 `skills/<技能名>/SKILL.md` 再传，平台是在**技能目录根**找 SKILL.md，找不到就直接报「**压缩包缺少 SKILL.md 文件**」。技能上传包 = 技能目录本身，`pack_plugin.py` 默认产出的就是。
11. **改了内容没升 `version`** —— 插件按版本号判断更新，不升版本已安装的用户看不到变化。
12. **头像超 500KB 直接塞进去** —— 上架会被拦。生成时按 1024×1024 出图，再用 `prepare_avatar.py` 压到 512×512。
13. **把大段知识库塞进 Agent MD 正文** —— 正文会被完整读进上下文，塞多了会挤掉真正有用的信息。放 `references/`，在正文里写明什么时候读。
14. **修改前没先读原文件** —— 只改用户要求改的部分，重写整个文件会把已有内容丢掉。
15. **两条上传线串用** —— 技能传成了插件形态（报「缺少 SKILL.md」），或专家传成了技能目录包（报「缺少 plugin.json」）。**技能传目录，专家传插件。** 分类也别串：技能写 frontmatter 的 `category`，专家写 `categoryId`（数字枚举）。
16. **技能包按专家的位置装** —— 技能解压到 `~/.workbuddy/skills/<技能名>/`，专家才放 `plugins/marketplaces/my-experts/plugins/`。技能放到 marketplaces 下不会生效。
17. **技能 frontmatter 缺必填字段** —— 上传要求 `description` / `description_zh` / `description_en` / `version` / `author` 五项齐全，缺一个平台就报必填缺失。
18. **技能包里出现三级目录** —— 平台只接受「技能根/二级目录/文件」，模板目录里再嵌套一层就会被判「目录层级超限」。模板文件一律平铺在 `templates/` 下。
19. **生成图直接缩放当图标** —— ImageGen 出的是「1024×1024 圆角方块 + 外圈留白」，右下角还带生成标。整图缩放会带着标和不对称留白；随手按固定框硬切（如 `(0,0,900,900)`）会**一边内容被截、另一边留白**。统一走 `prepare_avatar.py --center --clean`。

## 变更记录

### v1.3.0

- `prepare_avatar.py` 新增 `--center` 与 `--clean`，并支持 `--out` 另存：
  - `--center`：按圆角方块真实边界取正方形居中裁切。此前只做整图缩放，主体偏一侧时留白不对称。
  - `--clean`：抹掉 ImageGen 在右下角打的「AI生成 / WORKBUDDY」标 —— 该标落在圆角方块**外侧**背景上，
    用周围背景平滑重建即可，不碰主体；自动检测，没有就不动。
  - 修参数解析：`--size 512` 里的 `512` 会被当成图片路径，带值开关现在会把值一起跳过。
- 新增坑 19：生成图直接缩放/固定框硬切当图标会「一边被截一边留白」，统一走 `--center --clean`。

### v1.2.1

- 修技能包层级：模板从 `templates/agent-md/` 平铺到 `templates/`，平台只接受「技能根/二级目录/文件」。

### v1.2.0

**纠正一处根本性认知错误**：技能**上传开放平台不需要 `.codebuddy-plugin/plugin.json`**。

- 官方要求的技能上传包就是**技能目录本身**：`{skill-name}/SKILL.md` + `references/` + `scripts/` + `templates/`。
  此前按插件形态打成 `skills/<技能名>/SKILL.md`，平台在技能目录根找不到 SKILL.md，
  实测报「**压缩包缺少 SKILL.md 文件**」。
- `pack_plugin.py` 打技能时不再合成 `plugin.json`、不再套 `skills/` 子目录 ——
  技能一律产出技能目录包，加不加 `--platform` 都一样（技能没有「插件形态的上传包」）。
- 「压缩包缺少 .codebuddy-plugin/plugin.json」是**专家 / 插件**那条上传线的报错，
  这条认知此前被错套在技能上。
- `references/open-platform.md` 补上官方技能基础结构、frontmatter 必填字段表
  （`description` / `description_zh` / `description_en` / `version` / `author`），
  并把「两条上传线」改为**形态差异**（技能传目录、专家传插件）而不是字段差异。

### v1.1.0

理清「技能上传规范」与「专家上传规范」的边界——本技能**自己上架走技能规范**，它**产出的专家走上架专家规范**，两条线不复用字段。

- `_plugin_json_from_skill` 补 `category` 独立字段（技能规范的展示分类）。原先只把它当 keywords 的一项，导致平台展示位没有分类。
- 修掉一处会误导使用者的输出：打**技能**包时提示的安装位置写成了专家的 `plugins/marketplaces/…`。技能要装到 `~/.workbuddy/skills/`，按原提示装不会生效。
- 打包输出改为显式标注「技能上架包 / 专家上架包」，不再统称「开放平台插件包」。
- 触发词剥离规则与 skill-generator 的 `pack_skill.py` 统一（原先只认「当用户说」，`也适用于…` 一类整句会残留在市场文案里），并统一 keywords 取词规则——现在同一个技能用哪个打包器产出的清单完全相同。
- `references/open-platform.md` 新增第〇节：两套上传规范的字段对照表（含 `category` vs `categoryId` 这个最大混淆点）。

### v1.0.0

首个版本：生成 / 校验 / 安装 / 打包专家包（Agent 型、Team 型），技能目录可打包上架。

## References

- `references/expert-spec.md` —— 专家包规范：目录结构、plugin.json 全字段、12 类行业分类、Agent/Team 模板、11 条铁律
- `references/agent-md-spec.md` —— Agent MD 规范：frontmatter、普通 Agent / 主理人 / 团员正文结构、写作质量要求
- `references/avatar-spec.md` —— 头像规范：硬性要求、prompt 构建、团队风格统一、背景色调映射
- `references/open-platform.md` —— 开放平台打包与上传：**技能 / 专家两条上传线的形态差异**（`{skill-name}/SKILL.md` vs 插件包）、技能 frontmatter 必填字段、插件目录结构、路径规则、marketplace.json、常见报错对照
