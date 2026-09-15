# 头像规范

> 什么时候读：给专家或专家团生成头像时。专家卡片的第一印象全在这里。

## 一、硬性要求

| 项目 | 要求 |
|------|------|
| 格式 | PNG（推荐）或 JPG |
| 尺寸 | 512×512 px，正方形 |
| 大小 | 单张 ≤ 500KB |
| 风格 | 统一漫画 / 插画风，专业自然 |
| 内容 | 符合角色定位，不含违规内容 |

**生成策略**：用 `ImageGen` 生成，`size` 传 `"1024x1024"`（高清大图，展示时会缩到 512×512）。
文件超过 500KB 时用 `scripts/prepare_avatar.py` 压到 512×512。

**后处理必须带 `--center --clean`**：

```bash
python scripts/prepare_avatar.py <专家目录> --center --clean
```

| 开关 | 作用 | 不加会怎样 |
|---|---|---|
| `--center` | 按圆角方块真实边界取正方形居中裁切 | 主体偏一侧时留白不对称；手动按固定框硬切会**一边内容被截、另一边留白** |
| `--clean` | 抹掉右下角的「AI生成 / WORKBUDDY」标 | 生成标直接带上架，观感很差 |

`--clean` 之所以安全，是因为该标落在圆角方块**外侧**的浅色背景上，用周围背景平滑重建即可，不碰图标主体；检测不到就不动。

产出文件数（以下都是**运行时产物**，不入本技能目录）：

- **Agent 型**：1 张 → avatars/expert.png
- **Team 型**：N+1 张 → avatars/<团队名>.png（团队整体）+ 主理人 + 每名团员各一张

## 二、Prompt 怎么拼

**核心原则：每个头像的 prompt 都要从对应的 MD 文件里提取特征，不能套通用模板。**

| 步骤 | 从哪提取 |
|------|----------|
| 角色身份 | MD 标题与首段 |
| 专业特征 | 「核心能力」章节的关键词 → 转成视觉元素 |
| 工作风格 | 「工作流程」与「注意事项」→ 推断气质 |
| 人物属性 | `name` 字段 → 推断性别与基调 |

组装顺序：

```
[风格前缀] + [角色身份] + [外观特征] + [表情气质] + [背景元素] + [质量后缀]
```

| 片段 | 示例 |
|------|------|
| 风格前缀 | `Professional cartoon-style illustration avatar,` |
| 角色身份 | `a female design system document architect` |
| 外观特征 | `wearing stylish glasses, holding a design specification document` |
| 表情气质 | `confident and meticulous expression` |
| 背景元素 | `subtle design tokens and color palette swatches in background` |
| 质量后缀 | `Bust shot, facing forward. Clean simple background. High quality, professional, natural.` |

**示例**（技术分析师）：

```
Professional cartoon-style illustration avatar, a male technical stock market analyst named Marco,
wearing a sharp vest over dress shirt, looking at holographic candlestick charts,
focused and analytical expression with sharp observant eyes,
K-line charts, moving average lines and MACD indicators floating in the background.
Bust shot, facing forward. Clean simple blue-toned background. High quality, professional, natural.
```

## 三、团队头像

**输入来源**：plugin.json 的 `displayDescription` + 主理人 MD 的团队描述。

```
[风格前缀] + [团队场景] + [协作元素] + [成员象征] + [质量后缀]
```

团队头像要体现**协作场景**，不是简单的人物剪影。例如交易分析团队：

```
Professional cartoon-style illustration, a dynamic stock trading analysis team scene,
multiple diverse analysts gathered around a central holographic display showing candlestick charts,
a bull figure and a bear figure debating on opposite sides symbolizing bull-bear debate,
risk gauges and decision dashboards floating around,
warm collaborative atmosphere with focused professional energy.
Clean simple multi-tone gradient background. High quality, professional, team composition.
```

## 四、同一团队画风统一

所有头像共用**固定的风格锚定词**：

