# 开放平台打包与上传

> 什么时候读：要把专家/技能上传到 open.workbuddy.cn，或上传被平台打回时。

## 〇、两条上传线：形态根本不同（最容易搞混）

**技能上传 ≠ 专家上传 —— 不只是字段差异，包结构就不是一回事。**

| | **技能** | **专家** |
|---|---|---|
| 上传包形态 | **技能目录** | **插件（plugin）** |
| 顶层结构 | `{skill-name}/SKILL.md` + `references/` + `scripts/` + `templates/` | `<名字>/.codebuddy-plugin/plugin.json` + `<名字>/agents/…` |
| 清单文件 | **不需要** | **必须有** `plugin.json` |
| 分类字段 | frontmatter 的 `category`（字符串） | `categoryId` —— **数字枚举**，如 `02-Engineering` |
| 展示字段 | frontmatter 的 `display_name` / `description_zh` / `description_en` | `displayName` / `profession` / `displayDescription` / `avatar` |
| 交互字段 | 无 | `defaultInitPrompt` / `quickPrompts` / `tags` |
| 本机安装到 | `~/.workbuddy/skills/` | `plugins/marketplaces/my-experts/plugins/` |

> **最常见的错**：把技能按插件形态打成 `skills/<技能名>/SKILL.md` 再上传。
> 平台是在**技能目录根**找 `SKILL.md`，找不到就报「**压缩包缺少 SKILL.md 文件**」。
> 而「压缩包缺少 .codebuddy-plugin/plugin.json」是**专家/插件**那条线的报错，别套到技能上。

一句话：**技能传目录，专家传插件。**

## 一、技能上传：官方要求的技能基础结构

```
{skill-name}/
├── SKILL.md              # ★ 技能定义（必须）
├── references/           # 参考资料（可选）
│   ├── api-spec.md
│   └── examples.md
├── scripts/              # 可执行脚本（可选）
│   ├── fetch-data.js
│   └── transform.py
└── templates/            # 模板文件（可选）
    ├── report.sh
    └── workflow.sh
```

`SKILL.md` = YAML frontmatter + Markdown 正文。**frontmatter 必填字段**：

| 字段 | 必填 | 说明 |
|---|---|---|
| `description` | **是** | 写清用途和触发词 |
| `description_zh` | **是** | 简短中文介绍 |
| `description_en` | **是** | 简短英文介绍 |
| `version` | **是** | 版本号 |
| `author` | **是** | 合作方名称 |
| `name` | 否 | 技能标识 |
| `display_name` / `display_name_en` / `category` | 否 | 展示名称与分类 |
| `allowed-tools` | 否 | 工具白名单（逗号分隔） |
| `disable-model-invocation` | 否 | `true` 则 AI 不会自动触发，只能用户手动调用 |
| `user-invocable` | 否 | `false` 则隐藏菜单，仅供 AI 内部使用 |

子目录约定：

- `references/` —— 在 SKILL.md 中通过 `@references/xxx.md` 引用，AI 执行时按需读作上下文
- `scripts/` —— 在 SKILL.md 中声明调用命令与参数，AI 通过 Bash 执行
- `templates/` —— 可复用模板脚本 / 配置文件（认证会话模板、采集工作流模板等）

**`pack_plugin.py <技能目录>` 默认产出的包就是按这个结构打的，直接传即可。**

### 图标不进包，上架时单独交

技能图标（512×512、PNG/JPG、≤500KB）是**创建技能表单里的一个字段**，
不是 zip 里的文件。所以：

- 图标放在技能目录的 `icons/` 下（`make_icon.py` 的默认输出），
  **打包器一律排除它**，别指望它随 zip 上去；
- 上架时在平台「图标」处单独提交那张图；
- 顺带一提，`__pycache__`、`.git/`、`.gitignore`、`.gitattributes`、`README.md`、
  `LICENSE` 这些同样不进包 —— 技能目录同时是 git 仓库时最容易把仓库元数据一起打进去。

**包只装技能本身。** 仓库的东西、发布用的图，都不该出现在 zip 里。

## 二、产出形态

`pack_plugin.py` 先判断目录类型，技能与专家走**完全不同的**产出逻辑：

| 目录类型 | 判据 | 产出 |
|---|---|---|
| **技能** | 有 `SKILL.md` | **技能目录包**（`<技能名>/SKILL.md` + …）。本机包与上传包是同一个东西 |
| **专家** | 有 `agents/*.md`，且 plugin.json 声明了 `expertType` | 默认 = `<名字>.zip`（本机包）；`--platform` = `<名字>-plugin.zip`（**插件形态**，上传专家用） |
| 通用插件 | 只有 plugin.json | 原样复制 |

