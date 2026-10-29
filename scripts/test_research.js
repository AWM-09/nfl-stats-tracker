'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('research.html','utf8');
const match=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].find(m=>m[1].includes('window.__researchLabTestApi'));
assert.ok(match,'Research Lab inline script not found.');
const source=match[1].replace(/\ninit\(\);\s*$/,'\n');
const sandbox=vm.createContext({window:{},document:{getElementById(){return {};},querySelectorAll(){return [];}}});
vm.runInContext(source,sandbox,{timeout:10000});
const api=sandbox.window.__researchLabTestApi;
assert.ok(api,'Research Lab test API not exposed.');
function row(values){return Object.assign({player_id:'P1',player_name:'Audit Player',player_display_name:'Audit Player',team:'NE',opponent_team:'NYJ',position_group:'QB',season:2025,week:1,season_type:'REG',game_id:'G1'},values);}
function near(actual,expected,label){assert.ok(actual!==null&&actual!==undefined&&Math.abs(Number(actual)-expected)<1e-8,label+': expected '+expected+', got '+actual);}
function test(name,fn){fn();console.log('PASS '+name);}
test('metric catalogue is broad and available',()=>{assert.ok(api.metricKeys().length>=40,'metric list unexpectedly shrank');});
test('CSV parser handles quoted commas and escaped quotes',()=>{const p=api.parseCSV('name,team,note\n"A, Player",NE,"said ""go"""\n');assert.equal(p.rows[0].name,'A, Player');assert.equal(p.rows[0].note,'said "go"');});
test('season completion percentage uses combined totals',()=>{near(api.aggregateMetric([row({completions:'8',attempts:'10'}),row({week:2,completions:'20',attempts:'40'})],'completion_pct'),56,'completion percentage');});
test('passer rating is finite and bounded',()=>{const x=api.metricValue(row({completions:'25',attempts:'35',passing_yards:'300',passing_tds:'3',passing_interceptions:'1'}),'passer_rating');assert.ok(Number.isFinite(x)&&x>=0&&x<=158.3,'invalid passer rating '+x);});
test('yards per attempt uses total yards and attempts',()=>{near(api.aggregateMetric([row({passing_yards:'100',attempts:'10'}),row({week:2,passing_yards:'270',attempts:'30'})],'pass_yards_per_attempt'),9.25,'yards per attempt');});
test('CPOE average is attempt-weighted',()=>{near(api.aggregateMetric([row({passing_cpoe:'10',attempts:'10'}),row({week:2,passing_cpoe:'-10',attempts:'30'})],'passing_cpoe'),-5,'CPOE');});
test('aDOT excludes rows without air yards',()=>{near(api.aggregateMetric([row({targets:'10',receiving_air_yards:''}),row({week:2,targets:'10',receiving_air_yards:'70'})],'average_depth_of_target'),7,'aDOT');});
test('TD/INT ratio is undefined with zero interceptions',()=>{assert.equal(api.metricValue(row({passing_tds:'5',passing_interceptions:'0'}),'td_int_ratio'),null);});
test('historic team aliases resolve to one franchise',()=>{assert.equal(api.teamCode('STL'),'LA');assert.equal(api.teamCode('LAR'),'LA');assert.equal(api.teamCode('SD'),'LAC');assert.equal(api.teamCode('OAK'),'LV');});
test('franchise record calculation counts only completed games',()=>{const g=[{season:2024,phase:'REG',home:'LA',away:'SF',hs:24,as:17},{season:2024,phase:'REG',home:'SEA',away:'LA',hs:20,as:10},{season:2024,phase:'REG',home:'LA',away:'ARI',hs:14,as:14},{season:2024,phase:'REG',home:'LA',away:'KC',hs:null,as:null}];const r=api.franchiseRecords(g,'LAR',2024,2024,'REG')[0];assert.equal(r.w,1);assert.equal(r.l,1);assert.equal(r.t,1);assert.equal(r.games,3);assert.equal(r.pf,48);assert.equal(r.pa,51);});
test('streaks break when a recorded game misses the threshold',()=>{const rows=[1,1,0,1,1,1].map((td,i)=>row({week:i+1,game_id:'G'+(i+1),passing_tds:String(td)}));const s=api.streakQuery(api.makeEvents(rows),'passing_tds','gte',1,2,'');assert.equal(s[0].length,3);assert.equal(s[1].length,2);});
test('all Research Lab panels are present',()=>{for(const id of ['panel-games','panel-streaks','panel-quality','panel-metrics','panel-franchise','panel-seasons','panel-firstseen','panel-search','panel-content','panel-downloads'])assert.ok(html.includes('id="'+id+'"'),'Missing '+id);assert.ok(html.includes('build-info.json'));});
console.log('Research Lab tests passed.');
