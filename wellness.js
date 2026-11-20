(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  const params = new URLSearchParams(location.search);
  const PUBLIC = document.documentElement.dataset.mode === 'public';
  const SITE_BASE = new URL('.', document.currentScript.src).pathname;
  const EMAIL_ONLY = PUBLIC && location.hostname.endsWith('.github.io');
  const routePaths = {home:'',catalog:'jobs/',employers:'employers/',about:'about/',cases:'cases/',account:'demo-account/','employer-dashboard':'demo-employer-dashboard/',privacy:'privacy/'};
  const localePrefix = (locale = language) => locale === 'uk' ? '' : locale + '/';
  const publicPath = (route, locale = language) => SITE_BASE + localePrefix(locale) + (routePaths[route] ?? '');
  const productionURL = (name, locale = language) => 'https://www.emplivo.com.ua/' + localePrefix(locale) + (routePaths[name] ?? '');
  const read = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
  const persist = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch {} };
  let language = PUBLIC ? document.documentElement.lang : params.get('lang') || read('ec-language', 'uk');
  if (!['uk','en','ru'].includes(language)) language = 'uk';
  const t = (uk,en) => language === 'uk' ? uk : language === 'ru' ? window.EMPLIVO_RU?.[en] ?? en : en;
  const vacancies = window.EMPLIVO_VACANCIES || { jobs: [], sectors: {}, modes: {}, terms: {} };
  const kyivToday = new Intl.DateTimeFormat('sv-SE', {timeZone:'Europe/Kyiv', year:'numeric', month:'2-digit', day:'2-digit'}).format();
  const realJobs = vacancies.jobs.filter(job => job.external || (job.datePosted <= kyivToday && kyivToday <= job.validThrough));
  const demos = structuredClone(window.CONCEPT_JOBS || []);
  function translateDemo(value) {
    if (!value || typeof value !== 'object') return;
    if (Object.hasOwn(value, 'uk') && Object.hasOwn(value, 'en')) {
      value.ru = Array.isArray(value.en) ? value.en.map(text => t(text, text)) : t(value.en, value.en);
      return;
    }
    Object.values(value).forEach(translateDemo);
  }
  if (language === 'ru') translateDemo(demos);
  let jobs = [...realJobs, ...demos];
  const paramsForCatalog = () => new URLSearchParams(location.hash.includes('?') ? location.hash.split('?')[1] : location.search);
  const demoCatalog = () => !PUBLIC || paramsForCatalog().get('demo') === '1';
  const catalogJobs = () => demoCatalog() ? jobs.filter(job => job.isDemo) : realJobs;
  const jobFormats = job => job.workFormats || [job.workFormat];
  const newestFirst = (a, b) => Number(Boolean(a.external)) - Number(Boolean(b.external))
    || (b.listedOn || b.datePosted).localeCompare(a.listedOn || a.datePosted) || a.id.localeCompare(b.id);
  const vacancyPath = job => SITE_BASE + localePrefix(job.languages?.includes(language) ? language : 'uk') + 'vacancies/' + job.id + '/';
  const submitVacancyPath = () => SITE_BASE + localePrefix() + 'submit-vacancy/';
  const storedSaved = read('ec-saved', []);
  let saved = new Set((Array.isArray(storedSaved) ? storedSaved : []).filter(id => jobs.some(j => j.id === id)));
  let alerts = read('ec-alerts', []);
  if (!Array.isArray(alerts)) alerts = [];
  let page = 'home', audience = 'business', caseIndex = 0, demoProfile = false;
  let application = null, brief = null, lastFocus = null;
  const pipeline = [{id:'a', name:'A',status:'new'}, {id:'b',name:'B',status:'review'}, {id:'c',name:'C',status:'new'}];
  let filters = { query:'', city:'all', sectors:[], formats:[], employment:[], min:0, management:false, saved:false, sort:'date' };
  const iconPaths = {
    arrow:'M5 12h14m-6-6 6 6-6 6', diagonal:'M6 18 18 6M6 6h12v12', search:'M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z',
    map:'M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0ZM14 10a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z',
    save:'M6 4h12v17l-6-4-6 4V4Z', users:'M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-4M13 3a4 4 0 0 1 0 8M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z',
    leaf:'M20 3C9 3 3 7 3 14a7 7 0 0 0 7 7c7 0 10-8 10-18ZM4 20l10-10', check:'M5 12l4 4L19 6', menu:'M4 6h16M4 12h16M4 18h16', x:'M6 6l12 12M6 18 18 6',
    clock:'M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z', sliders:'M4 7h6m4 0h6M4 17h10m4 0h2M10 4v6M14 14v6',
    person:'M4 21v-2a8 8 0 0 1 16 0v2M16 6a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z', upload:'M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6',
    shield:'m12 3 8 3v6c0 5-8 9-8 9S4 17 4 12V6l8-3Zm-4 9 3 3 5-6', calendar:'M4 5h16v16H4V5Zm0 5h16M8 2v6M16 2v6',
    heart:'M20 5a5 5 0 0 0-8 1 5 5 0 0 0-8-1c-6 6 8 15 8 15s14-9 8-15Z', plus:'M12 5v14M5 12h14', bell:'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM9 21h6',
    pause:'M9 5v14M15 5v14', play:'m8 5 11 7-11 7V5Z', chevron:'m8 4 8 8-8 8', briefcase:'M3 7h18v14H3V7Zm5 0V3h8v4M3 12c5 3 13 3 18 0M10 13v4h4v-4'
  };
  const icon = (name,cls='') => `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${iconPaths[name] || iconPaths.leaf}"/></svg>`;
  const photo = (tile, cls='', label='') => {
    const [x,y] = ({ spa:[0,0],fitness:[-768,0],wellness:[0,-512],management:[-768,-512] })[tile] || [0,0];
    return `<div class="photo ${cls}"><svg viewBox="0 0 768 512" preserveAspectRatio="xMidYMid slice" role="img" aria-label="${escape(label || t('Концептуальна візуалізація інтер’єру','Conceptual interior visualisation'))}"><image href="${SITE_BASE}assets/wellness-atlas.png" x="${x}" y="${y}" width="1536" height="1024" preserveAspectRatio="none"/></svg></div>`;
  };
  const money = amount => new Intl.NumberFormat(({uk:'uk-UA',en:'en-GB',ru:'ru-RU'})[language]).format(amount);
  const format = job => job.workFormat === 'shifts' ? t('Позмінно','Shift work') : job.workFormat === 'rental' ? t('Оренда','Rental') : t('Повна зайнятість','Full-time');
  const sectorName = value => vacancies.sectors[value]?.[language] || ({spa:'SPA',fitness:'Fitness',wellness:'Wellness',beauty:'Beauty'})[value] || value;
  const formatsFor = () => demoCatalog() ? [['full',t('Повна зайнятість','Full-time')],['shifts',t('Позмінно','Shift work')],['rental',t('Оренда','Rental')]] : Object.entries(vacancies.modes).map(([key,label])=>[key,label[language]]);
  const salaryCeiling = () => Math.max(65000, ...catalogJobs().map(job => Math.ceil((monthlySalary(job) || 0) / 5000) * 5000));
  const monthlySalary = job => job.salary?.currency === 'UAH' && job.salary.unit === 'MONTH' ? job.salary.max : null;
  const industryOptions = () => demoCatalog() ? ['spa','fitness','beauty','wellness'] : [...new Set(catalogJobs().map(job=>job.sector))];
  const vacancyEmpty = () => `<div class="empty-state"><h3>${t('Активних вакансій поки немає','No active vacancies yet')}</h3><p>${t('Залиште загальну анкету, щоб команда Emplivo могла зв’язатися з вами, коли з’явиться відповідна пропозиція.','Share a general application so the Emplivo team can contact you about relevant opportunities.')}</p>${button('apply-general',t('Залишити загальну анкету','Share a general application'))}</div>`;
  const route = () => { const hash = location.hash.slice(1).split('?')[0]; if (hash === 'vacancies') return 'catalog'; if (hash && Object.hasOwn(routePaths, hash)) return hash; if (!PUBLIC) return hash || 'home'; const localPath = location.pathname.startsWith(SITE_BASE) ? location.pathname.slice(SITE_BASE.length) : location.pathname.replace(/^\//,''); const path = localPath.replace(/^(en|ru)\//,'').replace(/index\.html$/,''); return Object.entries(routePaths).find(([,value]) => value === path)?.[0] || 'home'; };
  const link = (path, label, cls='') => { const [name,query] = path.split('?'); const href = PUBLIC ? publicPath(name)+(query?'?'+query:'') : '#'+path; return `<a href="${href}" class="${cls}">${label}</a>`; };
  const button = (action,label,cls='button-primary',attrs='') => `<button class="button ${cls}" data-action="${action}" ${attrs}>${label}</button>`;

  function telegramFooterLinks() {
    return (window.emplivoTelegram?.links(language) || []).map(item => `<a href="${escape(item.url)}" target="_blank" rel="noopener noreferrer" data-telegram="${item.kind}">${escape(item.label)}</a>`).join('');
  }
  function telegramApplyLink() {
    const url=window.emplivoTelegram?.botUrl('apply');
    return url ? `<a class="button button-secondary" href="${escape(url)}" target="_blank" rel="noopener noreferrer" data-telegram="bot">${t('Анкета у Telegram','Apply via Telegram')}</a>` : '';
  }

  function languageNavigation() {
    if (!PUBLIC) return `<button class="language" data-action="language">${language === 'uk' ? 'EN' : 'UA'}</button>`;
    const names = {uk:['UA','Українська'],en:['EN','English'],ru:['RU','Русский']};
    const links = Object.entries(names).map(([code,[short,name]]) => `<a class="language" lang="${code}" hreflang="${code}" aria-label="${name}"${code === language ? ' aria-current="page"' : ''} href="${escape(publicPath(page,code) + location.search + location.hash)}">${short}</a>`);
    return `<nav class="language-options" aria-label="${t('Мова сайту','Website language')}">${links.join('')}</nav>`;
  }

  function shell() {
    document.documentElement.lang = language;
    document.body.dataset.page = page;
    const ribbon = $('.concept-ribbon');
    if (ribbon) ribbon.hidden = page !== 'catalog' || !demoCatalog();
    $('#prototype-label').textContent = page === 'catalog' && demoCatalog() ? t('Демонстраційні оголошення','Demonstration listings') : t('Вакансії та підбір персоналу','Jobs and recruitment');
    $('#system-link').innerHTML = t('Матеріали для кар’єри','Career resources')+icon('diagonal'); $('#system-link').href = SITE_BASE + localePrefix() + 'blog/';
    $('#header').innerHTML = `<div class="wrap header-inner"><a class="brand" href="#home" aria-label="Emplivo — ${t('головна','home')}"><img src="${SITE_BASE}assets/mark.svg" alt="" width="35" height="35"><span class="brand-word">Emplivo</span></a><nav class="header-nav" id="header-navigation" aria-label="${t('Головна навігація','Main navigation')}">${[['catalog',t('Вакансії','Jobs')],['employers',t('Роботодавцям','For employers')],['about',t('Про агенцію','About')],['cases',t('Кейси','Stories')]].map(([p,n])=>`<a href="#${p}" ${page===p?'aria-current="page"':''}>${n}</a>`).join('')}</nav><div class="header-actions">${languageNavigation()}<a href="#account" class="icon-button account-button" aria-label="${t('Кабінет і збережені вакансії','Account and saved jobs')}">${icon('person')}<span class="count-dot" ${saved.size?'':'hidden'}>${saved.size}</span></a>${link('catalog',t('Знайти роботу','Find a job'),'button button-secondary')}${button('brief',t('Підібрати персонал','Find talent'))}<button class="icon-button mobile-menu" data-action="menu" aria-controls="header-navigation" aria-expanded="false" aria-label="${t('Відкрити меню','Open menu')}">${icon('menu')}</button></div></div>`;
    $('#footer').innerHTML = `<div class="wrap"><div class="footer-grid"><div><a class="brand" href="#home"><img src="${SITE_BASE}assets/mark.svg" alt="" width="35" height="35"><span class="brand-word">Emplivo</span></a><p>${t('Пошук роботи й підбір персоналу в різних галузях.','Job search and recruitment across industries.')}</p></div><div><h3>${t('Знайти свій напрям','Find your direction')}</h3><div class="footer-links">${link('catalog',t('Усі вакансії','All vacancies'))}<a href="${publicPath('catalog')}?demo=1">${t('Демонстраційні вакансії','Demonstration vacancies')}</a></div></div><div><h3>${t('Для вашого бізнесу','For your business')}</h3><div class="footer-links">${link('employers',t('Підбір команди','Build your team'))}<a href="${submitVacancyPath()}">${t('Подати вакансію','Submit a vacancy')}</a>${link('cases',t('Сценарії співпраці','Collaboration scenarios'))}<button data-action="brief">${t('Запит на консультацію','Request a consultation')}</button></div></div><div><h3>${t('Залишаймося на зв’язку','Stay in touch')}</h3><div class="footer-links"><a href="tel:+380677778060">+380 (67) 777 80 60</a><a href="mailto:hr@emplivo.com.ua">hr@emplivo.com.ua</a><div class="footer-social">${telegramFooterLinks()}</div></div></div></div><div class="footer-bottom"><span>© 2026 Emplivo</span>${link('privacy',t('Конфіденційність','Privacy'))}<a href="${SITE_BASE}${language === 'en' ? 'en/' : ''}salary-guide/">${t('Посібник з оплати','Compensation guide')}</a><a href="${SITE_BASE}${language === 'en' ? 'en/' : ''}blog/">${t('Кар’єрні матеріали','Career resources')}</a></div></div>`;
  }

  function jobCard(job, compact=false) {
    if (!job.isDemo) {
      const title = escape(job.title[language]);
      const initials = Array.from(job.company.split(/\s+/).map(word=>word[0]).join('')).slice(0,2).join('').toLocaleUpperCase();
      const salary = job.salary;
      const pay = salary
        ? `${money(salary.min)}${salary.min !== salary.max ? '–' + money(salary.max) : ''} ${escape(salary.currency)}`
        : escape(job.payNote?.[language] || t('Оплату не вказано','Salary not disclosed'));
      const basis = salary ? (salary.unit === 'MONTH' ? t('місяць','month') : t('година','hour')) + (salary.gross ? t(', до податків',', gross') : t(', після податків',', net')) : '';
      const modes = jobFormats(job).map(mode => vacancies.modes[mode][language]).join(' / ');
      const source = job.external ? `<span class="chip chip-sage">${t('Оголошення роботодавця','Employer listing')}</span>` : '';
      const deadline = compact && job.validThrough ? `<div class="catalog-meta"><span>${t('Прийом до','Apply by')} ${escape(job.validThrough)}</span></div>` : '';
      return `<article class="job-card" data-job="${escape(job.id)}">
        <div class="job-top"><span class="company-monogram" aria-hidden="true">${escape(initials)}</span><div class="company-meta"><strong>${escape(job.company)}</strong><span>${escape(sectorName(job.sector))}</span></div>
        <button class="icon-button save-button" data-action="save" data-id="${escape(job.id)}" aria-pressed="${saved.has(job.id)}" aria-label="${escape(t('Зберегти: ','Save: ') + job.title[language])}">${icon('save')}</button></div>
        <h3><a href="${vacancyPath(job)}">${title}</a></h3>
        <div class="job-tags"><span class="chip">${escape(job.city[language])}</span><span class="chip">${escape(modes)}</span><span class="chip">${escape(vacancies.terms[job.employment][language])}</span>${source}</div>
        <div class="job-bottom"><div class="salary"><strong>${pay}</strong><small>${basis}</small></div><a class="text-link" href="${vacancyPath(job)}">${t('Детальніше','View details')}${icon('arrow')}</a></div>
        ${deadline}</article>`;
    }
    return `<article class="job-card" data-job="${escape(job.id)}"><div class="job-top"><span class="company-monogram" aria-hidden="true">${escape(job.company[0])}</span><div class="company-meta"><strong>${escape(job.company)}</strong><span>${sectorName(job.sector)} · ${t('демонстраційний заклад','fictional employer')}</span></div><button class="icon-button save-button" data-action="save" data-id="${escape(job.id)}" aria-pressed="${saved.has(job.id)}" aria-label="${escape(t('Зберегти: ','Save: ')+job.title[language])}">${icon('save')}</button></div><h3><a href="${SITE_BASE}${language === 'en' ? 'en/' : ''}demo-jobs/${escape(job.id)}/" data-action="details" data-id="${escape(job.id)}">${escape(job.title[language])}</a></h3><div class="job-tags"><span class="chip">${icon('map')}${escape(job.city[language])}</span><span class="chip">${icon('clock')}${format(job)}</span><span class="chip chip-sage">${t('Демо','Demo')}</span>${job.urgent?`<span class="chip chip-terra">${t('Терміново · демо','Urgent · demo')}</span>`:''}</div><div class="job-bottom"><div class="salary"><strong>${money(job.salary.min)}–${money(job.salary.max)} ₴</strong><small>${t('вигадана оплата / місяць, до податків','fictional monthly gross pay')}</small></div><button class="text-link" data-action="details" data-id="${escape(job.id)}">${t('Детальніше','View details')}${icon('arrow')}</button></div>${compact?`<div class="catalog-meta"><span>${t('Приклад від','Example dated')} 12.11.2026</span><span>${job.experienceYears}+ ${t('років досвіду','years of experience')}</span></div>`:''}</article>`;
  }

  function categories() {
    const sectors = [...new Set(realJobs.map(job=>job.sector))];
    if (!sectors.length) return '';
    return `<section class="section wrap"><div class="section-head"><h2>${t('Галузі','Industries')}</h2></div><div class="button-row">${sectors.map(sector=>link('catalog?sector='+sector,escape(sectorName(sector)),'button button-secondary')).join('')}</div></section>`;
  }

  function homeJobs() {
    if (!realJobs.length) return vacancyEmpty();
    const latest = [...realJobs].sort(newestFirst).slice(0,4);
    return `<div class="job-grid" id="home-job-grid">${latest.map(job=>jobCard(job)).join('')}</div>`;
  }

  function benefits() {
    const data=audience==='business' ? [
      ['users',t('Не просто досвід. Відповідність вашому сервісу.','Beyond experience. The right fit for your service.'),t('Уточнюємо навички, очікування й культуру команди до знайомства з кандидатами.','Define skills, expectations and team culture before meeting candidates.')],
      ['shield',t('Зрозумілий процес відбору','A clear assessment process'),t('Погоджений бриф, критерії оцінки та наступні кроки — в одному процесі.','An agreed brief, assessment criteria and next steps in one process.')],
      ['leaf',t('Увага до довготривалого партнерства','Attention to lasting partnerships'),t('Умови та відповідальність обговорюються до початку пошуку.','Discuss terms and responsibilities before the search begins.')]
    ]:[
      ['heart',t('Робота, що відповідає вашим цінностям','Work that reflects your values'),t('Порівнюйте напрям, формат роботи, місто й структуру винагороди.','Compare specialisms, arrangements, locations and compensation.')],
      ['save',t('Ваш пошук у вашому ритмі','A search at your pace'),t('Зберігайте цікаві пропозиції та повертайтеся до них без реєстрації.','Save interesting opportunities and return without registering.')],
      ['users',t('Людина по той бік заявки','A person behind every application'),t('Описуйте свій досвід, ставте питання та обирайте усвідомлено.','Describe your experience, ask questions and choose thoughtfully.')]
    ];
    return data.map(([i,h,p])=>`<div class="benefit-item"><div class="benefit-icon">${icon(i)}</div><div><h3>${h}</h3><p>${p}</p></div></div>`).join('');
  }

  function caseSlide() {
    const slides=[['spa',t('Сезон, до якого<br>готова вся команда.','A season the whole<br>team is ready for.'),t('Сценарій: spa-готель готується до пікового сезону. Підхід — узгодити процедури, зміни й вимоги до навчання перед початком пошуку.','Scenario: a spa hotel prepares for peak season. Agree treatments, shifts and training requirements before starting the search.')],['wellness',t('Новий простір.<br>Спільне бачення.','A new space.<br>A shared vision.'),t('Сценарій: відкриття wellness-центру. Почати варто з ролей, відповідальності керівника та досвіду, який має отримати гість.','Scenario: launching a wellness centre. Start with roles, management responsibilities and the intended guest experience.')],['fitness',t('Енергія людей.<br>Сила спільноти.','People bring energy.<br>Community brings strength.'),t('Сценарій: fitness-студія розширює розклад. Визначаємо формати занять, кваліфікації тренерів і умови роботи з клієнтами.','Scenario: a fitness studio expands its schedule. Define class formats, trainer qualifications and client arrangements.')]];
    const [tile,title,copy]=slides[caseIndex];
    return `${photo(tile,'case-photo')}<div class="case-copy"><p class="eyebrow">${t('Ілюстративний сценарій','Illustrative scenario')} 0${caseIndex+1}</p><h3>${title}</h3><p>${copy}</p><p class="case-caption">${t('Не клієнтський кейс і не відгук. Фотографія — концептуальна візуалізація.','Not a client case study or testimonial. The image is a conceptual visualisation.')}</p><div class="case-controls"><button class="icon-button" data-action="case-prev" aria-label="${t('Попередній сценарій','Previous scenario')}"><span style="transform:rotate(180deg)">${icon('arrow')}</span></button><button class="icon-button" data-action="case-next" aria-label="${t('Наступний сценарій','Next scenario')}">${icon('arrow')}</button><span aria-live="polite">0${caseIndex+1} / 03</span></div></div>`;
  }

  function workplacePhoto(className, eager = false) {
    return `<div class="workplace-photo ${className}">
      <picture>
        <source media="(max-width: 650px)" srcset="${SITE_BASE}assets/workplace-hero-small.webp?v=d7747ae840">
        <img src="${SITE_BASE}assets/workplace-hero.webp?v=d7747ae840" width="900" height="1125" alt="${t('Колеги обговорюють роботу за столом','Colleagues discussing work around a table')}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">
      </picture>
    </div>`;
  }

  function home() {
    return `<section class="hero wrap">
      <div class="hero-grid">
        <div class="hero-copy">
          <h1>${t('Робота й підбір персоналу <em>в різних галузях</em>','Jobs and recruitment <em>across industries</em>')}</h1>
          <p>${t('Шукайте роботу за посадою, містом і форматом або зверніться до Emplivo по допомогу в підборі команди.','Search by role, location and work arrangement, or ask Emplivo to help you hire.')}</p>
          <div class="button-row">
            ${link('catalog',t('Знайти роботу','Find a job')+icon('arrow'),'button button-primary')}
            ${link('employers',t('Підібрати персонал','Recruit staff'),'button button-secondary')}
          </div>
        </div>
        ${workplacePhoto('hero-media',true)}
      </div>
      <form id="hero-search" class="hero-search" action="${publicPath('catalog')}" method="get">
        <div class="search-field">${icon('search')}<div>
          <label for="hero-query">${t('Посада','Job title')}</label>
          <input id="hero-query" name="q" type="search" placeholder="${t('Посада або ключове слово','Role or keyword')}">
        </div></div>
        <div class="search-field">${icon('map')}<div>
          <label for="hero-city">${t('Місто','City')}</label>
          <select id="hero-city" name="city"><option value="all">${t('Усі міста','All cities')}</option>${citiesOptions()}</select>
        </div></div>
        <button class="button button-primary" type="submit">${t('Знайти вакансії','Explore jobs')}${icon('arrow')}</button>
      </form>
    </section>
    <section class="section wrap jobs-section">
      <div class="section-head">
        <h2>${t('Актуальні вакансії','Current vacancies')}</h2>
        ${link('catalog',t('Усі вакансії','All vacancies')+icon('arrow'),'text-link')}
      </div>
      <div id="home-jobs">${homeJobs()}</div>
    </section>
    <section class="section wrap home-benefits">
      <div class="benefits-layout">
        <div>
          <h2>${t('Як допомагає Emplivo','How Emplivo helps')}</h2>
          <div class="tabs" role="tablist" aria-label="${t('Кому допомагаємо','Who we help')}">
            <button class="tab" id="business-tab" role="tab" tabindex="${audience==='business'?0:-1}" data-audience="business" aria-selected="${audience==='business'}" aria-controls="benefits-panel">${t('Для бізнесу','For business')}</button>
            <button class="tab" id="candidate-tab" role="tab" tabindex="${audience==='candidate'?0:-1}" data-audience="candidate" aria-selected="${audience==='candidate'}" aria-controls="benefits-panel">${t('Для фахівців','For professionals')}</button>
          </div>
        </div>
        <div class="benefit-list" id="benefits-panel" role="tabpanel" aria-labelledby="${audience==='business'?'business-tab':'candidate-tab'}">${benefits()}</div>
      </div>
    </section>
    <section class="cta-section wrap">
      <div class="cta-panel">
        <div>
          <h2>${t('Наступний крок у пошуку роботи','Your next step in finding work')}</h2>
          <p>${t('Залиште контакти й розкажіть про свій досвід. Команда Emplivo зможе зв’язатися з вами щодо відповідних пропозицій.','Share your contact details and experience so the Emplivo team can reach you about suitable opportunities.')}</p>
        </div>
        <div class="button-row">
          ${button('apply-general',t('Залишити резюме','Share your CV')+icon('arrow'),'button-light')}
          ${telegramApplyLink()}
        </div>
      </div>
    </section>`;
  }

  function citiesOptions(selected='') {
    const pool = page === 'employer-dashboard' || (page === 'catalog' && demoCatalog()) ? jobs.filter(job=>job.isDemo) : realJobs;
    const unique=[...new Set(pool.map(j=>j.city.uk))];
    return unique.map(city=>{const j=pool.find(j=>j.city.uk===city);return `<option value="${escape(city)}" ${city===selected?'selected':''}>${escape(j.city[language])}</option>`;}).join('');
  }

  function filteredJobs() {
    const normal = s=>s.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'');
    const words=normal(filters.query).trim().split(/\s+/);
    const result=catalogJobs().filter(j=>words.every(w=>normal([j.title.uk,j.title.en,j.company,j.city.uk,j.city.en].join(' ')).includes(w)) && (filters.city==='all'||j.city.uk===filters.city) && (!filters.sectors.length||filters.sectors.includes(j.sector)) && (!filters.formats.length||jobFormats(j).some(mode=>filters.formats.includes(mode))) && (!filters.employment.length||filters.employment.includes(j.employment)) && (!filters.min||(monthlySalary(j)??0)>=filters.min) && (!filters.management||j.management) && (!filters.saved||saved.has(j.id)));
    return result.sort(filters.sort==='salary'?(a,b)=>(monthlySalary(b)??-1)-(monthlySalary(a)??-1):newestFirst);
  }

  function catalog() {
    return `<div class="wrap page-head catalog-heading"><div class="breadcrumbs">${link('home',t('Головна','Home'))}<span>/</span>${t('Вакансії','Jobs')}</div><h1>${demoCatalog()?t('Демонстраційні вакансії','Demonstration vacancies'):t('Актуальні вакансії','Current vacancies')}</h1><p>${demoCatalog()?t('Вигадані оголошення для перевірки пошуку.','Fictional listings for trying the search.'):t('Шукайте роботу за посадою, містом, галуззю та форматом.','Search by role, city, industry and work arrangement.')}</p></div><div class="wrap"><button class="button button-secondary filter-mobile" data-action="filters" aria-expanded="false" aria-controls="filter-panel">${icon('sliders')}${t('Фільтри','Filters')}</button></div><div class="wrap catalog-shell" data-wireframe-label="CATALOG · FILTERS + RESULTS"><aside class="filter-panel" id="filter-panel" aria-label="${t('Фільтри вакансій','Job filters')}"><div class="filter-header"><h2>${t('Ваші критерії','Your preferences')}</h2><button class="reset" data-action="reset-filters">${t('Скинути','Reset')}</button></div><div class="field"><label for="keyword">${t('Пошук','Search')}</label><div class="input-wrap">${icon('search')}<input id="keyword" data-filter="query" value="${escape(filters.query)}" placeholder="${t('Посада, компанія…','Role, employer…')}"></div></div><fieldset class="filter-group"><legend>${t('Напрям','Specialism')}</legend>${industryOptions().map(s=>`<label class="check-row"><input type="checkbox" data-filter="sector" value="${s}" ${filters.sectors.includes(s)?'checked':''}><span>${sectorName(s)}</span><small>${catalogJobs().filter(j=>j.sector===s).length}</small></label>`).join('')}</fieldset><div class="field"><label for="filter-city">${t('Місто','City')}</label><select id="filter-city" data-filter="city"><option value="all">${t('Усі міста','All cities')}</option>${citiesOptions(filters.city)}</select></div><fieldset class="filter-group"><legend>${t('Формат роботи','Work arrangement')}</legend>${formatsFor().map(([v,n])=>`<label class="check-row"><input type="checkbox" data-filter="format" value="${v}" ${filters.formats.includes(v)?'checked':''}><span>${n}</span></label>`).join('')}</fieldset>${demoCatalog()?'':`<fieldset class="filter-group"><legend>${t('Зайнятість','Employment type')}</legend>${Object.entries(vacancies.terms).map(([key,name])=>`<label class="check-row"><input type="checkbox" data-filter="employment" value="${key}" ${filters.employment.includes(key)?'checked':''}><span>${name[language]}</span></label>`).join('')}</fieldset>`}<div class="field"><label for="salary">${t('Місячна оплата від','Monthly pay from')} <output id="salary-output">${money(filters.min)}</output> ₴</label><input id="salary" type="range" min="0" max="${salaryCeiling()}" step="5000" data-filter="min" value="${filters.min}" aria-label="${t('Мінімальний бажаний дохід','Desired minimum pay')}"><small class="muted">${t('Порівнюємо вказану місячну оплату в гривнях.','Compares disclosed monthly pay in UAH.')}</small></div><fieldset class="filter-group"><legend>${t('Додатково','More preferences')}</legend><label class="check-row"><input type="checkbox" data-filter="management" ${filters.management?'checked':''}><span>${t('Керівні посади','Management roles')}</span></label><label class="check-row"><input type="checkbox" data-filter="saved" ${filters.saved?'checked':''}><span>${t('Лише збережені','Saved only')}</span></label></fieldset></aside><section aria-label="${t('Результати пошуку','Search results')}"><div class="catalog-top"><p class="catalog-count" id="catalog-count" role="status" aria-live="polite"></p><label class="catalog-sort">${t('Сортувати:','Sort:')}<select data-filter="sort" aria-label="${t('Сортування вакансій','Job sorting')}"><option value="date" ${filters.sort==='date'?'selected':''}>${t('Спочатку нові','Newest first')}</option><option value="salary" ${filters.sort==='salary'?'selected':''}>${t('За місячною оплатою, ₴','Monthly pay, UAH')}</option></select></label></div>${demoCatalog()? `<p class="catalog-disclaimer">${t('Оголошення, роботодавці й зарплати вигадані.','The listings, employers and salaries are fictional.')}</p>` : ''}<div id="active-filters" class="active-filters"></div><div class="catalog-list" id="catalog-list"></div><div class="alert-box"><div><h3>${t('Ваше місце ще попереду?','Your next role still ahead?')}</h3><p>${t('Збережіть критерії пошуку в цьому браузері.','Save your search preferences in this browser.')}</p></div>${button('alert',icon('bell')+t('Створити сповіщення','Create alert'))}</div></section></div>`;
  }

  function updateResults() {
    if (!$('#catalog-list')) return;
    const result=filteredJobs();
    $('#catalog-count').innerHTML=`<strong>${result.length}</strong> ${(demoCatalog()?t('демо-вакансій','demo vacancies'):t('вакансій за вашими критеріями','vacancies matching your filters'))}`;
    $('#catalog-list').innerHTML=result.length?result.map(j=>jobCard(j,true)).join(''):!demoCatalog()&&!realJobs.length?vacancyEmpty():`<div class="empty-state">${icon('search')}<h3>${t('Трохи більше простору для пошуку.','Give your search a little more room.')}</h3><p>${t('За цими критеріями вакансій немає. Спробуйте змінити фільтри.','No vacancies match these filters. Try adjusting them.')}</p><div class="button-row" style="justify-content:center">${button('reset-filters',t('Скинути фільтри','Reset filters'),'button-secondary')}${button('alert',t('Зберегти пошук','Save search'))}</div></div>`;
    const tags=[...filters.sectors.map(sectorName),...filters.employment.map(key=>vacancies.terms[key][language]),filters.city==='all'?'':jobs.find(j=>j.city.uk===filters.city)?.city[language],filters.management?t('Керівники','Management'):'',filters.saved?t('Збережені','Saved'):''].filter(Boolean);
    $('#active-filters').innerHTML=tags.map(v=>`<span class="chip">${escape(v)}</span>`).join('');
    if ($('#salary-output')) $('#salary-output').textContent=money(filters.min);
  }

  function employers() {
    return `<section class="wrap employer-hero"><div class="breadcrumbs">${link('home',t('Головна','Home'))}<span>/</span>${t('Роботодавцям','For employers')}</div><div class="employer-grid"><div><p class="eyebrow">${t('Роботодавцям','For employers')}</p><h1>${t('Підбір персоналу <em>для вашої команди</em>','Recruitment <em>for your team</em>')}</h1><p>${t('Опишіть посаду, умови й завдання. Команда Emplivo перевірить вакансію та погодить із вами умови підбору.','Describe the role, terms and responsibilities. Emplivo will review the vacancy and agree recruitment terms with you.')}</p><div class="button-row">${button('brief',t('Обговорити підбір','Discuss recruitment')+icon('arrow'))}<a class="button button-secondary" href="${submitVacancyPath()}">${t('Подати вакансію','Submit a vacancy')}</a></div></div>${workplacePhoto('employer-photo',true)}</div></section><section class="section-small wrap"><div class="section-head"><div><p class="eyebrow">${t('Зрозумілий процес','A clear process')}</p><h2>${t('Від першої розмови<br>до відповідного знайомства.','From the first conversation<br>to the right introduction.')}</h2></div></div><div class="process-grid">${[['01',t('Уточнюємо потребу','Understand the need'),t('Роль, обов’язки, кваліфікація, графік і бюджет. Без нечітких очікувань.','Role, duties, qualifications, schedule and budget. Clear expectations from the start.')],['02',t('Погоджуємо відбір','Agree the assessment'),t('Критерії, формат знайомства та перевірки обговорюються до початку роботи.','Agree criteria, interviews and checks before work begins.')],['03',t('Координуємо наступний крок','Coordinate the next step'),t('Прозора комунікація, умови й організаційні питання для обох сторін.','Clear communication, terms and practical arrangements for both sides.')]].map(([n,h,p])=>`<article class="process-card"><span>${n}</span><h3>${h}</h3><p>${p}</p></article>`).join('')}</div><p class="demo-panel">${t('Вартість, доступність і умови підбору погоджуємо індивідуально.','We agree fees, availability and recruitment terms individually.')}</p></section>${categories()}`;
  }

  function account() {
    const selected=jobs.filter(j=>saved.has(j.id));
    return `<div class="wrap page-head"><p class="eyebrow">${t('Ваш простір','Your space')}</p><h1>${t('Наступний крок — ваш.','Your next move is yours.')}</h1><p>${t('Демонстрація кабінету: збереження та критерії пошуку доступні без справжнього облікового запису.','Account demonstration: saves and search preferences work without a real account.')}</p></div><section class="wrap section-small"><nav class="dashboard-tabs">${link('account',t('Для кандидата','Candidate account'))}${link('employer-dashboard',t('Для роботодавця','Employer account'))}</nav><div class="dashboard-grid"><aside class="profile-card"><div class="profile-avatar">${icon('person')}</div><h3>${t('Місце для вашої історії','Space for your story')}</h3><p>${t('Можна підставити тестовий профіль у пробний відгук. Персональні дані не зберігаються.','Use a test profile in the demo application. Personal information is not persisted.')}</p>${button('demo-profile',demoProfile?t('Демо-профіль увімкнено','Demo profile enabled'):t('Увімкнути демо-профіль','Use a demo profile'),'button-secondary')}${button('apply-general',t('Спробувати завантаження CV','Try CV upload'),'text-link')}</aside><div class="dashboard-content"><h2>${t('Збережені можливості','Saved opportunities')} <span class="muted">${selected.length}</span></h2>${selected.length?selected.map(j=>jobCard(j)).join(''):`<div class="empty-state"><h3>${t('Збережіть те, що відгукується.','Save what speaks to you.')}</h3><p>${t('Натисніть закладку на картці вакансії — вона з’явиться тут.','Select the bookmark on a job card and find it here.')}</p>${link('catalog',t('До каталогу','Browse jobs'),'button button-primary')}</div>`}<h2 style="margin-top:35px">${t('Ваші сповіщення','Your alerts')}</h2><p class="component-note">${t('Локальні приклади. Email-розсилка не підключена.','Local examples. Email delivery is not connected.')}</p>${alerts.map((a,i)=>`<div class="alert-item"><div>${escape(a.label)}<small>${t('Збережено в цьому браузері','Saved in this browser')}</small></div><button class="icon-button" data-action="delete-alert" data-index="${i}" aria-label="${t('Видалити сповіщення','Delete alert')}">${icon('x')}</button></div>`).join('')}${button('alert',icon('plus')+t('Додати сповіщення','Add alert'),'button-secondary')}</div></div></section>`;
  }

  function employerDashboard() {
    return `<div class="wrap page-head"><p class="eyebrow">${t('Кабінет роботодавця · демо','Employer dashboard · demo')}</p><h1>${t('Ваша команда.<br>Один зрозумілий простір.','Your team.<br>One clear workspace.')}</h1><p>${t('Створіть приклад оголошення та спробуйте змінити етап відбору. Зміни існують лише до перезавантаження.','Create an example advertisement and try changing a recruitment stage. Changes last until reload only.')}</p></div><section class="section-small wrap"><nav class="dashboard-tabs">${link('account',t('Для кандидата','Candidate account'))}${link('employer-dashboard',t('Для роботодавця','Employer account'))}</nav><div class="demo-panel">${t('Це не авторизований кабінет і не ATS. Усі вакансії та кандидати тут тестові; оголошення не публікуються в інтернеті.','This is not an authenticated account or ATS. All jobs and candidates are examples; advertisements are not published online.')}</div><div class="section-head"><h2>${t('Приклад вакансій','Example vacancies')}</h2>${button('new-job',icon('plus')+t('Створити демо-оголошення','Create demo advertisement'))}</div><div class="job-grid">${jobs.filter(j=>j.isDemo && (j.local || j.sector==='spa')).map(j=>jobCard(j)).join('')}</div><div class="section-head" style="margin-top:50px"><h2>${t('Етапи знайомства','Recruitment stages')}</h2><p>${t('Змінюйте статус у картці кандидата.','Change the status in each candidate card.')}</p></div><div class="pipeline">${[['new',t('Нові','New')],['review',t('Перегляд','Review')],['interview',t('Співбесіда','Interview')]].map(([status,name])=>`<div class="pipeline-col"><h3>${name} · ${pipeline.filter(p=>p.status===status).length}</h3>${pipeline.filter(p=>p.status===status).map(p=>`<article class="candidate-tile"><strong>${t('Кандидат','Candidate')} ${p.name} · ${t('демо','demo')}</strong><p>Spa therapist · ${t('тестовий профіль','test profile')}</p><select data-pipeline="${p.id}" aria-label="${t('Етап кандидата','Candidate stage')} ${p.name}">${[['new',t('Нові','New')],['review',t('Перегляд','Review')],['interview',t('Співбесіда','Interview')]].map(([v,n])=>`<option value="${v}" ${v===p.status?'selected':''}>${n}</option>`).join('')}</select></article>`).join('')}</div>`).join('')}</div></section>`;
  }

  function components() {
    const swatches=[['Milk','#F9F7F2'],['Cream','#EFECE6'],['Graphite','#262624'],['Sage','#5A7263'],['Terracotta','#C87D55'],['Sage tint','#E6ECE5']];
    return `<div class="wrap page-head"><p class="eyebrow">EMPLIVO · DESIGN SYSTEM 01</p><h1>${t('Гармонія в кожній деталі.','Harmony in every detail.')}</h1><p>${t('Жива бібліотека компонентів. Ті самі токени, стани та елементи використовуються в усьому прототипі.','A living component library. These tokens, states and components power the entire prototype.')}</p><div class="docs-links">${link('home',t('Головна','Homepage'),'text-link')}${link('catalog',t('Каталог','Catalogue'),'text-link')}<a href="docs/CONCEPT.md" class="text-link">${t('Концепція та структура','Concept and structure')}${icon('arrow')}</a><a href="docs/TECHNICAL.md" class="text-link">${t('Технічні нотатки','Technical notes')}${icon('arrow')}</a></div></div><section class="wrap section-small components-grid"><article class="content-card"><h2>${t('Палітра','Colour palette')}</h2><div class="swatches">${swatches.map(([n,c])=>`<div class="swatch"><div style="background:${c}"></div><span>${n}</span><small>${c}</small></div>`).join('')}</div><p class="component-note">${t('Теракота — акцент і маркер терміновості. Для дрібного тексту використовуємо темніший Terra ink.','Terracotta is an accent and urgency marker. Small text uses the darker Terra ink.')}</p></article><article class="content-card"><h2>${t('Типографіка','Typography')}</h2><p class="type-specimen">${t('Турбота.<br>Як професія.','Care.<br>As a profession.')}</p><p>Cormorant Garamond · 400 / 500</p><p style="margin-top:15px">Inter · 400 / 500 / 600</p><p class="component-note">${t('Локальні WOFF2 із кирилицею. Заголовки 48–94 px, текст 14–16 px, підписи 10–12 px; мобільна версія адаптується.','Local WOFF2 with Cyrillic. Headings 48–94 px, body 14–16 px, labels 10–12 px; responsive sizing on mobile.')}</p></article><article class="content-card"><h2>${t('Кнопки та стани','Buttons and states')}</h2><div class="button-row">${button('brief',t('Основна дія','Primary action'))}${link('catalog',t('Другорядна','Secondary'),'button button-secondary')}<button class="button button-primary" disabled>${t('Недоступно','Disabled')}</button></div><p class="component-note">${t('Наведіть курсор або натисніть Tab для перевірки hover і focus.','Hover or press Tab to inspect hover and focus states.')}</p><div class="button-row"><span class="chip chip-sage">Spa · ${t('Демо','Demo')}</span><span class="chip chip-terra">${t('Терміново · демо','Urgent · demo')}</span><button class="icon-button" data-action="sample-toast" aria-label="${t('Приклад сповіщення','Example notification')}">${icon('bell')}</button></div></article><article class="content-card"><h2>${t('Поля та вибір','Inputs and selection')}</h2><label class="field"><span>${t('Пошук за ключовим словом','Keyword search')}</span><div class="input-wrap">${icon('search')}<input placeholder="${t('SPA-терапевт…','Spa therapist…')}"></div></label><label class="check-row"><input type="checkbox" checked><span>${t('Лише збережені','Saved jobs only')}</span></label><label class="field"><span>${t('Місто','City')}</span><select><option>${t('Усі міста','All cities')}</option>${citiesOptions()}</select></label></article><article class="content-card component-wide"><h2>${t('Картка вакансії','Job card')}</h2><div class="job-grid">${jobs.slice(0,2).map(j=>jobCard(j)).join('')}</div></article><article class="content-card component-wide"><h2>${t('Специфікація інтерфейсу','Interface specification')}</h2><table class="spec-table"><thead><tr><th>Token</th><th>${t('Значення','Value')}</th><th>${t('Застосування','Use')}</th></tr></thead><tbody><tr><td>radius</td><td>12 / 16 / 20 / 24 px</td><td>${t('Кнопки, поля, картки, великі панелі','Buttons, inputs, cards, large panels')}</td></tr><tr><td>spacing</td><td>4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96</td><td>${t('Ритм, що масштабується між екранами','A rhythm that scales across screens')}</td></tr><tr><td>motion</td><td>180–250 / 650–700 ms</td><td>${t('Стани / поява блоків; reduced-motion підтримано','States / section reveals; reduced-motion supported')}</td></tr><tr><td>grid</td><td>1256 px max · 12 / 4 columns</td><td>${t('Десктоп / мобільна версія','Desktop / mobile')}</td></tr><tr><td>focus</td><td>3 px · #405446 · offset 5 px</td><td>${t('Клавіатурна навігація','Keyboard navigation')}</td></tr></tbody></table></article></section>`;
  }

  function editorial(kind) {
    const privacy=kind==='privacy';
    return `<div class="wrap page-head"><p class="eyebrow">${privacy?'PRIVACY BY DESIGN':t('Філософія Emplivo','The Emplivo philosophy')}</p><h1>${privacy?t('Турбота також<br>про ваші дані.','Care extends<br>to your data.'):t('Добрий сервіс<br>починається з людей.','Good service<br>begins with people.')}</h1></div><article class="wrap section-small editorial">${privacy?`<section><h2>${t('Як працюють форми','How forms work')}</h2><p>${t('Демонстраційні вакансії та роботодавці вигадані. Загальна анкета — реальний запит до Emplivo: команда отримує контакти, досвід і необов’язкове резюме для підбору роботи. Пробні відгуки залишаються локальними. У браузері зберігаються лише мова, ID вакансій і критерії пошуку.','Published demonstration jobs and employers are fictional. A general application is a real request to Emplivo: the team receives your contact details, experience and optional CV for recruitment. Test job applications remain local. Browser storage holds only language, saved job IDs and search preferences.')}</p></section><section><h2>${t('Файли та анкети','Files and applications')}</h2><p>${t('Оператор: ТОВ «ЕМПЛІВО», ЄДРПОУ 46615773. Доступ до надісланих анкет і резюме має команда Emplivo. Для запиту про доступ, виправлення, видалення даних, строки зберігання або передачу роботодавцям звертайтеся на hr@emplivo.com.ua або +380 (67) 777 80 60. Згоду можна відкликати через ці контакти.','Operator: Emplivo LLC, registration 46615773. The Emplivo team has access to submitted applications and CVs. For access, correction, deletion, retention or employer-sharing enquiries, contact hr@emplivo.com.ua or +380 (67) 777 80 60. You can withdraw consent through these contacts.')}</p></section><section><h2>Telegram</h2><p>${t('Якщо ви обираєте анкету через Telegram, бот запитує згоду, ім’я, контакт, бажану посаду, місто та досвід. Після вашого підтвердження дані отримує менеджер в особистому чаті, а не публічна група вакансій. Telegram також обробляє повідомлення за власною політикою. Чернетку можна скасувати командою /cancel; вона не продовжується після 1 години неактивності. Зашифровані записи сервера видаляються після 24 годин неактивності на найближчому щогодинному очищенні. Регламент для менеджера: видалити отриману анкету не пізніше 90 днів. Для видалення вже надісланих даних або відкликання згоди: hr@emplivo.com.ua. Файли резюме бот не приймає.','If you choose the Telegram application, the bot requests consent, your name, contact, preferred role, city and experience. Only after confirmation does it send these details to the manager’s private chat. The public jobs group does not receive applications. Telegram also processes messages under its own privacy policy. Use /cancel to discard a draft; drafts cannot resume after 1 hour of inactivity. Encrypted server records are deleted after 24 hours of inactivity at the next hourly cleanup. The manager must delete received applications within 90 days. To request deletion of submitted information or withdraw consent, contact hr@emplivo.com.ua. The bot does not accept CV files.')}</p></section>${button('clear-local',t('Очистити локальні налаштування','Clear local preferences'),'button-secondary')}`:`<section><h2>${t('Відповідність, яку відчуваєш','A fit you can feel')}</h2><p>${t('Emplivo допомагає знаходити роботу й підбирати персонал у різних галузях. Серед наших напрямів — SPA, wellness і фітнес.','Emplivo supports job seekers and employers across industries, including spa, wellness and fitness.')}</p></section><section><h2>${t('Три принципи','Three principles')}</h2><ul><li>${t('Ясність: умови, ролі та наступний крок зрозумілі обом сторонам.','Clarity: terms, responsibilities and next steps are understandable to both sides.')}</li><li>${t('Повага: увага до часу, досвіду та особистої інформації.','Respect: care for people’s time, experience and personal information.')}</li><li>${t('Відповідність: важливі навички, цінності та спосіб роботи.','Fit: skills, values and ways of working all matter.')}</li></ul></section><div class="button-row">${link('catalog',t('Переглянути вакансії','Explore jobs'),'button button-primary')}${button('brief',t('Обговорити найм','Discuss hiring'),'button-secondary')}</div>`}</article>`;
  }

  function syncHash() {
    const q=new URLSearchParams();
    if (PUBLIC && demoCatalog()) q.set('demo','1');
    if (filters.query) q.set('q',filters.query);
    if (filters.city!=='all') q.set('city',filters.city);
    if (filters.sectors.length) q.set('sector',filters.sectors.join(','));
    if (filters.formats.length) q.set('format',filters.formats.join(','));
    if (filters.employment.length) q.set('employment',filters.employment.join(','));
    if (filters.min) q.set('min',filters.min);
    if (filters.management) q.set('management','1');
    if (filters.saved) q.set('saved','1');
    if (filters.sort!=='date') q.set('sort',filters.sort);
    history.replaceState(null,'',PUBLIC ? publicPath('catalog')+(q.size?'?'+q.toString():'') : location.pathname+location.search+'#catalog'+(q.size?'?'+q.toString():''));
  }

  function parseFilters() {
    const q=paramsForCatalog();
    filters={query:q.get('q')||'',city:q.get('city')||'all',sectors:(q.get('sector')||'').split(',').filter(s=>Object.hasOwn(vacancies.sectors,s) || ['spa','fitness','wellness','beauty'].includes(s)),formats:(q.get('format')||'').split(',').filter(s=>formatsFor().some(([value])=>value===s)),employment:demoCatalog()?[]:(q.get('employment')||'').split(',').filter(k=>Object.hasOwn(vacancies.terms,k)),min:Math.min(salaryCeiling(),Math.max(0,Number(q.get('min'))||0)),management:q.get('management')==='1',saved:q.get('saved')==='1',sort:q.get('sort')==='salary'?'salary':'date'};
  }

  function render(scroll=true) {
    page=route();
    const valid=['home','catalog','employers','account','employer-dashboard','components','about','cases','privacy'];
    if (!valid.includes(page)) page='home';
    if (page==='catalog') parseFilters();
    shell();
    const pages={home,catalog,employers,account,'employer-dashboard':employerDashboard,components,about:()=>editorial('about'),privacy:()=>editorial('privacy'),cases:()=>`<section class="section wrap"><div class="section-head"><div><p class="eyebrow">${t('Від запиту до рішення','From brief to approach')}</p><h1>${t('Сценарії співпраці.','Collaboration scenarios.')}</h1></div></div><div class="demo-panel">${t('Це ілюстративні сценарії, не реальні клієнтські кейси чи відгуки. Для публікації результатів потрібні підтверджені дані та дозвіл клієнта.','These are illustrative scenarios, not actual client case studies or reviews. Publishing results requires verified evidence and client permission.')}</div><div class="case-slide" id="case-slide">${caseSlide()}</div></section>`};
    $('#main').innerHTML=pages[page]();
    document.title=`Emplivo — ${({home:t('Вакансії та підбір персоналу','Jobs and recruitment'),catalog:t('Каталог вакансій','Job catalogue'),employers:t('Роботодавцям','For employers'),account:t('Кабінет кандидата','Candidate account'),'employer-dashboard':t('Кабінет роботодавця','Employer dashboard'),components:t('Дизайн-система','Design system'),about:t('Про агенцію','About'),privacy:t('Конфіденційність','Privacy'),cases:t('Сценарії','Scenarios')})[page]} · Concept`;
    if (page==='catalog') updateResults();
    const robots = $('meta[name=robots]');
    if (page === 'catalog' && demoCatalog() && robots) robots.content = 'noindex,follow';
    if (scroll) window.scrollTo({top:0,behavior:'instant'});
    if(PUBLIC){
      $$('a[href^="#"]').forEach(a=>{const raw=a.getAttribute('href').slice(1);const [name,query]=raw.split('?');if(Object.hasOwn(routePaths,name))a.href=publicPath(name)+(query?'?'+query:'');});
      const canonical=$('link[rel=canonical]');if(canonical)canonical.href=productionURL(page);
      for (const locale of ['uk','en','ru']) {
        const alternate = $(`link[hreflang=${locale}]`);
        if (alternate) alternate.href=productionURL(page,locale);
      }
      const x=$('link[hreflang="x-default"]');if(x)x.href=productionURL(page,'uk');
      document.title=document.title.replace(' · Concept','');
      if(page==='home' && location.hash.startsWith('#application')){const job=params.get('job');startApplication(jobs.some(j=>j.isDemo&&j.id===job)?job:'');}
    }
    observe();
  }

  function observe() {
    if (!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion: reduce)').matches||document.body.classList.contains('wireframe')) { $$('.reveal').forEach(el=>el.classList.add('in-view'));return; }
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('in-view');observer.unobserve(entry.target);}}),{threshold:.06});
    $$('.reveal').forEach(el=>observer.observe(el));
  }

  function toast(text) {
    $('#toasts').innerHTML=`<div class="toast">${escape(text)}</div>`;
    clearTimeout(toast.timer);toast.timer=setTimeout(()=>{$('#toasts').innerHTML='';},4200);
  }

  function openDialog(title, body, narrow=false, remember=true) {
    const d=$('#dialog');
    if (!d.open && remember) lastFocus=document.activeElement;
    d.className=narrow?'dialog-narrow':'';
    d.innerHTML=`<div class="dialog-header"><h2 id="dialog-title">${title}</h2><button class="icon-button" data-action="close" aria-label="${t('Закрити','Close')}">${icon('x')}</button></div><div class="dialog-body">${body}</div>`;
    if(!d.open) d.showModal();
    document.body.style.overflow='hidden';
  }

  function closeDialog() { $('#dialog').close(); }
  $('#dialog').addEventListener('close',()=>{document.body.style.overflow='';application?.controller?.abort();application=null;brief=null;if(lastFocus?.isConnected)lastFocus.focus();});
  $('#dialog').addEventListener('click',event=>{if(event.target===$('#dialog')) {const r=$('#dialog').getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeDialog();}});

  function openDetails(id) {
    const j=jobs.find(j=>j.isDemo&&j.id===id);if(!j)return;
    openDialog(escape(j.title[language]),`<div class="detail-demo">${t('ДЕМОНСТРАЦІЯ. Заклад, вакансія, зарплата та умови вигадані. Це не пропозиція роботи.','DEMONSTRATION. The employer, job, salary and conditions are fictional. This is not an employment offer.')}</div><div class="job-detail-grid"><div class="detail-body"><div class="job-top"><span class="company-monogram">${escape(j.company[0])}</span><div class="company-meta"><strong>${escape(j.company)}</strong><span>${escape(j.city[language])} · ${sectorName(j.sector)}</span></div></div>${[['duties',t('Що ви робитимете','What you would do')],['requirements',t('Ваш досвід','Your experience')],['benefits',t('Що пропонує приклад','Example benefits')]].map(([key,h])=>`<section><h3>${h}</h3><ul>${j[key][language].map(v=>`<li>${escape(v)}</li>`).join('')}</ul></section>`).join('')}<section><h3>${t('Графік','Schedule')}</h3><p>${escape(j.schedule[language])}</p></section></div><aside class="detail-summary"><p class="eyebrow">${t('Приклад умов','Example conditions')}</p><div class="details-pay">${money(j.salary.min)}–${money(j.salary.max)} ₴</div><p class="component-note">${t('Вигадана місячна оплата до податків','Fictional monthly gross pay')}</p><div class="job-tags"><span class="chip">${format(j)}</span><span class="chip">${j.experienceYears}+ ${t('років','years')}</span></div>${button('apply',t('Спробувати відгук','Try applying')+icon('arrow'),'button-primary',`data-id="${escape(j.id)}"`)}${button('save',saved.has(j.id)?t('Збережено','Saved'):t('Зберегти','Save'),'button-secondary',`data-id="${escape(j.id)}"`)}<p class="component-note">${t('Заповнення форми не надсилає дані роботодавцю.','The form does not send data to an employer.')}</p></aside></div>`);
  }

  function startApplication(id='') {
    if (id && !jobs.some(job=>job.isDemo && job.id===id)) return;
    const canPrefill = demoProfile && (!PUBLIC || Boolean(id));
    application={id,step:0,submitting:false,name:canPrefill?t('Тестовий кандидат','Demo Candidate'):'',email:canPrefill?'candidate@example.test':'',phone:canPrefill?'+380000000001':'',experience:'',city:'',file:null};
    if (PUBLIC && !id && params.get('interest')) application.experience = t('Бажаний напрям: ','Preferred specialism: ') + params.get('interest').slice(0,80);
    applicationStep();
  }

  function applicationStep() {
    const a=application;if(!a)return;
    const j=jobs.find(j=>j.id===a.id);
    const real = PUBLIC && !j;
    const emailOnly = real && EMAIL_ONLY;
    const steps=[t('Контакти','Contact'),t('Досвід','Experience'),t('Перевірка','Review')];
    let body='';
    if(a.step===0) body=`<div class="form-grid"><label class="field full"><span>${t('Ім’я та прізвище','Full name')}</span><input name="name" autocomplete="name" value="${escape(a.name)}" minlength="2" maxlength="120" required></label><label class="field"><span>Email</span><input name="email" type="email" autocomplete="email" value="${escape(a.email)}" maxlength="254" required></label><label class="field"><span>${t('Телефон','Phone')}</span><input name="phone" type="tel" autocomplete="tel" value="${escape(a.phone)}" pattern="[+0-9 ]{9,32}" maxlength="32" required></label></div>`;
    if(a.step===1) body=`<label class="field"><span>${t('Бажане місто','Preferred city')}</span><select name="city"><option value="">${t('Розглядаю різні міста','Open to different cities')}</option>${citiesOptions(a.city)}</select></label><label class="field"><span>${t('Коротко про досвід','A little about your experience')}</span><textarea name="experience" maxlength="2000" placeholder="${t('Спеціалізація, навчання, доступність…','Specialisms, training, availability…')}">${escape(a.experience)}</textarea></label><label class="upload">${icon('upload')}<strong>${t('Додайте резюме, якщо зручно','Add your CV if you like')}</strong><input id="cv-upload" type="file" accept=".pdf,.docx" aria-label="${t('Резюме PDF або DOCX','PDF or DOCX CV')}"><small>${a.file?escape(a.file.name):'PDF / DOCX · ≤ 5 MB · '+t('необов’язково','optional')}</small></label><p class="form-error" id="file-error" hidden></p>`;
    if(emailOnly && a.step===1) body=body.replace(/<label class="upload">[\s\S]*?<\/label><p class="form-error" id="file-error" hidden><\/p>/, `<p class="application-notice">${t('На GitHub Pages резюме не завантажується. Прикріпіть PDF або DOCX до листа у своїй поштовій програмі.','GitHub Pages cannot receive CV uploads. Attach your PDF or DOCX to the email in your mail app.')}</p>`);
    if(a.step===2) body=`<dl>${[[t('Ім’я','Name'),a.name],['Email',a.email],[t('Телефон','Phone'),a.phone],[t('Вакансія','Role'),j?j.title[language]:t('Загальна анкета Emplivo','General Emplivo application')],[t('Резюме','CV'),a.file?.name||t('Без файлу','No file')]].map(([k,v])=>`<div class="review-row"><dt>${k}</dt><dd>${escape(v)}</dd></div>`).join('')}</dl><label class="consent-row"><input type="checkbox" name="consent" required><span>${real ? t('Погоджуюся на обробку контактів, досвіду та резюме компанією Emplivo для підбору роботи.','I consent to Emplivo processing my contact details, experience and CV for recruitment.') : t('Розумію, що це пробний відгук: дані й резюме не надсилатимуться та не зберігатимуться в базі.','I understand this is a test application: data and CV will not be sent or stored in a database.')}</span></label>`;
    openDialog(t('Ваш наступний крок','Your next step'),`<p class="dialog-subtitle">${escape(j?j.title[language]+' · '+j.company:t('Загальна анкета до Emplivo','General application to Emplivo'))}</p><ol class="steps">${steps.map((s,i)=>`<li ${i===a.step?'aria-current="step"':''}>0${i+1} ${s}</li>`).join('')}</ol><form id="application-form"><p class="${real ? 'application-notice' : 'detail-demo'}">${real ? (emailOnly ? t('Ця версія працює через email. Форма підготує лист, який ви надішлете самостійно; дані не зберігаються на GitHub Pages.','This version works by email. The form prepares a message for you to send; data is not saved on GitHub Pages.') : t('Реальне звернення: після надсилання анкета потрапить команді Emplivo. Це не відгук на вигадану вакансію.','Real enquiry: submitting sends your application to Emplivo. This is not an application for a fictional job.')) : t('Демонстраційна вакансія: анкета та файл нікуди не надсилаються.','Fictional vacancy: your application and file will not be sent.')}</p><p class="form-error" id="application-error" role="alert" tabindex="-1" hidden></p>${body}<div class="form-actions">${a.step?button('application-back',t('Назад','Back'),'button-secondary','type="button"'):`<small>${(real ? t('Ваші дані передаються лише після надсилання.','Your data is sent only on submission.') : t('Демо. Нічого не надсилається.','Demo. Nothing is submitted.'))}</small>`}<button class="button button-primary" type="submit">${a.step===2?(real?(emailOnly?t('Підготувати лист','Prepare email'):t('Надіслати загальну анкету','Submit general application')):t('Завершити демо-відгук','Complete demo application')):t('Продовжити','Continue')}${icon('arrow')}</button></div></form>`,true);
  }

  function briefStep() {
    const b=brief;if(!b)return;
    const steps=[t('Ваш простір','Your business'),t('Потреба','Your needs'),t('Контакти','Contact')];
    const body=b.step===0?`<label class="field"><span>${t('Назва компанії','Company name')}</span><input name="company" value="${escape(b.company)}" maxlength="120" required></label><label class="field"><span>${t('Напрям','Sector')}</span><select name="sector">${Object.keys(vacancies.sectors).map(v=>`<option value="${v}" ${b.sector===v?'selected':''}>${v==='management'?t('Менеджмент','Management'):sectorName(v)}</option>`).join('')}</select></label><label class="field"><span>${t('Місто / країна','City / country')}</span><input name="location" value="${escape(b.location)}" maxlength="120" required></label>`:b.step===1?`<div class="form-grid"><label class="field full"><span>${t('Кого шукаєте?','Who do you need?')}</span><input name="role" value="${escape(b.role)}" maxlength="120" required></label><label class="field"><span>${t('Кількість людей','Headcount')}</span><input type="number" name="count" min="1" max="100" value="${b.count}" required></label><label class="field"><span>${t('Коли почати?','When to start?')}</span><input name="start" value="${escape(b.start)}" placeholder="${t('Наприклад, наступного місяця','For example, next month')}" maxlength="100" required></label></div>`:`<label class="field"><span>${t('Контактне ім’я','Contact name')}</span><input name="name" value="${escape(b.name)}" minlength="2" maxlength="120" required></label><label class="field"><span>Email</span><input name="email" type="email" value="${escape(b.email)}" required maxlength="254"></label><label class="field"><span>${t('Зручний час і часовий пояс','Preferred time and time zone')}</span><input name="time" value="${escape(b.time)}" placeholder="${t('Наприклад, вівторок 11:00, Київ','For example, Tuesday 11:00, Kyiv')}" maxlength="150"></label><label class="consent-row"><input type="checkbox" required><span>${t('Розумію: форма підготує лист, який я надішлю самостійно. Час консультації потребує підтвердження команди.','I understand the form prepares an email for me to send. Consultation time requires confirmation from the team.')}</span></label>`;
    openDialog(t('Почнімо з вашого запиту','Let’s start with your brief'),`<p class="dialog-subtitle">${t('Три спокійні кроки, щоб сформулювати потребу.','Three simple steps to define what you need.')}</p><ol class="steps">${steps.map((s,i)=>`<li ${i===b.step?'aria-current="step"':''}>0${i+1} ${s}</li>`).join('')}</ol><form id="brief-form">${body}<div class="form-actions">${b.step?button('brief-back',t('Назад','Back'),'button-secondary','type="button"'):`<small>${t('Запит не створює замовлення.','An enquiry does not create an order.')}</small>`}<button class="button button-primary" type="submit">${b.step===2?t('Переглянути результат','Preview result'):t('Продовжити','Continue')}${icon('arrow')}</button></div></form>`,true);
  }

  function success(title,copy) {
    const real = PUBLIC && application && !application.id;
    application=null;brief=null;
    openDialog(real ? t('Анкету отримано','Application received') : t('Готово · демонстрація','Complete · demonstration'),`<div class="success-panel"><div class="success-symbol">${icon('check')}</div><h2>${title}</h2><p>${copy}</p>${button('close',t('Повернутися до перегляду','Continue exploring'),'button-primary')}</div>`,true);
  }

  function openAlert() {
    openDialog(t('Ваш пошук — під рукою','Keep your search close'),`<p class="dialog-subtitle">${t('Зберегти критерії у цьому браузері. Це не підписка на email.','Save preferences in this browser. This is not an email subscription.')}</p><p class="demo-panel">${escape([filters.query,...filters.sectors.map(sectorName),filters.city==='all'?t('Усі міста','All cities'):filters.city].filter(Boolean).join(' · '))}</p><form id="alert-form"><label class="field"><span>${t('Назва пошуку','Search name')}</span><input name="name" maxlength="80" value="${escape(filters.sectors.length?filters.sectors.map(sectorName).join(' / '):t('Мій wellness-пошук','My wellness search'))}" required></label><button class="button button-primary" type="submit">${t('Зберегти локально','Save locally')}${icon('check')}</button></form>`,true);
  }

  function openNewJob() {
    openDialog(t('Демо-оголошення роботодавця','Demo employer advertisement'),`<p class="dialog-subtitle">${t('Створіть вигаданий приклад лише для поточного перегляду. Нічого не публікується.','Create a fictional example for this session only. Nothing is published.')}</p><form id="new-job-form"><div class="form-grid"><label class="field full"><span>${t('Посада','Job title')}</span><input name="title" required maxlength="100"></label><label class="field full"><span>${t('Вигаданий заклад','Fictional employer')}</span><input name="company" required maxlength="80"></label><label class="field"><span>${t('Напрям','Sector')}</span><select name="sector">${['spa','fitness','wellness'].map(v=>`<option>${v}</option>`).join('')}</select></label><label class="field"><span>${t('Місто','City')}</span><select name="city">${citiesOptions()}</select></label><label class="field"><span>${t('Оплата від, ₴','Pay from, ₴')}</span><input name="min" type="number" min="1" max="999999" required></label><label class="field"><span>${t('Оплата до, ₴','Pay to, ₴')}</span><input name="max" type="number" min="1" max="999999" required></label></div><p class="form-error" id="job-error" hidden></p><button class="button button-primary" type="submit">${t('Додати демо-приклад','Add demo example')}${icon('plus')}</button></form>`,true);
  }


  async function submitGeneral(form) {
    const a=application;if(!a||a.submitting)return;
    if(EMAIL_ONLY){prepareGeneralEmail();return;}
    const fingerprint=JSON.stringify([a.name,a.phone,a.email,a.city,a.experience,a.file?.name,a.file?.size,a.file?.lastModified]);
    if(a.fingerprint!==fingerprint){a.fingerprint=fingerprint;a.submissionId=crypto.randomUUID();}
    const data=new FormData();
    for(const [key,value] of Object.entries({submissionId:a.submissionId,fullName:a.name,phone:a.phone,email:a.email,role:'',destination:'any',experience:(a.city?t('Бажане місто: ','Preferred city: ')+a.city+'\n':'')+a.experience,consent:'on'}))data.set(key,value);
    if(a.file)data.set('cv',a.file);
    const error=$('#application-error');error.hidden=true;
    a.submitting=true;const controls=[...form.elements];controls.forEach(e=>e.disabled=true);
    const controller=new AbortController();a.controller=controller;const timeout=setTimeout(()=>controller.abort(),30000);
    try{
      const response=await fetch(SITE_BASE+'api/applications.php',{method:'POST',body:data,signal:controller.signal,headers:{'Accept-Language':language}});
      const result=await response.json().catch(()=>null);
      if(application!==a)return;
      if(!response.ok||result?.ok!==true||result.id!==a.submissionId){
        if(response.status===409){a.submissionId=null;a.fingerprint=null;}
        throw new Error(response.status===413?t('Файл завеликий. Додайте PDF або DOCX до 5 МБ.','File too large. Add a PDF or DOCX up to 5 MB.'):response.status===422?t('Перевірте контакти й файл резюме. Можна повернутися до попереднього кроку.','Check your contact details and CV. You can return to the previous step.'):t('Не вдалося підтвердити збереження. Дані залишилися у формі. Спробуйте ще раз.','Could not confirm saving. Your information remains in the form. Please try again.'));
      }
      success(t('Дякуємо. Анкету збережено.','Thank you. Your application is saved.'),t('Команда Emplivo отримала ваше звернення. Номер: ','Emplivo received your application. Reference: ')+result.id);
    }catch(e){if(application!==a)return;error.textContent=e.name==='AbortError'?t('Час очікування минув. Дані залишилися у формі. Повторіть надсилання.','The request timed out. Your information remains in the form. Please retry.'):e instanceof TypeError?t('Зв’язок перервався. Дані залишилися у формі; можна повторити.','Connection interrupted. Your information remains in the form; you can retry.'):e.message;error.hidden=false;error.focus();}
    finally{clearTimeout(timeout);a.submitting=false;controls.forEach(e=>e.disabled=false);}
  }

  function prepareGeneralEmail(){
    const a=application;if(!a)return;
    const body=[t('Загальна анкета Emplivo','Emplivo general application'),a.name,a.email,a.phone,a.city,a.experience,'',t('Резюме додається до листа окремо, за бажанням.','A CV can be attached separately to this email.')].filter(Boolean).join('\n');
    const href='mailto:hr@emplivo.com.ua?subject='+encodeURIComponent('Emplivo — '+t('загальна анкета','general application'))+'&body='+encodeURIComponent(body);
    application=null;
    openDialog(t('Лист підготовлено','Your email is ready'),`<p class="dialog-subtitle">${t('Анкету ще не надіслано. Відкрийте поштову програму або скопіюйте текст у лист на hr@emplivo.com.ua. За бажанням прикріпіть резюме вручну.','Your application has not been sent. Open your email app or copy this text into a message to hr@emplivo.com.ua. Attach your CV manually if you wish.')}</p><a class="button button-primary" href="${escape(href)}" target="_blank" rel="noopener noreferrer">${t('Відкрити поштову програму','Open email app')}</a><label class="field" style="margin-top:20px"><span>${t('Текст для копіювання','Text to copy')}</span><textarea rows="10" readonly>${escape(body)}</textarea></label>`,true);
  }
  function prepareBriefEmail(){
    const b=brief;if(!b)return;
    const body=[t('Запит на підбір Emplivo','Emplivo hiring brief'),b.company,sectorName(b.sector),b.location,b.role,t('Кількість: ','Headcount: ')+b.count,t('Початок: ','Start: ')+b.start,b.name,b.email,t('Бажаний час: ','Preferred time: ')+b.time].join('\n');
    const href='mailto:hr@emplivo.com.ua?subject='+encodeURIComponent('Emplivo — '+b.company)+'&body='+encodeURIComponent(body);
    brief=null;
    openDialog(t('Запит підготовлено','Your brief is ready'),`<p class="dialog-subtitle">${t('Форма не надсилає лист автоматично. Відкрийте поштову програму або скопіюйте текст і надішліть на hr@emplivo.com.ua. Час розмови потребує підтвердження.','The form does not send automatically. Open your email app or copy the text to hr@emplivo.com.ua. A consultation time requires confirmation.')}</p><a class="button button-primary" href="${escape(href)}" target="_blank" rel="noopener noreferrer">${t('Відкрити поштову програму','Open email app')}</a><label class="field" style="margin-top:20px"><span>${t('Текст для копіювання','Text to copy')}</span><textarea rows="10" readonly>${escape(body)}</textarea></label>`,true);
  }

  document.addEventListener('click',event=>{
    const a=event.target.closest('[data-audience]');
    if(a){audience=a.dataset.audience;$$('[data-audience]').forEach(b=>{b.setAttribute('aria-selected',String(b===a));b.tabIndex=b===a?0:-1;});$('#benefits-panel').innerHTML=benefits();$('#benefits-panel').setAttribute('aria-labelledby',a.id);return;}
    const el=event.target.closest('[data-action]');if(!el)return;
    const action=el.dataset.action,id=el.dataset.id;
    if(PUBLIC && el.tagName==='A')event.preventDefault();
    if(el.tagName==='BUTTON'&&el.closest('form')&&el.type!=='submit')event.preventDefault();
    if(action==='language'){language=language==='uk'?'en':'uk';persist('ec-language',language);if(PUBLIC){history.replaceState(null,'',publicPath(page)+location.search);}render(false);}
    if(action==='menu'){const open=el.getAttribute('aria-expanded')!=='true';el.setAttribute('aria-expanded',String(open));$('#header-navigation').classList.toggle('is-open',open);}
    if(action==='motion'){const paused=document.body.classList.toggle('pause-motion');el.setAttribute('aria-pressed',String(paused));el.innerHTML=icon(paused?'play':'pause');el.setAttribute('aria-label',paused?t('Відновити рух','Resume motion'):t('Призупинити рух','Pause motion'));}
    if(action==='filters'){const open=$('#filter-panel').classList.toggle('is-open');el.setAttribute('aria-expanded',String(open));}
    if(action==='save'){
      if(saved.has(id))saved.delete(id);else saved.add(id);persist('ec-saved',[...saved]);
      $$(`.save-button[data-id="${id}"]`).forEach(b=>b.setAttribute('aria-pressed',String(saved.has(id))));
      const count=$('.count-dot');if(count){count.textContent=saved.size;count.hidden=!saved.size;}
      if(page==='catalog'&&filters.saved)updateResults();
      if(page==='account')render(false);
      if(el.closest('#dialog'))el.textContent=saved.has(id)?t('Збережено','Saved'):t('Зберегти','Save');
      toast(saved.has(id)?t('Вакансію збережено на цьому пристрої.','Job saved on this device.'):t('Вакансію прибрано зі збережених.','Job removed from saved.'));
    }
    if(action==='details')openDetails(id);
    if(action==='apply')startApplication(id);
    if(action==='apply-general')startApplication();
    if(action==='close')closeDialog();
    if(action==='brief'){brief={step:0,company:'',sector:'other',location:'',role:'',count:1,start:'',name:'',email:'',time:''};briefStep();}
    if(action==='application-back'&&application){captureApplication();application.step=Math.max(0,application.step-1);applicationStep();}
    if(action==='brief-back'&&brief){captureBrief();brief.step=Math.max(0,brief.step-1);briefStep();}
    if(action==='alert')openAlert();
    if(action==='delete-alert'){alerts.splice(Number(el.dataset.index),1);persist('ec-alerts',alerts);render(false);}
    if(action==='reset-filters'){filters={query:'',city:'all',sectors:[],formats:[],employment:[],min:0,management:false,saved:false,sort:'date'};syncHash();render(false);}
    if(action==='case-prev'||action==='case-next'){caseIndex=(caseIndex+(action==='case-next'?1:2))%3;$('#case-slide').innerHTML=caseSlide();$(`[data-action="${action}"]`).focus();}
    if(action==='demo-profile'){demoProfile=!demoProfile;render(false);toast(demoProfile?t('Тестовий профіль заповнить лише демо-анкету.','The test profile fills only the demo application.'):t('Демо-профіль вимкнено.','Demo profile disabled.'));}
    if(action==='new-job')openNewJob();
    if(action==='social')toast(language==='ru'?`Профиль ${el.dataset.network} можно подключить позже.`:t(`Профіль ${el.dataset.network} потрібно під’єднати перед запуском.`,`Connect the ${el.dataset.network} profile before launch.`));
    if(action==='sample-toast')toast(t('Приклад ненав’язливого сповіщення.','An unobtrusive notification example.'));
    if(action==='wireframe'){document.body.classList.toggle('wireframe');observe();}
    if(action==='clear-local'){['ec-saved','ec-alerts','ec-language'].forEach(k=>{try{localStorage.removeItem(k);}catch{}});saved.clear();alerts=[];demoProfile=false;toast(t('Локальні налаштування очищено.','Local preferences cleared.'));shell();}
  });

  function captureApplication() {if(!application)return;const f=$('#application-form');if(f)for(const [k,v]of new FormData(f))if(['name','email','phone','city','experience'].includes(k))application[k]=v;}
  function captureBrief(){if(!brief)return;const f=$('#brief-form');if(f)for(const [k,v]of new FormData(f))if(Object.hasOwn(brief,k)&&k!=='step')brief[k]=v;}
  document.addEventListener('submit',async event=>{
    const form=event.target;
    if(!['hero-search','application-form','brief-form','alert-form','new-job-form'].includes(form.id))return;
    event.preventDefault();if(!form.reportValidity())return;
    const data=new FormData(form);
    if(form.id==='hero-search'){const q=new URLSearchParams();if(data.get('q').trim())q.set('q',data.get('q').trim());if(data.get('city')!=='all')q.set('city',data.get('city'));if(PUBLIC)location.href=publicPath('catalog')+(q.size?'?'+q:'');else location.hash='catalog'+(q.size?'?'+q:'');}
    if(form.id==='application-form'&&application){captureApplication();if(application.step===1&&application.fileError){$('#file-error').hidden=false;return;}if(application.step<2){application.step++;applicationStep();}else{if(PUBLIC&&!application.id){await submitGeneral(form);return;}success(t('Перший крок зроблено.','You have taken the first step.'),t('Демо-відгук завершено. Ваші дані та резюме не надсилалися й не зберігалися в базі.','Demo application complete. Your details and CV were not sent or stored in a database.'));}}
    if(form.id==='brief-form'&&brief){captureBrief();if(brief.step<2){brief.step++;briefStep();}else if(PUBLIC){prepareBriefEmail();}else success(t('Запит набув форми.','Your brief has taken shape.'),t('Демонстрацію завершено. Запит не надсилався; час консультації не заброньовано.','Demonstration complete. No enquiry was sent and no consultation was booked.'));}
    if(form.id==='alert-form'){alerts.push({label:String(data.get('name')),filters:structuredClone(filters)});persist('ec-alerts',alerts);closeDialog();toast(t('Критерії збережено локально. Email не надсилатиметься.','Preferences saved locally. No email will be sent.'));if(page==='account')render(false);}
    if(form.id==='new-job-form'){
      if(Number(data.get('min'))>Number(data.get('max'))){$('#job-error').hidden=false;$('#job-error').textContent=t('Нижня межа не може перевищувати верхню.','Minimum pay cannot exceed maximum pay.');return;}
      const examples=jobs.filter(job=>job.isDemo);
      const source=examples.find(j=>j.sector===data.get('sector'))||examples[0],j=structuredClone(source);
      j.id='local-demo-'+Date.now();j.local=true;j.title={uk:String(data.get('title')),en:String(data.get('title')),ru:String(data.get('title'))};j.company=String(data.get('company'));j.salary.min=Number(data.get('min'));j.salary.max=Number(data.get('max'));j.city=structuredClone(examples.find(j=>j.city.uk===data.get('city')).city);j.urgent=false;jobs.push(j);
      closeDialog();render(false);toast(t('Демо-оголошення додано лише до цього перегляду.','Demo advertisement added to this session only.'));
    }
  });

  document.addEventListener('input',event=>{
    const el=event.target;if(!el.dataset.filter)return;
    if(el.dataset.filter==='query'){filters.query=el.value;updateResults();syncHash();}
    if(el.dataset.filter==='min'){filters.min=Number(el.value);updateResults();syncHash();}
  });
  document.addEventListener('change',event=>{
    const el=event.target,key=el.dataset.filter;
    if(key){if(['sector','format','employment'].includes(key)){const target=({sector:'sectors',format:'formats',employment:'employment'})[key];filters[target]=$$(`[data-filter="${key}"]:checked`).map(e=>e.value);}else if(['management','saved'].includes(key))filters[key]=el.checked;else if(['city','sort'].includes(key))filters[key]=el.value;updateResults();syncHash();}
    if(el.id==='cv-upload'&&application){const file=el.files[0];if(file&&(!/\.(pdf|docx)$/i.test(file.name)||file.size>5*1024*1024||file.size===0)){el.value='';application.fileError=true;$('#file-error').hidden=false;$('#file-error').textContent=t('Оберіть непорожній PDF або DOCX до 5 МБ.','Choose a non-empty PDF or DOCX up to 5 MB.');}else{application.file=file||null;application.fileError=false;$('#file-error').hidden=true;}}
    if(el.dataset.pipeline){const item=pipeline.find(p=>p.id===el.dataset.pipeline);if(item&&['new','review','interview'].includes(el.value)){item.status=el.value;render(false);toast(t('Етап демо-кандидата змінено.','Demo candidate stage updated.'));}}
  });
  document.addEventListener('keydown',event=>{
    const current=event.target.closest('[role=tab]');if(!current||!['ArrowRight','ArrowLeft','Home','End'].includes(event.key))return;
    const tabs=$$('[role=tab]',current.closest('[role=tablist]'));let index=tabs.indexOf(current);
    index=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length;
    event.preventDefault();tabs[index].click();if(tabs[index].isConnected)tabs[index].focus();
  });
  window.addEventListener('hashchange',()=>{if($('#dialog').open)closeDialog();render();});
  if(params.get('wireframe')==='1')document.body.classList.add('wireframe');
  render(false);
})();
