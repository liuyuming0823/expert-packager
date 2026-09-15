"""生成 WorkBuddy 专家包骨架（Agent 型 / Team 型），默认直接落到专家安装目录。

    python new_expert.py <专家名> --type agent|team [--out 目录] [--meta 字段.json]
                         [--member 成员名 ...] [--force] [--no-install]

设计要点：专家目录固定为 ~/.workbuddy/plugins/marketplaces/my-experts/plugins，
生成即就位；提供 --meta 时可一条命令走完「生成 → 校验 → 安装」。
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    KEBAB_RE,
    TODO_RE,
    experts_plugins_dir,
    read_json,
    use_utf8_stdout,
    write_json,
)

# 模板文件直接放在 templates/ 根下，避免上传技能包出现三级子目录。
# 开放平台技能包最多允许：技能根/二级目录/文件。
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

TODO = "[TODO]"


def _base_manifest(name: str, expert_type: str, agent_name: str) -> dict:
    data = {
        "name": name,
        "version": "1.0.0",
        "description": f"{TODO} English one-line description",
        "author": {"name": TODO, "email": ""},
        "agents": [f"./agents/{agent_name}.md"],
        "expertType": expert_type,
        "agentName": agent_name,
        "displayName": {"en": f"{TODO} English display name", "zh": f"{TODO} 中文显示名称"},
        "profession": {"en": f"{TODO} English profession", "zh": f"{TODO} 中文职业头衔"},
        "displayDescription": {
            "en": f"{TODO} English detailed description",
            "zh": f"{TODO} 中文详细描述，40-50 字，突出核心能力",
        },
        "avatar": "avatars/expert.png",
        "categoryId": f"{TODO}-CategoryName",
        "plugin": name,
        "tags": [
            {"en": f"{TODO} Tag1 EN", "zh": f"{TODO} 标签1"},
            {"en": f"{TODO} Tag2 EN", "zh": f"{TODO} 标签2"},
            {"en": f"{TODO} Tag3 EN", "zh": f"{TODO} 标签3"},
        ],
        "quickPrompts": [
            {"en": f"{TODO} Prompt1 EN", "zh": f"{TODO} 推荐提示词1"},
            {"en": f"{TODO} Prompt2 EN", "zh": f"{TODO} 推荐提示词2"},
            {"en": f"{TODO} Prompt3 EN", "zh": f"{TODO} 推荐提示词3"},
        ],
    }
    data["defaultInitPrompt"] = dict(data["quickPrompts"][0])
    if expert_type == "team":
        data["teamInfo"] = {"leadAgent": agent_name, "memberAgents": []}
        data["members"] = [{
            "id": agent_name,
            "displayName": {"en": f"{TODO} Lead EN", "zh": f"{TODO} 主理人"},
            "profession": {"en": f"{TODO} Lead EN", "zh": f"{TODO} 主理人职业"},
            "avatar": f"avatars/{agent_name}.png",
            "role": "lead",
        }]
    return data


def _read_template(filename: str) -> str:
    path = TEMPLATES / filename
    if not path.is_file():
        raise SystemExit(f"[X] 模板缺失：{path}")
    return path.read_text(encoding="utf-8")


def _fill(text: str, mapping: dict) -> str:
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def scaffold(name: str, expert_type: str, out_dir: Path, meta: dict | None = None,
             members: list[str] | None = None, force: bool = False) -> Path:
    if not KEBAB_RE.match(name):
        raise SystemExit(f"[X] 专家名必须是 kebab-case（小写字母 + 数字 + 连字符）：{name!r}")

    target = out_dir / name
    if target.exists():
        if not force:
            raise SystemExit(
                f"[X] 目录已存在：{target}\n"
                f"    · 想改内容 → 直接编辑现有文件，然后运行 install_expert.py 重新注册\n"
                f"    · 确认要重建骨架 → 加 --force"
            )
        if not (target / ".codebuddy-plugin").exists():
            raise SystemExit(f"[X] 拒绝覆盖：{target} 看起来不是专家包目录（没有 .codebuddy-plugin/）")
        # 作用范围仅限：专家安装目录下、且上方已确认含 .codebuddy-plugin/ 的同名专家包。
        # 不会触及用户的其他文件，也不会碰其它专家。
        shutil.rmtree(target)  # skill-audit: ignore

    agent_name = f"{name}-team-lead" if expert_type == "team" else name
    for sub in (".codebuddy-plugin", "agents", "avatars", "skills"):
        (target / sub).mkdir(parents=True, exist_ok=True)

    manifest = _base_manifest(name, expert_type, agent_name)
    if meta:
        manifest.update(meta)
        if expert_type == "team" and "teamInfo" not in (meta or {}):
            manifest["teamInfo"]["leadAgent"] = manifest.get("agentName", agent_name)

    # Team 型：为每个团员补 agents 声明与 members 条目
    if expert_type == "team" and members:
        for member in members:
            if not KEBAB_RE.match(member):
                raise SystemExit(f"[X] 团员名必须是 kebab-case：{member!r}")
            manifest["agents"].append(f"./agents/{member}.md")
            manifest["teamInfo"]["memberAgents"].append(member)
            manifest["members"].append({
                "id": member,
                "displayName": {"en": f"{TODO} {member} EN", "zh": f"{TODO} {member}"},
                "profession": {"en": f"{TODO} profession EN", "zh": f"{TODO} 职业头衔"},
                "avatar": f"avatars/{member}.png",
                "role": "member",
            })
    write_json(target / ".codebuddy-plugin" / "plugin.json", manifest)

    display_zh = (manifest.get("displayName") or {}).get("zh", name)
    display_en = (manifest.get("displayName") or {}).get("en", name)
    common = {
        "NAME": agent_name,
        "DISPLAY_ZH": display_zh,
        "DISPLAY_EN": display_en,
        "TEAM": manifest.get("displayName", {}).get("zh", name)
        if expert_type == "team" else name,
    }

    lead_tpl = "team-lead.md" if expert_type == "team" else "agent.md"
    (target / "agents" / f"{agent_name}.md").write_text(
        _fill(_read_template(lead_tpl), common), encoding="utf-8")

    member_tpl = _read_template("team-member.md")
    for member in (members or []):
        (target / "agents" / f"{member}.md").write_text(
            _fill(member_tpl, {**common, "NAME": member,
                               "DISPLAY_ZH": f"{TODO} {member}",
                               "DISPLAY_EN": member}), encoding="utf-8")

    (target / "avatars" / ".gitkeep").write_text("", encoding="utf-8")
    (target / "README.md").write_text(
        f"# {display_zh}\n\n"
        "> 一句话说明这个专家替用户解决了什么问题（建议 30 字以内）。\n\n"
        "## 能力边界\n\n"
        "- 擅长：待补充\n"
        "- 不做：待补充\n\n"
        "## 使用方式\n\n在专家中心选中本专家后直接描述问题，或用 quickPrompts 里的推荐提问起步。\n\n"
        "## 重新安装\n\n```bash\n"
        f"python scripts/validate_expert.py <本目录>\n"
        f"python scripts/install_expert.py <本目录>\n```\n",
        encoding="utf-8")

    return target


def _has_todo(root: Path) -> bool:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".json", ".md", ".txt"):
            if TODO_RE.search(path.read_text(encoding="utf-8", errors="replace")):
                return True
    return False


def main() -> int:
    use_utf8_stdout()
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    name = argv[0]
    def opt(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default

    expert_type = opt("--type")
    if expert_type not in ("agent", "team"):
        print("[X] 必须指定 --type agent 或 --type team")
        return 1

    out_dir = Path(opt("--out", str(experts_plugins_dir()))).expanduser()
    meta = read_json(opt("--meta"), {}) if opt("--meta") else {}
    members = [argv[i + 1] for i, a in enumerate(argv) if a == "--member"]

    target = scaffold(name, expert_type, out_dir, meta=meta, members=members,
                      force="--force" in argv)

    print(f"\n专家包骨架已生成：{target}")
    for line in sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()):
        print(f"  · {line}")

    is_expert_home = target.parent.resolve() == experts_plugins_dir().resolve()
    print("\n下一步：")
    if _has_todo(target):
        print("  1. 填充 plugin.json 展示字段与 agents/*.md 正文（把 [TODO] 全部替换掉）")
        print("  2. 用 ImageGen 生成头像，输出到 avatars/，尺寸 1024x1024 后压到 512×512、≤500KB")
        print(f"  3. python scripts/install_expert.py \"{target}\"   # 校验通过即自动安装")
    else:
        print("  内容已完整，可直接运行 install_expert.py 完成安装")

    if "--no-install" not in argv and not _has_todo(target):
        from install_expert import install  # 延迟导入，避免无谓依赖
        return install(target, force=False)

    if not is_expert_home:
        print(f"\n[!] 注意：专家未生成在专家目录，专家中心不会检测到它。")
        print(f"    专家目录：{experts_plugins_dir()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
