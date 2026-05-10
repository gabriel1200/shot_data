import pandas as pd

# Load the log
df = pd.read_csv('game_dates.csv')

# Count occurrences of each unique GAME_ID
game_counts = df['GAME_ID'].value_counts()

# Identify IDs that appear only once
missing_pair_ids = game_counts[game_counts == 1].index

# Extract the rows associated with those IDs
missing_games_df = df[df['GAME_ID'].isin(missing_pair_ids)]

# Save to a new file for inspection
missing_games_df.to_csv('missing_game_entries.csv', index=False)