技能加不加 `--platform` 产出都一样 —— 技能**没有**「插件形态的上传包」。
别去合成 `plugin.json`、别套 `skills/` 子目录，那只会给自己制造「缺少 SKILL.md」的报错。

> 若确实要把某个技能**作为插件**分发（挂到插件下、进团队 marketplace），
> 用 ym-skill-generator 的 `pack_skill.py <技能目录> --as-plugin` 另打一个插件形态包。
> 那个包**不能**用于开放平台的技能类目上传。

平台若报结构类错误、提示不接受顶层目录，加 `--flat-root` 重打一次。

## 三、插件目录结构（官方规范）

```
<plugin-name>/
├── .codebuddy-plugin/
│   └── plugin.json      ← 只有清单在这里
├── agents/              ← 组件目录都在插件根，不能在 .codebuddy-plugin/ 里面
├── skills/
├── commands/
├── hooks/hooks.json
├── bin/
├── .mcp.json
└── .lsp.json
```

`.codebuddy-plugin/` 同时兼容 `.workbuddy-plugin/` 与 `.claude-plugin/` 命名。

## 四、路径规则

- 所有路径**必须相对插件根、以 `./` 开头**，不能用绝对路径
- 自定义路径会**替换**默认目录：写了 `"agents": ["./x/"]` 就不会再扫描默认的 `agents/`。
  想保留默认目录，把默认目录也列进数组：`["./agents/", "./extras/"]`
- 插件安装后会被复制到版本化缓存，**无法引用插件目录之外的文件**。
  同一市场内的共享文件可以用符号链接（打包时会解引用并复制内容）
- 插件内引用自身文件一律用 `${CODEBUDDY_PLUGIN_ROOT}`，不要写相对路径硬拼

## 五、marketplace.json（团队分发时用）

`<市场根>/.codebuddy-plugin/marketplace.json`：

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Team", "email": "" },
  "plugins": [
    { "name": "my-expert", "source": "./plugins/my-expert", "description": "..." }
  ]
}
```

`source` 支持相对路径、GitHub 简写、Git URL。团队分发时把市场目录放进 Git 仓库，
成员用 `/plugin marketplace add owner/repo` 添加即可。

> `my-experts` 就是一个 directory 型市场，`installLocation` 指向本机目录。
> 专家安装 = 放包 + 写清单，见 `references/expert-spec.md`。

## 六、版本与缓存

缓存键优先级：`plugin.json.version` → marketplace 条目的 `version` → Git commit SHA → `unknown`。

**改了代码但没升 `version`，已安装的用户不会看到更新。** 所以每次分发前记得升版本号并记 CHANGELOG。

## 七、常见报错对照

| 报错 | 原因 | 处理 |
|------|------|------|
| **压缩包缺少 SKILL.md 文件** | 把技能按**插件形态**传了（SKILL.md 被埋在 `skills/<技能名>/` 下） | 改用 `pack_plugin.py <技能目录>` 默认产出的**技能目录包**重传 |
| 压缩包缺少 .codebuddy-plugin/plugin.json 文件 | 这是**专家/插件**那条线的报错：把技能目录包当插件传了 | 专家包必须是含 `plugin.json` + `agents/` 的插件形态 |
| 技能上传报必填字段缺失 | frontmatter 缺 `description_zh` / `description_en` / `version` / `author` | 补齐这 4 个必填（连同 `description`） |
| 平台不接受顶层目录 | 包结构与平台期望不符 | 加 `--flat-root` 重打 |
| 展示位没有分类 | 专家侧该用 `categoryId`（数字枚举），不是 `category` | 专家用 `categoryId: 02-Engineering`；技能在 frontmatter 写 `category` |
| 专家上传后没有中文名 / 头像 / 快捷提问 | 传的是技能目录包（技能本就没有这些字段） | 专家要走插件形态：源目录有 `agents/*.md`，加 `--platform` 打 |
| Invalid JSON syntax / corrupt manifest | plugin.json 语法错 | `python scripts/validate_expert.py <目录>` 先过一遍 |
| name: Required | 清单缺 `name` | 补 kebab-case 的 name |
| Plugin directory not found at path | marketplace 条目的 `source` 指向不存在的目录 | 修正 source |
| 路径错误 / 找不到文件 | 用了绝对路径或越出插件根 | 改成 `./` 开头的相对路径 |
| 组件（agents/commands）缺失 | 组件放在了 `.codebuddy-plugin/` 里面 | 移到插件根 |
| 装了但看不到更新 | `version` 没升 | 升版本号重新打包 |
