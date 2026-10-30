## 2026-10-30

- Added a dedicated platform homepage that organises all existing tools into a clear navigation structure; moved the original weekly dashboard to `tracker.html`.
- Added shareable Player Profiles with season-by-season summaries, career totals where tracked, progression charts and on-demand game logs for a selected season.
- Extended the historical Records build to generate the compact player-season index in the same pass, avoiding a second download/parse of the 2000–2026 weekly files.
- Added a System Health Centre backed by a build-generated manifest covering player, team, advanced-team and play-by-play datasets, Records and Player Profile indexes, and schedule data.
- Added published-site integration tests for required pages, local links, mobile metadata, generated indexes, health manifest and build metadata.
- Added consistent Home, Player Profiles and System Health navigation to the existing tools, with shared mobile layout improvements.

# Changelog

## 2026-10-29

- Changed the Records Explorer to load a build-time precomputed ranking index instead of parsing all 27 weekly-stat CSVs and recalculating every metric in the browser.
- Added automated generation and publication of the compact index, capped to the 50 results the interface can display.
- Made index generation process one season at a time, removed unused per-player career aggregates and per-metric Sets, and replaced repeated full-list sorts with binary top-50 insertion to prevent build-runner memory exhaustion.
- Calculated weekly metric results once and reused them for overall, regular-season and playoff indexes instead of calculating the same player-week three times.

- Added NFL Research Lab with Player Game Finder, Streak Finder, Data Quality Centre, Statistical Definitions Library, Franchise History Explorer, historical season comparison, first-observed-season research, global search, saved configurations, shareable query URLs, exports and data-led content packs.
- Added automated Research Lab formula/data-shape tests to the pre-deployment workflow.
- Added build metadata and a visible published-build freshness indicator.
- Compressed play-by-play CSV files for web delivery and updated the Calendar loader to decompress on demand; uncompressed data remains available to generate team summaries during the build.
- Linked Research Lab from the existing tools.
- Corrected Records aggregation and source-coverage safeguards.

## Notes

Historical coverage varies by statistic. First-observed-season results are not an official rookie database. Franchise histories are schedule-derived and should be checked against official record books before publication.
