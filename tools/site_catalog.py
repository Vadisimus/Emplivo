"""Static catalogue and saved-job page. Browser enhancements hide or reorder existing cards."""
from html import escape

from build_vacancies import MODES, SECTORS, TERMS, translator, work_modes
from site_layout import locale_prefix, page, root_prefix
from site_pages import translate, vacancy_cards


def option(value, label):
    return f'<option value="{escape(value, quote=True)}">{escape(label)}</option>'


def select_field(name, label, entries):
    return f'<label class="field">{label}<select name="{name}">' + ''.join(option(*entry) for entry in entries) + '</select></label>'


def catalog(lang, jobs):
    t = translate(lang)
    labels = translator(lang)
    route = 'jobs/'
    local = root_prefix(lang, route) + locale_prefix(lang)
    title = t('Вакансії','Jobs','Вакансии')
    all_options = [('',t('Усі','All','Все'))]
    any_pay = [('',t('Будь-яка оплата','Any pay','Любая оплата'))]
    date_order = ('date',t('Спочатку нові','Newest first','Сначала новые'))
    city_options = sorted({(job.get(lang) or job['uk'])['location'] for job in jobs})
    active_sectors = sorted({job['sector'] for job in jobs} | {'technology','hospitality','sales','spa','wellness','fitness'})
    active_modes = sorted({mode for job in jobs for mode in work_modes(job)} | MODES.keys())
    active_terms = sorted({job['employment'] for job in jobs} | TERMS.keys())
    bases = {('UAH','MONTH'), ('USD','HOUR')} | {(job['salary']['currency'],job['salary']['unit']) for job in jobs if job.get('salary')}
    pay_options = [(f'{currency}/{unit}', currency + ' / ' + (t('місяць','month','месяц') if unit == 'MONTH' else t('година','hour','час')))
                   for currency, unit in sorted(bases)]
    title_location = t('Посада або компанія','Job title or company','Должность или компания')
    label_from = t('Оплата від','Pay from','Оплата от')
    label_to = t('Оплата до','Pay to','Оплата до')
    body = f'''<h1 class="accent-heading">{title}</h1>
<p class="reading">{t('Відфільтруйте вакансії за напрямом, форматом роботи й оплатою.','Filter by industry, work arrangement and pay.','Отфильтруйте вакансии по отрасли, формату работы и оплате.')}</p>
<form class="filters" id="job-filters" method="get" hidden>
<label class="field">{title_location}<input type="search" name="q" maxlength="120"></label>
{select_field('city',t('Локація','Location','Локация'),all_options+[(city,city) for city in city_options])}
{select_field('sector',t('Напрям','Industry','Отрасль'),all_options+[(key,labels(*SECTORS[key])) for key in active_sectors])}
{select_field('mode',t('Формат','Work arrangement','Формат'),all_options+[(key,labels(*MODES[key])) for key in active_modes])}
{select_field('term',t('Зайнятість','Employment','Занятость'),all_options+[(key,labels(*TERMS[key])) for key in active_terms])}
{select_field('pay',t('Валюта й період','Currency and period','Валюта и период'),any_pay+pay_options)}
<label class="field">{label_from}<input name="min" type="number" min="0" max="100000000" step=".01" inputmode="decimal"></label>
<label class="field">{label_to}<input name="max" type="number" min="0" max="100000000" step=".01" inputmode="decimal"></label>
{select_field('sort',t('Сортування','Sort','Сортировка'),[date_order,('pay',t('Найвища оплата в обраному періоді','Highest pay in selected period','Наибольшая оплата за выбранный период'))])}
<label class="consent"><input type="checkbox" name="undisclosed" value="1">{t('Показувати вакансії без підтвердженої оплати','Include listings without confirmed pay','Показывать вакансии без подтверждённой оплаты')}</label>
<button type="reset" class="button secondary">{t('Скинути фільтри','Reset filters','Сбросить фильтры')}</button>
</form>
<p id="filter-error" role="status" data-invalid="{t('Нижня межа має бути меншою або рівною верхній.','The minimum must be at most the maximum.','Нижняя граница должна быть не выше верхней.')}"></p>
<section aria-label="{title}"><p class="result-status" data-results role="status" data-label="{t('Знайдено вакансій', 'Jobs found', 'Найдено вакансий')}"></p>
<div class="cards" data-catalog>{vacancy_cards(jobs,lang,route)}</div>
<p data-no-jobs{(' hidden' if jobs else '')}>{t('Вакансій за цими критеріями немає.', 'No jobs match these filters.', 'Вакансий по этим критериям нет.')}
<a href="{local}apply/">{t('Залишити резюме','Send your CV','Отправить резюме')}</a></p></section>'''
    return page(lang, route, title, t('Вакансії Emplivo та перевірені джерела роботодавців.',
                                    'Emplivo vacancies and reviewed employer listings.',
                                    'Вакансии Emplivo и проверенные объявления работодателей.'), body, modules=('jobs.mjs',))


def saved(lang, jobs):
    t = translate(lang)
    route = 'saved/'
    title = t('Збережені вакансії','Saved jobs','Сохранённые вакансии')
    local = root_prefix(lang, route) + locale_prefix(lang)
    desc = t('Ваш список у цьому браузері.','Your list in this browser.','Ваш список в этом браузере.')
    body = f'''<h1 class="accent-heading">{title}</h1><p>{desc}</p>
<div class="cards" data-saved-catalog hidden>{vacancy_cards(jobs,lang,route)}</div>
<p data-saved-empty hidden>{t('У каталозі немає вакансій з вашого списку.','None of your saved jobs are in the catalogue.','В каталоге нет вакансий из вашего списка.')}
<a href="{local}jobs/">{t('Переглянути вакансії','Browse jobs','Посмотреть вакансии')}</a></p>
<noscript><p>{t('Увімкніть JavaScript, щоб переглянути збережені вакансії.','Enable JavaScript to view saved jobs.','Включите JavaScript, чтобы увидеть сохранённые вакансии.')}</p></noscript>'''
    return page(lang, route, title, desc, body, noindex=True, modules=('jobs.mjs',))
