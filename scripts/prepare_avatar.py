"""头像/图标后处理：居中裁切 + 清理 AI 生成标 + 缩到 512×512、压到 500KB 以内。

    python prepare_avatar.py <专家目录 | 图片文件...> [--size 512] [--max-kb 500]
                             [--center] [--clean] [--out 输出目录] [--dry-run]

为什么需要 --center / --clean（两个真实踩过的坑）：
  · ImageGen 出的图是 1024×1024 的圆角方块 + 外圈留白，主体常偏一侧。
    直接整图缩放会带着不对称留白；随手按固定框硬切又会「一边被截、一边留白」。
    --center 按圆角方块的真实边界取正方形居中裁切，四边等距。
  · 生成图右下角带「AI生成 / WORKBUDDY」字样的标。它落在圆角方块**外侧**的背景上，
    --clean 用周围背景重建那一小块，不碰主体；检测不到就不动。

依赖 Pillow（可选）。未安装时给出明确提示，不会擅自安装。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import use_utf8_stdout  # noqa: E402

SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def collect(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in targets:
        path = Path(raw).expanduser()
        if path.is_dir():
            avatar_dir = path / "avatars"
            root = avatar_dir if avatar_dir.is_dir() else path
            files += sorted(p for p in root.iterdir() if p.suffix.lower() in SUFFIXES)
        elif path.is_file():
            files.append(path)
        else:
            print(f"[!] 跳过（不存在）：{path}")
    return files


# --------------------------------------------------------------------------- #
# 图像处理（仅用 Pillow，不引入 numpy）
# --------------------------------------------------------------------------- #

def _content_mask(img, threshold: int = 8):
    """与最外圈背景色差异明显的区域（= 圆角方块本身）。

    PIL 没有现成的「批量算色差」，用 ImageChops 组合：
    sat = max(RGB) - min(RGB)，dark = 255 - min(RGB)，两者取大再阈值化。
    """
    from PIL import ImageChops, ImageOps

    rgb = img.convert("RGB")
    r, g, b = rgb.split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    sat = ImageChops.difference(mx, mn)
    dark = ImageOps.invert(mn)
    return ImageChops.lighter(sat, dark).point(lambda v: 255 if v > threshold else 0)


def detect_watermark(img, box=None) -> bool:
    """判断右下角是否真的有 AI 生成标：与「局部平滑背景」差异明显即算有。"""
    from PIL import Image, ImageChops

    w, h = img.size
    if box is None:
        box = (int(w * 0.84), int(h * 0.89), w, h)
    region = img.convert("RGB").crop(box)
    if region.width < 8 or region.height < 8:
        return False
    smooth = region.resize((6, 6), Image.BOX).resize(region.size, Image.BICUBIC)
    diff = ImageChops.difference(region, smooth).convert("L")
    return diff.getextrema()[1] > 18


def clean_mark(img, box=None, feather_ratio: float = 0.22):
    """用背景平滑重建覆盖右下角小矩形，边缘羽化，避免出现接缝。

    该矩形必须整块落在圆角方块**之外**的背景里（默认取右下角 16%×11%），
    这样重建不会侵蚀图标主体；羽化只加在靠主体的一侧。
    """
    from PIL import Image, ImageChops

    w, h = img.size
    if box is None:
        box = (int(w * 0.84), int(h * 0.89), w, h)
    x0, y0, x1, y1 = box
    region = img.convert("RGB").crop(box)
    rw, rh = region.size

    smooth = region.resize((6, 6), Image.BOX).resize((rw, rh), Image.BICUBIC)

    # 羽化蒙版：上边与左边为 0，向内 feather 像素升到 255，取两者较暗的一侧
    feather = max(4, int(min(rw, rh) * feather_ratio))
    lut = [min(255, int(255 * i / feather)) for i in range(256)]
    ramp_down = Image.linear_gradient("L").resize((rw, rh)).point(lut)      # 上→下 0..255
    ramp_right = ramp_down.rotate(-90, expand=True).resize((rw, rh)).point(lut)
    mask = ImageChops.darker(ramp_down, ramp_right)

    out = img.convert("RGB").copy()
    out.paste(smooth, (x0, y0), mask)
    return out


def center_crop(img):
    """按圆角方块的真实边界取正方形、四边等距地裁切。"""
    w, h = img.size
    bbox = _content_mask(img).getbbox()
    if not bbox:
        return img, None
    x0, y0, x1, y1 = bbox
    side = min(max(x1 - x0, y1 - y0), w, h)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    left = max(0, min(cx - side // 2, w - side))
    top = max(0, min(cy - side // 2, h - side))
    return img.crop((left, top, left + side, top + side)), (left, top, side)


# --------------------------------------------------------------------------- #

def main() -> int:
    use_utf8_stdout()
    # 带值的开关要把它的值一起跳过，否则 --size 512 里的 512 会被当成图片路径
    VALUE_OPTS = {"--size", "--max-kb", "--out"}
    targets, i = [], 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in VALUE_OPTS:
            i += 2
            continue
        if not arg.startswith("--"):
            targets.append(arg)
        i += 1
    argv = targets
    if not argv or "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__.strip())
        return 0

    def opt(flag, default):
        return int(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

    size = opt("--size", 512)
    max_kb = opt("--max-kb", 500)
    dry_run = "--dry-run" in sys.argv
    do_center = "--center" in sys.argv
    do_clean = "--clean" in sys.argv
    out_dir = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None

    try:
        from PIL import Image
    except ImportError:
        print("[X] 未安装 Pillow，无法缩放/压缩头像。")
        print("    安装：python setup.py --install-pillow")
        print("    或手动：python -m pip install Pillow")
        return 1

    files = collect(argv)
    if not files:
        print("[!] 没有找到任何图片。")
        return 1

    print(f"处理 {len(files)} 张图片（目标 {size}×{size}，≤{max_kb}KB"
          f"{'，居中裁切' if do_center else ''}{'，清理生成标' if do_clean else ''}）\n")
    changed = 0
    for path in files:
        before_kb = path.stat().st_size / 1024
        with Image.open(path) as img:
            dims = img.size
            if dry_run:
                need = dims != (size, size) or before_kb > max_kb or do_center or do_clean
                state = "需要处理" if need else "已达标"
                print(f"  · {path.name}  {state}"
                      f"（{dims[0]}×{dims[1]}, {before_kb:.0f}KB）")
                continue

            work = img.convert("RGB")
            notes = []

            if do_clean and detect_watermark(work):
                work = clean_mark(work)
                notes.append("已清生成标")

            if do_center:
                cropped, info = center_crop(work)
                if info:
                    work = cropped
                    notes.append(f"居中裁切 {info[2]}px")

            if work.size != (size, size):
                work = work.resize((size, size), Image.LANCZOS)

            target = Path(out_dir) / path.name if out_dir else path
            target.parent.mkdir(parents=True, exist_ok=True)
            work.save(target, format="PNG", optimize=True, compress_level=9)

        after_kb = target.stat().st_size / 1024
        changed += 1
        flag = "" if after_kb <= max_kb else "  ← 仍超限，请手工压缩"
        extra = f"  [{'; '.join(notes)}]" if notes else ""
        print(f"  · {path.name}  {dims[0]}×{dims[1]} {before_kb:.0f}KB →"
              f" {size}×{size} {after_kb:.0f}KB{flag}{extra}")

    print(f"\n{'[dry-run] ' if dry_run else ''}完成：{changed} 张已处理，"
          f"{len(files) - changed} 张无需处理。")
    if out_dir:
        print(f"输出目录：{Path(out_dir).expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
