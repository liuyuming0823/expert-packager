# 专家包规范（open.workbuddy.cn / 专家中心）

> 什么时候读：生成或修改 plugin.json 的展示字段时、不确定某个字段是否必填时、上架被平台打回时。

## 一、专家就是插件

WorkBuddy 没有独立的「专家文件格式」。**专家包 = 一个普通插件包 + `agents/` 目录 + 一组展示字段。**

```
<expert-name>/
├── .codebuddy-plugin/
│   └── plugin.json          # 插件清单，平台校验的就是它
├── agents/                  # ★ 有它 + expertType 才是专家
│   ├── <expert-name>.md     # Agent 型：主 Agent
│   └── <team>-team-lead.md  # Team 型：主理人（文件名必须带团队前缀）
├── avatars/                 # 头像，512×512 PNG/JPG，≤500KB
├── skills/                  # 可选：专家自带的技能
├── README.md                # 建议有
└── bin/                     # 可选：可执行文件，启用后加入 PATH
```

**安装目录是固定的**：`~/.workbuddy/plugins/marketplaces/my-experts/plugins/<expert-name>/`
（配置根目录由 `WORKBUDDY_CONFIG_DIR` 决定，未设置时为 `~/.workbuddy`。）

`my-experts` 是 **directory 型市场**，`installLocation` 就指向该目录。所以：

> **把专家包放进去 + 写进 `my-experts/.codebuddy-plugin/marketplace.json`，就等于安装完成。**
> 不需要改 `settings.json` 的 `enabledPlugins`——那是第三方插件市场的机制。

生成到其他目录的专家**专家中心检测不到**，必须拒绝并说明原因。

## 二、plugin.json 字段

### 基础字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `name` | string | ✅ | kebab-case，**必须等于目录名**，也是技能命名空间前缀 |
| `version` | string | ✅ | 语义化版本 `MAJOR.MINOR.PATCH` |
| `description` | string | ✅ | 英文一句话描述，会进市场清单 |
| `author` | `{name, email}` | 建议 | 归属信息 |
| `license` / `homepage` / `repository` | string | 可选 | — |
| `keywords` | string[] | 建议 | 检索标签，影响开放平台命中 |

### 类型字段

| 字段 | 说明 |
|------|------|
| `expertType` | `"agent"`（单角色）或 `"team"`（多角色协作）。**按实际结构判断，不可随意指定** |
| `agentName` | 主 Agent 名 = `agents/` 下 MD 文件名（不含 `.md`）。**必须有业务语义**，不能叫 `team-lead` |
| `teamInfo` | Team 型必填：`{leadAgent, memberAgents[]}`。`memberAgents` **不含**主理人 |

### 展示字段（上架与专家中心必需）

| 字段 | 类型 | 约束 |
|------|------|------|
| `displayName` | `{en, zh}` | 卡片标题下的人名 / 团队名 |
| `profession` | `{en, zh}` | 卡片标题的「职业」。**Team 型必须与 displayName 一致** |
| `displayDescription` | `{en, zh}` | 能力介绍。**中文 40-50 字**，突出核心能力 |
| `avatar` | string | 相对路径，如 avatars/expert.png（由生图流程产出的运行时文件） |
| `categoryId` | string | 必须取自下方枚举，不可自造 |
| `defaultInitPrompt` | `{en, zh}` | 首次对话引导语。**必须等于 `quickPrompts[0]`** |
| `tags` | `{en, zh}[]` | 擅长领域标签，**固定 3 个** |
| `quickPrompts` | `{en, zh}[]` | 推荐提问，**固定 3 个** |
| `plugin` | string | 值与 `name` 一致 |

### Team 专用

| 字段 | 说明 |
|------|------|
| `members[]` | 每项 `{id, displayName, profession, avatar, role}`；`role` ∈ `lead` / `member` |

- **主理人也必须在 `members` 里**，`role` 为 `"lead"`
- `id` 用 Agent ID（MD 文件名去掉 `.md`）
- 主理人的头像文件名建议 `avatars/<team>-team-lead.png`

## 三、行业分类（categoryId）

判定优先级：① 主要产出物属于哪个领域 → ② 服务对象是谁 → ③ 跨领域时取最核心的一个。

