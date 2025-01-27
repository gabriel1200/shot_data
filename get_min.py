#!/usr/bin/env python
# coding: utf-8

# In[1]:


from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players,teams
from nba_api.stats.endpoints import playbyplayv2
from nba_api.stats.endpoints import ShotChartDetail # For player shot location and frequency
from nba_api.stats.endpoints import commonplayerinfo # For Common Player Information
import requests
import os
import numpy as np
#from nba_api.stats.endpoints import playergamelogs
import pandas as pd
import time
def pull_rotation(url):


    headers = {
                                    "Host": "stats.nba.com",
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
                                    "Accept": "application/json, text/plain, */*",
                                    "Accept-Language": "en-US,en;q=0.5",
                                    "Accept-Encoding": "gzip, deflate, br",

                                    "Connection": "keep-alive",
                                    "Referer": "https://stats.nba.com/"
                                }
    json = requests.get(url,headers = headers).json()

    frames = []
    for i in range(len(json["resultSets"])):
        data = json["resultSets"][i]["rowSet"]
        #print(data)
        columns = json["resultSets"][i]["headers"]
    #print(columns)

        df = pd.DataFrame.from_records(data, columns=columns)
        frames.append(df)
    gameframe = pd.concat(frames)
    time.sleep(1.5)
    
    return gameframe
def team_shotmap(team,season,stype ='Regular Season',league_id = '00',save_avg=False):
    carry = ''
    if stype!='Regular Season':
        carry ='ps'
   
    #print(team_id)
    nba_teams = teams.get_teams()
    team_list= {}
    full_name = {}
    for org in nba_teams:
        team_list[org['abbreviation']] = org['id']
        full_name[org['abbreviation']] = org['full_name']

    
    
    season_nullable= season
    team_id = team_list[team]
   
    shot_chart = ShotChartDetail(
                      player_id ='0',
                      
                      team_id=team_id,
                      season_nullable= season,
                      season_type_all_star=stype, 
                      context_measure_simple= 'FGA',
                                    league_id = league_id).get_data_frames()
        
    team_shots = shot_chart[0]
    if save_avg== True:
        
        avg = shot_chart[1]
        year = int(season.split('-')[0])+1
        avg.to_csv('team/'+str(year)+carry+'/avg.csv',index=False)
    return team_shots
def pull_rotation(url):


    headers = {
                                    "Host": "stats.nba.com",
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
                                    "Accept": "application/json, text/plain, */*",
                                    "Accept-Language": "en-US,en;q=0.5",
                                    "Accept-Encoding": "gzip, deflate, br",

                                    "Connection": "keep-alive",
                                    "Referer": "https://stats.nba.com/"
                                }
    json = requests.get(url,headers = headers).json()

    frames = []
    for i in range(len(json["resultSets"])):
        data = json["resultSets"][i]["rowSet"]
        #print(data)
        columns = json["resultSets"][i]["headers"]
    #print(columns)

        df = pd.DataFrame.from_records(data, columns=columns)
        frames.append(df)
    gameframe = pd.concat(frames)
    return gameframe
