# expert-packager · 专家生成器

把「手写一堆 JSON 和 Markdown、再摆到对的目录、再打成 zip」压成一条命令。

WorkBuddy 专家包（Agent 型 / Team 型）的 **生成 → 校验 → 安装 → 打包** 全流程工具，产出符合 [open.workbuddy.cn](https://open.workbuddy.cn) 开放平台规范的专家包与插件包。生成后自动注册到本机专家中心，开箱即用。

## 解决什么问题

- **字段和路径容易摆错** —— 手写 `plugin.json` + `agents/*.md` 时，专家中心经常扫不到
- **标识必须四处一致** —— `name` / `agentName` / 目录名 / MD 文件名是同一个标识的四种写法，手改必错
- **头图不合规** —— 尺寸超标、带生成水印，平台直接拒收
- **打包形态搞混** —— 专家上架走插件形态包，技能上架直接传技能目录包，两者完全不同

## 安装

克隆到 WorkBuddy 技能目录即可被识别：

```bash
git clone https://github.com/liuyuming0823/expert-packager.git ~/.workbuddy/skills/expert-packager
```

Windows 路径：`%USERPROFILE%\.workbuddy\skills\expert-packager`

## 快速开始

```bash
cd ~/.workbuddy/skills/expert-packager

# 建 Agent 型骨架（默认直接落到本机专家中心）
python scripts/new_expert.py my-expert --type agent

# 建 Team 型骨架（--member 可重复）
python scripts/new_expert.py my-team --type team --member a --member b

# 校验 / 重新注册
python scripts/validate_expert.py <dir>
python scripts/install_expert.py <dir>

# 头像压到 512×512 且 ≤500KB
python scripts/prepare_avatar.py <dir> --center --clean

# 打包
python scripts/pack_plugin.py <dir> --out <out>              # 本机包 / 技能上传包
python scripts/pack_plugin.py <专家目录> --platform --out <out>  # 专家上架（插件形态）

# 环境自检
python scripts/setup.py
```

## 命令速查

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

## 目录结构

```
expert-packager/
├── SKILL.md                  # 技能主文档（工作流 + 命令 + 坑）
├── references/
│   ├── expert-spec.md        # plugin.json 字段与分类
│   ├── agent-md-spec.md      # Agent MD 结构规范
│   ├── avatar-spec.md        # 头像与 prompt 构建
│   └── open-platform.md      # 打包上传形态与排错
├── scripts/
│   ├── _common.py            # 共用库（路径 / frontmatter / 分级报告）
│   ├── new_expert.py         # 生成骨架（默认直接安装到专家中心）
│   ├── validate_expert.py    # 校验
│   ├── install_expert.py     # 注册到 marketplace.json = 安装
│   ├── pack_plugin.py        # 打包（按目录类型自动分流专家 / 技能）
│   ├── prepare_avatar.py     # 头像处理
│   └── setup.py              # 环境自检
└── templates/
    ├── agent.md              # Agent 型骨架
    ├── team-lead.md          # 专家团主理人骨架
    └── team-member.md        # 专家团团员骨架
```

## 依赖

核心流程只用 Python 标准库。Pillow 仅在压缩头像时用到，属可选依赖：

```bash
python scripts/setup.py --install-pillow
```

## 常见坑

1. **生成到了别的地方** —— 专家必须落在 `~/.workbuddy/plugins/marketplaces/my-experts/plugins/`，放别处专家中心扫不到。`new_expert.py` 默认就是这里，别为「看着方便」改 `--out`。
2. **只建目录不注册就收工** —— 专家中心不会出现它，注册（`install_expert.py`）是生成流程的一部分。
3. **四处标识不一致** —— `name` / `agentName` / 目录名 / MD 文件名任何一处对不上都会加载不到，改名只能重建。
4. **上传形态搞混** —— 技能上架传技能目录包（顶层 `{skill-name}/SKILL.md`），专家上架才用 `--platform` 出插件形态包。

## 相关项目

- [ym-skill-generator](https://github.com/liuyuming0823/ym-skill-generator) —— 配套的**技能**生成器：按需求生成技能骨架、体检脱敏、打包上架

这对工具的分工是：**expert-packager 管「专家」，ym-skill-generator 管「技能」**，两条上传规范不复用，别混。

