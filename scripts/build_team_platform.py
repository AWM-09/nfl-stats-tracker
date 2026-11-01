#!/usr/bin/env python3
"""Build source-labelled NFL franchise dossiers from nflverse data releases."""
import csv, gzip, json, os, re, unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CAP_LIMITS={1994:34.6,1995:37.1,1996:40.8,1997:41.5,1998:52.4,1999:57.3,2000:63.2,2001:67.4,2002:71.1,2003:75.0,2004:80.6,2005:85.5,2006:102.0,2007:109.0,2008:116.0,2009:128.0,2011:120.375,2012:120.6,2013:123.0,2014:133.0,2015:143.28,2016:155.27,2017:167.0,2018:177.2,2019:188.2,2020:198.2,2021:182.5,2022:208.2,2023:224.8,2024:255.4,2025:279.2,2026:301.2}
STATUS_LABELS={"ACT":"Active roster","DEV":"Practice squad","PUP":"Physically unable to perform","RES":"Reserve list","INA":"Inactive","IR":"Injured reserve","SUS":"Suspended","RET":"Retired","CUT":"Released","UFA":"Unrestricted free agent","EXE":"Commissioner exempt"}
CURRENT_TEAMS={
"ARI":"Arizona Cardinals","ATL":"Atlanta Falcons","BAL":"Baltimore Ravens","BUF":"Buffalo Bills",
"CAR":"Carolina Panthers","CHI":"Chicago Bears","CIN":"Cincinnati Bengals","CLE":"Cleveland Browns",
"DAL":"Dallas Cowboys","DEN":"Denver Broncos","DET":"Detroit Lions","GB":"Green Bay Packers",
"HOU":"Houston Texans","IND":"Indianapolis Colts","JAX":"Jacksonville Jaguars","KC":"Kansas City Chiefs",
"LAC":"Los Angeles Chargers","LAR":"Los Angeles Rams","LV":"Las Vegas Raiders","MIA":"Miami Dolphins",
"MIN":"Minnesota Vikings","NE":"New England Patriots","NO":"New Orleans Saints","NYG":"New York Giants",
"NYJ":"New York Jets","PHI":"Philadelphia Eagles","PIT":"Pittsburgh Steelers","SEA":"Seattle Seahawks",
"SF":"San Francisco 49ers","TB":"Tampa Bay Buccaneers","TEN":"Tennessee Titans","WAS":"Washington Commanders"}
TEAM_ALIASES={"JAC":"JAX","LA":"LAR","STL":"LAR","OAK":"LV","SD":"LAC","SDG":"LAC","WSH":"WAS"}
def canonical_team(value):
    code=str(value or "").strip().upper()
    return TEAM_ALIASES.get(code,code)
def norm(value):
    text=unicodedata.normalize("NFKD",str(value or ""))
    return re.sub(r"[^a-z0-9]","", "".join(c for c in text if not unicodedata.combining(c)).lower())
def first(row,keys,default=""):
    for key in keys:
        value=row.get(key)
        if value is not None and str(value).strip()!="": return str(value).strip()
    return default
def number(value):
    try:
        if value is None or str(value).strip()=="": return None
        n=float(value)
        return n if n==n and abs(n)!=float("inf") else None
    except (TypeError,ValueError): return None
def millions(value):
    n=number(value)
    return round(n/1_000_000,3) if n is not None else None
