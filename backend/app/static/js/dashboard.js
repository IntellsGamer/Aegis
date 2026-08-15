/* Dashboard: meaningful posture metrics and first-run guidance. */
(function () {
  'use strict';
  const { api, esc, badgeFor, fmtTime, t } = window.Aegis;
  const statCards = [
    { key: 'scans', label: () => t('dashboard.scans', 'Checks saved'), index: '01' },
    { key: 'threats', label: () => t('dashboard.threats', 'High-risk findings'), index: '02' },
    { key: 'avg_score', label: () => t('dashboard.average_score', 'Average trust score'), index: '03' },
    { key: 'needs_attention', label: () => t('dashboard.needs_attention', 'Needs review'), index: '04' },
  ];
  const scanTypeLabel = (type) => t(`dashboard.scan_type_${type}`, type);

  function fillStats(stats) {
    const grid = document.getElementById('stats-grid');
    if (!grid) return;
    grid.innerHTML = statCards.map((card) => {
      const value = stats[card.key] ?? '—';
      const note = card.key === 'threats'
        ? `<span class="metric-note ${value > 0 ? 'metric-note-risk' : 'metric-note-safe'}">${value > 0 ? t('dashboard.review_findings', 'Review findings') : t('dashboard.none_detected', 'None detected')}</span>`
        : card.key === 'needs_attention' && value > 0
          ? `<span class="metric-note metric-note-review">${t('dashboard.review_risk_scans', 'Review suspicious or high-risk checks')}</span>`
          : `<span class="metric-note">${t('dashboard.current_snapshot', 'Current snapshot')}</span>`;
      return `<div class="metric-card metric-${card.key}"><div class="metric-card-top"><p>${card.label()}</p><span>${card.index}</span></div><p class="metric-value">${esc(value)}</p>${note}</div>`;
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
    box.innerHTML = scans.slice(0, 5).map((scan) => `<a href="/report/${scan.id}" class="dashboard-scan-row scan-card"><span class="scan-risk-marker scan-risk-${esc(scan.verdict || 'unverified')}" aria-hidden="true"></span><div class="min-w-0 flex-1"><p class="scan-card-target" dir="auto"><bdi>${esc(scan.target)}</bdi></p><div class="scan-card-meta"><span class="scan-card-type">${esc(scanTypeLabel(scan.scan_type))}</span><span aria-hidden="true">·</span><time class="scan-card-time" dir="ltr">${esc(fmtTime(scan.created_at))}</time></div></div><div class="scan-card-outcome" dir="ltr"><data class="scan-card-score" value="${scan.trust_score ?? ''}">${scanScore(scan.trust_score)}</data>${badgeFor(scan.verdict)}</div></a>`).join('');
  }

  function renderThreats(threats) {
    const box = document.getElementById('recent-threats');
    if (!box) return;
    box.innerHTML = threats.length ? threats.slice(0, 5).map((threat) => `<div class="dashboard-threat-row"><span class="threat-dot" aria-hidden="true"></span><span class="truncate" dir="auto"><bdi>${esc(threat.domain || threat.target || t('dashboard.unknown', 'Unknown'))}</bdi></span><span class="threat-vector">${esc(threat.vector || '')}</span></div>`).join('') : `<p class="dashboard-empty-copy">${t('dashboard.no_attention', 'No saved checks need attention right now.')}</p>`;
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
    } catch (error) { window.Aegis.toast(t('dashboard.load_failed', 'Could not load dashboard: ') + error.message, 'error'); }
  });
})();
