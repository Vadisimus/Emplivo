"""Build the recruitment pages and wrap the existing editorial content."""
from html import escape, unescape
import json
from pathlib import Path
import re
from urllib.parse import quote

from site_layout import LOCALES, locale_prefix, page, root_prefix, select, telegram_form

HUBS = {
    'it-digital': (('IT & Digital', 'IT & Digital', 'IT и Digital'), ('technology',)),
    'hospitality-wellness': (('Готельно-ресторанний бізнес та Wellness', 'Hospitality & Wellness', 'Гостиничный бизнес и Wellness'),
                             ('hospitality', 'beauty', 'spa', 'wellness', 'fitness')),
    'sales-service': (('Продажі та сервіс', 'Sales & Service', 'Продажи и сервис'), ('sales',)),
}
SERVICES = (
    ('recruitment', ('Рекрутмент під ключ', 'Full-cycle recruitment', 'Рекрутмент под ключ'),
     ('Узгоджуємо вимоги, шукаємо кандидатів, проводимо первинні співбесіди й супроводжуємо офер.',
      'Agree requirements, source candidates, screen and guide the offer.',
      'Согласуем требования, найдём кандидатов, проведём первичные интервью и сопроводим оффер.')),
    ('executive-search', ('Executive Search', 'Executive Search', 'Executive Search'),
     ('Будуємо карту ринку, конфіденційно спілкуємося з керівниками та оцінюємо досвід.',
      'Map the market, approach leaders confidentially and assess their experience.',
      'Составим карту рынка, конфиденциально свяжемся с руководителями и оценим их опыт.')),
    ('volume-hiring', ('Масовий найм', 'High-volume hiring', 'Массовый найм'),
     ('Погоджуємо план найму, запускаємо пілот і координуємо співбесіди та виходи поетапно.',
      'Agree hiring volumes, run a pilot and coordinate interviews and starts in stages.',
      'Согласуем объём найма, запустим пилот и организуем интервью и выходы по этапам.')),
    ('contract', ('Аутстафінг / контракт', 'Contract staffing', 'Аутстаффинг / контракт'),
     ('Перевіряємо можливу модель співпраці, погоджуємо умови та плануємо онбординг.',
      'Review available engagement models, agree terms and plan onboarding.',
      'Проверим варианты сотрудничества, согласуем условия и составим план онбординга.')),
)
ICONS = {
    'bookmark': '<path d="M6 4h12v17l-6-4-6 4V4Z"/>',
    'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'shield': '<path d="m12 3 8 3v6c0 4-3.5 7.3-8 9-4.5-1.7-8-5-8-9V6l8-3Z"/><path d="m9 12 2 2 4-4"/>',
    'pause': '<path d="M9 6v12M15 6v12"/>',
    'play': '<path d="m9 5 10 7-10 7V5Z"/>',
}


def translate(lang):
    return lambda *values: select(lang, values)


def cta(href, label, extra=''):
    return f'<a class="button{extra}" href="{escape(href, quote=True)}">{escape(label)}</a>'


