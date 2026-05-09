import os
import time
import pandas as pd
import requests

def pull_rotation(url, max_retries=3):
    """Fetches the rotation data with automatic retries for timeouts/blocks."""
    headers = {
        "Host": "stats.nba.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://stats.nba.com/"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"  Attempt {attempt + 1} failed (Status {response.status_code}). Sleeping and retrying...")
                time.sleep(3)
                continue
                
            json_resp = response.json()
            
            frames = []
            if "resultSets" in json_resp:
                for i in range(len(json_resp["resultSets"])):
                    data = json_resp["resultSets"][i]["rowSet"]
                    columns = json_resp["resultSets"][i]["headers"]
                    df = pd.DataFrame.from_records(data, columns=columns)
                    frames.append(df)
                
            # Filter out empty frames before concatenating to avoid FutureWarnings
            valid_frames = [f for f in frames if not f.empty]
            gameframe = pd.concat(valid_frames) if valid_frames else pd.DataFrame()
            
            time.sleep(1.5)  # Standard delay on success
            return gameframe
            
        except requests.exceptions.ReadTimeout:
            print(f"  Attempt {attempt + 1} timed out. Retrying...")
            time.sleep(3)
        except Exception as e:
            print(f"  Attempt {attempt + 1} encountered an error: {e}. Retrying...")
            time.sleep(3)

    print(f"  Gave up on {url} after {max_retries} attempts.")
    return pd.DataFrame()

def diagnose_and_repair_with_master(start_year=1996, end_year=2026, ps=False):
    """
    Uses a local master CSV of game dates to figure out what rotation files are missing 
    games, scrapes only the missing data, and appends it.
    """
    try:
        master_dates = pd.read_csv('game_dates.csv')
    except FileNotFoundError:
        print("Error: 'game_dates.csv' not found. Please ensure it is in the same directory.")
        return
    
    master_dates['GAME_ID'] = master_dates['GAME_ID'].astype(str).str.zfill(10)
    master_dates = master_dates[master_dates['playoffs'] == ps]
    
    carry = "ps" if ps else ""
    
    for year in range(start_year, end_year + 1):
        season_str = f"{year}-{str(year + 1)[-2:]}"
        print(f"\n{'='*40}")
        print(f"--- Diagnosing Season: {season_str} ---")
        print(f"{'='*40}")
        
        season_schedule = master_dates[master_dates['season'] == season_str]
        if season_schedule.empty:
            print(f"No games found in master schedule for {season_str}. Skipping...")
            continue
            
        # Get unique combinations of TEAM_ID and the team abbreviation
        team_mapping = season_schedule[['TEAM_ID', 'team']].drop_duplicates().sort_values('team')
        
        # Print out the found teams for this season
        found_teams_str = ", ".join([f"{row['team']} ({row['TEAM_ID']})" for _, row in team_mapping.iterrows()])
        print(f"Found {len(team_mapping)} teams in schedule:\n{found_teams_str}\n")
        
        path = f"rotations/{year + 1}{carry}"
        os.makedirs(path, exist_ok=True)
        
        for _, row in team_mapping.iterrows():
            team_id = row['TEAM_ID']
            team_abbr = row['team']
            
            team_games = season_schedule[season_schedule['TEAM_ID'] == team_id]['GAME_ID'].unique().tolist()
            
            file_path = f"{path}/{team_id}.csv"
            stored_games = []
            existing_df = pd.DataFrame()
            
            if os.path.exists(file_path):
                try:
                    existing_df = pd.read_csv(file_path)
                    if 'GAME_ID' in existing_df.columns:
                        existing_df['GAME_ID'] = existing_df['GAME_ID'].astype(str).str.zfill(10)
                        stored_games = existing_df['GAME_ID'].unique().tolist()
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
            
            missing_games = list(set(team_games) - set(stored_games))
            
            if not missing_games:
                continue
                
            print(f"[{team_abbr}] Team {team_id} missing {len(missing_games)} game(s). Fetching...")
            
            new_frames = [existing_df] if not existing_df.empty else []
            games_added = 0
            
            for game_id in missing_games:
                url = f"https://stats.nba.com/stats/gamerotation?GameID={game_id}&LeagueID=00"
                fetched_df = pull_rotation(url)
                
                if not fetched_df.empty:
                    # Filter the rotation down to just the current team into a NEW variable
                    team_df = fetched_df[fetched_df['TEAM_ID'] == team_id].copy()
                    
                    if not team_df.empty:
                        team_df['GAME_ID'] = team_df['GAME_ID'].astype(str).str.zfill(10)
                        new_frames.append(team_df)
                        games_added += 1
                    else:
                        # Find out exactly which Team IDs WERE returned by the API
                        found_ids = fetched_df['TEAM_ID'].unique().tolist()
                        print(f"  [!] Game {game_id} fetched, but no rotation data exists for {team_abbr}.")
                        print(f"      -> Data WAS returned for Team IDs: {found_ids}")
                else:
                    print(f"  [!] NBA API returned completely empty data or failed for Game {game_id}.")
                    
            if games_added > 0:
                repaired_df = pd.concat(new_frames, ignore_index=True)
                repaired_df = repaired_df.drop_duplicates()
                
                repaired_df.to_csv(file_path, index=False)
                print(f"Repaired and saved {file_path} (Added {games_added} games for {team_abbr})")
            else:
                print(f"Skipped saving {file_path} (No valid new data found for {team_abbr})")

if __name__ == "__main__":
    # Example: Run diagnosis for the 2009-10 and 2010-11 seasons
    diagnose_and_repair_with_master(start_year=2009, end_year=2010, ps=False)