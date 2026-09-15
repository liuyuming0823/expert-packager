"""环境自检 + 可选依赖安装。

    python setup.py                 # 只做环境自检，列出缺什么、怎么补
    python setup.py --install-pillow  # 装上 Pillow（头像压缩需要）

本技能核心流程只用标准库；Pillow 仅在压缩/缩放头像时用到，属于可选依赖。
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import config_home, experts_plugins_dir, use_utf8_stdout  # noqa: E402


def has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def main() -> int:
    use_utf8_stdout()
    argv = sys.argv[1:]
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    print("expert-packager 环境自检")
    print("─" * 52)

    ok = True

    major, minor = sys.version_info[:2]
    version_ok = (major, minor) >= (3, 8)
    print(f"{'[OK]' if version_ok else '[X] '} Python {major}.{minor}"
          f"{'' if version_ok else '（需要 3.8+）'}")
    ok &= version_ok

    home = config_home()
    print(f"{'[OK]' if home.is_dir() else '[!] '} 配置根目录 {home}"
          f"{'' if home.is_dir() else '（尚未创建，WorkBuddy 首次启动会生成）'}")

    experts = experts_plugins_dir()
    exists = experts.is_dir()
    print(f"{'[OK]' if exists else '[!] '} 专家安装目录 {experts}")
    if not exists:
        print("     · 目录不存在：生成专家时会自动创建；"
              "若 WorkBuddy 已装好仍缺，说明配置根目录不是这个，请设置 WORKBUDDY_CONFIG_DIR")

    pillow_ok = has("PIL")
    print(f"{'[OK]' if pillow_ok else '[i]'} Pillow {'已安装' if pillow_ok else '未安装（可选）'}")
    if not pillow_ok:
        print("     · 只有压缩/缩放头像时需要它：python setup.py --install-pillow")
        print("     · 不装也能跑通全流程，只是超过 500KB 的头像需要手动处理")

    if "--install-pillow" in argv and not pillow_ok:
        print("\n正在安装 Pillow …")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        except subprocess.CalledProcessError:
            print("[X] 安装失败。可手动执行：python -m pip install Pillow")
            return 1
        print("[OK] Pillow 安装完成")
    elif "--install-pillow" in argv:
        print("\nPillow 已存在，无需安装。")

    print("─" * 52)
    print("环境就绪。" if ok else "请先解决上面的 [X] 项。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
