# -*- coding: utf-8 -*-
"""
封面校验：确认新增的装饰图标没有和标题/标签重合。

用法:
    python verify_no_overlap.py new.png old.png base.png

参数:
    new.png   本次新成品（含装饰图标）
    old.png   上一版成品（不含装饰图标，但已含标题+标签）
    base.png  Agnes 原始底图（不含任何文字）

输出:
    decor pixels / decor rows / overlap with title/labels
    **只需看 overlap 是否等于 0**，非 0 说明装饰图标压到了标题或标签。

原理:
    1) old - base 的差异 = 标题 + 标签的掩膜
    2) new - old 的差异 = 新加的装饰图标
    3) 两者求交，理想值为 0
"""
import sys
import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.int16)


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    new_p, old_p, base_p = sys.argv[1], sys.argv[2], sys.argv[3]

    a_new, a_old, a_base = load(new_p), load(old_p), load(base_p)
    if a_new.shape != a_old.shape:
        raise SystemExit("新旧成品尺寸不一致：%s vs %s" % (a_new.shape, a_old.shape))
    H, W = a_new.shape[:2]

    old = np.abs(a_old - a_base).sum(axis=2) > 40      # 标题 + 标签
    new = (np.abs(a_new - a_old).sum(axis=2) > 25) & (~old)   # 装饰图标

    print("size %dx%d" % (W, H))
    print("decor pixels:", int(new.sum()))
    if new.sum() == 0:
        print("没有检测到新增装饰元素，请确认 decor.enable=true")
        return
    rows = np.where(new.sum(axis=1) > 0)[0]
    print("decor rows: %d - %d (%.1f%% - %.1f%%)" % (
        rows[0], rows[-1], rows[0] / H * 100, rows[-1] / H * 100))

    overlap = int((new & old).sum())
    pct = overlap / new.sum() * 100
    print("overlap with title/labels: %d (%.2f%% of decor)" % (overlap, pct))
    print("VERDICT:", "PASS (无重合)" if overlap == 0 else "FAIL (有重合，需调整 decor 的 fx/fy)")

    # 按纵向分簇，逐个列出装饰图标落点
    ys = np.where(new.sum(axis=1) > 0)[0]
    clusters, cur = [], [ys[0]]
    for y in ys[1:]:
        if y - cur[-1] <= 3:
            cur.append(y)
        else:
            clusters.append((cur[0], cur[-1])); cur = [y]
    clusters.append((cur[0], cur[-1]))
    print("vertical clusters:", len(clusters))
    for c in clusters:
        band = new[c[0]:c[1] + 1]
        cs = np.where(band.sum(axis=0) > 0)[0]
        print("  y %4d-%4d (%.1f%%-%.1f%%) x %4d-%4d" % (
            c[0], c[1], c[0] / H * 100, c[1] / H * 100, cs[0], cs[-1]))


if __name__ == "__main__":
    main()
