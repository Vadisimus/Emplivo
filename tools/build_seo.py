#!/usr/bin/env python3
"""Build crawlable bilingual editorial pages. No dependencies or network access."""
from pathlib import Path
from html import escape
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.emplivo.com.ua/'
DATE = '2026-11-12'
PAGES = []

def add(path, uk, en, lead_uk, lead_en, blocks, links=(), article=False):
    PAGES.append(dict(path=path, titles=(uk, en), leads=(lead_uk, lead_en), blocks=blocks, links=links, article=article))

add('employers/', 'Підбір персоналу для SPA, wellness і фітнесу', 'Spa, wellness and fitness recruitment for employers',
    'Почніть із чіткого запиту: кого шукаєте, де працюватиме людина та які умови можете запропонувати.',
    'Start with a clear hiring brief: who you need, where they will work and the conditions you can offer.', [
    ('Що вказати у запиті', 'What to include in your brief',
     'Посада, країна й місто, кількість працівників, дата початку, графік, формат зайнятості та бюджет. Для SPA уточніть перелік процедур; для тренера — формат роботи з клієнтами; для менеджера — команду й обсяг відповідальності.',
     'Include the role, country and city, headcount, start date, schedule, employment arrangement and budget. Specify treatments for a spa role, client delivery for a trainer, and team size and responsibilities for a manager.'),
    ('Від вимог до співбесіди', 'From requirements to interview',
     'Розділіть обов’язкові й бажані навички. Підготуйте питання про досвід, кваліфікацію, доступність і знання мов. Обсяг пошуку, перевірки та наступні кроки потрібно погодити з командою Emplivo до початку роботи.',
     'Separate essential and preferred skills. Prepare questions on experience, qualifications, availability and languages. Agree the search scope, checks and next steps with Emplivo before work starts.'),
    ('Прозорі умови співпраці', 'Clear engagement terms',
     'Строки, вартість, відповідальність сторін і доступність послуги узгоджуються індивідуально. Надсилання запиту не публікує вакансію автоматично та не створює платного замовлення.',
     'Timing, fees, responsibilities and service availability are agreed individually. Sending a brief does not automatically publish a vacancy or create a paid order.')],
    [('contact/?type=employer#request', 'Надіслати запит на підбір', 'Send a hiring brief'), ('employers/temporary-recruitment/', 'Тимчасовий персонал', 'Temporary staffing'), ('employers/permanent-recruitment/', 'Постійний найм', 'Permanent recruitment')])

add('candidates/', 'Робота та підтримка кандидатів', 'Jobs and candidate support',
    'Знайдіть опубліковану вакансію або залиште загальну анкету з описом свого досвіду.',
    'Explore published vacancies or submit a general application describing your experience.', [
    ('Підготуйте анкету', 'Prepare your application',
     'Вкажіть актуальні контакти, спеціалізацію, країну роботи та доступність. У резюме опишіть конкретні обов’язки, навчання й сертифікати. PDF або DOCX до 5 МБ можна додати у формі на головній сторінці.',
     'Include current contact details, specialism, preferred country and availability. Describe specific responsibilities, training and certificates. You can attach a PDF or DOCX up to 5 MB using the homepage application form.'),
    ('Перевіряйте умови вакансії', 'Check the vacancy conditions',
     'Уточнюйте роботодавця, місце роботи, базову оплату, змінні виплати, графік і тип договору. Проживання, переїзд або організаційний супровід вважаються погодженими лише після прямого підтвердження.',
     'Confirm the employer, workplace, base pay, variable compensation, schedule and contract. Accommodation, relocation or administrative support should only be treated as agreed after explicit confirmation.'),
    ('Збережені вакансії та нові можливості', 'Saved jobs and future opportunities',
     'Опубліковану вакансію можна зберегти у браузері на поточному пристрої. Автоматичні email-сповіщення й особистий кабінет ще не підключені; запитати про майбутні можливості можна електронною поштою.',
     'You can save the published vacancy in your browser on this device. Automated email alerts and candidate accounts are not connected yet; you can ask about future opportunities by email.')],
    [('#application', 'Заповнити анкету', 'Submit an application'), ('jobs/', 'Переглянути напрями роботи', 'Explore job categories'), ('blog/spa-therapist-cv/', 'Підготовка резюме', 'Prepare your CV')])

