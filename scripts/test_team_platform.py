import csv,gzip,tempfile,unittest
from pathlib import Path
from build_team_platform import build_platform
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
 def test_optional_feeds_do_not_fabricate_data(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.write_csv(root/"roster_weekly_2026.csv",[{"season":"2026","week":"1","team":"BUF","full_name":"Test Player","position":"RB","status":"ACT"}])
   data=build_platform(root,2026);p=data["teams"]["BUF"]["roster"][0]
   self.assertIsNone(p["contract"]);self.assertIsNone(p["injury"]);self.assertIsNone(data["teams"]["BUF"]["salary_cap"]["cap_space_millions"]);self.assertEqual(len(data["teams"]),32);self.assertEqual(data["teams"]["NE"]["roster"],[])
if __name__=="__main__":unittest.main()
