#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd

def create_playoff_series_index(file_path):
    # Step 1: Load and filter playoff games only
    df = pd.read_csv(file_path)
    df = df[df.playoffs == True]
    
    # Step 2: Create a mapping from team name to TEAM_ID
    team_id_map = df[['team', 'TEAM_ID']].drop_duplicates().set_index('team')['TEAM_ID'].to_dict()
    
    # Step 3: Map opp_team to OPP_ID using the same dictionary
    df['OPP_ID'] = df['opp_team'].map(team_id_map)
    
    # Step 4: Rename and reformat columns
    df_transformed = df.rename(columns={
        'team': 'TEAM',
        'opp_team': 'OPP',
        'season': 'year'
    })
    
    # Step 5: Reformat year to end year (e.g., 2020-21 -> 2021)
    df_transformed['year'] = df_transformed['year'].str.split('-').str[0].astype(int) + 1
    
    # Step 6: Create a Series key for team-opponent combination (sorted to avoid duplicates)
    df_transformed['series_key'] = df_transformed.apply(
        lambda row: tuple(sorted([row['TEAM_ID'], row['OPP_ID']])), axis=1
    )
    
    # Step 7: Sort by year and date for proper ordering
    df_transformed = df_transformed.sort_values(['year', 'date'])
    
    # Step 8: Determine the round for each series based on when they appear in the playoff sequence
    # Group by year to process each playoff year separately
    all_series = []
    
    for year, year_data in df_transformed.groupby('year'):
        # Get unique series in the order they appeared
        series_order = []
        seen_series = set()
        
        for _, row in year_data.iterrows():
            series = row['series_key']
            if series not in seen_series:
                series_order.append(series)
                seen_series.add(series)
        
        # Calculate round for each series based on its position in the sequence
        # Assign rounds by order of appearance:
        # First 8 series are Round 1
        # Next 4 series are Round 2 (Conference Semifinals)
        # Next 2 series are Round 3 (Conference Finals)
        # Last series is Round 4 (NBA Finals)
        series_rounds = {}
        
        for i, series in enumerate(series_order):
            if i < 8:
                series_rounds[series] = 1  # First Round
            elif i < 12:
                series_rounds[series] = 2  # Conference Semifinals
            elif i < 14:
                series_rounds[series] = 3  # Conference Finals
            else:
                series_rounds[series] = 4  # NBA Finals
        
        # Assign rounds to each game
        year_data['Round'] = year_data['series_key'].map(series_rounds)
        all_series.append(year_data)
    
    # Combine all years back together
    final_df = pd.concat(all_series)
    
    # Step 9: Create the final series index by selecting one row per series
    # Use first record of each series as representative
    series_index = final_df.drop_duplicates(subset=['year', 'series_key'])
    
    # Step 10: Select and reorder columns
    series_index = series_index[['OPP', 'OPP_ID', 'TEAM_ID', 'TEAM', 'Round', 'year']]
    
    # Step 11: Create the swapped rows
    swapped_rows = series_index.copy()
    swapped_rows = swapped_rows.rename(columns={'OPP': 'TEAM', 'OPP_ID': 'TEAM_ID', 'TEAM': 'OPP', 'TEAM_ID': 'OPP_ID'})
    
    # Step 12: Append swapped rows to the original DataFrame
    final_series_index = pd.concat([series_index, swapped_rows])
    
    return final_series_index

if __name__ == "__main__":
    # Replace with your file path
    file_path = 'game_dates.csv'
    playoff_series = create_playoff_series_index(file_path)
    
    # Display the result
    playoff_series.sort_values(by=['year','Round'],inplace=True)
    print(playoff_series.tail(20))
    
    # Optionally save to a CSV file
    #playoff_series.to_csv('playoff_series_index.csv', index=False)

    playoff_series.to_csv('opponentmatch.csv', index=False)
    

