'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('tracker.html', 'utf8');
const names = ['gameVideoGames','gameVideoWeeks','gameDateLabel','gameVideoRecord','gameVideoPlayers','buildGameVideoScript'];
const extracted = names.map(name => {
  const start = html.indexOf('function ' + name + '(');
  assert.notEqual(start, -1, 'Missing video maker function ' + name);
  const end = html.indexOf('\nfunction ', start + 1);
  return html.slice(start, end < 0 ? html.indexOf('</script>', start) : end);
}).join('\n');

const rows = [
  {season:2025,week:17,game_type:'REG',home_team:'BUF',away_team:'MIA',home_score:'21',away_score:'14',gameday:'2025-12-28'},
  {season:2026,week:1,game_type:'REG',home_team:'BUF',away_team:'MIA',home_score:'',away_score:'',gameday:'2026-09-10',gametime:'8:15 PM'},
  {season:2026,week:2,game_type:'REG',home_team:'NYJ',away_team:'NE',home_score:'',away_score:'',gameday:'2026-09-17'},
  {season:2026,week:17,game_type:'REG',home_team:'MIA',away_team:'BUF',home_score:'',away_score:'',gameday:'2027-01-03'}
];
const raw = [
  {season:2026,week:1,team:'BUF',player:'Josh Allen',fantasy_points:'24',passing_yards:'220'},
  {season:2026,week:1,team:'MIA',player:'Tua Tagovailoa',fantasy_points:'15',passing_yards:'180'}
];
const context = {
  scheduleRows: rows, raw,
  first:(obj,keys)=>{for(const k of keys)if(obj[k]!==undefined&&obj[k]!==''&&obj[k]!==null)return obj[k];return '';},
  num:value=>{const n=Number(value);return Number.isFinite(n)?n:0;},
  gameTeams:g=>({home:String(g.home_team||'').toUpperCase(),away:String(g.away_team||'').toUpperCase(),hs:g.home_score,as:g.away_score}),
  completedGame:g=>g.home_score!==''&&g.away_score!==''&&Number.isFinite(Number(g.home_score))&&Number.isFinite(Number(g.away_score)),
  isRegularSeasonGame:g=>g.game_type==='REG',
  teamName:code=>({BUF:'Buffalo Bills',MIA:'Miami Dolphins',NYJ:'New York Jets',NE:'New England Patriots'}[code]||code),
  metricValue:(r,key)=>key==='standard_fantasy_points'?Number(r.fantasy_points):null
};
vm.createContext(context);
vm.runInContext(extracted, context);

assert.deepEqual(Array.from(context.gameVideoWeeks(rows, 2026)), [1,2,17]);
assert.deepEqual(Array.from(context.gameVideoGames(rows, 2026, 1), x=>x.index), [1]);
assert.equal(context.gameVideoGames(rows, 2025, 1).length, 0);

const pre = context.buildGameVideoScript(rows[1], 'PRE', 2026, 1, 30, 'TikTok');
assert.match(pre, /PRE-GAME · 30s · TikTok/);
assert.match(pre, /0–2s · HOOK/);
assert.match(pre, /8:15 PM ET/);
assert.match(pre, /last completed meeting in the available schedule/i);
assert.match(pre, /Miami Dolphins 14, Buffalo Bills 21/);
assert.match(pre, /Key-player statistics unavailable/);
assert.match(pre, /simple record comparison, not a model forecast/);

const post = context.buildGameVideoScript(rows[1], 'POST', 2026, 1, 60, 'YouTube Shorts');
assert.match(post, /Final score unavailable/);
assert.match(post, /Play-by-play turning points are unavailable/);
assert.match(post, /Josh Allen \(24\.0 standard fantasy points\)/);
assert.match(post, /Next meeting listed in the schedule: 2027-01-03, 2026 Week 17/);
assert.match(post, /0–5s · RESULT/);

const longer = context.buildGameVideoScript(rows[1], 'POST', 2026, 1, 90, 'Instagram Reels');
assert.match(longer, /POST-GAME · 90s · Instagram Reels/);
assert.match(longer, /0–8s · RESULT/);

console.log('Game video maker selection and PRE/POST generation checks passed.');
