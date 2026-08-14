/* Scan analyzer page: explicit coverage, retention, and response workflow. */
(function () {
  'use strict';
  const { api, toast, esc } = window.Aegis;
  let currentKind = 'url';
  let currentScanId = null;
  let currentScanType = null;
  let currentScanTarget = null;
  let currentResult = null;
  const tabs = document.querySelectorAll('.scan-tab');
  const feedbackPanel = document.getElementById('feedback-panel');
  const feedbackPanelMarkup = feedbackPanel?.innerHTML || '';
  const panels = {};

  function resetFeedbackPanel() {
    if (!feedbackPanel) return;
    feedbackPanel.innerHTML = feedbackPanelMarkup;
    feedbackPanel.classList.add('hidden');
  }

  function clearCurrentAssessment() {
    currentScanId = null;
    currentScanType = null;
    currentScanTarget = null;
    currentResult = null;
    resetFeedbackPanel();
  }
  document.querySelectorAll('.scan-panel').forEach((panel) => { panels[panel.dataset.panel] = panel; });

  function activate(kind) {
    currentKind = kind;
    tabs.forEach((tab) => {
      const active = tab.dataset.tab === kind;
      tab.className = `scan-tab px-3 py-2.5 rounded-xl border text-sm font-medium transition ${active ? 'border-aegis-500 bg-aegis-50 dark:bg-aegis-950 text-aegis-700 dark:text-aegis-300' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-500 hover:border-aegis-400'}`;
      tab.setAttribute('aria-selected', String(active));
    });
    Object.entries(panels).forEach(([panelKind, panel]) => panel.classList.toggle('hidden', panelKind !== kind));
    document.getElementById('result-box')?.classList.add('hidden');
    document.getElementById('scan-box')?.classList.remove('hidden');
  }

  tabs.forEach((tab) => tab.addEventListener('click', () => activate(tab.dataset.tab)));

  function bindDrop(zoneId, inputId, previewId, onSelect) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    if (!zone || !input) return;
    zone.addEventListener('click', () => input.click());
    input.addEventListener('change', () => onSelect(input.files[0]));
    zone.addEventListener('dragover', (event) => { event.preventDefault(); zone.classList.add('border-aegis-500'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('border-aegis-500'));
    zone.addEventListener('drop', (event) => {
      event.preventDefault(); zone.classList.remove('border-aegis-500');
      if (event.dataTransfer.files[0]) onSelect(event.dataTransfer.files[0]);
    });
    preview?.addEventListener('click', () => input.click());
  }

  function setFilePreview(file, imageId, textId) {
    const run = document.querySelector(`.scan-run[data-kind="${currentKind}"]`);
    if (file.type.startsWith('image/') && imageId) {
      const image = document.querySelector(`#${imageId} img`);
      document.getElementById(imageId).classList.remove('hidden');
      image.src = URL.createObjectURL(file);
    } else if (textId) {
      const preview = document.getElementById(textId);
      preview.classList.remove('hidden');
      preview.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    }
    if (run) run.disabled = false;
  }

  bindDrop('image-zone', 'image-input', 'image-preview', (file) => setFilePreview(file, 'image-preview', null));
  bindDrop('qr-zone', 'qr-input', 'qr-preview', (file) => setFilePreview(file, 'qr-preview', null));
  bindDrop('file-zone', 'file-input', 'file-preview', (file) => setFilePreview(file, null, 'file-preview'));

  async function runScan(kind) {
    const button = document.querySelector(`.scan-run[data-kind="${kind}"]`);
    if (!button) return;
          button.disabled = true;
      button.textContent = 'Analyzing…';
      clearCurrentAssessment();
      const payload = { is_public: false };

    try {
      if (kind === 'url') {
        payload.url = document.getElementById('url-input').value.trim();
        if (!payload.url) throw new Error('Enter a URL to analyze');
      } else if (kind === 'email') {
        const subject = document.getElementById('email-subject').value.trim();
        const sender = document.getElementById('email-sender').value.trim();
        const body = document.getElementById('email-body').value;
        const headers = document.getElementById('email-headers').value;
        if (!body && !subject) throw new Error('Enter an email subject or body');
        payload.raw_email = [headers, `Subject: ${subject}`, `From: ${sender}`, '', body].filter(Boolean).join('\n');
      } else if (kind === 'text') {
        payload.text = document.getElementById('text-input').value;
        if (!payload.text) throw new Error('Paste a message to analyze');
      }

      let data;
      if (kind === 'image' || kind === 'qr' || kind === 'file') {
        const input = document.getElementById(kind === 'image' ? 'image-input' : kind === 'qr' ? 'qr-input' : 'file-input');
        if (!input.files[0]) throw new Error('Choose a file to analyze');
        const form = new FormData();
        form.append('file', input.files[0]);
        data = await api('POST', `/api/v1/scans/${kind}`, form, true);
      } else {
        const endpoint = kind === 'url' ? '/api/v1/scans/url' : kind === 'email' ? '/api/v1/scans/email' : '/api/v1/scans/text';
        data = await api('POST', endpoint, payload);
      }
      currentScanId = data.scan_id || null;
      currentScanType = kind;
      currentScanTarget = data.target || '';
      currentResult = data;
      renderResult(data);
    } catch (error) {
      toast(error.message || 'The scan could not be completed', 'error');
    } finally {
      button.disabled = false;
      button.textContent = 'Analyze';
    }
  }

  function statePresentation(data) {
    const state = data.assessment_state || 'complete';
    if (state === 'limited') return {
      title: 'Limited assessment', cls: 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100',
      body: 'Remote checks were not performed because the destination could not be resolved. This is not evidence that the destination is malicious or safe.',
    };
    if (state === 'blocked') return {
      title: 'Safety boundary applied', cls: 'border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-100',
      body: 'AEGIS refused to probe this destination because it is private, reserved, malformed, or outside the safe web-analysis boundary. Treat it as unsafe to inspect from this service.',
    };
    return {
      title: 'Assessment completed', cls: 'border-aegis-200 bg-aegis-50 text-slate-800 dark:border-aegis-900 dark:bg-aegis-950/30 dark:text-slate-100',
      body: 'The displayed reasons reflect the evidence that AEGIS was able to collect. Confidence describes coverage and agreement, not a guarantee.',
    };
  }

  function reasonRows(data) {
    return (data.reasons || []).map((reason) => {
      const impact = Number(reason.impact || 0);
      const hostile = impact < 0;
      const neutral = impact === 0;
      const dot = neutral ? 'bg-slate-400' : hostile ? 'bg-red-500' : 'bg-emerald-500';
      const contribution = neutral ? 'Coverage note · no score effect' : `${Math.abs(impact).toFixed(1)} ${hostile ? 'risk' : 'protective'} weight`;
      return `<div class="flex items-start gap-3 py-3 border-b border-slate-100 dark:border-slate-800 last:border-0">
        <span class="mt-1.5 h-2 w-2 rounded-full shrink-0 ${dot}"></span>
        <div class="flex-1"><p class="text-sm font-medium">${esc(reason.reason)}</p>
        <p class="mt-0.5 text-xs text-slate-500">Evidence reliability ${reason.confidence !== null ? (Number(reason.confidence) * 100).toFixed(0) + '%' : '—'} · ${contribution}</p></div></div>`;
    }).join('');
  }

  function renderResult(data) {
    const box = document.getElementById('result-box');
    const content = document.getElementById('result-content');
    const state = statePresentation(data);
    const limited = data.assessment_state === 'limited';
    const score = Number(data.trust_score || 0);
    const scoreClass = limited ? 'text-slate-500' : score >= 85 ? 'text-emerald-500' : score >= 60 ? 'text-amber-500' : 'text-red-500';
    const barClass = limited ? 'bg-slate-400' : score >= 85 ? 'bg-emerald-500' : score >= 60 ? 'bg-amber-500' : 'bg-red-500';
    const confidence = data.confidence !== null && data.confidence !== undefined ? `${(Number(data.confidence) * 100).toFixed(0)}%` : '—';
    const highlights = (data.highlights || []).map((item) => `<span class="rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800">${esc(item)}</span>`).join('');
    const stored = data.retention === 'not_stored' ? 'Result was not stored' : data.scan_id ? 'Saved in scan history' : 'Storage status unavailable';
    const resultTitle = limited ? 'Coverage limited' : 'Trust score';
    const resultValue = limited ? '—' : `${data.trust_score ?? '—'}`;

    content.innerHTML = `<article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div class="mb-5 rounded-xl border p-4 ${state.cls}"><p class="font-semibold">${state.title}</p><p class="mt-1 text-sm leading-5">${state.body}</p></div>
      <div class="flex flex-wrap items-start justify-between gap-5 mb-5">
        <div class="min-w-0 flex-1"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Target</p><p class="mt-1 break-all font-mono text-sm">${esc(data.target || '')}</p></div>
        <div class="text-right"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${resultTitle}</p><p class="mt-1 font-mono text-4xl font-bold ${scoreClass}">${resultValue}${limited ? '' : '<span class="text-lg">/100</span>'}</p><p class="mt-1 text-xs text-slate-500">Evidence confidence ${confidence}</p></div>
        <div>${window.Aegis.badgeFor(data.verdict)}</div>
      </div>
      <div class="mb-6 h-2.5 rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-2.5 rounded-full ${barClass}" style="width: ${limited ? Math.max(8, Number(data.confidence || 0) * 100) : score}%"></div></div>
      <div class="grid gap-6 lg:grid-cols-2"><section><h2 class="font-semibold">Evidence reviewed</h2><div class="mt-2">${reasonRows(data) || '<p class="text-sm text-slate-500">No specific evidence was available.</p>'}</div></section>
      <section><h2 class="font-semibold">Recommended next steps</h2><ul class="mt-3 space-y-2">${(data.recommendations || []).map((item) => `<li class="flex gap-2 text-sm"><span class="text-aegis-500">→</span><span>${esc(item)}</span></li>`).join('') || '<li class="text-sm text-slate-500">No additional action is suggested.</li>'}</ul>
      <h3 class="mt-6 font-semibold">Evidence highlights</h3><div class="mt-2 flex flex-wrap gap-2">${highlights || '<span class="text-sm text-slate-500">—</span>'}</div></section></div>
      <div class="mt-6 flex flex-wrap items-center gap-2 text-xs text-slate-500"><span class="rounded bg-slate-100 px-2 py-1 dark:bg-slate-800">${esc(stored)}</span><span class="rounded bg-slate-100 px-2 py-1 dark:bg-slate-800">scan type: ${esc(data.scan_type || currentScanType || '')}</span><span class="rounded bg-slate-100 px-2 py-1 dark:bg-slate-800">engine: ${esc(data.model_used || 'evidence-fusion-v2')}</span></div>
    </article>`;
    document.getElementById('download-pdf-btn')?.classList.toggle('hidden', !currentScanId);
    if (feedbackPanel) feedbackPanel.classList.toggle('hidden', !(currentScanId && data.retention !== 'not_stored'));
    document.getElementById('report-btn')?.classList.toggle('hidden', limited || !currentScanTarget);
    box.classList.remove('hidden');
    window.scrollTo({ top: Math.max(0, box.offsetTop - 80), behavior: 'smooth' });
  }

  async function copyEvidence() {
    if (!currentResult) return;
    const evidence = (currentResult.findings || []).map((finding) => `${finding.title || finding.code}: ${finding.evidence || 'no excerpt'}`).join('\n');
    const text = [`AEGIS assessment`, `Target: ${currentResult.target || ''}`, `State: ${currentResult.assessment_state || 'complete'}`, `Verdict: ${currentResult.verdict}`, `Evidence:`, evidence].join('\n');
    try { await navigator.clipboard.writeText(text); toast('Evidence summary copied', 'success'); }
    catch (_) { toast('Clipboard access is unavailable', 'error'); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.scan-run').forEach((button) => button.addEventListener('click', () => runScan(button.dataset.kind)));
    document.getElementById('new-scan-btn')?.addEventListener('click', () => { clearCurrentAssessment(); activate(currentKind); });
    document.getElementById('copy-evidence-btn')?.addEventListener('click', copyEvidence);
    document.getElementById('download-pdf-btn')?.addEventListener('click', () => { if (currentScanId) window.location.href = `/api/v1/scans/${currentScanId}/report.pdf`; });
    document.getElementById('report-btn')?.addEventListener('click', async () => {
      if (!currentScanId || !currentScanTarget) return;
      try {
        const data = await api('POST', '/api/v1/threats/report', { content_type: currentScanType || 'url', content: currentScanTarget, category: 'phishing' });
        toast(data.message || 'Submitted for moderation', 'success');
      } catch (error) { toast(error.message, 'error'); }
    });
    feedbackPanel?.addEventListener('click', async (event) => {
      const button = event.target.closest('.feedback-btn');
      if (!button) return;
      if (!currentScanId) { toast('Only stored scans can receive outcome feedback', 'info'); return; }
      const verdict = button.dataset.feedback;
      button.disabled = true;
      try {
        await api('POST', `/api/v1/scans/${currentScanId}/feedback`, { verdict });
        feedbackPanel.innerHTML = '<p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">Thanks. Your outcome was recorded separately for quality review.</p>';
        toast('Outcome recorded', 'success');
      } catch (error) { toast(error.message, 'error'); button.disabled = false; }
    });
  });
})();
