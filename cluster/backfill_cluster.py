# regenerate_all.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import euclidean_distances
from kneed import KneeLocator

# paste the full save_cluster_data function here
def save_cluster_data(year):
    df = pd.read_csv(f'cluster_{year}.csv')
 
    season = str(year-1)+'-'+str(year)[-2:]
    print(season)
    testdf = df[(df.MPG > 10) & (df.GP > 10) & (df.SEASON == season)].reset_index(drop=True)
 
    # ── STEP 1: Standardize ──────────────────────────────────────────────────
    features = [x for x in df.columns if x not in ('PLAYER_NAME', 'POSITION', 'SEASON')]
    x = testdf.loc[:, features].apply(pd.to_numeric, errors='coerce').values
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = StandardScaler().fit_transform(x)
 
    # ── STEP 2: 2D PCA for visualization ────────────────────────────────────
    # Single PCA pass — coordinates, clustering, AND similarity all use this
    # same space so visual proximity matches the neighbor panel.
    pca = PCA(n_components=2)
    principalComponents = pca.fit_transform(x)
 
    testdf['PCA_1'] = principalComponents[:, 0]
    testdf['PCA_2'] = principalComponents[:, 1]
 
    # ── STEP 3: KMeans clustering on 2D coords ───────────────────────────────
    inertia = []
    silhouette_scores = []
    k_range = range(2, 15)
 
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(principalComponents)
        inertia.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(principalComponents, kmeans.labels_))
 
    knee_locator = KneeLocator(k_range, inertia, curve="convex", direction="decreasing")
    optimal_clusters_elbow = knee_locator.knee
    optimal_clusters_silhouette = k_range[np.argmax(silhouette_scores)]
 
    print(f"Optimal clusters (Elbow): {optimal_clusters_elbow}")
    print(f"Optimal clusters (Silhouette): {optimal_clusters_silhouette}")
 
    user_clusters = 8
    print(f"Using {user_clusters} clusters for final clustering.")
 
    kmeans_final = KMeans(n_clusters=user_clusters, random_state=42)
    kmeans_final.fit(principalComponents)
    testdf['Cluster'] = kmeans_final.labels_
 
    # ── STEP 4: Similar players — distances in 2D PCA space ─────────────────
    # Now computed AFTER the 2D projection so neighbors match what you see on
    # the scatter. Previously this ran in high-dim space (99%-variance PCA)
    # which caused the mismatch between visual proximity and the neighbor panel.
    #
    # One consequence: neighbors are now searched league-wide (not within the
    # Ward cluster), since the KMeans cluster boundaries in 2D are the relevant
    # grouping. A player near a cluster boundary will correctly surface
    # cross-cluster neighbors that are visually close.
 
    player_cluster_mapping = pd.DataFrame({
        'PLAYER_NAME': testdf['PLAYER_NAME'].values,
        'PLAYER_ID':   testdf['PLAYER_ID'].values,
        'CLUSTER':     testdf['Cluster'].values,
    })
 
    similar_players_df = pd.DataFrame()
 
    for idx, player in enumerate(testdf['PLAYER_NAME']):
        player_row     = player_cluster_mapping[player_cluster_mapping['PLAYER_NAME'] == player]
        base_player_id = player_row['PLAYER_ID'].iloc[0]
 
        # Compute euclidean distance from this player to ALL other players
        # in 2D PCA space — same coordinates plotted on the scatter.
        all_distances = euclidean_distances(
            principalComponents, [principalComponents[idx]]
        ).flatten()
 
        # Exclude the player themselves (distance = 0) and take 5 closest
        sorted_indices   = np.argsort(all_distances)
        closest_indices  = [i for i in sorted_indices if i != idx][:5]
        closest_players  = player_cluster_mapping.iloc[closest_indices]
        closest_distances = all_distances[closest_indices]
 
        new_row = pd.DataFrame([{
            'PLAYER_NAME':        player,
            'PLAYER_ID':          base_player_id,
            'SIMILAR_1_NAME':     closest_players['PLAYER_NAME'].iloc[0] if len(closest_players) > 0 else '',
            'SIMILAR_1_ID':       closest_players['PLAYER_ID'].iloc[0]   if len(closest_players) > 0 else '',
            'SIMILAR_1_DISTANCE': closest_distances[0]                   if len(closest_distances) > 0 else '',
            'SIMILAR_2_NAME':     closest_players['PLAYER_NAME'].iloc[1] if len(closest_players) > 1 else '',
            'SIMILAR_2_ID':       closest_players['PLAYER_ID'].iloc[1]   if len(closest_players) > 1 else '',
            'SIMILAR_2_DISTANCE': closest_distances[1]                   if len(closest_distances) > 1 else '',
            'SIMILAR_3_NAME':     closest_players['PLAYER_NAME'].iloc[2] if len(closest_players) > 2 else '',
            'SIMILAR_3_ID':       closest_players['PLAYER_ID'].iloc[2]   if len(closest_players) > 2 else '',
            'SIMILAR_3_DISTANCE': closest_distances[2]                   if len(closest_distances) > 2 else '',
            'SIMILAR_4_NAME':     closest_players['PLAYER_NAME'].iloc[3] if len(closest_players) > 3 else '',
            'SIMILAR_4_ID':       closest_players['PLAYER_ID'].iloc[3]   if len(closest_players) > 3 else '',
            'SIMILAR_4_DISTANCE': closest_distances[3]                   if len(closest_distances) > 3 else '',
            'SIMILAR_5_NAME':     closest_players['PLAYER_NAME'].iloc[4] if len(closest_players) > 4 else '',
            'SIMILAR_5_ID':       closest_players['PLAYER_ID'].iloc[4]   if len(closest_players) > 4 else '',
            'SIMILAR_5_DISTANCE': closest_distances[4]                   if len(closest_distances) > 4 else '',
        }])
 
        similar_players_df = pd.concat([similar_players_df, new_row], ignore_index=True)
 
    similar_players_df.to_csv(f'{year}_similar_players.csv', index=False)
    print(f"Similar players CSV saved for {year}.")
 
    # ── STEP 5: Save main analysis file ─────────────────────────────────────
    testdf.to_csv(f'nba_analysis_{year}.csv', index=False)
    print(f"Analysis CSV saved for {year}.")
 
 
for year in range(2014, 2016):
    print(f"\n--- Processing {year} ---")
    save_cluster_data(year)