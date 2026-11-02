# Data Sources and Definitions

## Sources

- Weekly player statistics, schedules and play-by-play: [nflverse data repository](https://github.com/nflverse/nflverse-data).
- Official historical record reference: the [2025 NFL Record & Fact Book](https://static.clubs.nfl.com/image/upload/saints/bvaqvsl0fwdhlxu6wnw2.pdf), compiled by NFL Communications and Elias Sports Bureau; that edition states its information is current as of June 26, 2025.
- Current player statistics for spot checks: [official NFL statistics](https://www.nfl.com/stats/).
- Official NFL rule information is linked from the Rulebook tool.

## Method notes

- Weekly player CSVs are the source for exploratory player-performance queries. Derived season rates use combined numerator/denominator fields when available.
- The Records page displays only a curated reference transcribed from the NFL Record & Fact Book. It no longer displays dataset-derived player-week rankings as records.
- Franchise roster snapshots select the latest available week independently for each team. Team Platform requests use a per-build cache key to prevent the browser from reusing an older roster JSON file. The System Health build fails when a franchise has fewer than 20 roster entries or lacks its own snapshot week.
- OverTheCap contract figures in the nflverse contract feed are already denominated in USD millions. Team matching supports OTC franchise nicknames and multi-team labels; contract years remaining are estimates from signing year and contract length.
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
