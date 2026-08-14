/* Threat map */
(function () {
  'use strict';
  const { api, esc } = window.Aegis;
  let map = null;

  async function load(rangeDays) {
    const data = await api('GET', `/api/v1/threats/map?range=${rangeDays}`);
    const points = data.points || [];
    document.getElementById('map-total').textContent = data.total_reports ?? points.length;
    const countries = new Set(points.map((p) => p.country).filter(Boolean));
    document.getElementById('map-countries').textContent = countries.size;
    const counts = {};
    points.forEach((p) => { counts[p.type || 'unknown'] = (counts[p.type || 'unknown'] || 0) + 1; });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    document.getElementById('map-vector').textContent = top ? `${top[0]} (${top[1]})` : '—';

    if (!map) {
      map = L.map('map').setView([20, 0], 2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);
    }

    points.forEach((p) => {
      if (p.lat === undefined || p.lng === undefined) return;
      const risk = String(p.risk || 'unknown');
      const color = risk === 'critical' || risk === 'high' || risk === 'threat' ? '#ef4444'
        : risk === 'medium' || risk === 'suspicious' ? '#f59e0b' : '#10b981';
      L.circleMarker([p.lat, p.lng], {
        radius: 7, color, fillColor: color, fillOpacity: 0.7, weight: 1,
      }).addTo(map)
        .bindPopup(`<b>${esc(p.type || 'Threat')}</b><br>risk: ${esc(p.risk || 'unknown')} · ${esc(p.country || 'Unknown')}`);
    });
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const radios = document.querySelectorAll('input[name=range]');
    radios.forEach((r) => r.addEventListener('change', () => load(parseInt(r.value, 10))));
    try {
      await load(24);
    } catch (err) {
      document.getElementById('map-total').textContent = '—';
      window.Aegis.toast('Failed to load map data', 'error');
    }
  });
})();
