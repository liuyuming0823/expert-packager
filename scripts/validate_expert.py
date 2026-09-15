"""校验 WorkBuddy 专家包是否符合开放平台规范。

    python validate_expert.py <专家目录> [--json] [--hide-p2]

退出码：0 通过 / 1 有 P1 / 2 有 P0
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    CATEGORIES,
    KEBAB_RE,
    TODO_RE,
    Report,
    char_count,
    find_marketplace_json,
    load_plugin_json,
    normalize_path,
    read_frontmatter,
    use_utf8_stdout,
)

AGENT_REQUIRED = ("displayName", "profession", "displayDescription", "categoryId")
EXPORT_FIELDS = ("displayName", "profession", "displayDescription", "avatar",
                 "categoryId", "defaultInitPrompt", "tags", "quickPrompts", "plugin")


def _pair_ok(value) -> bool:
    return isinstance(value, dict) and bool(value.get("zh")) and bool(value.get("en"))


def _png_size(path: Path):
    """从 PNG 头里读出宽高，不依赖 Pillow。"""
    try:
        head = path.read_bytes()[:32]
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def validate_expert(expert_dir) -> Report:
    root = Path(expert_dir).expanduser().resolve()
    rep = Report(f"专家包校验 · {root.name}")

    if not root.is_dir():
        rep.add("P0", "目录不存在", str(root))
        return rep

    # ── 1. 清单存在性与基础字段 ────────────────────────────────
    manifest = root / ".codebuddy-plugin" / "plugin.json"
    if not manifest.is_file():
        rep.add("P0", "缺 .codebuddy-plugin/plugin.json", "专家包必须带插件清单")
        return rep

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        rep.add("P0", "plugin.json 不是合法 JSON", str(exc))
        return rep
    if not isinstance(data, dict):
        rep.add("P0", "plugin.json 顶层不是对象", manifest.name)
        return rep

    name = data.get("name") or ""
    if not name:
        rep.add("P0", "缺 name 字段", "plugin.json")
    elif not KEBAB_RE.match(name):
        rep.add("P0", "name 必须是 kebab-case", f"name={name!r}")
    elif name != root.name:
        rep.add("P0", "name 与目录名不一致", f"name={name!r}  目录={root.name!r}")

    expert_type = data.get("expertType")
    if expert_type not in ("agent", "team"):
        rep.add("P0", "缺 expertType 或取值非法", f"expertType={expert_type!r}（只能 agent / team）")

    # ── 2. agents 声明与文件 ──────────────────────────────────
    agents = data.get("agents")
    if not isinstance(agents, list) or not agents:
        rep.add("P0", "agents 必须是非空数组", '形如 ["./agents/<name>.md"]')
        agents = []

    agent_files = []
    for raw in agents:
        rel = normalize_path(str(raw))
        target = root / rel
        if not target.is_file():
            rep.add("P0", "agents 声明的文件不存在", rel)
            continue
        agent_files.append(target)
        if not rel.startswith("agents/") or not rel.endswith(".md"):
            rep.add("P2", "agents 路径不符合约定", f"{rel}（建议 ./agents/<name>.md）")

    agent_name = data.get("agentName") or ""
    if not agent_name:
        rep.add("P0", "缺 agentName 字段", "agentName = agents 下 MD 文件名（不含 .md）")
    else:
        if not KEBAB_RE.match(agent_name):
            rep.add("P1", "agentName 建议用 kebab-case", agent_name)
        if agent_name in ("team-lead", "lead", "main", "agent"):
            rep.add("P1", "agentName 必须有业务语义", f"{agent_name!r} 过于通用")
        if agent_files and (root / "agents" / f"{agent_name}.md") not in agent_files:
            rep.add("P0", "agentName 与 agents 文件名不匹配",
                    f"agentName={agent_name!r}，agents={[p.name for p in agent_files]}")

    # ── 3. Agent MD 自身规范 ─────────────────────────────────
    for path in agent_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = read_frontmatter(text)
        rel = path.relative_to(root).as_posix()
        if not fm:
            rep.add("P0", "Agent MD 缺 frontmatter", rel)
            continue
        if not fm.get("name"):
            rep.add("P1", "Agent MD frontmatter 缺 name", rel)
        elif fm["name"] != path.stem:
            rep.add("P1", "Agent MD 的 name 与文件名不一致", f"{rel} → name={fm['name']!r}")
        if not fm.get("description"):
            rep.add("P1", "Agent MD frontmatter 缺 description", rel)
        for key in ("displayName", "profession"):
            if not fm.get(key):
                rep.add("P1", f"Agent MD frontmatter 缺 {key}", rel)
        if "tools" in fm:
            rep.add("P1", "Agent MD frontmatter 禁止声明 tools", rel)
        body = text.split("\n---", 1)[-1]
        if len(body.strip()) < 200:
            rep.add("P1", "Agent MD 正文过短", f"{rel}（{len(body.strip())} 字符）")
        if "SendMessage" not in body and expert_type == "team" and path.stem != agent_name:
            rep.add("P2", "团员 MD 未写明 SendMessage 回传要求", rel)

    # ── 4. 展示字段（上架 / 专家中心必需）─────────────────────
    for field in EXPORT_FIELDS:
        if field not in data:
            rep.add("P1", f"缺展示字段 {field}", "plugin.json")

    for field in ("displayName", "profession", "displayDescription"):
        value = data.get(field)
        if value is not None and not _pair_ok(value):
            rep.add("P1", f"{field} 必须是 {{en, zh}} 且都不为空", repr(value))

    desc = (data.get("displayDescription") or {}).get("zh", "") if isinstance(
        data.get("displayDescription"), dict) else ""
    if desc:
        n = char_count(desc)
        if n < 30 or n > 60:
            rep.add("P1", "displayDescription 中文字数超范围", f"{n} 字（规范 40-50 字）")
        elif n < 40 or n > 50:
            rep.add("P2", "displayDescription 建议 40-50 字", f"{n} 字")

    cat = data.get("categoryId")
    if cat and cat not in CATEGORIES:
        rep.add("P1", "categoryId 不在平台枚举内", f"{cat!r}（见 references/expert-spec.md）")

    for field in ("tags", "quickPrompts"):
        value = data.get(field)
        if value is None:
            continue
        if not isinstance(value, list):
            rep.add("P1", f"{field} 必须是数组", repr(type(value).__name__))
            continue
        if len(value) != 3:
            rep.add("P1", f"{field} 必须固定 3 条", f"当前 {len(value)} 条")
        for item in value:
            if not _pair_ok(item):
                rep.add("P1", f"{field} 每条都要有 zh 与 en", repr(item)[:80])
                break

    prompts = data.get("quickPrompts")
    init = data.get("defaultInitPrompt")
    if isinstance(prompts, list) and prompts and _pair_ok(init):
        if init.get("zh") != prompts[0].get("zh"):
            rep.add("P1", "defaultInitPrompt 须等于 quickPrompts[0]", "两者中文文案不一致")

    if data.get("plugin") and data["plugin"] != name:
        rep.add("P1", "plugin 字段必须与 name 一致", f"plugin={data['plugin']!r}")

    # ── 5. 头像 ──────────────────────────────────────────────
    avatar = data.get("avatar")
    if avatar:
        avatar_path = root / normalize_path(str(avatar))
        if not avatar_path.is_file():
            rep.add("P1", "avatar 指向的文件不存在", normalize_path(str(avatar)))
        else:
            size_kb = avatar_path.stat().st_size / 1024
            if size_kb > 500:
                rep.add("P1", "avatar 超过 500KB", f"{size_kb:.0f} KB")
            if avatar_path.suffix.lower() == ".png":
                dim = _png_size(avatar_path)
                if dim and dim != (512, 512):
                    rep.add("P2", "avatar 建议 512×512", f"当前 {dim[0]}×{dim[1]}")

    # ── 6. Team 型专属 ───────────────────────────────────────
    if expert_type == "team":
        info = data.get("teamInfo")
        if not isinstance(info, dict):
            rep.add("P0", "Team 型缺 teamInfo", '{"leadAgent": ..., "memberAgents": [...]}')
        else:
            if info.get("leadAgent") != agent_name:
                rep.add("P0", "teamInfo.leadAgent 必须等于 agentName",
                        f"leadAgent={info.get('leadAgent')!r}")
            members = data.get("members")
            if not isinstance(members, list) or not members:
                rep.add("P0", "Team 型缺 members 数组", "每个成员含 id/displayName/profession/avatar/role")
            else:
                leads = [m for m in members if isinstance(m, dict) and m.get("role") == "lead"]
                if not leads:
                    rep.add("P0", "members 中没有 role=lead 的主理人", "主理人也必须在 members 里")
                for member in members:
                    if not isinstance(member, dict):
                        continue
                    for key in ("id", "displayName", "profession", "avatar", "role"):
                        if not member.get(key):
                            rep.add("P1", "members 成员字段缺失", f"{member.get('id') or '?'} → {key}")
                    if member.get("role") not in ("lead", "member"):
                        rep.add("P1", "members role 取值非法", repr(member.get("role")))
                if len(members) < 2:
                    rep.add("P1", "Team 型至少要有主理人 + 1 名团员", f"当前 {len(members)} 人")
            member_agents = info.get("memberAgents")
            if isinstance(member_agents, list) and agent_name in member_agents:
                rep.add("P0", "teamInfo.memberAgents 不得包含主理人", agent_name)
        if _pair_ok(data.get("profession")) and _pair_ok(data.get("displayName")):
            if data["profession"]["zh"] != data["displayName"]["zh"]:
                rep.add("P1", "Team 型 profession 须与 displayName 一致",
                        f"{data['profession']['zh']!r} vs {data['displayName']['zh']!r}")

    # ── 7. 占位符残留 ────────────────────────────────────────
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".json", ".md", ".txt", ".yaml", ".yml"):
            continue
        if any(part in ("__pycache__", "node_modules") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if TODO_RE.search(text):
            rep.add("P0", "存在未替换的占位符", path.relative_to(root).as_posix())

    # ── 8. 注册状态与杂项 ────────────────────────────────────
    marketplace = find_marketplace_json(root)
    registered = False
    if marketplace:
        doc = json.loads(marketplace.read_text(encoding="utf-8"))
        registered = any(
            isinstance(p, dict) and p.get("name") == name for p in (doc.get("plugins") or [])
        )
    if not registered:
        rep.add("P2", "尚未注册到 marketplace.json", "运行 scripts/install_expert.py 完成安装")

    if not (data.get("author") or {}).get("name"):
        rep.add("P2", "缺 author.name", "建议署名，便于归属")
    if not (root / "README.md").is_file():
        rep.add("P2", "缺 README.md", "建议写明能力边界与使用方式")
    if not isinstance(data.get("keywords"), list) or not data.get("keywords"):
        rep.add("P2", "缺 keywords", "影响开放平台检索命中")

    return rep


def main() -> int:
    use_utf8_stdout()
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    target = next((a for a in args if not a.startswith("-")), None)
    if not target:
        print(__doc__.strip())
        return 0
    as_json = "--json" in args
    hide_p2 = "--hide-p2" in args

    rep = validate_expert(target)
    if as_json:
        print(json.dumps({
            "target": str(Path(target).expanduser()),
            "p0": rep.count("P0"), "p1": rep.count("P1"), "p2": rep.count("P2"),
            "items": [{"level": lv, "rule": r, "detail": d} for lv, r, d in rep.items],
        }, ensure_ascii=False, indent=2))
    else:
        if hide_p2:
            rep.items = [i for i in rep.items if i[0] != "P2"]
        print(rep.render())

    if rep.count("P0"):
        return 2
    if rep.count("P1"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
