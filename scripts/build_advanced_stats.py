#!/usr/bin/env python3
"""Build compact, team-level situational NFL analytics from nflverse play-by-play.

The output deliberately aggregates play-by-play rather than publishing the huge raw
files to GitHub Pages. Empty denominators remain blank in CSV outputs.
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path("data")
YEARS = range(2010, 2027)
FIELDS = [
    "season", "week", "season_type", "team", "plays", "pass_plays", "run_plays",
    "yards", "epa", "successes", "success_rate", "explosive_plays", "explosive_rate",
    "third_down_attempts", "third_down_conversions", "third_down_pct",
    "fourth_down_attempts", "fourth_down_conversions", "fourth_down_pct",
    "red_zone_plays", "red_zone_tds", "red_zone_td_rate",
    "plays_leading", "plays_trailing", "plays_tied",
    "plays_q1", "plays_q2", "plays_q3", "plays_q4", "plays_q5plus",
    "drives", "scoring_drives", "scoring_drive_rate",
    "plays_allowed", "yards_allowed", "epa_allowed", "successes_allowed", "success_rate_allowed",
    "explosive_plays_allowed", "third_down_attempts_allowed",
    "third_down_conversions_allowed", "fourth_down_attempts_allowed",
    "fourth_down_conversions_allowed", "red_zone_plays_allowed", "red_zone_tds_allowed"
]

def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else 0.0
    except (TypeError, ValueError):
        return 0.0

def truth(v):
    return str(v or "").strip().lower() in {"1", "1.0", "true", "yes"}

def pct(a, b):
    return round(100 * a / b, 3) if b else ""

for year in YEARS:
    path = ROOT / f"play_by_play_{year}.csv"
    if not path.exists():
        print(f"Skipping {year}: no play-by-play CSV")
        continue
    # Store only aggregate counters; no play-by-play rows are written to the site.
    team_week = defaultdict(lambda: defaultdict(float))
    game_teams = defaultdict(set)
    drive_seen = defaultdict(set)
    drive_scored = defaultdict(set)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        needed = {"season", "week", "game_id", "posteam", "defteam"}
        if not needed.issubset(headers):
            raise SystemExit(f"{path} missing required columns: {sorted(needed - headers)}")
        for r in reader:
            if int(num(r.get("season"))) != year:
                continue
            week = int(num(r.get("week")))
            game = (r.get("game_id") or "").strip()
            st = (r.get("season_type") or "REG").strip().upper()
            off = (r.get("posteam") or "").strip()
            deff = (r.get("defteam") or "").strip()
            if not week or not game or not off or not deff:
                continue
            key = (year, week, st, off)
            game_key = (year, week, st, game)
            game_teams[game_key].update((off, deff))
            d = team_week[key]
            play_type = (r.get("play_type") or "").strip().lower()
            down = int(num(r.get("down")))
            yards = num(r.get("yards_gained"))
            # Exclude non-scrimmage plays from efficiency rates, but count accepted
            # pass/run/kneel/spike play types as scrimmage plays.
            scrimmage = play_type in {"pass", "run", "qb_kneel", "qb_spike"}
            if scrimmage:
                d["plays"] += 1
                d["yards"] += yards
                if play_type == "pass":
                    d["pass_plays"] += 1
                if play_type == "run":
                    d["run_plays"] += 1
                d["epa"] += num(r.get("epa"))
                if truth(r.get("success")):
                    d["successes"] += 1
                if 20 <= yards <= 100:
                    d["explosive_plays"] += 1
                q = int(num(r.get("qtr")))
                d["plays_q" + (str(q) if q <= 4 else "5plus")] += 1
                offense_score = num(r.get("posteam_score"))
                defense_score = num(r.get("defteam_score"))
                if offense_score > defense_score:
                    d["plays_leading"] += 1
                elif offense_score < defense_score:
                    d["plays_trailing"] += 1
                else:
                    d["plays_tied"] += 1
                yardline = num(r.get("yardline_100"))
                if 0 < yardline <= 20:
                    d["red_zone_plays"] += 1
                    if truth(r.get("touchdown")):
                        d["red_zone_tds"] += 1
            if down == 3:
                d["third_down_attempts"] += 1
                if truth(r.get("first_down")) or truth(r.get("touchdown")):
                    d["third_down_conversions"] += 1
            if down == 4:
                d["fourth_down_attempts"] += 1
                if truth(r.get("first_down")) or truth(r.get("touchdown")):
                    d["fourth_down_conversions"] += 1
            drive = (r.get("drive") or "").strip()
            if drive:
                drive_seen[key].add((game, drive))
                result = (r.get("drive_result") or "").strip().upper()
                if result in {"TOUCHDOWN", "FIELD GOAL"}:
                    drive_scored[key].add((game, drive))

    for key, d in team_week.items():
        d["drives"] = len(drive_seen[key])
        d["scoring_drives"] = len(drive_scored[key])

    # Build opponent-allowed metrics by joining each offense's weekly totals to
    # the opposing team's same-game aggregate. Team names are keyed to the game.
    by_game_offense = defaultdict(dict)
    for (season, week, st, team), d in team_week.items():
        for game_key, teams in game_teams.items():
            if game_key[:3] == (season, week, st) and team in teams:
                by_game_offense[game_key][team] = d
    for game_key, offenses in by_game_offense.items():
        teams = list(offenses)
        if len(teams) != 2:
            continue
        for team, opponent in ((teams[0], teams[1]), (teams[1], teams[0])):
            own = team_week[(game_key[0], game_key[1], game_key[2], team)]
            opp = offenses[opponent]
            own["plays_allowed"] += opp["plays"]
            own["yards_allowed"] += opp["yards"]
            own["epa_allowed"] += opp["epa"]
            own["successes_allowed"] += opp["successes"]
            own["explosive_plays_allowed"] += opp["explosive_plays"]
            own["third_down_attempts_allowed"] += opp["third_down_attempts"]
            own["third_down_conversions_allowed"] += opp["third_down_conversions"]
            own["fourth_down_attempts_allowed"] += opp["fourth_down_attempts"]
            own["fourth_down_conversions_allowed"] += opp["fourth_down_conversions"]
            own["red_zone_plays_allowed"] += opp["red_zone_plays"]
            own["red_zone_tds_allowed"] += opp["red_zone_tds"]

    out = ROOT / f"advanced_team_week_{year}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for (season, week, st, team), d in sorted(team_week.items()):
            row = {
                "season": season, "week": week, "season_type": st, "team": team,
                "plays": int(d["plays"]), "pass_plays": int(d["pass_plays"]),
                "run_plays": int(d["run_plays"]), "yards": round(d["yards"], 3),
                "epa": round(d["epa"], 3), "successes": int(d["successes"]),
                "success_rate": pct(d["successes"], d["plays"]),
                "explosive_plays": int(d["explosive_plays"]),
                "explosive_rate": pct(d["explosive_plays"], d["plays"]),
                "third_down_attempts": int(d["third_down_attempts"]),
                "third_down_conversions": int(d["third_down_conversions"]),
                "third_down_pct": pct(d["third_down_conversions"], d["third_down_attempts"]),
                "fourth_down_attempts": int(d["fourth_down_attempts"]),
                "fourth_down_conversions": int(d["fourth_down_conversions"]),
                "fourth_down_pct": pct(d["fourth_down_conversions"], d["fourth_down_attempts"]),
                "red_zone_plays": int(d["red_zone_plays"]), "red_zone_tds": int(d["red_zone_tds"]),
                "red_zone_td_rate": pct(d["red_zone_tds"], d["red_zone_plays"]),
                "plays_leading": int(d["plays_leading"]), "plays_trailing": int(d["plays_trailing"]),
                "plays_tied": int(d["plays_tied"]), "plays_q1": int(d["plays_q1"]),
                "plays_q2": int(d["plays_q2"]), "plays_q3": int(d["plays_q3"]),
                "plays_q4": int(d["plays_q4"]), "plays_q5plus": int(d["plays_q5plus"]),
                "drives": int(d["drives"]), "scoring_drives": int(d["scoring_drives"]),
                "scoring_drive_rate": pct(d["scoring_drives"], d["drives"]),
                "plays_allowed": int(d["plays_allowed"]), "yards_allowed": round(d["yards_allowed"], 3),
                "epa_allowed": round(d["epa_allowed"], 3),
                "successes_allowed": int(d["successes_allowed"]),
                "success_rate_allowed": pct(d["successes_allowed"], d["plays_allowed"]),
                "explosive_plays_allowed": int(d["explosive_plays_allowed"]),
                "third_down_attempts_allowed": int(d["third_down_attempts_allowed"]),
                "third_down_conversions_allowed": int(d["third_down_conversions_allowed"]),
                "fourth_down_attempts_allowed": int(d["fourth_down_attempts_allowed"]),
                "fourth_down_conversions_allowed": int(d["fourth_down_conversions_allowed"]),
                "red_zone_plays_allowed": int(d["red_zone_plays_allowed"]),
                "red_zone_tds_allowed": int(d["red_zone_tds_allowed"]),
            }
            writer.writerow(row)
    print(f"Wrote {out} ({len(team_week)} team-week rows)")
