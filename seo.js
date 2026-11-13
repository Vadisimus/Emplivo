(() => {
  'use strict';
  const en = document.documentElement.lang === 'en';
  const allowedEvents = new Set(['view_job', 'save_job', 'unsave_job', 'begin_application', 'application_submitted', 'email_request_prepared']);
  // Opt-in adapter only. No analytics vendor, storage or personal data by default.
  window.emplivoTrack = (name, properties = {}) => {
    if (!allowedEvents.has(name)) return;
    const details = { event: name };
    for (const key of ['job_id', 'role', 'request_type']) {
      if (/^[a-z0-9-]{1,80}$/.test(properties[key] || '')) details[key] = properties[key];
    }
    window.dispatchEvent(new CustomEvent('emplivo:analytics', { detail: details }));
    if (window.emplivoAnalyticsEnabled === true) {
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push(details);
    }
  };

  if ('IntersectionObserver' in window) {
    const views = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        window.emplivoTrack('view_job', { job_id: entry.target.dataset.jobId });
        views.unobserve(entry.target);
      }
    }, { threshold: 0.3 });
    document.querySelectorAll('[data-job-id]').forEach(card => views.observe(card));
  }

  const form = document.getElementById('email-request');
  if (!form) return;
  const params = new URLSearchParams(location.search);
  const topics = ['employer', 'temporary', 'permanent', 'opportunities', 'consultation'];
  if (topics.includes(params.get('type'))) form.elements.topic.value = params.get('type');
  const roles = {
    'spa-therapist': en ? 'Spa therapist' : 'SPA-терапевт',
    'personal-trainer': en ? 'Personal trainer' : 'Персональний тренер',
    'wellness-manager': en ? 'Wellness manager' : 'Wellness-менеджер'
  };
  if (roles[params.get('role')]) form.elements.role.value = roles[params.get('role')];
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const topic = form.elements.topic.selectedOptions[0].textContent;
    const message = [topic, form.elements.role.value.trim(), form.elements.location.value.trim(), '', form.elements.message.value.trim()].join('\n');
    const mailto = 'mailto:hr@emplivo.com.ua?subject=' + encodeURIComponent('Emplivo — ' + topic) + '&body=' + encodeURIComponent(message);
    document.getElementById('request-copy').value = message;
    document.getElementById('email-fallback').hidden = false;
    const openEmail = document.getElementById('email-open');
    openEmail.href = mailto;
    openEmail.hidden = false;
    document.getElementById('request-status').textContent = en
      ? 'Send the message from your email app, or copy the text below. Your request has not been sent by this website. A time is only booked after team confirmation.'
      : 'Надішліть повідомлення у поштовій програмі або скопіюйте текст нижче. Сайт не надіслав запит. Час розмови буде погоджено лише після відповіді команди.';
    window.emplivoTrack('email_request_prepared', { request_type: form.elements.topic.value });
  });
})();
