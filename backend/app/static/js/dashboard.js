/* Dashboard: meaningful posture metrics and first-run guidance. */
(function () {
  'use strict';
  const { api, esc, badgeFor, fmtTime, t } = window.Aegis;
  const statCards = [
    { key: 'scans', label: () => t('dashboard.scans', 'Stored scans') },
    { key: 'threats', label: () => t('dashboard.threats', 'Threats detected') },
    { key: 'avg_score', label: () => t('dashboard.average_score', 'Average trust score') },
    { key: 'needs_attention', label: () => t('dashboard.needs_attention', 'Needs attention') },
  ];
  const scanTypeLabel = (type) => t(`dashboard.scan_type_${type}`, type);

  function fillStats(stats) {
    const grid = document.getElementById('stats-grid');
    if (!grid) return;
    grid.innerHTML = statCards.map((card) => {
      const value = stats[card.key] ?? '—';
      const note = card.key === 'threats'
        ? `<span class="rounded-full px-2 py-0.5 text-xs font-semibold text-white ${value > 0 ? 'bg-red-500' : 'bg-emerald-500'}">${value > 0 ? 'review findings' : 'none detected'}</span>`
        : card.key === 'needs_attention' && value > 0
          ? '<span class="text-xs text-amber-600 dark:text-amber-400">Review suspicious or threat scans</span>'
          : '';
      return `<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"><p class="mb-1 text-xs font-medium uppercase text-slate-500">${card.label()}</p><p class="font-mono text-2xl font-bold">${esc(value)}</p>${note}</div>`;
    }).join('');
  }

  function scanScore(score) {
    if (score === null || score === undefined || score === '') return '—';
    const value = Number(score);
    return Number.isFinite(value) ? `${value.toFixed(1)}/100` : '—';
  }

  function renderScans(scans) {
    const box = document.getElementById('recent-scans');
    if (!box) return;
    if (!scans.length) {
      box.innerHTML = '<div class="rounded-xl border border-dashed border-slate-300 p-5 text-center dark:border-slate-700"><p class="font-medium">No stored scans yet</p><p class="mt-1 text-sm text-slate-500">Run a scan and choose to retain it when you need a history or report.</p><a class="mt-3 inline-flex text-sm font-semibold text-aegis-600 hover:underline dark:text-aegis-400" href="/scan">Start a scan →</a></div>';
      return;
    }
    box.innerHTML = scans.slice(0, 5).map((scan) => `<a href="/report/${scan.id}" class="scan-card flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3 transition hover:border-aegis-500/50 dark:border-slate-800 dark:bg-slate-900/50"><div class="min-w-0 flex-1"><p class="scan-card-target truncate text-sm font-medium" dir="auto"><bdi>${esc(scan.target)}</bdi></p><div class="scan-card-meta mt-1 text-xs text-slate-500"><span class="scan-card-type">${esc(scanTypeLabel(scan.scan_type))}</span><span aria-hidden="true">·</span><time class="scan-card-time" dir="ltr">${esc(fmtTime(scan.created_at))}</time></div></div><div class="scan-card-outcome shrink-0" dir="ltr"><data class="scan-card-score font-mono text-sm" value="${scan.trust_score ?? ''}">${scanScore(scan.trust_score)}</data>${badgeFor(scan.verdict)}</div></a>`).join('');
  }

  function renderThreats(threats) {
    const box = document.getElementById('recent-threats');
    if (!box) return;
    box.innerHTML = threats.length ? threats.slice(0, 5).map((threat) => `<div class="flex items-center justify-between gap-2 py-1.5"><span class="truncate text-slate-600 dark:text-slate-300">${esc(threat.domain || threat.target || 'Unknown')}</span><span class="shrink-0 text-xs text-slate-400">${esc(threat.vector || '')}</span></div>`).join('') : '<p class="text-sm text-slate-500">No stored scans need attention.</p>';
  }

  function setFirstRun(active) {
    document.getElementById('first-run')?.classList.toggle('hidden', !active);
    ['activity-card', 'score-card'].forEach((id) => document.getElementById(id)?.classList.toggle('hidden', active));
  }

  function drawCharts(scans) {
    if (!window.Chart || !scans.length) return;
    const counts = {};
    const scores = {};
    scans.forEach((scan) => { const date = (scan.created_at || '').slice(0, 10); counts[date] = (counts[date] || 0) + 1; scores[date] = scan.trust_score; });
    const days = Array.from({ length: 14 }, (_, index) => { const date = new Date(); date.setDate(date.getDate() - (13 - index)); return date.toISOString().slice(0, 10); });
    const labels = days.map((date) => date.slice(5));
    const common = { animation: false, plugins: { legend: { labels: { boxWidth: 10 } } } };
    const activity = document.getElementById('activity-canvas');
    if (activity) new Chart(activity, { type: 'line', data: { labels, datasets: [{ label: t('dashboard.scans', 'Scans'), data: days.map((date) => counts[date] || 0), borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,.15)', fill: true, tension: 0.3, pointRadius: 2 }] }, options: { ...common, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } } });
    const score = document.getElementById('score-canvas');
    if (score) new Chart(score, { type: 'line', data: { labels, datasets: [{ label: t('scan.trust_score', 'Trust'), data: days.map((date) => scores[date] ?? null), borderColor: '#10b981', pointRadius: 3, tension: 0.3, spanGaps: true }] }, options: { ...common, scales: { y: { min: 0, max: 100 } } } });
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try {
      const [stats, scanResult] = await Promise.all([api('GET', '/api/v1/analytics/summary'), api('GET', '/api/v1/scans?page=1&page_size=10')]);
      const scans = scanResult.items || [];
      fillStats(stats); renderScans(scans); renderThreats(stats.recent_threats || []); setFirstRun(scans.length === 0); drawCharts(scans);
    } catch (error) { window.Aegis.toast(`Failed to load dashboard: ${error.message}`, 'error'); }
  });
})();
