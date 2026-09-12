import pandas as pd

years = [i for i in range(2014,2027)]
frames = []
for year in years:
    df=pd.read_csv(f"nba_analysis_{year}.csv")
    frames.append(df)

master = pd.concat(frames)
master.to_csv('all_cluster_seasons.csv',index=False)