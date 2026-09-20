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
  "title": { "line1": "我们这代的{鸡蛋}", "line2": "{免费}的token" },
  // 或任意多行（推荐做参考图那种「顶满宽度」的排版）：
  // "title": { "lines": [
  //     { "text": "WorkBuddy",        "size": 240, "ow": 17 },
  //     { "text": "{免费}送{token}",  "size": 240, "ow": 17 }
  // ] },
  "title_safe_margin": 0.035, // 可选，标题左右安全边距(占宽度比)，默认 0.035
                              // 脚本会自动缩字号 + 旋转后二次适配，保证文字绝不超出画布
  "title_max_bottom": 0.295,  // 可选，标题块底部上限(占高度比)
                              // 超限自动缩字号，用来保证「标题不压到人物」
  "title_emph_color": "FFD400", // 可选，{强调词} 的填充色（十六进制或 [r,g,b]）
                              // 默认 FFD400 亮黄——与白字形成层级，最醒目
  "cn_font": "yahei",         // 可选，中文字体。默认 "yahei"(微软雅黑粗体)
                              // 可选值: yahei(雅黑粗) yahei_r(雅黑常规)
                              //         zcool(站酷快乐体) simhei(黑体) deng(等线粗)
                              // 也可直接写字体文件名，如 "msyhbd.ttc"
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
  "title_cn_size": 245,     // 可选
  "title_emph_ratio": 1.28, // 可选，标题里 {强调词} 的放大倍数，默认 1.28
  "decor": {                 // 可选，科技感装饰小图标（默认关闭）
    "enable": true,
    "avoid_title": true,     // 自动避让标题占位矩形，绝不与标题重合
    "items": [               // 不写 items 则用内置默认排布
      { "icon": "bolt",    "fx": 0.10, "fy": 0.17, "size": 150, "rotate": -12 },
      { "icon": "chip",    "fx": 0.90, "fy": 0.30, "size": 140, "rotate": 10 },
      { "icon": "signal",  "fx": 0.07, "fy": 0.60, "size": 130, "rotate": -8 },
      { "icon": "hex",     "fx": 0.93, "fy": 0.72, "size": 135, "rotate": 14 },
      { "icon": "gear",    "fx": 0.12, "fy": 0.88, "size": 140, "rotate": 0 },
      { "icon": "spark",   "fx": 0.88, "fy": 0.12, "size": 120, "rotate": 0 }
    ]
  }
}

标题强调：用花括号 { } 包住想放大的词，例如 "我们这代的{鸡蛋}"。
    放大后的字与原文字基线对齐，同一行内混排不同字号。
    放大倍数由 title_emph_ratio 控制（默认 1.28）。
    强调词的颜色由 title_emph_color 控制（默认 FFD400 亮黄，与白字形成层级）。

标签图标：labels[].icon 可显式指定图标名；不写则按文字自动匹配；
    写 false / null 表示该标签不加图标。
    可用图标名：gift(礼物) coin(金币) star(星星) bolt(闪电) paw(爪印)
                rocket(火箭) code(代码) phone(手机) heart(爱心) sparkle(闪光)
    自动匹配规则见 pick_icon()。

科技感装饰图标：decor 段控制，默认关闭。启用后会在标题以外的空白区
    点缀半透明霓虹科技图标（芯片/闪电/信号/六边形/齿轮/星芒/原子/网格球）。
    可用 decor 图标名：chip bolt signal hex gear spark atom globe code
    avoid_title=true 时会自动把与标题矩形相交的图标下移或跳过。
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

# 覆盖全字库的中文备选字体（首选字体缺字时兜底）
CN_FALLBACKS = ["msyhbd.ttc", "simhei.ttf", "Dengb.ttf", "msyh.ttc"]

# 内置可选中文字体表：name -> (文件名, 说明)
CN_FONT_CHOICES = {
    "yahei":   ("msyhbd.ttc", "微软雅黑 粗体"),      # 默认，正规、清晰
    "yahei_r": ("msyh.ttc",   "微软雅黑 常规"),
    "zcool":   ("ZCOOLKuaiLe-Regular.ttf", "站酷快乐体 手写卡通"),
    "simhei":  ("simhei.ttf", "黑体"),
    "deng":    ("Dengb.ttf",  "等线 粗体"),
}

# 当前使用的中文字体（由 set_cn_font 设置，默认微软雅黑粗体）
_CN_FONT = {"path": None, "name": "yahei"}


def set_cn_font(key):
    """按配置切换中文字体。key 可为 CN_FONT_CHOICES 的键，
    也可直接给字体文件名（如 'msyhbd.ttc'）。"""
    if not key:
        return
    fn = CN_FONT_CHOICES.get(key, (key, key))[0]
    p = find_font(fn)
    if not p:
        print(f"  [字体] 找不到 {fn}，回退默认（微软雅黑粗体）")
        p = find_font("msyhbd.ttc")
        _CN_FONT["name"] = "msyhbd.ttc"
    else:
        _CN_FONT["name"] = key
    _CN_FONT["path"] = p
    print(f"  [字体] 中文字体 = {_CN_FONT['name']} ({p})")


def get_cn_font_path():
    """返回当前中文字体路径，未设置则用微软雅黑粗体"""
    if _CN_FONT["path"]:
        return _CN_FONT["path"]
    for n in ("msyhbd.ttc", "msyh.ttc"):
        p = find_font(n)
        if p:
            _CN_FONT["path"] = p
            _CN_FONT["name"] = n
            return p
    return find_font("ZCOOLKuaiLe-Regular.ttf")


def resolve_cn_font():
    """返回 (首选中文字体路径, 兜底粗体路径)"""
    primary = get_cn_font_path()
    fb = None
    for n in CN_FALLBACKS:
        fb = find_font(n)
        if fb and fb != primary:
            break
    return primary, fb


def missing_glyphs(font_path, text):
    """检测 text 中有哪些字符在该字体里缺字形（渲染为豆腐块）"""
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(font_path, fontNumber=0, lazy=True)
        cmap = set()
        for t in tt['cmap'].tables:
            cmap |= set(t.cmap.keys())
        tt.close()
        return [ch for ch in text if ord(ch) > 127 and ord(ch) not in cmap]
    except Exception:
        return []


def load_fonts(en_size, cn_size, cn_bold_path=None):
    en = find_font("comic.ttf") or find_font("comicbd.ttf")
    if not en:
        raise SystemExit("找不到 Comic Sans (comic.ttf)")
    cn = find_font("ZCOOLKuaiLe-Regular.ttf") or cn_bold_path
    if not cn:
        raise SystemExit("找不到中文字体，请把 ZCOOLKuaiLe-Regular.ttf 放到 assets/fonts/")
    return ImageFont.truetype(en, en_size), ImageFont.truetype(cn, cn_size)


def load_cn_font_for(text, size):
    """按文本内容选字体：当前字体缺字则用兜底字体"""
    primary, fb = resolve_cn_font()
    chosen = primary
    if primary:
        miss = missing_glyphs(primary, text)
        if miss:
            print(f"  [字体兜底] {os.path.basename(primary)} 缺字 {''.join(miss)} -> 改用 {os.path.basename(fb or primary)}")
            chosen = fb or primary
    else:
        chosen = fb
    if not chosen:
        raise SystemExit("找不到可用中文字体")
    return ImageFont.truetype(chosen, size)


def draw_comic_text(layer, ld, text, font, x, y, ow, fill=WHITE):
    """填充色（默认白） + 黑色圆形描边"""
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx * dx + dy * dy <= ow * ow + 6:
                ld.text((x + dx, y + dy), text, font=font, fill=BLACK)
    ld.text((x, y), text, font=font, fill=fill)


def parse_rich(text):
    """把 '我们这代的{鸡蛋}' 解析为 [(片段, 是否强调), ...]"""
    parts, buf, emph = [], '', False
    for ch in text:
        if ch == '{':
            if buf: parts.append((buf, emph)); buf = ''
            emph = True
        elif ch == '}':
            if buf: parts.append((buf, emph)); buf = ''
            emph = False
        else:
            buf += ch
    if buf: parts.append((buf, emph))
    return parts


def draw_rich_line(layer, ld, text, base_size, big_ratio, ow, font_of, cx, y,
                   emph_fill=None):
    """在一行内混排不同字号：{...} 内的文字放大为 base_size*big_ratio。
    以 cx 为水平中心绘制，返回该行实际宽度。
    emph_fill: {强调词} 的填充色，None 表示与普通文字同色（白）。"""
    parts = parse_rich(text)
    segs = []
    for frag, emph in parts:
        size = int(base_size * big_ratio) if emph else base_size
        font = font_of(size)
        bb = ld.textbbox((0, 0), frag, font=font)
        segs.append((frag, font, size, bb, emph))

    # 用统一基线对齐：以普通字号的 ascent 为基准
    norm_font = font_of(base_size)
    norm_asc = norm_font.getmetrics()[0]
    widths = []
    for frag, font, size, bb, emph in segs:
        asc = font.getmetrics()[0]
        widths.append((font.getlength(frag), asc))
    total = sum(w for w, _ in widths)

    x = cx - total / 2
    for (frag, font, size, bb, emph), (w, asc) in zip(segs, widths):
        # 基线对齐：让放大字的基线与非放大字一致
        dy = norm_asc - asc
        col = (emph_fill or WHITE) if emph else WHITE
        draw_comic_text(layer, ld, frag, font, int(x), int(y + dy), ow, fill=col)
        x += w
    return total


