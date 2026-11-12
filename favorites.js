/* Shared browser-local favorites for the NFL Stats Tracker. */
(() => {
  'use strict';
  const STORAGE_KEY = 'awmNFLFavoritesV1';
  const TEAM_ALIASES = {LA:'LAR',LAR:'LAR',STL:'LAR',LAC:'LAC',SD:'LAC',LV:'LV',OAK:'LV',WAS:'WAS',WSH:'WAS',JAX:'JAX',JAC:'JAX'};
  const teamCode = value => {
    const code = String(value || '').trim().toUpperCase();
    return TEAM_ALIASES[code] || code;
  };
  const normalizedName = player => String(player?.name || '').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase().replace(/[^a-z0-9]/g,'');
  const samePlayer = (a,b) => a?.id && b?.id ? String(a.id)===String(b.id) : normalizedName(a)===normalizedName(b);
  const read = () => {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return {
        players: Array.isArray(value.players) ? value.players.filter(p => p && p.name).map(p => ({id:String(p.id || ''),name:String(p.name)})) : [],
        teams: Array.isArray(value.teams) ? [...new Set(value.teams.map(teamCode).filter(Boolean))] : []
      };
    } catch { return {players:[],teams:[]}; }
  };
  const notify = () => window.dispatchEvent(new CustomEvent('nfl-favorites-change',{detail:read()}));
  const write = value => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(value)); notify(); return true; }
    catch { return false; }
  };
  const api = {
    key: STORAGE_KEY,
    read,
    teamCode,
    isPlayer(player) { return !!normalizedName(player) && read().players.some(p => samePlayer(p,player)); },
    togglePlayer(player) {
      if (!player?.name) return false;
      const value=read(),index=value.players.findIndex(p => samePlayer(p,player));
      if (index>=0) value.players.splice(index,1); else value.players.push({id:String(player.id||''),name:String(player.name)});
      return write(value);
    },
    isTeam(team) { return read().teams.includes(teamCode(team)); },
    toggleTeam(team) {
      const value=read(),code=teamCode(team),index=value.teams.indexOf(code);
      if (!code) return false;
      if (index>=0) value.teams.splice(index,1); else value.teams.push(code);
      return write(value);
    },
    removePlayer(player) { const value=read(); return write({...value,players:value.players.filter(p=>!samePlayer(p,player))}); },
    removeTeam(team) { const code=teamCode(team),value=read(); return write({...value,teams:value.teams.filter(t=>t!==code)}); }
  };
  window.NFLFavorites=api;
})();
