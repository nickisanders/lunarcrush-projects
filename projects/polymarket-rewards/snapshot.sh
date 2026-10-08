#!/bin/bash
# Daily capture of which Polymarket markets are paying rewards.
#
# Reward status is unrecoverable once a market closes: across 80 closed markets
# sampled on 2026-10-08, none retained clobRewards or rewardsMinSize on either
# API. A window that was not snapshotted while its markets were open can never
# be labelled, so this has to run before the data is wanted, not after.
#
# Installed as a LaunchAgent; see README. Logs to out/snapshot.log.
set -u
cd "$(dirname "$0")" || exit 1
mkdir -p out
printf '\n=== %s ===\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> out/snapshot.log
/usr/bin/env python3 markets.py --live-snapshot >> out/snapshot.log 2>&1
code=$?
# Keep a year of dated snapshots and drop the rest: each is ~1.7MB and the
# comparison only ever looks back over weeks.
find out/history -name 'markets-live-*.json' -mtime +365 -delete 2>/dev/null
printf 'exit %s\n' "$code" >> out/snapshot.log
exit $code
