#!/usr/bin/env python3
"""Regenerates the store screenshot style assets deterministically:

  background.png        warm orange->yellow gradient with soft diagonal rays
  frames/*.png          device frames with a transparent screen area
  frames.yaml           frame size, screen rectangle and layout hints per frame

Run: uv run --no-project --with pillow --with pyyaml python make_style.py
The output is committed; rerun only when the style changes.
"""
import math
from pathlib import Path

import yaml
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).parent
SS = 2  # supersampling factor for smooth rounded corners


def background(size=2560):
    # diagonal gradient: deep orange (top-left) -> golden yellow (bottom-right)
    v = Image.linear_gradient("L").resize((size, size), Image.BICUBIC)
    grad = ImageChops.add(v, v.transpose(Image.TRANSPOSE), scale=2)
    c0, c1 = (247, 138, 24), (255, 205, 60)
    base = Image.composite(Image.new("RGB", (size, size), c1), Image.new("RGB", (size, size), c0), grad)
    # soft rays fanning from below the centre, drawn at 2x for smooth edges
    big = size * SS
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy, r, n = big * 0.5, big * 1.15, big * 3, 28
    for i in range(0, n, 2):
        a0 = math.radians(180 + 180 * i / n)
        a1 = math.radians(180 + 180 * (i + 1) / n)
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=(255, 236, 160, 46))
    layer = layer.resize((size, size), Image.LANCZOS)
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def rrect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def device(name, screen, bezel, outer_r, screen_r, body, edge, extra=None):
    """Frame image: rounded body, outline, transparent rounded screen hole."""
    sw, sh = screen
    w, h = sw + 2 * bezel, sh + 2 * bezel
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rrect(d, (0, 0, w * SS - 1, h * SS - 1), outer_r * SS, edge)
    e = 3 * SS
    rrect(d, (e, e, w * SS - 1 - e, h * SS - 1 - e), (outer_r - 3) * SS, body)
    rrect(d, (bezel * SS, bezel * SS, (bezel + sw) * SS - 1, (bezel + sh) * SS - 1), screen_r * SS, (0, 0, 0, 0))
    img = img.resize((w, h), Image.LANCZOS)
    return img, {"size": [w, h], "screen": [bezel, bezel, sw, sh], "radius": screen_r}


def desktop(screen=(1600, 1000), bar=56, border=8):
    sw, sh = screen
    w, h = sw + 2 * border, sh + bar + border
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rrect(d, (0, 0, w * SS - 1, h * SS - 1), 16 * SS, (196, 190, 182, 255))
    rrect(d, (2 * SS, 2 * SS, w * SS - 3 * SS, h * SS - 3 * SS), 14 * SS, (238, 234, 228, 255))
    for i in range(3):  # neutral window dots, no OS branding
        cx, cy = (border + 26 + i * 34) * SS, (bar // 2 + 4) * SS
        d.ellipse((cx - 8 * SS, cy - 8 * SS, cx + 8 * SS, cy + 8 * SS), fill=(190, 184, 176, 255))
    d.rectangle((border * SS, bar * SS, (border + sw) * SS - 1, (bar + sh) * SS - 1), fill=(0, 0, 0, 0))
    img = img.resize((w, h), Image.LANCZOS)
    return img, {"size": [w, h], "screen": [border, bar, sw, sh], "radius": 0}


def main():
    background().save(HERE / "background.png", optimize=True)
    black, black_edge = (12, 12, 13, 255), (58, 58, 62, 255)
    titan, titan_edge = (52, 53, 57, 255), (122, 123, 128, 255)
    frames = {}
    specs = {
        # name: (image, hints). max_width: frame width as fraction of the image width;
        # max_overflow: how much of the frame height may run off the bottom edge.
        "phone": (device("phone", (900, 1950), 34, 120, 88, black, black_edge), 0.86, 0.08),
        "tablet": (device("tablet", (1600, 1000), 48, 64, 24, black, black_edge), 0.94, 0.16),
        "iphone": (device("iphone", (880, 1912), 20, 120, 100, titan, titan_edge), 0.86, 0.08),
        "ipad": (device("ipad", (1032, 1376), 26, 62, 40, titan, titan_edge), 0.86, 0.06),
        "desktop": (desktop(), 0.92, 0.0),
    }
    for name, ((img, meta), max_width, overflow) in specs.items():
        img.save(HERE / "frames" / f"{name}.png", optimize=True)
        meta.update(max_width=max_width, max_overflow=overflow)
        frames[name] = meta
    (HERE / "frames.yaml").write_text(yaml.safe_dump(frames, sort_keys=True))


if __name__ == "__main__":
    main()
