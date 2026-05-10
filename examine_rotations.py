"""
examine_rotations.py
====================
Examines NBA rotation CSV files to report:
  - Coverage: which games/teams are present
  - Duplication: Seattle/OKC double-row issue
  - Starter reliability: how many games have all 5 starters at IN_TIME_REAL==0
  - Missing games: games in game_dates not covered by rotation data
  - Per-team coverage summary

Usage
-----
    python examine_rotations.py                        # default: rotations/2009
    python examine_rotations.py rotations/2010
    python examine_rotations.py rotations/2009 --season 2008-09
"""

import os
import sys
import argparse
import pandas as pd

GAME_DATES_URL = (
    "https://raw.githubusercontent.com/gabriel1200/shot_data"
    "/refs/heads/master/game_dates.csv"
)


def load_all_rotations(rot_dir: str) -> pd.DataFrame:
    frames = []
    for f in os.listdir(rot_dir):
        if not f.endswith('.csv'):
            continue
        try:
            df = pd.read_csv(os.path.join(rot_dir, f), low_memory=False)
            frames.append(df)
        except Exception as e:
            print(f"  Could not read {f}: {e}")
    if not frames:
        print(f"No CSV files found in {rot_dir}")
        sys.exit(1)
    return pd.concat(frames, ignore_index=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rot_dir', nargs='?', default='rotations/2009')
    parser.add_argument('--season', default='2008-09',
                        help='Season string for game_dates lookup (e.g. 2008-09)')
    parser.add_argument('--playoffs', action='store_true')
    args = parser.parse_args()

    print(f"Loading rotation files from: {args.rot_dir}")
    rot = load_all_rotations(args.rot_dir)
    print(f"Total rows loaded: {len(rot):,}")
    print(f"Columns: {list(rot.columns)}")
    print()

    # ── 1. Duplication check ─────────────────────────────────────────────────
    key_cols = ['GAME_ID', 'PERSON_ID', 'IN_TIME_REAL', 'OUT_TIME_REAL']
    existing = [c for c in key_cols if c in rot.columns]
    dupes    = rot.duplicated(subset=existing).sum()
    total    = len(rot)
    print(f"── Duplication ──────────────────────────────────────────────────")
    print(f"  Total rows:      {total:,}")
    print(f"  Duplicate rows:  {dupes:,}")
    print(f"  Unique stints:   {total - dupes:,}")
    if dupes == total // 2:
        print(f"  ⚠  Exactly 2× duplication detected (franchise relocation artifact)")
    print()

    rot_dedup = rot.drop_duplicates(subset=existing).copy() if dupes else rot.copy()

    # ── 2. Coverage overview ─────────────────────────────────────────────────
    n_games   = rot_dedup['GAME_ID'].nunique()
    n_players = rot_dedup['PERSON_ID'].nunique()
    n_teams   = rot_dedup['TEAM_ID'].nunique() if 'TEAM_ID' in rot_dedup.columns else '?'
    print(f"── Coverage (after dedup) ───────────────────────────────────────")
    print(f"  Games:   {n_games}")
    print(f"  Players: {n_players}")
    print(f"  Teams:   {n_teams}")
    print()

    # ── 3. Starter reliability ───────────────────────────────────────────────
    if 'IN_TIME_REAL' in rot_dedup.columns:
        starters = rot_dedup[rot_dedup['IN_TIME_REAL'] == 0]
        per_game_starters = starters.groupby('GAME_ID')['PERSON_ID'].count()
        expected_per_game = 10 if n_teams > 1 else 5
        full_5  = (per_game_starters == expected_per_game).sum()
        short   = (per_game_starters < expected_per_game).sum()
        missing = n_games - len(per_game_starters)
        print(f"── Starter reliability (IN_TIME_REAL == 0) ──────────────────────")
        print(f"  Games with exactly 5 starters: {full_5} / {n_games} "
              f"({full_5/n_games*100:.0f}%)")
        print(f"  Games with < 5 starters:       {short}")
        print(f"  Games with 0 starters:         {missing}")
        if short > 0:
            print(f"  Starter count distribution:")
            print(per_game_starters.value_counts().sort_index()
                  .to_string(header=False))
        print()

    # ── 4. Stints per player per game ────────────────────────────────────────
    stints_per = rot_dedup.groupby(['GAME_ID', 'PERSON_ID']).size()
    print(f"── Stints per player per game ───────────────────────────────────")
    print(stints_per.value_counts().sort_index().to_string(header=False))
    print()

    # ── 5. Per-team coverage ─────────────────────────────────────────────────
    if 'TEAM_ID' in rot_dedup.columns and 'TEAM_CITY' in rot_dedup.columns:
        team_games = (rot_dedup.groupby(['TEAM_ID', 'TEAM_CITY'])['GAME_ID']
                      .nunique().reset_index()
                      .rename(columns={'GAME_ID': 'games'}))
        team_games = team_games.sort_values('games', ascending=False)
        print(f"── Games per team ───────────────────────────────────────────────")
        print(team_games.to_string(index=False))
        print()

        # Flag teams with far fewer games than expected
        median_games = team_games['games'].median()
        low_coverage = team_games[team_games['games'] < median_games * 0.5]
        if not low_coverage.empty:
            print(f"  ⚠  Teams with suspiciously low coverage (< 50% of median):")
            print(low_coverage.to_string(index=False))
            print()

    # ── 6. Compare against game_dates ────────────────────────────────────────
    print(f"── Coverage vs game_dates ({args.season}) ───────────────────────")
    try:
        gd = pd.read_csv(GAME_DATES_URL, dtype={'GAME_ID': str})
        mask = (gd['season'] == args.season) & (gd['playoffs'] == args.playoffs)
        expected_ids = set(gd[mask]['GAME_ID'].str.lstrip('0').astype(int).unique())
        rotation_ids = set(rot_dedup['GAME_ID'].astype(int).unique())
        missing_from_rot = expected_ids - rotation_ids
        extra_in_rot     = rotation_ids - expected_ids

        print(f"  Expected games (game_dates): {len(expected_ids)}")
        print(f"  Games in rotation files:     {len(rotation_ids)}")
        print(f"  Missing from rotation:       {len(missing_from_rot)}")
        print(f"  Extra in rotation:           {len(extra_in_rot)}")
# Add after the starter reliability block:
        print(f"── IN_TIME_REAL distribution (smallest values) ──────────────────")
        smallest = rot_dedup['IN_TIME_REAL'].sort_values().unique()[:10]
        print(f"  Smallest unique values: {list(smallest)}")
        print(f"  Rows with IN_TIME_REAL < 100: {(rot_dedup['IN_TIME_REAL'] < 100).sum()}")
        print(f"  Rows with IN_TIME_REAL < 600: {(rot_dedup['IN_TIME_REAL'] < 600).sum()}")
        if missing_from_rot:
            print(f"\n  Missing game IDs (first 20): "
                  f"{sorted(missing_from_rot)[:20]}")
    except Exception as e:
        print(f"  Could not fetch game_dates : {e}")


if __name__ == '__main__':
    main()