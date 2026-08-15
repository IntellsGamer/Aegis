/* Learning Center: Turbo-safe dynamic rendering with native Persian learning content. */
(function () {
  'use strict';
  const shared = window.Aegis;
  if (!shared) {
    window.addEventListener('aegis:ready', () => window.location.reload(), { once: true });
    return;
  }
  const { api, esc, toast } = shared;

  const fa = {
    ui: {
      noLessons: 'در این دسته هنوز درسی در دسترس نیست.', noQuizzes: 'هنوز آزمونی در دسترس نیست.',
      allLessons: 'همهٔ درس‌ها', example: 'نمونه', tips: 'نکته‌های کلیدی', markComplete: 'ثبت به‌عنوان تکمیل‌شده',
      completed: 'تکمیل شد', lessonCompleted: 'درس تکمیل شد', next: 'ادامه', yourAnswer: 'پاسخ شما', correct: 'پاسخ درست',
      passed: 'آفرین! آزمون را با موفقیت گذراندید.', retry: 'یادگیری را ادامه دهید و دوباره تلاش کنید.',
      certificate: 'گواهی', back: 'بازگشت به آموزش امنیت', question: 'سؤال', signInProgress: 'برای ثبت پیشرفت وارد حساب شوید.',
      level: 'سطح', novice: 'تازه‌کار', points: 'امتیاز', lessonsCompleted: 'درس‌های تکمیل‌شده', quizzesPassed: 'آزمون‌های پذیرفته‌شده',
      simulatorStreak: 'رکورد شبیه‌ساز', certificates: 'گواهی‌ها', whatWouldYouDo: 'در این موقعیت چه می‌کنید؟',
      correctChoice: 'درست انتخاب کردید.', incorrectChoice: 'هنوز نه؛ دوباره به نشانه‌ها نگاه کنید.', streak: 'رکورد', pass: 'حدنصاب', minutes: 'دقیقه',
    },
    lessons: {
      'what-is-phishing': {
        title: 'فیشینگ چیست؟', category: 'مبانی', summary: 'بیاموزید مهاجمان چگونه با جعل اعتماد، گذرواژه و پول شما را هدف می‌گیرند.',
        content: 'فیشینگ نوعی مهندسی اجتماعی است: مهاجم خود را بانک، سازمان دولتی، فروشگاه یا شخصی مورداعتماد نشان می‌دهد تا گذرواژه، پول یا اطلاعات شخصی شما را بگیرد. این فریب می‌تواند از راه ایمیل، پیامک، شبکهٔ اجتماعی، تماس تلفنی، کد QR یا یک وب‌سایت جعلی برسد.\n\nکلاه‌بردارها روی عجله، ترس، اعتبار ظاهری و وعدهٔ پاداش حساب می‌کنند تا پیش از فکر کردن اقدام کنید. هیچ سازمان معتبری رمز عبور یا رمز یک‌بارمصرف را در پیام از شما نمی‌خواهد.\n\nپیش از کلیک‌کردن مکث کنید و فرستنده را از مسیر مستقل بررسی کنید: نشانی را خودتان وارد کنید، با شمارهٔ رسمی تماس بگیرید یا نشانی فرستنده را نویسه‌به‌نویسه بخوانید.',
        example: '«فوری: اگر همین حالا از این پیوند کوتاه حساب خود را تأیید نکنید، مسدود می‌شود.» این پیام با ایجاد فوریت و فرستادن شما به یک پیوند ناشناس، الگوی فیشینگ دارد.',
        tips: ['نشانی واقعی فرستنده را بررسی کنید، نه فقط نام نمایشی را', 'پیش از کلیک، مقصد پیوند را ببینید', 'رمز یک‌بارمصرف را با هیچ‌کس به اشتراک نگذارید', 'نشانی رسمی سرویس را خودتان وارد کنید'],
      },
      'spotting-scam-messages': {
        title: 'تشخیص پیام‌های کلاه‌برداری', category: 'مبانی', summary: 'ترفندهای زبانیِ رایج در پیامک، واتساپ و تلگرام کلاه‌برداری را بشناسید.',
        content: 'پیام‌های کلاه‌برداری معمولاً چند نشانهٔ مشترک دارند: واژه‌های فوری مانند «همین حالا»، تهدیدهایی مانند «حساب شما بسته می‌شود» و وعده‌هایی که بیش از اندازه خوب به نظر می‌رسند.\n\nمهاجم ممکن است رمز تأیید، گذرواژه، دسترسی از راه دور، کارت هدیه یا رمزارز بخواهد؛ چیزهایی که پس از ارسال معمولاً بازگرداندنشان دشوار است.\n\nبه شمارهٔ فرستندهٔ غیرعادی، پیوند کوتاه، نگارش نامتعارف، درخواست مدارک شخصی و فشار برای پنهان‌کاری دقت کنید.',
        example: '«فعالیت غیرعادی دیدیم؛ همین حالا رمز یک‌بارمصرف را پاسخ دهید.» بانک واقعی هیچ‌وقت از شما نمی‌خواهد رمز را برای آن ارسال کنید؛ رمز فقط برای ورود شما در سامانهٔ رسمی است.',
        tips: ['اگر مطمئن نیستید عجله نکنید و سؤال بپرسید', 'متن دقیق پیام را جست‌وجو کنید؛ بسیاری از کلاه‌برداری‌ها تکراری‌اند', 'پیام مشکوک را به اپراتور یا پلتفرم گزارش کنید'],
      },
      'fake-websites': {
        title: 'وب‌سایت‌ها و پیوندهای جعلی', category: 'ایمنی وب', summary: 'با دامنه‌های شبیه‌سازی‌شده، پونیکد و پیوندهای گمراه‌کننده آشنا شوید.',
        content: 'وب‌سایت جعلی با تقلید از برندها تلاش می‌کند اطلاعات ورود شما را بگیرد. مهاجم‌ها از دامنه‌های مشابه مانند paypa1 به‌جای paypal، نویسه‌های پونیکد، پیوندهای کوتاه و گاهی نشانی IP استفاده می‌کنند.\n\nنام دامنه را با دقت بخوانید. قفل کنار نشانی فقط یعنی ارتباط رمزگذاری شده است؛ این قفل مشروع‌بودن وب‌سایت را ثابت نمی‌کند.\n\nپیش از واردکردن اطلاعات حساس، پیوند را با بررسی‌گر AEGIS ارزیابی کنید و فقط از نشانی رسمیِ تایپ‌شده یا ذخیره‌شده استفاده کنید.',
        example: 'نشانی `paypal-com-security-check.tk/login` شاید شبیه PayPal دیده شود، اما دامنهٔ اصلی آن `.tk` است و به برند PayPal تعلق ندارد.',
        tips: ['نشانی‌های مهم را خودتان تایپ کنید', 'صفحه‌های ورود معتبر را نشانه‌گذاری کنید', 'از مدیر گذرواژه استفاده کنید؛ روی دامنهٔ جعلی تکمیل خودکار نمی‌کند'],
      },
      'protecting-your-identity': {
        title: 'محافظت از هویت شما', category: 'ایمنی شخصی', summary: 'پیش از وقوع سرقت هویت، از اطلاعات شخصی خود محافظت کنید.',
        content: 'سارقان هویت به‌دنبال تصویر مدرک شناسایی، شمارهٔ ملی، تاریخ تولد، صورت‌حساب بانکی یا پاسخ پرسش‌های امنیتی هستند. از این اطلاعات برای ساخت حساب، گرفتن وام یا خالی‌کردن حساب استفاده می‌شود.\n\nتصویر مدارک هویتی را در چت ارسال نکنید. اگر یک فرصت شغلی، قرعه‌کشی یا سرمایه‌گذاری پیش از اثبات اعتبار خود از شما مدرک می‌خواهد، با احتمال زیاد باید آن را مشکوک بدانید.\n\nبرای هر سرویس گذرواژهٔ قوی و متفاوت بگذارید و احراز هویت دومرحله‌ای را فعال کنید.',
        example: '«برای آزادکردن جایزه فقط تصویر گذرنامه و صورت‌حساب بانکی شما را می‌خواهیم.» سازمان معتبر جایزه را به این روش آزاد نمی‌کند.',
        tips: ['مدارک شخصی را فقط در درگاه رسمی بارگذاری کنید', 'فعالیت غیرعادی حساب‌ها را پیگیری کنید', 'اگر مدارک گم شدند، سریع اقدامات حفاظتی مالی را انجام دهید'],
      },
      'qr-code-safety': {
        title: 'ایمنی کد QR', category: 'ایمنی وب', summary: 'کویشینگ: کدهای QR که مقصدهای بدخواه را پنهان می‌کنند.',
        content: 'کد QR کار را سریع می‌کند، اما می‌تواند هر مقصدی را پنهان کند. کلاه‌بردار ممکن است برچسب QR جعلی را روی کد واقعی پرداخت بچسباند.\n\nپیش از اسکن بپرسید: این کد را چه کسی و در چه مکانی گذاشته است؟ پس از اسکن، مقصد را ببینید. اگر صفحه‌ای شبیه ورود بانک باز شد، با احتیاط برخورد کنید.\n\nاز بررسی‌گر QR در AEGIS استفاده کنید تا مقصد بدون بازکردن ناایمن آن بررسی شود.',
        example: 'یک برچسب QR روی دستگاه پارکینگ که به صفحهٔ پرداخت جعلی و جمع‌آوری اطلاعات کارت هدایت می‌کند.',
        tips: ['برای پرداخت از برنامهٔ رسمی استفاده کنید', 'کدهای پوستر یا ایمیل ناشناس را اسکن نکنید', 'پس از اسکن، نشانی مقصد را بررسی کنید'],
      },
    },
    quizzes: {
      'phishing-101': {
        title: 'مبانی فیشینگ', category: 'مبانی', description: 'توانایی خود را در تشخیص تلاش‌های فیشینگ بسنجید.',
        questions: [
          { text: 'پیامکی دریافت می‌کنید: «کارت بانکی شما مسدود می‌شود؛ همین حالا تأیید کنید: http://bit.ly/xyz». چه می‌کنید؟', options: ['برای تأیید سریع روی پیوند می‌زنم', 'پیام را نادیده می‌گیرم و از مسیر رسمی با بانک تماس می‌گیرم', 'رمز یک‌بارمصرف را پاسخ می‌دهم', 'پیام را برای دوستانم می‌فرستم'], explanation: 'بانک‌ها تأیید حساب را از طریق پیوند کوتاه درخواست نمی‌کنند. با شماره یا برنامهٔ رسمی بانک تماس بگیرید.' },
          { text: 'کدام دامنه احتمال بیشتری دارد که فیشینگ باشد؟', options: ['https://www.paypal.com', 'https://paypal-secure-verify.tk', 'https://www.amazon.com/gp/buy', 'https://github.com'], explanation: 'ترکیب عبارت‌هایی مانند secure-verify با دامنهٔ رایگان و نامرتبط، نشانهٔ رایج فیشینگ است.' },
          { text: 'آیا اشتراک‌گذاشتن رمز یک‌بارمصرف پیامکی با تماس‌گیرنده‌ای از «امنیت بانک» ایمن است؟', options: ['بله، برای محافظت از من به آن نیاز دارند', 'فقط اگر نام مرا بدانند', 'خیر، رمز را با هیچ‌کس به اشتراک نمی‌گذارم', 'بله، اگر شماره رسمی به نظر برسد'], explanation: 'رمز تأیید از حساب شما محافظت می‌کند. هیچ سرویس معتبر برای کار خود به گفتن رمز توسط شما نیاز ندارد.' },
          { text: 'قرعه‌کشی می‌گوید ۵ میلیارد تومان برنده شده‌اید اما باید ابتدا «هزینهٔ پردازش» بپردازید. این چیست؟', options: ['روند عادی دریافت جایزه', 'کلاه‌برداری قرعه‌کشی', 'قانون مالیاتی معتبر', 'برنامهٔ دولتی'], explanation: 'جایزهٔ واقعی هزینهٔ اولیه نمی‌خواهد. پرداخت پول پیش از دریافت پاداش، الگوی شناخته‌شدهٔ کلاه‌برداری است.' },
        ],
      },
      'url-security': {
        title: 'امنیت نشانی وب و وب‌سایت', category: 'ایمنی وب', description: 'پیش از کلیک، یاد بگیرید پیوندها را ارزیابی کنید.',
        questions: [
          { text: 'نماد قفل در نوار نشانی یعنی چه؟', options: ['وب‌سایت صددرصد امن است', 'ارتباط رمزگذاری شده است', 'وب‌سایت تأیید دولتی دارد', 'رایانهٔ شما ویروس ندارد'], explanation: 'HTTPS مسیر ارتباط را رمزگذاری می‌کند، اما معتبر بودن خود وب‌سایت را ثابت نمی‌کند.' },
          { text: 'کدام نشانی نمونهٔ تایپواسکوات است؟', options: ['https://www.amazon.com', 'https://www.amzon.com', 'https://aws.amazon.com', 'https://www.google.com/maps'], explanation: 'amzon.com یک حرف از amazon.com کم دارد؛ این نمونه‌ای از دامنهٔ شبیه‌سازی‌شده است.' },
          { text: 'کویشینگ چیست؟', options: ['نوعی ماهی', 'فیشینگ با کد QR', 'ابزار هک', 'به‌روزرسانی امنیتی'], explanation: 'کویشینگ از کدهای QR برای بردن قربانی به صفحهٔ ورود یا پرداخت جعلی استفاده می‌کند.' },
        ],
      },
    },
    scenarios: {
      'sms-delivery-fee': { title: 'دام هزینهٔ تحویل', category: 'تحویل', content: 'پیامک از یک شمارهٔ ناشناس:\n\n«مرسولهٔ شما در گمرک نگه داشته شده است. برای آزادسازی، همین حالا ۳٫۵۰ پوند از این پیوند بپردازید: http://cutt.ly/parcel-fee»', options: ['روی پیوند می‌زنم و هزینه را می‌پردازم', 'ابتدا رهگیری را در وب‌سایت رسمی شرکت حمل‌ونقل بررسی می‌کنم', 'نشانی خود را پاسخ می‌دهم', 'تصویر برنامهٔ پرداخت را می‌فرستم'], explanation: 'شرکت حمل‌ونقل هزینهٔ گمرکی را با پیوند کوتاه جمع‌آوری نمی‌کند. هزینهٔ واقعی از صفحهٔ رسمی رهگیری پرداخت می‌شود.', redFlags: ['پیوند کوتاه', 'هزینهٔ فوری', 'شمارهٔ ناشناس', 'درخواست پول با پیامک'] },
      'friend-help': { title: 'دوست گرفتار', category: 'مهندسی اجتماعی', content: 'پیام از «مدیر» شما:\n\n«در جلسه‌ام و تلفنم خراب شده. فوری باید ۵ کارت هدیه بخری و کدها را برایم بفرستی. برای یک مشتری است؛ بین خودمان بماند.»', options: ['فوراً کارت هدیه می‌خرم', 'با شمارهٔ رسمی مدیر تماس می‌گیرم و تأیید می‌کنم', 'کدها را می‌فرستم و بعد سؤال می‌کنم', 'به‌جای کارت هدیه پول انتقال می‌دهم'], explanation: 'درخواست کارت هدیه از طرف یک فرد دارای اختیار، الگوی رایج کلاه‌برداری است. همیشه از کانال دوم تأیید کنید.', redFlags: ['درخواست کارت هدیه', 'فوریت', 'درخواست پنهان‌کاری', 'شمارهٔ تازه'] },
      'gov-warrant': { title: 'حکم بازداشت', category: 'دولتی', content: 'تماس از «افسر پلیس»:\n\n«پروندهٔ مالیاتی شما در حال بررسی است. اگر تا دو ساعت ۱۲۰۰ دلار جریمه نپردازید، حکم بازداشت صادر می‌شود.»', options: ['برای جلوگیری از بازداشت فوراً می‌پردازم', 'تماس را قطع و از کانال رسمی دولتی بررسی می‌کنم', 'شمارهٔ ملی‌ام را می‌گویم', 'می‌پرسم با کارت هدیه پرداخت کنم'], explanation: 'پلیس واقعی با تهدید بازداشت فوری از طریق تماس تلفنی پول درخواست نمی‌کند.', redFlags: ['تهدید بازداشت فوری', 'درخواست پرداخت', 'جعل هویت پلیس', 'فشار زمانی'] },
    },
  };

  let lessons = [], quizzes = [], scenarios = [], activeCat = 'all', currentQuiz = null;
  const isFa = () => window.AegisI18n?.locale?.() === 'fa';
  const ui = (key, fallback) => isFa() ? (fa.ui[key] || fallback) : fallback;
  const localizeLesson = (lesson) => isFa() && fa.lessons[lesson.slug] ? { ...lesson, ...fa.lessons[lesson.slug] } : lesson;
  const localizeQuiz = (quiz) => {
    const local = isFa() ? fa.quizzes[quiz.slug] : null;
    if (!local) return quiz;
    return { ...quiz, ...local, questions: (quiz.questions || []).map((question, index) => ({ ...question, ...(local.questions[index] || {}) })) };
  };
  const localizeScenario = (scenario) => isFa() && fa.scenarios[scenario.slug] ? { ...scenario, ...fa.scenarios[scenario.slug] } : scenario;
  const pre = (text) => `<div class="whitespace-pre-wrap text-sm leading-relaxed">${esc(text || '')}</div>`;
  const isActive = (dom) => dom.lessons?.isConnected && dom.detail?.isConnected;

  function dom() {
    return {
      lessons: document.getElementById('lessons'), detail: document.getElementById('lesson-detail'),
      quizzes: document.getElementById('quizzes'), progress: document.getElementById('progress'),
      simulator: document.getElementById('simulator'), scenarioSelect: document.getElementById('scenario-select'),
    };
  }

  async function loadProgress(view) {
    if (!view.progress) return;
    try {
      const p = await api('GET', '/api/v1/learning/progress');
      if (!view.progress.isConnected) return;
      view.progress.innerHTML = `<div class="flex items-center justify-between"><span>${ui('level', 'Level')}</span><span class="font-mono text-aegis-600 dark:text-aegis-400 font-semibold">${esc(isFa() && p.level === 'Novice' ? ui('novice', 'Novice') : p.level || 'Novice')}</span></div><div class="flex items-center justify-between"><span>${ui('points', 'Points')}</span><span class="font-mono">${p.points ?? 0}</span></div><div class="flex items-center justify-between"><span>${ui('lessonsCompleted', 'Lessons completed')}</span><span class="font-mono">${p.lessons_completed ?? 0} / ${p.lessons_total ?? 0}</span></div><div class="h-2 rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-2 rounded-full bg-aegis-500" style="width:${(p.lessons_total ?? 1) ? Math.min(100, (p.lessons_completed ?? 0) / p.lessons_total * 100) : 0}%"></div></div><div class="flex items-center justify-between"><span>${ui('quizzesPassed', 'Quizzes passed')}</span><span class="font-mono">${p.quizzes_passed ?? 0} / ${p.quizzes_total ?? 0}</span></div><div class="flex items-center justify-between"><span>${ui('simulatorStreak', 'Simulator streak')}</span><span class="font-mono">${p.streak ?? 0}</span></div><div class="flex items-center justify-between"><span>${ui('certificates', 'Certificates')}</span><span class="font-mono">${(p.certificates || []).length}</span></div>`;
    } catch (_) { if (view.progress.isConnected) view.progress.innerHTML = `<p class="text-sm text-slate-400">${ui('signInProgress', 'Sign in to track progress.')}</p>`; }
  }

  function categoryMatches(lesson) {
    const categories = { all: null, phishing: ['Basics'], identity: ['Personal Safety'], tech: ['Web Safety'] };
    return !categories[activeCat] || categories[activeCat].includes(lesson.category);
  }

  function renderLessons(view) {
    if (!isActive(view)) return;
    const list = lessons.filter(categoryMatches);
    if (!list.length) { view.lessons.innerHTML = `<p class="text-sm text-slate-400 py-8 text-center">${ui('noLessons', 'No lessons in this category yet.')}</p>`; return; }
    view.lessons.innerHTML = list.map((raw) => {
      const lesson = localizeLesson(raw);
      return `<button class="lesson-card w-full text-start p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-zinc-900/90 hover:border-aegis-500/50 transition" data-slug="${esc(lesson.slug)}"><div class="flex items-center justify-between gap-3 mb-1"><h3 class="font-semibold" dir="auto">${esc(lesson.title)}</h3><span class="px-2 py-0.5 rounded-full text-xs bg-aegis-50 dark:bg-aegis-950/60 text-aegis-700 dark:text-aegis-200">${esc(lesson.category)}</span></div><p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2" dir="auto">${esc(lesson.summary || '')}</p></button>`;
    }).join('');
    view.lessons.querySelectorAll('.lesson-card').forEach((card) => card.addEventListener('click', () => openLesson(card.dataset.slug, view)));
  }

  function renderQuizzes(view) {
    if (!view.quizzes?.isConnected) return;
    if (!quizzes.length) { view.quizzes.innerHTML = `<p class="text-sm text-slate-400">${ui('noQuizzes', 'No quizzes available.')}</p>`; return; }
    view.quizzes.innerHTML = quizzes.map((raw) => {
      const quiz = localizeQuiz(raw);
      return `<button class="quiz-card w-full text-start px-3 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-zinc-900/90 hover:border-aegis-500/50 text-sm transition" data-slug="${esc(quiz.slug)}"><span class="font-medium" dir="auto">${esc(quiz.title)}</span><span class="block text-xs text-slate-400 mt-0.5" dir="auto">${esc(quiz.description || quiz.category || '')} · ${ui('pass', 'pass')} ${quiz.pass_percent ?? 80}%</span></button>`;
    }).join('');
    view.quizzes.querySelectorAll('.quiz-card').forEach((card) => card.addEventListener('click', () => startQuiz(card.dataset.slug, view)));
  }

  async function openLesson(slug, view) {
    try {
      const lesson = localizeLesson(await api('GET', `/api/v1/learning/lessons/${slug}`));
      if (!isActive(view)) return;
      view.lessons.classList.add('hidden'); view.detail.classList.remove('hidden');
      view.detail.innerHTML = `<div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-zinc-900/95"><div class="flex items-center justify-between gap-4 mb-4"><h2 class="text-xl font-bold" dir="auto">${esc(lesson.title)}</h2><button class="lesson-back text-sm text-aegis-600 dark:text-aegis-300 hover:underline">${ui('allLessons', 'All lessons')} ←</button></div><p class="text-xs text-slate-400 mb-4">${esc(lesson.category || '')} · ${lesson.reading_time ? `${esc(String(lesson.reading_time))} ${ui('minutes', 'min')}` : ''}</p>${pre(lesson.content)}${lesson.example ? `<h3 class="font-semibold mt-6 mb-2">${ui('example', 'Example')}</h3>${pre(lesson.example)}` : ''}${(lesson.tips || []).length ? `<h3 class="font-semibold mt-6 mb-2">${ui('tips', 'Key tips')}</h3><ul class="list-disc ps-5 space-y-1 text-sm">${lesson.tips.map((tip) => `<li>${esc(tip)}</li>`).join('')}</ul>` : ''}<div class="mt-6 flex gap-3"><button class="lesson-complete px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition">${ui('markComplete', 'Mark complete')}</button></div></div>`;
      view.detail.querySelector('.lesson-back').addEventListener('click', () => { view.detail.classList.add('hidden'); view.lessons.classList.remove('hidden'); });
      view.detail.querySelector('.lesson-complete').addEventListener('click', async (event) => {
        try { await api('POST', `/api/v1/learning/lessons/${slug}/progress`, { progress: 1, completed: true }); if (!event.currentTarget.isConnected) return; toast(ui('lessonCompleted', 'Lesson completed'), 'success'); event.currentTarget.textContent = `✓ ${ui('completed', 'Completed')}`; event.currentTarget.disabled = true; loadProgress(view); } catch (error) { toast(error.message, 'error'); }
      });
    } catch (error) { if (isActive(view)) toast(error.message, 'error'); }
  }

  async function startQuiz(slug, view) {
    if (!isActive(view)) return;
    view.lessons.classList.add('hidden'); view.detail.classList.remove('hidden');
    try { currentQuiz = localizeQuiz(await api('GET', `/api/v1/learning/quizzes/${slug}`)); if (isActive(view)) renderQuizQuestion(0, [], view); } catch (error) { if (isActive(view)) toast(error.message, 'error'); }
  }

  function randomUnit() {
    if (window.crypto?.getRandomValues) {
      const value = new Uint32Array(1);
      window.crypto.getRandomValues(value);
      return value[0] / 0x100000000;
    }
    return Math.random();
  }

  function shuffledChoices(options) {
    const choices = (options || []).map((text, originalIndex) => ({ text, originalIndex }));
    for (let index = choices.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(randomUnit() * (index + 1));
      [choices[index], choices[swapIndex]] = [choices[swapIndex], choices[index]];
    }
    return choices;
  }

  function renderQuizQuestion(index, answers, view) {
    if (!isActive(view) || !currentQuiz) return;
    const questions = currentQuiz.questions || [];
    if (index >= questions.length) { submitQuiz(answers.map((answer) => Number(answer)), view); return; }
    const question = questions[index];
    const choices = shuffledChoices(question.options);
    view.detail.innerHTML = `<div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-zinc-900/95"><div class="flex items-center justify-between mb-4"><h2 class="text-lg font-bold" dir="auto">${esc(currentQuiz.title)}</h2><span class="text-sm text-slate-400">${ui('question', 'Question')} ${index + 1} / ${questions.length}</span></div><p class="font-medium mb-4" dir="auto">${esc(question.text || question.question || '')}</p><div class="space-y-2 mb-6" id="quiz-options">${choices.map((choice) => `<button class="quiz-option w-full text-start px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-aegis-500 transition" data-i="${choice.originalIndex}" dir="auto">${esc(choice.text)}</button>`).join('')}</div><button class="quiz-next px-4 py-2 rounded-lg bg-aegis-600 hover:bg-aegis-500 text-white text-sm font-semibold transition hidden">${ui('next', 'Next')}</button></div>`;
    view.detail.querySelectorAll('.quiz-option').forEach((button) => button.addEventListener('click', () => { view.detail.querySelectorAll('.quiz-option').forEach((node) => node.classList.remove('border-aegis-500', 'bg-aegis-50', 'dark:bg-aegis-950')); button.classList.add('border-aegis-500', 'bg-aegis-50', 'dark:bg-aegis-950'); answers[index] = Number(button.dataset.i); const next = view.detail.querySelector('.quiz-next'); next.classList.remove('hidden'); next.onclick = () => renderQuizQuestion(index + 1, answers, view); }));
  }

  async function submitQuiz(answers, view) {
    try {
      const result = await api('POST', `/api/v1/learning/quizzes/${currentQuiz.slug}/submit`, { answers });
      if (!isActive(view)) return;
      const score = Math.round(result.score_percent || 0);
      const explanations = (result.explanations || []).map((entry, index) => { const question = currentQuiz.questions[index] || {}; return `<div class="p-3 rounded-lg border ${entry.correct ? 'border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/30' : 'border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30'} text-sm"><p class="font-medium" dir="auto">${esc(question.text || entry.question || '')}</p><p class="text-xs text-slate-500 mt-1" dir="auto">${ui('yourAnswer', 'Your answer')}: ${esc(question.options?.[answers[index]] || entry.your_answer || '')} · ${ui('correct', 'Correct')}: ${esc(question.options?.[entry.correct_index] || entry.correct_answer || '')}</p>${question.explanation || entry.explanation ? `<p class="text-xs mt-1" dir="auto">${esc(question.explanation || entry.explanation)}</p>` : ''}</div>`; }).join('');
      view.detail.innerHTML = `<div class="p-6 rounded-2xl border ${score >= (currentQuiz.pass_percent || 80) ? 'border-emerald-500/50' : 'border-amber-500/50'} bg-white/95 dark:bg-zinc-900/95"><div class="text-center mb-6"><p class="text-5xl font-bold mb-2 ${score >= (currentQuiz.pass_percent || 80) ? 'text-emerald-500' : 'text-amber-500'}">${score}%</p><p class="text-slate-600 dark:text-slate-300">${result.passed ? ui('passed', 'Great job! You passed the quiz.') : ui('retry', 'Keep learning and try again.')}</p>${result.certificate_code ? `<p class="text-sm text-aegis-600 dark:text-aegis-300 mt-2">${ui('certificate', 'Certificate')}: <span class="font-mono">${esc(result.certificate_code)}</span></p>` : ''}<a href="/learn" class="inline-block mt-6 px-4 py-2 rounded-lg bg-aegis-600 hover:bg-aegis-500 text-white text-sm font-semibold">${ui('back', 'Back to Learning Center')}</a></div><div class="space-y-2">${explanations}</div></div>`;
      loadProgress(view);
    } catch (error) { if (isActive(view)) toast(error.message, 'error'); }
  }

  function renderScenarios(view) {
    if (!view.scenarioSelect?.isConnected) return;
    view.scenarioSelect.innerHTML = `<option value="">${isFa() ? 'یک سناریو انتخاب کنید…' : 'Choose a scenario…'}</option>`;
    scenarios.forEach((raw) => { const scenario = localizeScenario(raw); const option = document.createElement('option'); option.value = scenario.id; option.textContent = scenario.title; view.scenarioSelect.appendChild(option); });
  }

  function showScenario(raw, view) {
    if (!view.simulator?.isConnected) return;
    const scenario = localizeScenario(raw);
    const choices = shuffledChoices(scenario.options);
    view.simulator.innerHTML = `<p class="font-medium mb-3 whitespace-pre-wrap text-sm" dir="auto">${esc(scenario.content || '')}</p><p class="text-xs text-slate-500 mb-3">${ui('whatWouldYouDo', 'What would you do?')}</p><div class="space-y-2">${choices.map((choice) => `<button class="sim-choice w-full text-start px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-aegis-500 text-sm transition" data-i="${choice.originalIndex}" dir="auto">${esc(choice.text)}</button>`).join('')}</div><div class="sim-result mt-4"></div>`;
    view.simulator.querySelectorAll('.sim-choice').forEach((button) => button.addEventListener('click', async () => {
      try {
        const result = await api('POST', '/api/v1/learning/simulator/answer', { scenario_id: scenario.id, chosen_index: Number(button.dataset.i) });
        if (!view.simulator.isConnected) return;
        const flags = isFa() ? (scenario.redFlags || []) : (result.red_flags || []);
        const redFlags = flags.map((flag) => `<span class="px-2 py-0.5 rounded bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-200 text-xs">${esc(flag)}</span>`).join(' ');
        view.simulator.querySelector('.sim-result').innerHTML = `<div class="p-3 rounded-lg ${result.correct ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-200' : 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-200'} text-sm"><p class="font-semibold">${result.correct ? `✓ ${ui('correctChoice', 'Correct!')}` : `✗ ${ui('incorrectChoice', 'Not quite.')}`}</p><p class="mt-1" dir="auto">${esc(isFa() ? scenario.explanation : result.explanation || '')}</p>${redFlags ? `<div class="flex flex-wrap gap-2 mt-2">${redFlags}</div>` : ''}${result.streak ? `<p class="text-xs mt-2 text-slate-500">${ui('streak', 'Streak')}: ${result.streak}</p>` : ''}</div>`;
        view.simulator.querySelectorAll('.sim-choice').forEach((node) => { node.disabled = true; }); loadProgress(view);
      } catch (error) { if (view.simulator.isConnected) toast(error.message, 'error'); }
    }));
  }

  window.Aegis.onPageLoad('learn', async () => {
    const view = dom();
    if (!isActive(view)) return;
    lessons = []; quizzes = []; scenarios = []; activeCat = 'all'; currentQuiz = null;
    document.querySelectorAll('.lesson-filter').forEach((button) => button.addEventListener('click', () => { if (!isActive(view)) return; document.querySelectorAll('.lesson-filter').forEach((node) => { node.classList.remove('bg-white', 'dark:bg-slate-900', 'shadow', 'text-aegis-600', 'dark:text-aegis-400'); node.classList.add('text-slate-500'); }); button.classList.add('bg-white', 'dark:bg-slate-900', 'shadow', 'text-aegis-600', 'dark:text-aegis-400'); activeCat = button.dataset.cat; renderLessons(view); }));
    view.scenarioSelect?.addEventListener('change', (event) => { const scenario = scenarios.find((item) => String(item.id) === event.target.value); if (scenario) showScenario(scenario, view); });
    try { const response = await api('GET', '/api/v1/learning/lessons'); if (!isActive(view)) return; lessons = Array.isArray(response) ? response : (response.lessons || []); renderLessons(view); } catch (error) { if (view.lessons?.isConnected) view.lessons.innerHTML = `<p class="text-sm text-red-500">${esc(error.message)}</p>`; }
    try { const response = await api('GET', '/api/v1/learning/quizzes'); if (!isActive(view)) return; quizzes = Array.isArray(response) ? response : (response.quizzes || []); renderQuizzes(view); } catch (_) { if (view.quizzes?.isConnected) view.quizzes.innerHTML = `<p class="text-sm text-slate-400">${ui('noQuizzes', 'No quizzes available.')}</p>`; }
    try { const response = await api('GET', '/api/v1/learning/simulator'); if (!isActive(view)) return; scenarios = Array.isArray(response) ? response : (response.scenarios || []); renderScenarios(view); } catch (_) { /* simulator remains optional */ }
    loadProgress(view);
  });
})();
