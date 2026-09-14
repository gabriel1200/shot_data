"""Confirm the NOK fix resolved all 82 previously-known-bad games, and that
nothing outside 2005-06/2006-07 shifted unexpectedly. Compares
game_dates_fixed.csv against the current game_dates.csv.

Run from ~/basketball/shot_data/:
    python verify_game_dates_fix.py

Read-only -- does not modify either file.
"""
import pandas as pd

OLD = pd.read_csv('game_dates.csv', dtype={'GAME_ID': str})
NEW = pd.read_csv('game_dates_fixed.csv', dtype={'GAME_ID': str})

NOK_SEASONS = {'2005-06', '2006-07'}
NOP_TEAM_ID = 1610612740

old_nop = OLD[(OLD.TEAM_ID == NOP_TEAM_ID) & (OLD.season.isin(NOK_SEASONS))].set_index('GAME_ID')
new_nop = NEW[(NEW.TEAM_ID == NOP_TEAM_ID) & (NEW.season.isin(NOK_SEASONS))].set_index('GAME_ID')

changed = old_nop.index[old_nop['opp_team'] != new_nop.reindex(old_nop.index)['opp_team']]

still_nok = new_nop[new_nop['opp_team'] == 'NOK']

print(f'NOP games in 2005-06/2006-07: {len(old_nop)}')
print(f'Games where opp_team changed: {len(changed)}')
print(f'Games STILL showing opp_team=NOK after the fix: {len(still_nok)}')
if len(still_nok):
    print('  These did NOT resolve -- needs investigation:')
    print(still_nok[['season', 'HTM', 'VTM', 'opp_team']].to_string())

# Confirm nothing outside the NOK seasons/team shifted unexpectedly.
merged = OLD.merge(NEW, on=['GAME_ID', 'TEAM_ID'], suffixes=('_old', '_new'))
outside = merged[
    ~((merged.TEAM_ID == NOP_TEAM_ID) & (merged.season_old.isin(NOK_SEASONS)))
    & (merged.opp_team_old != merged.opp_team_new)
]
print()
print(f'Rows OUTSIDE the NOK fix scope where opp_team changed unexpectedly: {len(outside)}')
if len(outside):
    print('  This means the fix affected something it should not have:')
    print(outside[['GAME_ID', 'TEAM_ID', 'season_old', 'opp_team_old', 'opp_team_new']].to_string())
else:
    print('  Confirmed: fix is scoped exactly as intended, nothing else moved.')