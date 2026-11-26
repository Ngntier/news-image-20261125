#!/usr/bin/env python3
"""news-image-20261125 -- "Sum up 25 November's world news in one image".

Draws a dense newspaper front page for Wednesday 25 November 2026, using
only the Python standard library. No network, no files read at run time,
fully deterministic: two runs write byte-identical PNGs.

Layout (1024x1024): masthead with the date, a lead story on the Strait of
Hormuz tanker attacks, two second-lead stories, three columns (war &
conflict / politics, business & tech / the day in UTC), and a bottom band
with markets, sport and a sources footer. Every story below happened or
was first reported on Wednesday 25 November 2026, as reported by Reuters,
AP, BBC, The New York Times, Just Security and IANS that day.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (253, 251, 244)   # off-white newsprint
INK = (18, 18, 18)       # near-black ink
RED = (178, 24, 24)      # kicker / accent red
NAVY = (24, 52, 92)      # section headers / rules
GREY = (96, 96, 92)      # secondary text
LIGHT = (236, 231, 219)  # light rule fill
STEEL = (58, 84, 120)    # ship / graphic blue-grey
GOLD = (176, 132, 32)    # small accent

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 35 characters of '0'/'1': 7 rows of 5 bits.
# ASCII only, so the page never depends on an external font file.
# ---------------------------------------------------------------------------
FONT = {
    "A": "01110100011000111111100011000110001",
    "B": "11110100011000111110100011000111110",
    "C": "01110100011000010000100001000101110",
    "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111",
    "F": "11111100001000011110100001000010000",
    "G": "01110100011000010111100011000101111",
    "H": "10001100011000111111100011000110001",
    "I": "01110001000010000100001000010001110",
    "J": "00111000100001000010000101001001100",
    "K": "10001100101010011000101001001010001",
    "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001",
    "N": "10001110011010110011100011000110001",
    "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000",
    "Q": "01110100011000110001101011001001101",
    "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110",
    "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110",
    "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011101110001",
    "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100",
    "Z": "11111000010001000100010001000011111",
    "0": "01110100011001110101110011000101110",
    "1": "00100011000010000100001000010001110",
    "2": "01110100010000100110010001000011111",
    "3": "11111000100010000010000011000101110",
    "4": "00010001100101010010111110001000010",
    "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110",
    "7": "1111100001000100010001000100001000".ljust(35, "0"),
    "8": "01110100011000101110100011000101110",
    "9": "01110100011000101111000010001001100",
    "a": "00000000000111000001011111000101111",
    "b": "10000100001111010001100011000111110",
    "c": "00000000000111010000100001000101110",
    "d": "00001000010111110001100011000101111",
    "e": "00000000000111010001111111000001110",
    "f": "0011001001010001111001000100001000".ljust(35, "0"),
    "g": "00000011111000110001011110000101110",
    "h": "10000100001111010001100011000110001",
    "i": "00100000000110000100001000010001110",
    "j": "00010000000011000010000101001001100",
    "k": "10000100001001010100110001010010010",
    "l": "01100001000010000100001000010001110",
    "m": "00000000001101010101101011010110101",
    "n": "00000000001111010001100011000110001",
    "o": "00000000000111010001100011000101110",
    "p": "00000000001111010001100011111010000",
    "q": "00000000000111110001100010111100001",
    "r": "00000000001011011001100001000010000",
    "s": "00000000000111110000011100000111110",
    "t": "01000010001110001000010000100100110",
    "u": "00000000001000110001100011001101101",
    "v": "00000000001000110001100010101000100",
    "w": "00000000001000110101101011010101010",
    "x": "00000000001000101010001000101010001",
    "y": "00000000001000110001011110000101110",
    "z": "00000000001111100010001000100011111",
    " ": "00000000000000000000000000000000000",
    ".": "00000" * 5 + "01100" * 2,
    ",": "00000000000000000000011000010001000",
    ":": "00000011000110000000011000110000000",
    ";": "00000011000110000000011000010001000",
    "!": "00100001000010000100001000000000100",
    "?": "01110100010000100010001000000000100",
    "'": "00100001000100000000000000000000000",
    '"': "01010010100000000000000000000000000",
    "-": "00000000000000011111000000000000000",
    "(": "00010001000100001000010000010000010",
    ")": "01000001000001000010000100010001000",
    "/": "00001000100001000100010001000100000",
    "%": "11001110100001000100010000101110011",
    "$": "00100011111010001110001011111000100",
    "&": "01100100101010001000101011001001101",
    "*": "00000101010111010101000000000000000",
    "+": "00000001000010011111001000010000000",
    "=": "00000000001111100000111110000000000",
    "#": "01010010101111101010111110101001010",
    "@": "01110100011011110101101101000001110",
    "[": "01110010000100001000010000100001110",
    "]": "01110000100001000010000100010001110",
    "_": "00000000000000000000000000000011111",
    ">": "10000010000010000010001000100010000",
    "<": "00001000100010001000001000010000001",
}

# Fix the two glyphs written with ljust above: '7' and 'f' were typed short.
FONT["7"] = "1111100001000100010001000100001000" + "0"
FONT["f"] = "0011001001010001111001000100001000" + "0"


def glyph_rows(ch):
    """Return the 7 rows of 5 bits for a character (unknown -> blank)."""
    bits = FONT.get(ch, FONT[" "])
    return [bits[i * 5:(i + 1) * 5] for i in range(7)]


class Canvas:
    """A plain RGB pixel buffer with tiny drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        for xx in range(x, x + w):
            self.set(xx, y, color)

    def vline(self, x, y, h, color):
        for yy in range(y, y + h):
            self.set(x, yy, color)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            for xx in range(cx - dx, cx + dx + 1):
                self.set(xx, cy + dy, color)

    def ring(self, cx, cy, r, color):
        for deg in range(0, 360):
            import math
            a = math.radians(deg)
            self.set(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), color)

    # -- text -------------------------------------------------------------
    def text_w(self, s, scale, spacing=1):
        return len(s) * (5 * scale + spacing) - spacing if s else 0

    def text(self, s, x, y, scale, color, bold=False, spacing=1):
        cx = x
        for ch in s:
            rows = glyph_rows(ch)
            for r in range(7):
                for c in range(5):
                    if rows[r][c] == "1":
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(cx + c * scale + dx, y + r * scale + dy, color)
                                if bold:
                                    self.set(cx + c * scale + dx + 1, y + r * scale + dy, color)
            cx += 5 * scale + spacing
        return cx

    def text_center(self, s, cx, y, scale, color, bold=False, spacing=1):
        w = self.text_w(s, scale, spacing)
        return self.text(s, cx - w // 2, y, scale, color, bold, spacing)

    def wrap(self, s, max_w, scale, spacing=1):
        """Greedy word wrap; returns a list of lines that fit max_w."""
        words = s.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale, spacing) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def write_png(path, canvas):
    """Encode the canvas as a plain PNG (filter 0 rows, zlib level 9)."""
    raw = bytearray()
    row_len = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * row_len:(y + 1) * row_len]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------------------
