"""Trace the exact team/HTM/VTM/TEAM_ID values for a known-bad game, using
the already-generated team/{year}[ps]/{team_id}.csv files get_min.py itself
reads -- no need to re-run the scraper.

Run from ~/basketball/shot_data/:
    python diagnose_opp_team_bug.py

Confirms exactly where the mismatch happens: whether 'team' (computed from
the CURRENT-day numeric-ID lookup) actually disagrees with HTM/VTM (the raw,
historical values) for one of the 82 known-bad games -- before writing any
fix to get_min.py.
"""
import pandas as pd
from nba_api.stats.static import teams

# Game 20500025 is one of the 82 confirmed-bad games (2005-06 season,
# New Orleans's own numeric TEAM_ID historically appears as 1610612766
# in this era's raw per-game files).
KNOWN_BAD_GAME_ID = '0020500025'  # zero-padded to match get_min.py's convention
YEAR = 2006  # 2005-06 season -> year = start_year + 1
NOP_TEAM_ID = 1610612740
ALT_TEAM_ID = 1610612766

nba_teams = teams.get_teams()
name_map = {t['id']: t['abbreviation'] for t in nba_teams}

print(f"Current-day name_map lookup:")
print(f"  {NOP_TEAM_ID} -> {name_map.get(NOP_TEAM_ID)!r}")
print(f"  {ALT_TEAM_ID} -> {name_map.get(ALT_TEAM_ID)!r}")
print()

for team_id in (NOP_TEAM_ID, ALT_TEAM_ID):
    path = f'team/{YEAR}/{team_id}.csv'
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"{path}: not found")
        continue

    df['GAME_ID'] = df['GAME_ID'].astype(str).str.zfill(10)
    row = df[df['GAME_ID'] == KNOWN_BAD_GAME_ID]

    if row.empty:
        print(f"{path}: game {KNOWN_BAD_GAME_ID} not present in this file")
        continue

    r = row.iloc[0]
    computed_team = name_map.get(team_id)
    print(f"{path}, game {KNOWN_BAD_GAME_ID}:")
    print(f"  raw HTM={r.get('HTM')!r}  VTM={r.get('VTM')!r}")
    print(f"  current-day computed 'team' (via name_map): {computed_team!r}")
    print(f"  does computed team match HTM? {computed_team == r.get('HTM')}")
    print(f"  does computed team match VTM? {computed_team == r.get('VTM')}")
    if computed_team not in (r.get('HTM'), r.get('VTM')):
        print(f"  *** MISMATCH: computed team matches NEITHER HTM nor VTM ***")
    print()