#!/usr/bin/env python3
"""从 assets/icon.png 生成 Android 各密度启动图标。

用法：
    python android/tools/make_android_icons.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ICON = PROJECT_ROOT / "assets" / "icon.png"
RES = PROJECT_ROOT / "android" / "app" / "src" / "main" / "res"

LEGACY_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

FOREGROUND_SIZES = {
    "mipmap-mdpi": 108,
    "mipmap-hdpi": 162,
    "mipmap-xhdpi": 216,
    "mipmap-xxhdpi": 324,
    "mipmap-xxxhdpi": 432,
}


def circle_mask(size: int, scale: int = 4) -> Image.Image:
    """先放大再缩小，得到边缘平滑的圆形遮罩。"""
    big = size * scale
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def round_icon(image: Image.Image, size: int) -> Image.Image:
    resized = image.resize((size, size), Image.LANCZOS).convert("RGBA")
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(resized, (0, 0), circle_mask(size))
    return result


def main() -> int:
    if not SOURCE_ICON.exists():
        raise SystemExit(f"找不到图标源文件：{SOURCE_ICON}")

    source = Image.open(SOURCE_ICON).convert("RGBA")

    for folder, size in LEGACY_SIZES.items():
        out_dir = RES / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        source.resize((size, size), Image.LANCZOS).save(
            out_dir / "ic_launcher.png", optimize=True
        )
        round_icon(source, size).save(out_dir / "ic_launcher_round.png", optimize=True)

    for folder, size in FOREGROUND_SIZES.items():
        out_dir = RES / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        # 自适应图标前景放在 108dp 画布内，内容约占 66%，避开系统裁切安全区
        content = int(round(size * 0.66))
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        scaled = source.resize((content, content), Image.LANCZOS)
        offset = (size - content) // 2
        canvas.alpha_composite(scaled, (offset, offset))
        canvas.save(out_dir / "ic_launcher_foreground.png", optimize=True)

    print(f"图标源：{SOURCE_ICON}")
    print("已生成：")
    for folder in list(LEGACY_SIZES) + ["mipmap-anydpi-v26"]:
        print(f"  res/{folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
