#!/usr/bin/env python3
"""news-image-20261117 entry: "The Bridge Falls".

One PNG, /output/entry.png, drawn entirely in code (Python standard
library only, no network, no assets): the front page of a broadsheet
for Tuesday 17 November 2026, built with a small scanline rasteriser
and a hand-made 5x7 bitmap font (upper, lower, digits, punctuation).

The day, as reported on 17 November 2026 (Reuters, CNN, Le Monde,
AP): Ukraine struck the Kerch Bridge linking Russia to occupied
Crimea for a second straight day and its road arch collapsed into
the strait; Russia answered by hitting two bridges over the Dnipro
in Kyiv; Moscow said it shot down 1,441 Ukrainian drones, the
largest drone attack of the war. In the Gulf, U.S. jets struck an
Iranian missile site on Qeshm Island, Iran fired drones at a U.S.
radar base in Bahrain, and a fourth tanker caught fire east of the
Strait of Hormuz. Donald Trump left for Asia for Thursday's
first-ever Xi-Trump-Putin meeting in Shenzhen.

The front page tells it the way a paper would: one huge headline
and a drawn picture of the fallen bridge, with the Gulf and the
Shenzhen summit as the two other column stories, and the oil price
in the footer. Every word was checked against the wire reports
before it was drawn.

Deterministic: fixed constants only, no clock, no randomness
beyond a seeded counter used for paper grain.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (or plain, for /output)
"""

import math
import os
import struct
import zlib

W = H = 1024
fb = bytearray(W * H * 3)

PAPER = (245, 240, 225)
INK = (18, 16, 12)
GREY = (90, 86, 76)
RED = (178, 34, 28)
SKY_TOP = (214, 226, 232)
SKY_BOT = (238, 232, 214)
SEA_TOP = (74, 110, 122)
SEA_BOT = (38, 74, 88)
STEEL = (58, 58, 60)
STEEL_LT = (96, 96, 98)
SMOKE = (120, 118, 112)
FIRE = (224, 122, 32)
FIRE_Y = (240, 196, 64)


# ------------------------------------------------------------------ pixels
def px(x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i], fb[i + 1], fb[i + 2] = rgb


def blend(x, y, rgb, a):
    if 0 <= x < W and 0 <= y < H and 0.0 < a <= 1.0:
        i = (y * W + x) * 3
        fb[i] = int(fb[i] * (1 - a) + rgb[0] * a + 0.5)
        fb[i + 1] = int(fb[i + 1] * (1 - a) + rgb[1] * a + 0.5)
        fb[i + 2] = int(fb[i + 2] * (1 - a) + rgb[2] * a + 0.5)


def rect(x, y, w, h, rgb, alpha=1.0):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if alpha >= 1.0:
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                fb[i], fb[i + 1], fb[i + 2] = rgb
    else:
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                blend(xx, yy, rgb, alpha)


def hline(x0, x1, y, rgb, t=1):
    rect(x0, y - t // 2, x1 - x0, t, rgb)


def vline(x, y0, y1, rgb, t=1):
    rect(x - t // 2, y0, t, y1 - y0, rgb)


def disc(cx, cy, r, rgb, alpha=1.0):
    r2 = r * r
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        for xx in range(cx - dx, cx + dx + 1):
            if alpha >= 1.0:
                px(xx, yy, rgb)
            else:
                blend(xx, yy, rgb, alpha)


def ellipse(cx, cy, rx, ry, rgb, alpha=1.0):
    for yy in range(cy - ry, cy + ry + 1):
        dy = (yy - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        for xx in range(cx - dx, cx + dx + 1):
            if alpha >= 1.0:
                px(xx, yy, rgb)
            else:
                blend(xx, yy, rgb, alpha)


def poly(points, rgb, alpha=1.0):
    """Scanline fill of a simple polygon."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa, xb = int(math.ceil(xs[k])), int(math.floor(xs[k + 1]))
            for x in range(max(0, xa), min(W, xb + 1)):
                if alpha >= 1.0:
                    px(x, y, rgb)
                else:
                    blend(x, y, rgb, alpha)


def seg(x0, y0, x1, y1, w, rgb, alpha=1.0):
    """Thick segment as a quad."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
          (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], rgb, alpha)


def arc_pts(cx, cy, rx, ry, a0, a1, n=48):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n),
             cy + ry * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def arc_seg(cx, cy, rx, ry, a0, a1, w, rgb, alpha=1.0):
    pts = arc_pts(cx, cy, rx, ry, a0, a1)
    for i in range(len(pts) - 1):
        seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], w, rgb, alpha)