add('employers/temporary-recruitment/', 'Тимчасовий персонал для SPA та фітнесу', 'Temporary spa and fitness staffing',
    'Обговоріть потребу в сезонному підсиленні, заміні працівника або покритті конкретних змін.',
    'Discuss seasonal demand, staff cover or support for specific shifts.', [
    ('Коли потрібне тимчасове підсилення', 'When temporary cover is useful',
     'Опишіть причину запиту, період і потрібні зміни. Для SPA важливі доступні процедури та досвід роботи з обладнанням; для фітнесу — формат занять і потрібні кваліфікації.',
     'Describe the reason, dates and shifts. For a spa, specify treatments and equipment experience; for fitness, specify session formats and required qualifications.'),
    ('Що погодити до початку', 'Agree before the start',
     'Підтвердьте формат договору, оплату, робочі години, інструктаж, відповідальність за обладнання та порядок заміни. Вимоги залежать від країни й конкретної ролі.',
     'Confirm the contract arrangement, pay, working hours, induction, equipment responsibilities and replacement process. Requirements depend on the country and role.'),
    ('Доступність і строки', 'Availability and timing',
     'Наявність фахівців та можливість організувати тимчасовий підбір уточнюються після запиту. Миттєвий вихід і гарантовані строки без погодження не обіцяються.',
     'Candidate availability and the feasibility of temporary recruitment are confirmed after enquiry. Immediate cover and fixed turnaround times require explicit agreement.')],
    [('contact/?type=temporary#request', 'Обговорити тимчасове підсилення', 'Discuss temporary cover'), ('jobs/spa-therapist/', 'Напрям SPA-терапевтів', 'Spa therapist roles'), ('salary-guide/', 'Як оцінити бюджет', 'Plan the compensation budget')])

add('employers/permanent-recruitment/', 'Постійний підбір персоналу', 'Permanent spa, fitness and wellness recruitment',
    'Підготуйте пропозицію роботи, у якій зрозумілі відповідальність, очікування та винагорода.',
    'Prepare an offer with clear responsibilities, expectations and compensation.', [
    ('Опишіть роль', 'Define the role',
     'Для терапевта вкажіть процедури та вимоги до навчання. Для тренера — формат зайнятості та роботу з клієнтською базою. Для wellness-менеджера — розмір команди, бюджет і повноваження.',
     'For therapists, specify treatments and training. For trainers, explain the employment model and client arrangements. For wellness managers, define team size, budget and decision-making authority.'),
    ('Побудуйте відбір', 'Plan the assessment',
     'Визначте критерії оцінки та учасників співбесіди. Практичні завдання мають бути доречними, безпечними й погодженими з кандидатом. Узгодьте, які документи та рекомендації перевірятимуться.',
     'Define assessment criteria and interviewers. Practical assessments should be relevant, safe and agreed with candidates. Agree which documents and references will be checked.'),
    ('Погодьте умови', 'Agree the terms',
     'Пропозиція має розрізняти базову оплату, бонуси, графік і випробувальний період, якщо він передбачений. Вартість та умови рекрутингової послуги погоджуються окремо.',
     'Distinguish base pay, bonuses, schedule and any probation period in the offer. Recruitment service fees and terms are agreed separately.')],
    [('contact/?type=permanent#request', 'Запит на постійний підбір', 'Request permanent recruitment'), ('jobs/wellness-manager/', 'Підбір wellness-менеджера', 'Wellness management roles'), ('blog/hiring-spa-therapists/', 'Як скласти запит на підбір', 'Prepare a hiring brief')])

ROLES = [
    ('spa-therapist', 'SPA-терапевти', 'Spa therapists', 'SPA-терапевта', 'spa therapist',
     'Перелік процедур, знання протоколів, гігієна, консультація клієнта й документи про навчання. Перевіряйте вимоги конкретної країни; назва посади сама по собі не підтверджує ліцензію.',
     'Treatment skills, protocols, hygiene, client consultation and training records. Check the requirements in the destination country; a job title alone does not establish a licence.',
     'Оплата за годину чи місяць, комісія за процедури, чайові, перерви між клієнтами та оплачуване навчання.',
     'Hourly or monthly base pay, treatment commission, tips, breaks between clients and paid training.'),
    ('personal-trainer', 'Персональні тренери', 'Personal trainers', 'персонального тренера', 'personal trainer',
     'Досвід складання програм, індивідуальних занять і роботи з різними рівнями підготовки. Уточніть визнання кваліфікації, страхування та вимоги до першої допомоги у країні роботи.',
     'Experience in programme design, individual sessions and different fitness levels. Confirm recognised qualifications, insurance and first-aid requirements in the destination country.',
     'Найманий працівник чи самозайнятість, базова ставка, оплата сесій, оренда залу та відповідальність за пошук клієнтів.',
     'Employment or self-employment, base pay, session payments, gym rental and responsibility for finding clients.'),
    ('wellness-manager', 'Wellness-менеджери', 'Wellness managers', 'wellness-менеджера', 'wellness manager',
     'Управління командою, клієнтським досвідом, розкладом і бюджетом. Порівнюйте не лише назву, а й масштаб об’єкта, підпорядкування та фактичні повноваження.',
     'Team leadership, guest experience, scheduling and budgets. Compare property scale, reporting lines and actual authority rather than the job title alone.',
     'Базова винагорода, критерії бонусу, чисельність команди, чергування, робота у вихідні та право ухвалювати рішення.',
     'Base compensation, bonus criteria, team size, on-call duties, weekends and decision-making authority.')]