| categoryId | 名称 | 典型场景 |
|---|---|---|
| `01-ProductDesign` | 产品设计 | UI/UX、产品规划、原型、交互 |
| `02-Engineering` | 技术工程 | 编程开发、架构、DevOps、技术选型 |
| `03-GameSpatial` | 游戏空间 | 游戏开发、3D、虚拟现实 |
| `04-DataAI` | 数据智能 | 数据分析、机器学习、大模型、BI |
| `05-MarketingGrowth` | 营销增长 | 品牌、增长、投放、SEO |
| `06-ContentCreative` | 内容创作 | 文案、视频脚本、创意、翻译 |
| `07-SalesCommerce` | 销售商务 | 销售策略、商务谈判、客户管理、电商 |
| `08-FinanceInvestment` | 金融投资 | 投资分析、财务、风控、量化 |
| `09-OperationsHR` | 运营人力 | 项目运营、HR、组织管理、培训 |
| `10-ProjectQuality` | 项目质量 | 项目管理、质量保障、测试、流程优化 |
| `11-SecurityCompliance` | 法务安全 | 信息安全、合规、法务、隐私 |
| `12-IndustryConsultant` | 行业顾问 | 跨行业咨询、战略规划、不属以上任何一类 |

## 四、模板

### Agent 型

```json
{
  "name": "kebab-case-name",
  "version": "1.0.0",
  "description": "English one-line description",
  "author": { "name": "Author", "email": "" },
  "agents": ["./agents/kebab-case-name.md"],
  "skills": ["./skills/my-skill"],

  "expertType": "agent",
  "agentName": "kebab-case-name",

  "displayName":  { "en": "English name", "zh": "中文名" },
  "profession":   { "en": "English profession", "zh": "中文职业头衔" },
  "displayDescription": { "en": "...", "zh": "中文 40-50 字" },
  "avatar": "avatars/expert.png",
  "categoryId": "02-Engineering",
  "plugin": "kebab-case-name",
  "defaultInitPrompt": { "zh": "与 quickPrompts[0].zh 一致", "en": "same as quickPrompts[0].en" },
  "tags": [
    { "en": "Tag1", "zh": "标签1" },
    { "en": "Tag2", "zh": "标签2" },
    { "en": "Tag3", "zh": "标签3" }
  ],
  "quickPrompts": [
    { "en": "Prompt1", "zh": "提示词1" },
    { "en": "Prompt2", "zh": "提示词2" },
    { "en": "Prompt3", "zh": "提示词3" }
  ]
}
```

> 没有自带技能时**省略 `skills` 字段**，不要留空数组。

### Team 型（差异部分）

```json
{
  "agents": [
    "./agents/my-team-team-lead.md",
    "./agents/member-a.md",
    "./agents/member-b.md"
  ],
  "expertType": "team",
  "agentName": "my-team-team-lead",
  "teamInfo": {
    "leadAgent": "my-team-team-lead",
    "memberAgents": ["member-a", "member-b"]
  },
  "profession": { "en": "My Team", "zh": "我的专家团" },
  "members": [
    {
      "id": "my-team-team-lead",
      "displayName": { "en": "Lead", "zh": "主理人" },
      "profession": { "en": "Lead", "zh": "主理人职业" },
      "avatar": "avatars/my-team-team-lead.png",
      "role": "lead"
    },
    {
      "id": "member-a",
      "displayName": { "en": "A", "zh": "成员A" },
      "profession": { "en": "Analyst", "zh": "分析师" },
      "avatar": "avatars/member-a.png",
      "role": "member"
    }
  ]
}
```

## 五、铁律

1. `name` kebab-case，且 **= 目录名 = `agentName` = agents 下 MD 文件名**
2. `agents` 是**路径数组**，形如 `["./agents/x.md"]`，所有路径相对插件根、以 `./` 开头
3. `tags` 与 `quickPrompts` **各固定 3 条**，多了必须替换或删除，不能新增
4. `defaultInitPrompt` 必须与 `quickPrompts[0]` 文案一致
5. `displayDescription.zh` 控制在 **40-50 字**
6. Agent MD 的 frontmatter **禁止声明 `tools`**——工具权限由系统统一分配
7. Team 型的**主理人文件名不能是通用的 `team-lead.md`**，必须带团队前缀
8. Team 型 `profession` 与 `displayName` 保持一致
9. 同一团队的头像**画风与背景色调统一**
10. **改动 `name` / `agentName` / 目录名 / MD 文件名 = 换一个专家**，不支持原地改名；要改名只能重建
11. 目标目录已存在同名专家时，**仍要走一遍校验 + 注册**，保证它可用