def vgrad(x, y, w, h, top, bottom):
    for yy in range(y, y + h):
        t = (yy - y) / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t + 0.5) for i in range(3))
        rect(x, yy, w, 1, c)


# ------------------------------------------------------------------ 5x7 font
# Hand-made bitmap font. Each glyph: 7 rows of 5 pixels, '#' = ink.
# Written from scratch for this entry.
FONT = {
' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
'c': (".....", ".....", ".###.", "#....", "#....", "#...#", ".###."),
'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
'f': ("..##.", ".#..#", ".#...", "###..", ".#...", ".#...", ".#..."),
'g': (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
'j': ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", "...#.", ".##.."),
'k': ("#....", "#....", "#.#..", "#.#..", "##...", "#.#..", "#..#."),
'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#....", "#...."),
'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#", "....#"),
'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
't': (".#...", ".#...", "###..", ".#...", ".#...", ".#...", "..##."),
'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
'y': (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#", ".###."),
'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
'0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
'1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
'2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
'3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
'4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
'5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
'6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
'7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
'8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
'9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
'.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
',': (".....", ".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
'!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
'?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
'-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
'\u2013': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
'\u2014': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
'(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
'/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
'%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.###", "#..##"),
'&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
'$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
'+': (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
'=': (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
'*': (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
'"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
"'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
'\u2019': ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
'\u2022': (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}


def glyph(ch):
    return FONT.get(ch, FONT['?'])


def text_width(text, s):
    w = 0
    for ch in text:
        g = glyph(ch)
        w += (len(g[0]) + 1) * s
    return w - s if w else 0


def draw_text(x, y, text, s, rgb, align='l', bold=False):
    """Draw text with the 5x7 font at integer scale s. Returns width."""
    total = text_width(text, s)
    if align == 'c':
        x -= total // 2
    elif align == 'r':
        x -= total
    cx = x
    for ch in text:
        g = glyph(ch)
        gh = len(g)
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == '#':
                    rect(cx + c * s, y + r * s, s, s, rgb)
                    if bold:
                        rect(cx + c * s + 1, y + r * s, s, s, rgb)
        cx += (len(g[0]) + 1) * s
    return total


def wrap(text, max_w, s):
    """Greedy word wrap; returns list of lines."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, s) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(x, y, text, s, rgb, max_w, leading=None):
    """Draw a wrapped paragraph; returns y after the last line."""
    lh = leading or int(7 * s * 1.55)
    for line in wrap(text, max_w, s):
        draw_text(x, y, line, s, rgb)
        y += lh
    return y


# ------------------------------------------------------------------ page
def paper_grain():
    """Deterministic faint speckle so the page is not flat white."""
    seed = 1234567
    for _ in range(2600):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        x = seed % W
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        y = seed % H
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        if seed % 3 == 0:
            px(x, y, (232, 226, 208))
        else:
            px(x, y, (238, 233, 218))


def masthead():
    rect(0, 0, W, H, PAPER)
    paper_grain()
    # double border
    rect(14, 14, W - 28, H - 28, INK, alpha=1.0)  # placeholder overwritten below
    rect(15, 15, W - 30, H - 30, PAPER)
    hline(18, W - 18, 18, INK, 3)
    hline(18, W - 18, H - 19, INK, 3)
    vline(18, 18, H - 18, INK, 3)
    vline(W - 19, 18, H - 18, INK, 3)
    # nameplate
    draw_text(W // 2, 34, "THE WORLD", 16, INK, align='c')
    hline(48, W - 48, 168, INK, 2)
    draw_text(48, 178, "No. 322", 2, GREY)
    draw_text(W // 2, 178, "TUESDAY, 17 NOVEMBER 2026", 3, INK, align='c', bold=True)
    draw_text(W - 48, 178, "ONE DAY, ONE PAGE", 2, GREY, align='r')
    hline(48, W - 48, 202, INK, 4)


def kicker_headline_deck():
    draw_text(W // 2, 216, "UKRAINE STRIKES FOR A SECOND DAY", 3, RED, align='c', bold=True)
    draw_text(W // 2, 252, "KERCH BRIDGE FALLS", 9, INK, align='c', bold=True)
    deck = ("Ukraine brings down the road arch of the Crimea bridge; "
            "Russia hits Kyiv's bridges.")
    para(72, 330, deck, 3, INK, W - 144, leading=34)


def bridge_scene(x0, y0, x1, y1):
    """The fallen bridge: deck with a gap, the arch in the water, smoke."""
    rect(x0, y0, x1 - x0, y1 - y0, SKY_TOP)
    vgrad(x0, y0, x1 - x0, 170, SKY_TOP, SKY_BOT)
    sea_y = y0 + 168
    vgrad(x0, sea_y, x1 - x0, y1 - sea_y, SEA_TOP, SEA_BOT)
    # pale sun, upper right
    disc(x1 - 120, y0 + 62, 34, (240, 228, 180))
    disc(x1 - 120, y0 + 62, 26, (244, 236, 198))
    # distant shore, left
    poly([(x0, sea_y), (x0 + 150, sea_y - 26), (x0 + 300, sea_y - 10),
          (x0 + 330, sea_y), (x0, sea_y)], (168, 160, 138))
    # drones in the sky
    for dx, dy, s in ((x0 + 150, y0 + 46, 7), (x0 + 330, y0 + 30, 6),
                      (x0 + 560, y0 + 58, 7)):
        seg(dx - s, dy - s, dx + s, dy + s, 3, INK)
        seg(dx + s, dy - s, dx - s, dy + s, 3, INK)
        disc(dx, dy, 2, INK)
    # smoke over the gap
    gap_cx = (x0 + x1) // 2
    for i, (ox, oy, r, a) in enumerate((
            (-58, -58, 30, 0.55), (-20, -84, 38, 0.5), (24, -66, 32, 0.55),
            (62, -96, 40, 0.45), (0, -112, 34, 0.4), (-84, -84, 24, 0.5))):
        disc(gap_cx + ox, y0 + 128 + oy, r, SMOKE, alpha=a)
    # explosion flash at the gap
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        seg(gap_cx, y0 + 128, gap_cx + int(46 * math.cos(a)),
            y0 + 128 + int(46 * math.sin(a)), 5, FIRE_Y)
    disc(gap_cx, y0 + 128, 20, FIRE)
    disc(gap_cx, y0 + 128, 11, FIRE_Y)
    # deck: left and right spans, gap in the middle
    deck_y = y0 + 128
    rect(x0, deck_y, 400, 12, STEEL)
    rect(x0 + 560, deck_y, x1 - (x0 + 560), 12, STEEL)
    hline(x0, x0 + 400, deck_y + 14, STEEL_LT, 2)
    hline(x0 + 560, x1, deck_y + 14, STEEL_LT, 2)
    # deck supports
    for sx in (x0 + 60, x0 + 200, x0 + 340, x0 + 640, x0 + 790):
        rect(sx, deck_y + 12, 10, sea_y - deck_y - 12 + 40, STEEL)
    # standing arch on the right span
    arc_seg(x0 + 700, deck_y, 120, 92, math.pi, 2 * math.pi, 10, STEEL)
    # broken arch stub on the left span
    arc_seg(x0 + 250, deck_y, 110, 84, math.pi * 1.18, math.pi * 1.62, 10, STEEL)
    # fallen arch in the water, tilted, half sunk
    arc_seg(gap_cx - 8, sea_y + 66, 96, 60, math.pi * 1.08, math.pi * 1.92, 12, STEEL)
    arc_seg(gap_cx - 8, sea_y + 66, 96, 60, math.pi * 1.08, math.pi * 1.92, 5, STEEL_LT)
    # splash arcs around the fallen arch
    arc_seg(gap_cx - 60, sea_y + 74, 46, 14, math.pi, 2 * math.pi, 3, (235, 240, 238))
    arc_seg(gap_cx + 52, sea_y + 70, 38, 12, math.pi, 2 * math.pi, 3, (235, 240, 238))
    # waves
    for wy in range(sea_y + 26, y1 - 12, 26):
        for wx in range(x0 + 20, x1 - 20, 64):
            arc_seg(wx, wy, 22, 7, math.pi, 2 * math.pi, 2, (200, 215, 218), alpha=0.7)
    # frame
    rect(x0, y0, x1 - x0, 3, INK)
    rect(x0, y1 - 3, x1 - x0, 3, INK)
    rect(x0, y0, 3, y1 - y0, INK)
    rect(x1 - 3, y0, 3, y1 - y0, INK)


def caption(y):
    text = ("The Kerch Bridge on Tuesday: the road arch fell into the strait, "
            "blocking navigation. Two people were killed, Crimea's "
            "Russian-installed governor said. Rail traffic resumed on one track.")
    return para(72, y, text, 2, GREY, W - 144, leading=20)


def columns(y0):
    col_w = 288
    xs = [48, 368, 688]
    heads = ["KYIV'S BRIDGES HIT", "GULF IN FLAMES", "SHENZHEN THURSDAY"]
    bodies = [
        ("Russia struck two bridges over the Dnipro in Kyiv overnight. "
         "Moscow said it shot down 1,441 drones, the largest drone "
         "attack of the war."),
        ("U.S. jets struck an Iranian missile site on Qeshm Island. "
         "Iran fired drones at a U.S. radar base in Bahrain, and a "
         "fourth tanker burned east of Hormuz."),
        ("Donald Trump left for Asia on Tuesday for the first-ever "
         "U.S.-China-Russia leaders' meeting. Xi Jinping, Trump and "
         "Vladimir Putin meet in Shenzhen on Thursday."),
    ]
    for x, head, body in zip(xs, heads, bodies):
        draw_text(x, y0, head, 2, INK, bold=True)
        hline(x, x + col_w, y0 + 22, INK, 2)
        para(x, y0 + 34, body, 2, INK, col_w, leading=20)
    vline(352, y0, y0 + 190, GREY, 1)
    vline(672, y0, y0 + 190, GREY, 1)


def footer():
    hline(48, W - 48, 946, INK, 2)
    draw_text(W // 2, 958, "MARKETS: BRENT CRUDE NEAR $93 AS GULF ATTACKS OFFSET A U.S. STOCK BUILD",
              2, INK, align='c')
    draw_text(W // 2, 984, "THE WORLD  •  TUESDAY, 17 NOVEMBER 2026  •  ONE DAY'S NEWS IN ONE PAGE",
              2, GREY, align='c')


def build():
    masthead()
    kicker_headline_deck()
    bridge_scene(48, 402, W - 48, 668)
    caption(680)
    columns(748)
    footer()


def chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += fb[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out, "entry.png")
    build()
    n = write_png(path)
    print(f"wrote {path} {n} bytes")


if __name__ == "__main__":
    main()
