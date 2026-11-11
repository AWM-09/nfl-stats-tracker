# Data Sources and Definitions

## Sources

- Weekly player statistics, schedules and play-by-play: [nflverse data repository](https://github.com/nflverse/nflverse-data).
- Official historical record reference: the [2025 NFL Record & Fact Book](https://static.clubs.nfl.com/image/upload/saints/bvaqvsl0fwdhlxu6wnw2.pdf), compiled by NFL Communications and Elias Sports Bureau; that edition states its information is current as of June 26, 2025.
- Current player statistics for spot checks: [official NFL statistics](https://www.nfl.com/stats/).
- Official NFL rule information is linked from the Rulebook tool.

## Method notes

- Weekly player CSVs are the source for exploratory player-performance queries. Derived season rates use combined numerator/denominator fields when available.
- The Commentary Box uses the published weekly player CSV for player-week fact leaderboards and available postgame player lines, the schedule CSV for completed scores, recent team results and fixtures, and compressed play-by-play on demand for game-level yards, player leaders, third-down outcomes and flagged events. Pregame history is restricted to the latest completed meeting; the stated score and win-probability forecast is a lightweight schedule-only estimate from completed regular-season scores before kickoff and does not include injuries, weather or player matchup adjustments. The forecast is presented as an estimate. Weekly previews and reviews derive record-only conference and division snapshots and low-record draft context from the selected season’s schedule; official tiebreakers, playoff odds, clinching/elimination scenarios and exact draft slots are not calculated. The 60-second weekly predictions script spotlights up to three matchups and lists the full selected-week forecast card. Schedule kickoff display uses source time text as supplied because the schedule does not consistently identify a time zone. Play-by-play detail is marked unavailable when a game ID or dataset rows cannot be matched.
- The Records page exposes the full metric catalogue used by the analytics platform. Numeric all-time entries are shown only for categories transcribed from the NFL Record & Fact Book; other tracked metrics remain selectable but clearly state when the cited official source does not publish a standardized all-time leaderboard. Dataset-derived player-week rankings are not presented as official records.
- Franchise roster snapshots select the latest available week independently for each team. Team Platform requests use a per-build cache key to prevent the browser from reusing an older roster JSON file. The System Health build fails when a franchise has fewer than 20 roster entries or lacks its own snapshot week.
- The nflreadr Contracts dictionary documents the contract schema: is_active is the current active-contract flag; GSIS ID is the join key; OTC team labels may be multi-team strings separated by slash; money fields are USD millions. The builder trusts the explicit active flag, joins by GSIS ID first, then exact normalized name/team, and reports match-method coverage. Contract seasons remaining are estimates from signing year and contract length; an active contract with incomplete dates still displays its monetary terms.
- Shareable Player Profiles are generated from those same weekly files during the Records precomputation stage. Season summaries are pre-aggregated; game logs are fetched for one selected season when requested.
- A blank or absent field is not a genuine zero. Advanced tracking statistics have shorter historical coverage than traditional box-score statistics.
- Franchise W-L-T and point totals are calculated from completed rows in the published schedule file. Historical aliases are normalized where known; verify major all-time claims externally.
- Play-by-play files are used during the build to calculate advanced team summaries. The web artifact uses gzip-compressed files, decompressed by the Calendar tool when requested.
- Season comparisons are descriptive unless an explicit adjustment is shown. The First-Seen Explorer uses first observed season, not an authoritative rookie/draft-year field.
- Prediction results are estimates. Backtests must not use information published after the game being predicted.
- The Content Studio produces drafts. Verify statistics, scope, names, sources and licenses before publication.
- The published System Health manifest checks required files, non-empty datasets, expected season coverage and the validity of the Records and Player Profile indexes. It does not independently verify every player statistic against the official NFL record book.

## Attribution

Follow license and attribution requirements of each upstream dataset. This independent project is not affiliated with or endorsed by the NFL or nflverse.
