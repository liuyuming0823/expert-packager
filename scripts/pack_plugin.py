"""把专家包 / 技能目录 / 插件目录打成可分发或可上传开放平台的 zip。

    python pack_plugin.py <目录> [--out 输出目录] [--platform] [--flat-root]
                          [--dry-run] [--force] [--no-validate]

产出形态（**技能与专家的上传包不是一种东西，别互套**）：

  · 技能（目录里有 SKILL.md）
      默认 = 上传 = <技能名>.zip
      顶层：<技能名>/SKILL.md + references/ + scripts/ + templates/
      开放平台「技能」类目就认这个形态，**不需要** .codebuddy-plugin/plugin.json。
      （曾误按插件形态打成 skills/<技能名>/SKILL.md，平台直接报「压缩包缺少 SKILL.md 文件」）

  · 专家（有 agents/*.md，plugin.json 声明了 expertType）
      · 默认         <名字>.zip         顶层 = <名字>/，本机安装或发给同事
      · --platform   <名字>-plugin.zip  插件形态（plugin.json + agents/），上传专家用

  · --flat-root  去掉 zip 顶层的 <名字>/，zip 根即包根（平台报「不接受顶层目录」时用）

退出码：0 成功 / 1 参数或校验问题
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    PLUGIN_DIR,
    is_expert_dir,
    is_skill_dir,
    use_utf8_stdout,
)

SKIP_DIRS = {"__pycache__", "node_modules", ".venv", "venv", ".git", ".idea", ".vscode",
             ".pytest_cache", ".mypy_cache", ".review-cache"}
SKIP_NAMES = {".DS_Store", "Thumbs.db", ".gitkeep", ".downloaded_at", "desktop.ini"}
SKIP_SUFFIX = {".pyc", ".pyo", ".log", ".tmp", ".bak"}


def _keep(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts
    if any(p in SKIP_DIRS for p in parts):
        return False
    if path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIX:
        return False
    if any(p.startswith(".") and p != PLUGIN_DIR for p in parts):
        return False
    return True


def detect_kind(root: Path) -> str:
    if is_expert_dir(root):
        return "expert"
    if (root / PLUGIN_DIR / "plugin.json").is_file():
        return "plugin"
    if is_skill_dir(root):
        return "skill"
    return "unknown"


def _collect(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if _keep(p, root)]


def build(root: Path, out_dir: Path | None, platform: bool, flat_root: bool,
          dry_run: bool, force: bool, validate: bool) -> int:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        print(f"[X] 目录不存在：{root}")
        return 1

    kind = detect_kind(root)
    if kind == "unknown":
        print(f"[X] 无法识别目录类型：{root}")
        print("    专家包需要 .codebuddy-plugin/plugin.json；技能需要 SKILL.md")
        return 1

    if kind == "expert" and validate:
        from validate_expert import validate_expert
        report = validate_expert(root)
        print(report.render())
        if report.count("P0") or (report.count("P1") and not force):
            print("\n[X] 打包中止。修掉问题，或确认无碍后加 --force。")
            return 1

    name = root.name
    if kind == "expert":
        data = json.loads((root / PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))
        name = data.get("name") or name

    # 组装 zip 内的路径映射： {zip 内路径: 源文件}
    #
    # ⚠️ 技能上传包就是**技能目录本身**：
    #       {skill-name}/SKILL.md + references/ + scripts/ + templates/
    #   开放平台「技能」类目认这个形态，**不需要** .codebuddy-plugin/plugin.json。
    #   曾经按插件形态打成 `skills/<技能名>/SKILL.md`，平台在技能目录下找不到
    #   SKILL.md，直接报「压缩包缺少 SKILL.md 文件」。
    #   只有**专家**包才是插件形态（plugin.json + agents/），两者不要互相套用。
    root_prefix = "" if flat_root else f"{name}/"
    entries: dict[str, Path] = {}
    empty_dirs: set[str] = set()

    for path in _collect(root):
        entries[f"{root_prefix}{path.relative_to(root).as_posix()}"] = path
    for path in sorted(root.rglob("*")):
        if path.is_dir() and _keep(path, root) and not any(path.iterdir()):
            empty_dirs.add(f"{root_prefix}{path.relative_to(root).as_posix()}/")

    # 技能不加 -plugin 后缀：上传包与本机包是同一个东西（技能目录）
    zip_name = f"{name}-plugin.zip" if (platform and kind != "skill") else f"{name}.zip"
    out_dir = (Path(out_dir).expanduser() if out_dir else Path.cwd())
    zip_path = out_dir / zip_name

    kind_label = {"expert": "专家包", "skill": "技能包", "plugin": "通用插件包"}.get(kind, kind)
    if kind == "skill":
        # 技能没有"插件形态的上传包"——上传开放平台用的就是技能目录本身
        form = "技能上传包 / 本机包（技能目录形态）"
    elif platform:
        form = "专家上架包（插件形态，按**专家**上传规范）"
    else:
        form = "本机包"
    print(f"\n打包 · {kind_label} · {form}")
    print(f"  源目录  ：{root}")
    print(f"  产出    ：{zip_path}")
    payload = [k for k, v in entries.items() if v is not None and v.is_file()]
    print(f"  文件数  ：{len(payload)}")
    for key in payload[:12]:
        print(f"    · {key}")
    if len(payload) > 12:
        print(f"    … 另有 {len(payload) - 12} 个")

    if dry_run:
        print("\n[dry-run] 未落盘。")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    if zip_path.exists() and not force:
        print(f"\n[X] 已存在 {zip_path}，加 --force 覆盖。")
        return 1

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for key, src in entries.items():
                if src.is_file():
                    zf.write(src, key)
            for folder in sorted(empty_dirs):
                zf.writestr(folder, "")
    except OSError as exc:
        print(f"[X] 写 zip 失败：{exc}")
        return 1

    print(f"\n[OK] 已打包 {len(payload)} 个文件 → {zip_path}"
          f"（{zip_path.stat().st_size / 1024:.1f} KB）")
    if kind == "skill":
        # 技能装到 skills/，不是 marketplaces/ —— 走错地方技能不会生效
        print("     本机安装：解压到 ~/.workbuddy/skills/<技能名>/（技能目录）")
        print("     上传 open.workbuddy.cn 技能类目：直接传这个包")
        print("       官方要求形态 = {skill-name}/SKILL.md + references/ + scripts/ + templates/")
        if platform:
            print("     说明：技能上传包就是技能目录，**不需要** .codebuddy-plugin/plugin.json，")
            print("           所以本包与默认包内容一致（加不加 --platform 都一样）")
    elif platform:
        print("     上传 open.workbuddy.cn 用这个包 —— 专家包（插件形态），字段按**专家**规范"
              "（expertType / displayName / categoryId…）")
        print("     若平台提示不接受顶层目录，改用 --flat-root 重打一次")
    elif kind == "expert":
        print("     本机安装：解压到 ~/.workbuddy/plugins/marketplaces/my-experts/plugins/ 后注册")
    else:
        print("     本机安装：解压到对应插件目录后注册")
    return 0


def main() -> int:
    use_utf8_stdout()
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    def opt(flag):
        return argv[argv.index(flag) + 1] if flag in argv else None

    return build(
        argv[0],
        opt("--out"),
        platform="--platform" in argv,
        flat_root="--flat-root" in argv,
        dry_run="--dry-run" in argv,
        force="--force" in argv,
        validate="--no-validate" not in argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
