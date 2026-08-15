(function () {
  'use strict';

  const translations = {
    fa: {
      'nav.dashboard': 'داشبورد',
      'nav.scan': 'تحلیل‌گر اسکن',
      'nav.map': 'نقشه تهدید',
      'nav.learn': 'مرکز آموزش',
      'nav.profile': 'پروفایل من',
      'nav.admin': 'پنل مدیریت',
      'header.search': 'جست‌وجوی اسکن‌ها و تهدیدها…',
      'header.language': 'زبان',
      'header.theme': 'تغییر پوسته',
      'header.notifications': 'اعلان‌ها',
      'header.logout': 'خروج',
      'footer.product': 'پلتفرم اعتماد دیجیتال و تحلیل کلاه‌برداری AEGIS',
      'footer.engine': 'ترکیب قطعی شواهد · بدون آموزش مدل',
      'scan.eyebrow': 'ارزیابی مبتنی بر شواهد',
      'scan.title': 'تحلیل‌گر اسکن',
      'scan.description': 'یک پیوند، ایمیل، پیام، تصویر، کد QR یا فایل را بررسی کنید. AEGIS شواهد قابل مشاهده را ترکیب می‌کند، از اثرگذاریِ بیش از حد سیگنال‌های تکراری جلوگیری می‌کند و دلیل نتیجه را شفاف نشان می‌دهد.',
      'scan.prediction_path': 'مسیر پیش‌بینی',
      'scan.no_training': 'بدون آموزش مدل',
      'scan.load_demo': 'بارگیری دمو',
      'scan.collect': '۱. گردآوری',
      'scan.collect_desc': 'پیوندها، نشانه‌های فرستنده، سرنخ‌های محتوا و مشاهدات فنی استخراج می‌شوند.',
      'scan.correlate': '۲. هم‌بستگی',
      'scan.correlate_desc': 'نشانه‌های تکراری کم‌اثر می‌شوند و توافق خانواده‌های مستقلِ شواهد برجسته می‌شود.',
      'scan.explain': '۳. توضیح',
      'scan.explain_desc': 'به‌جای یک برچسب جعبه‌سیاه، دلایل کالیبره، پوشش و اقدام‌های بعدی نمایش داده می‌شوند.',
      'scan.url': 'پیوند',
      'scan.email': 'ایمیل',
      'scan.message': 'پیام',
      'scan.image': 'تصویر',
      'scan.qr': 'کد QR',
      'scan.file': 'فایل',
      'scan.enter_url': 'نشانی وب برای تحلیل',
      'scan.unsafe_destinations': 'مقصدهای خصوصی، رزروشده و غیروبی هرگز دریافت نمی‌شوند.',
      'scan.analyze': 'تحلیل',
      'scan.subject': 'موضوع',
      'scan.sender': 'نشانی فرستنده',
      'scan.message_body': 'متن پیام',
      'scan.raw_headers': 'سرآیندهای خام (اختیاری)',
      'scan.paste_message': 'پیامی را برای تحلیل وارد کنید',
      'scan.local_text': 'متن و پیوندهای درون آن در مسیر ارزیابی محلی می‌مانند.',
      'scan.upload_image': 'یک تصویر بارگذاری کنید',
      'scan.upload_qr': 'تصویر کد QR را بارگذاری کنید',
      'scan.upload_file': 'یک سند بارگذاری کنید',
      'scan.drop_image': 'تصویر را اینجا رها کنید یا مرور کنید',
      'scan.drop_qr': 'کد QR را اینجا رها کنید یا مرور کنید',
      'scan.drop_file': 'یک فایل PDF، TXT، EML یا MSG را اینجا رها کنید یا مرور کنید',
      'scan.static_validation': 'فایل‌ها پیش از تحلیل به‌صورت ایستا اعتبارسنجی می‌شوند و هرگز اجرا نمی‌شوند.',
      'scan.copy_evidence': 'کپی خلاصه شواهد',
      'scan.open_casefile': 'باز کردن پرونده ارزیابی',
      'scan.submit_review': 'ارسال برای بررسی تهدید',
      'scan.download_pdf': 'دانلود گزارش (PDF)',
      'scan.new_scan': 'اسکن جدید',
      'scan.moderation_note': 'ارسال‌های تهدید برای تعدیل صف‌بندی می‌شوند و خودکار به دادهٔ نقشه یا اطلاعات تهدید عمومی تبدیل نخواهند شد.',
      'scan.feedback_title': 'آیا این ارزیابی با چیزی که بررسی کردید مطابقت داشت؟',
      'scan.feedback_desc': 'نتیجهٔ شما جدا از موتور ثبت می‌شود و از بررسی کیفیت پشتیبانی می‌کند؛ AEGIS را خودکار بازآموزی نمی‌دهد.',
      'scan.confirmed_malicious': 'بدخواه بودن تأیید شد',
      'scan.confirmed_benign': 'بی‌خطر بودن تأیید شد',
      'scan.not_sure': 'مطمئن نیستم',
      'scan.analyzing': 'در حال تحلیل…',
      'scan.enter_url_error': 'یک نشانی وب برای تحلیل وارد کنید',
      'scan.enter_email_error': 'موضوع یا متن ایمیل را وارد کنید',
      'scan.enter_message_error': 'پیامی را برای تحلیل وارد کنید',
      'scan.choose_file_error': 'فایلی را برای تحلیل انتخاب کنید',
      'scan.failure': 'اسکن کامل نشد',
      'scan.demo_loaded': 'دموی ساختگیِ فریبِ دریافت اعتبار بارگذاری شد. شواهد را بررسی کنید و سپس «تحلیل» را انتخاب کنید.',
      'scan.limited_title': 'ارزیابی محدود',
      'scan.limited_body': 'بررسی‌های راه‌دور انجام نشدند، زیرا مقصد قابل حل نبود. این موضوع نه بدخواه بودن و نه بی‌خطر بودن مقصد را ثابت نمی‌کند.',
      'scan.blocked_title': 'مرز ایمنی اعمال شد',
      'scan.blocked_body': 'AEGIS از بررسی این مقصد خودداری کرد، زیرا خصوصی، رزروشده، نادرست یا خارج از مرز امن تحلیل وب است. بررسی آن از این سرویس ایمن نیست.',
      'scan.complete_title': 'ارزیابی تکمیل شد',
      'scan.complete_body': 'دلایل نمایش‌داده‌شده، شواهدی هستند که AEGIS توانسته گردآوری کند. اطمینان، پوشش و توافق را توصیف می‌کند، نه تضمین را.',
      'scan.coverage_note': 'یادداشت پوشش · بدون اثر در امتیاز',
      'scan.risk_weight': 'وزن خطر',
      'scan.protective_weight': 'وزن محافظتی',
      'scan.reliability': 'قابلیت اتکای شواهد',
      'scan.not_stored': 'نتیجه ذخیره نشد',
      'scan.saved_history': 'در تاریخچهٔ اسکن ذخیره شد',
      'scan.storage_unknown': 'وضعیت ذخیره‌سازی در دسترس نیست',
      'scan.coverage_limited': 'پوشش محدود',
      'scan.trust_score': 'امتیاز اعتماد',
      'scan.target': 'مقصد',
      'scan.evidence_confidence': 'اطمینان از شواهد',
      'scan.evidence_reviewed': 'شواهد بررسی‌شده',
      'scan.no_evidence': 'شواهد مشخصی در دسترس نبود.',
      'scan.recommendations': 'گام‌های پیشنهادی بعدی',
      'scan.no_action': 'اقدام دیگری پیشنهاد نمی‌شود.',
      'scan.highlights': 'نکات برجستهٔ شواهد',
      'scan.copied': 'خلاصهٔ شواهد کپی شد',
      'scan.clipboard_unavailable': 'دسترسی به کلیپ‌بورد در دسترس نیست',
      'scan.submitted': 'برای تعدیل ارسال شد',
      'scan.only_stored': 'فقط اسکن‌های ذخیره‌شده می‌توانند بازخورد نتیجه دریافت کنند',
      'scan.outcome_recorded': 'نتیجه ثبت شد',
      'scan.thanks': 'سپاسگزاریم. نتیجهٔ شما جداگانه برای بررسی کیفیت ثبت شد.',
      'verdict.safe': 'ایمن',
      'verdict.suspicious': 'مشکوک',
      'verdict.threat': 'تهدید',
      'verdict.unverified': 'تأییدنشده',
      'profile.account': 'حساب کاربری',
      'profile.title': 'پروفایل و ترجیحات',
      'profile.description': 'نحوهٔ نمایش، نگهداری و اطلاع‌رسانی AEGIS دربارهٔ ارزیابی‌های امنیتی خود را کنترل کنید.',
      'profile.username': 'نام کاربری',
      'profile.email': 'ایمیل',
      'profile.display_name': 'نام نمایشی',
      'profile.optional_name': 'نام نمایشی اختیاری',
      'profile.save_profile': 'ذخیرهٔ پروفایل',
      'profile.privacy_display': 'حریم خصوصی، اعلان‌ها و نمایش',
      'profile.privacy_description': 'یک اسکن فقط زمانی نگهداری می‌شود که ذخیره‌سازی تاریخچه را انتخاب کنید. ارسال عمومی تهدید همیشه اقدامی صریح برای هر اسکن است و تعدیل می‌شود.',
      'profile.language_layout': 'زبان و چیدمان',
      'profile.rtl_note': 'انتخاب از سربرگ بلافاصله پس از ذخیره و بارگیری مجدد اعمال می‌شود.',
      'profile.theme': 'پوستهٔ رنگ',
      'profile.data_accessibility': 'داده و دسترس‌پذیری',
      'profile.save_history': 'ذخیرهٔ تاریخچهٔ اسکن من',
      'profile.history_description': 'در حالت خاموش، اسکن‌های خصوصی تکمیل‌شده به شما نمایش داده می‌شوند، اما در AEGIS نگهداری نمی‌شوند.',
      'profile.high_contrast': 'کنتراست بالا',
      'profile.contrast_description': 'کنتراست بصری رابط را افزایش دهید.',
      'profile.notifications': 'اعلان‌ها',
      'profile.email_notifications': 'اعلان‌های ایمیل',
      'profile.in_app_notifications': 'اعلان‌های درون‌برنامه‌ای',
      'profile.threat_alerts': 'هشدارهای تهدید و خطر بالا',
      'profile.save_preferences': 'ذخیرهٔ ترجیحات',
      'profile.change_password': 'تغییر گذرواژه',
      'profile.current_password': 'گذرواژهٔ فعلی',
      'profile.new_password': 'گذرواژهٔ جدید',
      'profile.confirm_password': 'تأیید گذرواژه',
      'profile.update_password': 'به‌روزرسانی گذرواژه',
      'profile.load_failed': 'بارگذاری ترجیحات انجام نشد',
      'profile.saved': 'پروفایل ذخیره شد',
      'profile.preferences_saved': 'ترجیحات ذخیره شد. برای اعمال زبان جدید، صفحه را بارگیری مجدد کنید.',
      'profile.password_mismatch': 'گذرواژه‌های جدید یکسان نیستند',
      'profile.password_updated': 'گذرواژه به‌روزرسانی شد',
      'profile.danger_zone': 'بخش حساس',
      'profile.delete_description': 'حساب کاربری و همهٔ داده‌های اسکن ذخیره‌شده را برای همیشه حذف کنید. این عمل قابل بازگشت نیست.',
      'profile.delete_account': 'حذف حساب کاربری من',
      'profile.delete_confirm': 'حساب کاربری و همهٔ داده‌های اسکن ذخیره‌شده برای همیشه حذف شود؟ این عمل قابل بازگشت نیست.',
    },
  };

  function locale() {
    return (document.documentElement.lang || 'en').toLowerCase().split('-')[0];
  }

  function t(key, fallback) {
    return translations[locale()]?.[key] || fallback || key;
  }

  function apply(root = document) {
    root.querySelectorAll?.('[data-i18n]').forEach((element) => {
      element.textContent = t(element.dataset.i18n, element.dataset.i18nFallback || element.textContent);
    });
    root.querySelectorAll?.('[data-i18n-placeholder]').forEach((element) => {
      element.placeholder = t(element.dataset.i18nPlaceholder, element.dataset.i18nPlaceholderFallback || element.placeholder);
    });
    root.querySelectorAll?.('[data-i18n-title]').forEach((element) => {
      element.title = t(element.dataset.i18nTitle, element.dataset.i18nTitleFallback || element.title);
    });
    root.querySelectorAll?.('[data-i18n-aria-label]').forEach((element) => {
      element.setAttribute('aria-label', t(element.dataset.i18nAriaLabel, element.dataset.i18nAriaLabelFallback || element.getAttribute('aria-label')));
    });
  }

  window.AegisI18n = { t, apply, locale, translations };
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    document.documentElement.dataset.i18nReady = 'true';
  });
})();
