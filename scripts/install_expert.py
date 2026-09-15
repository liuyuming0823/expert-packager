"""把校验通过的专家包注册进 my-experts 市场清单 —— 这一步就是「安装」。

    python install_expert.py <专家目录> [--force] [--dry-run]

注册后专家会出现在 WorkBuddy 专家中心的「我的专家」里。
退出码：0 已安装 / 1 校验有 P1（需 --force）/ 2 校验有 P0 / 3 找不到市场清单
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    PLUGIN_DIR,
    find_marketplace_json,
    load_plugin_json,
    read_json,
    use_utf8_stdout,
    write_json,
)
from validate_expert import validate_expert  # noqa: E402


def install(expert_dir, force: bool = False, dry_run: bool = False) -> int:
    root = Path(expert_dir).expanduser().resolve()

    report = validate_expert(root)
    print(report.render())
    if report.count("P0"):
        print("\n[X] 存在 P0 问题，安装中止。先修掉再重试。")
        return 2
    if report.count("P1") and not force:
        print("\n[X] 存在 P1 问题，安装中止。修掉，或确认无碍后加 --force 强行安装。")
        return 1

    manifest = load_plugin_json(root) or {}
    name = manifest.get("name") or root.name
    description = manifest.get("description") or f"WorkBuddy expert: {name}"

    marketplace = find_marketplace_json(root)
    if not marketplace:
        marketplace = root.parent.parent / PLUGIN_DIR / "marketplace.json"
        if not marketplace.parent.exists():
            print(f"\n[X] 找不到市场清单，且无法推断：{marketplace}")
            return 3
        write_json(marketplace, {
            "name": marketplace.parent.parent.name,
            "description": f"{marketplace.parent.parent.name} marketplace (auto-generated)",
            "plugins": [],
        })

    doc = read_json(marketplace, {}) or {}
    doc.setdefault("name", marketplace.parent.parent.name)
    doc.setdefault("description", f"{doc['name']} marketplace (auto-generated)")
    plugins = doc.setdefault("plugins", [])

    try:
        source = "./" + root.relative_to(marketplace.parent.parent).as_posix()
    except ValueError:
        source = "./plugins/" + root.name

    entry = {"name": name, "source": source, "description": description}
    for index, item in enumerate(plugins):
        if isinstance(item, dict) and item.get("name") == name:
            plugins[index] = {**item, **entry}
            action = "更新"
            break
    else:
        plugins.append(entry)
        action = "新增"

    if dry_run:
        print(f"\n[dry-run] 将{action}市场条目 {name} → {source}")
        return 0

    write_json(marketplace, doc)

    expert_type = manifest.get("expertType", "agent")
    print(f"\n[OK] 已{action}并安装：{name}（{'专家团' if expert_type == 'team' else '专家'}）")
    print(f"     · 专家包  ：{root}")
    print(f"     · 市场清单：{marketplace}")
    print("\n下一步：")
    print("  1. 打开 WorkBuddy 专家中心 →「我的专家」查收（未出现时重启会话）")
    print(f"  2. 需要分发/上架 → python scripts/pack_plugin.py \"{root}\"")
    return 0


def main() -> int:
    use_utf8_stdout()
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    return install(argv[0], force="--force" in argv, dry_run="--dry-run" in argv)


if __name__ == "__main__":
    raise SystemExit(main())