def get_shotrotations(season,ps = False):
    stype = "Regular Season"
    carry = ""
    if ps == True:
        stype = "Playoffs"
        carry = "ps"
    nba_teams = teams.get_teams()
    
    team_list= {}
    full_name = {}
    for org in nba_teams:
        team_list[org['abbreviation']] = org['id']
        full_name[org['abbreviation']] = org['full_name']
    team_abr = full_name.keys()
    
    data = {}
    save_avg = True
    for team in team_abr:
        team = team.upper()
        
        shotmap = team_shotmap(team,season,stype=stype,save_avg=save_avg)
        save_avg=False
        games = list(set(shotmap.GAME_ID.tolist()))

        frames = []
        year =int(season.split('-')[0])+1
        path = 'rotations/'+str(year)+carry
        team_id=team_list[team]
        
        if os.path.exists(path+'/'+str(team_id)+'.csv'):
            
            temp = pd.read_csv(path+'/'+str(team_id)+'.csv')
            stored = set(temp.GAME_ID.tolist())
            frames.append(temp)
            new_games = []
            for game in games:
                if str(game)[0:2] !='00':
                    new_game = '00'+str(game)
                    new_games.append(new_game)
                else:
                    new_games.append(game)
                    
            games = new_games
            
            new_stored = []
            for game in stored:
                if str(game)[0:2] !='00':
                    new_game = '00'+str(game)
                    new_stored.append(new_game)
                else:
                    new_stored.append(game)
            stored=new_stored
  
            games = list(set(games) -set(stored))
            #print(games)
        for game in games:
            url='https://stats.nba.com/stats/gamerotation?GameID='+game+'&LeagueID=00'
            df = pull_rotation(url)

            frames.append(df)
        if len(shotmap)!=0:
            all_games = pd.concat(frames)
            all_games = all_games.drop_duplicates()
            all_games['GAME_ID']=all_games['GAME_ID'].astype(str)
            all_games['GAME_ID'] = np.where(all_games['GAME_ID'].str[0:2]=='00', all_games['GAME_ID'], '00'+all_games['GAME_ID'])
    
            all_games['GAME_ID'] = np.where(all_games['GAME_ID'].str[0:2]=='00', all_games['GAME_ID'], '00'+all_games['GAME_ID'])
    
    
            shotmap['GAME_ID'] = np.where(shotmap['GAME_ID'].str[0:2]=='00', shotmap['GAME_ID'], '00'+shotmap['GAME_ID'])
    
            
            to_merge = all_games[['GAME_ID','TEAM_ID','PERSON_ID','IN_TIME_REAL','OUT_TIME_REAL']].reset_index(drop=True)
            to_merge['GAME_ID']=to_merge['GAME_ID'].astype(str)
    
    
            #to_merge.rename(columns={'PERSON_ID':'PLAYER_ID'},inplace=True)
            to_merge = to_merge[to_merge.TEAM_ID==team_id]        
    
            shotmap['SHOT_ID'] = shotmap['GAME_ID'].astype(str)+shotmap['GAME_EVENT_ID'].astype(str)
            shotmap['PERIOD'].value_counts()
            shotmap['time'] = (shotmap['PERIOD']-1)*720+(12-(shotmap['MINUTES_REMAINING']+1))*60+(60-shotmap['SECONDS_REMAINING'])
            shotmap['extra'] = (shotmap['PERIOD']//5) *(shotmap['PERIOD']-4)
            shotmap['time'] = shotmap['time']-(shotmap['extra']*420)
            #shotmap[shotmap.extra>0]
            shotmap['time']*=10
            shot_times = shotmap.merge(to_merge,on=['GAME_ID','TEAM_ID'],how='left')
            shot_times = shot_times[shot_times.time>=shot_times.IN_TIME_REAL]
            shot_times = shot_times[shot_times.time<shot_times.OUT_TIME_REAL]
            shot_times.sort_values(by='GAME_DATE')
            shot_times['SHOT_ID'] = shot_times['SHOT_ID'].astype(str)
            shot_times['PERSON_ID'] =shot_times['PERSON_ID'].astype(str)
            shot_on = shot_times.groupby('SHOT_ID')['PERSON_ID'].apply('|'.join).reset_index()
            shot_on.columns=['SHOT_ID','PLAYERS_ON']
            #print(shot_on)
            print(len(shot_on))
            value_dict={}
            id_count = []
            for col in shot_on.PLAYERS_ON.tolist():
                count = len(col.split('|'))
                if count not in value_dict:
                    value_dict[count] = 1
                else:
                    value_dict[count]+=1
                id_count.append(count)
            shot_on['id_count']=id_count
            
            print(value_dict)
            if 'PLAYERS_ON' in shotmap.columns:
                shotmap = shotmap.drop(columns='PLAYERS_ON')
            final_shotmap = shotmap.merge(shot_on,how='left').reset_index(drop=True)
            #print(final_shotmap['PLAYERS_ON'])
            final_shotmap['PLAYERS_ON'] = np.where(final_shotmap['id_count']==5, final_shotmap['PLAYERS_ON'],final_shotmap['PLAYER_ID'].astype(str))
            #print(final_shotmap['PLAYERS_ON'])
            final_shotmap.PLAYERS_ON = final_shotmap.PLAYERS_ON.astype(str)
            value_dict={}
            for col in final_shotmap.PLAYERS_ON.tolist():
                count = len(col.split('|'))
                if count not in value_dict:
                    value_dict[count] = 1
                else:
                    value_dict[count]+=1
            print(value_dict)
            print(len(shotmap))
            year =int(season.split('-')[0])+1
            final_shotmap = final_shotmap.drop(columns='id_count')
            final_shotmap.to_csv('team/'+str(year)+carry+'/'+str(team_id)+'.csv',index = False)
            all_games = all_games[all_games.TEAM_ID==team_id]
            path = 'rotations/'+str(year)+carry
            isExist = os.path.exists(path)
            if not isExist:
    
       # Create a new directory because it does not exist
                os.makedirs(path)
                print('Making Folder ' +path)
            all_games.to_csv(path+'/'+str(team_id)+'.csv',index=False)
            
            data[team]=final_shotmap
        #print(team)
        #print(len(shotmap))
        #print(len(final_shotmap))
        #print(len(shot_on))
    return data
#data = get_shotrotations('2023-24',ps=False)
data = get_shotrotations('2024-25',ps=False)


# In[2]:


#ps = 'ps'
ps =''
master= []
year = 2025
for team in teams.get_teams():
    team_id = team['id']
    file_path = f'team/{year}{ps}/{team_id}.csv'
    
    # Check if the file exists
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        master.append(df)
    else:
        print(f"File not found: {file_path}")
all_shots = pd.concat(master)


# In[3]:


for team in teams.get_teams():
    
    team_id=team['id']
    team_games = all_shots[all_shots.TEAM_ID==team['id']].GAME_ID.unique()
    team_games = list(team_games)
    opp_shots = all_shots[(all_shots.TEAM_ID!=team['id']) &(all_shots.GAME_ID.isin(team_games))].reset_index(drop=True)

    opp_shots['PLAYER_ID']='0'
    opp_shots['PLAYER_NAME']='Opponent'
    opp_shots['TEAM_ID']=team_id
    opp_shots.drop(columns=['PLAYERS_ON'],inplace=True)
    shotmap = opp_shots
                                        
    shotmap['GAME_ID'] = shotmap['GAME_ID'].astype(str)
    path = 'rotations/'+str(year)+ps

    if os.path.exists(path+'/'+str(team_id)+'.csv'):
        print(team)
        all_games = pd.read_csv(path+'/'+str(team_id)+'.csv')
        all_games = all_games.drop_duplicates()
        all_games = all_games[all_games.TEAM_ID==team_id]
    
        #print(all_games)
        
        all_games['GAME_ID']=all_games['GAME_ID'].astype(str)
        all_games['GAME_ID'] = np.where(all_games['GAME_ID'].str[0:2]=='00', all_games['GAME_ID'], '00'+all_games['GAME_ID'])
    
     
        shotmap['GAME_ID'] = np.where(shotmap['GAME_ID'].str[0:2]=='00', shotmap['GAME_ID'], '00'+shotmap['GAME_ID'])
    
        #print(len(shotmap))
        to_merge = all_games[['GAME_ID','TEAM_ID','PERSON_ID','IN_TIME_REAL','OUT_TIME_REAL']].reset_index(drop=True)
        to_merge['GAME_ID']=to_merge['GAME_ID'].astype(str)
    
    
        #to_merge.rename(columns={'PERSON_ID':'PLAYER_ID'},inplace=True)
        to_merge = to_merge[to_merge.TEAM_ID==team_id]        
        
        shot_times = shotmap.merge(to_merge,on=['GAME_ID','TEAM_ID'])
        #print(len(shot_times))
        shot_times = shot_times[shot_times.time>=shot_times.IN_TIME_REAL]
        shot_times = shot_times[shot_times.time<shot_times.OUT_TIME_REAL]
        #print(len(shot_times))
        shot_times.sort_values(by='GAME_DATE')
        shot_times['SHOT_ID'] = shot_times['SHOT_ID'].astype(str)
        shot_times['PERSON_ID'] =shot_times['PERSON_ID'].astype(str)
        shot_on = shot_times.groupby('SHOT_ID')['PERSON_ID'].apply('|'.join).reset_index()
        shot_on['SHOT_ID'] = shot_on['SHOT_ID'].astype(str)
        shotmap['SHOT_ID'] = shotmap['SHOT_ID'].astype(str)
        shot_on.columns=['SHOT_ID','PLAYERS_ON']
        #print(len(shot_on))
        value_dict = {}
        id_count=[]
        for col in shot_on.PLAYERS_ON.tolist():
            count = len(col.split('|'))
            if count not in value_dict:
                value_dict[count] = 1
            else:
                value_dict[count]+=1
            id_count.append(count)
        print(value_dict)
        shot_on['id_count'] = id_count
        final_shotmap = shotmap.merge(shot_on,how='left')
        final_shotmap['PLAYERS_ON'] = np.where(final_shotmap['id_count']==5, final_shotmap['PLAYERS_ON'],final_shotmap['PLAYER_ID'].astype(str))
        value_dict = {}
        id_count=[]
        for col in final_shotmap.PLAYERS_ON.tolist():
            count = len(col.split('|'))
            if count not in value_dict:
                value_dict[count] = 1
            else:
                value_dict[count]+=1
              
            id_count.append(count)
        print(value_dict)
        final_shotmap = final_shotmap.drop(columns='id_count')
        final_shotmap.to_csv('team/'+str(year)+ps+'/'+str(team_id)+'vs.csv',index = False)
        print(final_shotmap['TEAM_NAME'].unique())
        #print(final_shotmap.head())


# In[4]:


df.columns


# In[5]:


players = all_shots.PLAYER_ID.unique().tolist()
for player in players:
    df = all_shots[all_shots.PLAYER_ID==player]
    columns = ['GRID_TYPE', 'GAME_ID', 'GAME_EVENT_ID', 'PLAYER_ID', 'PLAYER_NAME',
       'TEAM_ID', 'TEAM_NAME', 'PERIOD', 'MINUTES_REMAINING',
       'SECONDS_REMAINING', 'EVENT_TYPE', 'ACTION_TYPE', 'SHOT_TYPE',
       'SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE', 'SHOT_DISTANCE',
       'LOC_X', 'LOC_Y', 'SHOT_ATTEMPTED_FLAG', 'SHOT_MADE_FLAG', 'GAME_DATE',
       'HTM', 'VTM']
    df=df[columns]
    df.to_csv('2025/'+str(player)+'.csv',index=False)


# In[6]:


def get_rotations(season,ps=False):
    nba_teams = teams.get_teams()
    team_list= {}
    full_name = {}
    for org in nba_teams:
        team_list[org['abbreviation']] = org['id']
        full_name[org['abbreviation']] = org['full_name']
    team_abr = full_name.keys()
    
    data = []
    save_avg = True
    stored=[]
    missed_games = []
    carry=''
    if ps==True:
        carry='ps'
    for team in team_abr:
        team = team.upper()
        team_id=team_list[team]
        year =int(season.split('-')[0])+1
        
        shotmap_url='https://raw.githubusercontent.com/gabriel1200/shot_data/master/team/'+str(year)+carry+'/'+str(team_id)+'.csv'
        
        response = requests.get(shotmap_url)
        if response.status_code != 404:
            print(shotmap_url)
            shotmap = pd.read_csv(shotmap_url)
            save_avg=False
            games = list(set(shotmap.GAME_ID.tolist()))

            frames = []

            path = 'rotations/'+str(year)
            team_id=team_list[team]


            new_games = []
            for game in games:
                game = str(game)
                if game[0:2]!='00':
                    game = '00'+game
                    new_games.append(game)
                else:
                    new_games.append(games)
            games = new_games



            games = list(set(games) -set(stored))
            print(len(games))

            for game in games:
                game = str(game)
                if game[0:2]!='00':
                    game = '00'+game

                url='https://stats.nba.com/stats/gamerotation?GameID='+game+'&LeagueID=00'
                try:
                    df = pull_rotation(url)

                    frames.append(df)
                except ValueError:
                    print(game)
                    missed_games.append(game)
            
            if len(frames)!=0:
                all_games = pd.concat(frames)

                games =all_games['GAME_ID'].unique().tolist()
                stored =stored+games


                data.append(all_games)

        print(team)
            #print(len(shotmap))
            #print(len(final_shotmap))
            #print(len(shot_on))

    print(missed_games)
    return pd.concat(data)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[7]:


'''
seasons = [str(year)+'-'+str(year+1)[-2:] for year in range (1997,1999)]

for season in seasons:
    year = int(season.split('-')[0])+1
    print(season)
    data = get_rotations(season)
   
    data.to_csv('rotations/'+str(year)+'.csv',index=False)
    
seasons = [str(year)+'-'+str(year+1)[-2:] for year in range (1996,2001)]

for season in seasons:
    year = int(season.split('-')[0])+1
    print(season)
    data = get_rotations(season,ps=True)
   
    data.to_csv('rotations/'+str(year)+'ps.csv',index=False)

for year in range(1997,2001):
        path = 'rotations/'+str(year)
        
        isExist = os.path.exists(path)
        if not isExist:

   # Create a new directory because it does not exist
            os.makedirs(path)
            print('Making Folder ' +path)
        df =pd.read_csv(path+'.csv')
        teams = df.TEAM_ID.unique().tolist()
        
        for team in teams:
            teamdf=df[df.TEAM_ID==team]
            
            teamdf.to_csv(path+'/'+str(team)+'.csv',index=False)
        print(year)

for year in range(1997,2001):
        path = 'rotations/'+str(year)+'ps'
        
        isExist = os.path.exists(path)
        if not isExist:

   # Create a new directory because it does not exist
            os.makedirs(path)
            print('Making Folder ' +path)
        df =pd.read_csv(path+'.csv')
        teams = df.TEAM_ID.unique().tolist()
        
        for team in teams:
            teamdf=df[df.TEAM_ID==team]
            
            teamdf.to_csv(path+'/'+str(team)+'.csv',index=False)
'''


# In[8]:


start_year=1997
end_year=2026

def get_dates(start_year,end_year):
    dates=[]
    for year in range(start_year,end_year):
    
        for team in teams.get_teams():
            team_id=team['id']
            path = 'team/'+str(year)+'ps/'+str(team_id)+'.csv'
            if os.path.exists(path):
                df=pd.read_csv(path)
    
                df=df[['GAME_ID','TEAM_ID','HTM','VTM','GAME_DATE']]
                df.rename(columns={'GAME_DATE':'date'},inplace=True)
                df.drop_duplicates(inplace=True)
                df['season']=str(year-1)+'-'+str(year)[-2:]
                df['playoffs']=True
                dates.append(df)
        for team in teams.get_teams():
            team_id=team['id']
            path = 'team/'+str(year)+'/'+str(team_id)+'.csv'
            if os.path.exists(path):
                df=pd.read_csv(path)
    
                df=df[['GAME_ID','TEAM_ID','HTM','VTM','GAME_DATE']]
                df.rename(columns={'GAME_DATE':'date'},inplace=True)
                df.drop_duplicates(inplace=True)
                df['season']=str(year-1)+'-'+str(year)[-2:]
                df['playoffs']=False
                dates.append(df)
                
    return pd.concat(dates)


dates=get_dates(start_year,end_year)
dates[dates.playoffs==False]
name_map={}
for team in teams.get_teams():

    name_map[team['id']]= team['abbreviation']

dates['team']=dates['TEAM_ID'].map(name_map)
acronym_changes = {
    "CHH": "CHA",
    "NOH": "NOP",
    "NJN": "BKN",
    "SEA": "OKC",
    "WSB": "WAS",
    "VAN": "MEM",
    "SDC": "LAC",
    "KCK": "SAC",
    "FTW": "DET",
    "SFW": "GSW",
    "STL": "ATL"
}
dates['team'] = dates['team'].replace(acronym_changes)

dates['HTM'] = dates['HTM'].replace(acronym_changes)
dates['VTM'] = dates['VTM'].replace(acronym_changes)

dates['opp_team'] = dates.apply(lambda row: row['VTM'] if row['team'] == row['HTM'] else row['HTM'], axis=1)

dates.sort_values(by='date',inplace=True)
dates.to_csv('game_dates.csv',index=False)
dates.to_csv('../web_app/data/game_dates.csv',index=False)


# In[9]:


dates[dates.playoffs==False].tail(20)


# In[10]:


width = 2400
height = 2000

# Calculate aspect ratios
aspect_ratio_1 = width / height
aspect_ratio_2 = width / height

# Calculate combined aspect ratio
aspect_ratio_combined = aspect_ratio_1 + aspect_ratio_2

# Set the dimensions of the combined image
combined_width = 2 * width  # Assuming you are combining two images side by side
combined_height = int(combined_width / aspect_ratio_combined)

# Print the dimensions of the combined image
print(f"Combined Image Dimensions: {combined_width} x {combined_height}")


# In[ ]:




