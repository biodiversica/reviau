/* Pure helpers shared by the client — no DOM, no globals of their own.
 *
 * Kept apart from app.js so they can be exercised directly by the test suite,
 * which has no browser to drive.
 */
(function (root) {
  'use strict';

  /** Frequency axes the server can draw; anything else falls back to the first. */
  const SPEC_TYPES = ['mel', 'fft', 'log'];

  /** Split a comma-separated label box into a clean list, keeping the order. */
  function splitLabels(text) {
    const out = [];
    for (const raw of String(text === undefined || text === null ? '' : text).split(',')) {
      const part = raw.trim();
      if (part && !out.includes(part)) out.push(part);
    }
    return out;
  }

  /** Read a number out of an input, clamped, falling back when it is not one. */
  function clampInt(value, lo, hi, fallback) {
    const n = Number.parseInt(value, 10);
    if (Number.isNaN(n)) return fallback;
    return Math.min(hi, Math.max(lo, n));
  }

  /* A segment's position in the pending list is not a stable identity: giving a
   * verdict drops the current clip, so the next one takes the very same index.
   * Keying the media URLs on the clip's path as well keeps two different clips
   * from sharing one URL — otherwise the browser answers the second request
   * with the first clip's image, and the view appears frozen. */
  function mediaKey(segment) {
    return (segment && (segment.relpath || segment.name)) || '';
  }

  /** URL of the spectrogram for *segment*, drawn with the settings in *view*. */
  function spectrogramUrl(segment, view) {
    const query = new URLSearchParams({
      index: String(segment.index),
      type: SPEC_TYPES.includes(view.type) ? view.type : SPEC_TYPES[0],
      fmin: String(clampInt(view.fmin, 0, 96000, 0)),
      fmax: String(clampInt(view.fmax, 0, 96000, 0)),
      db: String(clampInt(view.db, -120, -20, -80)),
      v: mediaKey(segment),
    });
    return `/api/spectrogram?${query.toString()}`;
  }

  /** URL of the audio for *segment*. */
  function audioUrl(segment) {
    const query = new URLSearchParams({
      index: String(segment.index),
      v: mediaKey(segment),
    });
    return `/api/audio?${query.toString()}`;
  }

  /** Toggle a label in a selection; with `single`, it replaces the selection. */
  function toggleLabel(selection, label, single) {
    if (single) return selection.length === 1 && selection[0] === label ? [] : [label];
    return selection.includes(label)
      ? selection.filter((x) => x !== label)
      : selection.concat([label]);
  }

  /* The buttons on screen: the list the reviewer curates, plus any label the
   * current selection uses that is not on it — a clip whose own label has been
   * trimmed away from the list must still show, or its verdict would silently
   * change what it is labelled. */
  function buttonLabels(list, selection) {
    const out = (list || []).slice();
    for (const label of selection || []) if (!out.includes(label)) out.push(label);
    return out;
  }

  /* The labels a segment is filed as holding, for the button that was pressed.
   *
   * The chips say what is in the clip; the button only says what that means for
   * the prediction, so the two can never disagree:
   *   correct — the prediction is in the clip, along with anything else selected
   *             (with one label per segment, the prediction alone);
   *   wrong   — the prediction is not: whatever else is selected is what the clip
   *             really holds, and nothing selected means nothing on the list;
   *   unsure  — the selection as it stands, kept as a guess.
   * A clip that came with no prediction has nothing to be right about, so every
   * button saves the selection. The server works the outcome out again from
   * these labels — it never takes the button's word for it. */
  function reviewLabels(kind, selection, predicted, single) {
    const chosen = (selection || []).slice();
    if (!predicted || kind === 'unsure') return chosen;
    const others = chosen.filter((x) => x !== predicted);
    if (kind === 'correct') return single ? [predicted] : [predicted].concat(others);
    return others;
  }

  /** The recently opened folders, *path* first, without repeats, at most *max*. */
  function rememberFolder(recent, path, max) {
    const clean = String(path === undefined || path === null ? '' : path).trim();
    const rest = (recent || []).filter((x) => typeof x === 'string' && x && x !== clean);
    return (clean ? [clean] : []).concat(rest).slice(0, max || 8);
  }

  /* Light / dark theme: follow the OS, or pin one. "system" is a real third
   * state rather than the absence of a choice — without it there is no way
   * back to following the OS once a theme is pinned. The order is the order
   * the header button cycles through them. */
  const THEME_MODES = ['system', 'light', 'dark'];
  const THEME_GLYPHS = { system: '◐', light: '☀', dark: '☾' };

  /** A stored theme read back safely: anything unknown means "system". */
  function themeMode(stored) {
    return THEME_MODES.includes(stored) ? stored : 'system';
  }

  /** The mode after *mode*, as the header button cycles. */
  function nextTheme(mode) {
    return THEME_MODES[(THEME_MODES.indexOf(themeMode(mode)) + 1) % THEME_MODES.length];
  }

  const lib = {
    SPEC_TYPES, splitLabels, clampInt, mediaKey,
    spectrogramUrl, audioUrl, toggleLabel, buttonLabels, reviewLabels, rememberFolder,
    THEME_MODES, THEME_GLYPHS, themeMode, nextTheme,
  };
  if (typeof module === 'object' && module.exports) module.exports = lib;
  else root.SegRev = lib;
})(typeof globalThis !== 'undefined' ? globalThis : this);
