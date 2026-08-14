/* Learning center */
(function () {
    'use strict';
    const { api, esc, toast } = window.Aegis;
    let lessons = [];
    let quizzes = [];
    let scenarios = [];
    let activeCat = 'all';
    let currentLesson = null;
    let currentQuiz = null;

    const pre = (t) => `<div class="whitespace-pre-wrap text-sm leading-relaxed">${esc(t)}</div>`;

    async function loadProgress() {
        const box = document.getElementById('progress');
        try {
            const p = await api('GET', '/api/v1/learning/progress');
            box.innerHTML = `
        <div class="flex items-center justify-between">
          <span>Level</span><span class="font-mono text-aegis-600 dark:text-aegis-400 font-semibold">${esc(p.level || 'Novice')}</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Points</span><span class="font-mono">${p.points ?? 0}</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Lessons completed</span><span class="font-mono">${p.lessons_completed ?? 0} / ${p.lessons_total ?? 0}</span>
        </div>
        <div class="h-2 rounded-full bg-slate-200 dark:bg-slate-800"><div class="h-2 rounded-full bg-aegis-500" style="width:${(p.lessons_total ?? 1) ? Math.min(100, (p.lessons_completed ?? 0) / p.lessons_total * 100) : 0}%"></div></div>
        <div class="flex items-center justify-between">
          <span>Quizzes passed</span><span class="font-mono">${p.quizzes_passed ?? 0} / ${p.quizzes_total ?? 0}</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Simulator streak</span><span class="font-mono">${p.streak ?? 0}</span>
        </div>
        <div class="flex items-center justify-between">
          <span>Certificates</span><span class="font-mono">${(p.certificates || []).length}</span>
        </div>`;
        } catch (e) {
            box.innerHTML = '<p class="text-sm text-slate-400">Sign in to track progress.</p>';
        }
    }

    function renderLessons() {
        const box = document.getElementById('lessons');
        const list = lessons.filter((l) => activeCat === 'all' || l.category === activeCat);
        if (!list.length) {
            box.innerHTML = '<p class="text-sm text-slate-400 py-8 text-center">No lessons in this category yet.</p>';
            return;
        }
        box.innerHTML = list.map((l) => `
      <button class="lesson-card w-full text-left p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-aegis-500/50 transition" data-slug="${esc(l.slug)}">
        <div class="flex items-center justify-between mb-1">
          <h3 class="font-semibold">${esc(l.title)}</h3>
          <span class="px-2 py-0.5 rounded-full text-xs bg-aegis-50 dark:bg-aegis-950 text-aegis-700 dark:text-aegis-300">${esc(l.category)}</span>
        </div>
        <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">${esc(l.summary || '')}</p>
      </button>`).join('');
        box.querySelectorAll('.lesson-card').forEach((c) => c.addEventListener('click', () => openLesson(c.dataset.slug)));
    }

    function renderQuizzes() {
        const box = document.getElementById('quizzes');
        if (!quizzes.length) {
            box.innerHTML = '<p class="text-sm text-slate-400">No quizzes available.</p>';
            return;
        }
        box.innerHTML = quizzes.map((q) => `
      <button class="quiz-card w-full text-left px-3 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-aegis-500/50 text-sm transition" data-slug="${esc(q.slug)}">
        <span class="font-medium">${esc(q.title)}</span>
        <span class="block text-xs text-slate-400 mt-0.5">${esc(q.description || q.category || '')} · pass ${q.pass_percent ?? 80}%</span>
      </button>`).join('');
        box.querySelectorAll('.quiz-card').forEach((c) => c.addEventListener('click', () => startQuiz(c.dataset.slug)));
    }

    async function openLesson(slug) {
        const detail = document.getElementById('lesson-detail');
        const list = document.getElementById('lessons');
        try {
            const res = await api('GET', `/api/v1/learning/lessons/${slug}`);
            const l = res.lesson || res;
            currentLesson = l;
            list.classList.add('hidden');
            detail.classList.remove('hidden');
            detail.innerHTML = `
        <div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold">${esc(l.title)}</h2>
            <button class="lesson-back text-sm text-aegis-600 dark:text-aegis-400 hover:underline">← All lessons</button>
          </div>
          <p class="text-xs text-slate-400 mb-4">${esc(l.category || '')} · ${l.reading_time ? esc(String(l.reading_time)) + ' min' : ''}</p>
          ${pre(l.content || '')}
          ${l.example ? `<h3 class="font-semibold mt-6 mb-2">Example</h3>${pre(l.example)}` : ''}
          ${(l.tips || []).length ? `<h3 class="font-semibold mt-6 mb-2">Key tips</h3><ul class="list-disc pl-5 space-y-1 text-sm">${l.tips.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
          <div class="mt-6 flex gap-3">
            <button class="lesson-complete px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition">Mark complete</button>
          </div>
        </div>`;
            detail.querySelector('.lesson-back').addEventListener('click', () => {
                detail.classList.add('hidden'); list.classList.remove('hidden');
            });
            detail.querySelector('.lesson-complete').addEventListener('click', async (e) => {
                try {
                    await api('POST', `/api/v1/learning/lessons/${slug}/progress`, { progress: 1, completed: true });
                    toast('Lesson completed', 'success');
                    e.target.textContent = '✓ Completed'; e.target.disabled = true;
                    loadProgress();
                } catch (err) { toast(err.message, 'error'); }
            });
        } catch (e) { toast(e.message, 'error'); }
    }

    async function startQuiz(slug) {
        const detail = document.getElementById('lesson-detail');
        const list = document.getElementById('lessons');
        list.classList.add('hidden');
        detail.classList.remove('hidden');
        try {
            currentQuiz = await api('GET', `/api/v1/learning/quizzes/${slug}`);
            renderQuizQuestion(0, []);
        } catch (e) { toast(e.message, 'error'); }
    }

    function renderQuizQuestion(idx, answers) {
        const detail = document.getElementById('lesson-detail');
        const questions = (currentQuiz.questions || []);
        if (idx >= questions.length) {
            // Ensure answers is an array before mapping
            const answersArray = Array.isArray(answers) ? answers : [];
            const flatAnswers = answersArray.map(a => typeof a === 'number' ? a : parseInt(a));
            submitQuiz(flatAnswers);
            return;
        }
        const q = questions[idx];
        detail.innerHTML = `
      <div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold">${esc(currentQuiz.title)}</h2>
          <span class="text-sm text-slate-400">${idx + 1} / ${questions.length}</span>
        </div>
        <p class="font-medium mb-4">${esc(q.text || q.question || '')}</p>
        <div class="space-y-2 mb-6" id="quiz-options">
          ${(q.options || []).map((o, i) => `
            <button class="quiz-option w-full text-left px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-aegis-500 transition" data-i="${i}">
              ${esc(o)}
            </button>`).join('')}
        </div>
        <button class="quiz-next px-4 py-2 rounded-lg bg-aegis-600 hover:bg-aegis-500 text-white text-sm font-semibold transition hidden">Next</button>
      </div>`;
        detail.querySelectorAll('.quiz-option').forEach((b) => b.addEventListener('click', () => {
            detail.querySelectorAll('.quiz-option').forEach((x) => x.classList.remove('border-aegis-500', 'bg-aegis-50', 'dark:bg-aegis-950'));
            b.classList.add('border-aegis-500', 'bg-aegis-50', 'dark:bg-aegis-950');
            // Store the selected answer in an array at the current index
            answers[idx] = parseInt(b.dataset.i, 10);
            const next = detail.querySelector('.quiz-next');
            next.classList.remove('hidden');
            next.onclick = () => renderQuizQuestion(idx + 1, answers);
        }));
    }

    async function submitQuiz(answers) {
        const detail = document.getElementById('lesson-detail');
        try {
            const res = await api('POST', `/api/v1/learning/quizzes/${currentQuiz.slug}/submit`, { answers });
            const score = Math.round(res.score_percent || 0);
            const explanations = (res.explanations || []).map((x) => `
        <div class="p-3 rounded-lg border ${x.correct ? 'border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40' : 'border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40'} text-sm">
          <p class="font-medium">${esc(x.question)}</p>
          <p class="text-xs text-slate-500 mt-1">Your answer: ${esc(x.your_answer)} · Correct: ${esc(x.correct_answer)}</p>
          ${x.explanation ? `<p class="text-xs mt-1">${esc(x.explanation)}</p>` : ''}
        </div>`).join('');
            detail.innerHTML = `
        <div class="p-6 rounded-2xl border ${score >= (currentQuiz.pass_percent || 80) ? 'border-emerald-500/50' : 'border-amber-500/50'} bg-white dark:bg-slate-900">
          <div class="text-center mb-6">
            <p class="text-5xl font-bold mb-2 ${score >= (currentQuiz.pass_percent || 80) ? 'text-emerald-500' : 'text-amber-500'}">${score}%</p>
            <p class="text-slate-600 dark:text-slate-300">${res.passed ? 'Great job! You passed the quiz.' : 'Keep learning and try again.'}</p>
            ${res.certificate_code ? `<p class="text-sm text-aegis-600 dark:text-aegis-400 mt-2">Certificate: <span class="font-mono">${esc(res.certificate_code)}</span></p>` : ''}
            <a href="/learn" class="inline-block mt-6 px-4 py-2 rounded-lg bg-aegis-600 hover:bg-aegis-500 text-white text-sm font-semibold">Back to Learning Center</a>
          </div>
          <div class="space-y-2">${explanations}</div>
        </div>`;
            loadProgress();
        } catch (e) { toast(e.message, 'error'); }
    }

    function renderScenarios() {
        const sel = document.getElementById('scenario-select');
        scenarios.forEach((s) => {
            const opt = document.createElement('option');
            opt.value = s.id; opt.textContent = s.title;
            sel.appendChild(opt);
        });
    }

    function showScenario(scenario) {
        const box = document.getElementById('simulator');
        box.innerHTML = `
      <p class="font-medium mb-3 whitespace-pre-wrap text-sm">${esc(scenario.content || '')}</p>
      <p class="text-xs text-slate-500 mb-3">What would you do?</p>
      <div class="space-y-2">
        ${(scenario.options || []).map((c, i) => `<button class="sim-choice w-full text-left px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-aegis-500 text-sm transition" data-i="${i}">${esc(c)}</button>`).join('')}
      </div>
      <div id="sim-result" class="mt-4"></div>`;
        box.querySelectorAll('.sim-choice').forEach((b) => b.addEventListener('click', async () => {
            const res = await api('POST', '/api/v1/learning/simulator/answer', {
                scenario_id: scenario.id, chosen_index: parseInt(b.dataset.i, 10),
            });
            const result = document.getElementById('sim-result');
            const redFlags = (res.red_flags || []).map((f) => `<span class="px-2 py-0.5 rounded bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-300 text-xs">${esc(f)}</span>`).join(' ');
            result.innerHTML = `
        <div class="p-3 rounded-lg ${res.correct ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300' : 'bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300'} text-sm">
          <p class="font-semibold">${res.correct ? '✓ Correct!' : '✗ Not quite.'}</p>
          <p class="mt-1">${esc(res.explanation || '')}</p>
          ${redFlags ? `<div class="flex flex-wrap gap-2 mt-2">${redFlags}</div>` : ''}
          ${res.streak ? `<p class="text-xs mt-2 text-slate-500">Streak: ${res.streak}</p>` : ''}
        </div>`;
            box.querySelectorAll('.sim-choice').forEach((x) => x.disabled = true);
            loadProgress();
        }));
    }

    document.addEventListener('DOMContentLoaded', async () => {
        document.querySelectorAll('.lesson-filter').forEach((b) => b.addEventListener('click', () => {
            document.querySelectorAll('.lesson-filter').forEach((x) => {
                x.classList.remove('bg-white', 'dark:bg-slate-900', 'shadow', 'text-aegis-600', 'dark:text-aegis-400');
                x.classList.add('text-slate-500');
            });
            b.classList.add('bg-white', 'dark:bg-slate-900', 'shadow', 'text-aegis-600', 'dark:text-aegis-400');
            activeCat = b.dataset.cat;
            renderLessons();
        }));
        document.getElementById('scenario-select').addEventListener('change', (e) => {
            const s = scenarios.find((x) => String(x.id) === e.target.value);
            if (s) showScenario(s);
        });
        try {
            lessons = await api('GET', '/api/v1/learning/lessons');
            lessons = Array.isArray(lessons) ? lessons : (lessons.lessons || []);
            renderLessons();
        } catch (e) {
            document.getElementById('lessons').innerHTML = `<p class="text-sm text-red-500">${esc(e.message)}</p>`;
        }
        try {
            quizzes = await api('GET', '/api/v1/learning/quizzes');
            quizzes = Array.isArray(quizzes) ? quizzes : (quizzes.quizzes || []);
            renderQuizzes();
        } catch (e) { /* quizzes optional */ }
        try {
            scenarios = await api('GET', '/api/v1/learning/simulator');
            scenarios = Array.isArray(scenarios) ? scenarios : (scenarios.scenarios || []);
            renderScenarios();
        } catch (e) { /* simulator optional */ }
        loadProgress();
    });
})();
