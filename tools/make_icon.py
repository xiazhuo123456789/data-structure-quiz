#!/usr/bin/env python3
"""生成应用图标：深绿底、米白 DS、琥珀色下划线。依赖 Pillow。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SIZE = 1024


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("georgiab.ttf", "arialbd.ttf", "segoeuib.ttf"):
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise SystemExit("找不到可用的粗体字体")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=210, fill=255)

    # 从深绿到近黑的竖向渐变
    gradient = Image.new("RGBA", (SIZE, SIZE))
    top = (31, 68, 58)
    bottom = (12, 31, 27)
    px = gradient.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        px_color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,)
        for x in range(SIZE):
            px[x, y] = px_color

    img.paste(gradient, (0, 0), mask)
    draw = ImageDraw.Draw(img)

    font = load_font(430)
    text = "DS"
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(
        ((SIZE - w) / 2 - box[0], (SIZE - h) / 2 - box[1] - 42),
        text,
        font=font,
        fill=(244, 234, 214),
    )

    draw.rounded_rectangle((352, 686, 672, 714), radius=14, fill=(224, 163, 62))
    draw.rounded_rectangle((402, 744, 622, 762), radius=9, fill=(244, 234, 214, 110))
    draw.rounded_rectangle((442, 792, 582, 810), radius=9, fill=(244, 234, 214, 70))

    png = ASSETS / "icon.png"
    img.resize((512, 512), Image.LANCZOS).save(png)

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ASSETS / "icon.ico", sizes=sizes)
    print(f"已生成：{png}")
    print(f"已生成：{ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
