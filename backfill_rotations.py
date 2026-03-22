#!/usr/bin/env python
# coding: utf-8
"""
backfill_rotations.py

Scans rotations/{year}/ and rotations/{year}ps/ folders for every season
from 2001 to 2026, identifies games that are present in the corresponding
team shot-chart CSVs but missing from the rotation files, fetches them from
the NBA stats API, and saves the results in the exact same format used by
get_shotrotations() in get_min.py.

Rotation file format  (one CSV per team per season):
    rotations/{year}{carry}/{team_id}.csv
    Columns (at minimum): GAME_ID, TEAM_ID, PERSON_ID, IN_TIME_REAL, OUT_TIME_REAL
    (all columns returned by the gamerotation endpoint are preserved)

Usage:
    python backfill_rotations.py                  # regular season only, 2001-2026
    python backfill_rotations.py --playoffs       # playoffs only
    python backfill_rotations.py --both           # regular season + playoffs
"""

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
import requests
from nba_api.stats.static import teams


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://stats.nba.com/",
}


def pull_rotation(url: str) -> pd.DataFrame:
    """Fetch a single game's rotation data from stats.nba.com and return a
    combined DataFrame of all resultSets (home + away rotations)."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    json_data = resp.json()

    frames = []
    for result_set in json_data["resultSets"]:
        data = result_set["rowSet"]
        columns = result_set["headers"]
        df = pd.DataFrame.from_records(data, columns=columns)
        frames.append(df)

    time.sleep(1.5)  # be polite to the API
    return pd.concat(frames, ignore_index=True)


def normalize_game_ids(game_ids) -> list:
    """Ensure every game ID starts with '00'."""
    result = []
    for gid in game_ids:
        gid = str(gid)
        if not gid.startswith("00"):
            gid = "00" + gid
        result.append(gid)
    return result


def get_team_map():
    """Return {team_id: abbreviation} and {abbreviation: team_id} mappings."""
    nba_teams = teams.get_teams()
    id_to_abr = {t["id"]: t["abbreviation"] for t in nba_teams}
    abr_to_id = {t["abbreviation"]: t["id"] for t in nba_teams}
    return id_to_abr, abr_to_id


# ---------------------------------------------------------------------------
# Core backfill logic
# ---------------------------------------------------------------------------

def get_games_from_shot_data(year: int, carry: str, team_id: int) -> list:
    """
    Return the list of (normalized) GAME_IDs for a team/season from the
    local shot-chart CSV that get_shotrotations() writes.
    Falls back to the GitHub mirror used by get_rotations() if the local
    file is absent.
    """
    local_path = f"team/{year}{carry}/{team_id}.csv"
    if os.path.exists(local_path):
        df = pd.read_csv(local_path, usecols=["GAME_ID"])
        return normalize_game_ids(df["GAME_ID"].dropna().unique().tolist())

    # GitHub mirror fallback (same URL pattern used in get_rotations)
    github_url = (
        f"https://raw.githubusercontent.com/gabriel1200/shot_data/master/"
        f"team/{year}{carry}/{team_id}.csv"
    )
    try:
        resp = requests.get(github_url, timeout=20)
        if resp.status_code == 200:
            df = pd.read_csv(github_url, usecols=["GAME_ID"])
            return normalize_game_ids(df["GAME_ID"].dropna().unique().tolist())
    except Exception:
        pass

    return []


def get_stored_game_ids(rotation_path: str) -> set:
    """Return the set of already-stored (normalized) GAME_IDs in a rotation CSV."""
    if not os.path.exists(rotation_path):
        return set()
    df = pd.read_csv(rotation_path, usecols=["GAME_ID"])
    return set(normalize_game_ids(df["GAME_ID"].dropna().unique().tolist()))


def backfill_team_rotation(year: int, team_id: int, carry: str,
                           missed_games: list) -> None:
    """
    For one team/season, fetch any games that appear in the shot data but
    are absent from the rotation file, then append them and save.
    """
    rotation_dir = f"rotations/{year}{carry}"
    rotation_path = f"{rotation_dir}/{team_id}.csv"

    # ----- determine which game IDs we need --------------------------------
    all_game_ids = get_games_from_shot_data(year, carry, team_id)
    if not all_game_ids:
        return  # no shot data for this team/season — skip

    stored_ids = get_stored_game_ids(rotation_path)
    missing_ids = list(set(all_game_ids) - stored_ids)

    if not missing_ids:
        return  # already complete

    print(f"  [{year}{carry}] team {team_id}: {len(missing_ids)} missing game(s)")

    # ----- fetch missing games ---------------------------------------------
    new_frames = []
    for game_id in missing_ids:
        url = f"https://stats.nba.com/stats/gamerotation?GameID={game_id}&LeagueID=00"
        try:
            df = pull_rotation(url)
            new_frames.append(df)
        except Exception as exc:
            print(f"    WARNING: could not fetch {game_id} — {exc}")
            missed_games.append(game_id)

    if not new_frames:
        return

    # ----- merge with existing data and save --------------------------------
    os.makedirs(rotation_dir, exist_ok=True)

    existing_frames = []
    if os.path.exists(rotation_path):
        existing_frames.append(pd.read_csv(rotation_path))

    combined = pd.concat(existing_frames + new_frames, ignore_index=True)

    # Normalize GAME_ID format
    combined["GAME_ID"] = combined["GAME_ID"].astype(str)
    combined["GAME_ID"] = np.where(
        combined["GAME_ID"].str[:2] == "00",
        combined["GAME_ID"],
        "00" + combined["GAME_ID"],
    )

    combined.drop_duplicates(inplace=True)

    # Filter to only this team's rows (mirrors get_shotrotations behaviour)
    combined = combined[combined["TEAM_ID"] == team_id]

    combined.to_csv(rotation_path, index=False)
    print(f"    Saved {len(combined)} rows → {rotation_path}")


def backfill_rotations(start_year: int = 2001,
                       end_year: int = 2026,
                       ps: bool = False) -> list:
    """
    Main entry point.  Iterates every season from start_year to end_year
    (inclusive on both ends) and every NBA team, filling in any rotation
    data that is missing from the local files.

    Parameters
    ----------
    start_year : int
        The 'year' part of the season label, e.g. 2001 means the 2000-01
        season.  Rotation files live at rotations/2001/ etc.
    end_year   : int
        Last year to process (inclusive).
    ps         : bool
        If True, process playoff rotations (rotations/{year}ps/).

    Returns
    -------
    list of game IDs that could not be fetched.
    """
    carry = "ps" if ps else ""
    _, abr_to_id = get_team_map()
    all_team_ids = list(abr_to_id.values())

    missed_games: list = []

    for year in range(start_year, end_year + 1):
        print(f"\n=== Season year: {year}{carry} ===")
        for team_id in all_team_ids:
            try:
                backfill_team_rotation(year, team_id, carry, missed_games)
            except Exception as exc:
                print(f"  ERROR on team {team_id} year {year}: {exc}")

    if missed_games:
        print(f"\nFailed to fetch {len(missed_games)} game(s): {missed_games}")
    else:
        print("\nAll rotation data is up to date.")

    return missed_games


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill missing NBA rotation CSVs from 2001 to 2026."
    )
    parser.add_argument(
        "--playoffs",
        action="store_true",
        help="Process playoff rotations instead of regular season.",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Process both regular season AND playoff rotations.",
    )
    parser.add_argument(
        "--start", type=int, default=2001,
        help="First year to process (default: 2001)."
    )
    parser.add_argument(
        "--end", type=int, default=2026,
        help="Last year to process (default: 2026)."
    )
    args = parser.parse_args()

    if args.both:
        backfill_rotations(args.start, args.end, ps=False)
        backfill_rotations(args.start, args.end, ps=True)
    elif args.playoffs:
        backfill_rotations(args.start, args.end, ps=True)
    else:
        backfill_rotations(args.start, args.end, ps=False)