# Content. Every story below happened or was first reported on Wednesday
# 25 November 2026, as reported that day by Reuters, AP, BBC, The New
# York Times, Just Security and IANS. No invented facts.
# ---------------------------------------------------------------------------
MARGIN = 28
CW = 968  # content width, x = 28..996

LEAD_KICKER = "LEAD STORY - WAR IN THE GULF"
LEAD_HEAD = ["TANKERS HIT BY MINES", "IN THE STRAIT OF HORMUZ"]
LEAD_DECK = (
    "Iran's Revolutionary Guard says two oil tankers struck naval mines and "
    "caught fire in the Strait of Hormuz. Tehran says new defences now guard "
    "the waterway; oil prices rose on supply fears."
)

SECOND = [
    {
        "kicker": "YEMEN - SAUDI ARABIA",
        "head": "HOUTHIS CLAIM STRIKE ON RAS TANURA REFINERY",
        "deck": "Yemen's Houthis say they hit Saudi Arabia's largest oil "
                "refinery and fires broke out. Riyadh says air defences "
                "downed four drones.",
    },
    {
        "kicker": "TRADE - WASHINGTON",
        "head": "US PROPOSES NEW TARIFFS",
        "deck": "Washington proposes tariffs of 20 to 40 percent on 14 "
                "trading partners after a probe into excess factory "
                "capacity. A hearing is set for January 25.",
    },
]

# Column stories: headline fits one line at scale 2 in 310 px (<= 27 chars),
# deck wraps to at most 3 lines (<= 84 chars).
COL1_TITLE = "WAR AND CONFLICT"
COL1 = [
    {
        "kicker": "GAZA",
        "head": "ISRAEL KILLS HAMAS COLONEL",
        "deck": "Israeli strike kills Hamas security chief Abuelouf, his "
                "wife and two children.",
    },
    {
        "kicker": "UKRAINE",
        "head": "RUSSIAN STRIKES HIT ODESA",
        "deck": "Two killed, three hurt as Russian strikes hit Odesa and a "
                "Kyiv apartment block.",
    },
    {
        "kicker": "UKRAINE",
        "head": "490,334 RUSSIAN WAR DEAD",
        "deck": "Leaked Russian records analysed by the BBC put war "
                "dead at 490,334.",
    },
    {
        "kicker": "SUDAN",
        "head": "RSF DRONES KILL 19 CIVILIANS",
        "deck": "Paramilitary drone strikes kill 19 civilians and wound 20 "
                "in Damazin and Roseires.",
    },
]

