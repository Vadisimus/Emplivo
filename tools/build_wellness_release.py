#!/usr/bin/env python3
"""Integrate the approved wellness design with existing public pages and PHP API."""
from pathlib import Path
import shutil
import re
import json

CONCEPT=Path('/workspace/emplivo-concept')
STAGE=Path('/workspace/releases/Emplivo_Wellness_2026-11-12/www')
STAGE.mkdir(parents=True,exist_ok=True)
shutil.copytree(CONCEPT/'assets',STAGE/'assets',dirs_exist_ok=True)
shutil.copy2(CONCEPT/'styles.css',STAGE/'wellness.css')
shutil.copy2(CONCEPT/'data.js',STAGE/'wellness-data.js')

app=(CONCEPT/'app.js').read_text()
app=app.replace("const params = new URLSearchParams(location.search);", "const params = new URLSearchParams(location.search);\n  const PUBLIC = document.documentElement.dataset.mode === 'public';\n  const routePaths = {home:'',catalog:'jobs/',employers:'employers/',about:'about/',cases:'cases/',account:'demo-account/','employer-dashboard':'demo-employer-dashboard/',privacy:'privacy/'};\n  const publicPath = (route, locale = language) => '/' + (locale === 'en' ? 'en/' : '') + (routePaths[route] ?? '');")
app=app.replace("let language = params.get('lang') === 'en' ? 'en' : read('ec-language', 'uk');", "let language = PUBLIC ? (location.pathname.startsWith('/en/') ? 'en' : document.documentElement.lang) : params.get('lang') === 'en' ? 'en' : read('ec-language', 'uk');")
app=app.replace("const route = () => (location.hash.slice(1).split('?')[0] || 'home');", "const route = () => { const hash = location.hash.slice(1).split('?')[0]; if (hash === 'vacancies') return 'catalog'; if (hash && Object.hasOwn(routePaths, hash)) return hash; if (!PUBLIC) return hash || 'home'; const path = location.pathname.replace(/^\\/en\\//,'/').replace(/^\\//,'').replace(/index\\.html$/,''); return Object.entries(routePaths).find(([,value]) => value === path)?.[0] || 'home'; };")
app=app.replace("const link = (path, label, cls='') => `<a href=\"#${path}\" class=\"${cls}\">${label}</a>`;", "const link = (path, label, cls='') => { const [name,query] = path.split('?'); const href = PUBLIC ? publicPath(name)+(query?'?'+query:'') : '#'+path; return `<a href=\"${href}\" class=\"${cls}\">${label}</a>`; };")
app=app.replace("t('Інтерактивна концепція · усі вакансії демонстраційні','Interactive concept · all vacancies are fictional')", "t('Вакансії-приклади · усі заклади та умови вигадані','Example vacancies · employers and conditions are fictional')")
app=app.replace("$('#system-link').innerHTML = t('Дизайн-система','Design system')+icon('diagonal');", "$('#system-link').innerHTML = t('Матеріали для кар’єри','Career resources')+icon('diagonal'); $('#system-link').href = '/' + (language === 'en' ? 'en/' : '') + 'blog/';")
app=app.replace("t('Дизайн-концепція','Design concept')", "t('Wellness Talent','Wellness Talent')")
app=app.replace("${link('components',t('Бібліотека компонентів','Component library'))}<button class=\"reset\" data-action=\"wireframe\">${t('Переглянути wireframe','View wireframe')}</button>", "<a href=\"/${language === 'en' ? 'en/' : ''}salary-guide/\">${t('Посібник з оплати','Compensation guide')}</a><a href=\"/${language === 'en' ? 'en/' : ''}blog/\">${t('Кар’єрні матеріали','Career resources')}</a>")
# Keep search-engine-visible links to actual detail pages, enhancing them with a dialog in JS.
app=app.replace('<h3><button data-action="details" data-id="${escape(job.id)}">${escape(job.title[language])}</button></h3>', '<h3><a href="/${language === \'en\' ? \'en/\' : \'\'}demo-jobs/${escape(job.id)}/" data-action="details" data-id="${escape(job.id)}">${escape(job.title[language])}</a></h3>')
app=app.replace("<li ${i===a.step?'aria-current=\"step\"':''}","<li ${i===a.step?'aria-current=\"step\"':''}")
# A general application is real; applications for fictional jobs remain local demos.
app=app.replace("application={id,step:0,", "application={id,step:0,submitting:false,")
app=app.replace("  function startApplication(id='') {", "  function startApplication(id='') {\n    const canPrefill = demoProfile && (!PUBLIC || Boolean(id));")
app=app.replace('name:demoProfile?', 'name:canPrefill?').replace('email:demoProfile?', 'email:canPrefill?').replace('phone:demoProfile?', 'phone:canPrefill?')
app=app.replace("    applicationStep();\n  }\n\n  function applicationStep()", "    if (PUBLIC && !id && params.get('interest')) application.experience = t('Бажаний напрям: ','Preferred specialism: ') + params.get('interest').slice(0,80);\n    applicationStep();\n  }\n\n  function applicationStep()")
app=app.replace("const steps=[t('Контакти','Contact'),t('Досвід','Experience'),t('Перевірка','Review')];", "const real = PUBLIC && !j;\n    const steps=[t('Контакти','Contact'),t('Досвід','Experience'),t('Перевірка','Review')];")
app=app.replace("t('Загальна демо-анкета','General demo application')", "t('Загальна анкета Emplivo','General Emplivo application')")
app=app.replace("${t('Розумію, що це пробний відгук: дані й резюме не надсилатимуться та не зберігатимуться в базі.','I understand this is a test application: data and CV will not be sent or stored in a database.')}", "${real ? t('Погоджуюся на обробку контактів, досвіду та резюме компанією Emplivo для підбору роботи.','I consent to Emplivo processing my contact details, experience and CV for recruitment.') : t('Розумію, що це пробний відгук: дані й резюме не надсилатимуться та не зберігатимуться в базі.','I understand this is a test application: data and CV will not be sent or stored in a database.')}")
app=app.replace("t('Загальна анкета · демонстрація','General application · demonstration')", "t('Загальна анкета до Emplivo','General application to Emplivo')")
app=app.replace("<form id=\"application-form\">${body}", "<form id=\"application-form\"><p class=\"${real ? 'application-notice' : 'detail-demo'}\">${real ? t('Реальне звернення: після надсилання анкета потрапить команді Emplivo. Це не відгук на вигадану вакансію.','Real enquiry: submitting sends your application to Emplivo. This is not an application for a fictional job.') : t('Демонстраційна вакансія: анкета та файл нікуди не надсилаються.','Fictional vacancy: your application and file will not be sent.')}</p><p class=\"form-error\" id=\"application-error\" role=\"alert\" tabindex=\"-1\" hidden></p>${body}")
app=app.replace("t('Прототип. Нічого не надсилається.','Prototype. Nothing is submitted.')", "(real ? t('Ваші дані передаються лише після надсилання.','Your data is sent only on submission.') : t('Демо. Нічого не надсилається.','Demo. Nothing is submitted.'))")
app=app.replace("${a.step===2?t('Завершити демо-відгук','Complete demo application'):t('Продовжити','Continue')}", "${a.step===2?(real?t('Надіслати загальну анкету','Submit general application'):t('Завершити демо-відгук','Complete demo application')):t('Продовжити','Continue')}")
app=app.replace("document.addEventListener('submit',event=>{", "document.addEventListener('submit',async event=>{")
app=app.replace("else{success(t('Перший крок зроблено.'", "else{if(PUBLIC&&!application.id){await submitGeneral(form);return;}success(t('Перший крок зроблено.'")
app=app.replace("application=null;brief=null;\n    openDialog(t('Готово · демонстрація','Complete · demonstration')", "const real = PUBLIC && application && !application.id;\n    application=null;brief=null;\n    openDialog(real ? t('Анкету отримано','Application received') : t('Готово · демонстрація','Complete · demonstration')")
app=app.replace("document.body.style.overflow='';application=null;brief=null;", "document.body.style.overflow='';application?.controller?.abort();application=null;brief=null;")
# Employer briefs become honest user-sent email requests, never fake bookings.
app=app.replace("t('Розумію: це демонстрація, запит не надсилається й консультація не бронюється.','I understand this is a demonstration: no enquiry is sent and no consultation is booked.')", "t('Розумію: форма підготує лист, який я надішлю самостійно. Час консультації потребує підтвердження команди.','I understand the form prepares an email for me to send. Consultation time requires confirmation from the team.')")
app=app.replace("else success(t('Запит набув форми.'", "else if(PUBLIC){prepareBriefEmail();}else success(t('Запит набув форми.'")
# Use real URL routes for the public site; old hash links are still recognised.
app=app.replace("location.hash='catalog'+(q.size?'?'+q:'');", "if(PUBLIC)location.href=publicPath('catalog')+(q.size?'?'+q:'');else location.hash='catalog'+(q.size?'?'+q:'');")
app=app.replace("history.replaceState(null,'',location.pathname+location.search+'#catalog'+(q.size?'?'+q.toString():''));", "history.replaceState(null,'',PUBLIC ? publicPath('catalog')+(q.size?'?'+q.toString():'') : location.pathname+location.search+'#catalog'+(q.size?'?'+q.toString():''));")
app=app.replace("new URLSearchParams(location.hash.split('?')[1]||'')", "new URLSearchParams(PUBLIC ? (location.hash.includes('?')?location.hash.split('?')[1]:location.search) : location.hash.split('?')[1]||'')")
app=app.replace("language=language==='uk'?'en':'uk';persist('ec-language',language);render(false);", "language=language==='uk'?'en':'uk';persist('ec-language',language);if(PUBLIC){history.replaceState(null,'',publicPath(page)+location.search);}render(false);")
app=app.replace("const action=el.dataset.action,id=el.dataset.id;", "const action=el.dataset.action,id=el.dataset.id;\n    if(PUBLIC && el.tagName==='A')event.preventDefault();")
app=app.replace("    observe();\n  }", "    if(PUBLIC){\n      $$('a[href^=\"#\"]').forEach(a=>{const raw=a.getAttribute('href').slice(1);const [name,query]=raw.split('?');if(Object.hasOwn(routePaths,name))a.href=publicPath(name)+(query?'?'+query:'');});\n      const canonical=$('link[rel=canonical]');if(canonical)canonical.href='https://www.emplivo.com.ua'+publicPath(page);\n      const uk=$('link[hreflang=uk]'),en=$('link[hreflang=en]');if(uk)uk.href='https://www.emplivo.com.ua'+publicPath(page,'uk');if(en)en.href='https://www.emplivo.com.ua'+publicPath(page,'en');\n      const x=$('link[hreflang=\"x-default\"]');if(x)x.href='https://www.emplivo.com.ua'+publicPath(page,'uk');\n      document.title=document.title.replace(' · Concept','');\n      if(page==='home' && location.hash.startsWith('#application')){const job=params.get('job');startApplication(jobs.some(j=>j.id===job)?job:'');}\n    }\n    observe();\n  }")
# Public privacy information replaces prototype-only statements.
app=app.replace("'Jobs, employers and candidates are fictional. Forms make no network requests. Local storage holds only language, saved job identifiers and local alert criteria. Names, contacts and CV contents are not persisted.'", "'Published demonstration jobs and employers are fictional. A general application is a real request to Emplivo: the team receives your contact details, experience and optional CV for recruitment. Test job applications remain local. Browser storage holds only language, saved job IDs and search preferences.'")
app=app.replace("'Вакансії, роботодавці та кандидати вигадані. Форми не роблять мережевих запитів. У localStorage зберігаються лише мова, ідентифікатори збережених вакансій та критерії локальних сповіщень. Імена, контакти та вміст резюме не записуються.'", "'Демонстраційні вакансії та роботодавці вигадані. Загальна анкета — реальний запит до Emplivo: команда отримує контакти, досвід і необов’язкове резюме для підбору роботи. Пробні відгуки залишаються локальними. У браузері зберігаються лише мова, ID вакансій і критерії пошуку.'")
app=app.replace("'Це інтерактивний прототип: для перегляду сценаріїв увімкніть JavaScript.'", "'Для пошуку й надсилання анкети увімкніть JavaScript.'")
app=app.replace("'Турбота також<br>про ваші дані.'", "'Турбота також<br>про ваші дані.'")
app=app.replace("'Що робить прототип','What this prototype does'", "'Як працюють форми','How forms work'")
app=app.replace("'Вибране резюме залишається в пам’яті вкладки для демонстрації кроків. Закрийте форму або перезавантажте сторінку, щоб очистити цей стан. Повноцінна політика для робочого сайту потребує даних про юридичну особу, підстави обробки, строки зберігання й одержувачів.'", "'Оператор: ТОВ «ЕМПЛІВО», ЄДРПОУ 46615773. Доступ до надісланих анкет і резюме має команда Emplivo. Для запиту про доступ, виправлення, видалення даних, строки зберігання або передачу роботодавцям звертайтеся на hr@emplivo.com.ua або +380 (67) 777 80 60. Згоду можна відкликати через ці контакти.'")
app=app.replace("'A selected CV remains in tab memory to demonstrate the flow. Close the form or reload to clear this state. A production privacy notice requires the legal entity, processing bases, retention periods and recipients.'", "'Operator: Emplivo LLC, registration 46615773. The Emplivo team has access to submitted applications and CVs. For access, correction, deletion, retention or employer-sharing enquiries, contact hr@emplivo.com.ua or +380 (67) 777 80 60. You can withdraw consent through these contacts.'")
app=app.replace("'Про Emplivo'", "'Про Emplivo'")
app=app.replace("'Ця концепція показує, як уважний підбір і зрозумілі цифрові інструменти можуть працювати разом.'", "'Уважний підбір і зрозумілі цифрові інструменти допомагають зробити наступний крок.'")
app=app.replace("'Emplivo поєднує міжнародний рекрутинг із фокусом на індустріях турботи про здоров’я та якість життя. Ця концепція показує, як уважний підбір і зрозумілі цифрові інструменти можуть працювати разом.'", "'Emplivo поєднує міжнародний рекрутинг із професійними напрямами SPA, wellness і фітнесу. Уважний підбір і зрозумілі цифрові інструменти допомагають зробити наступний крок.'")
app=app.replace("'Emplivo combines international recruitment with a focus on care, wellbeing and quality of life. This concept explores how thoughtful matching and clear digital tools can work together.'", "'Emplivo combines international recruitment with spa, wellness and fitness career resources. Thoughtful matching and clear digital tools help you take the next step.'")
app=app.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')

extra=r'''
  async function submitGeneral(form) {
    const a=application;if(!a||a.submitting)return;
    const fingerprint=JSON.stringify([a.name,a.phone,a.email,a.city,a.experience,a.file?.name,a.file?.size,a.file?.lastModified]);
    if(a.fingerprint!==fingerprint){a.fingerprint=fingerprint;a.submissionId=crypto.randomUUID();}
    const data=new FormData();
    for(const [key,value] of Object.entries({submissionId:a.submissionId,fullName:a.name,phone:a.phone,email:a.email,role:'',destination:'any',experience:(a.city?t('Бажане місто: ','Preferred city: ')+a.city+'\n':'')+a.experience,consent:'on'}))data.set(key,value);
    if(a.file)data.set('cv',a.file);
    const error=$('#application-error');error.hidden=true;
    a.submitting=true;const controls=[...form.elements];controls.forEach(e=>e.disabled=true);
    const controller=new AbortController();a.controller=controller;const timeout=setTimeout(()=>controller.abort(),30000);
    try{
      const response=await fetch('/api/applications.php',{method:'POST',body:data,signal:controller.signal,headers:{'Accept-Language':language}});
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
  function prepareBriefEmail(){
    const b=brief;if(!b)return;
    const body=[t('Запит на підбір Emplivo','Emplivo hiring brief'),b.company,b.sector,b.location,b.role,t('Кількість: ','Headcount: ')+b.count,t('Початок: ','Start: ')+b.start,b.name,b.email,t('Бажаний час: ','Preferred time: ')+b.time].join('\n');
    const href='mailto:hr@emplivo.com.ua?subject='+encodeURIComponent('Emplivo — '+b.company)+'&body='+encodeURIComponent(body);
    brief=null;
    openDialog(t('Запит підготовлено','Your brief is ready'),`<p class="dialog-subtitle">${t('Форма не надсилає лист автоматично. Відкрийте поштову програму або скопіюйте текст і надішліть на hr@emplivo.com.ua. Час розмови потребує підтвердження.','The form does not send automatically. Open your email app or copy the text to hr@emplivo.com.ua. A consultation time requires confirmation.')}</p><a class="button button-primary" href="${escape(href)}" target="_blank" rel="noopener noreferrer">${t('Відкрити поштову програму','Open email app')}</a><label class="field" style="margin-top:20px"><span>${t('Текст для копіювання','Text to copy')}</span><textarea rows="10" readonly>${escape(body)}</textarea></label>`,true);
  }
'''
app=app.replace("  document.addEventListener('click',event=>{",extra+"\n  document.addEventListener('click',event=>{")
(STAGE/'wellness.js').write_text(app)
template=(CONCEPT/'index.html').read_text()
template=template.replace('<html lang="uk">','<html lang="uk" data-mode="public">')
template=template.replace('content="noindex,nofollow"','content="index,follow"')
template=template.replace('href="styles.css"','href="/wellness.css?v=20261112w"').replace('src="data.js"','src="/wellness-data.js?v=20261112w"').replace('src="app.js"','src="/wellness.js?v=20261112w"')
template=template.replace('href="assets/','href="/assets/')
template=template.replace('Інтерактивна дизайн-концепція Emplivo: преміальний рекрутинг Wellness, Spa та Fitness.','Emplivo — рекрутинг і кар’єра у Wellness, Spa та Fitness. Каталог демонстраційних вакансій, запити на підбір і загальна анкета кандидата.')
template=template.replace('Emplivo — Wellness Talent · Design concept','Emplivo — Wellness Talent')
template=template.replace('<main id="main" tabindex="-1"></main>','<main id="main" tabindex="-1"></main><span id="application" hidden></span><span id="vacancies" hidden></span>')
template=template.replace('Це інтерактивний прототип: для перегляду сценаріїв увімкніть JavaScript. Структура та технічні нотатки доступні у папці docs.','Для фільтрів і надсилання анкети увімкніть JavaScript. Контакти: hr@emplivo.com.ua · +380 (67) 777 80 60.')
schema={'@context':'https://schema.org','@type':'Organization','@id':'https://www.emplivo.com.ua/#organization','name':'Emplivo','url':'https://www.emplivo.com.ua/','email':'hr@emplivo.com.ua','telephone':'+380677778060'}
meta='''<link rel="canonical" href="https://www.emplivo.com.ua/">
<link rel="alternate" hreflang="uk" href="https://www.emplivo.com.ua/">
<link rel="alternate" hreflang="en" href="https://www.emplivo.com.ua/en/">
<link rel="alternate" hreflang="x-default" href="https://www.emplivo.com.ua/">
<script type="application/ld+json">'''+json.dumps(schema,ensure_ascii=False)+'''</script>'''
template=template.replace('</head>',meta+'</head>')
routes=['','jobs/','employers/','about/','cases/','demo-account/','demo-employer-dashboard/','privacy/']
for route in routes:
    for lang in ['uk','en']:
        out=STAGE/('en' if lang=='en' else '')/route/'index.html';out.parent.mkdir(parents=True,exist_ok=True)
        html=template.replace('lang="uk" data-mode','lang="'+lang+'" data-mode')
        if route in ['cases/','demo-account/','demo-employer-dashboard/']:html=html.replace('content="index,follow"','content="noindex,follow"')
        out.write_text(html)

