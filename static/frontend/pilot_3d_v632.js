/* v6.0.32 — Pilot 3D section.
 * Re-enables the Digital Vehicle / Heavy Truck WebGL models as a standalone
 * "3D-модели" view. The heavy 3D files are loaded lazily on first open, so the
 * cold-start shell stays lightweight. No API, XP, scoring or answer ownership.
 */
(function (root) {
  'use strict';

  const frontend = root.MGCFrontend;
  if (!frontend) throw new Error('MGCFrontend runtime is missing');
  if (frontend.has('pilot-3d')) return;

  const VIEW = '3d';
  const CSS = '/digital_vehicle_3d_v630.css';
  const SCRIPTS = ['/frontend/digital_vehicle_3d_v630.js', '/frontend/digital_truck_3d_v630.js'];
  const MODELS = {
    car: {module: 'digital-vehicle-3d-v630', title: 'Легковой автомобиль', note: '8 учебных зон кузова'},
    truck: {module: 'digital-truck-3d-v630', title: 'Грузовик (тягач)', note: '8 учебных зон тяжёлого тягача'}
  };

  let installed = false;
  let assets = null;
  let instance = null;
  let kind = 'car';

  function legacy() { return frontend.get('legacy-app'); }
  function state() { return frontend.get('app-state'); }
  function esc(value) { return legacy().escapeHtml(value); }
  function query(selector) { return legacy().query(selector); }
  function queryAll(selector) { return legacy().queryAll(selector); }
  function owns(view) { return String(view || '') === VIEW; }

  function reportError(scope, error) {
    if (!frontend.has('error-boundary')) return;
    frontend.get('error-boundary').record(
      String(scope || 'pilot-3d'), error && error.message ? error.message : error, '', 0, 0
    );
  }

  function loadStyle(href) {
    return new Promise(function (resolve) {
      if (document.querySelector('link[href="' + href + '"]')) return resolve();
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.onload = link.onerror = function () { resolve(); };
      document.head.appendChild(link);
    });
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (document.querySelector('script[src="' + src + '"]')) return resolve();
      const script = document.createElement('script');
      script.src = src;
      script.onload = function () { resolve(); };
      script.onerror = function () { reject(new Error('Не удалось загрузить ' + src)); };
      document.head.appendChild(script);
    });
  }

  function ensureAssets() {
    if (!assets) {
      assets = loadStyle(CSS)
        .then(function () { return Promise.all(SCRIPTS.map(loadScript)); })
        .catch(function (error) { assets = null; throw error; });
    }
    return assets;
  }

  function dispose() {
    const old = instance;
    instance = null;
    if (!old) return;
    try {
      if (typeof old.destroy === 'function') old.destroy();
      else {
        if (old.ro) old.ro.disconnect();
        old.gl = null;
      }
    } catch (_) {}
  }

  function zoneInfo(host, zone) {
    const english = state().current().language !== 'chinese';
    Array.prototype.forEach.call(host.querySelectorAll('.dv3d-zone-info'), function (node) { node.remove(); });
    host.insertAdjacentHTML('beforeend',
      '<div class="dv3d-zone-info"><div class="dv3d-learning"><span>УЧЕБНЫЙ ОБЪЕКТ</span><b>' +
      esc(english ? zone.en : zone.zh) + '</b>' + (english ? '' : '<em>' + esc(zone.py) + '</em>') +
      '<small>' + esc(zone.ru) + (english ? '' : ' · ' + esc(zone.en)) + '</small></div></div>');
  }

  function showFallback(host, message) {
    host.innerHTML = '<div class="p3d-fallback"><b>3D недоступно в этом браузере</b><p>' + esc(message) +
      '</p><p>Включите аппаратное ускорение в настройках браузера (Chrome: Настройки → Система → ' +
      '«Использовать аппаратное ускорение»), перезапустите его и обновите страницу.</p></div>';
  }

  async function mount() {
    const host = query('#p3dHost');
    if (!host) return;
    dispose();
    host.innerHTML = '';
    host.classList.add('dv3d-host');
    try {
      await ensureAssets();
      if (query('#p3dHost') !== host) return;
      const model = frontend.get(MODELS[kind].module);
      if (kind === 'car') {
        instance = model.create(host, {interactive: true, onZone: function (id) { zoneInfo(host, model.zones[id]); }});
      } else {
        instance = model.create(host);
      }
      const badge = document.createElement('div');
      badge.className = 'dv3d-badge';
      badge.innerHTML = '<span>M</span><b>' + esc(MODELS[kind].title.toUpperCase()) + '</b><small>' +
        esc(MODELS[kind].note) + '</small>';
      host.appendChild(badge);
    } catch (error) {
      reportError('pilot-3d-mount', error);
      showFallback(host, error && error.message ? error.message : 'WebGL недоступен');
    }
  }

  function render() {
    const main = query('#main');
    if (!main) return;
    dispose();
    main.innerHTML =
      '<div class="page-head"><div><div class="kicker">MGC · DIGITAL VEHICLE</div><h1>3D-модели</h1>' +
      '<p>Вращайте модель мышью или пальцем и нажимайте на метки: название детали на китайском, пиньинь и перевод.</p></div></div>' +
      '<div class="p3d-tabs" role="tablist">' + Object.keys(MODELS).map(function (key) {
        return '<button type="button" role="tab" class="p3d-tab' + (key === kind ? ' active' : '') +
          '" data-p3d-kind="' + key + '" aria-selected="' + (key === kind) + '">' + esc(MODELS[key].title) + '</button>';
      }).join('') + '</div><div id="p3dHost" class="p3d-host"></div>';
    return mount();
  }

  async function navigate(view) {
    if (!owns(view)) return legacy().setView(view);
    state().set('view', VIEW);
    legacy().closeMenu();
    queryAll('[data-view]').forEach(function (button) {
      button.classList.toggle('active', button.dataset.view === VIEW);
    });
    try {
      await render();
    } catch (error) {
      reportError('pilot-3d-navigation', error);
      throw error;
    }
  }

  function install() {
    if (installed) return;
    installed = true;
    document.addEventListener('click', function (event) {
      const target = event.target && event.target.closest ? event.target : null;
      if (!target) return;
      const tab = target.closest('[data-p3d-kind]');
      if (tab && MODELS[tab.dataset.p3dKind] && tab.dataset.p3dKind !== kind) {
        kind = tab.dataset.p3dKind;
        queryAll('[data-p3d-kind]').forEach(function (node) {
          const active = node.dataset.p3dKind === kind;
          node.classList.toggle('active', active);
          node.setAttribute('aria-selected', String(active));
        });
        mount();
        return;
      }
      const nav = target.closest('[data-view]');
      if (!nav || !owns(nav.dataset.view)) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      navigate(VIEW).catch(function (error) { reportError('pilot-3d-click', error); });
    }, true);
  }

  frontend.register('pilot-3d', {views: [VIEW], owns: owns, render: render, navigate: navigate, install: install});

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, {once: true});
  else install();
})(typeof window !== 'undefined' ? window : globalThis);
