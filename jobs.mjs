import { savedIDs } from './navigation.mjs';

export function matchesSalary(pay, filter) {
  if (!filter.currency || !filter.unit) return true;
  if (!pay) return Boolean(filter.includeUndisclosed);
  if (pay.currency !== filter.currency || pay.unit !== filter.unit) return false;
  const low = filter.min ?? 0;
  const high = filter.max ?? Infinity;
  return low <= high && pay.max >= low && pay.min <= high;
}

const today = () => new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Europe/Kyiv', year: 'numeric', month: '2-digit', day: '2-digit',
}).format();
const expiryDay = today();
const expired = card => Boolean(card.dataset.until && card.dataset.until < expiryDay);

function salary(card) {
  const { currency, unit, low, high } = card.dataset;
  if (!currency || !unit) return null;
  return { currency, unit, min: Number(low), max: Number(high) };
}

function syncExpiry() {
  for (const section of document.querySelectorAll('[data-vacancy-until]')) {
    if (section.dataset.vacancyUntil >= expiryDay) continue;
    section.hidden = true;
    const notice = section.parentElement.querySelector('[data-vacancy-expired]');
    if (notice) notice.hidden = false;
  }
}

function setupCatalog(form, list) {
  const fields = form.elements;
  const cards = [...list.querySelectorAll('[data-job-id]')];
  const defaultOrder = new Map(cards.map((card, index) => [card, index]));
  const count = document.querySelector('[data-results]');
  const noJobs = document.querySelector('[data-no-jobs]');
  const error = document.querySelector('#filter-error');
  const paramsToFields = () => {
    const params = new URLSearchParams(location.search);
    for (const field of [...fields].filter(field => field.name)) {
      let value = params.get(field.name) ?? '';
      if (field instanceof HTMLSelectElement && ![...field.options].some(option => option.value === value)) {
        value = field.options[0].value;
      }
      if (field.type === 'checkbox') field.checked = value === '1';
      else field.value = value.slice(0, 120);
    }
  };
  function update(writeURL) {
    const [currency, unit] = fields.pay.value.split('/');
    const usingPay = Boolean(currency && unit);
    for (const field of [fields.min, fields.max, fields.undisclosed]) field.disabled = !usingPay;
    fields.sort.querySelector('[value=pay]').disabled = !usingPay;
    if (!usingPay) {
      fields.min.value = '';
      fields.max.value = '';
      fields.undisclosed.checked = false;
      fields.sort.value = 'date';
    }
    const min = Number.isFinite(fields.min.valueAsNumber) ? fields.min.valueAsNumber : undefined;
    const max = Number.isFinite(fields.max.valueAsNumber) ? fields.max.valueAsNumber : undefined;
    const invalid = !fields.min.validity.valid || !fields.max.validity.valid ||
      (min !== undefined && max !== undefined && min > max);
    error.textContent = invalid ? error.dataset.invalid : '';
    fields.min.setAttribute('aria-invalid', String(invalid));
    fields.max.setAttribute('aria-invalid', String(invalid));
    if (invalid) return;

    const query = fields.q.value.trim().toLocaleLowerCase(document.documentElement.lang);
    const payFilter = { currency, unit, min, max, includeUndisclosed: fields.undisclosed.checked };
    let visible = 0;
    for (const card of cards) {
      const position = card.querySelector('[data-location]').textContent.trim();
      const text = [card.querySelector('[data-job-title]').textContent, card.querySelector('[data-employer]').textContent, position]
        .join(' ').toLocaleLowerCase(document.documentElement.lang);
      const show = !expired(card) && text.includes(query) && (!fields.city.value || position === fields.city.value) &&
        (!fields.sector.value || card.dataset.sector === fields.sector.value) &&
        (!fields.mode.value || card.dataset.mode.split(' ').includes(fields.mode.value)) &&
        (!fields.term.value || card.dataset.term === fields.term.value) &&
        matchesSalary(salary(card), payFilter);
      card.hidden = !show;
      if (show) visible++;
    }
    const sorted = [...cards].sort((left, right) => {
      if (fields.sort.value === 'pay') {
        const sortable = card => {
          const pay = salary(card);
          return pay?.currency === currency && pay?.unit === unit ? pay.max : -1;
        };
        const order = sortable(right) - sortable(left);
        if (order) return order;
      }
      return defaultOrder.get(left) - defaultOrder.get(right);
    });
    let cursor = list.firstElementChild;
    for (const card of sorted) {
      if (card === cursor) cursor = cursor.nextElementSibling;
      else list.insertBefore(card, cursor);
    }
    count.textContent = count.dataset.label + ' ' + visible;
    noJobs.hidden = visible > 0;
    if (writeURL) {
      const url = new URL(location.href);
      const current = new FormData(form);
      for (const key of ['q', 'city', 'sector', 'mode', 'term', 'pay', 'min', 'max', 'undisclosed', 'sort']) {
        const value = current.get(key);
        if (value && (key !== 'sort' || value !== 'date')) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
      }
      history.replaceState(null, '', url);
    }
  }
  paramsToFields();
  form.hidden = false;
  update(false);
  form.addEventListener('input', () => update(true));
  form.addEventListener('submit', event => {
    event.preventDefault();
    update(true);
  });
  form.addEventListener('reset', () => queueMicrotask(() => update(true)));
  window.addEventListener('popstate', () => {
    paramsToFields();
    update(false);
  });
}

if (typeof document !== 'undefined') {
  syncExpiry();
  const form = document.querySelector('#job-filters');
  if (form) setupCatalog(form, document.querySelector('[data-catalog]'));
  const savedList = document.querySelector('[data-saved-catalog]');
  if (savedList) {
    const updateSaved = () => {
      const ids = savedIDs();
      let visible = 0;
      for (const card of savedList.querySelectorAll('[data-job-id]')) {
        card.hidden = !ids.has(card.dataset.jobId);
        if (!card.hidden) visible++;
      }
      savedList.hidden = visible === 0;
      document.querySelector('[data-saved-empty]').hidden = visible !== 0;
    };
    document.addEventListener('emplivo:saved', updateSaved);
    updateSaved();
  }
}
