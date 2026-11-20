"""One server-rendered layout for public Emplivo pages on either hosting base."""
import hashlib
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.emplivo.com.ua/'
LOCALES = ('uk', 'en', 'ru')
LANG_NAMES = (('UA', 'Українська'), ('EN', 'English'), ('RU', 'Русский'))
NAV_ITEMS = (
    ('jobs/', ('Вакансії', 'Jobs', 'Вакансии')),
    ('employers/', ('Роботодавцям', 'For employers', 'Работодателям')),
    ('submit-vacancy/', ('Подати вакансію', 'Submit a vacancy', 'Подать вакансию')),
    ('blog/', ('Блог / Аналітика', 'Blog / Insights', 'Блог / Аналитика')),
    ('about/', ('Про нас', 'About us', 'О нас')),
    ('contact/', ('Контакти', 'Contact', 'Контакты')),
)
CURRENT = ' aria-current="page"'
IMAGE = SITE + 'assets/recruitment-preview.jpg'
STYLE_VERSION = hashlib.sha256((ROOT / 'design.css').read_bytes()).hexdigest()[:12]
TELEGRAM = json.loads(re.search(r'Object\.freeze\((\{.*?\})\);', (ROOT / 'telegram-config.js').read_text(), re.S)[1])


def locale_prefix(lang):
    return '' if lang == 'uk' else lang + '/'


def root_prefix(lang, route):
    return '../' * len([part for part in (locale_prefix(lang) + route).split('/') if part]) or './'


def select(lang, values):
    return values[LOCALES.index(lang)]


def json_html(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def telegram_form():
    return 'https://t.me/' + TELEGRAM['botUsername'] + '?start=apply' if TELEGRAM['botEnabled'] else ''


def page(lang, route, title, description, body, *, schemas=(), noindex=False, languages=LOCALES,
         crumbs=(), modules=(), marker=''):
    pref = root_prefix(lang, route)
    local = pref + locale_prefix(lang)
    canonical = SITE + locale_prefix(lang) + route
    t = lambda *values: select(lang, values)
    alt_text = t('Колеги обговорюють роботу за столом', 'Colleagues discuss work around a table', 'Коллеги обсуждают работу за столом')
    navigation = ''.join(
        f'<li><a href="{local}{path}"{CURRENT if route == path else ""}>{select(lang, labels)}</a></li>'
        for path, labels in NAV_ITEMS
    )
    switches = ''.join(
        f'<a href="{pref}{locale_prefix(code)}{route}" lang="{code}" hreflang="{code}" aria-label="{name}"'
        f'{CURRENT if lang == code else ""}>{short}</a>'
        for code, (short, name) in zip(LOCALES, LANG_NAMES) if code in languages
    )
    alternates = ''.join(f'<link rel="alternate" hreflang="{code}" href="{SITE}{locale_prefix(code)}{route}">\n'
                         for code in languages)
    if 'uk' in languages:
        alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE}{route}">\n'
    breadcrumb = ''
    if route:
        trail = [(t('Головна', 'Home', 'Главная'), ''), *crumbs, (title, route)]
        parts = [f'<li><a href="{local}{path}">{escape(label)}</a></li>' for label, path in trail[:-1]]
        parts.append(f'<li aria-current="page">{escape(title)}</li>')
        breadcrumb = f'<nav class="crumbs" aria-label="{t("Шлях сторінки", "Breadcrumbs", "Хлебные крошки")}"><ol>' + ''.join(parts) + '</ol></nav>'
        schemas = (*schemas, {
            '@context': 'https://schema.org', '@type': 'BreadcrumbList',
            'itemListElement': [{'@type': 'ListItem', 'position': index, 'name': label,
                                 'item': SITE + locale_prefix(lang) + path}
                                for index, (label, path) in enumerate(trail, 1)],
        })
    if not schemas:
        schemas = ({'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'url': canonical, 'inLanguage': lang},)
    structured = '\n'.join(f'<script type="application/ld+json">{json_html(value)}</script>' for value in schemas)
    scripts = '\n'.join(f'<script type="module" src="{pref}{name}"></script>' for name in ('navigation.mjs', *modules))
    bots = f'<a href="{escape(telegram_form(), quote=True)}">{t("Анкета у Telegram", "Apply via Telegram", "Анкета в Telegram")}</a>' if telegram_form() else ''
    community = (f'<a href="{escape(TELEGRAM["groupUrl"], quote=True)}">Telegram</a>' if TELEGRAM['groupUrl'] else '')
    description = escape(description, quote=True)
    return f'''<!doctype html>
{marker}
<html lang="{lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Emplivo</title>
<meta name="description" content="{description}"><meta name="theme-color" content="#F9F7F2">
<meta name="robots" content="{"noindex,follow" if noindex else "index,follow"}">
<link rel="canonical" href="{canonical}">
{alternates}<meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
<meta property="og:title" content="{escape(title, quote=True)}"><meta property="og:description" content="{description}">
<meta property="og:locale" content="{t('uk_UA','en_GB','ru_RU')}"><meta property="og:image" content="{IMAGE}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{alt_text}">
<link rel="icon" href="{pref}assets/mark.svg"><link rel="stylesheet" href="{pref}design.css?v={STYLE_VERSION}">
{structured}
{scripts}
</head><body>
<a class="skip" href="#main">{t('До основного вмісту','Skip to content','К основному содержанию')}</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" href="{local}"><img src="{pref}assets/mark.svg" alt="" width="36" height="36">Emplivo</a>
<nav class="navigation" aria-label="{t('Головна навігація','Main navigation','Главная навигация')}"><ul>{navigation}</ul></nav>
<div class="utilities">
<a href="{local}saved/">{t('Збережені','Saved','Сохранённые')} <span class="badge" data-saved-count>0</span></a>
<nav class="languages" aria-label="{t('Мова сайту','Website language','Язык сайта')}">{switches}</nav>
<button type="button" class="button secondary menu-toggle" data-menu-toggle aria-expanded="false" aria-controls="site-menu" aria-haspopup="dialog" hidden>{t('Меню','Menu','Меню')}</button>
</div></div></header>
<dialog id="site-menu" class="site-menu" aria-labelledby="menu-title"><div class="menu-top">
<h2 id="menu-title">{t('Меню','Menu','Меню')}</h2>
<form method="dialog"><button type="submit" class="button secondary" autofocus>{t('Закрити','Close','Закрыть')}</button></form>
</div><div data-menu-links></div></dialog>
<main class="wrap" id="main" tabindex="-1">
{breadcrumb}
{body}
<p data-saved-status role="status" data-storage-unavailable="{t('Збереження доступне до закриття сторінки.','Saved jobs are available until the page closes.','Сохранённые доступны до закрытия страницы.')}"></p>
</main>
<footer class="site-footer"><div class="wrap footer-inner">
<div><strong>ТОВ «ЕМПЛІВО»</strong><p>ЄДРПОУ 46615773</p></div>
<nav aria-label="{t('Посилання у підвалі','Footer links','Ссылки в подвале')}"><ul class="footer-links">
<li><a href="{local}jobs/">{t('Вакансії','Jobs','Вакансии')}</a></li>
<li><a href="{local}contact/">{t('Контакти','Contact','Контакты')}</a></li>
<li><a href="{local}privacy/">{t('Політика конфіденційності','Privacy policy','Политика конфиденциальности')}</a></li>
</ul></nav>
<div><a href="mailto:hr@emplivo.com.ua">hr@emplivo.com.ua</a><br><a href="tel:+380677778060">+380 (67) 777 80 60</a><br>{community} {bots}</div>
</div></footer>
</body></html>
'''
