const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'commentary.html'), 'utf8');
const home = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

for (const id of [
  'pregameGame', 'postgameGame', 'factSeason', 'factPhase', 'factMetric',
  'factWeek', 'factTeam', 'factLimit', 'commentGame', 'commentTone',
  'contentGame', 'contentTopic', 'contentEvidence', 'loadStatus', 'pregameOutput',
  'postgameOutput', 'factsOutput', 'commentaryOutput', 'contentOutput'
]) assert.match(page, new RegExp(`id=["']${id}["']`), `Commentary page is missing #${id}`);

for (const feature of ['buildPregame', 'buildPostgame', 'factGen', 'draft', 'buildContent', 'recordsBefore', 'forecast', 'nextMeeting', 'pregameContext', 'postgameReport', 'loadGamePlays', 'gamePlaySummary']) {
  assert.match(page, new RegExp(`function ${feature}\\(`), `Missing ${feature} generator`);
}
assert.match(page, /schedule\.csv\?v=commentary-20261111-v2/, 'Schedule request should use cache busting');
assert.match(page, /stats_player_week_\$\{current\}\.csv\?v=commentary-20261111-v2/, 'Player stats request should use cache busting');
assert.match(page, /String\(v\)\.trim\(\)===''|String\(v\)\.trim\(\)===\"\"/, 'Blank schedule scores must not be treated as zero');
assert.match(page, /x\.value>0/, 'Zero-valued players should not be described as game performances');
assert.match(page, /PREDICTION/, 'Pregame notes should state the explicit model prediction');
assert.match(page, /NEXT SCHEDULED MEETING/, 'Pregame notes should report whether a mutual rematch is scheduled');
assert.doesNotMatch(page, /Add at least 10 characters of evidence/, 'Content Studio must not require evidence notes');
assert.match(page, /Optional extra notes/, 'Content notes should be clearly optional');
assert.match(page, /COMPARATIVE READ/, 'Postgame analysis should compare team production');
assert.match(page, /play_by_play_\$\{season\}\.csv\.gz/, 'Postgame recap must load the published play-by-play data');
assert.match(home, /href="\.\/commentary\.html(?:\?[^\"]*)?"/, 'Home page must link to Commentary Box');
const playerPath = path.join(root, 'data', 'stats_player_week_2026.csv');
if (fs.existsSync(playerPath)) {
  const header = fs.readFileSync(playerPath, 'utf8').split(/\r?\n/, 1)[0].split(',');
  for (const column of ['season', 'season_type', 'week', 'team', 'player_display_name', 'passing_yards', 'rushing_yards', 'receiving_yards']) {
    assert.ok(header.includes(column), `Player CSV is missing ${column}`);
  }
}
const schedulePath = path.join(root, 'data', 'schedule.csv');
if (fs.existsSync(schedulePath)) {
  const header = fs.readFileSync(schedulePath, 'utf8').split(/\r?\n/, 1)[0].split(',');
  for (const column of ['season', 'week', 'home_team', 'away_team', 'home_score', 'away_score']) {
    assert.ok(header.includes(column), `Schedule CSV is missing ${column}`);
  }
}
console.log('Commentary Box structural and dataset validation passed.');
