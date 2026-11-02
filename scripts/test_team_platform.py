import csv,gzip,tempfile,unittest
from pathlib import Path
from build_team_platform import build_platform, contract_team_codes, canonical_team, millions
class TeamPlatformTests(unittest.TestCase):
 def write_csv(self,path,rows):
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 def test_roster_contract_injury_and_cap_are_source_labelled(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   self.write_csv(root/"roster_weekly_2026.csv",[
    {"season":"2026","week":"8","team":"NE","full_name":"Test Player","position":"QB","jersey_number":"10","status":"ACT","gsis_id":"P1"},
    {"season":"2026","week":"9","team":"NE","full_name":"Test Player","position":"QB","jersey_number":"10","status":"ACT","gsis_id":"P1"}])
   with gzip.open(root/"historical_contracts.csv.gz","wt",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["player","team","is_active","year_signed","years","value","apy","guaranteed","gsis_id"])
    w.writeheader();w.writerow({"player":"Test Player","team":"Patriots","is_active":"TRUE","year_signed":"2024","years":"4","value":"100","apy":"25","guaranteed":"60","gsis_id":"P1"})
   self.write_csv(root/"injuries_2026.csv",[{"team":"NE","full_name":"Test Player","report_primary_injury":"Ankle","report_status":"Questionable","date_modified":"2026-10-31"}])
   self.write_csv(root/"depth_charts_2026.csv",[{"team":"NE","player_name":"Test Player","pos_name":"Quarterback","pos_rank":"1","dt":"2026-10-31"}])
   self.write_csv(root/"teams_colors_logos.csv",[{"team_abbr":"NE","team_name":"New England Patriots","team_conf":"AFC","team_division":"East","team_color":"002244"}])
   data=build_platform(root,2026);team=data["teams"]["NE"];p=team["roster"][0]
   self.assertEqual(data["roster_week"],9);self.assertEqual(len(data["teams"]),32);self.assertEqual(data["coverage"]["teams_with_rosters"],1);self.assertEqual(len(data["coverage"]["teams_missing_rosters"]),31);self.assertEqual(p["contract"]["years_left_estimate"],2)
   self.assertEqual(p["contract"]["apy"],25);self.assertEqual(p["contract"]["total_value"],100);self.assertEqual(p["contract"]["guaranteed"],60);self.assertEqual(p["contract"]["end_year_estimate"],2027);self.assertEqual(p["injury"]["report_status"],"Questionable")
   self.assertEqual(p["depth_rank"],1);self.assertEqual(team["salary_cap"]["league_limit_millions"],301.2)
   self.assertIsNone(team["salary_cap"]["cap_space_millions"]);self.assertEqual(team["team"]["name"],"New England Patriots")
 def test_each_team_uses_its_latest_available_week_and_contract_name_fallback(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   self.write_csv(root/"roster_weekly_2026.csv",[
    {"season":"2026","week":"8","team":"ARI","full_name":"Arizona Player","position":"DB","status":"ACT","gsis_id":"ARI-ID"},
    {"season":"2026","week":"7","team":"HST","full_name":"Houston Player","position":"QB","status":"ACT","gsis_id":"ROSTER-ID-DOES-NOT-MATCH"},
    {"season":"2026","week":"6","team":"HOU","full_name":"Old Houston Player","position":"RB","status":"ACT","gsis_id":"OLD-ID"}])
   with gzip.open(root/"historical_contracts.csv.gz","wt",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["player","team","is_active","year_signed","years","value","apy","guaranteed","gsis_id"])
    w.writeheader()
    w.writerow({"player":"Houston Player","team":"Texans","is_active":"TRUE","year_signed":"2024","years":"4","value":"100","apy":"25","guaranteed":"60","gsis_id":"CONTRACT-ID"})
   data=build_platform(root,2026)
   hou=data["teams"]["HOU"]
   self.assertEqual(data["roster_week"],8)
   self.assertEqual(data["teams"]["ARI"]["roster_week"],8)
   self.assertEqual(hou["roster_week"],7)
   self.assertEqual(len(hou["roster"]),1)
   self.assertEqual(hou["roster"][0]["name"],"Houston Player")
   self.assertEqual(hou["roster"][0]["contract"]["years_left_estimate"],2)
   self.assertEqual(hou["roster"][0]["contract"]["end_year_estimate"],2027)
   self.assertEqual(hou["roster"][0]["contract"]["apy"],25)
   self.assertEqual(hou["roster"][0]["contract"]["total_value"],100)
   self.assertEqual(hou["roster"][0]["contract"]["guaranteed"],60)
   self.assertEqual(data["coverage"]["teams_missing_rosters"].count("HOU"),0)
 def test_real_over_the_cap_schema_matches_by_gsis_id_and_exact_team_name(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   self.write_csv(root/"roster_weekly_2026.csv",[
    {"season":"2026","week":"8","team":"CIN","full_name":"Example Quarterback","position":"QB","status":"ACT","gsis_id":"GSIS-PLAYER-A"},
    {"season":"2026","week":"8","team":"NE","full_name":"Example Veteran","position":"WR","status":"ACT"},
    {"season":"2026","week":"8","team":"NE","full_name":"Example Incomplete Date","position":"LB","status":"ACT","gsis_id":"GSIS-PLAYER-C"}])
   with gzip.open(root/"historical_contracts.csv.gz","wt",newline="",encoding="utf-8") as f:
    fields=["player","position","team","is_active","year_signed","years","value","apy","guaranteed","gsis_id"]
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    w.writerow({"player":"Example Quarterback","position":"QB","team":"Bengals","is_active":"TRUE","year_signed":"2023","years":"5","value":"275","apy":"55","guaranteed":"146.5","gsis_id":"GSIS-PLAYER-A"})
    w.writerow({"player":"Example Veteran","position":"WR","team":"Patriots","is_active":"TRUE","year_signed":"2024","years":"4","value":"80","apy":"20","guaranteed":"40","gsis_id":"GSIS-PLAYER-B"})
    w.writerow({"player":"Example Incomplete Date","position":"LB","team":"NE","is_active":"TRUE","year_signed":"","years":"","value":"12","apy":"6","guaranteed":"8","gsis_id":"GSIS-PLAYER-C"})
   data=build_platform(root,2026)
   cin=data["teams"]["CIN"]["roster"][0]["contract"]
   ne={p["name"]:p["contract"] for p in data["teams"]["NE"]["roster"]}
   self.assertEqual(cin["total_value"],275)
   self.assertEqual(cin["apy"],55)
   self.assertEqual(cin["years_left_estimate"],2)
   self.assertEqual(cin["end_year_estimate"],2027)
   self.assertEqual(ne["Example Veteran"]["apy"],20)
   self.assertEqual(ne["Example Veteran"]["years_left_estimate"],2)
   self.assertEqual(ne["Example Incomplete Date"]["apy"],6)
   self.assertIsNone(ne["Example Incomplete Date"]["years_left_estimate"])
   self.assertEqual(data["coverage"]["contracts_matched"],3)
   self.assertEqual(data["coverage"]["contracts_matched_by_gsis_id"],2)
   self.assertEqual(data["coverage"]["contracts_matched_by_name"],1)
 def test_contract_team_labels_resolve_over_the_cap_nicknames_and_history(self):
  self.assertEqual(contract_team_codes("NYJ/GB"),{"NYJ","GB"})
  self.assertEqual(contract_team_codes("Bengals"),{"CIN"})
  self.assertEqual(contract_team_codes("Patriots"),{"NE"})
  self.assertEqual(canonical_team("Buccaneers"),"TB")
  self.assertEqual(millions("275"),275)
  self.assertEqual(millions("275000000"),275)
 def test_optional_feeds_do_not_fabricate_data(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.write_csv(root/"roster_weekly_2026.csv",[{"season":"2026","week":"1","team":"BUF","full_name":"Test Player","position":"RB","status":"ACT"}])
   data=build_platform(root,2026);p=data["teams"]["BUF"]["roster"][0]
   self.assertIsNone(p["contract"]);self.assertIsNone(p["injury"]);self.assertIsNone(data["teams"]["BUF"]["salary_cap"]["cap_space_millions"]);self.assertEqual(len(data["teams"]),32);self.assertEqual(data["teams"]["NE"]["roster"],[])
if __name__=="__main__":unittest.main()