add('jobs/', 'Вакансії та професійні напрями', 'Jobs and professional categories',
    'Перегляньте демонстраційні вакансії SPA, wellness і фітнесу та підготуйтеся до пошуку роботи.',
    'Explore demonstration spa, wellness and fitness jobs and prepare for your next career step.', [
    ('Які вакансії доступні', 'Available vacancies',
     'На головній сторінці є шість вигаданих вакансій для ознайомлення з можливостями сайту. Усі роботодавці, умови та зарплати в цих прикладах демонстраційні. Це не справжні пропозиції працевлаштування.',
     'The homepage contains six fictional jobs illustrating the site. All employers, conditions and salaries in these examples are demonstrations, not real employment offers.'),
    ('Як шукати та зберігати', 'Search and save',
     'Використовуйте пошук за посадою або містом, фільтр напряму й збереження на поточному пристрої. Пробний відгук на демонстраційну вакансію не передає анкету в базу. Загальна анкета до Emplivo є окремою дією.',
     'Search by role or city, filter by category and save on this device. A test application to a demonstration job does not submit data to the database. A general Emplivo application is a separate action.')],
    [('jobs/'+r[0]+'/', r[1], r[2]) for r in ROLES] + [('#vacancies','Демонстраційні вакансії','Demonstration jobs'),('demo-employers/','Вигадані оголошення роботодавців','Fictional employer advertisements'),('locations/ukraine/','Робота в Україні','Working in Ukraine')])

for slug, uk, en, genuk, genen, requk, reqen, payuk, payen in ROLES:
    add('jobs/'+slug+'/', uk+': робота та вимоги', en+': jobs and requirements',
        'Орієнтири для кандидатів і роботодавців: кваліфікація, умови та питання для співбесіди.',
        'A practical guide for candidates and employers: qualifications, conditions and interview questions.', [
        ('Навички та кваліфікація', 'Skills and qualifications', requk, reqen),
        ('Що уточнити про умови', 'Questions about the offer', payuk, payen),
        ('Поточні можливості', 'Current opportunities',
         'На головній сторінці є демонстраційні вакансії цього напряму з вигаданими умовами. Вони не є реальними пропозиціями. Для реального звернення до Emplivo можна окремо залишити загальну анкету зі своєю спеціалізацією.',
         'The homepage includes demonstration jobs in this category with fictional conditions. These are not real offers. You can separately submit a general application to Emplivo with your specialism.'),
        ('Роботодавцям', 'For employers',
         'У запиті на підбір вкажіть локацію, обов’язки, графік, вимоги до навчання та бюджет. Доступність пошуку й умови роботи потрібно погодити з командою.',
         'Include location, duties, schedule, qualification requirements and budget in your hiring brief. Agree recruitment availability and engagement terms with the team.')],
        [('#application?interest='+slug, 'Загальна анкета: '+genuk, 'General application: '+genen),
         ('salary-guide/'+slug+'/', 'Умови та структура оплати', 'Compensation and offer checklist'),
         ('contact/?type=opportunities&role='+slug+'#request', 'Запитати про майбутні можливості', 'Ask about future opportunities'),
         ('employers/', 'Підбір для роботодавців', 'Recruitment for employers')])

