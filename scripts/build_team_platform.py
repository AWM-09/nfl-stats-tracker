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
TEAM_ALIASES={"JAC":"JAX","HST":"HOU","LA":"LAR","STL":"LAR","OAK":"LV","SD":"LAC","SDG":"LAC","WSH":"WAS","WFT":"WAS","CLV":"CLE","ARZ":"ARI"}
TEAM_NAME_ALIASES={
"ARIZONA":"ARI","ARIZONA CARDINALS":"ARI","CARDINALS":"ARI",
"ATLANTA":"ATL","ATLANTA FALCONS":"ATL","FALCONS":"ATL",
"BALTIMORE":"BAL","BALTIMORE RAVENS":"BAL","RAVENS":"BAL",
"BUFFALO":"BUF","BUFFALO BILLS":"BUF","BILLS":"BUF",
"CAROLINA":"CAR","CAROLINA PANTHERS":"CAR","PANTHERS":"CAR",
"CHICAGO":"CHI","CHICAGO BEARS":"CHI","BEARS":"CHI",
"CINCINNATI":"CIN","CINCINNATI BENGALS":"CIN","BENGALS":"CIN",
"CLEVELAND":"CLE","CLEVELAND BROWNS":"CLE","BROWNS":"CLE",
"DALLAS":"DAL","DALLAS COWBOYS":"DAL","COWBOYS":"DAL",
"DENVER":"DEN","DENVER BRONCOS":"DEN","BRONCOS":"DEN",
"DETROIT":"DET","DETROIT LIONS":"DET","LIONS":"DET",
"GREEN BAY":"GB","GREEN BAY PACKERS":"GB","PACKERS":"GB",
"HOUSTON":"HOU","HOUSTON TEXANS":"HOU","TEXANS":"HOU",
"INDIANAPOLIS":"IND","INDIANAPOLIS COLTS":"IND","COLTS":"IND",
"JACKSONVILLE":"JAX","JACKSONVILLE JAGUARS":"JAX","JAGUARS":"JAX",
"KANSAS CITY":"KC","KANSAS CITY CHIEFS":"KC","CHIEFS":"KC",
"LOS ANGELES CHARGERS":"LAC","SAN DIEGO CHARGERS":"LAC","CHARGERS":"LAC",
"LOS ANGELES RAMS":"LAR","ST LOUIS RAMS":"LAR","RAMS":"LAR",
"LAS VEGAS":"LV","LAS VEGAS RAIDERS":"LV","OAKLAND RAIDERS":"LV","RAIDERS":"LV",
"MIAMI":"MIA","MIAMI DOLPHINS":"MIA","DOLPHINS":"MIA",
"MINNESOTA":"MIN","MINNESOTA VIKINGS":"MIN","VIKINGS":"MIN",
"NEW ENGLAND":"NE","NEW ENGLAND PATRIOTS":"NE","PATRIOTS":"NE",
"NEW ORLEANS":"NO","NEW ORLEANS SAINTS":"NO","SAINTS":"NO",
"NEW YORK GIANTS":"NYG","GIANTS":"NYG",
"NEW YORK JETS":"NYJ","JETS":"NYJ",
"PHILADELPHIA":"PHI","PHILADELPHIA EAGLES":"PHI","EAGLES":"PHI",
"PITTSBURGH":"PIT","PITTSBURGH STEELERS":"PIT","STEELERS":"PIT",
"SEATTLE":"SEA","SEATTLE SEAHAWKS":"SEA","SEAHAWKS":"SEA",
"SAN FRANCISCO":"SF","SAN FRANCISCO 49ERS":"SF","49ERS":"SF",
"TAMPA BAY":"TB","TAMPA BAY BUCCANEERS":"TB","BUCCANEERS":"TB","BUCS":"TB",
"TENNESSEE":"TEN","TENNESSEE TITANS":"TEN","TITANS":"TEN",
"WASHINGTON":"WAS","WASHINGTON COMMANDERS":"WAS","COMMANDERS":"WAS",
"WASHINGTON FOOTBALL TEAM":"WAS","WASHINGTON REDSKINS":"WAS",
"BILLS":"BUF","DOLPHINS":"MIA","PATS":"NE","PATRIOTS":"NE","JETS":"NYJ",
"RAVENS":"BAL","BENGALS":"CIN","BROWNS":"CLE","STEELERS":"PIT",
"TEXANS":"HOU","COLTS":"IND","JAGS":"JAX","JAGUARS":"JAX","TITANS":"TEN",
"BRONCOS":"DEN","CHIEFS":"KC","RAIDERS":"LV","CHARGERS":"LAC",
"COWBOYS":"DAL","GIANTS":"NYG","EAGLES":"PHI","COMMANDERS":"WAS",
"BEARS":"CHI","LIONS":"DET","PACKERS":"GB","VIKINGS":"MIN",
"FALCONS":"ATL","PANTHERS":"CAR","SAINTS":"NO","BUCS":"TB","BUCCANEERS":"TB",
"CARDINALS":"ARI","RAMS":"LAR","49ERS":"SF","NINERS":"SF","SEAHAWKS":"SEA"
}
def canonical_team(value):
    raw=str(value or "").strip()
    code=raw.upper()
    if code in CURRENT_TEAMS: return code
    if code in TEAM_ALIASES: return TEAM_ALIASES[code]
    normalized=re.sub(r"[^A-Z0-9]","",code)
    for alias,target in TEAM_NAME_ALIASES.items():
        if re.sub(r"[^A-Z0-9]","",alias)==normalized: return target
    return code
