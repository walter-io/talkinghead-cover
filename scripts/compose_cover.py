#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WorkBuddy 口播封面合成：在 Agnes 生成的底图上叠加「大标题 + 四个文字标签牌」

用法:
    python compose_cover.py config.json

config.json 字段:
{
  "base": "C:/Users/we/agnes-output/base.png",   // Agnes 生成的底图
  "out":  "C:/Users/we/agnes-output/cover.png",  // 输出
  "title": { "line1": "WorkBuddy", "line2": "自动签到" },
  "labels": [
    { "text": "自动签到",   "fx": 0.215, "fy": 0.505, "size": 112 },
    { "text": "多账号管理", "fx": 0.792, "fy": 0.548, "size": 102 },
    { "text": "积分管理",   "fx": 0.215, "fy": 0.660, "size": 112 },
    { "text": "token统计",  "fx": 0.792, "fy": 0.700, "size": 102 }
  ],
  "title_top": 0.032,       // 可选，标题块距顶部比例，默认 0.032
  "title_line_gap": 115,    // 可选，两行间距(px)，默认 115
  "title_angle": 6,         // 可选，标题倾斜角度(度，左低右高)，默认 6
  "title_en_size": 250,     // 可选
  "title_cn_size": 245      // 可选
}
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
TEAL   = (40, 184, 148)     # #28b894
PURPLE = (108, 77, 255)     # #6c4dff

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIRS = [
    os.path.join(HERE, '..', 'assets', 'fonts'),
    r"C:\Users\we\agnes-output\fonts",
    r"C:\Windows\Fonts",
]

def find_font(name):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None

def load_fonts(en_size, cn_size):
    en = find_font("comic.ttf") or find_font("comicbd.ttf")
    cn = find_font("ZCOOLKuaiLe-Regular.ttf")
    if not en:
        raise SystemExit("找不到 Comic Sans (comic.ttf)")
    if not cn:
        raise SystemExit("找不到站酷快乐体 (ZCOOLKuaiLe-Regular.ttf)，请放到 assets/fonts/")
    return ImageFont.truetype(en, en_size), ImageFont.truetype(cn, cn_size)


def draw_comic_text(layer, ld, text, font, x, y, ow):
    """白色填充 + 黑色圆形描边"""
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx * dx + dy * dy <= ow * ow + 6:
                ld.text((x + dx, y + dy), text, font=font, fill=BLACK)
    ld.text((x, y), text, font=font, fill=WHITE)


def add_title(base, cfg):
    W, H = base.size
    f1, f2 = load_fonts(cfg.get("title_en_size", 250), cfg.get("title_cn_size", 245))
    l1, l2 = cfg["title"]["line1"], cfg["title"]["line2"]
    gap = cfg.get("title_line_gap", 115)
    angle = cfg.get("title_angle", 6)
    top = int(H * cfg.get("title_top", 0.032))

    meas = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w1 = meas.textbbox((0, 0), l1, font=f1)[2] - meas.textbbox((0, 0), l1, font=f1)[0]
    w2 = meas.textbbox((0, 0), l2, font=f2)[2] - meas.textbbox((0, 0), l2, font=f2)[0]

    layer = Image.new("RGBA", (W * 3, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    y1 = 180
    draw_comic_text(layer, ld, l1, f1, (W * 3 - w1) // 2, y1, 17)
    y2 = y1 + cfg.get("title_en_size", 250) + gap
    draw_comic_text(layer, ld, l2, f2, (W * 3 - w2) // 2, y2, 16)

    bb = [min((W*3-w1)//2, (W*3-w2)//2), y1, max((W*3+w1)//2, (W*3+w2)//2), y2 + 300]
    pad = 40
    crop = layer.crop((bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad)).rotate(angle, expand=True, resample=Image.BICUBIC)
    base.paste(crop, ((W - crop.width) // 2, top), crop)


def gradient(w, h, c1, c2):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            px[x, y] = (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))
    return g


def make_label(text, cn_font_path, fsize, padx=48, pady=30, radius=40, ow=6):
    font = ImageFont.truetype(cn_font_path, fsize)
    m = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = m.textbbox((0, 0), text, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    w, h = tw + padx*2, th + pady*2

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w-1, h-1], radius=radius, fill=255)

    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    plate.paste(gradient(w, h, TEAL, PURPLE), (0, 0), mask)
    d = ImageDraw.Draw(plate)
    tx, ty = padx - bb[0], pady - bb[1]
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 22:
                d.text((tx+dx, ty+dy), text, font=font, fill=(30, 20, 60, 255))
    d.text((tx, ty), text, font=font, fill=WHITE)

    full = Image.new("RGBA", (w + ow*2, h + ow*2), (0, 0, 0, 0))
    outer = Image.new("L", (w + ow*2, h + ow*2), 0)
    ImageDraw.Draw(outer).rounded_rectangle([0, 0, w + ow*2 - 1, h + ow*2 - 1], radius=radius + ow, fill=255)
    full.paste((255, 255, 255, 255), (0, 0), outer)
    full.paste(plate, (ow, ow), plate)
    return full


def add_labels(base, labels, cn_font_path):
    W, H = base.size
    for lab in labels:
        img = make_label(lab["text"], cn_font_path, lab.get("size", 110))
        cx, cy = int(W * lab["fx"]), int(H * lab["fy"])
        x, y = cx - img.width // 2, cy - img.height // 2
        # 防出界
        x = max(6, min(x, W - img.width - 6))
        base.paste(img, (x, y), img)
        print(f"label {lab['text']} -> ({x},{y}) size {img.size}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: python compose_cover.py config.json")
    cfg = json.load(open(sys.argv[1], encoding="utf-8-sig"))

    base = Image.open(cfg["base"]).convert("RGBA")
    print("base", base.size)

    cn_font_path = find_font("ZCOOLKuaiLe-Regular.ttf")
    if not cn_font_path:
        raise SystemExit("找不到站酷快乐体，请放到 assets/fonts/")

    if cfg.get("title"):
        add_title(base, cfg)
    add_labels(base, cfg.get("labels", []), cn_font_path)

    base.convert("RGB").save(cfg["out"], "PNG")
    print("saved", cfg["out"], base.size)


if __name__ == "__main__":
    main()
