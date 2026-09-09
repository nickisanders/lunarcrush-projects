#!/usr/bin/env python3
"""Where a launch's volume actually sits relative to its money.

Screeners rank by volume. This draws volume and liquidity side by side, split
between the contracts turning their whole depth over more than 100x a day and
everything else. On $LAPTOP's announced launch day, 82% of the volume ran
through 7.2% of the money.

Usage: python3 concentration_chart.py out/laptop-day3.json
"""

import json
import sys
from pathlib import Path

BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
RED, ORANGE, GREY, BLUE = "#f85149", "#f7931a", "#6e7681", "#58a6ff"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
CHURN_TURNOVER = 100


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    body = esc(s)
    if weight >= 700 and " " in str(s):
        # librsvg drops the space between words at bold weights, so each word
        # after the first carries its own explicit offset. A word ending in "%"
        # needs a wider one; the glyph sits tight against its advance.
        words = str(s).split(" ")
        parts = [esc(words[0])]
        for prev, w in zip(words, words[1:]):
            parts.append(f'<tspan dx="{size * (0.45 if prev.endswith("%") else 0.30):.2f}">{esc(w)}</tspan>')
        body = "".join(parts)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def money(n: float) -> str:
    if n >= 1e9: return f"${n / 1e9:.2f}B"
    if n >= 1e6: return f"${n / 1e6:.1f}M"
    if n >= 1e3: return f"${n / 1e3:.0f}k"
    return f"${n:,.0f}"


def render(s: dict) -> str:
    bc = {k: v for k, v in s["byContract"].items() if not v.get("implausible")}
    churn = {k: v for k, v in bc.items()
             if v["liquidity"] and v["volume24h"] / v["liquidity"] > CHURN_TURNOVER}
    rest = {k: v for k, v in bc.items() if k not in churn}

    cv = sum(v["volume24h"] for v in churn.values())
    cl = sum(v["liquidity"] for v in churn.values())
    rv = sum(v["volume24h"] for v in rest.values())
    rl = sum(v["liquidity"] for v in rest.values())
    tv, tl = cv + rv, cl + rl

    W, H = 1300, 820
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    o.append(txt(60, 78, 40, TEXT, "82% of the volume. 7.2% of the money.", 700))
    o.append(txt(60, 118, 20, SUB,
                 f"${s['ticker']} on its announced launch day. "
                 f"{s['contracts']} contracts carry the name."))

    # Two stacked bars: volume and liquidity, each split churn vs rest.
    x0, bw, gap = 60, 1180, 0
    rows = [("24h VOLUME", tv, cv, rv, 200), ("LIQUIDITY", tl, cl, rl, 380)]
    for label, total, c, r, y in rows:
        o.append(txt(x0, y - 16, 17, SUB, label, 700))
        o.append(txt(x0 + bw, y - 16, 17, TEXT, money(total), 700, "end"))
        cw = bw * (c / total) if total else 0
        o.append(f'<rect x="{x0}" y="{y}" width="{cw:.1f}" height="86" fill="{RED}" rx="3"/>')
        o.append(f'<rect x="{x0 + cw:.1f}" y="{y}" width="{bw - cw:.1f}" height="86" fill="{GREY}" rx="3"/>')
        pct = c / total * 100 if total else 0
        # Percentage label goes inside the red block when it fits, else beside it.
        if cw > 150:
            o.append(txt(x0 + 20, y + 56, 34, "#ffffff", f"{pct:.0f}%", 700))
        else:
            o.append(txt(x0 + cw + 20, y + 56, 34, RED, f"{pct:.1f}%", 700))

    o.append(f'<rect x="60" y="500" width="1180" height="1" fill="#30363d"/>')

    o.append(txt(60, 552, 19, RED, "■", 700))
    o.append(txt(86, 552, 19, TEXT, f"{len(churn)} contracts turning over more than {CHURN_TURNOVER}x a day", 700))
    o.append(txt(86, 580, 18, SUB, f"{money(cv)} of volume standing on {money(cl)} of liquidity"))

    o.append(txt(660, 552, 19, GREY, "■", 700))
    o.append(txt(686, 552, 19, TEXT, f"The other {len(rest)} contracts", 700))
    o.append(txt(686, 580, 18, SUB, f"{money(rv)} of volume on {money(rl)} of liquidity"))

    o.append(f'<rect x="60" y="624" width="1180" height="80" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, 656, 18, TEXT,
                 "Volume is what screeners rank by. Liquidity is what you get back when you sell.", 700))
    o.append(txt(84, 684, 17, SUB,
                 "Nothing here identifies which contract, if any, is official. A screener cannot tell you either."))

    o.append(txt(60, 762, 16, GREY, "Source: GeckoTerminal, 2026-09-09. Pools reporting reserves at or above"))
    o.append(txt(60, 786, 16, GREY, "their own FDV are excluded: that depth is the token, not money."))
    o.append(txt(1240, 786, 16, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "out/laptop-day3.json")
    out = src.parent / "laptop-concentration.svg"
    out.write_text(render(json.loads(src.read_text())))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