def contract_team_codes(value):
    # OTC can report abbreviations ("NYJ/GB") or team nicknames ("Bengals").
    parts=re.split(r"\s*(?:/|,|&|;|\band\b|\bor\b)\s*",str(value or ""),flags=re.I)
    return {code for part in parts if part.strip()
            for code in [canonical_team(part)] if code in CURRENT_TEAMS}
def contract_matches_team(row,team):
    raw=first(row,["team","team_abbr","team_code"])
    if not raw: return False
    return team in contract_team_codes(raw)
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
    # OverTheCap/nflreadr contract fields are already in USD millions
    # (e.g. value=275, APY=55). Also tolerate legacy dollar-denominated files.
    n=number(value)
    if n is None: return None
    if abs(n)>=100_000: n/=1_000_000
    return round(n,3)
def truth(value): return str(value or "").strip().lower() in ("true","1","yes","y")
def norm_id(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").strip().lower())
def active_contract_for_season(row, season):
    # nflreadr documents is_active as OverTheCap's current active-contract flag.
    # Trust an explicit flag; only fall back to dates when the flag is absent.
    flag=first(row,["is_active","active","currently_active"]).strip().lower()
    if flag in ("false","0","no","n","inactive"): return False
    if flag in ("true","1","yes","y","active"): return True
    signed=number(first(row,["year_signed","signing_year"]))
    years=number(first(row,["years","contract_years","length","yrs"]))
    if signed is None or years is None or not (1990<=signed<=season and 1<=years<=15): return False
    return int(signed+years-1)>=season
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
    # Select the newest available snapshot independently for each franchise.
    # A league-wide max week can silently drop a team whose feed is a week behind.
    weekly_by_team=defaultdict(list)
    for row in roster_rows:
        team=canonical_team(first(row,["team","team_abbr","recent_team"]))
        week_value=number(first(row,["week","week_num"]))
        name=first(row,["full_name","player_name","player_display_name","name"])
        if team in CURRENT_TEAMS and week_value is not None and name:
            weekly_by_team[team].append((int(week_value),row))
    team_roster_weeks={team:max((week for week,_ in entries),default=0)
                       for team,entries in weekly_by_team.items()}
    latest=[]
    for team,entries in weekly_by_team.items():
        team_week=team_roster_weeks[team]
        latest.extend(row for week,row in entries if week==team_week)
    contracts=defaultdict(list)
    contracts_by_id=defaultdict(list)
    for row in contract_rows:
        name=first(row,["player","player_name","full_name"])
        if name: contracts[norm(name)].append(row)
        player_id=first(row,["gsis_id","player_id"])
        if player_id: contracts_by_id[norm_id(player_id)].append(row)
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
    matched_by_gsis_id=0
    matched_by_name=0
    for row in latest:
        team=canonical_team(first(row,["team","team_abbr","recent_team"]))
        name=first(row,["full_name","player_name","player_display_name","name"])
        if not team or not name: continue
        roster_id=first(row,["gsis_id","player_id"])
        id_choices=contracts_by_id.get(norm_id(roster_id),[]) if roster_id else []
        name_choices=contracts.get(norm(name),[])
        # GSIS ID is the source-documented primary join key. Do not reject a
        # unique ID match because OTC still lists a historical team label.
        active_id=[c for c in id_choices if active_contract_for_season(c,year)]
        active_name=[c for c in name_choices if active_contract_for_season(c,year)]
        contract=None
        match_method=None
        contract_sort=lambda c: (
            number(first(c,["year_signed","signing_year"])) or 0,
            number(first(c,["years","contract_years","length","yrs"])) or 0
        )
        if active_id:
            # A player's current active contract is a single GSIS identity;
            # where duplicate active entries exist, prefer the latest signed row.
            contract=max(active_id,key=contract_sort)
            match_method="gsis_id"
        else:
            name_team=[c for c in active_name if contract_matches_team(c,team)]
            if name_team:
                contract=max(name_team,key=contract_sort)
                match_method="exact_name_and_team"
            elif len(active_name)==1:
                contract=active_name[0]
                match_method="unique_exact_name"
        if contract:
            if match_method=="gsis_id": matched_by_gsis_id+=1
            else: matched_by_name+=1
        signed=number(first(contract,["year_signed","signing_year"])) if contract else None
        years=number(first(contract,["years","contract_years","length","yrs"])) if contract else None
        valid_dates=(signed is not None and years is not None and 1990<=signed<=year and 1<=years<=15)
        calculated_end=int(signed+years-1) if valid_dates else None
        # Do not discard the contract's money fields if date estimates are absent
        # or inconsistent with the source's explicit is_active flag.
        end_year=calculated_end if calculated_end is not None and calculated_end>=year else None
        left=int(end_year-year+1) if end_year is not None else None
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
         "roster_week":team_roster_weeks.get(team,0),
         "injuries":[{"name":p["name"],"position":p["position"],**p["injury"]} for p in reports],
         "salary_cap":{"league_limit_millions":CAP_LIMITS.get(year),"known_roster_contracts":len(found),
          "known_annual_value_millions":round(sum(apys),3) if apys else None,
          "known_guaranteed_millions":round(sum(guarantees),3) if guarantees else None,"cap_space_millions":None,
          "note":"Annual contract value is not a current-year cap charge. The source does not provide every cap adjustment, dead-money charge, restructure or carryover, so team cap space is not calculated."}}
    payload={"version":1,"season":year,"generated_at":datetime.now(timezone.utc).isoformat(),"roster_week":latest_week,
     "teams":result,"league_cap_history_millions":CAP_LIMITS,"coverage":{"roster_rows":len(roster_rows),"latest_roster_rows":len(latest),"contracts_rows":len(contract_rows),
      "injury_rows":len(injury_rows),"depth_chart_rows":len(depth_rows),"franchises":len(result),"teams_with_rosters":sum(bool(v["roster"]) for v in result.values()),"teams_missing_rosters":[k for k,v in result.items() if not v["roster"]],
      "teams_below_20_players":[k for k,v in result.items() if len(v["roster"])<20],
      "teams_with_contracts":[k for k,v in result.items() if any(p["contract"] for p in v["roster"])],
      "contracts_matched":sum(1 for v in result.values() for p in v["roster"] if p["contract"]),
      "contracts_matched_by_gsis_id":matched_by_gsis_id,
      "contracts_matched_by_name":matched_by_name,
      "contract_match_rate":round(sum(1 for v in result.values() for p in v["roster"] if p["contract"])/max(1,len(latest)),4),
      "team_roster_weeks":team_roster_weeks},
     "sources":{"roster":"nflverse weekly rosters","contracts":"OverTheCap historical contracts via nflverse",
      "injuries":"nflverse injury reports where available","depth_chart":"nflverse depth charts","team_metadata":"nflverse team metadata"}}
    root.mkdir(parents=True,exist_ok=True)
    (root/"team-platform.json").write_text(json.dumps(payload,separators=(",",":"),ensure_ascii=False),encoding="utf-8")
    matched=sum(1 for v in result.values() for p in v["roster"] if p["contract"])
    print(f"Built team platform: {len(result)} teams; {len(latest)} latest-week roster rows; {len(contract_rows)} contract records; {matched} roster contracts matched ({matched_by_gsis_id} GSIS ID, {matched_by_name} name); {len(injury_rows)} injury rows.")
    return payload
if __name__=="__main__": build_platform("data",int(os.environ.get("NFL_SEASON","2026")))
