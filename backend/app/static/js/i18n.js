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
      'auth.signing_in': 'در حال ورود…', 'auth.signed_in': 'با موفقیت وارد شدید', 'auth.sign_in': 'ورود',
      'auth.password_mismatch': 'گذرواژه‌ها یکسان نیستند', 'auth.creating_account': 'در حال ایجاد حساب…', 'auth.account_created': 'حساب ایجاد شد؛ اکنون وارد شوید', 'auth.create_account': 'ایجاد حساب',
      'auth.reset_sent': 'اگر این ایمیل وجود داشته باشد، پیوند بازنشانی ارسال شده است.', 'auth.updating': 'در حال به‌روزرسانی…', 'auth.password_updated': 'گذرواژه به‌روزرسانی شد؛ وارد شوید', 'auth.update_password': 'به‌روزرسانی گذرواژه',
      'dashboard.greeting': 'خوش آمدید، {username}. این نمای کلی وضعیت امنیتی شماست.', 'dashboard.scans': 'اسکن‌ها', 'dashboard.threats': 'تهدیدهای شناسایی‌شده', 'dashboard.average_score': 'میانگین امتیاز اعتماد', 'dashboard.needs_attention': 'نیازمند توجه', 'dashboard.scan_type_url': 'نشانی وب', 'dashboard.scan_type_email': 'ایمیل', 'dashboard.scan_type_text': 'پیام', 'dashboard.scan_type_image': 'تصویر', 'dashboard.scan_type_qr': 'کد QR', 'dashboard.scan_type_file': 'فایل',
      'map.no_reports': 'گزارش تأییدشده‌ای برای این بازه در دسترس نیست.', 'map.unknown_country': 'کشور نامشخص', 'map.unknown': 'نامشخص', 'map.approved_reports': 'گزارش تأییدشده', 'map.approved_report': 'گزارش تأییدشده', 'map.country_aggregate': 'تجمیع کشوری', 'map.approved_community': 'گزارش‌های تأییدشدهٔ جامعه', 'map.in_last': 'در', 'map.days': 'روز گذشته', 'map.load_failed': 'بارگیری داده‌های نقشه انجام نشد.',
      'report.complete_title': 'ارزیابی تکمیل شد', 'report.complete_body': 'AEGIS مسیر ارزیابی در دسترس را کامل کرد. نتیجه بر شواهد تکیه دارد، نه تضمین.', 'report.limited_title': 'ارزیابی محدود', 'report.limited_body': 'بررسی‌های مقصد راه‌دور کامل نشدند. شواهد محلی نمایش داده می‌شوند، اما نتیجه عمداً تأییدنشده است.', 'report.blocked_title': 'مرز ایمنی اعمال شد', 'report.blocked_body': 'AEGIS از بررسی این هدف خودداری کرد، زیرا از مرز ایمنی شبکه عبور می‌کند.',
      'report.no_evidence': 'شواهد جزئی برای این ارزیابی نگهداری نشده است.', 'report.reliability': 'قابلیت اتکا', 'report.coverage_note': 'یادداشت پوشش', 'report.risk': 'خطر', 'report.protective': 'محافظتی', 'report.scanner_observation': 'مشاهدهٔ تحلیل‌گر', 'report.neutral': 'خنثی', 'report.signals': 'سیگنال', 'report.net_contribution': 'مشارکت خالص شواهد', 'report.no_families': 'خانوادهٔ شواهدی ثبت نشده است.', 'report.no_action': 'اقدام دیگری برای این پرونده ثبت نشده است.', 'report.local_completion': 'تکمیل فقط در همین مرورگر ذخیره می‌شود و پرونده یا نتیجه را تغییر نمی‌دهد.',
      'report.case': 'پرونده', 'report.content': 'محتوا', 'report.assessment': 'ارزیابی', 'report.time_unavailable': 'زمان در دسترس نیست', 'report.coverage': 'پوشش', 'report.evidence_chain': 'زنجیرهٔ شواهد', 'report.observations': 'مشاهدهٔ ثبت‌شده', 'report.response_playbook': 'راهنمای پاسخ', 'report.prioritize_containment': 'پیش از هر تعامل بیشتر، مهار را در اولویت قرار دهید.', 'report.scope': 'دامنه و منشأ', 'report.engine': 'موتور', 'report.network_acquisition': 'دریافت شبکه', 'report.external_intelligence': 'اطلاعات بیرونی', 'report.no_feed_match': 'تطابقی با خوراک بیرونی ثبت نشده است', 'report.integrity': 'اثر انگشت یکپارچگی', 'report.limitations': 'محدودیت‌های ارزیابی', 'report.evidence_first_record': 'رکورد مبتنی بر شواهد', 'report.link_copied': 'پیوند پرونده کپی شد', 'report.link_copy_failed': 'کپی پیوند انجام نشد', 'report.estimated_risk': 'خطر برآوردشده', 'report.phase_contain': 'مهار', 'report.owner_user_service': 'کاربر یا میز خدمات', 'report.action_stop': 'از هرگونه تعامل با این محتوا دست بکشید. چند نشانهٔ مستقل از کلاه‌برداری محتمل یا تطابق با تهدید تأییدشده وجود دارد.', 'report.action_block': 'فرستنده یا نشانی وب را مسدود و گزارش کنید. اگر دادهٔ مالی یا حساب خود را به اشتراک گذاشته‌اید، فوراً با ارائه‌دهندهٔ اصلی تماس بگیرید.', 'report.action_passwords': 'گذرواژه‌های در معرض خطر را تغییر دهید و نشست‌های فعال را از یک دستگاه مطمئن لغو کنید.', 'report.evidence_to_verify': 'شواهد نیازمند بررسی:', 'report.integrity_scope': 'محتوای معیار پرونده پیش از این فیلد یکپارچگی است؛ اثرانگشت، امضای دیجیتال نیست.', 'report.limitation_confidence': 'اطمینان از شواهد، پوشش گردآوری و توافق میان خانواده‌های شواهد را توصیف می‌کند؛ این مقدار دقت پیش‌بینی اندازه‌گیری‌شده نیست.', 'report.limitation_scope': 'پرونده فقط همین ارزیابی را ثبت می‌کند و انتساب مجرمانه یا تأیید بیرونی را اثبات نمی‌کند.',
      'admin.human_review': 'فرایند بررسی انسانی', 'admin.triage_title': 'صف تریاژ تحلیل‌گر', 'admin.triage_description': 'ارزیابی‌های پرخطر ذخیره‌شدهٔ اخیر برای بررسی انسانی مرتب می‌شوند. ثبت نتیجه از امتیازدهی جدا است: موتور را بازآموزی نمی‌دهد، شواهد را تغییر نمی‌دهد و اطلاعات را خودکار منتشر نمی‌کند.', 'admin.triage_purpose': 'صف بررسی انسانی برای ارزیابی‌های پرخطر ذخیره‌شده. بلوک‌های صرفاً مرز ایمنی کنار گذاشته می‌شوند؛ نتیجه از امتیاز موتور جدا است.',
    },
  };

  // These are interface literals that originate from templates or dynamic view
  // renderers. They deliberately exclude observed scan content, domains,
  // sender names, indicator values, and other user-supplied evidence.
  const literalTranslations = {
    fa: {
      'Dashboard': 'داشبورد',
      'Welcome back,': 'خوش آمدید،',
      "Here's your security posture.": 'این نمای کلی وضعیت امنیتی شماست.',
      '+ New Scan': '+ اسکن جدید',
      'Start with evidence': 'با شواهد شروع کنید',
      'Analyze the message or link that made you pause.': 'پیام یا پیوندی را که باعث تردیدتان شد بررسی کنید.',
      'AEGIS will show the evidence it collected, clearly state coverage limitations, and suggest the next safe action. It does not treat a lack of evidence as proof that something is safe.': 'AEGIS شواهد گردآوری‌شده را نمایش می‌دهد، محدودیت‌های پوشش را روشن بیان می‌کند و گام ایمن بعدی را پیشنهاد می‌دهد. نبود شواهد به‌معنای بی‌خطر بودن نیست.',
      'Analyze a link or message': 'تحلیل یک پیوند یا پیام',
      'Learn common warning signs': 'نشانه‌های هشدار رایج را بیاموزید',
      'Stored scans': 'اسکن‌های ذخیره‌شده',
      'Threats detected': 'تهدیدهای شناسایی‌شده',
      'Average trust score': 'میانگین امتیاز اعتماد',
      'Needs attention': 'نیازمند توجه',
      'review findings': 'یافته برای بررسی',
      'none detected': 'موردی یافت نشد',
      'Review suspicious or threat scans': 'اسکن‌های مشکوک یا تهدید را بررسی کنید',
      'Recent Scans': 'اسکن‌های اخیر',
      'View all': 'مشاهدهٔ همه',
      'Scan Activity (14 days)': 'فعالیت اسکن (۱۴ روز)',
      'Trust Score Trend': 'روند امتیاز اعتماد',
      'Recent Threats': 'تهدیدهای اخیر',
      'No stored scans yet': 'هنوز اسکن ذخیره‌شده‌ای نیست',
      'Run a scan and choose to retain it when you need a history or report.': 'یک اسکن اجرا کنید و در صورت نیاز به تاریخچه یا گزارش، نگهداری آن را انتخاب کنید.',
      'Start a scan →': 'شروع اسکن ←',
      'No stored scans need attention.': 'هیچ اسکن ذخیره‌شده‌ای نیاز به توجه ندارد.',
      'Scans': 'اسکن‌ها',
      'Trust': 'اعتماد',
      'Community intelligence': 'اطلاعات جامعه',
      'Verified threat activity': 'فعالیت تأییدشدهٔ تهدید',
      'Approved community reports only. Locations are displayed as country aggregates, never as an exact reporter, victim, or server location.': 'فقط گزارش‌های تأییدشدهٔ جامعه. موقعیت‌ها تنها به‌صورت تجمیع کشوری نمایش داده می‌شوند، نه مکان دقیق گزارش‌دهنده، قربانی یا سرور.',
      'Last 24h': '۲۴ ساعت گذشته',
      '7 days': '۷ روز',
      '30 days': '۳۰ روز',
      'Approved community reports · country aggregate': 'گزارش‌های تأییدشدهٔ جامعه · تجمیع کشوری',
      'Loading verified reports…': 'در حال بارگیری گزارش‌های تأییدشده…',
      'No verified reports in this period': 'در این بازه گزارش تأییدشده‌ای نیست',
      'The map stays empty until real reports are approved. AEGIS never fills it with sample activity.': 'نقشه تا زمانی که گزارش‌های واقعی تأیید نشوند خالی می‌ماند. AEGIS هرگز آن را با فعالیت نمونه پُر نمی‌کند.',
      'Critical / high': 'بحرانی / بالا',
      'Medium': 'متوسط',
      'Low / informational': 'پایین / اطلاع‌رسانی',
      'Marker size reflects report count, not geographic precision.': 'اندازهٔ نشانگر تعداد گزارش را نشان می‌دهد، نه دقت جغرافیایی را.',
      'Verified reports': 'گزارش‌های تأییدشده',
      'Countries represented': 'کشورهای دارای گزارش',
      'Most reported vector': 'پُرگزارش‌ترین بردار',
      'Learning Center': 'مرکز آموزش',
      'Lessons, quizzes and a scam simulator to sharpen your detection skills.': 'درس‌ها، آزمون‌ها و شبیه‌ساز کلاه‌برداری برای تقویت مهارت تشخیص شما.',
      'Lessons': 'درس‌ها',
      'All': 'همه',
      'Phishing': 'فیشینگ',
      'Identity': 'هویت',
      'Tech Scams': 'کلاه‌برداری‌های فناوری',
      'Quizzes': 'آزمون‌ها',
      'Scam Simulator': 'شبیه‌ساز کلاه‌برداری',
      'Can you spot the scam? Play through realistic scenarios and see the trust analysis.': 'می‌توانید کلاه‌برداری را تشخیص دهید؟ سناریوهای واقع‌گرایانه را تجربه کنید و تحلیل اعتماد را ببینید.',
      'Choose a scenario…': 'یک سناریو انتخاب کنید…',
      'Your Progress': 'پیشرفت شما',
      'What is Phishing?': 'فیشینگ چیست؟',
      'Basics': 'مبانی',
      'Learn how attackers trick you into revealing passwords and money.': 'بیاموزید مهاجمان چگونه شما را برای افشای گذرواژه و پول فریب می‌دهند.',
      'Spotting Scam Messages': 'تشخیص پیام‌های کلاه‌برداری',
      'The language tricks used in scam SMS, WhatsApp and Telegram.': 'ترفندهای زبانیِ مورد استفاده در پیامک، واتساپ و تلگرام کلاه‌برداری.',
      'Fake Websites and Links': 'وب‌سایت‌ها و پیوندهای جعلی',
      'Web Safety': 'ایمنی وب',
      'How typosquatting, punycode and lookalike domains work.': 'تایپواسکواتینگ، پونیکد و دامنه‌های مشابه چگونه کار می‌کنند.',
      'Protecting Your Identity': 'محافظت از هویت شما',
      'Personal Safety': 'ایمنی شخصی',
      'Stop identity theft before it happens.': 'پیش از وقوع، از سرقت هویت جلوگیری کنید.',
      'QR Code Safety': 'ایمنی کد QR',
      'Quishing: QR codes that hide malicious links.': 'کویشینگ: کدهای QR که پیوندهای بدخواه را پنهان می‌کنند.',
      'Phishing 101': 'مبانی فیشینگ',
      'Test your ability to spot phishing attempts.': 'توانایی خود را در تشخیص تلاش‌های فیشینگ بسنجید.',
      'URL & Website Security': 'امنیت نشانی وب و وب‌سایت',
      'Learn to evaluate links before clicking.': 'بیاموزید پیش از کلیک، پیوندها را ارزیابی کنید.',
      'Level': 'سطح', 'Novice': 'تازه‌کار', 'Points': 'امتیاز', 'Lessons completed': 'درس‌های تکمیل‌شده', 'Quizzes passed': 'آزمون‌های پذیرفته‌شده', 'Simulator streak': 'رکورد شبیه‌ساز', 'Certificates': 'گواهی‌ها',
      'Admin Panel': 'پنل مدیریت',
      'Platform analytics, trust rule tuning, threat intelligence and moderation.': 'تحلیل پلتفرم، تنظیم قوانین اعتماد، اطلاعات تهدید و تعدیل.',
      'Total Users': 'کل کاربران', 'Total Scans': 'کل اسکن‌ها', 'Active Threats': 'تهدیدهای فعال', 'Avg Trust Score': 'میانگین امتیاز اعتماد',
      'Threat Intelligence': 'اطلاعات تهدید', 'Trust Rules': 'قوانین اعتماد', 'Keywords': 'کلیدواژه‌ها', 'Users': 'کاربران', 'Audit Log': 'گزارش حسابرسی', 'Analyst Triage': 'تریاژ تحلیل‌گر', 'Engine Conformance': 'انطباق موتور', 'Operational Readiness': 'آمادگی عملیاتی',
      'Search threats…': 'جست‌وجوی تهدیدها…', 'Delete': 'حذف',
      'Search': 'جست‌وجو', 'Search across your scans and platform threats.': 'در اسکن‌های خود و تهدیدهای پلتفرم جست‌وجو کنید.', 'Everything': 'همه‌چیز', 'My scans': 'اسکن‌های من', 'Threats': 'تهدیدها', 'Users (admin)': 'کاربران (مدیر)', 'e.g. paypal, 09xxxx, phishing domain…': 'مانند paypal، ۰۹xxxx یا دامنهٔ فیشینگ…',
      'Reviewable security record': 'رکورد امنیتی قابل بررسی', 'Assessment casefile': 'پروندهٔ ارزیابی', 'Export casefile JSON': 'برون‌بری JSON پرونده', 'Download PDF': 'دانلود PDF', 'Copy case link': 'کپی پیوند پرونده', 'Assessment completed': 'ارزیابی تکمیل شد', 'Evidence chain': 'زنجیرهٔ شواهد', 'Response playbook': 'راهنمای پاسخ', 'Scope & provenance': 'دامنه و منشأ', 'Integrity fingerprint': 'اثر انگشت یکپارچگی', 'Assessment limitations': 'محدودیت‌های ارزیابی',
      'Prioritize containment before further interaction.': 'پیش از هر تعامل بیشتر، مهار را در اولویت قرار دهید.', 'Completion is stored only in this browser; it does not modify the casefile or report an outcome.': 'تکمیل فقط در همین مرورگر ذخیره می‌شود و پرونده یا نتیجه را تغییر نمی‌دهد.',
      'Digital Trust Shield': 'سپر اعتماد دیجیتال', 'Know who to trust.': 'بدانید به چه کسی اعتماد کنید.', 'Before they know you.': 'پیش از آن‌که شما را بشناسند.',
      'Launch Scanner': 'باز کردن تحلیل‌گر', 'Go to Dashboard': 'رفتن به داشبورد', 'View guided demo': 'نمایش دموی راهنما', 'Get Started Free': 'شروع رایگان', 'Sign In': 'ورود',
      'Six input paths, one evidence model': 'شش مسیر ورودی، یک مدل شواهد', 'URL Scanner': 'تحلیل‌گر URL', 'Email Scanner': 'تحلیل‌گر ایمیل', 'Message Scanner': 'تحلیل‌گر پیام', 'Image Scanner': 'تحلیل‌گر تصویر', 'QR Code Scanner': 'تحلیل‌گر کد QR', 'File Scanner': 'تحلیل‌گر فایل',
      'An explainable assessment, not a black box': 'ارزیابی توضیح‌پذیر، نه جعبه‌سیاه', 'What every assessment preserves': 'آنچه هر ارزیابی حفظ می‌کند', 'Evidence chain': 'زنجیرهٔ شواهد', 'Assessment boundary': 'مرز ارزیابی', 'Safe next step': 'گام ایمن بعدی',
      'Welcome back': 'خوش آمدید', 'Sign in to your AEGIS account': 'به حساب AEGIS خود وارد شوید.', 'Email': 'ایمیل', 'Password': 'گذرواژه', 'Forgot password?': 'گذرواژه را فراموش کرده‌اید؟', 'Remember me': 'مرا به خاطر بسپار', 'Create account': 'ایجاد حساب',
      'Create your account': 'حساب خود را بسازید', 'Free forever · No credit card': 'رایگان برای همیشه · بدون کارت بانکی', 'Username': 'نام کاربری', 'Confirm password': 'تأیید گذرواژه', 'At least 8 characters with upper, lower and digits.': 'حداقل ۸ نویسه شامل حروف بزرگ، کوچک و رقم.', 'Already have an account?': 'از قبل حساب دارید؟',
      'Reset your password': 'بازنشانی گذرواژه', "Enter your email and we'll send you a reset link.": 'ایمیل خود را وارد کنید تا پیوند بازنشانی را ارسال کنیم.', 'Send Reset Link': 'ارسال پیوند بازنشانی', 'Back to sign in': 'بازگشت به ورود',
      'Set a new password': 'تنظیم گذرواژهٔ جدید', 'Choose a strong password for': 'یک گذرواژهٔ قوی انتخاب کنید برای', 'New password': 'گذرواژهٔ جدید', 'Update Password': 'به‌روزرسانی گذرواژه'
    }
  };

  Object.assign(literalTranslations.fa, {
    'inactive': 'غیرفعال', 'active': 'فعال', 'disabled': 'غیرفعال', 'enabled': 'فعال', 'accepted': 'پذیرفته‌شده', 'not accepted': 'پذیرفته‌نشده',
    'No threats.': 'تهدیدی وجود ندارد.', 'Threat deleted': 'تهدید حذف شد', 'Adjust rule weights and activation. Changes apply to the next scan.': 'وزن و فعال‌سازی قوانین را تنظیم کنید. تغییرات در اسکن بعدی اعمال می‌شوند.', 'Save Changes': 'ذخیرهٔ تغییرات', 'Rules updated': 'قوانین به‌روزرسانی شدند', 'Phishing Keywords': 'کلیدواژه‌های فیشینگ', 'e.g. urgent action required': 'مانند: اقدام فوری لازم است', 'category': 'دسته‌بندی', 'impact': 'اثر', 'Add': 'افزودن', 'No keywords.': 'کلیدواژه‌ای وجود ندارد.', 'Keyword added': 'کلیدواژه افزوده شد', 'Keyword deleted': 'کلیدواژه حذف شد',
    'admin': 'مدیر', 'user': 'کاربر', 'Disable': 'غیرفعال‌سازی', 'Enable': 'فعال‌سازی', 'User updated': 'کاربر به‌روزرسانی شد', 'system': 'سامانه', 'No logs.': 'رویدادی ثبت نشده است.',
    'awaiting review': 'در انتظار بررسی', 'confirmed malicious': 'بدخواه بودن تأیید شد', 'confirmed benign': 'بی‌خطر بودن تأیید شد', 'inconclusive': 'نامشخص',
    'Human review workflow': 'فرایند بررسی انسانی', 'Analyst triage queue': 'صف تریاژ تحلیل‌گر', 'Open casefile': 'باز کردن پرونده', 'Evidence families': 'خانواده‌های شواهد', 'No family summary available.': 'خلاصهٔ خانوادهٔ شواهد در دسترس نیست.', 'Strongest recorded evidence': 'قوی‌ترین شواهد ثبت‌شده', 'No evidence summary available.': 'خلاصهٔ شواهد در دسترس نیست.', 'Latest review:': 'آخرین بررسی:', 'Confirm malicious': 'تأیید بدخواه بودن', 'Confirm benign': 'تأیید بی‌خطر بودن', 'Mark inconclusive': 'علامت‌گذاری نامشخص', 'A latest review is recorded. Use the casefile and audit log for follow-up.': 'آخرین بررسی ثبت شده است. برای پیگیری از پرونده و گزارش حسابرسی استفاده کنید.', 'No high-risk persisted assessments are awaiting operational triage.': 'هیچ ارزیابی پرخطر ذخیره‌شده‌ای در انتظار تریاژ عملیاتی نیست.',
    'Engineering regression contract': 'قرارداد رگرسیون مهندسی', 'Deterministic engine conformance': 'انطباق موتور قطعی', 'fixtures passing': 'نمونهٔ عبورکرده', 'PASS': 'قبول', 'FAIL': 'ناموفق', 'Observed risk': 'خطر مشاهده‌شده', 'Trust score': 'امتیاز اعتماد', 'Evidence confidence': 'اطمینان از شواهد',
    'Operational accountability': 'پاسخ‌گویی عملیاتی', 'Readiness & governance': 'آمادگی و حاکمیت', 'Engine': 'موتور', 'training required': 'نیازمند آموزش', 'no model training': 'بدون آموزش مدل', 'Completed assessments': 'ارزیابی‌های تکمیل‌شده', 'Persisted assessments in the quality view.': 'ارزیابی‌های ذخیره‌شده در نمای کیفیت.', 'High-coverage share': 'سهم پوشش بالا', 'Coverage and agreement, not predictive accuracy.': 'پوشش و توافق، نه دقت پیش‌بینی.', 'Outcome review': 'بررسی نتیجه', 'Human or policy-confirmed outcomes.': 'نتیجه‌های تأییدشده توسط انسان یا سیاست.', 'Engine disclosure': 'افشای موتور', 'Control boundaries': 'مرزهای کنترل', 'No outcomes in this review window.': 'نتیجه‌ای در این بازهٔ بررسی نیست.', 'Governed intelligence sources': 'منابع اطلاعاتِ حاکمیت‌شده', 'Sources remain disabled until their terms are explicitly accepted; their state is visible here for review.': 'منابع تا زمانی که شرایط آن‌ها صریحاً پذیرفته نشود غیرفعال می‌مانند و وضعیتشان برای بررسی نمایش داده می‌شود.', 'Source': 'منبع', 'State': 'وضعیت', 'Terms': 'شرایط', 'Boundary': 'مرز', 'No governed feed records yet.': 'هنوز رکورد خوراک حاکمیت‌شده‌ای نیست.',
    'The Delivery Fee Trap': 'دام هزینهٔ تحویل', 'The Friend in Trouble': 'دوست گرفتار', 'The Oil Rig Romance': 'عاشقانهٔ سکوی نفتی', 'The Arrest Warrant': 'حکم بازداشت', 'pass': 'حدنصاب',
    'email assessment': 'ارزیابی ایمیل', 'url assessment': 'ارزیابی نشانی وب', 'text assessment': 'ارزیابی پیام', 'image assessment': 'ارزیابی تصویر', 'qr assessment': 'ارزیابی کد QR', 'file assessment': 'ارزیابی فایل', 'content assessment': 'ارزیابی محتوا', 'not applicable': 'اعمال نمی‌شود',
    'url': 'نشانی وب', 'phone': 'تلفن', 'government': 'دولتی', 'credential_harvesting': 'سرقت اعتبار', 'advance_fee': 'پیش‌پرداخت', 'phishing': 'فیشینگ', 'crypto': 'رمزارز', 'high': 'بالا', 'critical': 'بحرانی', 'medium': 'متوسط', 'low': 'پایین', 'info': 'اطلاع‌رسانی', 'complete': 'تکمیل‌شده', 'limited': 'محدود', 'blocked': 'مسدودشده', 'email_auth': 'اعتبارسنجی ایمیل', 'impersonation': 'جعل هویت', 'obfuscation': 'پنهان‌سازی', 'urgency': 'فوریت', 'availability': 'دسترس‌پذیری', 'bank': 'بانک', 'fear': 'ترس', 'password': 'گذرواژه', 'not_applicable': 'اعمال نمی‌شود', 'scanner_observation': 'مشاهدهٔ تحلیل‌گر', 'url_observation': 'مشاهدهٔ نشانی وب', 'pattern': 'الگو', 'email_authentication': 'اعتبارسنجی ایمیل', 'Unknown sender': 'فرستندهٔ ناشناس', 'Urgency language detected': 'زبان فوریت‌ساز شناسایی شد', 'Brand-like destination hostname': 'نام میزبان شبیه برند', 'Sensitive-action words in link': 'واژه‌های حساس در پیوند', 'Suspicious link in email': 'پیوند مشکوک در ایمیل', 'The email comes from a domain you may not know.': 'این ایمیل از دامنه‌ای می‌آید که ممکن است آن را نشناسید.', 'The message uses pressure language designed to make you act without thinking.': 'پیام از زبان فشارآور استفاده می‌کند تا شما را به اقدام بدون فکر وادارد.', "The destination hostname closely resembles 'paypal' without being the verified brand domain.": 'نام میزبان مقصد به «paypal» شباهت زیادی دارد، اما دامنهٔ تأییدشدهٔ برند نیست.', 'The URL includes account, credential, payment, or verification terms often used in phishing flows.': 'نشانی وب شامل عبارت‌های حساب، اعتبار، پرداخت یا تأیید است که اغلب در روندهای فیشینگ استفاده می‌شوند.', 'The email contains links that look suspicious.': 'ایمیل حاوی پیوندهایی است که مشکوک به نظر می‌رسند.',
    'No approved reports with a verified country are available for this period.': 'گزارش تأییدشده‌ای با کشور اعتبارسنجی‌شده برای این بازه در دسترس نیست.'
  });

  function locale() {
    return (document.documentElement.lang || 'en').toLowerCase().split('-')[0];
  }

  function t(key, fallback) {
    return translations[locale()]?.[key] || fallback || key;
  }

  function translateLiteral(value) {
    const text = String(value || '');
    const trimmed = text.trim();
    if (locale() === 'fa') {
      const greeting = trimmed.match(/^Welcome back,\s*(.+)\.\s*Here's your security posture\.$/);
      if (greeting) return text.replace(trimmed, t('dashboard.greeting', 'خوش آمدید، {username}. این نمای کلی وضعیت امنیتی شماست.').replace('{username}', greeting[1]));
      const quiz = trimmed.match(/^(Test your ability to spot phishing attempts\.|Learn to evaluate links before clicking\.)\s*·\s*pass\s*(\d+)%$/);
      if (quiz) {
        const description = quiz[1].startsWith('Test') ? 'توانایی خود را در تشخیص تلاش‌های فیشینگ بسنجید.' : 'بیاموزید پیش از کلیک، پیوندها را ارزیابی کنید.';
        return text.replace(trimmed, `${description} · حدنصاب ${quiz[2]}٪`);
      }
      const threatCount = trimmed.match(/^(\d+) threat\(s\)$/);
      if (threatCount) return text.replace(trimmed, `${threatCount[1]} تهدید`);
    }
    const translated = literalTranslations[locale()]?.[trimmed];
    return translated ? text.replace(trimmed, translated) : text;
  }

  function translateAuto(root) {
    if (!literalTranslations[locale()]) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || ['SCRIPT', 'STYLE', 'CODE', 'PRE'].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    textNodes.forEach((node) => { node.nodeValue = translateLiteral(node.nodeValue); });
    root.querySelectorAll?.('[placeholder], [title], [aria-label]').forEach((element) => {
      if (element.hasAttribute('placeholder')) element.placeholder = translateLiteral(element.placeholder);
      if (element.hasAttribute('title')) element.title = translateLiteral(element.title);
      if (element.hasAttribute('aria-label')) element.setAttribute('aria-label', translateLiteral(element.getAttribute('aria-label')));
    });
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
    const autoRoots = [];
    if (root.matches?.('[data-i18n-auto]')) autoRoots.push(root);
    root.querySelectorAll?.('[data-i18n-auto]').forEach((element) => autoRoots.push(element));
    autoRoots.forEach(translateAuto);
  }

  window.AegisI18n = { t, apply, locale, translations };
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    const observer = new MutationObserver((records) => {
      records.forEach((record) => record.addedNodes.forEach((node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        apply(node);
        const autoRoot = node.closest?.('[data-i18n-auto]') || node.querySelector?.('[data-i18n-auto]');
        if (autoRoot) translateAuto(autoRoot);
      }));
    });
    document.querySelectorAll('[data-i18n-auto]').forEach((root) => observer.observe(root, { childList: true, subtree: true }));
    document.documentElement.dataset.i18nReady = 'true';
  });
})();
