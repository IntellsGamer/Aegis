/* Scan analyzer page */
(function () {
  'use strict';
  const { api, toast, esc } = window.Aegis;
  let currentKind = 'url';
  let currentScanId = null;
  let currentScanType = null;
  let currentScanTarget = null;

  const tabs = document.querySelectorAll('.scan-tab');
  const panels = {};

  document.querySelectorAll('.scan-panel').forEach((p) => { panels[p.dataset.panel] = p; });

  function activate(kind) {
    currentKind = kind;
    tabs.forEach((t) => {
      const on = t.dataset.tab === kind;
      t.className = `scan-tab px-3 py-2.5 rounded-xl border text-sm font-medium transition ${on ? 'border-aegis-500 bg-aegis-50 dark:bg-aegis-950 text-aegis-700 dark:text-aegis-300' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-500 hover:border-aegis-400'}`;
    });
    Object.entries(panels).forEach(([k, el]) => el.classList.toggle('hidden', k !== kind));
    const box = document.getElementById('result-box');
    if (box) box.classList.add('hidden');
    if (document.getElementById('scan-box')) document.getElementById('scan-box').classList.remove('hidden');
  }

  tabs.forEach((t) => t.addEventListener('click', () => activate(t.dataset.tab)));

  function bindDrop(zoneId, inputId, previewId, onSelect) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    if (!zone || !input) return;
    zone.addEventListener('click', () => input.click());
    input.addEventListener('change', () => onSelect(input.files[0]));
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('border-aegis-500'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('border-aegis-500'));
    zone.addEventListener('drop', (e) => {
      e.preventDefault(); zone.classList.remove('border-aegis-500');
      if (e.dataTransfer.files[0]) onSelect(e.dataTransfer.files[0]);
    });
    if (preview) {
      preview.addEventListener('click', () => input.click());
    }
  }

  function setFilePreview(file, imgId, textId) {
    const enable = () => document.querySelector(`.scan-run[data-kind="${currentKind}"]`).disabled = false;
    if (file.type.startsWith('image/') && imgId) {
      const img = document.querySelector(`#${imgId} img`);
      const box = document.getElementById(imgId);
      box.classList.remove('hidden');
      img.src = URL.createObjectURL(file);
      enable();
    } else if (textId) {
      const box = document.getElementById(textId);
      box.classList.remove('hidden');
      box.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      enable();
    } else {
      enable();
    }
  }

  bindDrop('image-zone', 'image-input', 'image-preview', (f) => setFilePreview(f, 'image-preview', null));
  bindDrop('qr-zone', 'qr-input', 'qr-preview', (f) => setFilePreview(f, 'qr-preview', null));
  bindDrop('file-zone', 'file-input', 'file-preview', (f) => setFilePreview(f, null, 'file-preview'));

  async function runScan(kind) {
    const btn = document.querySelector(`.scan-run[data-kind="${kind}"]`);
    if (!btn) return;
    btn.disabled = true; btn.textContent = 'Analyzing…';

    const payload = { is_public: false };
    if (kind === 'url') {
      payload.url = document.getElementById('url-input').value.trim();
      if (!payload.url) { toast('Please enter a URL', 'error'); reset(btn, kind); return; }
    } else if (kind === 'email') {
      const subject = document.getElementById('email-subject').value.trim();
      const sender = document.getElementById('email-sender').value.trim();
      const body = document.getElementById('email-body').value;
      const headers = document.getElementById('email-headers').value;
      payload.raw_email = [headers, `Subject: ${subject}`, `From: ${sender}`, '', body]
        .filter(Boolean).join('\n');
      if (!body && !subject) { toast('Please enter an email subject or body', 'error'); reset(btn, kind); return; }
    } else if (kind === 'text') {
      payload.text = document.getElementById('text-input').value;
      if (!payload.text) { toast('Please paste a message', 'error'); reset(btn, kind); return; }
    } else if (kind === 'image' || kind === 'qr') {
      const input = document.getElementById(kind === 'image' ? 'image-input' : 'qr-input');
      if (!input.files[0]) { toast('Please choose a file', 'error'); reset(btn, kind); return; }
      const fd = new FormData();
      fd.append('file', input.files[0]);
      try {
        const data = await window.Aegis.api('POST', `/api/v1/scans/${kind}`, fd, true);
        currentScanId = data.scan_id; currentScanType = kind;
        renderResult(data);
      } catch (err) {
        toast(err.message, 'error');
      } finally {
        reset(btn, kind);
      }
      return;
    } else if (kind === 'file') {
      const input = document.getElementById('file-input');
      if (!input.files[0]) { toast('Please choose a file', 'error'); reset(btn, kind); return; }
      const fd = new FormData();
      fd.append('file', input.files[0]);
      try {
        const data = await window.Aegis.api('POST', `/api/v1/scans/${kind}`, fd, true);
        currentScanId = data.scan_id; currentScanType = kind;
        renderResult(data);
      } catch (err) {
        toast(err.message, 'error');
      } finally {
        reset(btn, kind);
      }
      return;
    }

    const endpoint = kind === 'url' ? '/api/v1/scans/url'
      : kind === 'email' ? '/api/v1/scans/email'
      : '/api/v1/scans/text';
    try {
      const data = await window.Aegis.api('POST', endpoint, payload);
      currentScanId = data.scan_id; currentScanType = kind;
      renderResult(data);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      reset(btn, kind);
    }
  }

  function reset(btn, kind) {
    if (!btn) return;
    btn.disabled = false;
    btn.textContent = 'Analyze';
  }

  function renderResult(data) {
    const box = document.getElementById('result-box');
    const content = document.getElementById('result-content');
    box.classList.remove('hidden');
    currentScanTarget = data.target || '';

    const reasons = (data.reasons || []).map((r) => `
      <div class="flex items-start gap-3 py-2 border-b border-slate-100 dark:border-slate-800 last:border-0">
        <span class="mt-1 w-2 h-2 rounded-full shrink-0 ${r.impact >= 0 ? 'bg-emerald-500' : 'bg-red-500'}"></span>
        <div class="flex-1">
          <p class="text-sm font-medium">${esc(r.reason)}</p>
          <p class="text-xs text-slate-500 mt-0.5">Confidence ${r.confidence !== null ? (r.confidence * 100).toFixed(0) + '%' : '—'} · impact ${r.impact > 0 ? '+' : ''}${r.impact}</p>
        </div>
      </div>`).join('');

    const highlights = (data.highlights || []).map((h) => `<span class="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-xs">${esc(h)}</span>`).join('');

    content.innerHTML = `
      <div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <p class="text-sm text-slate-500 mb-1">Target</p>
            <p class="font-mono break-all">${esc(data.target || '')}</p>
          </div>
          <div class="text-center">
            <p class="text-sm text-slate-500 mb-1">Trust Score</p>
            <p class="font-mono text-4xl font-bold ${(data.trust_score || 0) >= 70 ? 'text-emerald-500' : (data.trust_score || 0) >= 40 ? 'text-amber-500' : 'text-red-500'}">${data.trust_score ?? '—'}<span class="text-lg">/100</span></p>
          </div>
          <div>${window.Aegis.badgeFor(data.verdict)}</div>
        </div>
        <div class="h-3 rounded-full bg-slate-200 dark:bg-slate-800 mb-6">
          <div class="h-3 rounded-full transition-all ${(data.trust_score || 0) >= 70 ? 'bg-emerald-500' : (data.trust_score || 0) >= 40 ? 'bg-amber-500' : 'bg-red-500'}" style="width: ${data.trust_score || 0}%"></div>
        </div>
        <div class="grid lg:grid-cols-2 gap-6">
          <div>
            <h3 class="font-semibold mb-3">Why this verdict</h3>
            <div>${reasons || '<p class="text-sm text-slate-400">No reasons.</p>'}</div>
          </div>
          <div>
            <h3 class="font-semibold mb-3">Recommendations</h3>
            <ul class="space-y-2">
              ${(data.recommendations || []).map((r) => `<li class="flex items-start gap-2 text-sm"><span class="text-aegis-500 mt-0.5">→</span> ${esc(r)}</li>`).join('') || '<p class="text-sm text-slate-400">No recommendations.</p>'}
            </ul>
            <h3 class="font-semibold mt-6 mb-2">Highlights</h3>
            <div class="flex flex-wrap gap-2">${highlights || '—'}</div>
          </div>
        </div>
        <div class="mt-6 flex items-center gap-2 text-xs text-slate-400">
          <span class="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">scan_type: ${esc(data.scan_type || currentScanType || '')}</span>
          <span class="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">model: ${esc(data.model_used || 'rules')}</span>
        </div>
      </div>`;

    window.scrollTo({ top: box.offsetTop - 80, behavior: 'smooth' });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.scan-run').forEach((btn) => btn.addEventListener('click', () => runScan(btn.dataset.kind)));
    document.getElementById('new-scan-btn')?.addEventListener('click', () => { activate(currentKind); });
    document.getElementById('download-pdf-btn')?.addEventListener('click', () => {
      if (currentScanId) window.location.href = `/api/v1/scans/${currentScanId}/report.pdf`;
    });
    document.getElementById('report-btn')?.addEventListener('click', async () => {
      if (!currentScanId || !currentScanTarget) return;
      try {
        const data = await window.Aegis.api('POST', '/api/v1/threats/report', {
          content_type: currentScanType || 'url',
          content: currentScanTarget,
          category: 'phishing',
        });
        toast(data.message || 'Threat reported', 'success');
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });
})();
