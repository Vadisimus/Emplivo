import { intakeConfig } from './intake-config.mjs';

const MAX_BYTES = 5 * 1024 ** 2;
const copy = {
  invalid_fields: ['Перевірте заповнені поля.', 'Check the highlighted fields.', 'Проверьте заполненные поля.'],
  cv_required: ['Додайте резюме у форматі PDF або DOCX.', 'Attach a PDF or DOCX CV.', 'Прикрепите резюме в PDF или DOCX.'],
  too_large: ['Розмір резюме має бути до 5 МБ.', 'Your CV must be 5 MB or smaller.', 'Размер резюме — не более 5 МБ.'],
  invalid_file: ['Завантажте коректний PDF або DOCX.', 'Upload a valid PDF or DOCX.', 'Загрузите корректный PDF или DOCX.'],
  challenge: ['Пройдіть перевірку й повторіть надсилання.', 'Complete the verification and try again.', 'Пройдите проверку и повторите отправку.'],
  rate_limit: ['Забагато спроб. Спробуйте за хвилину.', 'Too many attempts. Try again in a minute.', 'Слишком много попыток. Повторите через минуту.'],
  delivery_rejected: ['Сервіс відхилив заявку. Можна повторити надсилання.', 'Delivery was rejected. You can try again.', 'Сервис отклонил заявку. Можно повторить отправку.'],
  unavailable: ['Сервіс тимчасово недоступний. Спробуйте пізніше.', 'The service is temporarily unavailable. Please try later.', 'Сервис временно недоступен. Попробуйте позже.'],
  privacy_changed: ['Оновіть сторінку й ознайомтеся з чинною політикою.', 'Reload the page and review the current policy.', 'Обновите страницу и ознакомьтесь с действующей политикой.'],
  vacancy_closed: ['Ця вакансія більше не приймає відгуки. Перевірте каталог.', 'This vacancy is closed. Browse the job listings.', 'Вакансия закрыта. Посмотрите другие вакансии.'],
  inactive: ['Онлайн-форма тимчасово недоступна. Скористайтеся контактами нижче.', 'The online form is unavailable. Use the contact details below.', 'Онлайн-форма недоступна. Воспользуйтесь контактами ниже.'],
  sending: ['Надсилаємо заявку…', 'Sending your submission…', 'Отправляем заявку…'],
  uploaded: ['Дані завантажено. Підтверджуємо доставку…', 'Upload complete. Confirming delivery…', 'Данные загружены. Подтверждаем доставку…'],
  uncertain: ['Доставку не підтверджено. Номер звернення', 'Delivery is unconfirmed. Reference', 'Доставка не подтверждена. Номер обращения'],
};
const text = key => (copy[key] ?? copy.unavailable)[{ en: 1, ru: 2 }[document.documentElement.lang] ?? 0];

let challengeScript;
function loadChallenge() {
  if (challengeScript) return challengeScript;
  challengeScript = new Promise((resolve, reject) => {
    window.emplivoChallengeReady = () => resolve(window.turnstile);
    const script = document.createElement('script');
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=emplivoChallengeReady';
    script.async = true;
    script.onerror = reject;
    document.head.append(script);
  });
  return challengeScript;
}

function send(url, data, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener('progress', event => onProgress(event));
    xhr.upload.addEventListener('load', () => onProgress(null));
    xhr.open('POST', url);
    xhr.responseType = 'json';
    xhr.timeout = 45000;
    xhr.onload = () => resolve({ status: xhr.status, body: xhr.response });
    xhr.onerror = xhr.ontimeout = xhr.onabort = reject;
    xhr.send(data);
  });
}

