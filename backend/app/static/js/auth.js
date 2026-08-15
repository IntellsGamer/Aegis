/* Auth pages (login / register / forgot / reset) */
(function () {
  'use strict';
  const shared = window.Aegis;
  if (!shared) {
    window.addEventListener('aegis:ready', () => window.location.reload(), { once: true });
    return;
  }
  const { api, toast, navigate, csrfToken, t } = shared;

  window.Aegis.onPageLoad('auth', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('login-btn');
        btn.disabled = true; btn.textContent = t('auth.signing_in', 'Signing in…');
        try {
          const data = await api('POST', '/api/v1/auth/login', {
            identifier: document.getElementById('email').value.trim(),
            password: document.getElementById('password').value,
          });
          toast(t('auth.signed_in', 'Signed in successfully'), 'success');
          navigate(data.redirect_url || '/dashboard');
        } catch (err) {
          toast(err.message, 'error');
          btn.disabled = false; btn.textContent = t('auth.sign_in', 'Sign In');
        }
      });
    }

    const regForm = document.getElementById('register-form');
    if (regForm) {
      regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('register-btn');
        const pw = document.getElementById('password').value;
        const confirm = document.getElementById('confirm').value;
        if (pw !== confirm) { toast(t('auth.password_mismatch', 'Passwords do not match'), 'error'); return; }
        btn.disabled = true; btn.textContent = t('auth.creating_account', 'Creating account…');
        try {
          await api('POST', '/api/v1/auth/register', {
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            password: pw,
          });
          toast(t('auth.account_created', 'Account created — sign in now'), 'success');
          navigate('/login');
        } catch (err) {
          toast(err.message, 'error');
          btn.disabled = false; btn.textContent = t('auth.create_account', 'Create Account');
        }
      });
    }

    const forgotForm = document.getElementById('forgot-form');
    if (forgotForm) {
      forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('forgot-btn');
        btn.disabled = true;
        try {
          await api('POST', '/api/v1/auth/forgot-password', { email: document.getElementById('email').value.trim() });
          toast(t('auth.reset_sent', 'If that email exists, a reset link has been sent.'), 'success');
        } catch (err) {
          toast(err.message, 'error');
        } finally {
          btn.disabled = false;
        }
      });
    }

    const resetForm = document.getElementById('reset-form');
    if (resetForm) {
      resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('reset-btn');
        const pw = document.getElementById('password').value;
        const confirm = document.getElementById('confirm').value;
        if (pw !== confirm) { toast(t('auth.password_mismatch', 'Passwords do not match'), 'error'); return; }
        btn.disabled = true; btn.textContent = t('auth.updating', 'Updating…');
        try {
          await api('POST', '/api/v1/auth/reset-password', {
            email: resetForm.dataset.email,
            token: resetForm.dataset.token,
            new_password: pw,
          });
          toast(t('auth.password_updated', 'Password updated — sign in'), 'success');
          navigate('/login');
        } catch (err) {
          toast(err.message, 'error');
          btn.disabled = false; btn.textContent = t('auth.update_password', 'Update Password');
        }
      });
    }
  });
})();
