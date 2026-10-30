'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = process.cwd();
const dataDir = path.join(root, 'data');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const match = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)]
  .find(item => item[1].includes('function recordAggregateValue') &&
                item[1].includes('function metricValue'));

if (!match) {
  throw new Error('Could not extract the Records calculation code from index.html.');
}

// Reuse the dashboard's tested calculations so the fast index and the browser
// share the same metric definitions and aggregation rules.
const source = match[1].replace(/\ninit\(\);\s*$/, '\n') +
  '\nglobalThis.__buildRecordsIndex = buildRecordsIndex;\n';

const documentStub = {
  getElementById() {
    return { textContent: '', innerHTML: '', classList: { add() {}, remove() {}, toggle() {} } };
  },
  querySelectorAll() { return []; }
};

async function localDataFetch(url) {
  const fileMatch = String(url).match(/stats_player_week_(\d{4})\.csv/);
  if (!fileMatch) return { ok: false, status: 404, async text() { return ''; } };

  try {
    const csv = await fs.promises.readFile(
      path.join(dataDir, 'stats_player_week_' + fileMatch[1] + '.csv'),
      'utf8'
    );
    return { ok: true, status: 200, async text() { return csv; } };
  } catch (error) {
    return { ok: false, status: 404, async text() { return ''; } };
  }
}

const sandbox = vm.createContext({
  console: { info() {}, log() {}, warn() {}, error() {} },
  document: documentStub,
  window: {},
  localStorage: { getItem() { return null; }, setItem() {} },
  fetch: localDataFetch,
  requestAnimationFrame(callback) { setImmediate(callback); },
  gc: typeof global.gc === 'function' ? global.gc : undefined
});

vm.runInNewContext(source, sandbox, { timeout: 20000 });

(async () => {
  const result = await sandbox.__buildRecordsIndex();
  if (!result || !result.index || !result.loaded) {
    throw new Error('Records index build returned no usable records.');
  }

  // The dashboard offers a maximum of 50 results, so ship only those while
  // retaining the same ordering and calculation semantics as the full index.
  let retainedEntries = 0;
  for (const mode of Object.values(result.index)) {
    for (const phase of Object.values(mode)) {
      for (const records of Object.values(phase)) {
        records.length = Math.min(records.length, 50);
        retainedEntries += records.length;
      }
    }
  }

  const output = {
    version: 1,
    generated_at: new Date().toISOString(),
    loaded: result.loaded,
    loaded_years: result.loadedYears || [],
    skipped: result.skipped || [],
    result_limit: 50,
    index: result.index
  };

  fs.mkdirSync(dataDir, { recursive: true });
  const outputPath = path.join(dataDir, 'records-index.json');
  fs.writeFileSync(outputPath, JSON.stringify(output), 'utf8');

  const playerOutput = {
    version: 1,
    generated_at: output.generated_at,
    loaded: result.loaded,
    loaded_years: result.loadedYears || [],
    skipped: result.skipped || [],
    metrics: ['passing_yards','passing_tds','passing_interceptions','completion_pct','passer_rating','pass_yards_per_attempt','passing_epa','passing_cpoe','rushing_yards','carries','rushing_tds','rushing_yards_per_carry','receiving_yards','receptions','targets','receiving_tds','catch_rate','average_depth_of_target','receiving_epa','def_sacks','def_interceptions','def_tackles_solo','def_tackles_with_assist','def_tackles_for_loss','def_qb_hits','def_forced_fumbles','def_fumble_recoveries','def_tds','fg_made','fg_attempts','fg_pct','fg_long','punting_avg','kick_return_yards','kick_return_avg','punt_return_yards'],
    players: result.players || []
  };
  const playerPath = path.join(dataDir, 'player-index.json');
  fs.writeFileSync(playerPath, JSON.stringify(playerOutput), 'utf8');

  const bytes = fs.statSync(outputPath).size;
  const playerBytes = fs.statSync(playerPath).size;
  console.log(
    'Precomputed records index: ' + result.loaded + ' seasons, ' +
    retainedEntries.toLocaleString('en-US') + ' ranked entries, ' +
    bytes.toLocaleString('en-US') + ' bytes. Player profiles: ' +
    playerOutput.players.length.toLocaleString('en-US') + ' players, ' +
    playerBytes.toLocaleString('en-US') + ' bytes.'
  );
  if (!result.loadedYears || !result.loadedYears.length) {
    throw new Error('Records index contains no loaded season metadata.');
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