bridge='''\n/* Wellness visual integration for retained editorial pages. */
@font-face{font-family:WellnessInter;src:url('/assets/fonts/inter-cyrillic-wght-normal.woff2');font-weight:100 900;font-display:swap;unicode-range:U+0400-052F,U+2116}@font-face{font-family:WellnessInter;src:url('/assets/fonts/inter-latin-wght-normal.woff2');font-weight:100 900;font-display:swap}@font-face{font-family:WellnessSerif;src:url('/assets/fonts/cormorant-garamond-cyrillic-wght-normal.woff2');font-weight:300 700;font-display:swap;unicode-range:U+0400-052F,U+2116}@font-face{font-family:WellnessSerif;src:url('/assets/fonts/cormorant-garamond-latin-wght-normal.woff2');font-weight:300 700;font-display:swap}
.seo-page{background:#F9F7F2;color:#262624;font-family:WellnessInter,Inter,Arial,sans-serif}.seo-header{background:#F9F7F2;border-color:#DDDCD3}.seo-nav .brand,.seo-page .brand{color:#262624}.seo-page .brand-emblem{background:#5A7263;color:#F9F7F2;border-radius:12px}.seo-hero h1,.seo-section h2,.seo-aside h2{font-family:WellnessSerif,Georgia,serif;color:#262624}.seo-section p,.seo-lead,.seo-aside p{color:#64675E}.seo-aside,.seo-card{background:#FFFEFA;border-color:#DDDCD3;border-radius:20px}.seo-card{color:#262624}.seo-card:hover{background:#E6ECE5;border-color:#5A7263}.seo-card svg{color:#5A7263}.seo-footer{background:#EFECE6;color:#262624}.seo-footer p{color:#64675E}.seo-footer .brand{color:#262624}.seo-page .button.primary,.seo-page .button-primary{background:#5A7263;color:#F9F7F2;border-color:#5A7263}.seo-page a:focus-visible,.seo-page button:focus-visible{outline-color:#405446}.seo-page .eyebrow{color:#5A7263}
'''
css=(Path('/workspace/Emplivo/seo.css')).read_text()
(STAGE/'seo.css').write_text(css+bridge)
with (STAGE/'wellness.css').open('a') as f:f.write('\n.application-notice{padding:14px 16px;background:#E6ECE5;border-radius:12px;color:#405446;font-size:11px;line-height:1.7;margin-bottom:20px}\n')
for item in STAGE.rglob('*'):
    item.chmod(0o755 if item.is_dir() else 0o644)
STAGE.chmod(0o755)
from make_portable import make_portable
make_portable(STAGE)
print('Wellness release integrated:',STAGE,'core page templates:',len(routes)*2)
