'use strict';

const fs = require('node:fs');
const path = require('node:path');

const site = path.resolve('site');
const data = path.join(site, 'data');
const years = Array.from({ length: 27 }, (_, i) => 2000 + i);
const checks = [];
const datasets = [];
const missing = [];
let filesChecked = 0;
let totalBytes = 0;

function addCheck(name, ok, detail) {
  checks.push({ name, status: ok ? 'passed' : 'failed', detail });
}

function inspectGroup(name, files, seasonLabel) {
  let bytes = 0;
  const absent = [];
  for (const file of files) {
    filesChecked++;
    const full = path.join(data, file);
    try {
      const stat = fs.statSync(full);
      if (!stat.isFile() || stat.size <= 0) throw new Error('empty or not a file');
      bytes += stat.size;
    } catch {
      absent.push(file);
      missing.push(file);
    }
  }
  totalBytes += bytes;
  const ok = absent.length === 0;
  datasets.push({
    name,
    seasons: seasonLabel || '—',
    files: files.length - absent.length,
    expected_files: files.length,
    bytes,
    status: ok ? 'passed' : 'failed'
  });
  addCheck(name, ok, ok
    ? files.length + ' non-empty files found (' + (seasonLabel || 'supporting files') + ').'
    : absent.length + ' missing or empty: ' + absent.slice(0, 5).join(', ') + (absent.length > 5 ? '…' : ''));
  return ok;
}

const yearFiles = suffix => years.map(year => 'stats_' + suffix + '_' + year + '.csv');
const playerFiles = years.map(year => 'stats_player_week_' + year + '.csv');
const teamFiles = years.map(year => 'stats_team_week_' + year + '.csv');
const advancedFiles = years.map(year => 'advanced_team_week_' + year + '.csv');
const pbpFiles = years.map(year => 'play_by_play_' + year + '.csv.gz');

inspectGroup('Weekly player statistics', playerFiles, '2000–2026');
inspectGroup('Weekly team statistics', teamFiles, '2000–2026');
inspectGroup('Advanced team statistics', advancedFiles, '2000–2026');
inspectGroup('Compressed play-by-play', pbpFiles, '2000–2026');

function readJson(file) {
  filesChecked++;
  const full = path.join(data, file);
  try {
    const stat = fs.statSync(full);
    if (!stat.size) throw new Error('empty file');
    totalBytes += stat.size;
    return JSON.parse(fs.readFileSync(full, 'utf8'));
  } catch (error) {
    missing.push(file);
    addCheck(file, false, 'Could not read valid JSON: ' + error.message);
    return null;
  }
}

const schedulePath = path.join(data, 'schedule.csv');
filesChecked++;
let scheduleOk = false;
try {
  const stat = fs.statSync(schedulePath);
  const header = fs.readFileSync(schedulePath, 'utf8').split(/\r?\n/, 1)[0].split(',').map(x => x.replace(/^"|"$/g, '').trim().toLowerCase());
  scheduleOk = stat.size > 0 && header.includes('season') && header.includes('week');
  totalBytes += stat.size;
} catch {
  missing.push('schedule.csv');
}
datasets.push({ name: 'NFL schedule and scores', seasons: 'Historical + published', files: scheduleOk ? 1 : 0, expected_files: 1, bytes: scheduleOk ? fs.statSync(schedulePath).size : 0, status: scheduleOk ? 'passed' : 'failed' });
addCheck('NFL schedule and scores', scheduleOk, scheduleOk ? 'Schedule file is present and includes season/week fields.' : 'Schedule file missing, empty or missing required columns.');

const records = readJson('records-index.json');
const recordsOk = !!records && records.version === 1 && Array.isArray(records.loaded_years) && records.loaded_years.length === years.length && !!records.index;
datasets.push({ name: 'Historical Records index', seasons: records ? String(records.loaded_years?.length || 0) + '/27' : '—', files: recordsOk ? 1 : 0, expected_files: 1, bytes: records ? fs.statSync(path.join(data, 'records-index.json')).size : 0, status: recordsOk ? 'passed' : 'failed' });
addCheck('Historical Records index', recordsOk, recordsOk ? 'Versioned index covers all 27 expected seasons.' : 'Records index is invalid or does not cover all expected seasons.');

const players = readJson('player-index.json');
const playerCount = Array.isArray(players?.players) ? players.players.length : 0;
const playerSeasons = (players?.players || []).reduce((total, player) => total + (Array.isArray(player.seasons) ? player.seasons.length : 0), 0);
const playersOk = !!players && players.version === 1 && playerCount > 0 && players.loaded_years?.length === years.length && playerSeasons > 0;
datasets.push({ name: 'Searchable player profiles', seasons: players ? String(players.loaded_years?.length || 0) + '/27' : '—', files: playersOk ? 1 : 0, expected_files: 1, bytes: players ? fs.statSync(path.join(data, 'player-index.json')).size : 0, status: playersOk ? 'passed' : 'failed' });
addCheck('Searchable player profiles', playersOk, playersOk ? playerCount.toLocaleString('en-US') + ' players and ' + playerSeasons.toLocaleString('en-US') + ' player-seasons indexed.' : 'Player index is invalid, empty or missing seasons.');

const allPassed = checks.every(check => check.status === 'passed') && missing.length === 0;
const manifest = {
  version: 1,
  generated_at: new Date().toISOString(),
  status: allPassed ? 'healthy' : 'degraded',
  seasons_expected: years,
  files_checked: filesChecked,
  total_bytes: totalBytes,
  players_indexed: playerCount,
  player_seasons: playerSeasons,
  records_loaded_seasons: records?.loaded_years?.length || 0,
  missing_files: missing,
  checks,
  datasets
};
fs.writeFileSync(path.join(data, 'site-manifest.json'), JSON.stringify(manifest), 'utf8');
console.log('Published data manifest: ' + manifest.status + '; checked ' + filesChecked + ' files; ' + playerCount + ' players; ' + playerSeasons + ' player-seasons; ' + totalBytes + ' bytes.');
if (!allPassed) {
  console.error('Missing or failed data checks:', JSON.stringify(checks.filter(check => check.status !== 'passed')));
  process.exitCode = 1;
}
