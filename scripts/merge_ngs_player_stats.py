#!/usr/bin/env python3
"""Join weekly Next Gen Stats measures to the published player-week CSVs."""
import csv
import re
import unicodedata
from pathlib import Path

DATA = Path("data")
SOURCES = {
    "passing": {
        "file": "ngs_passing.csv",
        "columns": ["avg_time_to_throw", "avg_completed_air_yards", "avg_intended_air_yards",
                    "avg_air_yards_differential", "aggressiveness", "avg_air_yards_to_sticks",
                    "expected_completion_percentage", "completion_percentage_above_expectation"],
        "weight": "attempts",
    },
    "receiving": {
        "file": "ngs_receiving.csv",
        "columns": ["avg_cushion", "avg_separation", "avg_intended_air_yards",
                    "percent_share_of_intended_air_yards", "catch_percentage", "avg_yac",
                    "avg_expected_yac", "avg_yac_above_expectation"],
        "weight": "targets",
    },
    "rushing": {
        "file": "ngs_rushing.csv",
        "columns": ["efficiency", "percent_attempts_gte_eight_defenders", "avg_time_to_los",
                    "expected_rush_yards", "rush_yards_over_expected",
                    "rush_yards_over_expected_per_att", "rush_pct_over_expected"],
        "weight": "carries",
    },
}

def norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", value.lower())

def integer(value):
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None

def find(headers, *candidates):
    lookup = {h.strip().lower(): h for h in headers or []}
    return next((lookup[c.lower()] for c in candidates if c.lower() in lookup), None)

def read_source(kind, spec):
    path = DATA / spec["file"]
    if not path.exists():
        print(f"NGS {kind}: file unavailable; leaving its fields blank")
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        required = [find(headers, "season"), find(headers, "week"),
                    find(headers, "season_type"), find(headers, "player_display_name", "player_name"),
                    find(headers, "team_abbr", "team")]
        if not all(required):
            raise SystemExit(f"{path} is missing NGS join columns: {headers}")
        season_c, week_c, type_c, name_c, team_c = required
        value_cols = {col: find(headers, col) for col in spec["columns"]}
        available = [name for name, col in value_cols.items() if col]
        if not available:
            raise SystemExit(f"{path} has none of the expected metrics: {spec['columns']}")
        index = {}
        for row in reader:
            season, week = integer(row.get(season_c)), integer(row.get(week_c))
            name, team = norm(row.get(name_c)), norm(row.get(team_c))
            if season is None or week is None or week == 0 or not name or not team:
                continue
            key = (season, week, (row.get(type_c) or "REG").strip().upper(), name, team)
            index[key] = {metric: (row.get(col) or "").strip() for metric, col in value_cols.items() if col}
    print(f"NGS {kind}: indexed {len(index)} player-week rows; metrics {', '.join(available)}")
    return index

def main():
    indexes = {kind: read_source(kind, spec) for kind, spec in SOURCES.items()}
    for path in sorted(DATA.glob("stats_player_week_*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows, headers = list(reader), reader.fieldnames or []
        season_c = find(headers, "season")
        week_c = find(headers, "week")
        type_c = find(headers, "season_type")
        name_c = find(headers, "player_display_name", "player_name", "name")
        team_c = find(headers, "team_abbr", "recent_team", "team")
        if not all([season_c, week_c, name_c, team_c]):
            raise SystemExit(f"Missing player-week join columns in {path}: {headers}")
        ngs_columns = sorted({c for spec in SOURCES.values() for c in spec["columns"]})
        for column in ngs_columns:
            if column not in headers:
                headers.append(column)
        matched = {kind: 0 for kind in SOURCES}
        for row in rows:
            season, week = integer(row.get(season_c)), integer(row.get(week_c))
            if season is None or week is None or week == 0:
                continue
            season_type = (row.get(type_c) or ("POST" if week >= 19 else "REG")).strip().upper() if type_c else ("POST" if week >= 19 else "REG")
            ngs_week = week - 18 if season_type == "POST" and week >= 19 else week
            key = (season, ngs_week, season_type, norm(row.get(name_c)), norm(row.get(team_c)))
            for kind, spec in SOURCES.items():
                data = indexes[kind].get(key)
                if not data:
                    continue
                found = False
                for column in spec["columns"]:
                    value = data.get(column, "")
                    row[column] = value
                    found = found or bool(value)
                if found:
                    weight = row.get(spec["weight"], "")
                    row[kind + "_ngs_weight"] = weight
                    matched[kind] += 1
        for kind in SOURCES:
            weight_column = kind + "_ngs_weight"
            if weight_column not in headers:
                headers.append(weight_column)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"{path}: matched player rows by NGS type: {matched}")

if __name__ == "__main__":
    main()
