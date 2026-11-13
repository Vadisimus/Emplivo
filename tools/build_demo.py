#!/usr/bin/env python3
"""Generate explicitly fictional job examples; never emit JobPosting data."""
from pathlib import Path
from html import escape
import json
import re
import subprocess
import build_seo

ROOT=Path(__file__).resolve().parents[1]
JOBS=json.loads((ROOT/'content/demo-jobs.json').read_text())
assert len(JOBS)==6 and all(j['isDemo'] is True for j in JOBS)
TEXT=json.loads(subprocess.check_output(['node','-e',"global.window={};require('./translations.js');process.stdout.write(JSON.stringify(window.EMPLIVO_TEXT));"],cwd=ROOT,text=True))

def field(j,key,value):
    for lang in ('uk','en'):
        TEXT[lang][j['id']+'-'+key]=value[lang] if isinstance(value,dict) else value
    return f'data-i18n="{j["id"]}-{key}"'

def salary(j):
    s=j['salary']
    return f'{s["min"]:,}–{s["max"]:,} UAH'.replace(',',' ')

def job_cards():
    out=[]
    for j in JOBS:
        id=j['id'];title=field(j,'title',j['title']);city=field(j,'city',j['city']);emp=field(j,'employer',j['employer']['name']);sched=field(j,'schedule',j['schedule'])
        out.append(f'''<article class="job-card demo-job-card" id="{id}" data-job-id="{id}"><div class="job-toolbar"><span class="demo-badge" data-i18n="demoBadge">ДЕМО · ВИГАДАНА ВАКАНСІЯ</span><div><button class="utility-button" type="button" data-save-job="{id}" aria-pressed="false"><span class="save-label" data-i18n="saveJob">Зберегти</span></button><button class="utility-button" type="button" data-share-job="{id}"><span data-i18n="shareJob">Поділитися</span></button></div></div><div class="job-summary"><div><p class="demo-employer" {emp}>{escape(j['employer']['name']['uk'])}</p><h3 {title}>{escape(j['title']['uk'])}</h3><p class="job-subtitle"><span {city}>{escape(j['city']['uk'])}</span> · <span data-i18n="ukraine">Україна</span></p><p {sched}>{escape(j['schedule']['uk'])}</p></div><div class="job-action"><span class="salary-label" data-i18n="demoSalary">Вигадана оплата / місяць, до податків</span><strong>{salary(j)}</strong><button class="button primary apply-job" type="button" data-job="{id}" data-i18n="demoApply">Спробувати відгук · демо</button></div></div><p class="demo-card-note" data-i18n="demoCardNote">Усі дані вигадані. Це не реальна пропозиція роботи.</p><a class="text-button" data-route="demo-jobs/{id}/" href="/demo-jobs/{id}/" data-i18n="demoDetails">Усі демонстраційні умови →</a></article>''')
    return '\n'.join(out)

