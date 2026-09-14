"""Regenerate game_dates.csv from already-downloaded local files, applying
the new NOK-era fix alongside the two existing CHA/NOP fixes. Reads only
local team/{year}[ps]/{team_id}.csv files -- no network access, no scraping.

Run from ~/basketball/shot_data/:
    python rebuild_game_dates.py

Writes to game_dates_fixed.csv for review FIRST -- does not overwrite the
real game_dates.csv or ../web_app/data/game_dates.csv. Compare the two, then
copy over manually once you're satisfied.
"""
import os

import pandas as pd
from nba_api.stats.static import teams

START_YEAR = 1997
END_YEAR = 2027


def get_dates(start_year, end_year):
    """Exact reimplementation of get_min.py's get_dates() -- reads only
    already-downloaded local files, no network calls."""
    dates = []
    for year in range(start_year, end_year):
        for team in teams.get_teams():
            team_id = team['id']
            path = f'team/{year}ps/{team_id}.csv'
            if os.path.exists(path):
                df = pd.read_csv(path)
                df = df[['GAME_ID', 'TEAM_ID', 'HTM', 'VTM', 'GAME_DATE']]
                df.rename(columns={'GAME_DATE': 'date'}, inplace=True)
                df.drop_duplicates(inplace=True)
                df['season'] = f'{year-1}-{str(year)[-2:]}'
                df['playoffs'] = True
                dates.append(df)
        for team in teams.get_teams():
            team_id = team['id']
            path = f'team/{year}/{team_id}.csv'
            if os.path.exists(path):
                df = pd.read_csv(path)
                df = df[['GAME_ID', 'TEAM_ID', 'HTM', 'VTM', 'GAME_DATE']]
                df.rename(columns={'GAME_DATE': 'date'}, inplace=True)
                df.drop_duplicates(inplace=True)
                df['season'] = f'{year-1}-{str(year)[-2:]}'
                df['playoffs'] = False
                dates.append(df)
    return pd.concat(dates)


def fix_cha_nop(df):
    """Unchanged from get_min.py: remap pre-expansion Charlotte Hornets rows
    to NOP. TEAM_ID 1610612766 (CHA) before 2004-05 belongs to the NOP
    franchise -- the modern CHA is the 2004 expansion Bobcats."""
    OLD_CHA_SEASONS = {'1996-97', '1997-98', '1998-99', '1999-00', '2000-01', '2001-02'}
    NOP_TEAM_ID = 1610612740

    mask = (df['TEAM_ID'] == 1610612766) & (df['season'].isin(OLD_CHA_SEASONS))
    df.loc[mask, 'TEAM_ID'] = NOP_TEAM_ID
    for col in ('team', 'opp_team', 'HTM', 'VTM'):
        if col in df.columns:
            df.loc[mask & (df[col] == 'CHA'), col] = 'NOP'
    return df


def fix_cha_nop_post_merge(df):
    """Unchanged from get_min.py."""
    OLD_CHA_SEASONS = {'1996-97', '1997-98', '1998-99', '1999-00', '2000-01',
                        '2001-02', '2002-03', '2003-04'}
    early = df['season'].isin(OLD_CHA_SEASONS)
    for col in ('team', 'opp_team', 'HTM', 'VTM'):
        if col in df.columns:
            df.loc[early & (df[col] == 'CHA'), col] = 'NOP'
    return df


def fix_nok_seasons(df):
    """NEW: post-Katrina New Orleans/Oklahoma City Hornets era. TEAM_ID
    1610612740's own HTM/VTM correctly say 'NOK' for these two seasons
    (era-accurate, from the raw API), but 'team' gets computed via the
    CURRENT-day name_map lookup ('NOP') instead -- causing the opp_team
    formula to treat 'NOK' as the opponent instead of recognizing it as this
    team's own historical name. Confirmed directly against game 20500025:
    raw HTM='NOK', VTM='SAC', computed team='NOP' -- matched neither.
    """
    NOK_SEASONS = {'2005-06', '2006-07'}
    mask = (df['TEAM_ID'] == 1610612740) & (df['season'].isin(NOK_SEASONS))
    for col in ('HTM', 'VTM'):
        df.loc[mask & (df[col] == 'NOK'), col] = 'NOP'
    return df


def main():
    dates = get_dates(START_YEAR, END_YEAR)

    name_map = {t['id']: t['abbreviation'] for t in teams.get_teams()}
    dates['team'] = dates['TEAM_ID'].map(name_map)

    acronym_changes = {
        "CHH": "CHA", "NOH": "NOP", "NJN": "BKN", "SEA": "OKC", "WSB": "WAS",
        "VAN": "MEM", "SDC": "LAC", "KCK": "SAC", "FTW": "DET", "SFW": "GSW",
        "STL": "ATL"
    }
    dates['team'] = dates['team'].replace(acronym_changes)
    dates['HTM'] = dates['HTM'].replace(acronym_changes)
    dates['VTM'] = dates['VTM'].replace(acronym_changes)

    dates = fix_cha_nop(dates)
    print('first nop fix applied')
    dates = fix_cha_nop_post_merge(dates)
    print('second nop fix applied')
    dates = fix_nok_seasons(dates)
    print('third fix (nok seasons) applied')

    dates['opp_team'] = dates.apply(
        lambda row: row['VTM'] if row['team'] == row['HTM'] else row['HTM'], axis=1)

    dates.sort_values(by='date', inplace=True)

    out_path = 'game_dates_fixed.csv'
    dates.to_csv(out_path, index=False)
    print(f'Wrote {out_path} -- review before replacing the real game_dates.csv')

    # Quick, targeted confirmation on the known-bad game.
    check = dates[(dates.TEAM_ID == 1610612740) & (dates.GAME_ID.astype(str).str.contains('20500025'))]
    if not check.empty:
        print()
        print('Confirmation for game 20500025 (the known-bad case):')
        print(check[['GAME_ID', 'season', 'team', 'HTM', 'VTM', 'opp_team']].to_string(index=False))


if __name__ == '__main__':
    main()