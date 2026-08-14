/* Assessment casefile: derives only from the authorized persisted scan record. */
(function () {
  'use strict';
  const { api, esc, badgeFor, toast } = window.Aegis;
  const scanId = window.__REPORT_SCAN_ID__ || window.location.pathname.split('/').pop();
  let casefile = null;

  const stateCopy = {
    complete: ['Assessment completed', 'AEGIS completed the available assessment path. The result is evidence-led, not a guarantee.'],
    limited: ['Limited assessment', 'Remote destination checks were not completed. Local evidence is shown, but the verdict is intentionally unverified.'],
    blocked: ['Safety boundary applied', 'AEGIS refused to probe this target because it crosses a network-safety boundary.'],
  };

  function impactClass(impact) { return impact < 0 ? 'text-red-600 dark:text-red-300' : impact > 0 ? 'text-emerald-600 dark:text-emerald-300' : 'text-slate-500'; }
  function severityClass(value) {
    return ({ critical: 'bg-red-600 text-white', high: 'bg-red-500 text-white', medium: 'bg-amber-500 text-white', low: 'bg-slate-500 text-white', info: 'bg-aegis-600 text-white', safe: 'bg-emerald-600 text-white' })[value] || 'bg-slate-500 text-white';
  }
  function getCompleted() {
    try { return new Set(JSON.parse(localStorage.getItem(`aegis-casefile-${scanId}-steps`) || '[]')); } catch (_) { return new Set(); }
  }
  function setCompleted(completed) {
    try { localStorage.setItem(`aegis-casefile-${scanId}-steps`, JSON.stringify([...completed])); } catch (_) { /* local enhancement only */ }
  }
  function statePanel(data) {
    const state = data.classification.assessment_state || 'complete';
    const [title, detail] = stateCopy[state] || stateCopy.complete;
    const style = state === 'blocked' ? 'border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100' : state === 'limited' ? 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100' : 'border-aegis-200 bg-aegis-50 text-slate-900 dark:border-aegis-900 dark:bg-aegis-950/30 dark:text-slate-100';
    return `<section class="rounded-2xl border p-5 ${style}"><div class="flex flex-wrap items-start justify-between gap-4"><div><p class="text-sm font-semibold">${esc(title)}</p><p class="mt-1 max-w-3xl text-sm leading-6 opacity-90">${esc(detail)}</p></div>${badgeFor(data.classification.verdict)}</div></section>`;
  }
  function renderEvidence(items) {
    if (!items.length) return '<p class="text-sm text-slate-500">No granular evidence was retained for this assessment.</p>';
    return items.map((item) => `<article class="border-b border-slate-100 py-4 last:border-0 dark:border-slate-800"><div class="flex flex-wrap items-start justify-between gap-3"><div class="min-w-0 flex-1"><div class="flex flex-wrap items-center gap-2"><p class="font-medium">${esc(item.title || item.code)}</p><span class="rounded px-2 py-0.5 text-[11px] font-semibold ${severityClass(item.severity)}">${esc(item.severity || 'info')}</span></div><p class="mt-1 text-sm text-slate-600 dark:text-slate-300">${esc(item.description || 'Recorded scanner observation.')}</p>${item.evidence ? `<p class="mt-2 break-all rounded bg-slate-50 px-2 py-1 font-mono text-xs text-slate-600 dark:bg-slate-950 dark:text-slate-300">${esc(item.evidence)}</p>` : ''}</div><div class="min-w-28 text-right text-xs text-slate-500"><p>Reliability ${item.confidence !== null && item.confidence !== undefined ? `${Math.round(Number(item.confidence) * 100)}%` : '—'}</p><p class="mt-1 ${impactClass(Number(item.engine_impact || 0))}">${Number(item.engine_impact || 0) === 0 ? 'coverage note' : `${Number(item.engine_impact).toFixed(1)} ${Number(item.engine_impact) < 0 ? 'risk' : 'protective'}`}</p><p class="mt-1">${esc(item.source || 'scanner observation')}</p></div></div></article>`).join('');
  }
  function renderFamilies(items) {
    return items.map((item) => `<div class="rounded-xl border border-slate-200 p-4 dark:border-slate-800"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${esc(item.family)}</p><p class="mt-2 text-xl font-bold ${impactClass(Number(item.net_impact))}">${Number(item.net_impact) === 0 ? 'Neutral' : `${Number(item.net_impact).toFixed(1)}`}</p><p class="mt-1 text-xs text-slate-500">${item.signals} signal${item.signals === 1 ? '' : 's'} · net evidence contribution</p></div>`).join('') || '<p class="text-sm text-slate-500">No evidence families were recorded.</p>';
  }
  function renderPlaybook(items) {
    const completed = getCompleted();
    if (!items.length) return '<p class="text-sm text-slate-500">No additional action was recorded for this case.</p>';
    return `<div class="space-y-2">${items.map((item, index) => `<label class="flex cursor-pointer gap-3 rounded-xl border border-slate-200 p-3 transition hover:border-aegis-400 dark:border-slate-800"><input class="case-step mt-1 rounded accent-aegis-600" type="checkbox" data-step="${index}" ${completed.has(index) ? 'checked' : ''}><span><span class="block text-xs font-semibold uppercase tracking-wide text-aegis-700 dark:text-aegis-300">${esc(item.phase)} · ${esc(item.owner)}</span><span class="mt-1 block text-sm">${esc(item.action)}</span></span></label>`).join('')}</div><p class="mt-3 text-xs text-slate-500">Completion is stored only in this browser; it does not modify the casefile or report an outcome.</p>`;
  }
  function render(data) {
    casefile = data;
    const c = data.classification || {};
    const limited = c.assessment_state === 'limited';
    const score = limited ? '—' : `${c.trust_score ?? '—'}<span class="text-lg">/100</span>`;
    const confidence = c.evidence_confidence !== null && c.evidence_confidence !== undefined ? `${Math.round(Number(c.evidence_confidence) * 100)}%` : '—';
    const box = document.getElementById('report-content');
    box.innerHTML = `<div class="space-y-6">${statePanel(data)}
      <section class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:grid-cols-[1fr_auto]"><div><p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Case ${esc(data.case_id)}</p><p class="mt-3 break-all font-mono text-sm">${esc(data.target || '')}</p><p class="mt-2 text-sm text-slate-500">${esc(data.scan_type || 'content')} assessment · ${data.created_at ? esc(new Date(data.created_at).toLocaleString()) : 'time unavailable'}</p><p class="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">${esc(data.report_summary || '')}</p></div><div class="min-w-44 text-right"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${limited ? 'Coverage' : 'Trust score'}</p><p class="mt-2 font-mono text-5xl font-bold ${limited ? 'text-slate-500' : Number(c.trust_score) >= 70 ? 'text-emerald-500' : Number(c.trust_score) >= 40 ? 'text-amber-500' : 'text-red-500'}">${score}</p><p class="mt-2 text-xs text-slate-500">Evidence confidence ${confidence}</p></div></section>
      <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">${renderFamilies(data.evidence_families || [])}</section>
      <section class="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]"><div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><div class="flex items-center justify-between gap-3"><h2 class="text-lg font-semibold">Evidence chain</h2><span class="text-xs text-slate-500">${(data.evidence || []).length} recorded observations</span></div><div class="mt-3">${renderEvidence(data.evidence || [])}</div></div><div class="space-y-6"><section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">Response playbook</h2><p class="mt-1 text-sm text-slate-500">Prioritize containment before further interaction.</p><div class="mt-4">${renderPlaybook(data.response_playbook || [])}</div></section><section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">Scope & provenance</h2><dl class="mt-4 space-y-3 text-sm"><div><dt class="text-slate-500">Engine</dt><dd class="font-mono">${esc(c.engine || 'evidence-fusion-v2')}</dd></div><div><dt class="text-slate-500">Network acquisition</dt><dd>${esc(data.provenance?.network_acquisition || 'not applicable')}</dd></div><div><dt class="text-slate-500">External intelligence</dt><dd>${(data.provenance?.external_intelligence || []).length ? (data.provenance.external_intelligence || []).map(esc).join(', ') : 'No external feed match recorded'}</dd></div></dl><details class="mt-5 rounded-lg bg-slate-50 p-3 text-xs dark:bg-slate-950"><summary class="cursor-pointer font-semibold">Integrity fingerprint</summary><p class="mt-2 break-all font-mono text-slate-600 dark:text-slate-300">${esc(data.integrity?.fingerprint || '')}</p><p class="mt-2 text-slate-500">${esc(data.integrity?.scope || '')}</p></details></section></div></section>
      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">Assessment limitations</h2><ul class="mt-3 space-y-2">${(data.limitations || []).map((item) => `<li class="flex gap-2 text-sm text-slate-600 dark:text-slate-300"><span class="text-aegis-500">•</span><span>${esc(item)}</span></li>`).join('')}</ul></section>
    </div>`;
    document.querySelectorAll('.case-step').forEach((input) => input.addEventListener('change', () => { const completed = getCompleted(); const id = Number(input.dataset.step); input.checked ? completed.add(id) : completed.delete(id); setCompleted(completed); }));
  }
  function exportJson() {
    if (!casefile) return;
    const blob = new Blob([JSON.stringify(casefile, null, 2)], { type: 'application/json' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${casefile.case_id || 'aegis-casefile'}.json`; link.click(); URL.revokeObjectURL(link.href);
  }
  document.addEventListener('DOMContentLoaded', async () => {
    if (!scanId) return;
    try {
      const data = await api('GET', `/api/v1/scans/${scanId}/casefile`);
      render(data);
      document.getElementById('report-meta').textContent = `${data.scan_type || 'content'} assessment · ${data.case_id} · evidence-first record`;
    } catch (error) { document.getElementById('report-content').innerHTML = `<div class="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">${esc(error.message)}</div>`; }
    document.getElementById('casefile-json-btn')?.addEventListener('click', exportJson);
    document.getElementById('pdf-btn')?.addEventListener('click', () => { window.location.href = `/api/v1/scans/${scanId}/report.pdf`; });
    document.getElementById('share-btn')?.addEventListener('click', async () => { try { await navigator.clipboard.writeText(window.location.href); toast('Case link copied', 'success'); } catch (_) { toast('Could not copy link', 'error'); } });
  });
})();
