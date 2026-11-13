# Поточний стан — Wellness release, 12.11.2026

Погоджене оформлення інтегровано локально: 64 HTML-сторінки, 1162 внутрішні
посилання, 44 індексовані sitemap URL. Пакет: emplivo-wellness-site.zip.
Загальна анкета — реальна; demo-job відгуки локальні. У браузерних тестах
підтверджено retry/idempotency з контрольованими відповідями, без робочих записів.
Новий номер: +380 (67) 777 80 60.

На домен ще не завантажено: очікуються SFTP host/port/username/path та
доступність відповідного мережевого маршруту. SSH-ключ створено окремо
поза документ-коренем; його відбиток підтверджено користувачем.

Попередній план контенту й інтеграцій наведено нижче.

# Emplivo SEO delivery — 12 November 2026

## Implemented

- Homepage and PHP general-application flow preserved; original kitchen-helper vacancy removed. Six explicitly fictional jobs, three fictional employer advertisements and a crawlable English homepage added.
- 54 HTML pages in total, including four service pages, three role guides, a job category hub, a supported Ukraine location page, four compensation pages, three career/hiring articles, blog/insights hubs and contact page, all in Ukrainian and English.
- Unique titles, descriptions, canonical URLs, reciprocal hreflang, XML sitemap and robots.txt.
- Organization and breadcrumb JSON-LD; Article markup only on actual dated articles.
- Demo job and employer detail pages are noindex and excluded from the sitemap. No JobPosting, Review or AggregateRating markup is emitted for fictional data.
- Compensation methodology and offer checklists without invented salary figures.
- Employer brief and consultation request preparation by mailto, with manual-copy fallback and explicit notice that sending/booking is not automatic.
- Event adapter for application starts/success, job saves and prepared email requests. No analytics vendor is loaded; dataLayer forwarding is opt-in through `window.emplivoAnalyticsEnabled = true` after consent configuration. No names, emails, CVs, free text or query strings enter events.

## Dependencies still required

1. **Hosting deployment:** authorised panel/SFTP access is not available in the cloud machine. Upload only the tested release's www contents to the existing PHP document root. No GitHub push is part of this deployment.
2. **New vacancy inventory:** supply verified role, location, employer, original date, expiry and pay before adding live spa/fitness/wellness jobs and JobPosting markup.
3. **Automated alerts:** matching backend, consent/confirmation, email delivery and unsubscribe are not configured. The site offers a clearly labelled email enquiry instead.
4. **Employer posting and application management:** accounts, moderation, storage, access controls and notifications require a separate implementation. An email brief does not publish a job or create an employer dashboard.
5. **Calendar booking:** provide an approved scheduling integration. The current contact page prepares a request; it does not claim a reservation.
6. **Salary figures:** supply attributable sources, geography, collection period, sample size and rights to use the data.
7. **Case studies / Google Reviews:** supply approved real cases and the genuine Google Business Profile/review source. No invented testimonials or self-serving review-star markup are published.
8. **Analytics:** provide an approved analytics property and consent configuration; connect the CRM and booking confirmation source before measuring those conversions.
9. **Location expansion:** publish new city pages only with supported service coverage, real demand and useful unique information.

## Six-month editorial backlog

P1 supports an immediate conversion; P2 expands coverage after core journeys work.

| Month | Priority | Topic / keyword | Format | Destination | Required evidence |
|---|---|---|---|---|---|
| 1 | P1 | spa therapist recruitment | Hiring brief guide; initial version shipped | /employers/, /jobs/spa-therapist/ | Team review and actual screening process |
| 1 | P1 | spa therapist salary [market] | Expand compensation guide | /salary-guide/spa-therapist/ | Verified sources, period, sample and geography |
| 1 | P1 | spa therapist CV | Checklist; initial version shipped | /candidates/, general application | Recruiter review; no unsupported credential claims |
| 2 | P1 | employed vs self-employed personal trainer | Explainer; initial version shipped | /jobs/personal-trainer/ | Destination-country official sources before local legal detail |
| 2 | P1 | personal trainer salary [market] | Expand compensation guide | /salary-guide/personal-trainer/ | Separate base pay, commission, rent and revenue |
| 2 | P1 | temporary spa staffing case study | Approved case study | /employers/temporary-recruitment/ | Client permission and documented outcome |
| 3 | P1 | wellness manager recruitment | Hiring guide | /employers/permanent-recruitment/ | Actual role briefs and assessment criteria |
| 3 | P1 | wellness manager salary [market] | Expand compensation guide | /salary-guide/wellness-manager/ | Verified seniority/property-context data |
| 3 | P2 | spa jobs [priority city] | Local market guide | Evidence-supported location page | Live jobs and official local evidence |
| 4 | P1 | seasonal spa recruitment | Planning guide | /employers/temporary-recruitment/ | Actual demand patterns and briefs |
| 4 | P1 | spa therapist interview questions | Candidate guide | /jobs/spa-therapist/ | Recruiter and hiring-manager input |
| 4 | P2 | spa and fitness salary guide | Evidence review/update | /salary-guide/ | New verified observations; do not refresh dates cosmetically |
| 5 | P1 | wellness recruitment case study | Approved case study | /employers/permanent-recruitment/ | Permission, dates, actual outcomes |
| 5 | P1 | personal trainer job advert | Employer template | /employers/ | Accurate contract and compensation requirements |
| 5 | P2 | spa and fitness qualifications | Industry article | Relevant role hubs | Disclosed vacancy sample and official jurisdiction sources |
| 6 | P1 | [role] salary [market] | Role guide refresh | Existing salary guides | Sufficient new observations |
| 6 | P1 | fitness recruitment case study | Approved case study | /employers/ | Documented client evidence and consent |
| 6 | P2 | spa and fitness recruitment trends | Industry report | /insights/, employer and role hubs | Usable historical data with limitations |

## Measurement

Establish a reliable baseline before numerical targets. Report organic entry pages by service/role/location; confirmed applications per listing and application-start completion; qualified candidate outcomes; confirmed alert subscriptions after implementation; published employer jobs; qualified employer enquiries; confirmed consultations and CRM outcomes. A prepared email or a CTA click is not a lead or booking confirmation.

Review failures weekly, conversions monthly, and salary/local content quarterly. Do not transmit personal data or unrestricted site searches to analytics.

## Rebuild

Run `python tools/build_demo.py` from this checkout. The command is offline and deterministic; it regenerates editorial pages, the English homepage, sitemap and robots.txt. The Ukrainian homepage and shared application remain hand-maintained.

## Latest requested changes

Emplivo contact number is +380 (67) 777 80 60 (tel/schema: +380677778060). The six fictional jobs have complete descriptions, pay, location, dates, requirements, duties, benefits and reserved .example contacts. Fictional salaries are not market evidence. Browser tests demonstrate zero API calls for demo applications; the PHP gateway separately rejects demo roles before loading production credentials. General applications remain a separate real flow.
