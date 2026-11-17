<?php
declare(strict_types=1);

// Run on the PHP server over SSH. No token in CLI arguments, URLs or console output.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
ini_set('display_errors', '0');
require_once dirname(__DIR__) . '/api/lib/TelegramBot.php';
require_once __DIR__ . '/TelegramPrivateConfig.php';
$command = $argv[1] ?? 'help';
if (!in_array($command, ['init', 'prepare', 'admin-id', 'check', 'diagnose', 'register', 'status', 'disable', 'cleanup'], true)) {
    echo "Usage: php tools/telegram_admin.php init|prepare|admin-id|check|diagnose|register|status|disable|cleanup [absolute-private-config-path]\n";
    exit($command === 'help' ? 0 : 1);
}
$stage = 'configuration';
try {
    if ($command === 'diagnose') {
        echo 'PHP: ' . PHP_VERSION . "\n";
        foreach (['curl', 'sodium'] as $extension) {
            echo $extension . ': ' . (extension_loaded($extension) ? 'OK' : 'MISSING') . "\n";
        }
        if (!extension_loaded('curl') || !extension_loaded('sodium')) {
            fwrite(STDERR, "Виберіть PHP із розширеннями cURL та Sodium і повторіть diagnose.\n");
            exit(1);
        }
    }
    $path = $argv[2] ?? dirname(__DIR__, 2) . '/emplivo-private/telegram.php';
    if ($command === 'init') {
        $token = trim((string) getenv('EMPLIVO_TELEGRAM_TOKEN'));
        putenv('EMPLIVO_TELEGRAM_TOKEN');
        \Emplivo\TelegramPrivateConfig::initialize($path, dirname(__DIR__), $token);
        unset($token);
        echo "Токен збережено приватно. Налаштування підготовлено.\nНаступна команда: php tools/telegram_admin.php admin-id\n";
        exit;
    }
    if (!is_readable($path)) { throw new RuntimeException('Missing config'); }
    if ($command === 'prepare') {
        \Emplivo\TelegramPrivateConfig::prepare($path, dirname(__DIR__));
        echo "Технічні налаштування збережені приватно. Токен не змінено.\nНаступна команда: php tools/telegram_admin.php admin-id\n";
        exit;
    }
    $config = \Emplivo\TelegramConfig::load($path);
    $adminConfigured = preg_match('/^[1-9][0-9]{0,15}$/D', (string) ($config['admin_chat_id'] ?? '')) === 1;
    if ($command === 'diagnose') {
        echo "Private PHP config: loaded\n";
        foreach (['bot_token', 'webhook_secret', 'state_key', 'group_url', 'site_url', 'state_dir'] as $field) {
            echo $field . ': ' . (is_string($config[$field] ?? null) && $config[$field] !== '' ? 'present' : 'MISSING') . "\n";
        }
        echo 'Manager chat ID: ' . ($adminConfigured ? 'configured' : 'not configured; use admin-id') . "\n";
    }
    if ($command === 'admin-id' || (!$adminConfigured && in_array($command, ['diagnose', 'check', 'status', 'disable'], true))) {
        // Bootstrap only: no sendMessage is called with this temporary value.
        $config['admin_chat_id'] = '1';
    }
    $stage = 'validate_configuration';
    $bot = new \Emplivo\TelegramBot($config);
    if ($command === 'cleanup') {
        echo 'Expired records deleted: ' . $bot->cleanup() . "\n";
        exit;
    }
    $stage = 'getMe';
    $me = $bot->call('getMe')['result'] ?? [];
    $username = (string) ($me['username'] ?? '');
    if (!preg_match('/^[A-Za-z][A-Za-z0-9_]{4,31}$/D', $username) || !preg_match('/bot$/iD', $username)) { throw new RuntimeException('Invalid bot'); }
    echo "Bot: @{$username}\n";
    if ($command === 'check') { echo "Private configuration and getMe: OK\n"; }
    if ($command === 'admin-id') {
        $stage = 'getWebhookInfo';
        $info = $bot->call('getWebhookInfo')['result'] ?? [];
        if (!empty($info['url'])) { throw new RuntimeException('Disable webhook before bootstrap'); }
        $challenge = bin2hex(random_bytes(8));
        echo "Open the bot in your PRIVATE Telegram chat and send: /id {$challenge}\nThen press Enter here.\n";
        fgets(STDIN);
        $matched = false;
        $stage = 'getUpdates';
        foreach (($bot->call('getUpdates', ['timeout' => 0, 'limit' => 100, 'allowed_updates' => ['message']])['result'] ?? []) as $update) {
            $m = $update['message'] ?? [];
            if (($m['text'] ?? '') === '/id ' . $challenge && ($m['chat']['type'] ?? '') === 'private'
                && ($m['from']['id'] ?? 0) === ($m['chat']['id'] ?? -1) && ($m['chat']['id'] ?? 0) > 0) {
                $config['admin_chat_id'] = (string) $m['chat']['id'];
                $stage = 'save_admin_id';
                \Emplivo\TelegramPrivateConfig::save($path, $config, dirname(__DIR__));
                echo 'ID особистого чату менеджера збережено: ' . $m['chat']['id'] . "\nНаступні команди: check, register, status.\n";
                $matched = true;
            }
        }
        if (!$matched) { throw new RuntimeException('Challenge not found; repeat before publishing the bot'); }
    }
    if ($command === 'register') {
        $stage = 'register';
        if (str_contains($config['site_url'], 'github.io')) { throw new RuntimeException('PHP hosting required'); }
        if (strcasecmp(ltrim((string) ($config['bot_username'] ?? ''), '@'), $username) !== 0) { throw new RuntimeException('Bot username mismatch'); }
        // Installing the webhook does not send any chat messages.
        $stage = 'setWebhook';
        $bot->call('setWebhook', [
            'url' => $config['site_url'] . '/api/telegram-webhook.php',
            'secret_token' => $config['webhook_secret'], 'allowed_updates' => ['message'], 'max_connections' => 1,
        ]);
        $stage = 'setMyCommands';
        $bot->call('setMyCommands', ['commands' => [
            ['command' => 'apply', 'description' => 'Анкета кандидата'],
            ['command' => 'jobs', 'description' => 'Вакансії та група'],
            ['command' => 'privacy', 'description' => 'Обробка даних'],
            ['command' => 'cancel', 'description' => 'Видалити чернетку'],
            ['command' => 'help', 'description' => 'Допомога'],
        ]]);
        echo "Webhook registered; max_connections=1. Verify status and test from your private chat.\n";
    }
    if (in_array($command, ['status', 'diagnose'], true)) {
        $stage = 'getWebhookInfo';
        $info = $bot->call('getWebhookInfo')['result'] ?? [];
        echo 'Webhook configured: ' . (!empty($info['url']) ? 'yes' : 'no') . "\n";
        echo 'URL matches this site: ' . (($info['url'] ?? '') === $config['site_url'] . '/api/telegram-webhook.php' ? 'yes' : 'no') . "\n";
        echo 'Pending updates: ' . (int) ($info['pending_update_count'] ?? 0) . "\n";
        echo 'Last delivery error (Unix time; 0=none): ' . (int) ($info['last_error_date'] ?? 0) . "\n";
        if ($command === 'diagnose' && !empty($info['url']) && !$adminConfigured) {
            echo "Webhook already configured. Bootstrap admin-id needs polling; inspect the existing setup before disabling its webhook.\n";
        }
    }
    if ($command === 'disable') {
        $stage = 'deleteWebhook';
        $bot->call('deleteWebhook', ['drop_pending_updates' => false]);
        echo "Webhook disabled; pending updates preserved.\n";
    }
} catch (\Emplivo\TelegramTransportException $error) {
    fwrite(STDERR, 'Telegram API stage: ' . $stage . '; cURL=' . $error->curlCode . '; HTTP=' . $error->httpStatus . '; API=' . $error->apiCode . "\n");
    $hint = match (true) {
        $error->curlCode === 6 => 'DNS не знаходить api.telegram.org на хостингу.',
        $error->curlCode === 7 => 'Не вдалося з’єднатися з api.telegram.org:443.',
        $error->curlCode === 28 => 'Час очікування Telegram вичерпано. Перевірте вихідний HTTPS хостингу.',
        in_array($error->curlCode, [35, 60], true) => 'Помилка TLS або сертифікатів CA. Перевірте налаштування PHP cURL.',
        $error->httpStatus === 401 => 'Telegram відхилив токен. Перевірте, що збережено новий токен після відкликання.',
        $error->httpStatus === 404 => 'Telegram не знайшов бота або запит. Перевірте новий токен через приховане введення.',
        $error->httpStatus === 409 => 'Конфлікт getUpdates: уже працює webhook або інший процес опитування цього бота.',
        $error->httpStatus === 429 => 'Telegram тимчасово обмежив частоту запитів. Повторіть після паузи.',
        default => 'Надішліть цей рядок із кодами для подальшої діагностики.',
    };
    fwrite(STDERR, $hint . "\n");
    if ($error->retryAfter > 0) { fwrite(STDERR, 'Retry after seconds: ' . $error->retryAfter . "\n"); }
    exit(1);
} catch (\Emplivo\TelegramConfigException $error) {
    fwrite(STDERR, "Неправильний формат приватного telegram.php. Файл має починатися з <?php і повертати масив. Вміст приховано. Скористайтеся: bash tools/telegram_init.sh\n");
    exit(1);
} catch (Throwable $error) {
    // Details intentionally exclude API responses and secrets.
    $hints = [
        'Missing config' => 'Приватний telegram.php відсутній або недоступний для читання.',
        'Disable webhook before bootstrap' => 'Webhook уже встановлено. Перевірте status; admin-id потребує вільного getUpdates.',
        'Challenge not found; repeat before publishing the bot' => 'Одноразову команду не знайдено. Повторіть admin-id, надішліть нову /id … у приватний чат бота й натисніть Enter.',
        'Bot username mismatch' => 'Username у приватній конфігурації відрізняється від username бота, показаного вище.',
        'Telegram configuration incomplete' => 'Налаштування неповні або мають неправильний формат. Виконайте diagnose.',
        'Telegram transport unavailable' => 'PHP cURL недоступний для запитів Telegram.',
    ];
    fwrite(STDERR, 'Setup stage: ' . $stage . "\n" . ($hints[$error->getMessage()] ?? 'Не вдалося завершити етап. Виконайте php tools/telegram_admin.php diagnose і надішліть його результат.') . "\n");
    exit(1);
}
