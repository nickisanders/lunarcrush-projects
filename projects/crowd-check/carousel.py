#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for one coin from the screen.

Reads out/spotlight-<sym>.json, so the slides always match the last run of
spotlight.py. Numbers typed into slides by hand go stale the moment the data
moves, and the current day keeps settling for hours after midnight UTC.

Writes out/instagram/<sym>-N.svg and rasterizes them.

Usage: python3 carousel.py STRK
"""

import argparse
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#161b22"
RED, GREEN, AMBER = "#f85149", "#3fb950", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 5


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    """librsvg drops word spaces at weight >= 700, so set them by hand. The %
    glyph overhangs its advance width and needs a wider gap after it."""
    words = str(text).split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        parts.append(f'<tspan dx="{size * (0.45 if prev.endswith("%") else 0.30):.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x, y, size, fill, content, weight=400, anchor="start") -> str:
    body = heavy(content, size) if weight >= 700 and " " in str(content) else esc(content)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>')


def lines_for(text, size, width, weight=400) -> list[str]:
    """Greedy wrap at an estimated glyph width, measured against this font."""
    per = size * (0.54 if weight >= 700 else 0.50)
    out, line = [], []
    for word in str(text).split():
        if line and (len(" ".join(line + [word])) * per) > width:
            out.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        out.append(" ".join(line))
    return out


class Flow:
    """A cursor that advances by what it actually drew.

    Slides used fixed y positions under a wrapper that returns a variable
    number of lines, so a paragraph one line longer than expected ran straight
    into the next block. Nothing here can collide, because nothing here guesses
    where the previous block ended.
    """

    def __init__(self, y: int, x: int = M, width: int = W - 2 * M):
        self.y, self.x, self.width, self.parts = y, x, width, []

    def say(self, size, fill, text, weight=400, gap=34, lh=1.42):
        for ln in lines_for(text, size, self.width, weight):
            self.parts.append(txt(self.x, self.y, size, fill, ln, weight))
            self.y += size * lh
        self.y += gap
        return self

    def gap(self, n):
        self.y += n
        return self

    def raw(self, svg, advance=0):
        self.parts.append(svg)
        self.y += advance
        return self

    # The footer sits at H-112 and the dots at H-60, so content past this is
    # colliding with them even though the renderer will happily draw it.
    SAFE = H - 150

    def svg(self) -> str:
        if self.y > self.SAFE:
            print(f"  WARNING: content runs to y={self.y:.0f}, past the safe area "
                  f"at {self.SAFE}", flush=True)
        return "".join(self.parts)


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def slide1(d) -> str:
    f = Flow(300)
    f.say(84, TEXT, f"{d['name']}'s price is up {d['price_pct_7d']:.0f}% this week.", 700, gap=56)
    f.say(52, SUB, "Most pumps arrive with a crowd that was already there, just shouting louder.")
    f.gap(120)
    f.say(46, GREEN if d["crowd_grew"] else AMBER, "So I counted the people.", 700)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    head = ("The crowd actually turned up." if d["crowd_grew"]
            else "The crowd went the other way.")
    f = Flow(250)
    f.say(64, TEXT, head, 700, gap=90)
    for m in d["metrics"]:
        up = m["after"] >= m["before"]
        y = f.y
        f.raw(txt(M, y, 38, SUB, m["label"].split(",")[0]))
        f.raw(txt(M, y + 62, 54, TEXT, f"{m['before']:,}", 700))
        f.raw(txt(M + 250, y + 62, 46, SUB, "to"))
        f.raw(txt(M + 350, y + 62, 54, GREEN if up else RED, f"{m['after']:,}", 700), 180)
    return frame(2, f.svg(), "per day, this week against the 30 days before")


def slide3(d) -> str:
    rose = d["spam_rose"]
    f = Flow(250)
    f.say(64, TEXT, "And the junk took over." if rose else "And the junk thinned out.",
          700, gap=80)
    y = f.y
    f.raw(txt(M, y, 40, SUB, "spam as a share of posts"))
    f.raw(txt(M, y + 96, 86, SUB, f"{d['spam_before']*100:.0f}%", 700))
    f.raw(txt(M + 230, y + 96, 60, SUB, "to"))
    f.raw(txt(M + 360, y + 96, 86, RED if rose else GREEN,
              f"{d['spam_after']*100:.0f}%", 700), 180)
    if rose:
        f.say(48, TEXT, "Fewer people, and a bigger share of what is left is junk. "
                        "That is what a bought wave looks like.", gap=40)
        f.say(38, SUB, "This token runs a high share even when quiet, so the lift against "
                       "its own norm is the signal, not the level.")
    else:
        f.say(48, TEXT, "A bought wave runs the other way. Paid posts crowd in as the "
                        "price goes, and the share climbs.", gap=40)
        f.say(42, GREEN, "Real people dilute spam. Bots concentrate it.", 700)
    return frame(3, f.svg())


def slide4(d) -> str:
    f = Flow(250)
    if not d["crowd_grew"]:
        f.say(64, TEXT, "So what is moving the price?", 700, gap=40)
        f.say(50, SUB, "Not a crowd. Fewer people are posting than a month ago, they are "
                       "posting less, and engagement has more than halved.", gap=52)
        f.say(50, AMBER, "This does not identify who is behind anything.", 700, gap=34)
        f.say(40, SUB, "Amplification patterns are compatible with bots, with paid "
                       "promotion, and with an unusually tight community.")
        return frame(4, f.svg())

    pk = d["year_peak"] or {}
    mult = (d["price"] / pk["price"]) if pk.get("price") else 0
    f.say(64, TEXT, "So the attention is real.", 700, gap=30)
    f.say(56, AMBER, "Whether that is good news is a different question.", 700, gap=80)
    y = f.y
    f.raw(txt(M, y, 44, SUB, "people posting today"))
    f.raw(txt(M, y + 86, 90, TEXT, f"{d['today_people']:,}", 700), 150)
    f.say(46, SUB, f"Near its highest in a year. The last time it was this loud was "
                   f"{pk.get('day','')}, when it traded at ${pk.get('price',0):.4f}.", gap=44)
    f.say(50, AMBER, f"Today's price is {mult:.0f}x higher.", 700)
    return frame(4, f.svg())


def slide5(d) -> str:
    mid = ("Not whether it is a good entry. My own backtest of coins whose conversation "
           "spikes into the top ten found the median one trailing Bitcoin by 21% three "
           "months later."
           if d["crowd_grew"] else
           "Not whether the price is wrong. A rally with a shrinking audience is the "
           "rarest pattern on this screen, and it is a reason to look closer rather than "
           "a verdict.")
    f = Flow(250)
    f.say(62, TEXT, "I measure whether a crowd is real.", 700, gap=60)
    f.say(48, SUB, mid, gap=70)
    f.say(52, RED, "Those are different questions.", 700, gap=50)
    f.say(42, SUB, "Method and code are public. Nothing here is advice.")
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("symbol")
    a = ap.parse_args()
    sym = a.symbol.upper()
    src = HERE / "out" / f"spotlight-{sym.lower()}.json"
    if not src.exists():
        raise SystemExit(f"No {src.name}. Run spotlight.py {sym} first.")
    d = json.loads(src.read_text())
    # A json written before the direction fields existed renders the wrong case
    # silently, so fail loudly and say what to do.
    missing = [k for k in ("crowd_grew", "spam_rose") if k not in d]
    if missing:
        raise SystemExit(f"{src.name} is missing {', '.join(missing)}. "
                         f"Re-run: python3 spotlight.py {sym}")

    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{sym.lower()}-{i}.svg"
        p.write_text(fn(d))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{sym.lower()}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
