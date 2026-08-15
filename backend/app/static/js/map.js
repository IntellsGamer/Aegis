/* Verified public threat-map client. */
(function () {
  'use strict';
  const shared = window.Aegis;
  if (!shared) {
    window.addEventListener('aegis:ready', () => window.location.reload(), { once: true });
    return;
  }
  const { api, esc, t } = shared;
  let map = null;
  let markers = null;

  function riskColor(risk) {
    const value = String(risk || 'unknown').toLowerCase();
    if (['critical', 'high', 'threat', 'phishing', 'credential_harvesting'].includes(value)) return '#ef4444';
    if (['medium', 'suspicious', 'crypto', 'advance_fee', 'quishing'].includes(value)) return '#f59e0b';
    return '#10b981';
  }

  function initializeMap() {
    if (map) return;
    map = L.map('map', {
      worldCopyJump: true,
      minZoom: 2,
      dragging: true,
      touchZoom: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      boxZoom: true,
      keyboard: true,
      tap: true,
    }).setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    markers = L.layerGroup().addTo(map);
  }

  function updateStats(points, total) {
    document.getElementById('map-total').textContent = total;
    document.getElementById('map-countries').textContent = new Set(points.map((p) => p.country_code || p.country).filter(Boolean)).size;
    const vectors = {};
    points.forEach((point) => {
      const key = point.type || 'unknown';
      vectors[key] = (vectors[key] || 0) + Number(point.count || 1);
    });
    const top = Object.entries(vectors).sort((a, b) => b[1] - a[1])[0];
    document.getElementById('map-vector').textContent = top ? `${top[0]} (${top[1]})` : '—';
  }

  function setEmpty(data, empty) {
    const panel = document.getElementById('map-empty');
    panel.classList.toggle('hidden', !empty);
    panel.classList.toggle('flex', empty);
    if (empty) document.getElementById('map-empty-copy').textContent = t('map.no_reports', 'No approved reports are available for this period.');
  }

  function renderPoints(points, developmentDemo = false) {
    markers.clearLayers();
    const bounds = [];
    points.forEach((point) => {
      if (!Number.isFinite(Number(point.lat)) || !Number.isFinite(Number(point.lng))) return;
      const count = Math.max(1, Number(point.count || 1));
      const color = riskColor(point.category);
      const marker = L.circleMarker([Number(point.lat), Number(point.lng)], {
        radius: Math.min(26, 7 + Math.sqrt(count) * 4), color, fillColor: color,
        fillOpacity: 0.72, weight: 2,
      });
      marker.bindPopup(
        `<strong>${esc(point.country || t('map.unknown_country', 'Unknown country'))}</strong><br>` +
        `${esc(point.type || t('verdict.threat', 'threat'))} · ${esc(point.category || t('map.unknown', 'unknown'))}<br>` +
        `${count} ${t('map.approved_reports', 'approved reports')}<br>` +
        `<span class="text-xs">${developmentDemo ? t('map.development_demo_marker', 'local development demo') : esc(point.provenance || t('map.approved_report', 'approved report'))} · ${esc(point.location_precision || t('map.country_aggregate', 'country aggregate'))}</span>`
      );
      marker.addTo(markers);
      bounds.push([Number(point.lat), Number(point.lng)]);
    });
    if (bounds.length > 1) map.fitBounds(bounds, { padding: [36, 36], maxZoom: 4 });
    else if (bounds.length === 1) map.setView(bounds[0], 3);
    else map.setView([20, 0], 2);
  }

  async function load(rangeDays) {
    const data = await api('GET', `/api/v1/threats/map?range=${rangeDays}`);
    const points = data.points || [];
    initializeMap();
    updateStats(points, Number(data.total_reports || 0));
    const developmentDemo = data.data_state === 'development_demo_reports';
    renderPoints(points, developmentDemo);
    setEmpty(data, points.length === 0);
    document.getElementById('map-provenance').lastChild.textContent = developmentDemo
      ? `${t('map.development_demo', 'Local development demo data')} · ${t('map.country_aggregate', 'country aggregate')}`
      : `${t('map.approved_community', 'Approved community reports')} · ${t('map.country_aggregate', 'country aggregate')}`;
    document.getElementById('map-updated').textContent = `${data.total_reports || 0} ${t('map.approved_reports', 'approved reports')} ${t('map.in_last', 'in the last')} ${data.range_days || rangeDays} ${t('map.days', 'days')}`;
  }

  window.Aegis.onPageLoad('map', async () => {
    const radios = document.querySelectorAll('input[name=range]');
    radios.forEach((radio) => radio.addEventListener('change', () => load(parseInt(radio.value, 10)).catch(showError)));
    function showError() {
      document.getElementById('map-total').textContent = '—';
      document.getElementById('map-updated').textContent = t('map.load_failed', 'Map data could not be loaded.');
      window.Aegis.toast(t('map.load_failed', 'Failed to load verified map data'), 'error');
    }
    try {
      await load(1);
    } catch (error) {
      showError(error);
    }
  });
})();
