# Changelog

## 2026-10-29

- Changed the Records Explorer to load a build-time precomputed ranking index instead of parsing all 27 weekly-stat CSVs and recalculating every metric in the browser.
- Added automated generation and publication of the compact index, capped to the 50 results the interface can display.
- Made index generation process one season at a time, removed unused per-player career aggregates and per-metric Sets, and replaced repeated full-list sorts with binary top-50 insertion to prevent build-runner memory exhaustion.

- Added NFL Research Lab with Player Game Finder, Streak Finder, Data Quality Centre, Statistical Definitions Library, Franchise History Explorer, historical season comparison, first-observed-season research, global search, saved configurations, shareable query URLs, exports and data-led content packs.
- Added automated Research Lab formula/data-shape tests to the pre-deployment workflow.
- Added build metadata and a visible published-build freshness indicator.
- Compressed play-by-play CSV files for web delivery and updated the Calendar loader to decompress on demand; uncompressed data remains available to generate team summaries during the build.
- Linked Research Lab from the existing tools.
- Corrected Records aggregation and source-coverage safeguards.

## Notes

Historical coverage varies by statistic. First-observed-season results are not an official rookie database. Franchise histories are schedule-derived and should be checked against official record books before publication.
