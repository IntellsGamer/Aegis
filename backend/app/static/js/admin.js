/* Admin panel */
(function () {
  'use strict';
  const { api, esc, toast } = window.Aegis;
  let currentTab = 'threats';
  let currentQuery = '';

  function loadStats() {
    api('GET', '/api/v1/admin/stats').then((s) => {
      const grid = document.getElementById('admin-stats');
      const totals = s.totals || {};
      const active = (s.risk_distribution || []).reduce((n, r) =>
        n + (['high', 'critical'].includes(r.risk) ? r.count : 0), 0);
      const scores = (s.recent_scans || []).map((x) => x.score).filter((x) => x != null);
      const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : '—';
      const items = [
        ['Total Users', totals.users],
        ['Total Scans', totals.scans],
        ['Active Threats', active],
        ['Avg Trust Score', avg],
      ];
      grid.innerHTML = items.map(([label, val]) => `
        <div class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <p class="text-xs text-slate-500 uppercase font-medium mb-1">${label}</p>
          <p class="text-2xl font-bold font-mono">${esc(val ?? '—')}</p>
        </div>`).join('');
    }).catch(() => {});
  }

  async function loadTab(tab, query = '') {
    currentQuery = query;
    const box = document.getElementById('admin-content');
    box.innerHTML = '<div class="py-16 flex justify-center"><div class="w-10 h-10 border-4 border-aegis-500 border-t-transparent rounded-full animate-spin"></div></div>';

    if (tab === 'threats') {
      const data = await api('GET', `/api/v1/admin/threats?q=${encodeURIComponent(query)}`);
      renderThreats(data.items || [], data.total);
    } else if (tab === 'rules') {
      const data = await api('GET', '/api/v1/admin/rules');
      renderRules(Array.isArray(data) ? data : (data.rules || []));
    } else if (tab === 'keywords') {
      const data = await api('GET', '/api/v1/admin/keywords');
      renderKeywords(data.items || [], data.total);
    } else if (tab === 'users') {
      const data = await api('GET', '/api/v1/admin/users');
      renderUsers(data.items || [], data.total);
    } else if (tab === 'audit') {
      const data = await api('GET', '/api/v1/admin/logs');
      renderAudit(data.items || [], data.total);
    } else if (tab === 'readiness') {
      const data = await api('GET', '/api/v1/admin/readiness');
      renderReadiness(data);
    }
  }

  function adminBox(title, inner) {
    return `<div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <h2 class="font-semibold mb-4">${title}</h2>${inner}</div>`;
  }

  function renderThreats(items, total) {
    const box = document.getElementById('admin-content');
    const rows = items.map((t) => `
      <tr class="border-b border-slate-100 dark:border-slate-800">
        <td class="py-2 px-2 font-mono text-sm">${esc(t.value || t.target || '')}</td>
        <td class="py-2 px-2 text-sm">${esc(t.threat_type || '')}</td>
        <td class="py-2 px-2 text-sm">${esc(t.category || '')}</td>
        <td class="py-2 px-2"><span class="px-2 py-0.5 rounded-full text-xs text-white ${t.severity === 'critical' || t.severity === 'high' ? 'bg-red-500' : 'bg-amber-500'}">${esc(t.severity || '')}</span></td>
        <td class="py-2 px-2 text-sm">${t.active === false ? '<span class="text-slate-400">inactive</span>' : '<span class="text-emerald-500">active</span>'}</td>
        <td class="py-2 px-2 text-sm">${t.hits ?? 0}</td>
        <td class="py-2 px-2 text-right"><button class="del-threat text-xs text-red-500 hover:underline" data-id="${t.id}">Delete</button></td>
      </tr>`).join('');
    box.innerHTML = adminBox('Threat Intelligence', `
      <input id="threat-search" placeholder="Search threats…" value="${esc(currentQuery)}" class="mb-4 w-full max-w-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-3 py-2 text-sm">
      <p class="text-xs text-slate-400 mb-2">${total || items.length} threat(s)</p>
      <div class="overflow-x-auto"><table class="w-full text-left">${rows || '<tr><td class="py-4 text-sm text-slate-400">No threats.</td></tr>'}</table></div>`);
    document.getElementById('threat-search')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') loadTab('threats', e.target.value);
    });
    box.querySelectorAll('.del-threat').forEach((b) => b.addEventListener('click', async () => {
      await api('DELETE', `/api/v1/admin/threats/${b.dataset.id}`);
      toast('Threat deleted', 'success');
      loadTab('threats');
    }));
  }

  function renderRules(rules) {
    const box = document.getElementById('admin-content');
    const rows = rules.map((r) => `
      <tr class="border-b border-slate-100 dark:border-slate-800">
        <td class="py-2 px-2"><span class="font-mono text-sm">${esc(r.code || r.key || '')}</span><span class="block text-xs text-slate-400">${esc(r.category || '')}</span></td>
        <td class="py-2 px-2 text-sm">${esc(r.description || r.name || '')}</td>
        <td class="py-2 px-2"><input class="rule-weight w-20 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2 py-1 text-sm font-mono" data-id="${r.id}" value="${r.weight ?? r.impact ?? 0}" type="number"></td>
        <td class="py-2 px-2"><label class="flex items-center gap-2 text-sm"><input class="rule-active" data-id="${r.id}" type="checkbox" ${r.enabled ? 'checked' : ''}> active</label></td>
        <td class="py-2 px-2 text-sm">${esc(r.severity || '')}</td>
      </tr>`).join('');
    box.innerHTML = adminBox('Trust Rules', `
      <p class="text-xs text-slate-400 mb-3">Adjust rule weights and activation. Changes apply to the next scan.</p>
      <div class="overflow-x-auto"><table class="w-full text-left">${rows}</table></div>
      <button id="save-rules" class="mt-4 px-4 py-2 rounded-lg bg-aegis-600 hover:bg-aegis-500 text-white text-sm font-semibold">Save Changes</button>`);
    document.getElementById('save-rules').addEventListener('click', async () => {
      const updates = [];
      box.querySelectorAll('.rule-weight').forEach((i) => {
        updates.push({ id: parseInt(i.dataset.id, 10), weight: parseFloat(i.value) });
      });
      box.querySelectorAll('.rule-active').forEach((c) => {
        const u = updates.find((x) => x.id === parseInt(c.dataset.id, 10));
        if (u) u.is_active = c.checked;
      });
      try {
        await api('PUT', '/api/v1/admin/rules', { rules: updates });
        toast('Rules updated', 'success');
      } catch (e) { toast(e.message, 'error'); }
    });
  }

  function renderKeywords(keywords) {
    const box = document.getElementById('admin-content');
    const rows = keywords.map((k) => `
      <tr class="border-b border-slate-100 dark:border-slate-800">
        <td class="py-2 px-2 font-mono text-sm">${esc(k.keyword)}</td>
        <td class="py-2 px-2 text-sm">${esc(k.category || '')}</td>
        <td class="py-2 px-2 text-sm font-mono">${k.impact ?? 0}</td>
        <td class="py-2 px-2 text-sm">${k.enabled === false ? '<span class="text-slate-400">inactive</span>' : '<span class="text-emerald-500">active</span>'}</td>
        <td class="py-2 px-2 text-right"><button class="del-kw text-xs text-red-500 hover:underline" data-id="${k.id}">Delete</button></td>
      </tr>`).join('');
    box.innerHTML = adminBox('Phishing Keywords', `
      <form id="add-kw" class="flex gap-2 mb-4">
        <input name="keyword" placeholder="e.g. urgent action required" class="flex-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-3 py-2 text-sm">
        <input name="category" placeholder="category" class="w-32 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-3 py-2 text-sm">
        <input name="impact" placeholder="impact" type="number" class="w-20 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-3 py-2 text-sm">
        <button class="px-4 py-2 rounded-lg bg-aegis-600 hover:bg-aegis-500 text-white text-sm font-semibold">Add</button>
      </form>
      <div class="overflow-x-auto"><table class="w-full text-left">${rows || '<tr><td class="py-4 text-sm text-slate-400">No keywords.</td></tr>'}</table></div>`);
    document.getElementById('add-kw').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await api('POST', '/api/v1/admin/keywords', {
          keyword: e.target.keyword.value.trim(),
          category: e.target.category.value.trim(),
          impact: parseFloat(e.target.impact.value || -5),
        });
        toast('Keyword added', 'success');
        loadTab('keywords');
      } catch (err) { toast(err.message, 'error'); }
    });
    box.querySelectorAll('.del-kw').forEach((b) => b.addEventListener('click', async () => {
      await api('DELETE', `/api/v1/admin/keywords/${b.dataset.id}`);
      toast('Keyword deleted', 'success');
      loadTab('keywords');
    }));
  }

  function renderUsers(items, total) {
    const box = document.getElementById('admin-content');
    const rows = items.map((u) => `
      <tr class="border-b border-slate-100 dark:border-slate-800">
        <td class="py-2 px-2 text-sm font-medium">${esc(u.username)}</td>
        <td class="py-2 px-2 text-sm">${esc(u.email || '')}</td>
        <td class="py-2 px-2 text-sm">${u.is_admin ? '<span class="px-2 py-0.5 rounded-full bg-aegis-600 text-white text-xs">admin</span>' : '<span class="text-slate-400 text-xs">user</span>'}</td>
        <td class="py-2 px-2 text-sm">${u.is_active ? '<span class="text-emerald-500">active</span>' : '<span class="text-red-500">disabled</span>'}</td>
        <td class="py-2 px-2 text-right">
          ${u.is_admin ? '' : `<button class="toggle-user text-xs text-amber-500 hover:underline" data-id="${u.id}" data-active="${u.is_active}">${u.is_active ? 'Disable' : 'Enable'}</button>`}
        </td>
      </tr>`).join('');
    box.innerHTML = adminBox(`Users (${total || items.length})`, `
      <div class="overflow-x-auto"><table class="w-full text-left">${rows}</table></div>`);
    box.querySelectorAll('.toggle-user').forEach((b) => b.addEventListener('click', async () => {
      const id = b.dataset.id;
      const active = b.dataset.active === 'true' ? false : true;
      try {
        await api('PATCH', `/api/v1/admin/users/${id}`, { is_active: active });
        toast('User updated', 'success');
        loadTab('users');
      } catch (e) { toast(e.message, 'error'); }
    }));
  }

  function renderAudit(logs) {
    const box = document.getElementById('admin-content');
    const rows = logs.map((l) => `
      <tr class="border-b border-slate-100 dark:border-slate-800">
        <td class="py-2 px-2 text-xs font-mono text-slate-400">${esc((l.created_at || '').slice(0, 19).replace('T', ' '))}</td>
        <td class="py-2 px-2 text-sm">${esc(l.user_id || 'system')}</td>
        <td class="py-2 px-2 text-sm">${esc(l.action)}</td>
        <td class="py-2 px-2 text-xs text-slate-500">${esc(l.detail || l.ip_address || '')}</td>
      </tr>`).join('');
    box.innerHTML = adminBox('Audit Log', `
      <div class="overflow-x-auto"><table class="w-full text-left">${rows || '<tr><td class="py-4 text-sm text-slate-400">No logs.</td></tr>'}</table></div>`);
  }

  function renderReadiness(data) {
    const box = document.getElementById('admin-content');
    const engine = data.engine || {};
    const quality = data.assessment_quality || {};
    const outcomes = data.outcome_review || {};
    const outcomeRows = Object.entries(outcomes.by_verdict || {}).map(([key, value]) => `<span class="rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">${esc(key.replaceAll('_', ' '))}: <strong>${esc(value)}</strong></span>`).join('');
    const feedRows = (data.feeds || []).map((feed) => `<tr class="border-b border-slate-100 dark:border-slate-800"><td class="px-2 py-2 font-mono text-sm">${esc(feed.provider || feed.slug)}</td><td class="px-2 py-2 text-sm">${feed.enabled ? '<span class="text-emerald-500">enabled</span>' : '<span class="text-slate-400">disabled</span>'}</td><td class="px-2 py-2 text-sm">${feed.terms_accepted ? '<span class="text-emerald-500">accepted</span>' : '<span class="text-amber-500">not accepted</span>'}</td><td class="px-2 py-2 text-xs text-slate-500">${esc(feed.data_boundary || '—')}</td></tr>`).join('') || '<tr><td class="px-2 py-4 text-sm text-slate-500" colspan="4">No governed feed records yet.</td></tr>';
    const safeguards = (data.safeguards || []).map((item) => `<li class="rounded-xl border border-slate-200 p-3 dark:border-slate-800"><p class="text-sm font-semibold">${esc(item.control)}</p><p class="mt-1 text-xs leading-5 text-slate-500">${esc(item.detail)}</p></li>`).join('');
    box.innerHTML = `<div class="space-y-6">
      <section class="overflow-hidden rounded-2xl border border-aegis-200 bg-gradient-to-br from-aegis-50 via-white to-slate-50 p-6 dark:border-aegis-900 dark:from-aegis-950/30 dark:via-slate-900 dark:to-slate-900"><div class="flex flex-wrap items-start justify-between gap-5"><div><p class="text-xs font-semibold uppercase tracking-[0.18em] text-aegis-700 dark:text-aegis-300">Operational accountability</p><h2 class="mt-1 text-xl font-bold">Readiness & governance</h2><p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">A review surface for the controls that make AEGIS explainable and governable. It reports observed coverage and outcome review, never fabricated model accuracy.</p></div><div class="rounded-xl border border-aegis-200 bg-white/80 p-4 text-right dark:border-aegis-900 dark:bg-slate-950/60"><p class="text-xs text-slate-500">Engine</p><p class="mt-1 font-semibold text-aegis-700 dark:text-aegis-300">${esc(engine.version || 'evidence-fusion-v2')}</p><p class="mt-1 text-xs text-slate-500">${engine.training_required ? 'training required' : 'no model training'}</p></div></div></section>
      <section class="grid gap-4 md:grid-cols-3"><div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Completed assessments</p><p class="mt-2 font-mono text-3xl font-bold">${esc(quality.completed ?? 0)}</p><p class="mt-2 text-xs text-slate-500">Persisted assessments in the quality view.</p></div><div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">High-coverage share</p><p class="mt-2 font-mono text-3xl font-bold">${quality.high_confidence_share !== undefined ? `${Math.round(Number(quality.high_confidence_share) * 100)}%` : '—'}</p><p class="mt-2 text-xs text-slate-500">Coverage and agreement, not predictive accuracy.</p></div><div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Outcome review · ${esc(outcomes.window_days || 30)}d</p><p class="mt-2 font-mono text-3xl font-bold">${esc(outcomes.total ?? 0)}</p><p class="mt-2 text-xs text-slate-500">Human or policy-confirmed outcomes.</p></div></section>
      <section class="grid gap-6 lg:grid-cols-2"><div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900"><h3 class="font-semibold">Engine disclosure</h3><p class="mt-2 text-sm text-slate-500">${esc(engine.prediction_method || 'Deterministic evidence fusion')}</p><div class="mt-4 flex flex-wrap gap-2">${(engine.evidence_sources || []).map((source) => `<span class="rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">${esc(source)}</span>`).join('')}</div><p class="mt-4 text-xs leading-5 text-slate-500">${esc(data.measurement_note || '')}</p><div class="mt-4 flex flex-wrap gap-2">${outcomeRows || '<span class="text-xs text-slate-500">No outcomes in this review window.</span>'}</div></div><div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900"><h3 class="font-semibold">Control boundaries</h3><ul class="mt-4 grid gap-3">${safeguards}</ul></div></section>
      <section class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900"><div class="flex flex-wrap items-center justify-between gap-3"><div><h3 class="font-semibold">Governed intelligence sources</h3><p class="mt-1 text-sm text-slate-500">Sources remain disabled until their terms are explicitly accepted; their state is visible here for review.</p></div><span class="rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">${(data.feeds || []).filter((feed) => feed.enabled).length}/${(data.feeds || []).length} enabled</span></div><div class="mt-4 overflow-x-auto"><table class="w-full text-left"><thead class="text-xs uppercase tracking-wide text-slate-500"><tr><th class="px-2 py-2">Source</th><th class="px-2 py-2">State</th><th class="px-2 py-2">Terms</th><th class="px-2 py-2">Boundary</th></tr></thead><tbody>${feedRows}</tbody></table></div></section>
    </div>`;
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    document.querySelectorAll('.admin-tab').forEach((t) => t.addEventListener('click', () => {
      document.querySelectorAll('.admin-tab').forEach((x) => {
        x.classList.remove('border-aegis-500', 'bg-aegis-600', 'text-white');
        x.classList.add('text-slate-500');
      });
      t.classList.add('border-aegis-500', 'bg-aegis-600', 'text-white');
      t.classList.remove('text-slate-500');
      currentTab = t.dataset.tab;
      loadTab(currentTab);
    }));
    loadTab(currentTab);
  });
})();
