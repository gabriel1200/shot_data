#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import pandas as pd
# Define the base path and the range of years
base_path = 'team/'
start_year = 2025
end_year = 2025
frames = []
# Loop through each year and list files in the corresponding directory
for year in range(start_year, end_year + 1):
    # Construct the path for the current year
    year_path = os.path.join(base_path, str(year))
    
    # Check if the directory exists
    if os.path.isdir(year_path):
        print(f"\nFiles in directory {year_path}:")
        
        # List all files in the directory
        for filename in os.listdir(year_path):
            file_path = os.path.join(year_path, filename)
            # Check if it is a file before printing
            if 'vs' not in filename and 'avg' not in filename:
                if '.csv' in filename:
                    
                    
                    df=pd.read_csv(file_path)
                    if len(df)>0:
                        #print(filename)
                        df['year']=year
                        frames.append(df)
        print(year)

    else:
        print(f"\nDirectory {year_path} does not exist.")

master=pd.concat(frames)
master


# In[2]:


master['SHOT_ATTEMPTED_FLAG'].value_counts()
master['SHOT_MADE_FLAG'].value_counts()


# In[3]:


shots = master.groupby(['year','SHOT_ZONE_RANGE','SHOT_DISTANCE']).sum(numeric_only=True)[['SHOT_ATTEMPTED_FLAG','SHOT_MADE_FLAG']].reset_index()

shots.rename(columns={'SHOT_ATTEMPTED_FLAG':'FGA','SHOT_MADE_FLAG':'FGM'},inplace=True)
shots


# In[4]:


for year in range(start_year,2026):
    shot_distance=shots[shots.year==year].reset_index()
    shot_distance.drop(columns='year',inplace=True)
    shot_distance.to_csv(str(year)+'.csv',index=False)


# In[5]:


master['SHOT_ZONE_RANGE'].unique()


# In[ ]:





# In[ ]:




