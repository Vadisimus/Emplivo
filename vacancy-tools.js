(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const english = document.documentElement.lang === 'en';
  const russian = document.documentElement.lang === 'ru';
  const application = document.querySelector('[data-vacancy-until]');
  if (application) {
    const today = new Intl.DateTimeFormat('sv-SE', {
      timeZone: 'Europe/Kyiv', year: 'numeric', month: '2-digit', day: '2-digit',
    }).format();
    if (today > application.dataset.vacancyUntil) {
      application.hidden = true;
      document.querySelector('[data-vacancy-expired]').hidden = false;
    }
  }
  const form = byId('vacancy-brief');
  if (!form) return;
  form.hidden = false;
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const fields = [...form.elements].filter(element => element.name && element.type !== 'checkbox');
    const lines = fields.flatMap(element => {
      const value = String(data.get(element.name) || '').trim();
      return value ? [
        element.labels[0].firstChild.textContent.trim(), value, '',
      ] : [];
    });
    lines.push(russian ? 'Я уполномочен подать вакансию от имени работодателя.' : english ? 'I am authorized to submit this vacancy on behalf of the employer.'
      : 'Я уповноважений подати вакансію від імені роботодавця.');
    const body = lines.join('\n');
    const subject = (russian ? 'Бриф вакансии — ' : english ? 'Vacancy brief — ' : 'Бриф вакансії — ') + String(data.get('title')).trim();
    byId('vacancy-brief-text').value = body;
    const uri = 'mailto:hr@emplivo.com.ua?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    byId('vacancy-brief-email').href = uri.length <= 1800 ? uri : 'mailto:hr@emplivo.com.ua?subject=' + encodeURIComponent(subject);
    const note = byId('vacancy-brief-result').querySelector('p');
    if (!note.dataset.defaultText) note.dataset.defaultText = note.textContent;
    note.textContent = uri.length <= 1800 ? note.dataset.defaultText : (russian
      ? 'Скопируйте бриф ниже. Затем откройте почтовую программу, вставьте бриф в письмо и отправьте его.' : english
      ? 'Copy the brief below, then open your email app and paste it into the draft before sending.'
      : 'Скопіюйте бриф нижче. Потім відкрийте поштову програму, вставте бриф у лист і надішліть його.');
    byId('vacancy-brief-result').hidden = false;
    byId('vacancy-brief-result').querySelector('h2').focus();
  });
})();