- 开头固定：`Professional cartoon-style illustration avatar, consistent art style with warm lighting and soft shadows,`
- 结尾固定：`Bust shot, facing forward. Clean simple {color}-toned background. High quality, professional, natural.`

背景色调按 `categoryId` 取（同一团队全部成员用同一个）：

| categoryId | 背景色调 |
|------------|---------|
| 01-ProductDesign | warm orange-coral |
| 02-Engineering | blue-purple |
| 03-GameSpatial | purple-red gradient |
| 04-DataAI | cyan-teal |
| 05-MarketingGrowth | red-orange |
| 06-ContentCreative | pink-magenta |
| 07-SalesCommerce | golden-amber |
| 08-FinanceInvestment | dark blue with gold accent |
| 09-OperationsHR | navy slate-blue |
| 10-ProjectQuality | green-emerald |
| 11-SecurityCompliance | dark grey-blue |
| 12-IndustryConsultant | deep teal with silver accent |

## 五、执行顺序

1. 逐个读取 `agents/*.md`
2. 从角色定义、核心能力、工作流程里提取特征
3. 按上面的结构拼出每个人物的 prompt
4. Team 型再拼一张团队场景 prompt
5. 统一风格锚定词与背景色调
6. 调 `ImageGen` 逐张生成，`size="1024x1024"`，落盘到专家包的 `avatars/`
7. 重命名成 plugin.json 里声明的文件名
8. 超 500KB 的跑 `python scripts/prepare_avatar.py <专家目录> --center --clean`
9. 确认 `avatars/` 下文件齐全、文件名与 plugin.json 声明一致

> 生成失败时的兜底：在 `README.md` 里列出待手动补充的头像文件名，并附上推荐 prompt。
> 同时提醒用户：自动生成的头像可以手动替换（512×512，PNG/JPG，≤500KB）。

## 六、别搞混：专家头像 vs 技能图标

两者都叫「图片」，规则也像（512×512、PNG/JPG、≤500KB），但**归属完全不同**：

| | 专家头像 | 技能图标 |
|---|---|---|
| 给谁用 | 专家在专家中心的展示图 | 技能在市场上架时的图标 |
| 放哪 | 专家包内 `avatars/`，文件名由 `plugin.json` 的 `avatar` 声明 | 技能目录下 `icons/` |
| 进不进包 | **要进**（专家包必须带，缺了校验会报） | **不进**（打包器一律排除） |
| 怎么提交 | 随专家包一起上传 | 上架时在平台「图标」处**单独**上传 |
| 用哪个脚本 | `prepare_avatar.py --center --clean` | `make_icon.py`（提示词 + 裁切 + 清标 + 压到 512 一步到位） |
| 张数 | Agent 型 1 张；Team 型 N+1 张 | 1 张 |
| 画风 | 人物头像（漫画 / 插画风） | 具象物件的应用图标（简洁几何、居中、可缩到 64px） |

典型误用有两种，都真实出现过：

- 把技能图标塞进技能 zip —— 平台不认，且白占体积。技能图标是**表单里的一个字段**，不是包里的文件。
- 拿 `prepare_avatar.py` 去处理技能图标 —— 它按 `avatars/` 找文件，会找不到；技能图标走 `make_icon.py`。

### 技能图标怎么做

```bash
# ① 提示词（按本技能 SKILL.md 的 display_name / description 拼，贴合技能身份）
python scripts/make_icon.py --prompt

# ② 交给 ImageGen（size 用 1024x1024），生成图回来做后处理
#    默认：居中裁切 + 清右下角生成标 + 缩到 512×512 + 压到 ≤500KB
python scripts/make_icon.py <生成图>            # 落盘到本技能 icons/

# ③ 上传前自查
python scripts/make_icon.py --check icons/*.png
```

图标 prompt 的要点与头像不同：**单一主体、居中、不要文字**，缩小到 64px 仍要能认出来；
不要人物特写，用 1~2 个具象物件表达「这个技能做什么」。
