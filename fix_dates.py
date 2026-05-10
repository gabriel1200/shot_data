import pandas as pd

df = pd.read_csv('game_dates.csv')

# Create a mapping of team abbreviations to TEAM_IDs
team_map = df[['team', 'TEAM_ID']].drop_duplicates().set_index('team')['TEAM_ID'].to_dict()

# Identify GAME_IDs with only one entry
game_counts = df['GAME_ID'].value_counts()
missing_pair_ids = game_counts[game_counts == 1].index
single_rows = df[df['GAME_ID'].isin(missing_pair_ids)].copy()

# Create the missing partner rows
partner_rows = single_rows.copy()
partner_rows['team'] = single_rows['opp_team']
partner_rows['opp_team'] = single_rows['team']
partner_rows['TEAM_ID'] = partner_rows['team'].map(team_map)

# Merge and save
corrected_df = pd.concat([df, partner_rows], ignore_index=True)
corrected_df.to_csv('game_dates.csv', index=False)