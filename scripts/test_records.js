'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('index.html', 'utf8');
assert.ok(html.includes("./data/records-index.json"), 'Records page should load its precomputed index.');
const match = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)]
 .find(item => item[1].includes('function recordAggregateValue') && item[1].includes('function metricValue'));
assert.ok(match, 'Could not extract main dashboard script.');
const original = match[1];
const source = original.replace(/\ninit\(\);\s*$/, '\n');
assert.notEqual(source, original, 'Could not remove browser startup call for isolated tests.');
const sandbox = vm.createContext({
 console: { info() {}, log() {}, warn() {}, error() {} },
 document: { getElementById() { return {}; }, querySelectorAll() { return []; } },
 window: {},
 localStorage: { getItem() { return null; }, setItem() {} }
});
vm.runInNewContext(source + '\nglobalThis.__recordMetricKeys = Object.keys(metrics);', sandbox, { timeout: 10000 });
function row(values) {
 return Object.assign({ player:'Audit Player',team:'NE',position:'QB',season:2025,week:1,season_type:'REG' }, values);
}
function near(actual, expected, message) {
 assert.ok(actual!==null&&actual!==undefined&&Math.abs(Number(actual)-expected)<1e-8,
 message+': expected '+expected+', got '+actual);
}
function test(name, fn) { fn(); console.log('PASS '+name); }

test('metric catalogue remains complete', () => {
 assert.ok(sandbox.__recordMetricKeys.length >= 70, 'Metric inventory unexpectedly shrank.');
});
test('season passing yards sum weekly totals', () => {
 near(sandbox.recordAggregateValue([row({passing_yards:'400'}),row({week:2,passing_yards:'300'})],'passing_yards','season'),700,'Passing yards');
});
test('completion percentage uses total completions / attempts', () => {
 near(sandbox.recordAggregateValue([row({attempts:'10',completions:'8'}),row({week:2,attempts:'40',completions:'20'})],'completion_pct','season'),56,'Completion percentage');
});
test('passer rating uses combined passing totals', () => {
 const rows=[row({attempts:'20',completions:'14',passing_yards:'180',passing_tds:'2',passing_interceptions:'1'}),row({week:2,attempts:'30',completions:'21',passing_yards:'270',passing_tds:'3',passing_interceptions:'0'})];
 near(sandbox.recordAggregateValue(rows,'passer_rating','season'),sandbox.passerRatingForRows(rows),'Passer rating');
});
test('yards per attempt uses aggregate yards / attempts', () => {
 near(sandbox.recordAggregateValue([row({attempts:'10',passing_yards:'100'}),row({week:2,attempts:'30',passing_yards:'270'})],'pass_yards_per_attempt','season'),9.25,'Yards per attempt');
});
test('field-goal percentage uses total makes / attempts', () => {
 near(sandbox.recordAggregateValue([row({fg_made:'1',fg_att:'1'}),row({week:2,fg_made:'2',fg_att:'4'})],'fg_pct','season'),60,'Field-goal percentage');
});
test('CPOE season and career averages are attempt-weighted', () => {
 const rows=[row({attempts:'10',passing_cpoe:'10'}),row({week:2,attempts:'30',passing_cpoe:'-10'})];
 near(sandbox.recordAggregateValue(rows,'passing_cpoe','season'),-5,'Season CPOE');
 const bucket=sandbox.newCareerBucket([rows[0]]);
 sandbox.addCareerSeason(bucket,[rows[0]],2024);
 sandbox.addCareerSeason(bucket,[rows[1]],2025);
 near(sandbox.careerRecordValue(bucket,'passing_cpoe'),-5,'Career CPOE');
});
test('aDOT is recalculated from total air yards / targets', () => {
 near(sandbox.recordAggregateValue([row({targets:'10',receiving_air_yards:'100'}),row({week:2,targets:'30',receiving_air_yards:'120'})],'average_depth_of_target','season'),5.5,'aDOT');
});
test('punting and return averages use aggregate yards / attempts', () => {
 const rows=[row({pt_att:'2',pt_yards:'90',pt_net_yards:'80',kickoff_returns:'2',kickoff_return_yards:'50',punt_returns:'1',punt_return_yards:'15'}),row({week:2,pt_att:'4',pt_yards:'200',pt_net_yards:'190',kickoff_returns:'3',kickoff_return_yards:'90',punt_returns:'4',punt_return_yards:'80'})];
 near(sandbox.recordAggregateValue(rows,'punting_avg','season'),290/6,'Punting average');
 near(sandbox.recordAggregateValue(rows,'punting_net_avg','season'),270/6,'Net punting average');
 near(sandbox.recordAggregateValue(rows,'kick_return_avg','season'),140/5,'Kick-return average');
 near(sandbox.recordAggregateValue(rows,'punt_return_avg','season'),95/5,'Punt-return average');
});
test('standard fantasy points use source standard-scoring values', () => {
 near(sandbox.recordAggregateValue([row({fantasy_points:'14',receptions:'5'}),row({week:2,fantasy_points:'12',receptions:'4'})],'standard_fantasy_points','career'),26,'Fantasy points');
});
test('standard fantasy fallback does not award reception points', () => {
 near(sandbox.metricValue(row({passing_yards:'0',passing_tds:'0',passing_interceptions:'0',carries:'0',rushing_yards:'0',rushing_tds:'0',receiving_yards:'100',receptions:'5',receiving_tds:'1'}),'standard_fantasy_points'),16,'Fallback fantasy points');
});
test('fumble recovery aliases are not double-counted', () => {
 near(sandbox.metricValue(row({fumble_recovery_own:'1',def_fumble_recovery_own:'1',fumble_recovery_opp:'2'}),'def_fumble_recoveries'),3,'Fumble recoveries');
 near(sandbox.metricValue(row({def_fumble_recoveries:'7',fumble_recovery_own:'1',fumble_recovery_opp:'2'}),'def_fumble_recoveries'),7,'Preferred total fumble recovery column');
});
test('real source column aliases map correctly', () => {
 near(sandbox.metricValue(row({kickoff_return_yards:'68'}),'kick_return_yards'),68,'Kick-return yards');
 near(sandbox.metricValue(row({pt_inside_20:'3'}),'punts_inside_20'),3,'Punts inside 20');
 near(sandbox.metricValue(row({def_pass_defended:'2'}),'def_passes_defended'),2,'Passes defended');
 near(sandbox.metricValue(row({def_interception_yards:'41'}),'def_interception_return_yards'),41,'Interception return yards');
 near(sandbox.metricValue(row({special_teams_tds:'2'}),'return_tds'),2,'Special-teams touchdowns');
 assert.equal(sandbox.metricValue(row({rushing_yards_after_contact_per_attempt:'4.2'}),'rushing_yards_after_contact'),null);
});
test('TD / INT ratio is undefined when no interceptions occurred', () => {
 assert.equal(sandbox.metricValue(row({passing_tds:'5',passing_interceptions:'0'}),'td_int_ratio'),null);
});
test('zero placeholders are excluded from most-volume records', () => {
 const index=sandbox.createRecordsIndex();
 sandbox.addTopRecord(index,'season','REG','passing_yards',{value:0,player:'No attempts',year:2024});
 sandbox.addTopRecord(index,'season','REG','passing_yards',{value:5000,player:'Passer',year:2024});
 assert.equal(index.season.REG.passing_yards.length,1);
 assert.equal(index.season.REG.passing_yards[0].player,'Passer');
});

