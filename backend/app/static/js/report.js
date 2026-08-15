/* Assessment casefile: derives only from the authorized persisted scan record. */
(function () {
  'use strict';
  const { api, esc, badgeFor, toast, t } = window.Aegis;
  const scanId = window.__REPORT_SCAN_ID__ || window.location.pathname.split('/').pop();
  let casefile = null;

  const stateCopy = () => ({
    complete: [t('report.complete_title', 'Assessment completed'), t('report.complete_body', 'AEGIS completed the available assessment path. The result is evidence-led, not a guarantee.')],
    limited: [t('report.limited_title', 'Limited assessment'), t('report.limited_body', 'Remote destination checks were not completed. Local evidence is shown, but the verdict is intentionally unverified.')],
    blocked: [t('report.blocked_title', 'Safety boundary applied'), t('report.blocked_body', 'AEGIS refused to probe this target because it crosses a network-safety boundary.')],
  });

  function isPersian() { return window.AegisI18n?.locale?.() === 'fa'; }
  function localizeObservation(value) {
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
      'Persian authority credential or payment lure': 'فریب با جعل نهاد فارسی و درخواست اعتبار یا پرداخت',
      'Persian delivery-fee lure': 'فریب هزینهٔ تحویل فارسی',
      'Persian benefit-claim lure': 'فریب مطالبهٔ مزایای عمومی فارسی',
      'The message asks for a verification or one-time code.': 'این پیام کد تأیید یا رمز یک‌بارمصرف درخواست می‌کند.',
      'The message asks for personal documents or data that can be used to steal your identity.': 'این پیام مدارک یا اطلاعات شخصیِ قابل‌استفاده برای سرقت هویت درخواست می‌کند.',
      'The message has language problems typical of bulk scam messages.': 'متن پیام نشانه‌هایی از نگارش نامتعارفِ رایج در پیام‌های انبوه کلاهبرداری دارد.',
      'pattern': 'الگو',
    };
    return translations[text] || text;
  }
  function localizeSummary(value) {
    if (!isPersian()) return value;
    const match = String(value || '').match(/^The (.+?) (shows strong signs of a scam\.|is very likely a scam\.) Trust score ([\d.]+)\/100, estimated risk (\d+)%, evidence confidence (\d+)%\.$/);
    if (!match) return value;
    const labels = { email: 'ایمیل', url: 'نشانی وب', text: 'پیام', image: 'تصویر', qr: 'کد QR', file: 'فایل', content: 'محتوا' };
    const label = labels[match[1].toLowerCase()] || match[1];
    const finding = match[2].startsWith('shows') ? 'نشانه‌های قوی از کلاه‌برداری دارد' : 'به احتمال بسیار زیاد کلاه‌برداری است';
    return `${label} ${finding}. ${t('scan.trust_score', 'Trust score')} ${match[3]}/100، ${t('report.estimated_risk', 'estimated risk')} ${match[4]}٪، ${t('scan.evidence_confidence', 'Evidence confidence')} ${match[5]}٪.`;
  }
  function localizePlaybook(item) {
    if (!isPersian()) return item;
    const action = String(item.action || '');
    const actions = {
      'Stop interacting with this content. It has multiple independent signs of a likely scam or a verified threat match.': t('report.action_stop', 'Stop interacting with this content. It has multiple independent signs of a likely scam or a verified threat match.'),
      'Block and report the sender or URL. If financial or account data was shared, contact the legitimate provider immediately.': t('report.action_block', 'Block and report the sender or URL. If financial or account data was shared, contact the legitimate provider immediately.'),
      'Change exposed passwords and revoke active sessions from a trusted device.': t('report.action_passwords', 'Change exposed passwords and revoke active sessions from a trusted device.'),
    };
    return {
      ...item,
      phase: String(item.phase || '').toUpperCase() === 'CONTAIN' ? t('report.phase_contain', 'Contain') : item.phase,
      owner: String(item.owner || '').toUpperCase() === 'USER OR SERVICE DESK' ? t('report.owner_user_service', 'User or service desk') : item.owner,
      action: actions[action] || (() => {
        if (!action.startsWith('Evidence to verify: ')) return action;
        const evidence = action.slice('Evidence to verify: '.length);
        const titles = {
          'Brand-like destination hostname': 'نام میزبان شبیه برند',
          'Suspicious link in email': 'پیوند مشکوک در ایمیل',
          'Urgency language detected': 'زبان فوریت‌ساز شناسایی شد',
          'Sensitive-action words in link': 'واژه‌های حساس در پیوند',
          'Unknown sender': 'فرستندهٔ ناشناس',
          'Requests verification code': 'درخواست کد تأیید',
          'Identity theft attempt': 'تلاش برای سرقت هویت',
          'Persian authority credential or payment lure': 'فریب با جعل نهاد فارسی و درخواست اعتبار یا پرداخت',
        };
        const title = Object.keys(titles).find((candidate) => evidence.startsWith(candidate));
        return `${t('report.evidence_to_verify', 'Evidence to verify:')} ${title ? `${titles[title]}${evidence.slice(title.length)}` : evidence}`;
      })(),
    };
  }
  function localizeIntegrityScope(value) {
    const canonical = 'Canonical casefile payload before this integrity field; fingerprint is not a digital signature.';
    return isPersian() && value === canonical ? t('report.integrity_scope', canonical) : value;
  }
  function localizeLimitation(value) {
    const translations = {
      'Evidence confidence describes collection coverage and cross-family agreement; it is not measured predictive accuracy.': t('report.limitation_confidence', 'Evidence confidence describes collection coverage and cross-family agreement; it is not measured predictive accuracy.'),
      'A casefile records this assessment only. It does not establish criminal attribution or external confirmation.': t('report.limitation_scope', 'A casefile records this assessment only. It does not establish criminal attribution or external confirmation.'),
    };
    return isPersian() ? (translations[value] || value) : value;
  }

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
    const copy = stateCopy();
    const [title, detail] = copy[state] || copy.complete;
    const style = state === 'blocked' ? 'border-red-300 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/30 dark:text-red-100' : state === 'limited' ? 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100' : 'border-aegis-200 bg-aegis-50 text-slate-900 dark:border-aegis-900 dark:bg-aegis-950/30 dark:text-slate-100';
    return `<section class="rounded-2xl border p-5 ${style}"><div class="flex flex-wrap items-start justify-between gap-4"><div><p class="text-sm font-semibold">${esc(title)}</p><p class="mt-1 max-w-3xl text-sm leading-6 opacity-90">${esc(detail)}</p></div>${badgeFor(data.classification.verdict)}</div></section>`;
  }
  function renderEvidence(items) {
    if (!items.length) return `<p class="text-sm text-slate-500">${t('report.no_evidence', 'No granular evidence was retained for this assessment.')}</p>`;
    return items.map((item) => `<article class="border-b border-slate-100 py-4 last:border-0 dark:border-slate-800"><div class="flex flex-wrap items-start justify-between gap-3"><div class="min-w-0 flex-1"><div class="flex flex-wrap items-center gap-2"><p class="font-medium">${esc(localizeObservation(item.title || item.code))}</p><span class="rounded px-2 py-0.5 text-[11px] font-semibold ${severityClass(item.severity)}">${esc(item.severity || 'info')}</span></div><p class="mt-1 text-sm text-slate-600 dark:text-slate-300">${esc(localizeObservation(item.description || 'Recorded scanner observation.'))}</p>${item.evidence ? `<p class="mt-2 break-all rounded bg-slate-50 px-2 py-1 font-mono text-xs text-slate-600 dark:bg-slate-950 dark:text-slate-300">${esc(item.evidence)}</p>` : ''}</div><div class="min-w-28 text-right text-xs text-slate-500"><p>${t('report.reliability', 'Reliability')} ${item.confidence !== null && item.confidence !== undefined ? `${Math.round(Number(item.confidence) * 100)}%` : '—'}</p><p class="mt-1 ${impactClass(Number(item.engine_impact || 0))}">${Number(item.engine_impact || 0) === 0 ? t('report.coverage_note', 'coverage note') : `${Number(item.engine_impact).toFixed(1)} ${Number(item.engine_impact) < 0 ? t('report.risk', 'risk') : t('report.protective', 'protective')}`}</p><p class="mt-1">${esc(localizeObservation(item.source || t('report.scanner_observation', 'scanner observation')))}</p></div></div></article>`).join('');
  }
  function renderFamilies(items) {
    return items.map((item) => `<div class="rounded-xl border border-slate-200 p-4 dark:border-slate-800"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${esc(item.family)}</p><p class="mt-2 text-xl font-bold ${impactClass(Number(item.net_impact))}">${Number(item.net_impact) === 0 ? t('report.neutral', 'Neutral') : `${Number(item.net_impact).toFixed(1)}`}</p><p class="mt-1 text-xs text-slate-500">${item.signals} ${t('report.signals', 'signals')} · ${t('report.net_contribution', 'net evidence contribution')}</p></div>`).join('') || `<p class="text-sm text-slate-500">${t('report.no_families', 'No evidence families were recorded.')}</p>`;
  }
  function renderPlaybook(items) {
    const completed = getCompleted();
    if (!items.length) return `<p class="text-sm text-slate-500">${t('report.no_action', 'No additional action was recorded for this case.')}</p>`;
    return `<div class="space-y-2">${items.map((rawItem, index) => { const item = localizePlaybook(rawItem); return `<label class="flex cursor-pointer gap-3 rounded-xl border border-slate-200 p-3 transition hover:border-aegis-400 dark:border-slate-800"><input class="case-step mt-1 rounded accent-aegis-600" type="checkbox" data-step="${index}" ${completed.has(index) ? 'checked' : ''}><span><span class="block text-xs font-semibold uppercase tracking-wide text-aegis-700 dark:text-aegis-300">${esc(item.phase)} · ${esc(item.owner)}</span><span class="mt-1 block text-sm">${esc(item.action)}</span></span></label>`; }).join('')}</div><p class="mt-3 text-xs text-slate-500">${t('report.local_completion', 'Completion is stored only in this browser; it does not modify the casefile or report an outcome.')}</p>`;
  }
  function render(data) {
    casefile = data;
    const c = data.classification || {};
    const limited = c.assessment_state === 'limited';
    const score = limited ? '—' : `${c.trust_score ?? '—'}<span class="text-lg">/100</span>`;
    const confidence = c.evidence_confidence !== null && c.evidence_confidence !== undefined ? `${Math.round(Number(c.evidence_confidence) * 100)}%` : '—';
    const box = document.getElementById('report-content');
    box.innerHTML = `<div class="space-y-6">${statePanel(data)}
      <section class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:grid-cols-[1fr_auto]"><div><p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">${t('report.case', 'Case')} ${esc(data.case_id)}</p><p class="mt-3 break-all font-mono text-sm">${esc(data.target || '')}</p><p class="mt-2 text-sm text-slate-500">${t(`dashboard.scan_type_${data.scan_type}`, data.scan_type || t('report.content', 'content'))} ${t('report.assessment', 'assessment')} · ${data.created_at ? esc(new Date(data.created_at).toLocaleString()) : t('report.time_unavailable', 'time unavailable')}</p><p class="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">${esc(localizeSummary(data.report_summary || ''))}</p></div><div class="min-w-44 text-right"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${limited ? t('report.coverage', 'Coverage') : t('scan.trust_score', 'Trust score')}</p><p class="mt-2 font-mono text-5xl font-bold ${limited ? 'text-slate-500' : Number(c.trust_score) >= 70 ? 'text-emerald-500' : Number(c.trust_score) >= 40 ? 'text-amber-500' : 'text-red-500'}">${score}</p><p class="mt-2 text-xs text-slate-500">${t('scan.evidence_confidence', 'Evidence confidence')} ${confidence}</p></div></section>
      <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">${renderFamilies(data.evidence_families || [])}</section>
      <section class="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]"><div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><div class="flex items-center justify-between gap-3"><h2 class="text-lg font-semibold">${t('report.evidence_chain', 'Evidence chain')}</h2><span class="text-xs text-slate-500">${(data.evidence || []).length} ${t('report.observations', 'recorded observations')}</span></div><div class="mt-3">${renderEvidence(data.evidence || [])}</div></div><div class="space-y-6"><section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">${t('report.response_playbook', 'Response playbook')}</h2><p class="mt-1 text-sm text-slate-500">${t('report.prioritize_containment', 'Prioritize containment before further interaction.')}</p><div class="mt-4">${renderPlaybook(data.response_playbook || [])}</div></section><section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">${t('report.scope', 'Scope & provenance')}</h2><dl class="mt-4 space-y-3 text-sm"><div><dt class="text-slate-500">${t('report.engine', 'Engine')}</dt><dd class="font-mono">${esc(c.engine || 'evidence-fusion-v2')}</dd></div><div><dt class="text-slate-500">${t('report.network_acquisition', 'Network acquisition')}</dt><dd>${esc(data.provenance?.network_acquisition || 'not applicable')}</dd></div><div><dt class="text-slate-500">${t('report.external_intelligence', 'External intelligence')}</dt><dd>${(data.provenance?.external_intelligence || []).length ? (data.provenance.external_intelligence || []).map(esc).join(', ') : t('report.no_feed_match', 'No external feed match recorded')}</dd></div></dl><details class="mt-5 rounded-lg bg-slate-50 p-3 text-xs dark:bg-slate-950"><summary class="cursor-pointer font-semibold">${t('report.integrity', 'Integrity fingerprint')}</summary><p class="mt-2 break-all font-mono text-slate-600 dark:text-slate-300">${esc(data.integrity?.fingerprint || '')}</p><p class="mt-2 text-slate-500">${esc(localizeIntegrityScope(data.integrity?.scope || ''))}</p></details></section></div></section>
      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">${t('report.limitations', 'Assessment limitations')}</h2><ul class="mt-3 space-y-2">${(data.limitations || []).map((item) => `<li class="flex gap-2 text-sm text-slate-600 dark:text-slate-300"><span class="text-aegis-500">•</span><span>${esc(localizeLimitation(item))}</span></li>`).join('')}</ul></section>
    </div>`;
    document.querySelectorAll('.case-step').forEach((input) => input.addEventListener('change', () => { const completed = getCompleted(); const id = Number(input.dataset.step); input.checked ? completed.add(id) : completed.delete(id); setCompleted(completed); }));
  }
  function exportJson() {
    if (!casefile) return;
    const blob = new Blob([JSON.stringify(casefile, null, 2)], { type: 'application/json' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${casefile.case_id || 'aegis-casefile'}.json`; link.click(); URL.revokeObjectURL(link.href);
  }
  window.Aegis.onPageLoad('report', async () => {
    if (!scanId) return;
    try {
      const data = await api('GET', `/api/v1/scans/${scanId}/casefile`);
      render(data);
      document.getElementById('report-meta').textContent = `${t(`dashboard.scan_type_${data.scan_type}`, data.scan_type || t('report.content', 'content'))} ${t('report.assessment', 'assessment')} · ${data.case_id} · ${t('report.evidence_first_record', 'evidence-first record')}`;
    } catch (error) { document.getElementById('report-content').innerHTML = `<div class="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">${esc(error.message)}</div>`; }
    document.getElementById('casefile-json-btn')?.addEventListener('click', exportJson);
    document.getElementById('pdf-btn')?.addEventListener('click', () => { window.location.href = `/api/v1/scans/${scanId}/report.pdf`; });
    document.getElementById('share-btn')?.addEventListener('click', async () => { try { await navigator.clipboard.writeText(window.location.href); toast(t('report.link_copied', 'Case link copied'), 'success'); } catch (_) { toast(t('report.link_copy_failed', 'Could not copy link'), 'error'); } });
  });
})();