COL2_TITLE = "POLITICS, BUSINESS, TECH"
COL2 = [
    {
        "kicker": "SPACE",
        "head": "PAKISTAN'S FIRST ASTRONAUT",
        "deck": "China's Shenzhou-24 docks at Tiangong with Pakistan's "
                "Muhammad Zeeshan Ali aboard.",
    },
    {
        "kicker": "TECH",
        "head": "HUAWEI FOUND GUILTY IN US",
        "deck": "A US jury convicts Huawei of trade-secret theft and bank "
                "fraud.",
    },
    {
        "kicker": "PACIFIC",
        "head": "SOLOMON ISLES SIGN TREATY",
        "deck": "Solomon Islands and Australia sign a treaty barring "
                "foreign bases.",
    },
    {
        "kicker": "USA",
        "head": "CIA AND ODNI HIT BY BREACH",
        "deck": "US intelligence agencies suffer a cyber breach of "
                "unclassified data.",
    },
]

COL3_TITLE = "THE DAY IN UTC"
TIMELINE = [
    "EARLY - Russian strikes kill two in Odesa, hit Kyiv.",
    "MORNING - Shenzhou-24 docks at Tiangong.",
    "MORNING - Australia signs a treaty with Solomon Islands.",
    "MIDDAY - US proposes tariffs of 20-40% on 14 partners.",
    "MIDDAY - Huawei convicted; Nvidia falls 3.9%.",
    "AFTERNOON - Houthis claim Ras Tanura refinery hit.",
    "AFTERNOON - Tankers hit mines in Hormuz Strait.",
    "AFTERNOON - Pope Leo XIV laments the COP31 failure.",
    "EVENING - Inter 2-0 Stuttgart; Liverpool win.",
    "EVENING - S&P -2.2%, Nasdaq -3.2% on Wall Street.",
]

BOTTOM = [
    ("MARKETS", "S&P 500 -2.2%, Nasdaq -3.2%; Nvidia -3.9% to $149.30; "
                "Brent crude $94.81; Anthropic falls below its $83 IPO price."),
    ("SPORT", "Champions League: Inter 2-0 Stuttgart, Liverpool 3-0 Club "
              "Brugge, Arsenal 1-1 Dortmund, Man City 2-2 Napoli. Davis Cup: "
              "Italy 2-1 South Korea."),
    ("ALSO", "Macy's Thanksgiving parade postponed by storm; Trump pardons "
             "two turkeys; Abrego Garcia leaves the US for Spain."),
]
FOOTER = ("Sources: Reuters, AP, BBC, NYT, Just Security, IANS. "
          "Drawn by a program.")


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def rule(cv, y, color=NAVY, thick=2):
    cv.rect(MARGIN, y, CW, thick, color)
    return y + thick


def section_header(cv, x, y, w, title):
    cv.rect(x, y, w, 24, NAVY)
    cv.text(title, x + 8, y + 5, 2, PAPER, bold=True)
    return y + 24


def story_block(cv, x, y, w, story, max_deck_lines=3):
    cv.text(story["kicker"], x, y, 2, RED, bold=True)
    y += 17
    for line in cv.wrap(story["head"], w, 2, spacing=1)[:2]:
        cv.text(line, x, y, 2, INK, bold=True)
        y += 17
    y += 2
    for line in cv.wrap(story["deck"], w, 2, spacing=1)[:max_deck_lines]:
        cv.text(line, x, y, 2, INK)
        y += 17
    return y + 9