add('locations/ukraine/', 'Робота та підбір персоналу в Україні', 'Jobs and recruitment in Ukraine',
    'Орієнтуйтеся на фактичне місце роботи, умови договору та актуальну інформацію роботодавця.',
    'Check the actual workplace, contract conditions and up-to-date employer information.', [
    ('Локації у демонстраційних прикладах', 'Locations in the demonstration examples',
     'Київ, Львів і Одеса використані як локації вигаданих вакансій. Це не підтвердження наявності офісів Emplivo, клієнтів або реальних місць роботи в цих містах.',
     'Kyiv, Lviv and Odesa are used as locations for fictional jobs. This does not establish Emplivo offices, clients or real openings in these cities.'),
    ('Питання про місце роботи', 'Questions about the workplace',
     'Уточніть точну адресу, доступність транспорту, графік, безпекові процедури та місце проживання, якщо воно передбачене. Для кандидатів з інших країн право на роботу й оформлення документів розглядаються окремо.',
     'Confirm the address, transport, schedule, safety procedures and accommodation if offered. Work eligibility and documentation for international candidates must be considered separately.'),
    ('SPA, wellness і фітнес', 'Spa, wellness and fitness',
     'Нових підтверджених вакансій у цих напрямах для України наразі немає. Залиште загальну анкету або надішліть роботодавчий запит із конкретною локацією.',
     'There are no newly confirmed Ukrainian vacancies in these categories at present. Submit a general application or send a hiring brief with a specific location.')],
    [('#vacancies','Переглянути демонстраційні вакансії','Explore demonstration jobs'),('jobs/','Професійні напрями','Job categories'),('contact/?type=employer#request','Запит на підбір в Україні','Discuss hiring in Ukraine')])

add('salary-guide/', 'Оплата праці у SPA, wellness і фітнесі', 'Spa, wellness and fitness compensation guide',
    'Практичний посібник із порівняння пропозицій. Перевірені числові діапазони зарплат ще не опубліковані.',
    'A practical guide to comparing offers. Verified numerical salary ranges have not yet been published.', [
    ('Порівнюйте однакові умови', 'Compare like with like',
     'Порівнюйте одну країну, посаду, досвід, робочі години й формат зайнятості. Зарплата до податків, сума після податків та виручка самозайнятого фахівця — різні показники.',
     'Compare the same country, role, experience, hours and employment arrangement. Gross salary, net pay and self-employed revenue are different measures.'),
    ('Розділяйте складові винагороди', 'Separate compensation components',
     'Базова оплата, комісія, бонус, чайові та проживання мають бути описані окремо. Запитайте, які виплати гарантовані, коли вони нараховуються та які витрати несе працівник.',
     'Base pay, commission, bonuses, tips and accommodation should be described separately. Ask which payments are guaranteed, when they are earned and which costs the worker pays.'),
    ('Методика майбутніх діапазонів', 'Methodology for future salary ranges',
     'Числові дані можна додавати після перевірки джерела, географії, періоду, обсягу вибірки й дозволу на використання. Малі вибірки не слід видавати за ринковий стандарт. Оцінки з посібника не підставляються у вакансії як оплата роботодавця.',
     'Publish numerical ranges only after checking the source, geography, period, sample size and permission to use the data. Small samples should not be presented as market benchmarks. Guide estimates must not be inserted into job listings as employer-provided pay.')],
    [('salary-guide/'+r[0]+'/', r[1]+': оплата', r[2]+': compensation') for r in ROLES])

for slug,uk,en,genuk,genen,requk,reqen,payuk,payen in ROLES:
    add('salary-guide/'+slug+'/', 'Оплата '+genuk+': як оцінити пропозицію', en+': how to compare compensation',
        'Порівняйте складові винагороди та робоче навантаження перед співбесідою або підготовкою вакансії.',
        'Compare compensation components and workload before an interview or writing a job advertisement.', [
        ('Що має бути у пропозиції', 'What the offer should explain', payuk, payen),
        ('Питання роботодавцю', 'Questions for the employer',
         'Яка гарантована оплата за погоджені години? Як обчислюється змінна частина? Які витрати відшкодовуються? Попросіть письмовий опис і порівнюйте пропозиції за однаковим періодом та кількістю годин.',
         'What pay is guaranteed for the agreed hours? How is variable pay calculated? Which expenses are reimbursed? Ask for written terms and compare offers using the same period and working hours.'),
        ('Числові дані та обмеження', 'Figures and limitations',
         'Перевірених діапазонів для цієї ролі поки немає. Ця сторінка пояснює порівняння умов і не є дослідженням середньої зарплати. Географія, джерела, період та обсяг вибірки будуть потрібні для публікації цифр.',
         'Verified ranges for this role are not yet available. This page explains how to compare conditions; it is not an average salary survey. Geography, sources, collection period and sample size are required before publishing figures.')],
        [('jobs/'+slug+'/',uk+': професійний напрям',en+': role guide'),('salary-guide/','Методика порівняння оплати','Compensation methodology'),('contact/?type=employer#request','Обговорити бюджет вакансії','Discuss a hiring budget')])