def build_home():
    extras={
    'uk':{'demoBadge':'ДЕМО · ВИГАДАНА ВАКАНСІЯ','demoSalary':'Вигадана оплата / місяць, до податків','demoApply':'Спробувати відгук · демо','demoCardNote':'Усі дані вигадані. Це не реальна пропозиція роботи.','demoDetails':'Усі демонстраційні умови →','demoSubmit':'Завершити пробний відгук','demoSuccessTitle':'Пробний відгук завершено','demoSuccessBody':'Це демонстрація. Анкета й резюме не надсилалися роботодавцю та не зберігалися в базі.','demoMode':'Ви тестуєте вигадану вакансію. Дані не надсилатимуться в базу. Для реального звернення оберіть «Загальна анкета».','realMode':'Загальна анкета до Emplivo: після надсилання дані буде передано команді для підбору роботи.','jobsLead':'Шість демонстраційних вакансій SPA, wellness і фітнесу. Усі роботодавці, умови та зарплати вигадані; пробні відгуки не надсилаються в базу.','specialtyLead':'Оберіть напрям: навички, умови та демонстраційні вакансії. Усі вакансії-приклади вигадані й не є реальними пропозиціями роботи.','jobTitle':'SPA-терапевт · ДЕМО','jobLocation':'Київ, Україна · демонстраційна локація','jobSubtitle':'Вигадана вакансія / Fictional job','openRecruitment':'Демонстраційна вакансія','featuredEyebrow':'ПРИКЛАД · НЕ РЕАЛЬНИЙ НАБІР','threeOpenings':'2 місця · демо','featuredNote':'Вигадані умови для ознайомлення з можливостями сайту.','viewTerms':'Переглянути демо-вакансії','yearContract':'рік · приклад','hoursDaily':'годин · приклад','daysWeekly':'днів · приклад','noExperience':'Від 1 року досвіду · демо','exploreJobs':'Демо-вакансії','applyForRole':'Спробувати відгук · демо','demoEmployers':'Демонстраційні оголошення роботодавців','spaSector':'SPA','fitnessSector':'Фітнес','wellnessSector':'Wellness'},
    'en':{'demoBadge':'DEMO · FICTIONAL JOB','demoSalary':'Fictional monthly gross pay','demoApply':'Try an application · demo','demoCardNote':'All details are invented. This is not a real employment offer.','demoDetails':'Full demonstration details →','demoSubmit':'Complete test application','demoSuccessTitle':'Test application completed','demoSuccessBody':'This is a demonstration. Your application and CV were not sent to an employer or stored in the database.','demoMode':'You are testing a fictional vacancy. Data will not be sent to the database. Choose General application to contact Emplivo about real work.','realMode':'General application to Emplivo: submission sends your information to the team for recruitment.','jobsLead':'Six demonstration spa, wellness and fitness jobs. Employers, conditions and salaries are fictional; test applications are not sent to the database.','specialtyLead':'Explore skills, conditions and demonstration jobs. All sample vacancies are fictional and are not real employment offers.','jobTitle':'Spa therapist · DEMO','jobLocation':'Kyiv, Ukraine · demonstration location','jobSubtitle':'Fictional job / Вигадана вакансія','openRecruitment':'Demonstration vacancy','featuredEyebrow':'EXAMPLE · NOT REAL RECRUITMENT','threeOpenings':'2 places · demo','featuredNote':'Fictional conditions illustrating the site features.','viewTerms':'Explore demo jobs','yearContract':'year · example','hoursDaily':'hours · example','daysWeekly':'days · example','noExperience':'1+ year of experience · demo','exploreJobs':'Demo jobs','applyForRole':'Try an application · demo','demoEmployers':'Demonstration employer advertisements','spaSector':'Spa','fitnessSector':'Fitness','wellnessSector':'Wellness'}}
    for lang in ('uk','en'):TEXT[lang].update(extras[lang])
    cards=job_cards()
    (ROOT/'translations.js').write_text('window.EMPLIVO_TEXT = '+json.dumps(TEXT,ensure_ascii=False,indent=2)+';\n')
    (ROOT/'jobs-data.js').write_text('window.EMPLIVO_JOBS = '+json.dumps(JOBS,ensure_ascii=False,indent=2)+';\n')
    h=(ROOT/'index.html').read_text()
    if 'id="jobs-list"' in h:
        h=re.sub(r'<!-- DEMO JOBS START -->.*?<!-- DEMO JOBS END -->','<!-- DEMO JOBS START --><div id="jobs-list">'+cards+'</div><!-- DEMO JOBS END -->',h,flags=re.S)
    else:
        start=h.index('<article class="job-card"')
        end=h.index('<div class="empty-state"',start)
        h=h[:start]+'<!-- DEMO JOBS START --><div id="jobs-list">'+cards+'</div><!-- DEMO JOBS END -->\n'+h[end:]
    if 'id="interaction-status"' not in h:
        h=h.replace('<!-- DEMO JOBS START -->','<p id="interaction-status" role="status" aria-live="polite"></p><!-- DEMO JOBS START -->')
    h=re.sub(r'(<select id="sector-filter">).*?(</select>)',lambda m:m[1]+''.join(f'<option value="{v}" data-i18n="{k}">{TEXT["uk"][k]}</option>' for v,k in [('all','allSectors'),('spa','spaSector'),('fitness','fitnessSector'),('wellness','wellnessSector')])+m[2],h,flags=re.S)
    h=re.sub(r'(<select id="role-select" name="role">).*?(</select>)',lambda m:m[1]+'<option data-i18n="generalApplication" value="">'+TEXT['uk']['generalApplication']+'</option>'+''.join(f'<option value="{j["id"]}" data-i18n="{j["id"]}-title">{escape(j["title"]["uk"])}</option>' for j in JOBS)+m[2],h,flags=re.S)
    h=h.replace('<span aria-hidden="true">↗</span>','<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 18 18 6M6 6h12v12"/></svg>')
    if 'id="application-mode"' not in h:
        h=h.replace('<fieldset class="form-step" data-step="0"','<p class="application-mode" id="application-mode" role="status"></p><fieldset class="form-step" data-step="0"',1)
    h=h.replace('<button class="button primary apply-job" data-i18n="applyForRole"','<button class="button primary apply-job" data-job="demo-spa-01" data-i18n="applyForRole"')
    h=h.replace('href="#vacancies"><span data-i18n="viewTerms"','href="#demo-spa-01"><span data-i18n="viewTerms"')
    if 'src="/jobs-data.js' not in h:
        h=h.replace('<script defer="" src="app.js','<script defer src="/jobs-data.js?v=20261112"></script>\n<script defer="" src="app.js')
    # Translate every simple static label from the current dictionary, including the former kitchen feature.
    pattern=r'<(?P<tag>[a-zA-Z0-9]+)(?P<attrs>[^>]*\bdata-i18n="(?P<key>[^"]+)"[^>]*)>(?P<text>.*?)</(?P=tag)>'
    h=re.sub(pattern,lambda m:'<'+m['tag']+m['attrs']+'>'+escape(TEXT['uk'].get(m['key'],m['text']))+'</'+m['tag']+'>',h,flags=re.S)
    if 'data-route="demo-employers/"' not in h:
        h=h.replace('<div class="seo-resource-links">','<div class="seo-resource-links"><a data-route="demo-employers/" href="/demo-employers/" data-i18n="demoEmployers">Демонстраційні оголошення роботодавців</a>')
    (ROOT/'index.html').write_text(h)

