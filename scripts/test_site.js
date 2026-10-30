'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const site = path.resolve('site');
const expectedPages = [
  'index.html','tracker.html','player.html','health.html','advanced.html',
  'research.html','calendar.html','accuracy.html','news.html','playbook.html','rulebook.html'
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

const home = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
for (const target of ['tracker.html','player.html','advanced.html','research.html','calendar.html','accuracy.html','news.html','playbook.html','rulebook.html','health.html']) {
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

console.log('Site integration checks passed: ' + expectedPages.length + ' pages, local links, responsive metadata, player profiles, Records index, health manifest and build metadata.');
