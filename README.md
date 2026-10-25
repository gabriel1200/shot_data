# NBA shot-chart CSVs

Shot-chart detail is stored in player CSVs (`<season-ending-year>[ps]/<player_id>.csv`), shooting-team CSVs (`team/<year>[ps]/<team_id>.csv`), and opponent CSVs (`team/<year>[ps]/<team_id>vs.csv`). The season ending in 2025, for example, is `2025`; `ps` marks playoffs. Some older `SHOT_TYPE` cells are blank in the NBA source.

## Shot context

`context/<year>_<rs|po>.csv` adds one row per play-by-play field-goal shot, keyed by `(GAME_ID, GAME_EVENT_ID)`. Join it to any shot CSV on both columns. The context files are derived by `nba-pipeline/tools/shotcharts/shot_context.py` from that pipeline's play-by-play and the production databallr analytics artifacts:

- `PHASE` is the shot's own `transition`, `second_chance`, or `halfcourt` phase. It is blank when the possession is invalid or the analytics play cannot be matched. A shot following an offensive player rebound in the same possession is `second_chance`; otherwise the engine's transition flag decides between `transition` and `halfcourt`.
- `GARBAGE` is the analytics engine's garbage-time flag (`1` or `0`). It is blank when the play cannot be matched.
- `QUALIFIERS` is a `|`-separated list of the NBA's shot labels: `fastbreak`, `2ndchance`, `fromturnover`, and `pointsinthepaint`. It is available from 2020-21 onward. A blank cell in older seasons means unavailable; a blank cell in later seasons means no listed label. NBA `fastbreak` and engine `transition` use different rules.

Context keys are unique within each file. Some shot-chart-detail rows have no play-by-play match and therefore no context row. The source shot columns and their paths remain unchanged.

## Averages by shot context

`context/averages/<year>_<rs|po>_phase.csv` gives `FGA`, `FGM`, and `FG_PCT` by the same `SHOT_ZONE_BASIC` / `SHOT_ZONE_AREA` / `SHOT_ZONE_RANGE` grouping used in `team/<year>[ps]/avg.csv`, split by `PHASE`. It covers every season here. `all` reproduces the existing league-average counts; `halfcourt`, `transition`, `second_chance`, and `unclassified` partition those shots. `unclassified` includes shots with no valid phase or no matching context row.

`context/averages/<year>_<rs|po>_qualifier.csv` is available from 2020-21 onward, when the NBA labels exist. `all` again reproduces the existing counts. `none` means a matched shot with none of the four labels; `any` means at least one; `unmatched` means no context row. The four named labels can overlap, so their counts must not be added together. Each file's `FG_PCT` is `FGM / FGA`, rounded to three decimals. Both sets of averages include garbage-time shots, as the existing `avg.csv` does.

The companion files are generated from the shooting-team CSVs joined to the context sidecars with `python3 build_context_averages.py --root . --out context/averages`. The builder checks that every `all` zone count agrees exactly with the existing `avg.csv`; regenerate them after changing shot rows or context.

The 2014-15 Toronto and 2008-09 Oklahoma City shooting-team and player files include restored rows from their opponents' existing `vs.csv` shot-chart-detail rows. The play-by-play supplies the shooter identity and shooting lineup for these rows; coordinates, shot outcome and other chart-detail fields come from the existing opponent rows. Two play-by-play shots that have no shot-chart-detail row in the repository remain out of these repairs pending source verification.

Shot locations before the tracking era are coarse; 1996-97 locations are especially poor, and many later pre-tracking rim shots default to 0 feet.
