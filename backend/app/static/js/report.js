/* Scan report page */
(function () {
    'use strict';
    const { api, esc, badgeFor } = window.Aegis;
    // Get scan ID from URL path instead of global variable
    const scanId = window.__REPORT_SCAN_ID__ || window.location.pathname.split('/').pop();

    function render(data) {
        const box = document.getElementById('report-content');
        const reasons = (data.reasons || []).map((r) => `
      <div class="flex items-start gap-3 py-2 border-b border-slate-100 dark:border-slate-800 last:border-0">
        <span class="mt-1 w-2 h-2 rounded-full shrink-0 ${r.impact >= 0 ? 'bg-emerald-500' : 'bg-red-500'}"></span>
        <div class="flex-1">
          <p class="text-sm font-medium">${esc(r.reason)}</p>
          <p class="text-xs text-slate-500 mt-0.5">impact ${r.impact > 0 ? '+' : ''}${r.impact}</p>
        </div>
      </div>`).join('');

        box.innerHTML = `
      <div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div class="min-w-0">
            <p class="text-sm text-slate-500 mb-1">Target</p>
            <p class="font-mono break-all">${esc(data.target || '')}</p>
          </div>
          <div class="text-center">
            <p class="text-sm text-slate-500 mb-1">Trust Score</p>
            <p class="font-mono text-5xl font-bold ${(data.trust_score || 0) >= 70 ? 'text-emerald-500' : (data.trust_score || 0) >= 40 ? 'text-amber-500' : 'text-red-500'}">${data.trust_score ?? '—'}<span class="text-lg">/100</span></p>
          </div>
          ${badgeFor(data.verdict)}
        </div>
        <div class="h-3 rounded-full bg-slate-200 dark:bg-slate-800 mb-6">
          <div class="h-3 rounded-full ${(data.trust_score || 0) >= 70 ? 'bg-emerald-500' : (data.trust_score || 0) >= 40 ? 'bg-amber-500' : 'bg-red-500'}" style="width: ${data.trust_score || 0}%"></div>
        </div>
        <div class="grid lg:grid-cols-2 gap-6">
          <div>
            <h3 class="font-semibold mb-3">Reasons</h3>
            ${reasons || '<p class="text-sm text-slate-400">No reasons.</p>'}
          </div>
          <div>
            <h3 class="font-semibold mb-3">Recommendations</h3>
            <ul class="space-y-2">
              ${(data.recommendations || []).map((r) => `<li class="flex items-start gap-2 text-sm"><span class="text-aegis-500 mt-0.5">→</span> ${esc(r)}</li>`).join('') || '<p class="text-sm text-slate-400">No recommendations.</p>'}
            </ul>
            <h3 class="font-semibold mt-6 mb-2">Highlights</h3>
            <div class="flex flex-wrap gap-2">${(data.highlights || []).map((h) => `<span class="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-xs">${esc(h)}</span>`).join('') || '—'}</div>
          </div>
        </div>
      </div>`;
    }

    document.addEventListener('DOMContentLoaded', async () => {
        if (!scanId) { document.getElementById('report-content').innerHTML = '<p class="text-center text-slate-400 py-16">No scan specified.</p>'; return; }
        try {
            const data = await api('GET', `/api/v1/scans/${scanId}`);
            render(data);
            document.getElementById('report-meta').textContent = `${data.scan_type || 'scan'} · ${new Date(data.created_at).toLocaleString()}`;
        } catch (err) {
            document.getElementById('report-content').innerHTML = `<div class="p-6 rounded-2xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300">${esc(err.message)}</div>`;
        }
        document.getElementById('pdf-btn')?.addEventListener('click', () => { window.location.href = `/api/v1/scans/${scanId}/report.pdf`; });
        document.getElementById('share-btn')?.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(window.location.href);
                window.Aegis.toast('Report link copied', 'success');
            } catch (e) {
                window.Aegis.toast('Could not copy link', 'error');
            }
        });
    });
})();
