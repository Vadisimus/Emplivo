# Ветка модернизации Emplivo

Исходный код включает единое оформление, три локали, каталог, сохранённые
вакансии, отраслевые хабы, формы и Worker. HTML формируется через общий
Python-шаблон. Вакансии обновляются из `content/vacancies.json`.
Сборка сохраняет действующие публичные URL.

## Импорт в локальный клон на Windows

Распакуйте комплект `Emplivo-Refactor-Plan-and-Code.zip` и откройте в этой
папке PowerShell. Укажите путь к вашему клону Emplivo.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Update-EmplivoRepository.ps1 -Repository "C:\Users\WorkStation\source\Emplivo" -Archive "$env:USERPROFILE\Downloads\Emplivo-Refactor-Plan-and-Code.zip" -Push
```

Скрипт создаёт `refactor/modernization` из проверенного Git bundle и сохраняет
порядок коммитов. При наличии локальной ветки применяется только
fast-forward. Параметр `-Push` отправляет результат в ту же ветку на origin.
Путь к архиву можно опустить, чтобы импортировать ветку напрямую из origin.
Используйте свою обычную учётную запись Git. Для HTTPS с PAT нужны права
`Contents: Read and write` только на репозиторий Emplivo. Вводите PAT в
Git Credential Manager, если Git запросит его. Токен Telegram не участвует
в Git-операциях.

## Подключение Worker

1. В Cloudflare подготовьте закрытый чат рекрутеров, бота с правом отправлять
   документы в чат и Turnstile для `vadisimus.github.io` и
   `www.emplivo.com.ua`. Для теста используйте отдельный чат и D1.
2. В папке `worker` скопируйте `wrangler.toml.example` в `wrangler.toml`.
   Создайте D1 командой `npx wrangler d1 create emplivo-intake` и внесите
   полученный `database_id`. Укажите разрешённые origin и версию политики.
   В `EMPLIVO_VACANCY_IDS` перечислите через запятую только активные вакансии,
   на которые Emplivo уполномочено собирать отклики.
3. Выполните `npx wrangler d1 execute emplivo-intake --remote --file=schema.sql`
   и `npx wrangler deploy`. Задайте секреты через команды ниже. Worker
   возвращает 503 до заполнения секретов.

   ```sh
   npx wrangler secret put TELEGRAM_BOT_TOKEN
   npx wrangler secret put TELEGRAM_PRIVATE_CHAT_ID
   npx wrangler secret put TURNSTILE_SECRET_KEY
   ```

4. В корне проекта настройте публичный origin и site key. Укажите фактические
   значения Worker и Turnstile. Команда обновляет `intake-config.mjs` и его контрольную сумму.

   ```sh
   python tools/configure_intake.py --worker-origin "https://emplivo-intake.example.workers.dev" --site-key "PUBLIC_SITE_KEY"
   ```

   Те же значения можно передать скрипту импорта через `-WorkerOrigin` и
   `-TurnstileSiteKey`. Он создаст отдельный коммит с настройками.
5. На тестовом сайте отправьте синтетические PDF/DOCX и бриф. Успех
   подтверждается номером обращения после принятия сообщения Telegram.
   Проверьте защиту от повторов, лимит 5 МБ и юридические условия обработки
   данных перед приёмом реальных CV. D1 держит состояния доставки в течение
   семи дней; отдельные правила хранения CV действуют для закрытого чата.

Реальные секреты и конфигурация среды в ZIP не входят.
До подключения Worker на GitHub Pages доступны Telegram для кандидатов и
контакты агентства. На текущем PHP-хостинге общая анкета использует
существующий PHP endpoint, если Worker ещё не задан.
