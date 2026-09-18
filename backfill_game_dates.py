"""
One-time (or re-runnable) backfill for game_dates.csv's missing partner
rows -- see the identically-named function get_min.py/get_min.ipynb now
run automatically at generation time. This script applies the same fix
to an already-generated game_dates.csv without re-running the full
per-team NBA API scrape.

Usage:
    python backfill_game_dates.py
"""

import pandas as pd

PATHS = ["game_dates.csv", "../web_app/data/game_dates.csv"]


def backfill_missing_partner_rows(df):
    counts = df["GAME_ID"].value_counts()
    lone_game_ids = counts[counts == 1].index
    if len(lone_game_ids) == 0:
        print("No missing partner rows found.")
        return df

    abbrev_to_id = (
        df.groupby("team")["TEAM_ID"].agg(lambda s: s.value_counts().idxmax()).to_dict()
    )

    missing_rows = []
    for _, row in df[df["GAME_ID"].isin(lone_game_ids)].iterrows():
        missing_team = row["opp_team"]
        if missing_team not in abbrev_to_id:
            print(f"Could not backfill {row['GAME_ID']}: unknown team abbrev {missing_team}")
            continue
        missing_rows.append(
            {
                "GAME_ID": row["GAME_ID"],
                "TEAM_ID": abbrev_to_id[missing_team],
                "HTM": row["HTM"],
                "VTM": row["VTM"],
                "date": row["date"],
                "season": row["season"],
                "playoffs": row["playoffs"],
                "team": missing_team,
                "opp_team": row["team"],
            }
        )

    if missing_rows:
        print(f"Backfilling {len(missing_rows)} missing partner row(s), game_ids: {sorted(lone_game_ids.tolist())}")
        df = pd.concat([df, pd.DataFrame(missing_rows)], ignore_index=True)

    return df


def main():
    df = pd.read_csv(PATHS[0])
    before = len(df)

    df = backfill_missing_partner_rows(df)
    df.sort_values(by="date", inplace=True)

    added = len(df) - before
    for path in PATHS:
        df.to_csv(path, index=False)
        print(f"Wrote {len(df)} rows ({added:+d}) to {path}")


if __name__ == "__main__":
    main()
