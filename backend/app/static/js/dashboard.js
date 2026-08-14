/* Dashboard */
(function () {
  'use strict';
  const { api, esc, badgeFor, fmtTime } = window.Aegis;

  const statCards = [
    { key: 'scans', label: 'Total Scans' },
    { key: 'threats', label: 'Threats Detected' },
    { key: 'avg_score', label: 'Avg Trust Score' },
    { key: 'saved', label: 'Savings Estimate' },
  ];

  function fillStats(stats) {
    const grid = document.getElementById('stats-grid');
    if (!grid) return;
    const badges = {
      threats: (v) => `<span class="px-2 py-0.5 rounded-full text-xs font-semibold text-white ${v > 0 ? 'bg-red-500' : 'bg-emerald-500'}">${v > 0 ? '⚠ active' : 'clear'}</span>`,
    };
    grid.innerHTML = statCards.map((s) => `
      <div class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <p class="text-xs text-slate-500 uppercase font-medium mb-1">${s.label}</p>
        <p class="text-2xl font-bold font-mono">${esc(stats[s.key] ?? '—')}</p>
        ${badges[s.key] ? badges[s.key](stats[s.key]) : ''}
      </div>`).join('');
  }

  function renderScans(scans) {
    const box = document.getElementById('recent-scans');
    if (!box) return;
    if (!scans.length) {
      box.innerHTML = '<p class="text-sm text-slate-400 py-6 text-center">No scans yet. Run your first scan!</p>';
      return;
    }
    box.innerHTML = scans.slice(0, 5).map((s) => `
      <a href="/report/${s.id}" class="flex items-center justify-between gap-3 p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:border-aegis-500/50 transition bg-slate-50 dark:bg-slate-900/50">
        <div class="min-w-0">
          <p class="text-sm font-medium truncate">${esc(s.target)}</p>
          <p class="text-xs text-slate-500">${esc(s.scan_type)} · ${fmtTime(s.created_at)}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="font-mono text-sm">${s.trust_score ?? '—'}</span>
          ${badgeFor(s.verdict)}
        </div>
      </a>`).join('');
  }

  function renderThreats(threats) {
    const box = document.getElementById('recent-threats');
    if (!box) return;
    if (!threats.length) {
      box.innerHTML = '<p class="text-sm text-slate-400">No threats reported recently.</p>';
      return;
    }
    box.innerHTML = threats.slice(0, 5).map((t) => `
      <div class="flex items-center justify-between gap-2 py-1.5">
        <span class="truncate text-slate-600 dark:text-slate-300">${esc(t.domain || t.target || 'Unknown')}</span>
        <span class="text-xs text-slate-400 shrink-0">${esc(t.vector || '')}</span>
      </div>`).join('');
  }

  async function drawCharts(scans) {
    if (!window.Chart) return;
    const counts = {};
    const scores = {};
    (scans || []).forEach((s) => {
      const d = (s.created_at || '').slice(0, 10);
      counts[d] = (counts[d] || 0) + 1;
      scores[d] = s.trust_score;
    });
    const days = Array.from({ length: 14 }, (_, i) => {
      const dt = new Date(); dt.setDate(dt.getDate() - (13 - i));
      return dt.toISOString().slice(0, 10);
    });
    const labels = days.map((d) => d.slice(5));
    const data = days.map((d) => counts[d] || 0);
    const sdata = days.map((d) => scores[d] ?? null);

    const common = { animation: false };
    const act = document.getElementById('activity-canvas');
    if (act) new Chart(act, {
      type: 'line', data: { labels, datasets: [{ label: 'Scans', data, borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,.15)', fill: true, tension: 0.3, pointRadius: 2 }] },
      options: { ...common, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });
    const sc = document.getElementById('score-canvas');
    if (sc) new Chart(sc, {
      type: 'line', data: { labels, datasets: [{ label: 'Trust', data: sdata, borderColor: '#10b981', pointRadius: 3, tension: 0.3 }] },
      options: { ...common, scales: { y: { min: 0, max: 100 } } },
    });
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try {
      const [stats, scans] = await Promise.all([
        api('GET', '/api/v1/analytics/summary'),
        api('GET', '/api/v1/scans?page=1&page_size=10'),
      ]);
      fillStats(stats);
      renderScans(scans.items || []);
      drawCharts(scans.items || []);
      renderThreats(stats.recent_threats || []);
    } catch (err) {
      window.Aegis.toast('Failed to load dashboard: ' + err.message, 'error');
    }
  });
})();