def truth(value): return str(value or "").strip().lower() in ("true","1","yes","y")
def read_rows(path):
    path=Path(path)
    if not path.exists(): return []
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))
def build_platform(data_dir="data",year=2026):
    root=Path(data_dir)
    roster_rows=read_rows(root/f"roster_weekly_{year}.csv")
    if not roster_rows: raise RuntimeError(f"Missing weekly roster file for {year}.")
    contract_rows=read_rows(root/"historical_contracts.csv.gz") or read_rows(root/"historical_contracts.csv")
    injury_rows=read_rows(root/f"injuries_{year}.csv")
    depth_rows=read_rows(root/f"depth_charts_{year}.csv")
    team_rows=read_rows(root/"teams_colors_logos.csv")
    weeks=[number(first(r,["week","week_num"])) for r in roster_rows]
    latest_week=max((int(x) for x in weeks if x is not None),default=0)
    latest=[r for r in roster_rows if (number(first(r,["week","week_num"])) or 0)==latest_week]
    contracts=defaultdict(list)
    contracts_by_id=defaultdict(list)
    for row in contract_rows:
        name=first(row,["player","player_name","full_name"])
        if name: contracts[norm(name)].append(row)
        player_id=first(row,["gsis_id","player_id"])
        if player_id: contracts_by_id[player_id].append(row)
    injuries=defaultdict(list)
    for row in injury_rows:
        name=first(row,["full_name","player_name","player"]);team=canonical_team(first(row,["team","team_abbr"]))
        if name and team: injuries[(team,norm(name))].append(row)
    depths=defaultdict(list)
    for row in depth_rows:
        name=first(row,["player_name","full_name","player"]);team=first(row,["team","team_abbr"]).upper()
        if name and team: depths[(team,norm(name))].append(row)
    metadata={}
    for row in team_rows:
        code=canonical_team(first(row,["team_abbr","team","team_code"]))
        if code:
            metadata[code]={"name":first(row,["team_name","team_full_name","team_nick"]) or code,
             "conference":first(row,["team_conf","conference"]),"division":first(row,["team_division","division"]),
             "color":first(row,["team_color","team_color_primary"]),"color2":first(row,["team_color2","team_color_secondary"]),
             "logo":first(row,["team_logo_espn","team_logo_wikipedia","team_logo"])}
    grouped=defaultdict(list)
    for row in latest:
        team=canonical_team(first(row,["team","team_abbr","recent_team"]))
        name=first(row,["full_name","player_name","player_display_name","name"])
        if not team or not name: continue
        roster_id=first(row,["gsis_id","player_id"])
        choices=contracts_by_id.get(roster_id,[]) if roster_id else contracts.get(norm(name),[])
        active=[c for c in choices if truth(c.get("is_active"))]
        # Never fall back to an expired historical deal. If IDs are unavailable,
        # only use a name match when it identifies one active contract unambiguously.
        contract=active[0] if len(active)==1 else None
        if len(active)>1 and roster_id:
            contract=sorted(active,key=lambda c:(number(c.get("year_signed")) or 0,number(c.get("years")) or 0),reverse=True)[0]
        signed=number(contract.get("year_signed")) if contract else None
        years=number(contract.get("years")) if contract else None
        valid_dates=(signed is not None and years is not None and 1990<=signed<=year and 1<=years<=15)
        end_year=int(signed+years-1) if valid_dates else None
        left=max(0,int(end_year-year+1)) if end_year is not None else None
        if end_year is not None and end_year<year:
            contract=None
            signed=years=end_year=left=None
        inj=sorted(injuries.get((team,norm(name)),[]),key=lambda x:first(x,["date_modified","report_date"]),reverse=True)
        depth=sorted(depths.get((team,norm(name)),[]),key=lambda x:(first(x,["dt","date_modified"]),-(number(x.get("pos_rank")) or 999)),reverse=True)
        injury=inj[0] if inj else None
        depth_row=depth[0] if depth else None
        status=first(row,["status","roster_status","status_description"])
        player={"name":name,"position":first(row,["position","pos"]),"number":first(row,["jersey_number","jersey","number"]),
         "status":status,"status_label":STATUS_LABELS.get(status,status or "Not supplied"),
         "height":first(row,["height"]),"weight":first(row,["weight"]),"experience":first(row,["years_exp","experience"]),
         "college":first(row,["college","college_name"]),"gsis_id":first(row,["gsis_id","player_id"]),
         "headshot":first(row,["headshot_url","headshot"]),
         "depth_position":first(depth_row or {},["pos_name","pos_abb","depth_chart_position"]),
         "depth_rank":number((depth_row or {}).get("pos_rank")),"depth_updated":first(depth_row or {},["dt","date_modified"]),
         "contract":None,"injury":None}
        if contract:
            player["contract"]={"year_signed":int(signed) if signed is not None else None,"years":int(years) if years is not None else None,
             "years_left_estimate":left,"end_year_estimate":int(end_year) if end_year is not None else None,
             "total_value":millions(contract.get("value")),"apy":millions(contract.get("apy")),
             "guaranteed":millions(contract.get("guaranteed")),"contract_team":first(contract,["team","team_abbr"]),
             "source_url":first(contract,["player_page"])}
        if injury:
            player["injury"]={"report_injury":first(injury,["report_primary_injury"]),"report_secondary":first(injury,["report_secondary_injury"]),
             "report_status":first(injury,["report_status"]),"practice_injury":first(injury,["practice_primary_injury"]),
             "practice_status":first(injury,["practice_status"]),"updated":first(injury,["date_modified"])}
        grouped[team].append(player)
    result={}
    for team in CURRENT_TEAMS:
        players=grouped.get(team,[])
        players.sort(key=lambda p:(p["position"],p["name"]))
        found=[p["contract"] for p in players if p["contract"]]
        apys=[c["apy"] for c in found if c.get("apy") is not None]
        guarantees=[c["guaranteed"] for c in found if c.get("guaranteed") is not None]
        reports=[p for p in players if p["injury"] and (p["injury"]["report_status"] or p["injury"]["practice_status"])]
        result[team]={"team":{"abbr":team,**metadata.get(team,{"name":team})},"roster":players,
         "injuries":[{"name":p["name"],"position":p["position"],**p["injury"]} for p in reports],
         "salary_cap":{"league_limit_millions":CAP_LIMITS.get(year),"known_roster_contracts":len(found),
          "known_annual_value_millions":round(sum(apys),3) if apys else None,
          "known_guaranteed_millions":round(sum(guarantees),3) if guarantees else None,"cap_space_millions":None,
          "note":"Annual contract value is not a current-year cap charge. The source does not provide every cap adjustment, dead-money charge, restructure or carryover, so team cap space is not calculated."}}
    payload={"version":1,"season":year,"generated_at":datetime.now(timezone.utc).isoformat(),"roster_week":latest_week,
     "teams":result,"league_cap_history_millions":CAP_LIMITS,"coverage":{"roster_rows":len(roster_rows),"latest_roster_rows":len(latest),"contracts_rows":len(contract_rows),
      "injury_rows":len(injury_rows),"depth_chart_rows":len(depth_rows),"franchises":len(result),"teams_with_rosters":sum(bool(v["roster"]) for v in result.values()),"teams_missing_rosters":[k for k,v in result.items() if not v["roster"]]},
     "sources":{"roster":"nflverse weekly rosters","contracts":"OverTheCap historical contracts via nflverse",
      "injuries":"nflverse injury reports where available","depth_chart":"nflverse depth charts","team_metadata":"nflverse team metadata"}}
    root.mkdir(parents=True,exist_ok=True)
    (root/"team-platform.json").write_text(json.dumps(payload,separators=(",",":"),ensure_ascii=False),encoding="utf-8")
    print(f"Built team platform: {len(result)} teams; {len(latest)} roster rows; {len(contract_rows)} contracts; {len(injury_rows)} injury rows.")
    return payload
if __name__=="__main__": build_platform("data",int(os.environ.get("NFL_SEASON","2026")))
