/* Segment Reviewer — browser client.
 *
 * The server owns the pending list and the files; this file only draws it and
 * sends verdicts back. Spectrogram controls redraw the image alone — the audio
 * element is never touched by them, so a clip keeps playing while the view
 * changes.
 */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const el = {
    counts: $('counts'), lang: $('lang-select'),
    folderBar: $('folder-form'), folderInput: $('folder-input'),
    recentFolders: $('recent-folders'), btnBrowse: $('btn-browse'), notice: $('notice'),
    browse: $('browse-dialog'), browseUp: $('browse-up'), browseHere: $('browse-here'),
    browseList: $('browse-list'), browseError: $('browse-error'), browseWavs: $('browse-wavs'),
    browseCancel: $('browse-cancel'), browseOpen: $('browse-open'),
    progress: $('progress'), meta: $('meta'), controls: $('controls'),
    specWrap: $('spec-wrap'), spec: $('spec'), player: $('player'),
    error: $('error'), ann: $('ann'),
    labelsPanel: $('labels-panel'), labelsTitle: $('labels-title'),
    labelButtons: $('label-buttons'), labelInput: $('label-input'),
    btnAddLabel: $('btn-add-label'), btnManage: $('btn-manage'),
    labelsNote: $('labels-note'),
    navRow: $('nav-row'), btnPrev: $('btn-prev'), btnTrue: $('btn-true'),
    btnFalse: $('btn-false'), btnUnsure: $('btn-unsure'), btnNext: $('btn-next'),

    specType: $('spec-type'), specFmin: $('spec-fmin'), specFmax: $('spec-fmax'),
    specDb: $('spec-db'),
    btnRescan: $('btn-rescan'), btnHelp: $('btn-help'), help: $('help-dialog'),
  };

  const app = {
    bundle: {}, lang: 'en', multi: true, boot: null,
    state: { segment: null, counts: {}, labels: [], label_store: {}, annotations: {} },
    busy: false, specToken: 0,
    //: labels chosen for the segment on screen
    selection: [],
    //: true while the label list itself is being edited
    managing: false,
  };

  // ── i18n ──────────────────────────────────────────────────────────────────
  const t = (key, vars) => {
    let out = key.split('.').reduce((n, k) => (n && n[k] !== undefined ? n[k] : null), app.bundle);
    if (out === null || typeof out !== 'string') return key;
    if (vars) for (const [k, v] of Object.entries(vars)) out = out.split(`{${k}}`).join(v);
    return out;
  };

  function applyI18n() {
    document.documentElement.lang = app.lang;
    document.title = t('app.title');
    for (const node of document.querySelectorAll('[data-i18n]')) node.innerHTML = t(node.dataset.i18n);
    for (const node of document.querySelectorAll('[data-i18n-title]')) node.title = t(node.dataset.i18nTitle);
    for (const node of document.querySelectorAll('[data-i18n-ph]')) node.placeholder = t(node.dataset.i18nPh);
  }

  // ── HTTP ──────────────────────────────────────────────────────────────────
  async function api(path, options) {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      ...options,
    });
    if (res.status === 401) throw new Error(t('errors.unauthorized'));
    if (!res.ok) {
      let detail = res.statusText;
      try { detail = (await res.json()).detail || detail; } catch (_) { /* keep statusText */ }
      throw new Error(detail);
    }
    return res.json();
  }

  const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body || {}) });

  // ── label helpers ─────────────────────────────────────────────────────────
  const {
    splitLabels, spectrogramUrl, audioUrl, toggleLabel, buttonLabels, reviewLabels,
    rememberFolder,
  } = window.SegRev;

  // ── the label panel ───────────────────────────────────────────────────────
  /** The segment's own label: the model's prediction, or '' when it has none. */
  const predicted = () => (app.state.segment && app.state.segment.label) || '';

  /** Chips on screen, in a stable order so 1…9 always hit the same label. */
  const chipLabels = () => {
    const p = predicted();
    return buttonLabels(app.state.labels, (p ? [p] : []).concat(app.selection));
  };

  function renderLabels() {
    const labels = chipLabels();
    const p = predicted();
    el.labelsTitle.textContent = t(p ? 'labels.others' : 'labels.selected');
    el.labelsPanel.classList.toggle('managing', app.managing);
    el.btnManage.classList.toggle('active', app.managing);
    el.btnManage.title = t(app.managing ? 'labels.manage_on' : 'labels.manage');

    el.labelButtons.innerHTML = '';
    labels.forEach((label, i) => {
      const isPrediction = label === p;
      const chip = document.createElement('span');
      chip.className = 'chip'
        + (app.selection.includes(label) ? ' on' : '')
        + (isPrediction ? ' predicted' : '');

      const pick = document.createElement('button');
      pick.type = 'button';
      pick.className = 'chip-pick';
      // The first nine get a number, matching the 1…9 keyboard shortcuts.
      pick.innerHTML = (i < 9 ? `<kbd>${i + 1}</kbd>` : '') + escapeHtml(label)
        + (isPrediction ? ` <span class="chip-tag">${t('labels.predicted_tag')}</span>` : '');
      // The prediction is answered by Correct / Wrong, never by its chip: a
      // chip that could be lit while Wrong is pressed is the contradiction
      // this layout exists to rule out.
      pick.disabled = isPrediction;
      if (isPrediction) pick.title = t('labels.predicted_hint');
      pick.addEventListener('click', () => pickLabel(label));
      chip.appendChild(pick);

      const drop = document.createElement('button');
      drop.type = 'button';
      drop.className = 'chip-drop';
      drop.textContent = '×';
      drop.title = t('labels.remove', { label });
      drop.addEventListener('click', () => editList({ remove: label }));
      chip.appendChild(drop);

      el.labelButtons.appendChild(chip);
    });
    if (!labels.length) {
      el.labelButtons.innerHTML = `<span class="hint">${t('labels.empty')}</span>`;
    }
    renderLabelsNote();
    renderButtons();
  }

  /** Name, on each button, exactly what pressing it will save. */
  function renderButtons() {
    const p = predicted();
    const list = (xs) => xs.map(escapeHtml).join(', ');
    el.btnFalse.classList.toggle('hidden', !p);
    if (!p) {
      // Nothing was predicted, so there is nothing to be right or wrong about:
      // one button saves what is selected.
      const chosen = reviewLabels('correct', app.selection, p, !app.multi);
      el.btnTrue.innerHTML = chosen.length
        ? t('nav.save_labels', { labels: list(chosen) }) : t('nav.save_none');
      return;
    }
    const extra = reviewLabels('correct', app.selection, p, !app.multi).filter((x) => x !== p);
    el.btnTrue.innerHTML = extra.length
      ? t('nav.true_plus', { labels: list(extra) }) : t('nav.true');
    const really = reviewLabels('wrong', app.selection, p, !app.multi);
    el.btnFalse.innerHTML = really.length
      ? t('nav.false_to', { labels: list(really) }) : t('nav.false_none');
  }

  function renderLabelsNote() {
    const store = app.state.label_store || {};
    if (store.error) {
      el.labelsNote.innerHTML =
        `<span class="bad">${t('labels.not_saved', { error: escapeHtml(store.error) })}</span>`;
    } else if (!app.managing) {
      el.labelsNote.textContent = '';
    } else if (store.persisted) {
      el.labelsNote.textContent = t('labels.saved_to', { path: store.path });
    } else {
      el.labelsNote.textContent = t('labels.session_only');
    }
  }

  function pickLabel(label) {
    if (label === predicted()) return;   // answered by Correct / Wrong instead
    // One label at a time unless multi-label is on.
    app.selection = toggleLabel(app.selection, label, !app.multi);
    renderLabels();
  }

  async function editList(change) {
    try {
      const data = await post('/api/labels', change);
      app.state = data.state;
      renderLabels();
    } catch (err) {
      el.error.textContent = err.message || t('errors.network');
    }
  }

  function addTypedLabel() {
    const typed = splitLabels(el.labelInput.value);
    if (!typed.length) return;
    el.labelInput.value = '';
    // Typing a label both puts it on the list and picks it for this segment,
    // so a new class costs one action rather than two.
    for (const label of typed) {
      if (!app.selection.includes(label)) app.selection.push(label);
    }
    editList({ labels: buttonLabels(app.state.labels, typed) });
  }

  // ── rendering ─────────────────────────────────────────────────────────────
  const specView = () => ({
    type: el.specType.value,
    fmin: el.specFmin.value,
    fmax: el.specFmax.value,
    db: el.specDb.value,
  });

  function loadSpectrogram() {
    const seg = app.state.segment;
    if (!seg) return;
    const token = ++app.specToken;
    const url = spectrogramUrl(seg, specView());
    el.specWrap.classList.add('loading');
    const img = new Image();
    img.onload = () => {
      if (token !== app.specToken) return;   // a newer request already won
      el.spec.src = img.src;
      el.specWrap.classList.remove('loading');
    };
    img.onerror = async () => {
      if (token !== app.specToken) return;
      el.specWrap.classList.remove('loading');
      el.spec.removeAttribute('src');
      // The PNG endpoint answers errors as JSON; ask again to show the reason.
      try {
        await api(url);
      } catch (err) {
        el.error.textContent = t('spec.error', { error: err.message });
      }
    };
    img.src = url;
  }

  function loadAudio() {
    const seg = app.state.segment;
    if (!seg) { el.player.removeAttribute('src'); el.player.load(); return; }
    el.player.src = audioUrl(seg);
    el.player.load();
  }

  function renderMeta(seg) {
    // Only what this segment actually carries: a collection named by another
    // convention simply shows fewer facts rather than a row of question marks.
    const bits = [seg.label
      ? `${t('meta_row.predicted')}: <b>${escapeHtml(seg.label)}</b>`
      : `<i>${t('meta_row.no_label')}</i>`];
    const add = (key, value) => {
      if (value !== null && value !== undefined && value !== '') {
        bits.push(`${t(`meta_row.${key}`)}: <b>${escapeHtml(value)}</b>`);
      }
    };
    if (seg.score !== null) add('score', seg.score.toFixed(3));
    add('site', seg.site);
    add('date', seg.recorded_at);
    add('folder', seg.folder);
    add('extra', seg.extra);
    el.meta.innerHTML = bits.join(' &nbsp;|&nbsp; ');
  }

  function renderCounts() {
    const c = app.state.counts || {};
    if (!app.state.folder) { el.counts.textContent = ''; return; }
    el.counts.textContent = t('progress.counts', {
      pending: c.pending ?? 0, correct: c.correct ?? 0, wrong: c.wrong ?? 0,
      unsure: c.unsure ?? 0,
    }) + (c.labelled ? t('progress.labelled', { labelled: c.labelled }) : '');
  }

  function renderAnnotations(final) {
    const a = app.state.annotations || {};
    if (a.no_path) {
      el.ann.innerHTML = `<span class="bad">${t('annotations.label')}: ${t('annotations.no_path')}</span>`;
      return;
    }
    if (a.error) {
      el.ann.innerHTML = `<span class="bad">${t('annotations.label')}: ${escapeHtml(a.error)}</span>`;
      return;
    }
    if (!a.enabled) {
      el.ann.textContent = '';
      return;
    }
    let warn = '';
    if (a.read_error) {
      warn = ` — <span class="warn">${t('annotations.read_error', { error: escapeHtml(a.read_error) })}</span>`;
    } else if (a.rows_without_recording) {
      const why = a.have_sources ? t('annotations.why_unlisted') : t('annotations.why_missing');
      warn = ` — <span class="warn">${t('annotations.norec', { count: a.rows_without_recording, why })}</span>`;
    }
    el.ann.innerHTML = `${final ? '✔ ' : ''}${t('annotations.label')}: ${t('annotations.rows', {
      count: `<b>${a.rows}</b>`, path: escapeHtml(a.path),
    })}${warn}`;
  }

  const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));

  function hideViewer() {
    el.meta.textContent = '';
    el.controls.classList.add('hidden');
    el.specWrap.classList.add('hidden');
    el.player.classList.add('hidden');
    el.player.pause();
    el.navRow.classList.add('hidden');
    el.labelsPanel.classList.add('hidden');
  }

  function render({ reloadMedia = true, keepSelection = false } = {}) {
    const seg = app.state.segment;
    renderCounts();
    renderFolder();

    if (!app.state.folder) {
      // Nothing open yet: the folder box is the whole page.
      el.progress.className = 'progress done';
      el.progress.innerHTML = t('progress.no_folder');
      hideViewer();
      el.ann.textContent = '';
      return;
    }

    if (!seg) {
      // Hide the viewer rather than leaving an empty frame in place.
      const c = app.state.counts || {};
      const done = (c.correct || c.wrong || c.unsure || c.labelled);
      el.progress.className = 'progress done';
      el.progress.innerHTML = done ? t('progress.done') : t('progress.empty');
      el.error.textContent = '';
      hideViewer();
      renderAnnotations(true);
      return;
    }

    el.progress.className = 'progress';
    el.progress.innerHTML = t('progress.segment', { index: seg.index + 1, total: seg.total });
    el.controls.classList.remove('hidden');
    el.specWrap.classList.remove('hidden');
    el.player.classList.remove('hidden');
    el.error.textContent = '';
    renderMeta(seg);
    renderAnnotations(false);

    if (!keepSelection) {
      // Every segment starts with nothing selected. The prediction is the
      // question Correct / Wrong answer, not a chip that is already lit — so a
      // reviewer who presses Wrong without touching anything saves "nothing on
      // the list", never a label carried over from what was on screen before.
      app.selection = [];
    }
    el.labelsPanel.classList.remove('hidden');
    el.navRow.classList.remove('hidden');
    renderLabels();

    el.btnPrev.disabled = seg.index <= 0;
    el.btnNext.disabled = seg.index >= seg.total - 1;

    loadSpectrogram();
    if (reloadMedia) loadAudio();
  }

  // ── actions ───────────────────────────────────────────────────────────────
  async function run(fn) {
    if (app.busy) return;
    app.busy = true;
    try {
      app.state = await fn();
      render();
    } catch (err) {
      el.error.textContent = err.message || t('errors.network');
    } finally {
      app.busy = false;
    }
  }

  const nav = (delta) => run(() => post('/api/nav', { delta }));

  /** File the segment on screen, as the button *kind* reads the selection. */
  async function review(kind) {
    const seg = app.state.segment;
    if (!seg || app.busy) return;
    const labels = reviewLabels(kind, app.selection, seg.label, !app.multi);
    app.busy = true;
    try {
      app.state = await post('/api/review', {
        relpath: seg.relpath, labels, unsure: kind === 'unsure',
      });
      render();
    } catch (err) {
      el.error.textContent = err.message || t('errors.network');
      // The clip on screen may no longer be the server's current one (another
      // tab, a rescan): show what the server has now, keeping the message.
      try {
        const message = el.error.textContent;
        app.state = await api('/api/state');
        render();
        el.error.textContent = message;
      } catch (_) { /* keep the first error */ }
    } finally {
      app.busy = false;
    }
  }

  // ── the folder under review ───────────────────────────────────────────────
  const recentFolders = () => {
    try { return JSON.parse(localStorage.getItem('segrev.recent')) || []; } catch (_) { return []; }
  };

  function renderFolder() {
    const folder = app.state.folder || '';
    // Never overwrite what the reviewer is typing.
    if (document.activeElement !== el.folderInput) el.folderInput.value = folder;
    el.folderInput.title = folder || t('folder.hint');
    el.folderBar.classList.toggle('empty', !folder);
    el.recentFolders.innerHTML = '';
    for (const path of recentFolders()) el.recentFolders.appendChild(new Option(path));
  }

  /** A line saying the filename pattern read few of the names just opened. */
  function renderPattern(pattern) {
    el.notice.textContent = '';
    if (!pattern || !pattern.total || pattern.matched === pattern.total) return;
    const key = pattern.matched === 0 ? 'cli.pattern_none' : 'cli.pattern_some';
    el.notice.textContent = t(key, { matched: pattern.matched, total: pattern.total })
      + (pattern.example ? ` ${pattern.example}` : '');
  }

  async function openFolder(path) {
    const wanted = String(path || '').trim();
    if (!wanted || app.busy) return;
    app.busy = true;
    el.folderBar.classList.add('busy');
    try {
      const data = await post('/api/open', { path: wanted });
      app.state = data;
      try {
        localStorage.setItem('segrev.recent',
          JSON.stringify(rememberFolder(recentFolders(), data.folder, 8)));
      } catch (_) { /* a private window: no history, nothing else lost */ }
      el.folderInput.blur();
      render();
      renderPattern(data.pattern);
    } catch (err) {
      // The folder under review, if any, is still open and still on screen.
      el.error.textContent = err.message || t('errors.network');
    } finally {
      app.busy = false;
      el.folderBar.classList.remove('busy');
    }
  }

  // ── the folder picker ─────────────────────────────────────────────────────
  async function browseTo(path) {
    el.browseError.textContent = '';
    try {
      const data = await api(`/api/browse?path=${encodeURIComponent(path || '')}`);
      app.browsing = data;
      el.browseHere.textContent = data.path;
      el.browseUp.disabled = !data.parent;
      el.browseWavs.textContent = data.wavs ? t('browse.wavs_here', { count: data.wavs }) : '';
      el.browseList.innerHTML = '';
      for (const folder of data.folders) {
        const li = document.createElement('li');
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = folder.name;
        if (folder.has_wavs) button.className = 'has-wavs';
        button.addEventListener('click', () => browseTo(folder.path));
        li.appendChild(button);
        el.browseList.appendChild(li);
      }
      if (!data.folders.length) {
        el.browseList.innerHTML = `<li class="empty">${t('browse.empty')}</li>`;
      }
    } catch (err) {
      el.browseError.textContent = err.message || t('errors.network');
    }
  }

  function openBrowser() {
    el.browse.showModal();
    browseTo(el.folderInput.value.trim() || app.state.folder || '');
  }

  const markCorrect = () => review('correct');
  const markWrong = () => review('wrong');
  const markUnsure = () => review('unsure');

  async function setLanguage(code, { persist = true } = {}) {
    const data = await api(`/api/i18n/${encodeURIComponent(code)}`);
    app.lang = data.lang;
    app.bundle = data.bundle;
    if (persist) localStorage.setItem('segrev.lang', app.lang);
    el.lang.value = app.lang;
    applyI18n();
    render({ reloadMedia: false, keepSelection: true });
  }

  // ── wiring ────────────────────────────────────────────────────────────────
  el.btnPrev.addEventListener('click', () => nav(-1));
  el.btnNext.addEventListener('click', () => nav(+1));
  el.btnTrue.addEventListener('click', markCorrect);
  el.btnFalse.addEventListener('click', markWrong);
  el.btnUnsure.addEventListener('click', markUnsure);
  el.btnRescan.addEventListener('click', () => {
    if (app.state.folder) run(() => post('/api/rescan'));
  });
  el.folderBar.addEventListener('submit', (e) => {
    e.preventDefault();
    openFolder(el.folderInput.value);
  });
  el.folderInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { el.folderInput.value = app.state.folder || ''; el.folderInput.blur(); }
  });
  el.btnBrowse.addEventListener('click', openBrowser);
  el.browseUp.addEventListener('click', () => app.browsing && browseTo(app.browsing.parent));
  el.browseCancel.addEventListener('click', () => el.browse.close());
  el.browseOpen.addEventListener('click', () => {
    const path = app.browsing && app.browsing.path;
    el.browse.close();
    if (path) { el.folderInput.value = path; openFolder(path); }
  });
  el.btnHelp.addEventListener('click', () => el.help.showModal());

  el.btnManage.addEventListener('click', () => {
    app.managing = !app.managing;
    renderLabels();
  });
  el.btnAddLabel.addEventListener('click', addTypedLabel);
  el.labelInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addTypedLabel(); }
    if (e.key === 'Escape') { e.preventDefault(); el.labelInput.value = ''; el.labelInput.blur(); }
  });

  for (const control of [el.specType, el.specFmin, el.specFmax, el.specDb]) {
    control.addEventListener('change', () => {
      localStorage.setItem('segrev.spec', JSON.stringify({
        type: el.specType.value, fmin: el.specFmin.value,
        fmax: el.specFmax.value, db: el.specDb.value,
      }));
      loadSpectrogram();     // the audio player is deliberately left alone
    });
  }

  el.lang.addEventListener('change', () => setLanguage(el.lang.value));

  document.addEventListener('keydown', (e) => {
    if (e.target.matches('input, select, textarea') || el.help.open || el.browse.open) return;
    if (!app.state.segment) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    if (e.key === ' ') {
      e.preventDefault();
      el.player.paused ? el.player.play().catch(() => {}) : el.player.pause();
      return;
    }
    // 1…9 toggle the first nine labels, which is the whole point of the buttons.
    if (/^[1-9]$/.test(e.key)) {
      const label = chipLabels()[Number(e.key) - 1];
      if (label) { e.preventDefault(); pickLabel(label); }
      return;
    }
    const keys = {
      ArrowLeft: () => nav(-1),
      ArrowRight: () => nav(+1),
      t: markCorrect, T: markCorrect,
      f: markWrong, F: markWrong,
      u: markUnsure, U: markUnsure,
    };
    const action = keys[e.key];
    if (action) { e.preventDefault(); action(); }
  });

  // ── start ─────────────────────────────────────────────────────────────────
  (async function start() {
    try {
      const boot = await api('/api/bootstrap');
      app.boot = boot;
      app.multi = boot.multi_label;
      app.state = boot.state;

      el.lang.innerHTML = '';
      for (const lang of boot.languages) el.lang.add(new Option(lang.name, lang.code));

      const spec = { ...boot.spec_defaults, ...safeParse(localStorage.getItem('segrev.spec')) };
      el.specType.value = spec.type || 'mel';
      el.specFmin.value = spec.fmin ?? 0;
      el.specFmax.value = spec.fmax ?? 0;
      el.specDb.value = spec.db ?? -80;

      await setLanguage(localStorage.getItem('segrev.lang') || boot.lang, { persist: false });
      renderPattern(boot.pattern);
      if (!app.state.folder) el.folderInput.focus();
      else loadAudio();
    } catch (err) {
      document.body.innerHTML = `<main><div class="error">${escapeHtml(err.message)}</div></main>`;
    }
  })();

  function safeParse(text) {
    try { return text ? JSON.parse(text) : {}; } catch (_) { return {}; }
  }
})();
