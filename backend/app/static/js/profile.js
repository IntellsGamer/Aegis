/* Profile page */
(function () {
  'use strict';
  const { api, toast } = window.Aegis;

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('profile-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('button[type=submit]');
      btn.disabled = true;
      try {
        await api('PUT', '/api/v1/users/me', {
          username: document.getElementById('p-username').value.trim(),
          email: document.getElementById('p-email').value.trim(),
          email_notifications: document.getElementById('p-prefs').checked,
        });
        toast('Profile updated', 'success');
      } catch (err) {
        toast(err.message, 'error');
      } finally {
        btn.disabled = false;
      }
    });

    document.getElementById('password-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('button[type=submit]');
      const np = document.getElementById('p-new').value;
      if (np !== document.getElementById('p-confirm').value) { toast('New passwords do not match', 'error'); return; }
      btn.disabled = true;
      try {
        await api('PUT', '/api/v1/users/me/password', {
          current_password: document.getElementById('p-current').value,
          new_password: np,
        });
        toast('Password updated', 'success');
        e.target.reset();
      } catch (err) {
        toast(err.message, 'error');
      } finally {
        btn.disabled = false;
      }
    });

    document.getElementById('delete-account-btn')?.addEventListener('click', async () => {
      if (!confirm('Delete your account permanently? This cannot be undone.')) return;
      try {
        await api('DELETE', '/api/v1/users/me');
        toast('Account deleted', 'success');
        window.Aegis.navigate('/');
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });
})();
