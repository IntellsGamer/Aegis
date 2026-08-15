/* Profile and preference controls aligned with the current account API. */
(function () {
  'use strict';
  const { api, toast, t } = window.Aegis;
  const byId = (id) => document.getElementById(id);

  function disable(form, value) {
    const button = form.querySelector('button[type=submit]');
    if (button) button.disabled = value;
    return button;
  }

  async function loadPreferences() {
    try {
      const [profile, settings] = await Promise.all([api('GET', '/api/v1/users/me'), api('GET', '/api/v1/users/me/settings')]);
      byId('p-full-name').value = profile.full_name || '';
      byId('p-locale').value = profile.locale || 'en';
      byId('p-theme').value = profile.theme || window.Aegis.getTheme();
      byId('p-high-contrast').checked = Boolean(profile.high_contrast);
      byId('p-save-history').checked = Boolean(settings?.save_history);
      byId('p-notify-email').checked = Boolean(settings?.notify_email);
      byId('p-notify-push').checked = Boolean(settings?.notify_push);
      byId('p-notify-threats').checked = Boolean(settings?.notify_threats);
    } catch (error) { toast(`${t('profile.load_failed', 'Could not load preferences')}: ${error.message}`, 'error'); }
  }

  window.Aegis.onPageLoad('profile', () => {
    loadPreferences();
    byId('profile-form')?.addEventListener('submit', async (event) => {
      event.preventDefault(); const button = disable(event.currentTarget, true);
      try {
        await api('PATCH', '/api/v1/users/me', { full_name: byId('p-full-name').value.trim() || null });
        toast(t('profile.saved', 'Profile saved'), 'success');
      } catch (error) { toast(error.message, 'error'); }
      finally { if (button) button.disabled = false; }
    });

    byId('settings-form')?.addEventListener('submit', async (event) => {
      event.preventDefault(); const button = disable(event.currentTarget, true);
      const profile = { locale: byId('p-locale').value, theme: byId('p-theme').value, high_contrast: byId('p-high-contrast').checked };
      const settings = { save_history: byId('p-save-history').checked, notify_email: byId('p-notify-email').checked, notify_push: byId('p-notify-push').checked, notify_threats: byId('p-notify-threats').checked, language: profile.locale };
      try {
        await Promise.all([api('PATCH', '/api/v1/users/me', profile), api('PATCH', '/api/v1/users/me/settings', settings)]);
        window.Aegis.setTheme(profile.theme);
        document.documentElement.classList.toggle('high-contrast', profile.high_contrast);
        toast(t('profile.preferences_saved', 'Preferences saved. Reload to apply a changed language direction.'), 'success');
      } catch (error) { toast(error.message, 'error'); }
      finally { if (button) button.disabled = false; }
    });

    byId('password-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const next = byId('p-new').value;
      if (next !== byId('p-confirm').value) { toast(t('profile.password_mismatch', 'New passwords do not match'), 'error'); return; }
      const button = disable(event.currentTarget, true);
      try {
        await api('POST', '/api/v1/auth/change-password', { current_password: byId('p-current').value, new_password: next });
        toast(t('profile.password_updated', 'Password updated'), 'success'); event.currentTarget.reset();
      } catch (error) { toast(error.message, 'error'); }
      finally { if (button) button.disabled = false; }
    });

    byId('delete-account-btn')?.addEventListener('click', async () => {
      if (!confirm(t('profile.delete_confirm', 'Delete your account and all stored scan data permanently? This cannot be undone.'))) return;
      try { await api('DELETE', '/api/v1/users/me'); toast('Account deleted', 'success'); window.Aegis.navigate('/'); }
      catch (error) { toast(error.message, 'error'); }
    });
  });
})();
