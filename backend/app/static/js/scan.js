/* Scan analyzer page: explicit coverage, retention, and response workflow. */
(function () {
  'use strict';
  const { api, toast, esc, t } = window.Aegis;
  let currentKind = 'url';
  let currentScanId = null;
  let currentScanType = null;
  let currentScanTarget = null;
  let currentResult = null;
  const tabs = document.querySelectorAll('.scan-tab');
  const GUIDED_DEMO = {
    subject: 'Action required: verify your digital service account',
    sender: 'Account Review <security@paypa1-account-review.example>',
    body: 'This is a fictional AEGIS demonstration scenario. Your account requires urgent verification. Review it now at https://paypa1-account-review.example/verify?account=demo. Do not enter real credentials.',
    headers: 'From: Account Review <security@paypa1-account-review.example>\nSubject: Action required: verify your digital service account',
  };
  const feedbackPanel = document.getElementById('feedback-panel');
  const feedbackPanelMarkup = feedbackPanel?.innerHTML || '';
  const panels = {};

  function isPersian() { return window.AegisI18n?.locale?.() === 'fa'; }
  function localizeEngineCopy(value) {
    const text = String(value || '');
    if (!isPersian()) return text;
    const translations = {
      'Requests verification code': 'درخواست کد تأیید',
      'Identity theft attempt': 'تلاش برای سرقت هویت',
      'Poor grammar / broken language': 'نگارش نامتعارف یا ناقص',
      'Account verification request': 'درخواست تأیید حساب',
      'Requests password': 'درخواست گذرواژه',
      'Fear tactics detected': 'تاکتیک‌های ترساننده شناسایی شد',
      'Government impersonation': 'جعل هویت نهاد دولتی',
      'Bank impersonation': 'جعل هویت بانک',
      'Money transfer request': 'درخواست انتقال پول',
      'Remote access request': 'درخواست دسترسی از راه دور',
      'Stop interacting with this content. It has multiple independent signs of a likely scam or a verified threat match.': 'از هرگونه تعامل با این محتوا دست بکشید. چند نشانهٔ مستقل از کلاه‌برداری محتمل یا تطابق با تهدید تأییدشده وجود دارد.',
      'Block and report the sender or URL. If financial or account data was shared, contact the legitimate provider immediately.': 'فرستنده یا نشانی وب را مسدود و گزارش کنید. اگر دادهٔ مالی یا حساب خود را به اشتراک گذاشته‌اید، فوراً با ارائه‌دهندهٔ اصلی تماس بگیرید.',
      'Change exposed passwords and revoke active sessions from a trusted device.': 'گذرواژه‌های در معرض خطر را تغییر دهید و نشست‌های فعال را از یک دستگاه مطمئن لغو کنید.',
      'Persian authority credential or payment lure': 'فریب با جعل نهاد فارسی و درخواست اعتبار یا پرداخت',
      'Persian delivery-fee lure': 'فریب هزینهٔ تحویل فارسی',
      'Persian benefit-claim lure': 'فریب مطالبهٔ مزایای عمومی فارسی',
    };
    return translations[text] || text;
  }
  function localizeRecommendation(value) {
    const text = localizeEngineCopy(value);
    if (!isPersian() || !text.startsWith('Evidence to verify: ')) return text;
    const evidence = text.slice('Evidence to verify: '.length);
    const titles = {
      'Brand-like destination hostname': 'نام میزبان شبیه برند',
      'Suspicious link in email': 'پیوند مشکوک در ایمیل',
      'Urgency language detected': 'زبان فوریت‌ساز شناسایی شد',
      'Requests verification code': 'درخواست کد تأیید',
      'Identity theft attempt': 'تلاش برای سرقت هویت',
      'Persian authority credential or payment lure': 'فریب با جعل نهاد فارسی و درخواست اعتبار یا پرداخت',
    };
    const title = Object.keys(titles).find((candidate) => evidence.startsWith(candidate));
    return `شواهد نیازمند بررسی: ${title ? `${titles[title]}${evidence.slice(title.length)}` : evidence}`;
  }

  function resetFeedbackPanel() {
    if (!feedbackPanel) return;
    feedbackPanel.innerHTML = feedbackPanelMarkup;
    window.AegisI18n?.apply?.(feedbackPanel);
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
      tab.className = `scan-tab scanner-tab${active ? ' is-active' : ''}`;
      tab.setAttribute('aria-selected', String(active));
    });
    Object.entries(panels).forEach(([panelKind, panel]) => panel.classList.toggle('hidden', panelKind !== kind));
    document.getElementById('result-box')?.classList.add('hidden');
    document.getElementById('scan-box')?.classList.remove('hidden');
  }

  tabs.forEach((tab) => tab.addEventListener('click', () => activate(tab.dataset.tab)));

  function loadGuidedDemo() {
    clearCurrentAssessment();
    activate('email');
    document.getElementById('email-subject').value = GUIDED_DEMO.subject;
    document.getElementById('email-sender').value = GUIDED_DEMO.sender;
    document.getElementById('email-body').value = GUIDED_DEMO.body;
    document.getElementById('email-headers').value = GUIDED_DEMO.headers;
    toast(t('scan.demo_loaded', 'Fictional credential-lure demo loaded. Review the evidence, then choose Analyze.'), 'info');
    document.getElementById('email-body')?.focus();
  }

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
      button.textContent = t('scan.analyzing', 'Analyzing…');
      clearCurrentAssessment();
      const payload = { is_public: false };

    try {
      if (kind === 'url') {
        payload.url = document.getElementById('url-input').value.trim();
        if (!payload.url) throw new Error(t('scan.enter_url_error', 'Enter a URL to analyze'));
      } else if (kind === 'email') {
        const subject = document.getElementById('email-subject').value.trim();
        const sender = document.getElementById('email-sender').value.trim();
        const body = document.getElementById('email-body').value;
        const headers = document.getElementById('email-headers').value;
        if (!body && !subject) throw new Error(t('scan.enter_email_error', 'Enter an email subject or body'));
        payload.raw_email = [headers, `Subject: ${subject}`, `From: ${sender}`, '', body].filter(Boolean).join('\n');
      } else if (kind === 'text') {
        payload.text = document.getElementById('text-input').value;
        if (!payload.text) throw new Error(t('scan.enter_message_error', 'Paste a message to analyze'));
      }

      let data;
      if (kind === 'image' || kind === 'qr' || kind === 'file') {
        const input = document.getElementById(kind === 'image' ? 'image-input' : kind === 'qr' ? 'qr-input' : 'file-input');
        if (!input.files[0]) throw new Error(t('scan.choose_file_error', 'Choose a file to analyze'));
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
      toast(error.message || t('scan.failure', 'The scan could not be completed'), 'error');
    } finally {
      button.disabled = false;
      button.textContent = t('scan.analyze', 'Analyze');
    }
  }

  function statePresentation(data) {
    const state = data.assessment_state || 'complete';
    if (state === 'limited') return {
      title: t('scan.limited_title', 'Limited assessment'), cls: 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100',
      body: t('scan.limited_body', 'Remote checks were not performed because the destination could not be resolved. This is not evidence that the destination is malicious or safe.'),
    };
    if (state === 'blocked') return {
      title: t('scan.blocked_title', 'Safety boundary applied'), cls: 'border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-100',
      body: t('scan.blocked_body', 'AEGIS refused to probe this destination because it is private, reserved, malformed, or outside the safe web-analysis boundary. Treat it as unsafe to inspect from this service.'),
    };
    return {
      title: t('scan.complete_title', 'Assessment completed'), cls: 'border-aegis-200 bg-aegis-50 text-slate-800 dark:border-aegis-900 dark:bg-aegis-950/30 dark:text-slate-100',
      body: t('scan.complete_body', 'The displayed reasons reflect the evidence that AEGIS was able to collect. Confidence describes coverage and agreement, not a guarantee.'),
    };
  }

  function reasonRows(data) {
    return (data.reasons || []).map((reason) => {
      const impact = Number(reason.impact || 0);
      const hostile = impact < 0;
      const neutral = impact === 0;
      const tone = neutral ? 'is-neutral' : hostile ? 'is-risk' : 'is-protective';
      const contribution = neutral ? t('scan.coverage_note', 'Coverage note · no score effect') : `${Math.abs(impact).toFixed(1)} ${hostile ? t('scan.risk_weight', 'risk weight') : t('scan.protective_weight', 'protective weight')}`;
      return `<div class="result-reason ${tone}"><span class="result-reason-dot" aria-hidden="true"></span><div><p>${esc(localizeEngineCopy(reason.reason))}</p><small>${t('scan.reliability', 'Evidence reliability')} ${reason.confidence !== null ? (Number(reason.confidence) * 100).toFixed(0) + '%' : '—'} · ${contribution}</small></div></div>`;
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
    const highlights = (data.highlights || []).map((item) => `<span class="result-highlight">${esc(localizeEngineCopy(item))}</span>`).join('');
    const stored = data.retention === 'not_stored' ? t('scan.not_stored', 'Result was not stored') : data.scan_id ? t('scan.saved_history', 'Saved in scan history') : t('scan.storage_unknown', 'Storage status unavailable');
    const resultTitle = limited ? t('scan.coverage_limited', 'Coverage limited') : t('scan.trust_score', 'Trust score');
    const resultValue = limited ? '—' : `${data.trust_score ?? '—'}`;

    content.innerHTML = `<article class="assessment-result result-${data.verdict || 'unverified'}">
      <div class="result-state result-state-${state.state || data.assessment_state || 'complete'}"><div><p>${state.title}</p><span>${state.body}</span></div><span class="result-verdict">${window.Aegis.badgeFor(data.verdict)}</span></div>
      <div class="result-overview">
        <div class="result-target"><p>${t('scan.target', 'Target')}</p><strong dir="auto"><bdi>${esc(data.target || '')}</bdi></strong></div>
        <div class="result-score"><p>${resultTitle}</p><strong class="${scoreClass}">${resultValue}${limited ? '' : '<small>/100</small>'}</strong><span>${t('scan.evidence_confidence', 'Evidence confidence')} <bdi dir="ltr">${confidence}</bdi></span></div>
      </div>
      <div class="result-score-rail"><span class="${barClass}" style="width: ${limited ? Math.max(8, Number(data.confidence || 0) * 100) : score}%"></span></div>
      <div class="result-detail-grid"><section class="result-detail-panel"><div class="result-panel-heading"><p class="panel-kicker">${t('scan.evidence_reviewed', 'Evidence reviewed')}</p><span>${(data.reasons || []).length}</span></div><div class="result-reason-list">${reasonRows(data) || `<p class="result-empty">${t('scan.no_evidence', 'No specific evidence was available.')}</p>`}</div></section>
      <section class="result-detail-panel"><div class="result-panel-heading"><p class="panel-kicker">${t('scan.recommendations', 'Recommended next steps')}</p></div><ul class="result-recommendation-list">${(data.recommendations || []).map((item) => `<li><span aria-hidden="true">→</span><span>${esc(localizeRecommendation(item))}</span></li>`).join('') || `<li class="result-empty">${t('scan.no_action', 'No additional action is suggested.')}</li>`}</ul>
      <h3>${t('scan.highlights', 'Evidence highlights')}</h3><div class="result-highlights">${highlights || '<span class="result-empty">—</span>'}</div></section></div>
      <div class="result-meta"><span>${esc(stored)}</span><span>${t('report.assessment', 'assessment')}: ${t(`dashboard.scan_type_${data.scan_type || currentScanType}`, data.scan_type || currentScanType || '')}</span><span dir="ltr">${t('report.engine', 'engine')}: ${esc(data.model_used || 'evidence-fusion-v2')}</span></div>
    </article>`;
    document.getElementById('download-pdf-btn')?.classList.toggle('hidden', !currentScanId);
    document.getElementById('casefile-btn')?.classList.toggle('hidden', !currentScanId);
    if (feedbackPanel) feedbackPanel.classList.toggle('hidden', !(currentScanId && data.retention !== 'not_stored'));
    document.getElementById('report-btn')?.classList.toggle('hidden', limited || !currentScanTarget);
    box.classList.remove('hidden');
    window.scrollTo({ top: Math.max(0, box.offsetTop - 80), behavior: 'smooth' });
  }

  async function copyEvidence() {
    if (!currentResult) return;
    const evidence = (currentResult.findings || []).map((finding) => `${finding.title || finding.code}: ${finding.evidence || 'no excerpt'}`).join('\n');
    const text = [`AEGIS assessment`, `Target: ${currentResult.target || ''}`, `State: ${currentResult.assessment_state || 'complete'}`, `Verdict: ${currentResult.verdict}`, `Evidence:`, evidence].join('\n');
    try { await navigator.clipboard.writeText(text); toast(t('scan.copied', 'Evidence summary copied'), 'success'); }
    catch (_) { toast(t('scan.clipboard_unavailable', 'Clipboard access is unavailable'), 'error'); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.scan-run').forEach((button) => button.addEventListener('click', () => runScan(button.dataset.kind)));
    document.getElementById('new-scan-btn')?.addEventListener('click', () => { clearCurrentAssessment(); activate(currentKind); });
    document.getElementById('copy-evidence-btn')?.addEventListener('click', copyEvidence);
    document.getElementById('casefile-btn')?.addEventListener('click', () => { if (currentScanId) window.location.href = `/report/${currentScanId}`; });
    document.getElementById('load-demo-btn')?.addEventListener('click', loadGuidedDemo);
    if (new URLSearchParams(window.location.search).get('demo') === 'credential-lure') loadGuidedDemo();
    document.getElementById('download-pdf-btn')?.addEventListener('click', () => { if (currentScanId) window.location.href = `/api/v1/scans/${currentScanId}/report.pdf`; });
    document.getElementById('report-btn')?.addEventListener('click', async () => {
      if (!currentScanId || !currentScanTarget) return;
      try {
        const data = await api('POST', '/api/v1/threats/report', { content_type: currentScanType || 'url', content: currentScanTarget, category: 'phishing' });
        toast(data.message || t('scan.submitted', 'Submitted for moderation'), 'success');
      } catch (error) { toast(error.message, 'error'); }
    });
    feedbackPanel?.addEventListener('click', async (event) => {
      const button = event.target.closest('.feedback-btn');
      if (!button) return;
      if (!currentScanId) { toast(t('scan.only_stored', 'Only stored scans can receive outcome feedback'), 'info'); return; }
      const verdict = button.dataset.feedback;
      button.disabled = true;
      try {
        await api('POST', `/api/v1/scans/${currentScanId}/feedback`, { verdict });
        feedbackPanel.innerHTML = `<p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">${t('scan.thanks', 'Thanks. Your outcome was recorded separately for quality review.')}</p>`;
        toast(t('scan.outcome_recorded', 'Outcome recorded'), 'success');
      } catch (error) { toast(error.message, 'error'); button.disabled = false; }
    });
  });
})();
