const SAVED_KEY = 'ec-saved'; // Existing Emplivo installations already use this key.
const BOOKMARK_MESSAGES = {
  uk: ['Вакансію збережено', 'Вакансію вилучено зі збережених'],
  en: ['Job saved', 'Job removed from saved jobs'],
  ru: ['Вакансия сохранена', 'Вакансия удалена из сохранённых'],
};
const bookmarkAnimations = new WeakMap();
let toastTimer;

function readSaved() {
  try {
    const ids = JSON.parse(localStorage.getItem(SAVED_KEY) ?? '[]');
    return new Set((Array.isArray(ids) ? ids : []).filter(id =>
      typeof id === 'string' && /^[a-z0-9-]+$/.test(id) && !id.startsWith('demo-'),
    ));
  } catch {
    return new Set();
  }
}

let saved = readSaved();
export const savedIDs = () => new Set(saved);

export function syncSavedUI() {
  for (const count of document.querySelectorAll('[data-saved-count]')) count.textContent = saved.size;
  for (const button of document.querySelectorAll('[data-save-job]')) {
    button.hidden = false;
    button.setAttribute('aria-pressed', String(saved.has(button.dataset.saveJob)));
  }
}

function notifyBookmark(button, added) {
  if (!matchMedia('(prefers-reduced-motion: reduce)').matches && button.animate) {
    bookmarkAnimations.get(button)?.cancel();
    const animation = button.animate([
      { transform: 'scale(1)' },
      { transform: 'scale(1.13)', offset: .36 },
      { transform: 'scale(.95)', offset: .68 },
      { transform: 'scale(1)' },
    ], { duration: 400, easing: 'ease-out' });
    bookmarkAnimations.set(button, animation);
  }
  const toast = document.querySelector('[data-save-toast]');
  if (!toast) return;
  const messages = BOOKMARK_MESSAGES[document.documentElement.lang] ?? BOOKMARK_MESSAGES.uk;
  toast.textContent = messages[added ? 0 : 1];
  toast.dataset.visible = '';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    delete toast.dataset.visible;
  }, 2800);
}

function toggleSave(event) {
  const button = event.target.closest('[data-save-job]');
  if (!button) return;
  const id = button.dataset.saveJob;
  if (!/^[a-z0-9-]+$/.test(id) || id.startsWith('demo-')) return;
  const added = !saved.has(id);
  if (added) saved.add(id);
  else saved.delete(id);
  try {
    localStorage.setItem(SAVED_KEY, JSON.stringify([...saved]));
  } catch {
    const status = document.querySelector('[data-saved-status]');
    if (status) status.textContent = status.dataset.storageUnavailable;
  }
  syncSavedUI();
  notifyBookmark(button, added);
  document.dispatchEvent(new Event('emplivo:saved'));
}

function mountHeroMotion() {
  const hero = document.querySelector('[data-hero-motion]');
  const toggle = hero?.querySelector('[data-hero-motion-toggle]');
  if (!hero || !toggle) return;
  hero.dataset.heroMotion = 'running';
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    const paused = hero.dataset.heroMotion === 'running';
    hero.dataset.heroMotion = paused ? 'paused' : 'running';
    toggle.setAttribute('aria-pressed', String(paused));
  });
}

export function mountNavigation() {
  const header = document.querySelector('.site-header');
  const trigger = header?.querySelector('[data-menu-toggle]');
  const source = header?.querySelector('.navigation');
  const dialog = document.getElementById('site-menu');
  if (trigger && source && dialog?.showModal) {
    dialog.querySelector('[data-menu-links]').replaceChildren(source.cloneNode(true));
    header.dataset.enhanced = '';
    trigger.hidden = false;
    trigger.addEventListener('click', () => {
      if (dialog.open) return;
      dialog.showModal();
      document.body.classList.add('menu-open');
      trigger.setAttribute('aria-expanded', 'true');
    });
    dialog.addEventListener('close', () => {
      document.body.classList.remove('menu-open');
      trigger.setAttribute('aria-expanded', 'false');
      if (trigger.getClientRects().length) trigger.focus();
      else source.querySelector('[aria-current="page"], a')?.focus();
    });
    const wide = matchMedia('(min-width:72.001rem)');
    wide.addEventListener('change', event => {
      if (event.matches && dialog.open) dialog.close();
    });
  }
  document.addEventListener('click', toggleSave);
  window.addEventListener('storage', event => {
    if (event.key !== null && event.key !== SAVED_KEY) return;
    saved = readSaved();
    syncSavedUI();
    document.dispatchEvent(new Event('emplivo:saved'));
  });
  syncSavedUI();
  mountHeroMotion();
}

if (typeof document !== 'undefined') mountNavigation();
