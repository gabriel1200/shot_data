#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import requests
import os
from nba_api.stats.static import teams
import io

def get_dates(start_year=2025, end_year=2026):
    dates = []
    for year in range(start_year, end_year):
        for team in teams.get_teams():
            team_id = team['id']
            path = f'../team/{year}ps/{team_id}.csv'
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    required_cols = {'PLAYER_ID', 'HTM', 'VTM', 'GAME_DATE', 'GAME_ID'}
                    if required_cols.issubset(df.columns):
                        df = df[['PLAYER_ID', 'HTM', 'VTM', 'GAME_DATE', 'GAME_ID']]
                        df['year'] = year
                        df.drop_duplicates(inplace=True)
                        dates.append(df)
                except Exception:
                    continue
    if dates:
        return pd.concat(dates).drop_duplicates(subset='GAME_ID')
    else:
        return pd.DataFrame()

def fetch_game_csvs(dateframe, save_dir='game_data'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    all_game_data = []
    for _, row in dateframe.iterrows():
        year = int(row['year'])
        game_id = row['GAME_ID']
        url = f'https://raw.githubusercontent.com/gabriel1200/player_sheets/refs/heads/master/game_report/{year}/{game_id}.csv'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            if len(response.text.strip()) == 0:
                continue
            df = pd.read_csv(io.StringIO(response.text))
            df['GAME_ID'] = game_id
            df['date'] = row['GAME_DATE']
            df['HTM'] = row['HTM']
            df['VTM'] = row['VTM']
            df['year'] = year
            all_game_data.append(df)
            with open(os.path.join(save_dir, f'{year}_{game_id}.csv'), 'w', encoding='utf-8') as f:
                f.write(response.text)
        except Exception:
            print('game not found')
            continue
    if all_game_data:
        return pd.concat(all_game_data, ignore_index=True)
    else:
        return pd.DataFrame()

def process_and_save_series_data(df, dateframe):
    df.rename(columns={'GAME_DATE': 'date'}, inplace=True)
    if 'opp_team' in df.columns:
        df.drop(columns='opp_team', inplace=True)
    home = df[df.HTM == df.TEAM_ABBREVIATION].copy()
    away = df[df.VTM == df.TEAM_ABBREVIATION].copy()
    none = df[df.HTM.isna()].copy().reset_index(drop=True)
    home.drop(columns='HTM', inplace=True)
    home.rename(columns={'VTM': 'opp_team'}, inplace=True)
    away.drop(columns='VTM', inplace=True)
    away.rename(columns={'HTM': 'opp_team'}, inplace=True)
    home.drop_duplicates(inplace=True)
    away.drop_duplicates(inplace=True)
    frames = [home, away]
    if len(none) > 0:
        frames.append(none)
    df = pd.concat(frames, ignore_index=True)
    oppframe = df[['TEAM_ID', 'date', 'opp_team']].dropna(subset=['opp_team']).drop_duplicates()
    df.drop(columns='opp_team', inplace=True)
    df = df.merge(oppframe, on=['TEAM_ID', 'date'], how='left')
    df['team'] = df['TEAM_ABBREVIATION']
    teammap = dict(zip(df['TEAM_ABBREVIATION'], df['TEAM_ID']))
    player_index = df[['PLAYER_NAME', 'PLAYER_ID', 'team', 'TEAM_ID', 'opp_team', 'year']].copy()
    player_index['opp_id'] = player_index['opp_team'].map(teammap)
    player_index.drop_duplicates(inplace=True)
    index_path = 'series_index_players.csv'
    if os.path.exists(index_path):
        existing_index = pd.read_csv(index_path)
        combined = pd.concat([existing_index, player_index], ignore_index=True)
        combined.drop_duplicates(subset=['PLAYER_ID', 'team', 'TEAM_ID', 'opp_team', 'year'], keep='last', inplace=True)
        combined.to_csv(index_path, index=False)
    else:
        player_index.to_csv(index_path, index=False)
    df = df.dropna(subset=['opp_team'])
    df['opp_id'] = df['opp_team'].map(teammap)
    df.sort_values(by='date', inplace=True)
    df['series_key'] = df['team'] + '_' + df['opp_team'] + '_' + df['year'].astype(str)
    series_index = df[['series_key', 'team', 'opp_team', 'TEAM_ID', 'opp_id', 'year']].drop_duplicates()
    series_index_path = 'series_index.csv'
    if os.path.exists(series_index_path):
        existing_series_index = pd.read_csv(series_index_path)
        combined_series_index = pd.concat([existing_series_index, series_index], ignore_index=True)
        combined_series_index.drop_duplicates(subset=['series_key', 'team', 'TEAM_ID', 'opp_team', 'opp_id', 'year'], keep='last', inplace=True)
        combined_series_index.to_csv(series_index_path, index=False)
    else:
        series_index.to_csv(series_index_path, index=False)
    df.to_csv('playoff_data.csv', index=False)
    series_dir = '../series/data'
    os.makedirs(series_dir, exist_ok=True)
    for key, group in df.groupby('series_key'):
        safe_key = key.replace('/', '-').replace('\\', '-')
        group.to_csv(os.path.join(series_dir, f'{safe_key}.csv'), index=False)
    return df

def check_directory_structure():
    base_path = '../team'
    if not os.path.exists(base_path):
        return
    for year_dir in os.listdir(base_path):
        year_path = os.path.join(base_path, year_dir)
        if os.path.isdir(year_path):
            _ = [f for f in os.listdir(year_path) if f.endswith('.csv')]

def run_pipeline(start_year=2024, end_year=2025):
    check_directory_structure()
    dates = get_dates(start_year, end_year)
    if dates.empty:
        return None
    raw_df = fetch_game_csvs(dates)
    if raw_df.empty:
        return None
    return process_and_save_series_data(raw_df, dates)

if __name__ == "__main__":
    for year in range(2026,2027):
        run_pipeline(year,year+1)


# In[ ]:





# In[ ]:





# In[ ]:




