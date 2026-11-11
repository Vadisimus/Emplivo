(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const dictionaries = window.EMPLIVO_TEXT;
  const params = new URLSearchParams(location.search);
  const design = 'signature';
  document.documentElement.dataset.design = design;
  let storedLanguage;
  try { storedLanguage = localStorage.getItem('emplivo-language'); } catch {}
  let language = ['uk', 'en'].includes(params.get('lang')) ? params.get('lang') : ['uk', 'en'].includes(storedLanguage) ? storedLanguage : 'uk';
  const t = key => dictionaries[language][key] || dictionaries.uk[key] || key;
  const form = $('#candidate-form');
  const role = form.elements.role;
  const destination = form.elements.destination;
  const cv = $('#cv-file');
  const submit = $('#submit-button');
  const errorBox = $('#form-error');
  const success = $('#form-success');
  const fieldErrors = new Map();
  let globalError = null;
  let activeService = null;
  let submitting = false;
  let pending = null;
  let savedId = null;
  const jobId = 'kitchen-helper-ua-001';
  const fields = ['fullName', 'phone', 'email', 'role', 'destination', 'experience', 'cv', 'consent'];

  const stepGroups = [['fullName', 'phone', 'email'], ['role', 'destination', 'experience'], ['cv', 'consent']];
  let currentStep = 0, reachedStep = 0, activeTab = 0;
  let jobSaved = false, savedOnly = false;
  try { jobSaved = localStorage.getItem('emplivo-saved-role') === jobId; } catch {}

  function showStep(index, focus = false) {
    currentStep = index;
    reachedStep = Math.max(reachedStep, index);
    renderStep();
    if (focus) $('#form-step-' + currentStep + ' legend').focus();
  }
  function renderStep() {
    $$('.form-step').forEach((panel, index) => { panel.hidden = index !== currentStep; });
    $$('[data-form-step]').forEach((button, index) => {
      if (index === currentStep) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
      button.disabled = submitting || index > reachedStep;
      button.classList.toggle('is-complete', index < currentStep);
    });
    $('#form-step-count').textContent = t('stepCounter').replace('{step}', String(currentStep + 1));
    $('#form-back').hidden = currentStep === 0;
    $('#form-next').hidden = currentStep === 2;
    submit.hidden = currentStep !== 2;
    $('#summary-contact').textContent = [form.elements.fullName.value, form.elements.phone.value, form.elements.email.value].filter(Boolean).join(' · ');
    $('#summary-role').textContent = role.value === jobId ? t('roleOption') : t('generalApplication');
    $('#summary-destination').textContent = t({ any:'anyDestination', ukraine:'ukraine', other:'otherCountries' }[destination.value] || 'anyDestination');
  }
  function focusFieldError() {
    const name = fieldErrors.keys().next().value;
    if (!name) return;
    const index = stepGroups.findIndex(group => group.includes(name));
    if (index !== -1) showStep(index);
    form.elements[name]?.focus();
  }
  function nextStep() {
    globalError = null;
    if (validate(stepGroups[currentStep])) showStep(Math.min(currentStep + 1, 2), true);
  }
  function renderSaved() {
    $('#save-job').setAttribute('aria-pressed', String(jobSaved));
    $('#save-job-label').textContent = t(jobSaved ? 'savedJob' : 'saveJob');
    $('#saved-only').setAttribute('aria-pressed', String(savedOnly));
    $('#saved-only').textContent = t('savedFilter') + ' (' + (jobSaved ? 1 : 0) + ')';
  }
  function selectTab(index, focus = false) {
    activeTab = index;
    $$('[data-tab]').forEach((button, i) => {
      button.setAttribute('aria-selected', String(i === index)); button.tabIndex = i === index ? 0 : -1;
      $('#job-panel-' + i).hidden = i !== index;
      if (focus && i === index) button.focus();
    });
  }

  function renderErrors() {
    $('#remove-cv').hidden = !cv.files.length;
    for (const name of fields) {
      const input = form.elements[name];
      const error = $('#error-' + name);
      const key = fieldErrors.get(name);
      if (error) error.textContent = key ? t(key) : '';
      if (input) {
        input.setAttribute('aria-invalid', key ? 'true' : 'false');
        input.setAttribute('aria-describedby', name === 'cv' ? 'cv-hint error-cv' : 'error-' + name);
      }
    }
    errorBox.hidden = !globalError;
    errorBox.textContent = globalError ? t(globalError) : '';
  }

  function filterJobs() {
    const normalize = value => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[’ʼ']/g, '');
    const query = normalize($('#job-search').value.trim());
    const haystack = normalize('Помічник кухаря кухня харчування Kitchen Helper kitchen food service Умань Уманський регіон Uman region Україна Ukraine Filipino Philippines Філіппіни E-UA-001');
    const country = $('#country-filter').value;
    const sector = $('#sector-filter').value;
    const matches = (!savedOnly || jobSaved) && query.split(/\s+/).every(word => haystack.includes(word)) && (country === 'all' || country === 'ukraine') && (sector === 'all' || sector === 'kitchen');
    $('#kitchen-job').hidden = !matches;
    $('#job-empty').hidden = matches;
    $('#job-count').textContent = t('resultCount').replace('{count}', matches ? '1' : '0');
  }

  const services = { recruitment: ['serviceOneTitle', 'recruitmentDetails'], international: ['serviceTwoTitle', 'internationalDetails'], support: ['serviceThreeTitle', 'supportDetails'] };
  function renderService() {
    $$('.service-more').forEach(button => {
      button.setAttribute('aria-controls', 'service-panel');
      button.setAttribute('aria-expanded', String(button.dataset.service === activeService));
    });
    $('#service-panel').hidden = !activeService;
    if (activeService) {
      $('#service-panel-title').textContent = t(services[activeService][0]);
      $('#service-panel-body').textContent = t(services[activeService][1]);
    }
  }

  function translate(persist = false) {
    document.documentElement.lang = language;
    document.title = t('pageTitle');
    $('meta[name="description"]').setAttribute('content', t('metaDescription'));
    $$('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    $$('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    $$('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
    $$('[data-lang]').forEach(el => { el.setAttribute('aria-pressed', String(el.dataset.lang === language)); });
    $('#menu-toggle').setAttribute('aria-label', t($('#menu-toggle').getAttribute('aria-expanded') === 'true' ? 'closeMenu' : 'openMenu'));
    $('#file-label').textContent = cv.files[0]?.name || t('addCv');
    submit.textContent = t(submitting ? 'submitting' : 'submit');
    if (savedId) $('#application-reference').textContent = t('referencePrefix') + savedId;
    filterJobs(); renderService(); renderErrors(); renderStep(); renderSaved();
    if (persist) {
      try { localStorage.setItem('emplivo-language', language); } catch {}
      const url = new URL(location.href); url.searchParams.set('lang', language);
      try { history.replaceState(null, '', url.pathname + url.search + url.hash); } catch {}
    }
  }

  $$('[data-lang]').forEach(button => button.addEventListener('click', () => { language = button.dataset.lang; $('#interaction-status').textContent = ''; translate(true); }));
  $('#menu-toggle').addEventListener('click', () => {
    const open = $('#menu-toggle').getAttribute('aria-expanded') !== 'true';
    $('#menu-toggle').setAttribute('aria-expanded', String(open));
    $('#menu-toggle').setAttribute('aria-label', t(open ? 'closeMenu' : 'openMenu'));
    $('#navigation').classList.toggle('is-open', open);
  });
  $$('#navigation a').forEach(link => link.addEventListener('click', () => {
    $('#navigation').classList.remove('is-open');
    $('#menu-toggle').setAttribute('aria-expanded', 'false');
    $('#menu-toggle').setAttribute('aria-label', t('openMenu'));
  }));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && $('#menu-toggle').getAttribute('aria-expanded') === 'true') {
      $('#navigation').classList.remove('is-open'); $('#menu-toggle').setAttribute('aria-expanded', 'false');
      $('#menu-toggle').setAttribute('aria-label', t('openMenu')); $('#menu-toggle').focus();
    }
  });
  $$('.service-more').forEach(button => button.addEventListener('click', () => {
    activeService = activeService === button.dataset.service ? null : button.dataset.service;
    renderService();
  }));
  $('#service-close').addEventListener('click', () => {
    const trigger = $$('.service-more').find(button => button.dataset.service === activeService);
    activeService = null; renderService(); trigger?.focus();
  });
  ['job-search', 'country-filter', 'sector-filter'].forEach(id => $('#' + id).addEventListener(id === 'job-search' ? 'input' : 'change', filterJobs));
  $('#reset-filters').addEventListener('click', () => { $('#job-search').value = ''; $('#country-filter').value = 'all'; $('#sector-filter').value = 'all'; savedOnly = false; renderSaved(); filterJobs(); });

  function setJobDestination() {
    if (role.value === jobId) destination.value = 'ukraine';
    fieldErrors.delete('role'); fieldErrors.delete('destination'); renderErrors();
  }
  role.addEventListener('change', setJobDestination);
  $$('.apply-job').forEach(button => button.addEventListener('click', () => {
    if (form.hidden) {
      form.reset(); pending = null; savedId = null; globalError = null; fieldErrors.clear(); reachedStep = 0;
      form.hidden = false; success.hidden = true; translate();
    }
    role.value = jobId; setJobDestination(); showStep(0);
    $('#application').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    form.elements.fullName.focus({ preventScroll: true });
  }));

  function fileProblem() {
    const file = cv.files[0];
    if (!file) return null;
    if (!/\.(pdf|docx)$/i.test(file.name)) return 'errorCvType';
    if (file.size === 0) return 'errorCvEmpty';
    if (file.size > 5 * 1024 * 1024) return 'errorCvLarge';
    return null;
  }
  cv.addEventListener('change', () => {
    $('#file-label').textContent = cv.files[0]?.name || t('addCv');
    const problem = fileProblem();
    if (problem) fieldErrors.set('cv', problem); else fieldErrors.delete('cv');
    renderErrors();
  });
  $('#remove-cv').addEventListener('click', () => {
    cv.value = ''; fieldErrors.delete('cv');
    $('#file-label').textContent = t('addCv'); renderErrors(); cv.focus();
  });
  fields.forEach(name => {
    const input = form.elements[name];
    input?.addEventListener(name === 'consent' || name === 'destination' ? 'change' : 'input', () => {
      if (name !== 'cv') fieldErrors.delete(name);
      globalError = null; renderErrors();
    });
  });

  function validate(group = fields) {
    if (group === fields) fieldErrors.clear(); else group.forEach(name => fieldErrors.delete(name));
    const mark = (name, key) => { if (group.includes(name)) fieldErrors.set(name, key); };
    const value = name => form.elements[name].value.trim();
    if (value('fullName').length < 2 || value('fullName').length > 120) mark('fullName', 'errorName');
    const phone = value('phone'), digits = phone.replace(/\D/g, '');
    if (digits.length < 9 || digits.length > 15 || phone.length > 32 || !/^\+?[\d\s().-]+$/.test(phone)) mark('phone', 'errorPhone');
    const email = value('email');
    if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) mark('email', 'errorEmail');
    if (!['', jobId].includes(role.value)) mark('role', 'errorRole');
    if (!['any', 'ukraine', 'other'].includes(destination.value)) mark('destination', 'errorDestination');
    else if (role.value === jobId && destination.value !== 'ukraine') mark('destination', 'errorJobDestination');
    if (value('experience').length > 3000) mark('experience', 'errorExperience');
    if (!form.elements.consent.checked) mark('consent', 'errorConsent');
    const fileError = fileProblem(); if (fileError) mark('cv', fileError);
    renderErrors();
    if (group.some(name => fieldErrors.has(name))) { focusFieldError(); return false; }
    return true;
  }

  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
    const s = [...bytes].map(x => x.toString(16).padStart(2, '0')).join('');
    return `${s.slice(0,8)}-${s.slice(8,12)}-${s.slice(12,16)}-${s.slice(16,20)}-${s.slice(20)}`;
  }
  function busy(value) {
    submitting = value; form.setAttribute('aria-busy', String(value));
    [...form.elements].forEach(input => { input.disabled = value; });
    submit.textContent = t(value ? 'submitting' : 'submit'); renderStep();
  }
  function upstreamErrors(errors) {
    const keys = { fullName:'errorName', phone:'errorPhone', email:'errorEmail', role:'errorRole', destination:'errorDestination', experience:'errorExperience', consent:'errorConsent' };
    Object.entries(errors || {}).forEach(([name, message]) => {
      if (name === 'cv') fieldErrors.set('cv', /порожн|empty/i.test(String(message)) ? 'errorCvEmpty' : /завелик|5\s*МБ|too large/i.test(String(message)) ? 'errorCvLarge' : /вміст|content/i.test(String(message)) ? 'errorCvContent' : 'errorCvUpload');
      else if (keys[name]) fieldErrors.set(name, keys[name]);
    });
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (submitting) return;
    if (currentStep < 2) { nextStep(); return; }
    globalError = null;
    if (!validate()) return;
    if (navigator.onLine === false) { globalError = 'errorOffline'; renderErrors(); return; }
    const data = new FormData(form);
    const file = cv.files[0];
    const fingerprint = JSON.stringify([form.elements.fullName.value, form.elements.phone.value, form.elements.email.value, role.value, destination.value, form.elements.experience.value, file?.name, file?.size, file?.lastModified]);
    if (!pending || pending.fingerprint !== fingerprint) pending = { fingerprint, id:uuid() };
    data.set('submissionId', pending.id);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    busy(true);
    try {
      const response = await fetch('/api/applications.php', { method:'POST', body:data, signal:controller.signal, headers:{ 'Accept-Language':language } });
      const result = await response.json().catch(() => null);
      if (!response.ok || result?.ok !== true || result.id !== pending.id) {
        upstreamErrors(result?.errors);
        globalError = response.status === 422 ? 'errorFields' : response.status === 413 ? 'errorCvLarge' : [401,403].includes(response.status) ? 'errorOrigin' : response.status === 409 ? 'errorConflict' : response.status === 400 ? 'errorRefresh' : 'errorServer';
        if (response.status === 409) pending = null;
        renderErrors();
        return;
      }
      savedId = result.id; form.hidden = true; success.hidden = false;
      $('#application-reference').textContent = t('referencePrefix') + savedId;
      success.focus();
    } catch (error) {
      globalError = error.name === 'AbortError' || error instanceof TypeError ? 'errorNetwork' : 'errorServer'; renderErrors();
    } finally {
      clearTimeout(timeout); busy(false);
      if (fieldErrors.size) focusFieldError();
      else if (globalError) errorBox.focus();
    }
  });
  $('#new-application').addEventListener('click', () => {
    form.reset(); pending = null; savedId = null; globalError = null; fieldErrors.clear();
    form.hidden = false; success.hidden = true; reachedStep = 0; showStep(0); translate(); form.elements.fullName.focus();
  });

  $('#form-next').addEventListener('click', nextStep);
  $('#form-back').addEventListener('click', () => showStep(Math.max(0, currentStep - 1), true));
  $$('[data-form-step]').forEach(button => button.addEventListener('click', () => {
    const target = Number(button.dataset.formStep);
    if (target < currentStep) showStep(target, true);
    else if (target <= reachedStep) {
      for (let i = currentStep; i < target; i++) if (!validate(stepGroups[i])) return;
      showStep(target, true);
    }
  }));
  $('#save-job').addEventListener('click', () => {
    jobSaved = !jobSaved;
    try { if (jobSaved) localStorage.setItem('emplivo-saved-role', jobId); else localStorage.removeItem('emplivo-saved-role'); } catch {}
    renderSaved(); filterJobs();
    $('#interaction-status').textContent = t(jobSaved ? 'savedMessage' : 'removedMessage');
    if (savedOnly && !jobSaved) $('#saved-only').focus();
  });
  $('#saved-only').addEventListener('click', () => { savedOnly = !savedOnly; renderSaved(); filterJobs(); });
  $('#share-job').addEventListener('click', async () => {
    const url = new URL(location.pathname, location.origin); url.searchParams.set('lang', language); url.hash = 'kitchen-job';
    try { await navigator.clipboard.writeText(url.href); $('#interaction-status').textContent = t('linkCopied'); }
    catch { $('#interaction-status').textContent = t('copyLinkManually') + ' ' + url.href; }
  });
  $$('[data-tab]').forEach(button => {
    button.addEventListener('click', () => selectTab(Number(button.dataset.tab)));
    button.addEventListener('keydown', event => {
      let next = activeTab;
      if (event.key === 'ArrowRight') next = (activeTab + 1) % 3;
      else if (event.key === 'ArrowLeft') next = (activeTab + 2) % 3;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = 2;
      else return;
      event.preventDefault(); selectTab(next, true);
    });
  });
  $$('.view-job').forEach(link => link.addEventListener('click', () => { $('#job-details').open = true; selectTab(0); }));
  $$('.faq-item').forEach(item => item.addEventListener('toggle', () => {
    if (item.open) $$('.faq-item').forEach(other => { if (other !== item) other.open = false; });
  }));
  if ('IntersectionObserver' in window) {
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const reveal = new IntersectionObserver(entries => entries.forEach(entry => {
        if (entry.isIntersecting) { entry.target.classList.add('is-revealed'); reveal.unobserve(entry.target); }
      }), { threshold:0.08 });
      $$('[data-reveal]').forEach(element => { element.classList.add('reveal-pending'); reveal.observe(element); });
    }
    const navObserver = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) $$('#navigation a').forEach(link => {
        if (link.hash === '#' + entry.target.id) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      });
    }), { rootMargin:'-20% 0px -60% 0px' });
    ['services','vacancies','process','questions','application','contacts'].forEach(id => navObserver.observe($('#' + id)));
    navObserver.observe($('.hero'));
    let heroVisible = true, applicationVisible = false;
    const stickyObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.target.matches('.hero')) heroVisible = entry.isIntersecting;
        else applicationVisible = entry.isIntersecting;
      });
      $('#mobile-apply').hidden = heroVisible || applicationVisible;
    }, { threshold:0 });
    stickyObserver.observe($('.hero')); stickyObserver.observe($('#application'));
  }
  let scrollQueued = false;
  function reflectScroll() {
    const distance = document.documentElement.scrollHeight - innerHeight;
    $('#reading-progress').style.transform = 'scaleX(' + (distance > 0 ? Math.max(0, Math.min(1, scrollY / distance)) : 0) + ')';
    $('#back-top').hidden = scrollY < innerHeight;
    scrollQueued = false;
  }
  window.addEventListener('scroll', () => { if (!scrollQueued) { scrollQueued = true; requestAnimationFrame(reflectScroll); } }, { passive:true });
  window.addEventListener('resize', reflectScroll, { passive:true });
  reflectScroll();
  selectTab(0);

  $('#current-year').textContent = new Date().getFullYear();
  translate();
})();
