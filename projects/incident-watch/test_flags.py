#!/usr/bin/env python3
"""Cases the filter has to get right, taken from real posts it got wrong.

Every MUST NOT here was a live false positive on an earlier version. Run this
before changing PATTERNS, PROXIMITY or MAX_OTHERS.

Usage: LUNARCRUSH_API_KEY=... python3 test_flags.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from incident_watch import flags, get  # noqa: E402

CASES = [
    # The real $ZANO incident, 2026-09-25.
    ("ZANO", "Zano", True,
     "CEASE ALL ECONOMIC ACTIVITY INVOLVING ZANO AND fUSD IMMEDIATELY. The $Zano blockchain "
     "will be rolled back by approximately 24 hours. More information will follow."),
    ("ZANO", "Zano", True,
     "New event added 24-Hour Chain Rollback Zano $ZANO 25 Sep 2026 Impact 8/10"),
    # A synthetic incident, to prove the filter is not just memorising ZANO.
    ("CRV", "Curve DAO", True,
     "URGENT: $CRV pools have been exploited, do not interact with the protocol"),
    # 2026-09-27: a hackathon project called NOCK, listing other people's losses.
    ("NOCK", "Nockchain", False,
     "We built NOCK for the Meridian Buildathon. 2026 has been a brutal year for crypto with "
     "over $2B in reported losses from hacks. Just days ago Bitget suffered a $351.6M breach "
     "and temporarily paused withdrawals. Drift on Solana lost $285M. Attackers drained rsETH "
     "from Kelp and borrowed on Aave."),
    # 2026-09-25: the topic "elf" is not the coin.
    ("ELF", "aelf", False,
     "Let's keep pushing for SD models to get fixed. With all this talk about SD Skyborne "
     "models being stolen and re-stylizing HD models"),
    # 2026-09-25: the topic "lit" is not the coin either.
    ("LIT", "Lighter", False,
     "My neighbors side light for their trash cans. Motion sensitive. Someone stole it"),
]


def main() -> None:
    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    universe = {str(x["symbol"]).upper(): str(x["name"]) for _, x in L.iterrows()
                if isinstance(x.get("symbol"), str) and len(str(x["symbol"])) >= 3}

    failures = 0
    for symbol, name, should_flag, text in CASES:
        got = flags(text, symbol, name, universe)
        ok = bool(got) == should_flag
        failures += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} ${symbol:<6} expect {'flag' if should_flag else 'clean':<5} "
              f"got {'flag' if got else 'clean':<5} {','.join(got) if got else ''}")
    print(f"\n{len(CASES) - failures} of {len(CASES)} pass")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