export async function mountIntake(form) {
  const submit = form.querySelector('[type="submit"]');
  const spinner = form.querySelector('[data-spin]');
  const status = form.querySelector('[data-status]');
  const progress = form.querySelector('progress');
  const success = form.parentElement.querySelector('[data-success]');
  const fileInput = form.elements.namedItem('cv');
  const challengeTarget = form.querySelector('[data-challenge]');
  const kind = form.dataset.intake;
  const params = new URLSearchParams(location.search);
  if (kind === 'apply') {
    const vacancy = params.get('vacancy');
    if (vacancy && /^[a-z0-9-]{1,80}$/.test(vacancy)) form.elements.vacancyId.value = vacancy;
  } else {
    const service = params.get('service');
    const input = form.elements.service;
    if (service && [...input.options].some(option => option.value === service)) input.value = service;
  }
  const siteKey = intakeConfig.siteKey;
  const agencyHost = ['emplivo.com.ua', 'www.emplivo.com.ua'].includes(location.hostname);
  const usePhp = agencyHost && kind === 'apply' && !intakeConfig.workerOrigin && !form.elements.vacancyId.value;
  const endpoint = intakeConfig.workerOrigin && siteKey
    ? new URL('/api/' + kind, intakeConfig.workerOrigin)
    : usePhp ? new URL(form.dataset.legacyEndpoint, document.baseURI) : null;
  const feedback = (message, state = 'info') => {
    status.dataset.state = state;
    status.textContent = message;
  };
  if (!endpoint) {
    feedback(text('inactive'));
    return;
  }
  if (endpoint.protocol !== 'https:') throw new Error('Configure an HTTPS intake endpoint.');

  const id = crypto.randomUUID();
  let challenge;
  let widgetId;
  let busy = false;
  if (usePhp) {
    form.elements.phone.required = true;
    fileInput.required = false;
  } else {
    try {
      challenge = await loadChallenge();
      widgetId = challenge.render(challengeTarget, {
        sitekey: siteKey, action: kind, language: document.documentElement.lang,
      });
    } catch {
      feedback(text('unavailable'), 'error');
      return;
    }
  }
  submit.disabled = false;

  function validate(control) {
    if (control === fileInput) {
      const file = fileInput.files[0];
      let error = '';
      if (file?.size > MAX_BYTES) error = text('too_large');
      else if (file && (!file.size || !/\.(pdf|docx)$/i.test(file.name))) error = text('invalid_file');
      fileInput.setCustomValidity(error);
    }
    if (control.willValidate) {
      if (control.validity.valid) control.removeAttribute('aria-invalid');
      else control.setAttribute('aria-invalid', 'true');
    }
  }
  for (const event of ['input', 'change', 'invalid']) {
    form.addEventListener(event, e => {
      if (e.target instanceof HTMLElement) validate(e.target);
    }, true);
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy) return;
    if (fileInput) validate(fileInput);
    if (!form.reportValidity()) return;
    const token = challenge?.getResponse(widgetId);
    if (!usePhp && !token) {
      feedback(text('challenge'), 'error');
      return;
    }

    const data = new FormData(form);
    if (usePhp) {
      data.set('fullName', data.get('name'));
      data.set('role', '');
      data.set('destination', 'any');
      data.set('experience', '');
      data.set('consent', 'on');
      if (!data.get('cv')?.size) data.delete('cv');
    } else {
      data.set('cf-turnstile-response', token);
    }
    data.set('submissionId', id);
    busy = true;
    submit.disabled = true;
    spinner.hidden = false;
    progress.hidden = false;
    progress.removeAttribute('value');
    submit.setAttribute('aria-busy', 'true');
    feedback(text('sending'));

    let delivered = false;
    try {
      const { status: code, body } = await send(endpoint.href, data, event => {
        if (event?.lengthComputable) progress.value = event.loaded / event.total;
        if (!event) {
          progress.value = 1;
          feedback(text('uploaded'));
        }
      });
      if (code === 200 && body?.ok === true && body.id === id) {
        delivered = true;
        success.querySelector('[data-reference]').textContent = id;
        form.reset();
        form.hidden = true;
        success.hidden = false;
        success.focus();
      } else if (body?.error === 'delivery_unknown' || !body?.error) {
        feedback(text('uncertain') + ' ' + id + '.', 'error');
      } else {
        feedback(text(body.error), 'error');
      }
    } catch {
      feedback(text('uncertain') + ' ' + id + '.', 'error');
    } finally {
      busy = false;
      progress.hidden = true;
      spinner.hidden = true;
      submit.removeAttribute('aria-busy');
      if (!delivered) {
        challenge?.reset(widgetId);
        submit.disabled = false;
      }
    }
  });
}

for (const form of document.querySelectorAll('[data-intake]')) {
  mountIntake(form).catch(() => {
    form.querySelector('[data-status]').textContent = text('unavailable');
  });
}