def draw_globe(cv, cx, cy, r):
    """Small wireframe globe for the masthead."""
    cv.ring(cx, cy, r, NAVY)
    for dy in (-r // 2, 0, r // 2):
        half = int((r * r - dy * dy) ** 0.5)
        cv.hline(cx - half, cy + dy, 2 * half, NAVY)
    for dx in (-r // 2, 0, r // 2):
        half = int((r * r - dx * dx) ** 0.5)
        cv.vline(cx + dx, cy - half, 2 * half, NAVY)


def draw_tanker(cv, x, y):
    """Simple tanker silhouette in the lead box: hull, containers, funnel."""
    # smoke puffs, tucked right above the funnel
    for sx, sy, sr in ((x + 146, y + 10, 5), (x + 154, y + 4, 4), (x + 162, y + 10, 4)):
        cv.disc(sx, sy, sr, GREY)
    # funnel
    cv.rect(x + 140, y + 16, 22, 30, RED)
    cv.rect(x + 140, y + 16, 22, 6, PAPER)
    # containers on deck
    for i, col in enumerate((STEEL, GOLD, RED, STEEL)):
        cv.rect(x + 30 + i * 26, y + 26, 22, 20, col)
    # mast with a small flag
    cv.vline(x + 12, y + 14, 32, NAVY)
    cv.hline(x + 6, y + 14, 14, NAVY)
    cv.rect(x + 12, y + 8, 12, 6, RED)
    # hull
    cv.rect(x, y + 46, 190, 20, NAVY)
    cv.rect(x, y + 46, 190, 4, STEEL)
    # bow wedge (stepped)
    cv.rect(x + 190, y + 50, 10, 16, NAVY)
    cv.rect(x + 200, y + 54, 8, 12, NAVY)
    # waves
    for wy, ww in ((y + 74, 150), (y + 80, 190), (y + 86, 130)):
        cv.hline(x + 10, wy, ww, STEEL)
        cv.hline(x + 30, wy + 3, ww - 40, STEEL)


def draw_masthead(cv):
    y = 12
    cv.rect(MARGIN, y, CW, 3, NAVY)
    cv.text_center("ONE DAY - ONE IMAGE - ALL THE WORLD'S NEWS",
                   512, 24, 2, GREY, bold=True)
    draw_globe(cv, 72, 66, 21)
    # date badge, right side
    cv.rect(918, 42, 78, 54, NAVY)
    cv.rect(920, 44, 74, 50, PAPER)
    cv.text_center("25", 957, 47, 4, RED, bold=True)
    cv.text_center("NOV", 957, 79, 2, NAVY, bold=True)
    cv.text_center("WEDNESDAY 25 NOVEMBER 2026", 512, 52, 5, INK, bold=True)
    cv.text_center("EVERY STORY BELOW HAPPENED OR WAS FIRST REPORTED ON THIS DAY",
                   512, 98, 2, RED, bold=True)
    rule(cv, 118, NAVY, 2)
    rule(cv, 122, NAVY, 1)
    return 130

def draw_lead(cv, y):
    cv.text(LEAD_KICKER, MARGIN, y, 2, RED, bold=True)
    y += 18
    for line in LEAD_HEAD:
        cv.text(line, MARGIN, y, 4, INK, bold=True)
        y += 32
    y += 4
    for line in cv.wrap(LEAD_DECK, 720, 2, spacing=1):
        cv.text(line, MARGIN, y, 2, INK)
        y += 18
    draw_tanker(cv, 790, 158)
    return y + 6


def draw_second_row(cv, y):
    half = 474
    for i, s in enumerate(SECOND):
        x = MARGIN + i * (half + 20)
        yy = y
        cv.text(s["kicker"], x, yy, 2, RED, bold=True)
        yy += 17
        for line in cv.wrap(s["head"], half, 3, spacing=1):
            cv.text(line, x, yy, 3, INK, bold=True)
            yy += 23
        yy += 2
        for line in cv.wrap(s["deck"], half, 2, spacing=1):
            cv.text(line, x, yy, 2, INK)
            yy += 18
    return y + 140


def draw_columns(cv, y):
    col_w = 310
    gap = 19
    x1, x2, x3 = MARGIN, MARGIN + col_w + gap, MARGIN + 2 * (col_w + gap)
    end1 = section_header(cv, x1, y, col_w, COL1_TITLE) + 10
    end2 = section_header(cv, x2, y, col_w, COL2_TITLE) + 10
    end3 = section_header(cv, x3, y, col_w, COL3_TITLE) + 10
    for s in COL1:
        end1 = story_block(cv, x1, end1, col_w, s)
    for s in COL2:
        end2 = story_block(cv, x2, end2, col_w, s)
    for item in TIMELINE:
        lines = cv.wrap(item, col_w, 2, spacing=1)[:2]
        for j, line in enumerate(lines):
            cv.text(line, x3, end3, 2, NAVY if j == 0 else INK, bold=(j == 0))
            end3 += 17
        end3 += 5
    return max(end1, end2, end3)


def draw_bottom(cv, y):
    rule(cv, y, NAVY, 2)
    y += 10
    for label, text in BOTTOM:
        full = label + ": " + text
        for line in cv.wrap(full, CW, 2, spacing=1):
            cv.text(line, MARGIN, y, 2, INK)
            y += 18
        y += 2
    cv.text(FOOTER, MARGIN, y + 2, 2, GREY)
    return y + 16


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    y = draw_masthead(cv)
    y = draw_lead(cv, y)
    rule(cv, y + 2, NAVY, 1)
    y = draw_second_row(cv, y + 12)
    rule(cv, y + 2, NAVY, 1)
    y = draw_columns(cv, y + 12)
    print("columns end y =", y)
    y = draw_bottom(cv, y + 8)
    print("bottom end y =", y)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, cv)
    print("wrote", path, size, "bytes")


if __name__ == "__main__":
    main()
