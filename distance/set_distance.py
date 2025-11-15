#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import pandas as pd

# Config
base_path = '../team/'
start_year = 2026
end_year = start_year
include_regular = True
include_playoffs = False

frames = []

# Loop through each year
for year in range(start_year, end_year + 1):
    for mode, label in [(include_regular, ''), (include_playoffs, 'ps')]:
        if not mode:
            continue

        # Construct path based on whether it's regular season or playoffs
        year_str = f"{year}{label}"
        year_path = os.path.join(base_path, year_str)
        print(f"Checking directory: {year_path}")

        if os.path.isdir(year_path):
            print(f"\nFiles in directory {year_path}:")

            for filename in os.listdir(year_path):
                file_path = os.path.join(year_path, filename)

                if 'vs' not in filename and 'avg' not in filename and filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    if len(df) > 0:
                        df['year'] = year
                        df['mode'] = 'playoffs' if label == 'ps' else 'regular'
                        frames.append(df)
            print(f"Loaded data for: {year_str}")
        else:
            print(f"Directory {year_path} does not exist.")

# Combine all data
master = pd.concat(frames)

# Value counts (optional debugging info)
master['SHOT_ATTEMPTED_FLAG'].value_counts()
master['SHOT_MADE_FLAG'].value_counts()

# Group and summarize
shots = master.groupby(['year', 'mode', 'SHOT_ZONE_RANGE', 'SHOT_DISTANCE']).sum(numeric_only=True)[['SHOT_ATTEMPTED_FLAG', 'SHOT_MADE_FLAG']].reset_index()
shots.rename(columns={'SHOT_ATTEMPTED_FLAG': 'FGA', 'SHOT_MADE_FLAG': 'FGM'}, inplace=True)

# Output separate files for regular and playoffs
for (year, mode), df in shots.groupby(['year', 'mode']):
    mode_suffix = 'ps' if mode == 'playoffs' else ''
    df.reset_index(drop=True).to_csv(f"{year}{mode_suffix}.csv", index=False)

# Show unique shot zone ranges
print(master['SHOT_ZONE_RANGE'].unique())


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