test('Records index retains the correct top 50 in descending order', () => {
 const index=sandbox.createRecordsIndex();
 for(let value=1;value<=100;value++){
  sandbox.addTopRecord(index,'season','REG','passing_yards',{
   value,player:'Player '+String(value).padStart(3,'0'),year:2025
  });
 }
 const list=index.season.REG.passing_yards;
 assert.equal(list.length,50,'Index should retain only the visible maximum of 50 records');
 assert.equal(Number(list[0].value),100,'Highest value should rank first');
 assert.equal(Number(list[49].value),51,'Fiftieth value should be correct');
 for(let i=1;i<list.length;i++){
  assert.ok(Number(list[i-1].value)>=Number(list[i].value),'Ranking order should be descending');
 }
});

test('historical records are built one season at a time', () => {
 const start=html.indexOf('async function buildRecordsIndex()');
 const end=html.indexOf('function setupRecordsControls()',start);
 assert.ok(start>=0&&end>start,'Records index builder should exist');
 const builder=html.slice(start,end);
 assert.ok(builder.includes('for(let yearIndex=0;yearIndex<YEARS.length;yearIndex++)'),
  'Builder should process a single season per loop iteration');
 assert.ok(!builder.includes('Promise.all(YEARS.map'),
  'Builder must not retain all historical CSV rows concurrently');
 assert.equal((builder.match(/const weeklyGroups=/g)||[]).length,1,
  'Weekly player statistics should be calculated once and shared across phases');
 assert.ok(html.includes('replace per-player/per-metric Sets'),
  'Career coverage metadata should stay compact');
});
test('untracked drop data is not converted to a zero-percent record', () => {
 assert.equal(sandbox.metricValue(row({targets:'20'}),'receiving_drop_pct'),null);
 assert.equal(sandbox.recordAggregateValue([row({targets:'20'})],'receiving_drop_pct','season'),null);
 near(sandbox.metricValue(row({targets:'20',receiving_drops:'2'}),'receiving_drop_pct'),10,'Drop percentage with source data');
});
test('missing historical air-yard rows do not dilute aDOT', () => {
 const rows=[row({targets:'10',receiving_air_yards:''}),row({week:2,targets:'10',receiving_air_yards:'70'})];
 near(sandbox.recordAggregateValue(rows,'average_depth_of_target','season'),7,'aDOT with partial source coverage');
 const bucket=sandbox.newCareerBucket([rows[0]]);
 sandbox.addCareerSeason(bucket,[rows[0]],2009);
 sandbox.addCareerSeason(bucket,[rows[1]],2025);
 near(sandbox.careerRecordValue(bucket,'average_depth_of_target'),7,'Career aDOT with partial source coverage');
 const coverage=bucket.metricYears.average_depth_of_target;
 assert.equal(coverage.first,2025);
 assert.equal(coverage.last,2025);
 assert.equal(coverage.count,1);
});
console.log('Record calculation tests passed.');