def icon(name, css_class):
    return (f'<svg class="{css_class}" width="24" height="24" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


def card(job, lang, route):
    from build_vacancies import MODES, TERMS, listing_date, translator, work_modes

    t = translate(lang)
    pref = root_prefix(lang, route)
    local = pref + locale_prefix(lang)
    selected_lang = lang if job.get(lang) else 'uk'
    copy = job[selected_lang]
    details = pref + locale_prefix(selected_lang) + f'vacancies/{job["id"]}/'
    external = job['status'] == 'external'
    archived = job['status'] == 'closed'
    modes = work_modes(job)
    tags = [translator(lang)(*MODES[key]) for key in modes]
    tags.append(translator(lang)(*TERMS[job['employment']]))
    if archived:
        tags.append(t('Прийом відгуків завершено', 'Applications closed', 'Приём откликов завершён'))
    badges = ''.join(f'<span class="badge">{escape(value)}</span>' for value in tags)
    salary = job.get('salary')
    pay = copy.get('payNote') or t('Оплату не вказано', 'Pay not disclosed', 'Оплата не указана')
    salary_attributes = ''
    if salary:
        low, high = (f'{salary[key]:g}' for key in ('min', 'max'))
        amount = low if low == high else low + '–' + high
        period = t('година', 'hour', 'час') if salary['unit'] == 'HOUR' else t('місяць', 'month', 'месяц')
        taxes = t('до податків', 'gross', 'до налогов') if salary['gross'] else t('після податків', 'net', 'после налогов')
        pay = f'{amount} {salary["currency"]} / {period} · {taxes}'
        salary_attributes = f' data-currency="{salary["currency"]}" data-unit="{salary["unit"]}" data-low="{low}" data-high="{high}"'
    action = ''
    if not archived:
        action_url = job.get('applyUrl') or local + 'apply/?vacancy=' + quote(job['id'])
        action_label = (t('На сайті роботодавця', 'Apply on employer site', 'На сайте работодателя') if job.get('applyUrl')
                        else t('Відгукнутися', 'Apply', 'Откликнуться'))
        expiry_attribute = '' if external else f' data-vacancy-until="{job["validThrough"]}"'
        action = f'<div{expiry_attribute}>{cta(action_url, action_label)}</div>'
    date_label = (t('Джерело перевірено', 'Source checked', 'Источник проверен') if external
                  else t('Опубліковано', 'Posted', 'Опубликовано'))
    day = listing_date(job)
    expiry = job.get('validThrough') or ''
    return f'''<article class="job-card" data-job-id="{job['id']}" data-sector="{job['sector']}"
 data-mode="{' '.join(modes)}" data-term="{job['employment']}" data-listed="{day}" data-until="{expiry}"{salary_attributes}>
<p class="muted" data-employer>{escape(job['company'])}</p>
<h3><a href="{details}" data-job-title>{escape(copy['title'])}</a></h3>
<p data-location>{escape(copy['location'])}</p>
<div class="job-meta">{badges}</div>
<p>{escape(pay)}</p><p class="muted">{date_label} <time datetime="{day}">{day}</time></p>
<div class="job-actions">{action}<button type="button" class="button secondary job-save" data-save-job="{job['id']}" aria-pressed="false" hidden>
{icon('bookmark','job-save-icon')} {t('Зберегти','Save','Сохранить')}</button></div>
</article>'''


def vacancy_cards(jobs, lang, route):
    return ''.join(card(job, lang, route) for job in jobs)


def workplace(pref, lang):
    alt = select(lang, ('Співбесіда за робочим столом', 'Interview around a table', 'Собеседование за рабочим столом'))
    return f'''<picture><source media="(max-width:650px)" srcset="{pref}assets/workplace-hero-small.webp">
<img src="{pref}assets/workplace-hero.webp" width="1000" height="1250" fetchpriority="high" alt="{alt}"></picture>'''


def hero_metrics(lang):
    t = translate(lang)
    metrics = (
        ('reach', 'globe', t('Україна & ЄС', 'Ukraine & EU', 'Украина и ЕС'),
         t('Локальний та remote найм', 'Local and remote hiring', 'Локальный и удалённый найм')),
        ('timing', 'clock', t('12–14 днів', '12–14 days', '12–14 дней'),
         t('Сер. термін до офферу', 'Average time to offer', 'Средний срок до оффера')),
        ('guarantee', 'shield', t('90 днів гарантії', '90-day guarantee', '90 дней гарантии'),
         t('Безкоштовна заміна фахівця', 'Free candidate replacement', 'Бесплатная замена специалиста')),
    )
    notes = '\n'.join(
        f'''<li class="hero-note hero-note--{key} card-shimmer">
  <span class="hero-note-icon">{icon(symbol,'hero-note-svg')}</span>
  <strong>{escape(heading)}</strong><span class="hero-note-detail">{escape(description)}</span>
</li>'''
        for key, symbol, heading, description in metrics
    )
    return f'''<div class="hero-metrics">
  <ul class="hero-notes" role="list" aria-label="{t('Переваги підбору','Recruitment benefits','Преимущества подбора')}">
  {notes}
  </ul>
  <button class="motion-toggle" type="button" data-hero-motion-toggle aria-pressed="false"
          aria-label="{t('Пауза блиску','Pause shimmer','Пауза блика')}" hidden>
    {icon('pause','motion-pause')}{icon('play','motion-play')}
  </button>
</div>'''


def home(lang, jobs):
    t = translate(lang)
    pref = root_prefix(lang, '')
    local = pref + locale_prefix(lang)
    title = t('Робота й підбір персоналу', 'Jobs and recruitment', 'Работа и подбор персонала')
    accent = t('нового рівня.', 'at a new level.', 'нового уровня.')
    desc = t('Знайдіть вакансію за вашою спеціальністю або доручіть Emplivo пошук фахівців для команди.',
             'Find a role in your field or work with Emplivo to hire for your team.',
             'Найдите вакансию по своей специальности или поручите Emplivo подбор для вашей команды.')
    hubs = ''.join(f'<article class="panel"><h3><a href="{local}jobs/{slug}/">{escape(select(lang, value[0]))}</a></h3></article>'
                   for slug, value in HUBS.items())
    body = f'''<section class="hero hero--editorial" data-hero-motion><div class="hero-copy">
<h1 class="accent-heading">{title} <span class="editorial-italic">{accent}</span></h1><p class="reading">{desc}</p>
<div class="button-row">{cta(local + 'jobs/',t('Переглянути вакансії','Find jobs','Найти вакансии'))}
{cta(local + 'submit-vacancy/',t('Подати вакансію','Submit a vacancy','Подать вакансию'),' secondary')}</div>
<form class="hero-search" method="get" action="{local}jobs/">
<label class="field">{t('Посада або ключове слово','Job title or keyword','Должность или ключевое слово')}
<input type="search" name="q" maxlength="120"></label>
<button class="button" type="submit">{t('Шукати','Search','Поиск')}</button></form>
{hero_metrics(lang)}
</div><div class="hero-photo">{workplace(pref,lang)}</div></section>
<section class="section" id="vacancies"><h2 class="accent-heading">{t('Актуальні вакансії','Current vacancies','Актуальные вакансии')}</h2>
{listing_grid(jobs[:3],lang,'')}</section>
<section class="section"><h2 class="accent-heading">{t('Напрями підбору','Industries','Отрасли')}</h2><div class="cards">{hubs}</div></section>
<section class="section"><h2 class="accent-heading">{t('Як працює Emplivo','How Emplivo works','Как работает Emplivo')}</h2>
<div class="cards"><article class="panel"><h3>{t('Для кандидатів','For candidates','Кандидатам')}</h3>
<p>{t('У вакансії зазначаємо формат роботи, тип зайнятості та інформацію про оплату, яку надав роботодавець.',
       'Vacancies show the work arrangement, contract type and pay disclosed by the employer.',
       'В вакансии указаны формат работы, вид занятости и условия оплаты от работодателя.')}</p></article>
<article class="panel"><h3>{t('Для роботодавців','For employers','Работодателям')}</h3>
<p>{t('На старті погоджуємо профіль, етапи відбору та графік звітів.',
       'Agree the role profile, assessment stages and reporting schedule at the start.',
       'В начале согласуем профиль, этапы отбора и график отчётности.')}</p></article></div></section>
<section class="cta" id="application"><h2 class="accent-heading">{t('Залиште резюме','Send your CV','Отправьте резюме')}</h2>
<p>{t('Підготуйте резюме у форматі PDF або DOCX.','Prepare a PDF or DOCX CV.','Подготовьте резюме в PDF или DOCX.')}</p>
{cta(local + 'apply/',t('Відкрити анкету','Open the form','Открыть анкету'))}</section>'''
    return page(lang, '', f'{title} {accent}', desc, body, modules=('jobs.mjs',))


def listing_grid(jobs, lang, route):
    if jobs:
        return '<div class="cards">' + vacancy_cards(jobs, lang, route) + '</div>'
    return '<p>' + select(lang, ('Активних вакансій поки немає.', 'There are no active vacancies at the moment.',
                                'Активных вакансий пока нет.')) + '</p>'


def employers(lang):
    t = translate(lang)
    route = 'employers/'
    pref = root_prefix(lang, route)
    local = pref + locale_prefix(lang)
    title = t('Підбір персоналу для вашої команди', 'Recruitment for your team', 'Подбор персонала для вашей команды')
    desc = t('Узгодимо вимоги, етапи відбору, строки й умови підбору після брифу.',
             'Agree requirements, assessment stages, timing and recruitment terms after the brief.',
             'Согласуем требования, этапы отбора, сроки и условия подбора после получения брифа.')
    services = []
    for key, headings, summaries in SERVICES:
        services.append(f'''<article class="panel" id="{key}"><h3>{escape(select(lang,headings))}</h3>
<p>{escape(select(lang,summaries))}</p>
{cta(local + 'submit-vacancy/?service=' + key,t('Обговорити підбір','Discuss hiring','Обсудить подбор'),' secondary')}</article>''')
    faq = [
        (t('Коли отримаю перших кандидатів?', 'When will I receive the first profiles?', 'Когда я получу первых кандидатов?'),
         t('Графік першого списку кандидатів погоджуємо після затвердження вимог і бюджету.',
           'We agree the first shortlist schedule after confirming requirements and the budget.',
           'Срок первого списка кандидатов согласуем после утверждения требований и бюджета.')),
        (t('Як діє заміна?', 'How does replacement work?', 'Как действует замена?'),
         t('Умови й строк заміни погоджуємо в договорі до початку роботи.',
           'We agree the terms and period for replacement in the contract before work begins.',
           'Условия и срок замены согласуем в договоре до начала работы.')),
    ]
    body = f'''<section class="hero"><div><h1 class="accent-heading">{title}</h1><p>{desc}</p>
{cta(local + 'submit-vacancy/', t('Подати вакансію','Submit a vacancy','Подать вакансию'))}</div>{workplace(pref,lang)}</section>
<section class="section" id="services"><h2 class="accent-heading">{t('Формати співпраці','Recruitment services','Форматы сотрудничества')}</h2>
<div class="cards">{''.join(services)}</div></section>
<section class="section reading"><h2 class="accent-heading">{t('Поширені запитання','Frequently asked questions','Частые вопросы')}</h2>
{''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in faq)}</section>'''
    return page(lang, route, title, desc, body)


def intake_page(lang, kind):
    t = translate(lang)
    application = kind == 'apply'
    route = 'apply/' if application else 'submit-vacancy/'
    pref = root_prefix(lang, route)
    local = pref + locale_prefix(lang)
    title = t('Надіслати резюме','Send your CV','Отправить резюме') if application else t('Подати вакансію','Submit a vacancy','Подать вакансию')
    desc = (t('Надішліть резюме в PDF або DOCX до 5 МБ.', 'Attach a PDF or DOCX CV up to 5 MB.', 'Прикрепите резюме в PDF или DOCX до 5 МБ.')
            if application else t('Опишіть посаду, завдання та умови роботи.', 'Describe the role, responsibilities and working terms.',
                                  'Опишите должность, обязанности и условия работы.'))
    confirmation = (t('Резюме отримано','CV received','Резюме получено') if application
                    else t('Бриф отримано','Brief received','Бриф получен'))
    inputs = (f'''<input type="hidden" name="vacancyId" value="">
<label class="field">{t('Телефон','Phone','Телефон')} <input type="tel" name="phone" autocomplete="tel" maxlength="40"></label>
<label class="field">{t('Резюме PDF або DOCX','PDF or DOCX CV','Резюме PDF или DOCX')}
<input type="file" name="cv" accept=".pdf,.docx" aria-describedby="cv-hint" required></label>
<p id="cv-hint" class="muted">{t('Максимум 5 МБ.','Maximum size 5 MB.','Максимум 5 МБ.')}</p>''' if application else f'''
<label class="field">{t('Формат співпраці','Recruitment service','Формат сотрудничества')} <select name="service">
<option value="">{t('Обговоримо після брифу','Discuss after the brief','Обсудим после брифа')}</option>
{''.join(f'<option value="{key}">{select(lang, titles)}</option>' for key, titles, _ in SERVICES)}</select></label>
<label class="field">{t('Компанія','Company','Компания')} <input name="company" autocomplete="organization" maxlength="140" required></label>
<label class="field">{t('Посада','Job title','Должность')} <input name="role" maxlength="140" required></label>
<label class="field">{t('Завдання й умови роботи','Responsibilities and working terms','Задачи и условия работы')}
<textarea name="description" rows="5" maxlength="2000" required></textarea></label>''')
    fallback = (cta(telegram_form(), t('Анкета у Telegram','Apply via Telegram','Анкета в Telegram'),' secondary')
                if application and telegram_form() else cta(local + 'contact/', t('Зв’язатися з Emplivo','Contact Emplivo','Связаться с Emplivo'),' secondary'))
    body = f'''<h1 class="accent-heading">{title}</h1><p class="reading">{desc}</p>
<section class="reading">
<form class="form-shell" method="post" enctype="multipart/form-data" data-intake="{kind}" data-legacy-endpoint="{pref}api/applications.php">
<input type="hidden" name="privacyVersion" value="v1">
<label class="field">{t('Ім’я та прізвище','Full name','Имя и фамилия')} <input name="name" autocomplete="name" maxlength="120" required></label>
<label class="field">Email <input type="email" name="email" autocomplete="email" maxlength="200" required></label>
{inputs}
<label class="consent"><input name="consent" type="checkbox" value="yes" required><span>
{t('Погоджуюся на обробку даних для розгляду звернення.', 'I consent to the processing of data to review this submission.',
    'Согласен на обработку данных для рассмотрения обращения.')} <a href="{local}privacy/">{t('Політика конфіденційності','Privacy policy','Политика конфиденциальности')}</a></span></label>
<div data-challenge></div><progress hidden max="1" aria-label="{t('Завантаження заявки','Submission upload','Загрузка заявки')}"></progress>
<p data-status class="form-status" role="status"></p>
<button class="button" type="submit" disabled><span data-spin class="spinner" aria-hidden="true" hidden></span>
{t('Надіслати','Send','Отправить')}</button></form>
<div class="success" data-success hidden tabindex="-1"><h2>{confirmation}</h2>
<p>{t('Номер звернення','Reference','Номер обращения')} <strong data-reference></strong>.</p></div>
<p>{t('Інший спосіб зв’язку','Another way to get in touch','Другой способ связи')}</p>{fallback}</section>'''
    return page(lang, route, title, desc, body, modules=('intake.mjs',))


def contact(lang):
    t = translate(lang)
    pref = root_prefix(lang, 'contact/')
    local = pref + locale_prefix(lang)
    title = t('Контакти Emplivo','Contact Emplivo','Контакты Emplivo')
    desc = t('Зв’яжіться з командою підбору або залиште заявку.', 'Contact our recruitment team or submit a request.',
             'Свяжитесь с командой подбора или оставьте заявку.')
    body = f'''<section class="reading" id="request"><h1 class="accent-heading">{title}</h1><p>{desc}</p>
<p><strong>ТОВ «ЕМПЛІВО»</strong><br>ЄДРПОУ 46615773</p>
<p><a href="tel:+380677778060">+380 (67) 777 80 60</a><br><a href="mailto:hr@emplivo.com.ua">hr@emplivo.com.ua</a></p>
<div class="button-row">{cta(local+'apply/',t('Надіслати резюме','Send your CV','Отправить резюме'))}
{cta(local+'submit-vacancy/',t('Подати вакансію','Submit a vacancy','Подать вакансию'),' secondary')}</div></section>'''
    return page(lang, 'contact/', title, desc, body)


def hub(lang, slug, jobs):
    t = translate(lang)
    route = 'jobs/' + slug + '/'
    local = root_prefix(lang, route) + locale_prefix(lang)
    titles, sectors = HUBS[slug]
    title = select(lang, titles)
    desc = t('Перегляньте вакансії та матеріали у цьому напрямі.', 'Browse jobs and career resources in this field.',
             'Посмотрите вакансии и материалы по этой отрасли.')
    links = (f'<a href="{local}jobs/spa-therapist/">{t("Робота SPA-терапевта","Spa therapist careers","Работа SPA-терапевта")}</a>'
             if slug == 'hospitality-wellness' else
             f'<a href="{local}blog/">{t("Кар’єрні матеріали","Career resources","Карьерные материалы")}</a>')
    body = f'''<h1 class="accent-heading">{escape(title)}</h1><p class="reading">{desc}</p>
{listing_grid([job for job in jobs if job['sector'] in sectors],lang,route)}
<p>{links}</p>{cta(local + 'submit-vacancy/',t('Подати вакансію','Submit a vacancy','Подать вакансию'))}'''
    return page(lang, route, title, desc, body, crumbs=((t('Вакансії','Jobs','Вакансии'),'jobs/'),), modules=('jobs.mjs',))


def cases(lang):
    t = translate(lang)
    local = root_prefix(lang, 'cases/') + locale_prefix(lang)
    title = t('Формати співпраці','Recruitment services','Форматы сотрудничества')
    desc = t('Перегляньте послуги й етапи підбору.', 'Browse our services and recruitment stages.',
             'Посмотрите услуги и этапы подбора.')
    body = f'<h1 class="accent-heading">{title}</h1><p>{desc}</p>{cta(local + "employers/#services",title)}'
    return page(lang, 'cases/', title, desc, body, noindex=True)


def wrap_editorial(text, lang, route):
    title = unescape(re.search(r'<title>(.*?)</title>', text, re.S)[1]).removesuffix(' | Emplivo').removeprefix('Emplivo — ')
    main = re.search(r'<main\b[^>]*>(.*?)</main>', text, re.S)[1]
    description = re.search(r'<meta name="description" content="([^"]*)"', text)
    desc = unescape(description[1]) if description else title
    main = re.sub(r'<nav class="crumbs".*?</nav>', '', main, count=1, flags=re.S)
    main = re.sub(r'\s*<p data-saved-status\b[^>]*></p>', '', main)
    main = re.sub(r'<div class="breadcrumbs">.*?</div>', '', main, count=1, flags=re.S)
    main = re.sub(r'<section\b[^>]*>\s*<h2[^>]*>[^<]*(?:demonstration|демонстра|демо|вы́мышлен)[^<]*</h2>.*?</section>',
                  '', main, flags=re.S | re.I)
    main = re.sub(r'<p>(?:Published demonstration jobs|Демонстраційні вакансії|Демонстрационные вакансии).*?</p>', '', main, flags=re.S)
    main = re.sub(r'(href=")([^"]*)\?demo=1([^"]*)"', r'\1\2\3"', main)
    main = re.sub(r'>[^<]*(?:демонстраційн|демонстрационн|demonstration jobs)[^<]*<',
                  '>' + select(lang, ('Переглянути вакансії','Browse jobs','Все вакансии')) + '<', main, flags=re.I)
    main = re.sub(r'href="([^"]*)\?sector=([^"&#]+)#vacancies"', r'href="\1jobs/?sector=\2"', main)
    main = re.sub(r'href="([^"]*)\?interest=[^"]+#application"', r'href="\1apply/"', main)
    main = main.replace('#application"', 'apply/"')
    if route == 'privacy/' and 'id="online-intake"' not in main:
        t = translate(lang)
        main += f'''<section class="reading" id="online-intake">
<h2>{t('Онлайн-форми','Online forms','Онлайн-формы')}</h2>
<p>{t('Якщо форма працює через Cloudflare, прийняті анкети та брифи передаються в закритий чат рекрутерів у Telegram. Обмеження частоти й перевірка Turnstile захищають форми від спаму. Для захисту від дублювання зберігаємо ідентифікатор і статус доставки. Щоденне очищення видаляє записи, старші за сім днів.',
       'When a form uses Cloudflare, accepted applications and briefs are delivered to a private recruitment chat in Telegram. Rate limits and Turnstile protect the forms from spam. The reference and delivery status prevent duplicates. Daily cleanup removes records older than seven days.',
       'Когда форма работает через Cloudflare, принятые анкеты и брифы отправляются в закрытый чат рекрутеров в Telegram. Ограничения частоты и Turnstile защищают формы от спама. Номер обращения и статус доставки защищают от дублей. Ежедневная очистка удаляет записи старше семи дней.')}</p></section>'''
    schemas = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        value = json.loads(raw)
        if value.get('@type') not in ('BreadcrumbList', 'JobPosting'):
            schemas.append(value)
    trail = ()
    if '/' in route.strip('/'):
        parent = route.strip('/').split('/')[0] + '/'
        if parent in ('blog/', 'jobs/', 'salary-guide/', 'employers/'):
            labels = {'blog/': ('Блог','Blog','Блог'), 'jobs/': ('Вакансії','Jobs','Вакансии'),
                      'salary-guide/': ('Довідник оплати','Salary guide','Справочник зарплат'),
                      'employers/': ('Роботодавцям','For employers','Работодателям')}
            trail = ((select(lang, labels[parent]), parent),)
    noindex = bool(re.search(r'<meta name="robots" content="noindex', text))
    return page(lang, route, title, desc, main.strip(), schemas=schemas, noindex=noindex, crumbs=trail)


def write(root, lang, route, html):
    path = root / (locale_prefix(lang) + route + 'index.html')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