def build_details():
    for lang in ('uk','en'):
        en=lang=='en';t=lambda uk,en_:en_ if en else uk
        for j in JOBS:
            contact=j['employer']
            blocks=[
             (t('Вигаданий роботодавець','Fictional employer'),contact['name'][lang]+' — '+contact['description'][lang]),
             (t('Локація','Location'),j['address'][lang]),
             (t('Зарплата та формат','Pay and arrangement'),salary(j)+' / '+t('місяць, до податків. Умовна базова оплата; не ринкові дані. ','month, gross. Fictional base pay; not market data. ')+('PART_TIME' if j['employmentType']=='PART_TIME' else 'FULL_TIME')),
             (t('Графік, досвід та кількість місць','Schedule, experience and places'),j['schedule'][lang]+f' · {j["experienceYears"]} '+t('років досвіду','years of experience')+f' · {j["openings"]} '+t('місця','places')),
             (t('Обов’язки','Responsibilities'),' • '.join(j['duties'][lang])),
             (t('Вимоги','Requirements'),' • '.join(j['requirements'][lang])),
             (t('Демонстраційні переваги','Demonstration benefits'),' • '.join(j['benefits'][lang])),
             (t('Проживання','Accommodation'),j['accommodation'][lang]),
             (t('Дати прикладу','Example dates'),j['datePosted']+' → '+j['validThrough']),
             (t('Тестові контакти — не для зв’язку','Test contacts — not contact channels'),contact['email']+' · '+contact['phone']+' · '+contact['website']),
             (t('Пробний відгук','Test application'),j['applicationProcess'][lang])]
            page={'path':'demo-jobs/'+j['id']+'/','titles':(j['title']['uk']+' · ДЕМО',j['title']['en']+' · DEMO'),'leads':(j['description']['uk'],j['description']['en']),'blocks':[(a,a,b,b) for a,b in blocks],'links':[('#application?job='+j['id'],'Спробувати відгук · демо','Try an application · demo'),('demo-employers/','Вигадані оголошення роботодавців','Fictional employer advertisements'),('jobs/'+j['role']+'/','Професійний напрям','Role guide')],'article':False}
            html=build_seo.render(page,lang).replace('</head>','<meta name="robots" content="noindex,follow"></head>')
            out=ROOT/('en' if en else '')/page['path']/'index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(html)
        blocks=[];links=[]
        for sector in ('spa','fitness','wellness'):
            group=[j for j in JOBS if j['sector']==sector];c=group[0]['employer']
            b=c['description'][lang]+' '+t('Приклад запиту: шукаємо фахівців для таких вигаданих ролей: ','Example brief: seeking candidates for the following fictional roles: ')+', '.join(j['title'][lang] for j in group)+'. '+t('Тестові контакти, не для зв’язку: ','Test contacts, not contact channels: ')+c['email']+' · '+c['phone']+' · '+c['website']
            blocks.append((c['name'][lang],c['name'][lang],b,b))
            links.extend(('demo-jobs/'+j['id']+'/',j['title']['uk']+' · ДЕМО',j['title']['en']+' · DEMO') for j in group)
        page={'path':'demo-employers/','titles':('Вигадані оголошення роботодавців · ДЕМО','Fictional employer advertisements · DEMO'),'leads':('Три вигадані роботодавці та шість повністю заповнених прикладів вакансій. Це не клієнти Emplivo і не справжні пропозиції роботи.','Three fictional employers and six complete example vacancies. These are not Emplivo clients or real employment offers.'),'blocks':blocks,'links':links,'article':False}
        out=ROOT/('en' if en else '')/'demo-employers/index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(build_seo.render(page,lang).replace('</head>','<meta name="robots" content="noindex,follow"></head>'))
    print('Built 12 noindex demo job pages and 2 noindex fictional employer pages')

if __name__=='__main__':
    build_home()
    for page in build_seo.PAGES:
        for role,sector in [('spa-therapist','spa'),('personal-trainer','fitness'),('wellness-manager','wellness')]:
            if page['path']=='jobs/'+role+'/':
                page['links']=[('#vacancies?sector='+sector,'Приклади вакансій цього напряму · ДЕМО','Example jobs in this category · DEMO')]+list(page['links'])
    build_seo.build()
    build_details()
