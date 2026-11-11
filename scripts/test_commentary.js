const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'commentary.html'), 'utf8');
const home = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

for (const id of [
  'pregameGame', 'postgameGame', 'factSeason', 'factPhase', 'factMetric',
  'factWeek', 'factTeam', 'factLimit', 'commentGame', 'commentTone',
  'contentTopic', 'contentEvidence', 'loadStatus', 'pregameOutput',
  'postgameOutput', 'factsOutput', 'commentaryOutput', 'contentOutput'
]) assert.match(page, new RegExp(`id=["']${id}["']`), `Commentary page is missing #${id}`);

for (const feature of ['buildPregame', 'buildPostgame', 'factGen', 'draft', 'buildContent']) {
  assert.match(page, new RegExp(`function ${feature}\\(`), `Missing ${feature} generator`);
}
assert.match(page, /schedule\.csv\?v=commentary-20261111/, 'Schedule request should use cache busting');
assert.match(page, /stats_player_week_\$\{current\}\.csv\?v=commentary-20261111/, 'Player stats request should use cache busting');
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
