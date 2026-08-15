/* Assessment casefile: derives only from the authorized persisted scan record. */
(function () {
  'use strict';
  const shared = window.Aegis;
  if (!shared) {
    window.addEventListener('aegis:ready', () => window.location.reload(), { once: true });
    return;
  }
  const { api, esc, badgeFor, toast, t } = shared;
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
      'Requests verification code': 'درخواست کد تأیید', 'Identity theft attempt': 'تلاش برای سرقت هویت',
      'Poor grammar / broken language': 'نگارش نامتعارف یا ناقص', 'Account verification request': 'درخواست تأیید حساب',
      'Requests password': 'درخواست گذرواژه', 'Fear tactics detected': 'تاکتیک‌های ترساننده شناسایی شد',
      'Government impersonation': 'جعل هویت نهاد دولتی', 'Bank impersonation': 'جعل هویت بانک',
      'Money transfer request': 'درخواست انتقال پول', 'Remote access request': 'درخواست دسترسی از راه دور',
      'Social engineering': 'مهندسی اجتماعی', 'Persian authority credential or payment lure': 'فریب با جعل نهاد فارسی و درخواست اعتبار یا پرداخت',
      'Persian delivery-fee lure': 'فریب هزینهٔ تحویل فارسی', 'Persian benefit-claim lure': 'فریب مطالبهٔ مزایای عمومی فارسی',
      'Persian legal-case pressure lure': t('report.title_persian_legal_case', 'Persian legal-case pressure lure'), 'Persian legal attachment lure': t('report.title_persian_legal_attachment', 'Persian legal attachment lure'),
      'Persian familiar-person transfer lure': t('report.title_persian_familiar_transfer', 'Persian familiar-person transfer lure'), 'Persian deferred-repayment pressure': t('report.title_persian_deferred_repayment', 'Persian deferred-repayment pressure'),
      'Persian invoice-pressure lure': t('report.title_persian_invoice', 'Persian invoice-pressure lure'), 'Persian executive-transfer lure': t('report.title_persian_executive_transfer', 'Persian executive-transfer lure'),
      'Persian support-callback lure': t('report.title_persian_support_callback', 'Persian support-callback lure'), 'Persian investment-return lure': t('report.title_persian_investment_return', 'Persian investment-return lure'),
      'Persian reward-fee lure': t('report.title_persian_reward_fee', 'Persian reward-fee lure'), 'Persian job-document lure': t('report.title_persian_job_document', 'Persian job-document lure'),
      'Persian service-cutoff lure': t('report.title_persian_service_cutoff', 'Persian service-cutoff lure'), 'Persian bank-lockout lure': t('report.title_persian_bank_lockout', 'Persian bank-lockout lure'),
      'Persian stranded-friend transfer lure': t('report.title_persian_stranded_friend', 'Persian stranded-friend transfer lure'), 'Persian beta-access payment lure': t('report.title_persian_beta_payment', 'Persian beta-access payment lure'),
      'A purported case filed against the recipient is paired with a final-warning pressure cue.': t('report.desc_persian_legal_case', 'A purported case filed against the recipient is paired with a final-warning pressure cue.'),
      'A purported legal case directs the recipient to tracking or an attachment, a common delivery lure.': t('report.desc_persian_legal_attachment', 'A purported legal case directs the recipient to tracking or an attachment, a common delivery lure.'),
      'An alleged card-limit problem is used to ask the recipient to move money for another person.': t('report.desc_persian_familiar_transfer', 'An alleged card-limit problem is used to ask the recipient to move money for another person.'),
      'A money-transfer request is paired with a promise to repay later, a common impersonation pretext.': t('report.desc_persian_deferred_repayment', 'A money-transfer request is paired with a promise to repay later, a common impersonation pretext.'),
      'An overdue invoice claim is paired with an immediate payment or legal-pressure demand.': t('report.desc_persian_invoice', 'An overdue invoice claim is paired with an immediate payment or legal-pressure demand.'),
      'A claimed executive requests a confidential money transfer without independent confirmation.': t('report.desc_persian_executive_transfer', 'A claimed executive requests a confidential money transfer without independent confirmation.'),
      'A technical-security warning directs the recipient to call an unverified support number.': t('report.desc_persian_support_callback', 'A technical-security warning directs the recipient to call an unverified support number.'),
      'An investment pitch claims recurring or guaranteed returns while soliciting capital.': t('report.desc_persian_investment_return', 'An investment pitch claims recurring or guaranteed returns while soliciting capital.'),
      'A prize or reward claim requires an advance processing or administrative fee.': t('report.desc_persian_reward_fee', 'A prize or reward claim requires an advance processing or administrative fee.'),
      'A job approach requests identity or banking documents before a verified hiring process.': t('report.desc_persian_job_document', 'A job approach requests identity or banking documents before a verified hiring process.'),
      'A utility, telecom, or insurance cutoff notice directs an immediate payment or link action.': t('report.desc_persian_service_cutoff', 'A utility, telecom, or insurance cutoff notice directs an immediate payment or link action.'),
      'A claimed bank account lockout requests identity verification through message-provided details or a link.': t('report.desc_persian_bank_lockout', 'A claimed bank account lockout requests identity verification through message-provided details or a link.'),
      'A familiar-person emergency abroad is paired with a money transfer and repayment promise.': t('report.desc_persian_stranded_friend', 'A familiar-person emergency abroad is paired with a money transfer and repayment promise.'),
      'A beta-access invitation requests payment details before providing access.': t('report.desc_persian_beta_payment', 'A beta-access invitation requests payment details before providing access.'),
      'The message asks you to verify your account through a provided link.': 'پیام از شما می‌خواهد حساب خود را از طریق پیوندی که خودش ارائه کرده تأیید کنید.',
      'The message manipulates you using emotion, urgency, or authority.': 'پیام با احساسات، فوریت یا ادعای اختیار تلاش می‌کند شما را به اقدام وادار کند.',
      'The message asks for a verification or one-time code.': 'این پیام کد تأیید یا رمز یک‌بارمصرف درخواست می‌کند.',
      'The message asks for personal documents or data that can be used to steal your identity.': 'این پیام مدارک یا اطلاعات شخصیِ قابل‌استفاده برای سرقت هویت درخواست می‌کند.',
      'The message has language problems typical of bulk scam messages.': 'متن پیام نشانه‌هایی از نگارش نامتعارفِ رایج در پیام‌های انبوه کلاهبرداری دارد.',
      'HTTPS enabled': t('report.title_https', 'HTTPS enabled'), 'Valid SSL certificate': t('report.title_ssl_valid', 'Valid SSL certificate'), 'TLS certificate could not be verified': t('report.title_tls_limited', 'TLS certificate check unavailable'),
      'Long-established domain': t('report.title_domain_very_old', 'Long-established domain'), 'Established domain': t('report.title_domain_old', 'Established domain'),
      'No scam patterns found': t('report.title_no_scam_patterns', 'No scam patterns found'),
      'The site is served over an encrypted HTTPS connection.': t('report.desc_https', 'The site is served over an encrypted HTTPS connection.'),
      'The SSL certificate is currently valid.': t('report.desc_ssl_valid', 'The SSL certificate is currently valid.'),
      'AEGIS could not complete the certificate check for this destination. This is a coverage limitation, not evidence of a threat.': t('report.desc_tls_limited', 'The TLS certificate check could not be completed. This limits coverage and is not evidence of a threat.'),
      'The SSL certificate is valid and trusted.': t('report.desc_ssl_valid', 'The SSL certificate is valid and trusted.'),
      'The domain was registered more than five years ago, which is a positive trust signal.': t('report.desc_domain_very_old', 'The domain was registered more than five years ago, which is a positive trust signal.'),
      'The domain was registered for more than a year.': t('report.desc_domain_old', 'The domain was registered for more than a year.'),
      'No recognized scam patterns were found in the collected evidence.': t('report.desc_no_scam_patterns', 'No recognized scam patterns were found in the collected evidence.'),
      'url_observation': t('report.source_url_observation', 'url_observation'), 'tls_observation': t('report.source_tls_observation', 'tls_observation'),
      'content_semantics': t('report.source_content_semantics', 'content_semantics'), 'page_or_request': t('report.source_page_or_request', 'page_or_request'),
      'heuristic': t('report.source_heuristic', 'heuristic'), 'pattern': 'الگو',
    };
    return translations[text] || text;
  }
  function localizeSeverity(value) {
    if (!isPersian()) return value;
    return ({ critical: 'بحرانی', high: 'بالا', medium: 'متوسط', low: 'پایین', info: 'اطلاع‌رسانی', safe: 'ایمن' })[String(value || '').toLowerCase()] || value;
  }
  function localizeFamily(value) {
    if (!isPersian()) return value;
    return ({ transport: 'امنیت انتقال', site_reputation: 'اعتبار مقصد', identity: 'هویت و جعل', link_delivery: 'تحویل پیوند', requested_action: 'درخواست اقدام', social_engineering: 'مهندسی اجتماعی', page_behavior: 'رفتار صفحه', email_authentication: 'اعتبارسنجی ایمیل', fraud: 'کلاه‌برداری', impersonation: 'جعل هویت', manipulation: 'دست‌کاری روانی', otp: 'کد یک‌بارمصرف', credential: 'اعتبارنامه', analysis: 'تحلیل محتوا', obfuscation: 'پنهان‌سازی', reputation: 'اعتبار مقصد', security: 'ایمنی', code: 'کد و اسکریپت' })[String(value || '').toLowerCase()] || value;
  }
  function localizeNetworkAcquisition(value) {
    if (!isPersian()) return value;
    return ({ acquired: 'انجام شد', completed: 'انجام شد', blocked: 'مسدودشده', not_attempted: 'انجام‌نشده', 'not applicable': 'کاربرد ندارد' })[String(value || '').toLowerCase()] || value;
  }
  function formatAssessmentTime(value) {
    if (!value) return t('report.time_unavailable', 'time unavailable');
    return new Date(value).toLocaleString(isPersian() ? 'fa-IR' : undefined);
  }
  function localizeSummary(value) {
    if (!isPersian()) return value;
    const match = String(value || '').match(/^The (.+?) (appears to be safe\.|shows some warning signs\.|shows strong signs of a scam\.|is very likely a scam\.) Trust score ([\d.]+)\/100, estimated risk (\d+)%, evidence confidence (\d+)%\.$/);
    if (!match) return value;
    const labels = { website: 'وب‌سایت', url: 'نشانی وب', email: 'ایمیل', message: 'پیام', text: 'پیام', screenshot: 'تصویر', image: 'تصویر', 'qr code': 'کد QR', qr: 'کد QR', file: 'فایل', content: 'محتوا' };
    const label = labels[match[1].toLowerCase()] || match[1];
    const keys = { 'appears to be safe.': 'report.summary_safe', 'shows some warning signs.': 'report.summary_medium', 'shows strong signs of a scam.': 'report.summary_high', 'is very likely a scam.': 'report.summary_critical' };
    const finding = t(keys[match[2]], match[2]).replace('{type}', label);
    return `${finding} ${t('scan.trust_score', 'Trust score')} ${match[3]}/100، ${t('report.estimated_risk', 'estimated risk')} ${match[4]}٪، ${t('scan.evidence_confidence', 'Evidence confidence')} ${match[5]}٪.`;
  }
  function localizePlaybook(item) {
    if (!isPersian()) return item;
    const action = String(item.action || '');
    const actions = {
      'Stop interacting with this content. It has multiple independent signs of a likely scam or a verified threat match.': t('report.action_stop', 'Stop interacting with this content. It has multiple independent signs of a likely scam or a verified threat match.'),
      'Block and report the sender or URL. If financial or account data was shared, contact the legitimate provider immediately.': t('report.action_block', 'Block and report the sender or URL. If financial or account data was shared, contact the legitimate provider immediately.'),
      'Change exposed passwords and revoke active sessions from a trusted device.': t('report.action_passwords', 'Change exposed passwords and revoke active sessions from a trusted device.'),
      'No high-risk evidence was observed. This is not proof of safety; verify the sender or destination independently before sharing sensitive information.': t('report.action_low_evidence', 'No high-risk evidence was observed. This is not proof of safety; verify the sender or destination independently before sharing sensitive information.'),
      'Use a password manager and multi-factor authentication for important accounts.': t('report.action_low_hardening', 'Use a password manager and multi-factor authentication for important accounts.'),
      'Treat this as unverified. Do not use message-provided links, phone numbers, or contact details to validate it.': t('report.action_unverified', 'Treat this as unverified. Do not use message-provided links, phone numbers, or contact details to validate it.'),
      'Verify the request through a known official website, app, or an independent contact channel.': t('report.action_verify_official', 'Verify the request through a known official website, app, or an independent contact channel.'),
      'Do not click links, open attachments, reply, or provide credentials or payment information.': 'روی پیوندها کلیک نکنید، پیوست‌ها را باز نکنید، پاسخ ندهید و اطلاعات ورود یا پرداخت ارائه نکنید.',
      'Verify the claimed organization independently and report the message or site through its official channel.': 'سازمان ادعاشده را مستقل بررسی کنید و پیام یا وب‌سایت را از کانال رسمی آن گزارش دهید.',
      'If information was already shared, change affected credentials and contact the real service immediately.': t('report.action_shared_info', 'If information was already shared, change affected credentials and contact the real service immediately.'),
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
          'Persian legal-case pressure lure': t('report.title_persian_legal_case', 'Persian legal-case pressure lure'), 'Persian legal attachment lure': t('report.title_persian_legal_attachment', 'Persian legal attachment lure'),
          'Persian familiar-person transfer lure': t('report.title_persian_familiar_transfer', 'Persian familiar-person transfer lure'), 'Persian deferred-repayment pressure': t('report.title_persian_deferred_repayment', 'Persian deferred-repayment pressure'),
          'Persian invoice-pressure lure': t('report.title_persian_invoice', 'Persian invoice-pressure lure'), 'Persian executive-transfer lure': t('report.title_persian_executive_transfer', 'Persian executive-transfer lure'),
          'Persian support-callback lure': t('report.title_persian_support_callback', 'Persian support-callback lure'), 'Persian investment-return lure': t('report.title_persian_investment_return', 'Persian investment-return lure'),
          'Persian reward-fee lure': t('report.title_persian_reward_fee', 'Persian reward-fee lure'), 'Persian job-document lure': t('report.title_persian_job_document', 'Persian job-document lure'),
          'Persian service-cutoff lure': t('report.title_persian_service_cutoff', 'Persian service-cutoff lure'), 'Persian bank-lockout lure': t('report.title_persian_bank_lockout', 'Persian bank-lockout lure'),
          'Persian stranded-friend transfer lure': t('report.title_persian_stranded_friend', 'Persian stranded-friend transfer lure'), 'Persian beta-access payment lure': t('report.title_persian_beta_payment', 'Persian beta-access payment lure'),
        };
        const title = Object.keys(titles).find((candidate) => evidence.startsWith(candidate));
        return `${t('report.evidence_to_verify', 'Evidence to verify:')} ${title ? `${titles[title]}${evidence.slice(title.length)}` : evidence}`;
      })(),
    };
  }
  function localizeHighlight(value) {
    if (!isPersian()) return value;
    return ({ 'No high-risk evidence observed': t('report.highlight_no_high_risk', 'No high-risk evidence observed'), 'Assessment confidence is limited by available evidence': t('report.highlight_limited_confidence', 'Assessment confidence is limited by available evidence') })[String(value || '')] || localizeObservation(value);
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
    return items.map((item) => `<article class="border-b border-slate-100 py-4 last:border-0 dark:border-slate-800"><div class="flex flex-wrap items-start justify-between gap-3"><div class="min-w-0 flex-1"><div class="flex flex-wrap items-center gap-2"><p class="font-medium">${esc(localizeObservation(item.title || item.code))}</p><span class="rounded px-2 py-0.5 text-[11px] font-semibold ${severityClass(item.severity)}">${esc(localizeSeverity(item.severity || 'info'))}</span></div><p class="mt-1 text-sm text-slate-600 dark:text-slate-300">${esc(localizeObservation(item.description || 'Recorded scanner observation.'))}</p>${item.evidence ? `<p class="aegis-evidence-value mt-2 break-all rounded px-2 py-1 font-mono text-xs">${esc(item.evidence)}</p>` : ''}</div><div class="min-w-28 text-right text-xs text-slate-500"><p>${t('report.reliability', 'Reliability')} ${item.confidence !== null && item.confidence !== undefined ? `${Math.round(Number(item.confidence) * 100)}%` : '—'}</p><p class="mt-1 ${impactClass(Number(item.engine_impact || 0))}">${Number(item.engine_impact || 0) === 0 ? t('report.coverage_note', 'coverage note') : `${Number(item.engine_impact).toFixed(1)} ${Number(item.engine_impact) < 0 ? t('report.risk', 'risk') : t('report.protective', 'protective')}`}</p><p class="mt-1">${esc(localizeObservation(item.source || t('report.scanner_observation', 'scanner observation')))}</p></div></div></article>`).join('');
  }
  function renderFamilies(items) {
    return items.map((item) => `<div class="rounded-xl border border-slate-200 p-4 dark:border-slate-800"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${esc(localizeFamily(item.family))}</p><p class="mt-2 text-xl font-bold ${impactClass(Number(item.net_impact))}">${Number(item.net_impact) === 0 ? t('report.neutral', 'Neutral') : `${Number(item.net_impact).toFixed(1)}`}</p><p class="mt-1 text-xs text-slate-500">${item.signals} ${t('report.signals', 'signals')} · ${t('report.net_contribution', 'net evidence contribution')}</p></div>`).join('') || `<p class="text-sm text-slate-500">${t('report.no_families', 'No evidence families were recorded.')}</p>`;
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
      <section class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:grid-cols-[1fr_auto]"><div><p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">${t('report.case', 'Case')} ${esc(data.case_id)}</p><p class="mt-3 break-all font-mono text-sm">${esc(data.target || '')}</p><p class="mt-2 text-sm text-slate-500">${t(`dashboard.scan_type_${data.scan_type}`, data.scan_type || t('report.content', 'content'))} ${t('report.assessment', 'assessment')} · ${esc(formatAssessmentTime(data.created_at))}</p><p class="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">${esc(localizeSummary(data.report_summary || ''))}</p></div><div class="min-w-44 text-right"><p class="text-xs font-semibold uppercase tracking-wide text-slate-500">${limited ? t('report.coverage', 'Coverage') : t('scan.trust_score', 'Trust score')}</p><p class="mt-2 font-mono text-5xl font-bold ${limited ? 'text-slate-500' : Number(c.trust_score) >= 70 ? 'text-emerald-500' : Number(c.trust_score) >= 40 ? 'text-amber-500' : 'text-red-500'}">${score}</p><p class="mt-2 text-xs text-slate-500">${t('scan.evidence_confidence', 'Evidence confidence')} ${confidence}</p></div></section>
      <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">${renderFamilies(data.evidence_families || [])}</section>
      <section class="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]"><div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><div class="flex items-center justify-between gap-3"><h2 class="text-lg font-semibold">${t('report.evidence_chain', 'Evidence chain')}</h2><span class="text-xs text-slate-500">${(data.evidence || []).length} ${t('report.observations', 'recorded observations')}</span></div><div class="mt-3">${renderEvidence(data.evidence || [])}</div></div><div class="space-y-6"><section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">${t('report.response_playbook', 'Response playbook')}</h2><p class="mt-1 text-sm text-slate-500">${t('report.prioritize_containment', 'Prioritize containment before further interaction.')}</p><div class="mt-4">${renderPlaybook(data.response_playbook || [])}</div></section><section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"><h2 class="text-lg font-semibold">${t('report.scope', 'Scope & provenance')}</h2><dl class="mt-4 space-y-3 text-sm"><div><dt class="text-slate-500">${t('report.engine', 'Engine')}</dt><dd class="font-mono">${esc(c.engine || 'evidence-fusion-v2')}</dd></div><div><dt class="text-slate-500">${t('report.network_acquisition', 'Network acquisition')}</dt><dd>${esc(localizeNetworkAcquisition(data.provenance?.network_acquisition || 'not applicable'))}</dd></div><div><dt class="text-slate-500">${t('report.external_intelligence', 'External intelligence')}</dt><dd>${(data.provenance?.external_intelligence || []).length ? (data.provenance.external_intelligence || []).map(esc).join(', ') : t('report.no_feed_match', 'No external feed match recorded')}</dd></div></dl><details class="mt-5 rounded-lg bg-slate-50 p-3 text-xs dark:bg-slate-950"><summary class="cursor-pointer font-semibold">${t('report.integrity', 'Integrity fingerprint')}</summary><p class="mt-2 break-all font-mono text-slate-600 dark:text-slate-300">${esc(data.integrity?.fingerprint || '')}</p><p class="mt-2 text-slate-500">${esc(localizeIntegrityScope(data.integrity?.scope || ''))}</p></details></section></div></section>
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
