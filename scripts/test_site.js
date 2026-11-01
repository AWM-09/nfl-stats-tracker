'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const site = path.resolve('site');
const expectedPages = [
  'index.html','tracker.html','player.html','health.html','advanced.html',
  'research.html','calendar.html','accuracy.html','news.html','playbook.html','rulebook.html','teams.html'
];

for (const page of expectedPages) {
  const full = path.join(site, page);
  assert.ok(fs.existsSync(full), 'Missing published page: ' + page);
  const html = fs.readFileSync(full, 'utf8');
  assert.ok(/<meta[^>]+name=["']viewport["'][^>]*>/i.test(html), page + ' is missing a viewport meta tag.');
  assert.ok(/@media\s*\(/i.test(html), page + ' is missing responsive CSS.');
  assert.ok(/<title>[^<]+<\/title>/i.test(html), page + ' is missing a document title.');

  const localReferences = [...html.matchAll(/\b(?:href|src)=["']\.\/([^"']+)["']/gi)];
  for (const match of localReferences) {
    const target = match[1].split(/[?#]/, 1)[0];
    if (!target || target.startsWith('#')) continue;
    const resolved = path.resolve(site, target);
    assert.ok(resolved.startsWith(site + path.sep), page + ' contains an unsafe local reference: ' + target);
    assert.ok(fs.existsSync(resolved), page + ' references a missing local asset: ' + target);
  }
}

const teamPage = fs.readFileSync(path.join(site, 'teams.html'), 'utf8');
for (const id of ['franchiseDossier','teamIdentity','dossierKpis','dossierTabs','dossierContent']) {
  assert.ok(teamPage.includes('id="'+id+'"'), 'Team Platform is missing ' + id);
}
const officialRecordsPath = path.join(site, 'data', 'official-records.json');
assert.ok(fs.existsSync(officialRecordsPath), 'Published official-records.json is missing.');
const officialRecords = JSON.parse(fs.readFileSync(officialRecordsPath, 'utf8'));
assert.equal(officialRecords.version, 1, 'Official records reference version is invalid.');
assert.ok(Array.isArray(officialRecords.records) && officialRecords.records.length >= 10,
  'Official records reference is empty or incomplete.');

const teamDataPath = path.join(site, 'data', 'team-platform.json');
assert.ok(fs.existsSync(teamDataPath), 'Published team-platform.json is missing.');
const teamData = JSON.parse(fs.readFileSync(teamDataPath, 'utf8'));
assert.equal(teamData.version, 1, 'Team Platform data version is invalid.');
assert.equal(Object.keys(teamData.teams || {}).length, 32, 'Team Platform must contain all 32 current franchises.');
assert.ok(Object.values(teamData.teams).every(team => Array.isArray(team.roster)), 'Every franchise must expose a roster array, even when the source feed is incomplete.');

const home = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
for (const target of ['tracker.html','player.html','teams.html','advanced.html','research.html','calendar.html','accuracy.html','news.html','playbook.html','rulebook.html','health.html']) {
  assert.ok(home.includes('./' + target), 'Homepage is missing a link to ' + target);
}

const tracker = fs.readFileSync(path.join(site, 'tracker.html'), 'utf8');
assert.ok(tracker.includes('./data/records-index.json?build='), 'Records must use the precomputed index.');
assert.ok(tracker.includes('data-view="records"'), 'Main tracker is missing its Records view.');

const player = fs.readFileSync(path.join(site, 'player.html'), 'utf8');
assert.ok(player.includes('./data/player-index.json'), 'Player profile page must use the generated profile index.');
assert.ok(player.includes('stats_player_week_'), 'Player profile page must support on-demand game logs.');
assert.ok(player.includes("searchParams.set('player'"), 'Player profiles must have shareable query URLs.');

const health = fs.readFileSync(path.join(site, 'health.html'), 'utf8');
assert.ok(health.includes('./data/site-manifest.json'), 'Health Centre must load the published data manifest.');

// Static interaction contracts catch accidentally removed controls or core
// functions on the tools that are not covered by the formula-specific suites.
const toolContracts = {
  'teams.html': {
    ids: ['season','phase','team','metric','rankBody','compare','profileBody','trendChart','teamGrid'],
    functions: ['loadSeason','loadHistoricalTrend','render','metricValue']
  },
  'advanced.html': {
    ids: ['overview','players','teams','situational','games','records','scenarios','content','playerPick','runScenario','fourthCalc'],
    functions: ['renderPlayer','renderCareer','renderTeams','renderSituational','renderGames','renderRecords','renderScenario','fourthDown','makeContent']
  },
  'calendar.html': {
    ids: ['liveGames','calendarPanel','predictorPanel','gameList','detailPanel','plays'],
    functions: ['renderCalendar','openGame','loadPbpForGame','runPrediction','renderFullStandings']
  },
  'accuracy.html': {
    ids: ['modelSummary','accuracy','brier','misses','rerun'],
    functions: ['backtest','load']
  },
  'news.html': {
    ids: ['panel-news','panel-transactions','panel-injuries','panel-scores','panel-standings'],
    functions: ['loadNews','loadTransactions','loadInjuries','loadScores','loadStandings']
  },
  'playbook.html': {
    ids: ['builder','book','learn','savePlay','bookList'],
    functions: ['drawPlay','savePlay','renderBook','startSurvivor']
  },
  'rulebook.html': {
    ids: ['search','category','directory','details','prev','next'],
    functions: ['renderDirectory','renderDetail']
  },
  'research.html': {
    ids: ['panel-games','panel-streaks','panel-quality','panel-franchise','panel-seasons','panel-search','panel-content','panel-downloads'],
    functions: ['runGame','runStreak','runQuality','runFranchise','runSeason','runSearch','renderPack']
  },
  'tracker.html': {
    ids: ['viewTabs','recordsPanel','comparePanel','teamComparePanel','factPanel','contentStudioPanel'],
    functions: ['loadData','renderPlayerCompare','renderTeamCompare','renderRecords','renderFactGenerator','buildContentPack']
  }
};
for (const [page, contract] of Object.entries(toolContracts)) {
  const html = fs.readFileSync(path.join(site, page), 'utf8');
  for (const id of contract.ids) {
    assert.ok(html.includes('id="' + id + '"'), page + ' is missing required control/panel: ' + id);
  }
  for (const fn of contract.functions) {
    assert.ok(html.includes('function ' + fn + '(') || html.includes('async function ' + fn + '('),
      page + ' is missing required interaction function: ' + fn);
  }
}

const manifestPath = path.join(site, 'data', 'site-manifest.json');
assert.ok(fs.existsSync(manifestPath), 'Published data manifest is missing.');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
assert.equal(manifest.status, 'healthy', 'Published data manifest is not healthy.');
assert.ok(manifest.files_checked >= 100, 'Manifest did not check all expected data files.');
assert.ok(manifest.players_indexed > 0, 'Manifest reports no searchable player profiles.');
assert.ok(manifest.player_seasons > 0, 'Manifest reports no player-seasons.');

const buildInfoPath = path.join(site, 'build-info.json');
assert.ok(fs.existsSync(buildInfoPath), 'Build metadata is missing.');
const build = JSON.parse(fs.readFileSync(buildInfoPath, 'utf8'));
assert.ok(build.commit, 'Build metadata is missing the source commit.');
assert.ok(build.workflow_run_id, 'Build metadata is missing the workflow run ID.');

console.log('Site integration checks passed: ' + expectedPages.length + ' pages, local links, responsive metadata, Team Platform, player profiles, Records index, health manifest and build metadata.');
