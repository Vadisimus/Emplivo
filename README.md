# Emplivo

Мультигалузевий сайт вакансій і рекрутингу ТОВ «ЕМПЛІВО», ЄДРПОУ 46615773.
Українська версія живе в корені, англійська — у `/en/`, російська — у `/ru/`.
Готовий HTML працює на [GitHub Pages](https://vadisimus.github.io/Emplivo/) і
[PHP-хостингу](https://www.emplivo.com.ua/).

## Збірка та редагування

Потрібен Python 3.12+ і дані часових поясів. На Windows, якщо `Europe/Kyiv`
відсутній, установіть пакет `tzdata` у середовище Python.

```sh
python tools/build_vacancies.py
python -m http.server 8080
```

- `content/vacancies.json` містить перевірені оголошення й погоджені вакансії.
- `tools/site_layout.py` генерує єдину навігацію, футер, метадані, крихти та посилання між мовами.
- `tools/site_pages.py` і `tools/site_catalog.py` генерують головну, форми, каталог, збережені, контакти й галузеві хаби.
- Редакційний текст зберігається у відповідних `index.html` української, англійської та російської версій. Під час збірки внутрішній контент зберігається, спільний шаблон оновлюється.
- `design.css`, `navigation.mjs`, `jobs.mjs` і `intake.mjs` оформлюють і доповнюють статичний HTML.
- `api/` містить поточні PHP-обробники. `worker/` розгортається окремо від сайту.

Інструкція для редактора вакансій міститься у [VACANCIES_UA.md](docs/VACANCIES_UA.md).

## Форми й розгортання

[Налаштування Cloudflare Worker і перенесення в Git](docs/MODERNIZATION_RU.md).
Публічний Turnstile site key та HTTPS-origin Worker записуються в
`intake-config.mjs`. Доступ до Telegram, секрет Turnstile та ID закритого
чату зберігаються у секретах Worker. PHP-хостинг зберігає чинну форму
загального відгуку, якщо Worker ще не налаштовано. На Pages у цьому випадку
форма показує посилання на Telegram або контакти.

Порядок встановлення PHP-пакета описано в [PHP_HOSTING_DEPLOY_UA.md](docs/PHP_HOSTING_DEPLOY_UA.md).
Telegram webhook має окрему [інструкцію](TELEGRAM_UA.md).

## Перевірки

```sh
node tools/verify_github_pages.cjs
```

Для браузерних перевірок потрібні Node.js, Playwright і Chromium.
Скрипт запускає сайт з префіксом `/Emplivo/`, підміняє відповіді API
та перевіряє меню, форми, валютні фільтри й збережені вакансії.
