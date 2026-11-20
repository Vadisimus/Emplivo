(() => {
  'use strict';
  const raw = window.EMPLIVO_TELEGRAM || {};
  let groupUrl = '';
  try {
    const u = new URL(raw.groupUrl);
    if (u.protocol === 'https:' && u.hostname === 't.me' && !u.port && !u.username && !u.password && !u.search && !u.hash && /^\/(?:[A-Za-z][A-Za-z0-9_]{4,31}|\+[A-Za-z0-9_-]{16,64})\/?$/.test(u.pathname)) groupUrl = u.href.replace(/\/$/, '');
  } catch {}
  const name = String(raw.botUsername || '').replace(/^@/, '');
  const botUsername = /^[A-Za-z][A-Za-z0-9_]{4,31}$/.test(name) && /bot$/i.test(name) ? name : '';
  const botEnabled = raw.botEnabled === true && Boolean(botUsername);
  const botUrl = (payload = '') => botEnabled ? 'https://t.me/' + botUsername + (/^[A-Za-z0-9_-]{1,64}$/.test(payload) ? '?start=' + encodeURIComponent(payload) : '') : '';
  const links = language => [
    groupUrl && { url: groupUrl, label: ({en:'Telegram job group',ru:'Группа вакансий в Telegram'})[language] || 'Група вакансій у Telegram', kind: 'group' },
    botEnabled && { url: botUrl('apply'), label: ({en:'Apply with the Telegram bot',ru:'Анкета через Telegram-бота'})[language] || 'Анкета через Telegram-бота', kind: 'bot' }
  ].filter(Boolean);
  window.emplivoTelegram = Object.freeze({ groupUrl, botUsername, botEnabled, botUrl, links });

  // Retained editorial pages use a separate footer, outside the main app.
  const footer = document.querySelector('.seo-footer .shell');
  const configured = links(document.documentElement.lang);
  if (footer && configured.length && !document.querySelector('.telegram-static-links, .telegram-footer-links')) {
    const nav = document.createElement('nav');
    nav.className = 'telegram-footer-links';
    nav.setAttribute('aria-label', 'Telegram');
    for (const item of configured) {
      const a = document.createElement('a');
      a.href = item.url; a.textContent = item.label; a.target = '_blank'; a.rel = 'noopener noreferrer'; a.dataset.telegram = item.kind;
      nav.append(a);
    }
    footer.append(nav);
  }
})();
