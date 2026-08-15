/* AEGIS core frontend helpers */
(function () {
    'use strict';

    const CSRF = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = CSRF ? CSRF.content : '';

    const esc = (s) =>
        String(s ?? '').replace(/[&<>"']/g, (c) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[c]));

    async function api(method, path, body, isForm) {
        const opts = { method, credentials: 'same-origin', headers: {} };
        if (isForm) {
            opts.body = body;
        } else if (body !== undefined) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
        if (method !== 'GET') opts.headers['X-CSRF-Token'] = csrfToken;
        const res = await fetch(path, opts);
        let data = null;
        const ct = res.headers.get('content-type') || '';
        if (ct.includes('application/json')) data = await res.json();
        else data = { detail: await res.text() };
        if (!res.ok) throw Object.assign(new Error(data.detail || data.error || 'Request failed'), { status: res.status, data });
        return data;
    }

    function toast(message, type = 'info') {
        const root = document.getElementById('toast-root');
        if (!root) return;
        const colors = {
            success: 'border-emerald-500 text-emerald-700 dark:text-emerald-300',
            error: 'border-red-500 text-red-700 dark:text-red-300',
            info: 'border-aegis-500 text-slate-700 dark:text-slate-200',
        };
        const el = document.createElement('div');
        el.className = `px-4 py-3 rounded-lg border bg-white dark:bg-slate-900 shadow-lg text-sm max-w-sm animate-float ${colors[type] || colors.info}`;
        el.textContent = message;
        root.appendChild(el);
        setTimeout(() => el.remove(), 4000);
    }

    function setTheme(theme) {
        const resolvedTheme = theme === 'dark' ? 'dark' : 'light';
        document.documentElement.classList.toggle('dark', resolvedTheme === 'dark');
        document.documentElement.dataset.themePreference = resolvedTheme;
        try { localStorage.setItem('aegis-theme', resolvedTheme); } catch (e) { }
    }

    function getTheme() {
        try {
            const serverTheme = document.documentElement.dataset.themePreference;
            return serverTheme || localStorage.getItem('aegis-theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        } catch (e) { return document.documentElement.classList.contains('dark') ? 'dark' : 'light'; }
    }

    function translate(key, fallback) {
        return window.AegisI18n?.t ? window.AegisI18n.t(key, fallback) : fallback;
    }

    function badgeFor(level) {
        const map = {
            safe: ['bg-emerald-500', translate('verdict.safe', 'Safe')],
            suspicious: ['bg-amber-500', translate('verdict.suspicious', 'Suspicious')],
            threat: ['bg-red-500', translate('verdict.threat', 'Threat')],
            unverified: ['bg-slate-500', translate('verdict.unverified', 'Unverified')],
        };
        const [cls, label] = map[level] || ['bg-slate-500', level];
        return `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold text-white ${cls}">${label}</span>`;
    }

    function fmtTime(iso) {
        if (!iso) return '—';
        return new Date(iso).toLocaleString();
    }

    function navigate(path) {
        window.location.href = path;
    }

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const action = btn.dataset.action;
        if (action === 'logout') {
            e.preventDefault();
            api('POST', '/api/v1/auth/logout').finally(() => navigate('/login'));
        } else if (action === 'toggle-theme') {
            setTheme(document.documentElement.classList.contains('dark') ? 'light' : 'dark');
        } else if (action === 'notifications') {
            toggleNotifications();
        }
    });

    function toggleNotifications() {
        const panel = document.getElementById('notif-panel');
        if (!panel) return;
        if (!panel.classList.contains('hidden')) { panel.classList.add('hidden'); return; }
        panel.classList.remove('hidden');
        api('GET', '/api/v1/notifications').then((data) => {
            const items = data.notifications || [];
            const badge = document.getElementById('notif-badge');
            if (badge) {
                const unread = items.filter((n) => !n.read).length;
                badge.classList.toggle('hidden', unread === 0);
                badge.textContent = unread;
            }
            if (!items.length) {
                panel.innerHTML = '<p class="p-4 text-sm text-slate-400">No notifications yet.</p>';
                return;
            }
            panel.innerHTML = items.map((n) => `
        <div class="p-3 border-b border-slate-100 dark:border-slate-800 text-sm ${n.read ? '' : 'bg-aegis-50 dark:bg-aegis-950/40'}">
          <p class="font-medium">${esc(n.title)}</p>
          <p class="text-xs text-slate-500 mt-0.5">${esc(n.message)}</p>
          <p class="text-xs text-slate-400 mt-1">${fmtTime(n.created_at)}</p>
        </div>`).join('');
        }).catch(() => { });
    }

    function connectSSE() {
        if (!window.EventSource || !document.body.dataset.page || document.body.dataset.page === 'login') return;
        // Check if user is authenticated by looking for session cookie or user data
        const userData = document.body.dataset.user;
        if (!userData) return;
        try {
            const es = new EventSource('/api/v1/notifications/stream');
            es.onmessage = (ev) => {
                let data;
                try { data = JSON.parse(ev.data); } catch (e) { return; }
                if (data.unread_count !== undefined) {
                    const badge = document.getElementById('notif-badge');
                    if (badge) {
                        badge.textContent = data.unread_count;
                        badge.classList.toggle('hidden', data.unread_count === 0);
                    }
                }
                if (data.event) toast(data.event, 'info');
            };
            es.onerror = () => {
                // Only retry if not a 401/403 error
                setTimeout(connectSSE, 15000);
            };
            window.__aegis_sse = es;
        } catch (e) {
            // Silently fail for unauthenticated users
            console.debug('SSE connection skipped');
        }
    }

    const pageReadyEvent = window.Turbo ? 'turbo:load' : 'DOMContentLoaded';
    const pageModules = window.__aegisPageModules || new Map();
    const completedPageModules = window.__aegisCompletedPageModules || new Set();
    window.__aegisPageModules = pageModules;
    window.__aegisCompletedPageModules = completedPageModules;
    if (window.Turbo && !window.__aegisTurboModuleResetBound) {
        document.addEventListener('turbo:before-render', () => completedPageModules.clear());
        window.__aegisTurboModuleResetBound = true;
    }
    function onPageLoad(moduleName, callback) {
        let entry = pageModules.get(moduleName);
        if (!entry) {
            entry = {
                callback,
                run: () => {
                    if (completedPageModules.has(moduleName)) return;
                    completedPageModules.add(moduleName);
                    pageModules.get(moduleName).callback();
                },
            };
            pageModules.set(moduleName, entry);
            document.addEventListener(pageReadyEvent, entry.run);
        } else {
            entry.callback = callback;
        }
        if (document.readyState !== 'loading') entry.run();
    }

    window.Aegis = { api, toast, esc, badgeFor, fmtTime, navigate, setTheme, getTheme, csrfToken, t: translate, onPageLoad };
    window.dispatchEvent(new Event('aegis:ready'));

    document.addEventListener(pageReadyEvent, () => {
        setTheme(getTheme());

        const overlay = document.getElementById('sidebar-overlay');
        const toggle = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('sidebar');
        if (toggle && sidebar) {
            toggle.addEventListener('click', () => {
                sidebar.classList.toggle('-translate-x-full');
                if (overlay) overlay.classList.toggle('hidden');
            });
            if (overlay) overlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            });
        }

        const searchForm = document.querySelector('form[data-action="search"]');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const q = document.getElementById('global-search').value.trim();
                if (q) navigate('/search?q=' + encodeURIComponent(q));
            });
        }

        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.addEventListener('change', async () => {
                const locale = languageSelect.value;
                languageSelect.disabled = true;
                try {
                    document.cookie = `aegis_locale=${encodeURIComponent(locale)}; Path=/; Max-Age=31536000; SameSite=Lax`;
                    if (document.body.dataset.authenticated === 'true') {
                        await api('PATCH', '/api/v1/users/me', { locale });
                    }
                    // Reload so Flask renders lang/dir before the page is visible.
                    window.location.reload();
                } catch (error) {
                    toast(error.message || 'Could not update language', 'error');
                    languageSelect.value = document.documentElement.lang || 'en';
                } finally {
                    languageSelect.disabled = false;
                }
            });
        }

        connectSSE();
    });

})();
