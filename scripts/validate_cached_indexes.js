'use strict';
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('tracker.html','utf8');
const match=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].find(x=>x[1].includes('function recordAggregateValue')&&x[1].includes('function metricValue'));
if(!match)throw new Error('Could not extract metric engine.');
const source=match[1].replace(/\ninit\(\);\s*$/,'\n');
const sandbox=vm.createContext({
 console:{info(){},log(){},warn(){},error(){}},
 document:{getElementById(){return{}},querySelectorAll(){return[]}},
 window:{},localStorage:{getItem(){return null},setItem(){}}
});
vm.runInNewContext(source+'\nglobalThis.__metrics=Object.keys(metrics);',sandbox,{timeout:20000});
const records=JSON.parse(fs.readFileSync('data/records-index.json','utf8'));
const players=JSON.parse(fs.readFileSync('data/player-index.json','utf8'));
const expected=sandbox.__metrics.slice().sort();
const actual=(players.metrics||[]).slice().sort();
if(records.algorithm_version!==4||players.algorithm_version!==4)throw new Error('Cached indexes use an older record algorithm.');
if(records.version!==1||players.version!==1)throw new Error('Cached index schema version mismatch.');
if((records.loaded_years||[]).length!==27||(players.loaded_years||[]).length!==27)throw new Error('Cached indexes do not cover all 27 seasons.');
if(expected.length!==actual.length||expected.some((x,i)=>x!==actual[i]))throw new Error('Cached Player Profile metric catalogue does not match tracker.html.');
if(!Array.isArray(players.players)||!players.players.length||!records.index?.weekly||!records.index?.season||!records.index?.career)throw new Error('Cached index payload is incomplete.');
for(const mode of ['weekly','season','career'])for(const phase of ['ALL','REG','POST'])for(const metric of expected)if(!Array.isArray(records.index[mode]?.[phase]?.[metric]))throw new Error('Records index is missing '+mode+'/'+phase+'/'+metric);
console.log('Cached Records and Player Profile indexes are valid and compatible.');
