/* Click a table heading to sort that table; a second click reverses the order. */
(() => {
  const states = new WeakMap();
  let refreshQueued = false;

  const style = document.createElement('style');
  style.textContent = `
    table thead th[data-nfl-sortable="true"] { cursor: pointer; user-select: none; }
    table thead th[data-nfl-sortable="true"]:focus-visible { outline: 2px solid #55d6ae; outline-offset: -2px; }
    .nfl-sort-arrow { display: inline-block; min-width: 1.1em; margin-left: .35em; opacity: .72; font-size: .9em; }
    th[aria-sort="ascending"] .nfl-sort-arrow, th[aria-sort="descending"] .nfl-sort-arrow { opacity: 1; color: #55d6ae; }
  `;
  document.head.append(style);

  function cellValue(cell) {
    const text = (cell?.innerText || cell?.textContent || '').trim();
    if (!text || /^(—|–|-|n\/a)$/i.test(text)) return null;
    const cleaned = text.replace(/[,$%+\s]/g, '');
    if (/^-?\d+(\.\d+)?$/.test(cleaned)) return Number(cleaned);
    return text.toLocaleLowerCase();
  }

  function compare(a, b) {
    if (a === null && b !== null) return 1;
    if (b === null && a !== null) return -1;
    if (a === null && b === null) return 0;
    if (typeof a === 'number' && typeof b === 'number') return a - b;
    return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
  }

  function applySort(table, state) {
    const body = table.tBodies[0];
    if (!body || !state || state.column < 0) return;
    const current = [...body.rows];
    const rows = current.map((row, index) => ({ row, index, value: cellValue(row.cells[state.column]) }));
    rows.sort((a, b) => state.direction * compare(a.value, b.value) || a.index - b.index);
    if (rows.some((item, index) => item.row !== current[index])) {
      const fragment = document.createDocumentFragment();
      rows.forEach(item => fragment.append(item.row));
      body.append(fragment);
    }
  }

  function updateIndicators(table, headers, state) {
    headers.forEach((th, index) => {
      th.setAttribute('aria-sort', state?.column === index ? (state.direction === 1 ? 'ascending' : 'descending') : 'none');
      const arrow = th.querySelector('.nfl-sort-arrow');
      if (arrow) arrow.textContent = state?.column === index ? (state.direction === 1 ? '↑' : '↓') : '↕';
    });
  }

  function enhance(table) {
    if (table.hasAttribute('data-no-sort')) return;
    const headerRow = table.tHead?.rows?.[0];
    if (!headerRow || !table.tBodies.length) return;
    const headers = [...headerRow.cells];
    if (!headers.length) return;
    headers.forEach((th, index) => {
      th.dataset.nflSortable = 'true';
      th.tabIndex = 0;
      th.setAttribute('role', 'columnheader');
      th.setAttribute('aria-label', `${th.dataset.nflSortLabel || th.textContent.trim()}. Click to sort; click again to reverse.`);
      if (!th.querySelector('.nfl-sort-arrow')) {
        const arrow = document.createElement('span');
        arrow.className = 'nfl-sort-arrow';
        arrow.setAttribute('aria-hidden', 'true');
        arrow.textContent = '↕';
        th.append(arrow);
      }
      th.dataset.nflSortColumn = String(index);
    });
    const state = states.get(table) || null;
    updateIndicators(table, headers, state);
  }

  function chooseHeader(target) {
    const th = target.closest('th[data-nfl-sortable="true"]');
    if (!th) return;
    const table = th.closest('table');
    if (!table) return;
    const column = Number(th.dataset.nflSortColumn);
    const previous = states.get(table);
    const state = {
      column,
      direction: previous?.column === column ? -previous.direction : -1
    };
    states.set(table, state);
    applySort(table, state);
    updateIndicators(table, [...table.tHead.rows[0].cells], state);
  }

  document.addEventListener('click', event => chooseHeader(event.target));
  document.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches?.('th[data-nfl-sortable="true"]')) {
      event.preventDefault();
      chooseHeader(event.target);
    }
  });

  function refresh() {
    refreshQueued = false;
    document.querySelectorAll('table').forEach(table => {
      enhance(table);
      applySort(table, states.get(table));
    });
  }

  function queueRefresh() {
    if (refreshQueued) return;
    refreshQueued = true;
    requestAnimationFrame(refresh);
  }

  if (document.body) {
    new MutationObserver(queueRefresh).observe(document.body, { childList: true, subtree: true });
    refresh();
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      new MutationObserver(queueRefresh).observe(document.body, { childList: true, subtree: true });
      refresh();
    }, { once: true });
  }
})();