def _title_lines(cfg):
    """支持 2 行（line1/line2）或任意多行（lines 数组）。
    返回 [(文本, 基础字号, 描边宽), ...]"""
    t = cfg["title"]
    if "lines" in t:
        out = []
        for it in t["lines"]:
            if isinstance(it, str):
                out.append({"text": it})
            else:
                out.append(dict(it))
        # 每行字号：未指定则用 cn_size
        cn = cfg.get("title_cn_size", 245)
        return [(d["text"], d.get("size", cn), d.get("ow", 16)) for d in out]
    return [(t["line1"], cfg.get("title_en_size", 250), 17),
            (t["line2"], cfg.get("title_cn_size", 245), 16)]


def add_title(base, cfg):
    """渲染标题。支持任意行数，并**自动缩放保证不超出画布左右边界**。
    返回标题占位矩形 (x0,y0,x1,y1)。"""
    W, H = base.size
    gap = cfg.get("title_line_gap", 115)
    # 参考图是「左低右高」的小角度倾斜；负值=右下斜。默认沿用 6°
    angle = cfg.get("title_angle", 6)
    top = int(H * cfg.get("title_top", 0.032))
    big_ratio = cfg.get("title_emph_ratio", 1.28)
    # 左右安全边距（占宽度比例），保证旋转后文字仍在画布内
    # 旋转 angle° 后外接宽度会增加，需预留 h*sin(a) 的额外空间
    safe = cfg.get("title_safe_margin", 0.035)
    import math as _math
    rot_extra = int(H * 0.42 * abs(_math.sin(_math.radians(angle))) * 0.5)  # 标题区高约 42%H
    max_w = int(W * (1 - safe * 2)) - rot_extra * 2

    # {强调词} 的填充色：默认亮黄（鲜艳醒目，与白字形成层级）
    efill = cfg.get("title_emph_color", "FFD400")
    if isinstance(efill, str):
        efill = efill.lstrip('#')
        emph_fill = tuple(int(efill[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    elif isinstance(efill, (list, tuple)) and len(efill) >= 3:
        emph_fill = tuple(efill[:3]) + (255,)
    else:
        emph_fill = None

    lines = _title_lines(cfg)

    # --- 自动缩放：先在 3 倍宽画布上试排，若超出 max_w 则按比例缩字号 ---
    for attempt in range(24):
        layer = Image.new("RGBA", (W * 3, H * 2), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        LCX = W * 3 // 2
        y = 300
        widths, drawn = [], []
        for text, size, ow in lines:
            w = draw_rich_line(layer, ld, text, size, big_ratio, ow,
                               lambda s, tx=text: load_cn_font_for(tx, s), LCX, y,
                               emph_fill=emph_fill)
            widths.append(w)
            drawn.append((text, size, ow, y))
            y += int(size * max(1.0, big_ratio)) + gap
        wmax = max(widths) if widths else 0
        if wmax <= max_w or attempt == 23:
            break
        # 按超出比例整体缩小，留 2% 余量
        scale = (max_w / wmax) * 0.98
        lines = [(tx, max(28, int(sz * scale)), ow) for tx, sz, ow in lines]
        if attempt == 0:
            print("  [标题自动缩放] 原宽 %d > 上限 %d，开始缩字号" % (wmax, max_w))
        gap = max(8, int(gap * scale))

    print("  [标题] 最终 %d 行，最大宽 %d / 上限 %d" % (len(lines), wmax, max_w))
    for tx, sz, ow, yy in drawn:
        print("    行 y=%d 字号=%d  「%s」" % (yy, sz, tx))

    # --- 高度约束：若 title_max_bottom 给定，标题块底部不得超过它 ---
    max_bottom = cfg.get("title_max_bottom")
    if max_bottom:
        for _h in range(20):
            a2 = layer.split()[3].getbbox()
            if not a2:
                break
            blk_h = int(((a2[3] - a2[1]) + 58) * 1.14)     # 含 pad + 旋转 expand 余量
            bottom_ratio = top / H + blk_h / H
            if bottom_ratio <= max_bottom or _h == 18:
                print("  [标题] 底部 %.1f%% (上限 %.1f%%)" % (bottom_ratio*100, max_bottom*100))
                break
            scale = max(0.5, ((max_bottom - top/H) * H) / max(1, blk_h)) * 0.985
            lines = [(tx, max(28, int(sz * scale)), ow) for tx, sz, ow in lines]
            gap = max(8, int(gap * scale))
            # 重排并同步更新 wmax
            layer = Image.new("RGBA", (W * 3, H * 2), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            LCX = W * 3 // 2
            y, widths2, drawn = 300, [], []
            for text, size, ow in lines:
                w = draw_rich_line(layer, ld, text, size, big_ratio, ow,
                                   lambda s, tx=text: load_cn_font_for(tx, s), LCX, y,
                                   emph_fill=emph_fill)
                widths2.append(w)
                drawn.append((text, size, ow, y))
                y += int(size * max(1.0, big_ratio)) + gap
            wmax = max(widths2) if widths2 else 0
            print("  [标题] 高度超限 -> 缩字号至 %d (宽 %d)" % (lines[0][1], wmax))

    print("  [标题] 最终 %d 行，最大宽 %d / 上限 %d" % (len(lines), wmax, max_w))
    for tx, sz, ow, yy in drawn:
        print("    行 y=%d 字号=%d  「%s」" % (yy, sz, tx))

    # 用实际像素边界裁剪，去掉多余留白，让标题块紧凑贴住文字
    alpha = layer.split()[3]
    real = alpha.getbbox()
    if real:
        bb = [min(real[0], LCX - int(wmax/2) - 40), real[1],
              max(real[2], LCX + int(wmax/2) + 40), real[3]]
    else:
        half = int(wmax / 2) + 60
        last = drawn[-1]
        bb = [LCX - half, drawn[0][3] - 90,
              LCX + half, last[3] + int(last[1] * max(1.0, big_ratio)) + 130]
    pad = 28
    crop = layer.crop((bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad)) \
                .rotate(angle, expand=True, resample=Image.BICUBIC)

    # 旋转后若仍超出画布，缩放到刚好放下（宁可整体缩小，也不裁切文字）
    if crop.width > W - int(W * 0.01):
        target = W - int(W * 0.01)
        ratio = target / crop.width
        crop = crop.resize((target, int(crop.height * ratio)), Image.LANCZOS)
        print("  [标题] 旋转后超宽，整体缩放至 %dpx" % target)
    px = (W - crop.width) // 2
    py = top
    if py + crop.height > H:
        py = max(0, H - crop.height)
    base.paste(crop, (px, py), crop)

    title_box = (px - int(H * 0.012), py - int(H * 0.012),
                 px + crop.width + int(H * 0.012), py + crop.height + int(H * 0.012))
    print("  [标题] 落位 x %d-%d  y %d-%d (%.1f%%-%.1f%%)" % (
        px, px + crop.width, py, py + crop.height, py/H*100, (py+crop.height)/H*100))
    return title_box


def gradient(w, h, c1, c2):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            px[x, y] = (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))
    return g


# ---------- 小图标：按关键词自动匹配图形与颜色 ----------
ICON_COLORS = {
    "gift":    (255, 138, 76),    # 橙 礼物（送token/送积分）
    "coin":    (255, 196, 61),    # 金 金币
    "star":    (155, 108, 255),   # 紫 星星
    "bolt":    (255, 82, 150),    # 玫红 闪电
    "paw":     (74, 200, 255),    # 蓝 爪印
    "rocket":  (255, 110, 110),   # 红 火箭
    "code":    (108, 200, 255),   # 青蓝 代码
    "phone":   (120, 220, 170),   # 青绿 手机
    "heart":   (255, 120, 160),   # 粉 爱心
    "sparkle": (255, 215, 90),    # 亮黄 闪光
}

def pick_icon(text):
    """按标签文字猜图标类型"""
    t = text.lower()
    if "token" in t or "积分" in t or "送" in t:
        return "gift"
    if "coin" in t or "币" in t:
        return "coin"
    if "code" in t or "zocde" in t or "dev" in t:
        return "code"
    if "mimo" in t or "小米" in t or "猫" in t or "cat" in t:
        return "paw"
    if "workbuddy" in t or "buddy" in t:
        return "star"
    if "ai" in t or "fast" in t or "闪电" in t:
        return "bolt"
    return "sparkle"


def draw_icon(kind, size):
    """画一个圆形彩色底 + 白色简笔图形，返回 RGBA 图"""
    S = size * 4   # 超采样后缩小，边缘更顺滑
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = ICON_COLORS.get(kind, (255, 180, 90))
    # 白色外圈
    d.ellipse([0, 0, S-1, S-1], fill=(255, 255, 255, 255))
    m = int(S * 0.055)
    d.ellipse([m, m, S-1-m, S-1-m], fill=col + (255,))
    W_ = (255, 255, 255, 255)
    cx = cy = S // 2
    lw = max(2, int(S * 0.055))

    if kind == "gift":
        bw, bh = int(S*0.46), int(S*0.36)
        x0, y0 = cx - bw//2, cy - int(bh*0.15)
        d.rounded_rectangle([x0, y0, x0+bw, y0+bh], radius=int(S*0.05), fill=W_)
        d.rectangle([cx-lw, y0-int(S*0.06), cx+lw, y0+bh], fill=W_)
        ly = y0 - int(S*0.06)
        d.ellipse([cx-int(S*0.20), ly-int(S*0.13), cx-int(S*0.01), ly+int(S*0.03)], outline=W_, width=lw)
        d.ellipse([cx+int(S*0.01), ly-int(S*0.13), cx+int(S*0.20), ly+int(S*0.03)], outline=W_, width=lw)
    elif kind == "star":
        import math
        pts = []
        R, r = S*0.30, S*0.13
        for i in range(10):
            ang = -math.pi/2 + i*math.pi/5
            rr = R if i % 2 == 0 else r
            pts.append((cx + rr*math.cos(ang), cy + rr*math.sin(ang)))
        d.polygon(pts, fill=W_)
    elif kind == "bolt":
        d.polygon([(cx+S*0.06, cy-S*0.30), (cx-S*0.16, cy+S*0.03),
                   (cx-S*0.01, cy+S*0.03), (cx-S*0.07, cy+S*0.30),
                   (cx+S*0.17, cy-S*0.04), (cx+S*0.02, cy-S*0.04)], fill=W_)
    elif kind == "paw":
        pr = int(S*0.11)
        d.ellipse([cx-pr*2-pr, cy-pr-pr, cx-pr*2+pr, cy-pr+pr], fill=W_)
        d.ellipse([cx-pr, cy-int(S*0.22)-pr, cx+pr, cy-int(S*0.22)+pr], fill=W_)
        d.ellipse([cx+pr*2-pr, cy-pr-pr, cx+pr*2+pr, cy-pr+pr], fill=W_)
        d.ellipse([cx-int(S*0.19), cy+int(S*0.02), cx+int(S*0.19), cy+int(S*0.30)], fill=W_)
    elif kind == "coin":
        d.ellipse([cx-int(S*0.26), cy-int(S*0.26), cx+int(S*0.26), cy+int(S*0.26)], outline=W_, width=lw)
        d.ellipse([cx-int(S*0.11), cy-int(S*0.11), cx+int(S*0.11), cy+int(S*0.11)], fill=W_)
    elif kind == "code":
        for sgn in (-1, 1):
            ax = cx + sgn*int(S*0.13)
            d.line([(ax, cy-int(S*0.17)), (ax-sgn*int(S*0.11), cy), (ax, cy+int(S*0.17))],
                   fill=W_, width=lw, joint="curve")
        d.line([(cx+int(S*0.04), cy-int(S*0.19)), (cx-int(S*0.04), cy+int(S*0.19))], fill=W_, width=lw)
    elif kind == "rocket":
        d.polygon([(cx, cy-int(S*0.30)), (cx+int(S*0.12), cy+int(S*0.08)),
                   (cx-int(S*0.12), cy+int(S*0.08))], fill=W_)
        d.polygon([(cx-int(S*0.12), cy+int(S*0.08)), (cx-int(S*0.22), cy+int(S*0.26)),
                   (cx-int(S*0.04), cy+int(S*0.18))], fill=W_)
        d.polygon([(cx+int(S*0.12), cy+int(S*0.08)), (cx+int(S*0.22), cy+int(S*0.26)),
                   (cx+int(S*0.04), cy+int(S*0.18))], fill=W_)
    elif kind == "heart":
        d.ellipse([cx-int(S*0.25), cy-int(S*0.24), cx, cy+int(S*0.01)], fill=W_)
        d.ellipse([cx, cy-int(S*0.24), cx+int(S*0.25), cy+int(S*0.01)], fill=W_)
        d.polygon([(cx-int(S*0.25), cy-int(S*0.06)), (cx+int(S*0.25), cy-int(S*0.06)),
                   (cx, cy+int(S*0.28))], fill=W_)
    elif kind == "phone":
        d.rounded_rectangle([cx-int(S*0.15), cy-int(S*0.27), cx+int(S*0.15), cy+int(S*0.27)],
                            radius=int(S*0.05), outline=W_, width=lw)
        d.line([(cx-int(S*0.06), cy-int(S*0.21)), (cx+int(S*0.06), cy-int(S*0.21))], fill=W_, width=lw)
    else:  # sparkle
        d.polygon([(cx, cy-int(S*0.30)), (cx+int(S*0.07), cy-int(S*0.07)),
                   (cx+int(S*0.30), cy), (cx+int(S*0.07), cy+int(S*0.07)),
                   (cx, cy+int(S*0.30)), (cx-int(S*0.07), cy+int(S*0.07)),
                   (cx-int(S*0.30), cy), (cx-int(S*0.07), cy-int(S*0.07))], fill=W_)
    return img.resize((size, size), Image.LANCZOS)


def make_label(text, cn_font_path, fsize, icon=None, padx=48, pady=30, radius=40, ow=6):
    font = ImageFont.truetype(cn_font_path, fsize)
    m = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = m.textbbox((0, 0), text, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]

    icon_size = int(fsize * 1.30) if icon else 0
    icon_gap = int(fsize * 0.34) if icon else 0
    w = tw + padx*2 + (icon_size + icon_gap if icon else 0)
    h = max(th + pady*2, icon_size + pady*2 if icon else 0)

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w-1, h-1], radius=radius, fill=255)

    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    plate.paste(gradient(w, h, TEAL, PURPLE), (0, 0), mask)
    d = ImageDraw.Draw(plate)

    tx = padx - bb[0] + (icon_size + icon_gap if icon else 0)
    ty = (h - th) // 2 - bb[1]
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 22:
                d.text((tx+dx, ty+dy), text, font=font, fill=(30, 20, 60, 255))
    d.text((tx, ty), text, font=font, fill=WHITE)

    if icon:
        ic = draw_icon(icon, icon_size)
        plate.paste(ic, (int(padx*0.85), (h - icon_size)//2), ic)

    full = Image.new("RGBA", (w + ow*2, h + ow*2), (0, 0, 0, 0))
    outer = Image.new("L", (w + ow*2, h + ow*2), 0)
    ImageDraw.Draw(outer).rounded_rectangle([0, 0, w + ow*2 - 1, h + ow*2 - 1], radius=radius + ow, fill=255)
    full.paste((255, 255, 255, 255), (0, 0), outer)
    full.paste(plate, (ow, ow), plate)
    return full


def add_labels(base, labels, cn_font_path):
    W, H = base.size
    for lab in labels:
        # icon: 显式指定（字符串）→ 用指定；False → 不加图标；缺省 → 自动识别
        if "icon" in lab:
            icon = lab["icon"] or None
        else:
            icon = pick_icon(lab["text"])
        img = make_label(lab["text"], cn_font_path, lab.get("size", 110), icon=icon)
        cx, cy = int(W * lab["fx"]), int(H * lab["fy"])
        x, y = cx - img.width // 2, cy - img.height // 2
        # 防出界
        x = max(6, min(x, W - img.width - 6))
        base.paste(img, (x, y), img)
        print(f"label {lab['text']} icon={icon} -> ({x},{y}) size {img.size}")


# ---------- 科技感装饰图标：线框霓虹风格，半透明 ----------
# 青绿 / 紫 / 青 三色循环，营造赛博科技感
DECOR_COLORS = [
    (40, 184, 148),    # 品牌青绿
    (108, 77, 255),    # 品牌紫
    (0, 225, 255),     # 电光青
    (168, 120, 255),   # 浅紫
]

# 每类图标的推荐外径系数（相对 size）
def _decor_default_items(W, H):
    """四个角 + 上下中轴的默认装饰排布（均在标题下方或标题两侧空白处）"""
    return [
        {"icon": "spark",  "fx": 0.075, "fy": 0.100, "size": 0.052, "rotate": 0,   "alpha": 165},
        {"icon": "bolt",   "fx": 0.930, "fy": 0.135, "size": 0.048, "rotate": 12,  "alpha": 155},
        {"icon": "signal", "fx": 0.070, "fy": 0.455, "size": 0.048, "rotate": -10, "alpha": 150},
        {"icon": "chip",   "fx": 0.930, "fy": 0.480, "size": 0.052, "rotate": 8,   "alpha": 150},
        {"icon": "gear",   "fx": 0.085, "fy": 0.640, "size": 0.050, "rotate": 0,   "alpha": 140},
        {"icon": "hex",    "fx": 0.920, "fy": 0.640, "size": 0.048, "rotate": 20,  "alpha": 140},
        {"icon": "atom",   "fx": 0.080, "fy": 0.880, "size": 0.050, "rotate": 0,   "alpha": 135},
        {"icon": "globe",  "fx": 0.925, "fy": 0.900, "size": 0.048, "rotate": 0,   "alpha": 135},
    ]


def draw_decor_icon(kind, size, color, lw_ratio=0.075, alpha=150):
    """画一个科技感线框图标（无实心底盘），返回 RGBA 图。size 为图标边长。"""
    S = max(24, int(size))
    SS = S * 4                      # 超采样
    img = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = color + (alpha,)
    cx = cy = SS // 2
    lw = max(2, int(SS * lw_ratio))
    R = int(SS * 0.36)

    def arc(box, start, end, width=None):
        d.arc(box, start, end, fill=col, width=width or lw)

    if kind == "chip":
        half = int(SS * 0.22)
        d.rounded_rectangle([cx-half, cy-half, cx+half, cy+half],
                            radius=int(SS*0.045), outline=col, width=lw)
        d.rounded_rectangle([cx-int(SS*0.08), cy-int(SS*0.08), cx+int(SS*0.08), cy+int(SS*0.08)],
                            radius=int(SS*0.02), outline=col, width=max(2, lw-1))
        # 四周引脚
        for i in (-1, 0, 1):
            off = int(SS * 0.11 * i)
            pin = int(SS * 0.09)
            d.line([(cx+off, cy-half), (cx+off, cy-half-pin)], fill=col, width=lw)
            d.line([(cx+off, cy+half), (cx+off, cy+half+pin)], fill=col, width=lw)
            d.line([(cx-half, cy+off), (cx-half-pin, cy+off)], fill=col, width=lw)
            d.line([(cx+half, cy+off), (cx+half+pin, cy+off)], fill=col, width=lw)
    elif kind == "bolt":
        d.polygon([(cx+int(SS*0.09), cy-int(SS*0.34)), (cx-int(SS*0.20), cy+int(SS*0.04)),
                   (cx-int(SS*0.01), cy+int(SS*0.04)), (cx-int(SS*0.10), cy+int(SS*0.34)),
                   (cx+int(SS*0.21), cy-int(SS*0.05)), (cx+int(SS*0.02), cy-int(SS*0.05))],
                  fill=col)
    elif kind == "signal":
        # 三段同心弧（信号强度）
        for k, frac in enumerate((0.55, 0.78, 1.0)):
            rr = int(SS * 0.34 * frac)
            arc([cx-rr, cy-rr, cx+rr, cy+rr], 225, 315, width=max(2, lw - k))
        d.ellipse([cx-int(SS*0.055), cy-int(SS*0.055), cx+int(SS*0.055), cy+int(SS*0.055)], fill=col)
        d.line([(cx, cy), (cx-int(SS*0.22), cy-int(SS*0.22))], fill=col, width=lw)
    elif kind == "hex":
        import math
        pts = [(cx + R*math.cos(math.radians(60*i)), cy + R*math.sin(math.radians(60*i)))
               for i in range(6)]
        d.polygon(pts, outline=col, width=lw)
        r2 = int(R * 0.55)
        pts2 = [(cx + r2*math.cos(math.radians(60*i)), cy + r2*math.sin(math.radians(60*i)))
                for i in range(6)]
        d.polygon(pts2, outline=col, width=max(2, lw-1))
    elif kind == "gear":
        import math
        r_in, r_out = int(SS*0.22), int(SS*0.34)
        for i in range(8):
            a = math.radians(45*i)
            d.line([(cx + r_in*math.cos(a), cy + r_in*math.sin(a)),
                    (cx + r_out*math.cos(a), cy + r_out*math.sin(a))], fill=col, width=int(lw*1.6))
        d.ellipse([cx-r_in, cy-r_in, cx+r_in, cy+r_in], outline=col, width=lw)
        d.ellipse([cx-int(SS*0.075), cy-int(SS*0.075), cx+int(SS*0.075), cy+int(SS*0.075)],
                  outline=col, width=max(2, lw-1))
    elif kind == "atom":
        # 两个交叉椭圆 + 中心核
        for ang in (0, 60, 120):
            ell = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
            ImageDraw.Draw(ell).ellipse([cx-int(SS*0.34), cy-int(SS*0.15),
                                         cx+int(SS*0.34), cy+int(SS*0.15)],
                                        outline=col, width=lw)
            ell = ell.rotate(ang, resample=Image.BICUBIC, center=(cx, cy))
            img.alpha_composite(ell)
        d.ellipse([cx-int(SS*0.065), cy-int(SS*0.065), cx+int(SS*0.065), cy+int(SS*0.065)], fill=col)
    elif kind == "globe":
        d.ellipse([cx-R, cy-R, cx+R, cy+R], outline=col, width=lw)
        d.ellipse([cx-int(R*0.42), cy-R, cx+int(R*0.42), cy+R], outline=col, width=max(2, lw-1))
        d.line([(cx-R, cy), (cx+R, cy)], fill=col, width=lw)
        d.line([(cx-int(R*0.92), cy-int(R*0.36)), (cx+int(R*0.92), cy-int(R*0.36))], fill=col, width=max(2, lw-1))
        d.line([(cx-int(R*0.92), cy+int(R*0.36)), (cx+int(R*0.92), cy+int(R*0.36))], fill=col, width=max(2, lw-1))
    elif kind == "code":
        for sgn in (-1, 1):
            ax = cx + sgn*int(SS*0.13)
            d.line([(ax, cy-int(SS*0.18)), (ax-sgn*int(SS*0.12), cy), (ax, cy+int(SS*0.18))],
                   fill=col, width=int(lw*1.3), joint="curve")
        d.line([(cx+int(SS*0.05), cy-int(SS*0.20)), (cx-int(SS*0.05), cy+int(SS*0.20))],
               fill=col, width=int(lw*1.3))
    else:  # spark 四芒星
        L, s = int(SS*0.36), int(SS*0.075)
        d.polygon([(cx, cy-L), (cx+s, cy-s), (cx+L, cy), (cx+s, cy+s),
                   (cx, cy+L), (cx-s, cy+s), (cx-L, cy), (cx-s, cy-s)], fill=col)
    return img.resize((S, S), Image.LANCZOS)


def add_decor(base, decor, title_box):
    """叠加科技感装饰图标。title_box 为标题占位矩形 (x0,y0,x1,y1)，
    avoid_title=True 时与标题相交的图标会被向下推或跳过。"""
    if not decor or not decor.get("enable"):
        return
    W, H = base.size
    avoid = decor.get("avoid_title", True)
    items = decor.get("items") or _decor_default_items(W, H)

    def overlaps(box, tb):
        return not (box[2] < tb[0] or box[0] > tb[2] or box[3] < tb[1] or box[1] > tb[3])

    for i, it in enumerate(items):
        kind = it.get("icon", "spark")
        s = it.get("size", 0.05)
        size = int(H * s) if s <= 1 else int(s)
        colour = DECOR_COLORS[i % len(DECOR_COLORS)]
        alpha = it.get("alpha", 150)
        ic = draw_decor_icon(kind, size, colour, alpha=alpha)
        if it.get("rotate"):
            ic = ic.rotate(it["rotate"], resample=Image.BICUBIC, expand=True)

        cx, cy = int(W * it["fx"]), int(H * it["fy"])
        x, y = cx - ic.width // 2, cy - ic.height // 2

        # 避让标题：相交则尝试下推到标题下方，仍不行就跳过
        if avoid and title_box:
            if overlaps((x, y, x + ic.width, y + ic.height), title_box):
                y = title_box[3] + int(H * 0.012)
                if overlaps((x, y, x + ic.width, y + ic.height), title_box):
                    print(f"decor {kind} skipped (title conflict)")
                    continue

        # 防出界
        x = max(4, min(x, W - ic.width - 4))
        y = max(4, min(y, H - ic.height - 4))
        base.paste(ic, (x, y), ic)
        print(f"decor {kind} -> ({x},{y}) size {ic.size} alpha={alpha}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: python compose_cover.py config.json")
    cfg = json.load(open(sys.argv[1], encoding="utf-8-sig"))

    base = Image.open(cfg["base"]).convert("RGBA")
    print("base", base.size)

    # 中文字体：默认微软雅黑粗体；配置 cn_font 可切换
    set_cn_font(cfg.get("cn_font", "yahei"))
    cn_font_path = get_cn_font_path()
    if not cn_font_path:
        raise SystemExit("找不到可用的中文字体")

    title_box = None
    if cfg.get("title"):
        title_box = add_title(base, cfg)
    # 装饰图标压在标题之上、标签之下（标签永远在最上层）
    add_decor(base, cfg.get("decor"), title_box)
    add_labels(base, cfg.get("labels", []), cn_font_path)

    base.convert("RGB").save(cfg["out"], "PNG")
    print("saved", cfg["out"], base.size)


if __name__ == "__main__":
    main()
