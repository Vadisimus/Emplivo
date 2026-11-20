const SAVED_KEY = 'ec-saved'; // Existing Emplivo installations already use this key.

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

function toggleSave(event) {
  const button = event.target.closest('[data-save-job]');
  if (!button) return;
  const id = button.dataset.saveJob;
  if (!/^[a-z0-9-]+$/.test(id) || id.startsWith('demo-')) return;
  if (saved.has(id)) saved.delete(id);
  else saved.add(id);
  try {
    localStorage.setItem(SAVED_KEY, JSON.stringify([...saved]));
  } catch {
    const status = document.querySelector('[data-saved-status]');
    if (status) status.textContent = status.dataset.storageUnavailable;
  }
  syncSavedUI();
  document.dispatchEvent(new Event('emplivo:saved'));
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
}

if (typeof document !== 'undefined') mountNavigation();