ARTICLES = [
    ('hiring-spa-therapists', 'Як підготувати запит на підбір SPA-терапевта', 'How to prepare a spa therapist hiring brief',
     'Чітка вакансія допомагає порівнювати кандидатів за навичками й очікуваннями, а не лише за назвою посади.',
     'A clear brief helps compare candidates by skills and expectations rather than job title alone.', [
     ('Опишіть робочий день','Describe the working day','Вкажіть процедури, обладнання, тривалість сеансів, підготовку кабінету та правила взаємодії з клієнтом. Не замінюйте цей опис загальним словом «універсал».','Specify treatments, equipment, session length, room preparation and client interaction. A generic request for an all-rounder is not a substitute for describing the work.'),
     ('Розділіть вимоги','Separate the requirements','Виділіть необхідні кваліфікації та навички, яким можна навчити. Перевірте вимоги до практики у країні роботи за офіційними джерелами й погодьте спосіб перевірки документів.','Distinguish essential qualifications from skills that can be taught. Check destination-country practice requirements using official sources and agree how credentials will be verified.'),
     ('Підготуйте умови','Prepare the conditions','Опишіть базову оплату, комісію, графік, перерви та дату початку. Узгодьте питання для співбесіди, щоб усі кандидати отримували однакову інформацію.','Describe base pay, commission, schedule, breaks and start date. Agree interview questions so candidates receive consistent information.')],
     [('employers/','Послуги роботодавцям','Employer services'),('jobs/spa-therapist/','SPA-терапевти: навички','Spa therapist skills')]),
    ('spa-therapist-cv','Резюме SPA-терапевта: практичний список','Spa therapist CV: a practical checklist',
     'Покажіть досвід так, щоб роботодавцю було легко зрозуміти ваші навички й доступність.',
     'Make your experience, practical skills and availability easy for an employer to understand.', [
     ('Контакти та спеціалізація','Contact details and specialism','Зазначте актуальні контакти, бажаний напрям, доступність і країну роботи. На початковому етапі не додавайте до CV номери документів або зайві чутливі дані.','Include current contact details, specialism, availability and preferred country. Avoid document numbers or unnecessary sensitive information in an initial CV.'),
     ('Досвід і навчання','Experience and training','Для кожної роботи опишіть обов’язки, процедури та період. Вкажіть назву навчального закладу, кваліфікацію й дату навчання без перебільшень; поясніть фактичний рівень володіння мовами.','For each position, describe responsibilities, treatments and dates. State the training provider, qualification and dates accurately, and explain your actual language ability.'),
     ('Перевірка перед поданням','Before you submit','Перевірте контакти й читабельність файлу. Для форми Emplivo підходить PDF або DOCX до 5 МБ. Окремо вкажіть питання про умови, які хочете обговорити.','Check contact details and readability. The Emplivo form accepts PDF or DOCX files up to 5 MB. List any questions about the offer separately.')],
     [('candidates/','Підтримка кандидатів','Candidate support'),('#application?interest=spa-therapist','Загальна анкета SPA-терапевта','General spa therapist application')]),
    ('personal-trainer-employment','Тренер: наймана робота чи самозайнятість','Personal trainer: employment or self-employment?',
     'Однакова ціна тренування не означає однаковий дохід або однакові умови роботи.',
     'The same session price does not mean the same income or working conditions.', [
     ('З’ясуйте формат','Understand the arrangement','Уточніть, хто укладає договір із клієнтом, визначає розклад і ціну та відповідає за скасування занять. Назва «тренер» не визначає юридичний статус.','Ask who contracts with clients, sets prices and schedules, and handles cancellations. The title personal trainer does not determine employment status.'),
     ('Порівняйте витрати','Compare the costs','Врахуйте оренду, страхування, навчання, маркетинг і неоплачуваний час. Виручку від клієнтів не варто прирівнювати до зарплати найманого працівника.','Consider rent, insurance, training, marketing and unpaid time. Client revenue should not be treated as equivalent to an employee salary.'),
     ('Перевірте місцеві правила','Check local requirements','Правила оподаткування та визначення статусу залежать від країни. Перед підписанням договору перевірте офіційні джерела та за потреби зверніться до місцевого фахівця.','Tax and employment-status rules vary by country. Check official sources before signing and seek local professional advice where needed.')],
     [('jobs/personal-trainer/','Напрям персональних тренерів','Personal trainer roles'),('salary-guide/personal-trainer/','Структура оплати тренера','Trainer compensation')])]

for slug,uk,en,luk,len_,blocks,links in ARTICLES:
    add('blog/'+slug+'/',uk,en,luk,len_,blocks,links,True)

add('blog/','Поради з пошуку роботи та найму','Hiring and career advice',
    'Практичні матеріали для підготовки вакансії, резюме й розмови про умови.',
    'Practical resources for preparing a vacancy, CV and conversation about working conditions.', [
    ('Як користуватися матеріалами','Using these guides',
     'Оберіть тему відповідно до своєї задачі. Матеріали є загальними орієнтирами; конкретні вимоги та умови потрібно перевіряти для відповідної країни й роботодавця.',
     'Choose the guide that matches your task. These resources provide general guidance; check requirements and conditions for the relevant country and employer.')],
    [('blog/'+a[0]+'/',a[1],a[2]) for a in ARTICLES])

add('insights/','Орієнтири для найму у wellness-секторі','Spa, wellness and fitness hiring insights',
    'Як читати вакансії, оцінювати умови та відділяти факти від припущень.',
    'How to read vacancies, compare working conditions and distinguish evidence from assumptions.', [
    ('Не порівнюйте лише назви посад','Compare more than job titles',
     'Одна назва може означати різні процедури, повноваження й відповідальність. Для порівняння вакансій використовуйте обов’язки, кваліфікації, робочі години та географію.',
     'The same title can cover different treatments, authority and responsibilities. Compare duties, qualifications, hours and geography.'),
    ('Питайте про джерела цифр','Ask where figures come from',
     'Середня зарплата без країни, дати й опису вибірки не дає надійного орієнтиру. Уточнюйте, чи наведено базову оплату, повний дохід або виручку.',
     'An average salary without a country, date and sample description is not a reliable benchmark. Check whether a figure means base pay, total compensation or revenue.'),
    ('Вимоги до кваліфікації','Qualification requirements',
     'Визнання навчання й дозволи на практику залежать від країни та виду роботи. Для перевірки використовуйте офіційні органи відповідної країни, а не лише текст оголошення.',
     'Training recognition and permission to practise depend on the country and activity. Verify through the relevant official authority rather than relying only on a job advertisement.')],
    [('salary-guide/','Методика порівняння зарплат','Compensation methodology'),('employers/','Підготовка найму','Plan recruitment'),('blog/','Кар’єрні матеріали','Career resources')])

add('contact/','Контакти та запит на консультацію','Contact and consultation requests',
    'Напишіть команді Emplivo про вакансію, анкету або бажаний час розмови.',
    'Contact Emplivo about a hiring brief, an application or a preferred time to talk.', [
    ('Як зв’язатися','Contact the team',
     'Електронна пошта: hr@emplivo.com.ua. Телефон: +380 (67) 777 80 60. У запиті вкажіть тему, країну та зручний спосіб відповіді.',
     'Email: hr@emplivo.com.ua. Telephone: +380 (67) 777 80 60. Include your topic, country and preferred way to receive a reply.'),
    ('Узгодження консультації','Arranging a consultation',
     'Запропонуйте дату, час і часовий пояс у повідомленні. Консультація вважається погодженою лише після відповіді команди. Автоматичний календар бронювання ще не підключено.',
     'Suggest a date, time and time zone in your message. A consultation is only agreed after the team confirms it. An automated booking calendar is not connected yet.')],
    [('employers/','Послуги роботодавцям','Employer services'),('candidates/','Кандидатам','Candidate support')])

def url(path, lang):
    prefix = 'en/' if lang == 'en' else ''
    if path.startswith('#'):
        fragment, _, query = path[1:].partition('?')
        return '/' + prefix + ('?' + query if query else '') + '#' + fragment
    return '/' + prefix + path

def cards(links, lang):
    arrow='<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 18 18 6M6 6h12v12"/></svg>'
    return '<div class="seo-links">' + ''.join('<a class="seo-card" href="'+escape(url(p,lang),quote=True)+'">'+escape(en if lang=='en' else uk)+' '+arrow+'</a>' for p,uk,en in links) + '</div>'

def schema(path, title, lang, article=False):
    page_url=SITE + ('en/' if lang=='en' else '') + path
    graph=[{'@type':'Organization','@id':SITE+'#organization','name':'Emplivo','url':SITE,'email':'hr@emplivo.com.ua','telephone':'+380677778060'},
           {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Emplivo','item':SITE+('en/' if lang=='en' else '')},{'@type':'ListItem','position':2,'name':title,'item':page_url}]}]
    if article:
        graph.append({'@type':'Article','headline':title,'inLanguage':lang,'datePublished':DATE,'dateModified':DATE,'author':{'@id':SITE+'#organization'},'publisher':{'@id':SITE+'#organization'},'mainEntityOfPage':page_url})
    return json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<','\\u003c')

def form(lang):
    en=lang=='en'
    return '''<section class="seo-section" id="request"><h2>'''+('Prepare an email request' if en else 'Підготуйте запит електронною поштою')+'''</h2><p>'''+('Prepare your message, then open your email app or copy the text. This form does not send automatically or confirm a booking.' if en else 'Підготуйте повідомлення, потім відкрийте поштову програму або скопіюйте текст. Форма не надсилає лист автоматично й не підтверджує бронювання.')+'''</p>
<form id="email-request"><label>'''+('Topic' if en else 'Тема')+'''<select name="topic"><option value="employer">'''+('Hiring brief' if en else 'Запит на підбір')+'''</option><option value="temporary">'''+('Temporary staffing' if en else 'Тимчасове підсилення')+'''</option><option value="permanent">'''+('Permanent recruitment' if en else 'Постійний підбір')+'''</option><option value="opportunities">'''+('Future opportunities' if en else 'Майбутні можливості')+'''</option><option value="consultation">'''+('Consultation request' if en else 'Запит на консультацію')+'''</option></select></label>
<label>'''+('Role or subject' if en else 'Посада або питання')+'''<input name="role" maxlength="150" required></label>
<label>'''+('Location' if en else 'Локація')+'''<input name="location" maxlength="150" required></label>
<label>'''+('Your message, proposed time and time zone' if en else 'Повідомлення, бажаний час і часовий пояс')+'''<textarea name="message" rows="5" maxlength="3000" required></textarea></label>
<button class="button primary" type="submit">'''+('Prepare message' if en else 'Підготувати повідомлення')+'''</button>
<a class="button secondary" id="email-open" href="mailto:hr@emplivo.com.ua" target="_blank" rel="noopener noreferrer" hidden>'''+('Open email app' if en else 'Відкрити поштову програму')+'''</a>
<p id="request-status" role="status" aria-live="polite"></p><div id="email-fallback" hidden><p>'''+('If no email app opens, send the following text to hr@emplivo.com.ua:' if en else 'Якщо поштова програма не відкрилася, надішліть цей текст на hr@emplivo.com.ua:')+'''</p><textarea id="request-copy" readonly rows="7" aria-label="'''+('Email text' if en else 'Текст повідомлення')+'''"></textarea></div></form></section>'''

def render(page,lang):
    i=int(lang=='en');title=page['titles'][i];lead=page['leads'][i];path=page['path'];canonical=SITE+('en/' if i else '')+path
    t=lambda uk,en:en if i else uk
    nav=[('jobs/','Вакансії','Jobs'),('employers/','Роботодавцям','Employers'),('salary-guide/','Оплата','Compensation'),('blog/','Блог','Blog'),('contact/','Контакти','Contact')]
    other='uk' if i else 'en'
    body=''.join('<section class="seo-section"><h2>'+escape(b[i])+'</h2><p>'+escape(b[2+i])+'</p></section>' for b in page['blocks'])
    root='/' + ('en/' if i else '')
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Emplivo</title><meta name="description" content="{escape(lead,quote=True)}">
<meta name="theme-color" content="#0d233e"><link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="uk" href="{SITE+path}"><link rel="alternate" hreflang="en" href="{SITE+'en/'+path}"><link rel="alternate" hreflang="x-default" href="{SITE+path}">
<meta property="og:type" content="{'article' if page['article'] else 'website'}"><meta property="og:title" content="{escape(title,quote=True)}"><meta property="og:description" content="{escape(lead,quote=True)}"><meta property="og:url" content="{canonical}">
<link rel="stylesheet" href="/styles.css?v=20261112"><link rel="stylesheet" href="/modern.css?v=20261112"><link rel="stylesheet" href="/seo.css?v=20261112">
<script type="application/ld+json">{schema(path,title,lang,page['article'])}</script><script defer src="/seo.js?v=20261112"></script></head>
<body class="seo-page"><a class="skip" href="#main">{t('До основного вмісту','Skip to content')}</a>
<header class="seo-header"><div class="shell seo-nav"><a class="brand" href="{root}"><span class="brand-emblem" aria-hidden="true">E</span><span>EMPLIVO</span></a><nav aria-label="{t('Головна навігація','Main navigation')}">{''.join('<a href="'+url(p,lang)+'">'+escape(en if i else uk)+'</a>' for p,uk,en in nav)}</nav><a class="seo-language" lang="{other}" hreflang="{other}" href="{url(path,other)}">{'UA' if i else 'EN'}</a></div></header>
<main id="main"><div class="shell seo-content"><nav class="seo-breadcrumb" aria-label="{t('Навігаційний шлях','Breadcrumb')}"><a href="{root}">{t('Головна','Home')}</a><span aria-hidden="true"> / </span><span>{escape(title)}</span></nav>
<div class="seo-hero"><p class="eyebrow">EMPLIVO · SPA / WELLNESS / FITNESS</p><h1>{escape(title)}</h1><p class="seo-lead">{escape(lead)}</p></div>
{'<p class="seo-date">'+t('Опубліковано та переглянуто: ','Published and reviewed: ')+DATE+'</p>' if page['article'] else ''}
<div class="seo-columns"><div>{body}{form(lang) if path=='contact/' else ''}</div><aside class="seo-aside"><p class="eyebrow">{t('Наступний крок','Next step')}</p><h2>{t('Від інформації до дії','Make your next move')}</h2><p>{t('Оберіть відповідний напрям або зв’яжіться з командою.','Explore the relevant category or contact the team.')}</p>{cards(page['links'],lang)}</aside></div>
</div></main><footer class="seo-footer"><div class="shell"><a class="brand" href="{root}">EMPLIVO</a><p>{t('ТОВ «ЕМПЛІВО» · ЄДРПОУ 46615773','Emplivo LLC · Registration 46615773')}</p><a href="mailto:hr@emplivo.com.ua">hr@emplivo.com.ua</a> · <a href="tel:+380677778060">+380 (67) 777 80 60</a><nav>{''.join('<a href="'+url(p,lang)+'">'+escape(en if i else uk)+'</a>' for p,uk,en in [('candidates/','Кандидатам','Candidates'),('insights/','Галузеві матеріали','Industry insights'),('locations/ukraine/','Україна','Ukraine')])}</nav><p>© 2026 Emplivo</p></div></footer></body></html>'''

def build():
    for page in PAGES:
        for lang in ('uk','en'):
            dest=ROOT / ('en' if lang=='en' else '') / page['path'] / 'index.html'
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(render(page,lang),encoding='utf-8')
    urls=[SITE,SITE+'en/']+[SITE+prefix+p['path'] for p in PAGES for prefix in ('','en/')]
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join('<url><loc>'+escape(u)+'</loc></url>\n' for u in urls)+'</urlset>\n',encoding='utf-8')
    (ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: '+SITE+'sitemap.xml\n',encoding='utf-8')
    home=ROOT/'index.html'
    text=home.read_text(encoding='utf-8')
    # Generate a separately crawlable English homepage using the same application.
    dictionaries=json.loads(subprocess.check_output(['node','-e',"global.window={};require('./translations.js');process.stdout.write(JSON.stringify(window.EMPLIVO_TEXT));"],cwd=ROOT,text=True))
    en=dictionaries['en']
    def translate(m):
        return '<'+m['tag']+m['attrs']+'>'+escape(en.get(m['key'],m['text']))+'</'+m['tag']+'>'
    english=re.sub(r'<(?P<tag>[a-zA-Z0-9]+)(?P<attrs>[^>]*\bdata-i18n="(?P<key>[^"]+)"[^>]*)>(?P<text>.*?)</(?P=tag)>',translate,text,flags=re.S)
    def translate_attribute(m):
        tag=m[0]
        kind,key=m[1],m[2]
        attr='aria-label' if kind=='aria' else 'placeholder'
        if key in en:
            tag=re.sub(attr+r'="[^"]*"',attr+'="'+escape(en[key],quote=True)+'"',tag)
        return tag
    english=re.sub(r'<[^>]+data-i18n-(aria|placeholder)="([^"]+)"[^>]*>',translate_attribute,english)
    english=english.replace('lang="uk"','lang="en"',1)
    english=re.sub(r'<title>.*?</title>','<title>'+escape(en['pageTitle'])+'</title>',english)
    english=re.sub(r'<meta content="[^"]*" name="description"/>','<meta content="'+escape(en['metaDescription'],quote=True)+'" name="description"/>',english)
    english=english.replace('rel="canonical" href="'+SITE+'"','rel="canonical" href="'+SITE+'en/"')
    for asset in ('styles.css','modern.css','seo.css','translations.js','app.js','seo.js'):
        english=english.replace('"'+asset+'?','"/'+asset+'?')
    english=re.sub(r'data-route="([^"]*)" href="[^"]*"',lambda m:'data-route="'+m[1]+'" href="'+url(m[1],'en')+'"',english)
    out=ROOT/'en/index.html';out.parent.mkdir(exist_ok=True);out.write_text(english,encoding='utf-8')
    print(f'Built {len(PAGES)*2} editorial pages, English homepage, sitemap and robots.txt')

if __name__=='__main__':build()
