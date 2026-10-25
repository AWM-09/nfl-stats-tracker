#!/usr/bin/env python3
"""Build weekly team metrics from nflverse play-by-play CSV files."""
import csv, math
from collections import defaultdict
from pathlib import Path
ROOT=Path("data")
YEARS=range(2020,2027)
FIELDS=["season","week","season_type","team","games_played","points_scored","points_allowed","points_scored_per_game","points_allowed_per_game","point_differential","offensive_yards","offensive_yards_per_game","yards_allowed","yards_allowed_per_game","yards_per_play","turnover_differential","third_down_conversions","third_down_attempts","third_down_pct","third_down_pct_allowed","red_zone_tds","red_zone_trips","red_zone_td_pct","red_zone_tds_allowed","red_zone_trips_allowed","red_zone_td_pct_allowed","time_of_possession_seconds","penalties","penalty_yards","explosive_plays_20_plus","longest_play_td","longest_play_non_td","longest_play"]
def n(v):
 try:return float(v) if v not in ("",None) else 0.
 except (TypeError,ValueError):return 0.
def yes(v):return str(v or "").strip().lower() in ("1","1.0","true","yes")
def clock(v):
 try:
  p=str(v).split(":");return int(p[0])*60+int(p[1])+(int(p[2]) if len(p)>2 else 0)
 except Exception:return 0
for year in YEARS:
 path=ROOT/f"play_by_play_{year}.csv"
 if not path.exists(): print(f"Skipping {year}: no play-by-play CSV");continue
 games={}; tg=defaultdict(lambda:defaultdict(float)); teams_by_game=defaultdict(set)
 with path.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f); heads=set(rd.fieldnames or [])
  required={"season","week","game_id","posteam","defteam"}
  if not required.issubset(heads):raise SystemExit(f"{path} missing {sorted(required-heads)}")
  for r in rd:
   if int(n(r.get("season")))!=year:continue
   week=int(n(r.get("week"))); st=(r.get("season_type") or "REG").upper(); game=r.get("game_id") or ""
   off=(r.get("posteam") or "").strip(); deff=(r.get("defteam") or "").strip()
   if not week or not game or not off or not deff:continue
   key=(year,week,st,game); teams_by_game[key].update((off,deff))
   home=(r.get("home_team") or "").strip(); away=(r.get("away_team") or "").strip()
   if home and away:
    g=games.setdefault(key,{"home":home,"away":away,"hs":0,"as":0})
    g["hs"]=max(g["hs"],n(r.get("home_score")));g["as"]=max(g["as"],n(r.get("away_score")))
   d=tg[(key,off)]; pt=(r.get("play_type") or "").lower(); y=n(r.get("yards_gained"))
   if pt in ("pass","run","qb_kneel","qb_spike"):
    d["plays"]+=1;d["yards"]+=y
    if y>=20:d["explosive"]+=1
    d["longest"]=max(d["longest"],y)
    if yes(r.get("touchdown")):d["long_td"]=max(d["long_td"],y)
    else:d["long_non_td"]=max(d["long_non_td"],y)
   if str(r.get("down") or "")=="3":
    d["third_att"]+=1
    if yes(r.get("first_down")) or yes(r.get("touchdown")):d["third_conv"]+=1
   if yes(r.get("interception")) or yes(r.get("fumble_lost")):d["turnovers"]+=1
   if yes(r.get("penalty")):d["penalties"]+=1;d["penalty_yards"]+=n(r.get("penalty_yards"))
   drive=str(r.get("drive") or ""); yl=n(r.get("yardline_100"))
   if drive and 0<yl<=20:
    d["rz_seen:"+drive]=1
    if yes(r.get("touchdown")):d["rz_td:"+drive]=1
   if drive and r.get("drive_time_of_possession"):d["poss:"+drive]=clock(r.get("drive_time_of_possession"))
 buckets=defaultdict(lambda:defaultdict(float))
 for (key,team),d in tg.items():
  season,week,st,game=key;b=buckets[(season,week,st,team)]
  for k,v in d.items():
   if k.startswith("rz_seen:"):b["rz_trips"]+=v
   elif k.startswith("rz_td:"):b["rz_tds"]+=v
   elif k.startswith("poss:"):b["poss"]+=v
   else:b[k]+=v
 for key,ts in teams_by_game.items():
  if len(ts)!=2:continue
  a,bteam=sorted(ts);da=tg[(key,a)];db=tg[(key,bteam)]
  ba=buckets[(key[0],key[1],key[2],a)];bb=buckets[(key[0],key[1],key[2],bteam)]
  ba["yards_allowed"]+=db["yards"];bb["yards_allowed"]+=da["yards"]
  for out,src in ((ba,db),(bb,da)):
   out["third_att_allowed"]+=src["third_att"];out["third_conv_allowed"]+=src["third_conv"]
   out["rz_trips_allowed"]+=sum(v for k,v in src.items() if k.startswith("rz_seen:"))
   out["rz_tds_allowed"]+=sum(v for k,v in src.items() if k.startswith("rz_td:"))
  ba["turnovers_gained"]+=db["turnovers"];bb["turnovers_gained"]+=da["turnovers"]
 out=ROOT/f"stats_team_week_{year}.csv"
 with out.open("w",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=FIELDS);wr.writeheader()
  for (season,week,st,team),b in sorted(buckets.items()):
   gkeys=[k for k in games if k[0]==season and k[1]==week and k[2]==st and team in teams_by_game.get(k,set())]
   played=len(gkeys)
   if not played:continue
   scored=allowed=0
   for gk in gkeys:
    g=games[gk]
    if team==g["home"]:scored+=g["hs"];allowed+=g["as"]
    elif team==g["away"]:scored+=g["as"];allowed+=g["hs"]
   yards=b["yards"];plays=b["plays"];ta=b["third_att"];tc=b["third_conv"];taa=b["third_att_allowed"];tca=b["third_conv_allowed"];rz=b["rz_trips"];rzt=b["rz_tds"];rza=b["rz_trips_allowed"];rzta=b["rz_tds_allowed"]
   row={"season":season,"week":week,"season_type":st,"team":team,"games_played":played,"points_scored":scored,"points_allowed":allowed,"points_scored_per_game":scored/played,"points_allowed_per_game":allowed/played,"point_differential":scored-allowed,"offensive_yards":yards,"offensive_yards_per_game":yards/played,"yards_allowed":b["yards_allowed"],"yards_allowed_per_game":b["yards_allowed"]/played,"yards_per_play":yards/plays if plays else "","turnover_differential":b["turnovers_gained"]-b["turnovers"],"third_down_conversions":tc,"third_down_attempts":ta,"third_down_pct":100*tc/ta if ta else "","third_down_pct_allowed":100*tca/taa if taa else "","red_zone_tds":rzt,"red_zone_trips":rz,"red_zone_td_pct":100*rzt/rz if rz else "","red_zone_tds_allowed":rzta,"red_zone_trips_allowed":rza,"red_zone_td_pct_allowed":100*rzta/rza if rza else "","time_of_possession_seconds":int(b["poss"]),"penalties":int(b["penalties"]),"penalty_yards":int(b["penalty_yards"]),"explosive_plays_20_plus":int(b["explosive"]),"longest_play_td":b["long_td"],"longest_play_non_td":b["long_non_td"],"longest_play":b["longest"]}
   wr.writerow({k:(round(v,3) if isinstance(v,float) and math.isfinite(v) else v) for k,v in row.items()})
 print(f"Wrote {out}")
