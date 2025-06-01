#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import os




# In[2]:


def get_role_averages():
    frames = []

    zones = ['Center(C)',
     'Left Side Center(LC)',
     'Left Side(L)',
     'Right Side Center(RC)',
     'Right Side(R)',
     'Center(C)',
     'Left Side Center(LC)',
     'Left Side(L)',
     'Right Side Center(RC)',
     'Right Side(R)',
     'Center(C)',
     'Left Side(L)',
     'Right Side(R)',
     'Back Court(BC)',
     'Center(C)']

    ranges = ['16-24 ft.',
     '16-24 ft.',
     '16-24 ft.',
     '16-24 ft.',
     '16-24 ft.',
     '24+ ft.',
     '24+ ft.',
     '24+ ft.',
     '24+ ft.',
     '24+ ft.',
     '8-16 ft.',
     '8-16 ft.',
     '8-16 ft.',
     'Back Court Shot',
     'Less Than 8 ft.']
    df = pd.read_csv('https://raw.githubusercontent.com/gabriel1200/site_Data/refs/heads/master/lebron.csv')
    for year in range(2024,2026):

        year_df = df[df.year==year]


        roles = year_df['Offensive Archetype'].unique()
        for role in roles:

            role_avg=pd.DataFrame({'SHOT_ZONE':zones,'SHOT_ZONE_RANGE':ranges })
            role_avg['FGA'] = 0
            role_avg['FGM'] = 0

            role_df = year_df[year_df['Offensive Archetype']==role]

            for player_id in role_df['NBA ID'].unique():
                #print(player_id)
                if os.path.isfile(str(year)+'/'+str(int(player_id))+'.csv'):
                    playerdf = pd.read_csv(str(year)+'/'+str(int(player_id))+'.csv')
                    sum_df = playerdf.groupby(['SHOT_ZONE_RANGE','SHOT_ZONE_AREA','SHOT_MADE_FLAG']).size().unstack(fill_value=0).reset_index()

                    #sum_df.drop(columns=['SHOT_MADE_FLAG'],inplace=True)
                    if len(sum_df.columns) ==4:
                        sum_df.columns = ['SHOT_ZONE_RANGE','SHOT_ZONE_AREA','Missed','Made']
                    elif len(sum_df.columns) ==3:
                         sum_df.columns = ['SHOT_ZONE_RANGE','SHOT_ZONE_AREA','Missed']
                         sum_df['Made']=0
                    else:
                        sum_df.columns = ['SHOT_ZONE_RANGE','SHOT_ZONE_AREA']
                        sum_df['Missed']=0
                        sum_df['Made']=0

                    sum_df['FGM'] = sum_df['Made']
                    sum_df['FGA'] = sum_df['Made'] + sum_df['Missed']

                    sum_df.drop(columns=['Made','Missed'],inplace=True)
                    sum_df['role'] = role
                    sum_df['year']=year
                    frames.append(sum_df)

        print(year)
    return pd.concat(frames)

df = get_role_averages()


# In[3]:


df


# In[4]:


all_averages = df.groupby(['year','role','SHOT_ZONE_RANGE','SHOT_ZONE_AREA']).sum()[['FGM','FGA']].reset_index()
for year in df.year.unique():
    year_df= all_averages[all_averages.year==year].reset_index(drop=True)
    year_df.drop(columns='year',inplace=True)
    year_df.to_csv('roles/'+str(year)+'.csv',index = False)
    print(year_df)


# In[5]:


all_averages

