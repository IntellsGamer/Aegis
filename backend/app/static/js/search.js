/* Search page */
(function () {
  'use strict';
  const shared = window.Aegis;
  if (!shared) {
    window.addEventListener('aegis:ready', () => window.location.reload(), { once: true });
    return;
  }
  const { api, esc, badgeFor, fmtTime } = shared;

  function render(data) {
    const box = document.getElementById('search-results');
    const { scans = [], threats = [], users = [] } = data;
    const total = (scans.length || 0) + (threats.length || 0) + (users.length || 0);
    if (!total) {
      box.innerHTML = '<p class="text-center text-slate-400 py-12">No results found.</p>';
      return;
    }
    let html = '';
    if (scans.length) {
      html += `<h2 class="font-semibold mb-2 mt-6">Scans (${scans.length})</h2>` +
        scans.map((s) => `
          <a href="/report/${s.id}" class="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 mb-2 hover:border-aegis-500/50">
            <span class="text-sm font-medium truncate">${esc(s.target)}</span>
            <span class="flex items-center gap-2 shrink-0 text-xs text-slate-400">${esc(s.scan_type)} · ${fmtTime(s.created_at)} ${badgeFor(s.verdict)}</span>
          </a>`).join('');
    }
    if (threats.length) {
      html += `<h2 class="font-semibold mb-2 mt-6">Threats (${threats.length})</h2>` +
        threats.map((t) => `
          <div class="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 mb-2">
            <span class="text-sm font-mono">${esc(t.domain || t.target || '')}</span>
            <span class="text-xs text-slate-400">${esc(t.vector || '')} · ${esc(t.country || '')}</span>
          </div>`).join('');
    }
    if (users.length) {
      html += `<h2 class="font-semibold mb-2 mt-6">Users (${users.length})</h2>` +
        users.map((u) => `
          <div class="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 mb-2">
            <span class="text-sm">${esc(u.username)} <span class="text-slate-400">· ${esc(u.email || '')}</span></span>
            <span class="text-xs text-slate-400">${u.is_admin ? 'admin' : 'user'}</span>
          </div>`).join('');
    }
    box.innerHTML = html;
  }

  window.Aegis.onPageLoad('search', () => {
    const form = document.getElementById('search-form');
    const input = document.getElementById('search-input');
    const scope = document.getElementById('search-scope');

    const run = async () => {
      const q = input.value.trim();
      if (!q) return;
      const params = new URLSearchParams({ q });
      if (scope.value !== 'all') params.set('scope', scope.value);
      try {
        const data = await api('GET', '/api/v1/search?' + params.toString());
        render(data);
      } catch (e) {
        document.getElementById('search-results').innerHTML = `<p class="text-center text-red-500 py-8">${esc(e.message)}</p>`;
      }
    };

    form.addEventListener('submit', (e) => { e.preventDefault(); run(); });

    if (window.__SEARCH_QUERY__) {
      input.value = window.__SEARCH_QUERY__;
      run();
    }
  });
})();
