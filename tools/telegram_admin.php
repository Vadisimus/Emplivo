<?php
declare(strict_types=1);

// Run on the PHP server over SSH. No token in CLI arguments, URLs or console output.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
ini_set('display_errors', '0');
require_once dirname(__DIR__) . '/api/lib/TelegramBot.php';
require_once __DIR__ . '/TelegramPrivateConfig.php';
$command = $argv[1] ?? 'help';
if (!in_array($command, ['prepare', 'admin-id', 'check', 'register', 'status', 'disable', 'cleanup'], true)) {
    echo "Usage: php tools/telegram_admin.php prepare|admin-id|check|register|status|disable|cleanup [absolute-private-config-path]\n";
    exit($command === 'help' ? 0 : 1);
}
try {
    $path = $argv[2] ?? dirname(__DIR__, 2) . '/emplivo-private/telegram.php';
    if (!is_readable($path)) { throw new RuntimeException('Missing config'); }
    if ($command === 'prepare') {
        \Emplivo\TelegramPrivateConfig::prepare($path, dirname(__DIR__));
        echo "Технічні налаштування збережені приватно. Токен не змінено.\nНаступна команда: php tools/telegram_admin.php admin-id\n";
        exit;
    }
    $config = require $path;
    if ($command === 'admin-id') {
        // Bootstrap only: no sendMessage is called with this temporary value.
        $config['admin_chat_id'] = '1';
    }
    $bot = new \Emplivo\TelegramBot($config);
    if ($command === 'cleanup') {
        echo 'Expired records deleted: ' . $bot->cleanup() . "\n";
        exit;
    }
    $me = $bot->call('getMe')['result'] ?? [];
    $username = (string) ($me['username'] ?? '');
    if (!preg_match('/^[A-Za-z][A-Za-z0-9_]{4,31}$/D', $username) || !preg_match('/bot$/iD', $username)) { throw new RuntimeException('Invalid bot'); }
    echo "Bot: @{$username}\n";
    if ($command === 'check') { echo "Private configuration and getMe: OK\n"; }
    if ($command === 'admin-id') {
        $info = $bot->call('getWebhookInfo')['result'] ?? [];
        if (!empty($info['url'])) { throw new RuntimeException('Disable webhook before bootstrap'); }
        $challenge = bin2hex(random_bytes(8));
        echo "Open the bot in your PRIVATE Telegram chat and send: /id {$challenge}\nThen press Enter here.\n";
        fgets(STDIN);
        $matched = false;
        foreach (($bot->call('getUpdates', ['timeout' => 0, 'limit' => 100, 'allowed_updates' => ['message']])['result'] ?? []) as $update) {
            $m = $update['message'] ?? [];
            if (($m['text'] ?? '') === '/id ' . $challenge && ($m['chat']['type'] ?? '') === 'private'
                && ($m['from']['id'] ?? 0) === ($m['chat']['id'] ?? -1) && ($m['chat']['id'] ?? 0) > 0) {
                $config['admin_chat_id'] = (string) $m['chat']['id'];
                \Emplivo\TelegramPrivateConfig::save($path, $config, dirname(__DIR__));
                echo 'ID особистого чату менеджера збережено: ' . $m['chat']['id'] . "\nНаступні команди: check, register, status.\n";
                $matched = true;
            }
        }
        if (!$matched) { throw new RuntimeException('Challenge not found; repeat before publishing the bot'); }
    }
    if ($command === 'register') {
        if (str_contains($config['site_url'], 'github.io')) { throw new RuntimeException('PHP hosting required'); }
        if (strcasecmp(ltrim((string) ($config['bot_username'] ?? ''), '@'), $username) !== 0) { throw new RuntimeException('Bot username mismatch'); }
        // Installing the webhook does not send any chat messages.
        $bot->call('setWebhook', [
            'url' => $config['site_url'] . '/api/telegram-webhook.php',
            'secret_token' => $config['webhook_secret'], 'allowed_updates' => ['message'], 'max_connections' => 1,
        ]);
        $bot->call('setMyCommands', ['commands' => [
            ['command' => 'apply', 'description' => 'Анкета кандидата'],
            ['command' => 'jobs', 'description' => 'Вакансії та група'],
            ['command' => 'privacy', 'description' => 'Обробка даних'],
            ['command' => 'cancel', 'description' => 'Видалити чернетку'],
            ['command' => 'help', 'description' => 'Допомога'],
        ]]);
        echo "Webhook registered; max_connections=1. Verify status and test from your private chat.\n";
    }
    if ($command === 'status') {
        $info = $bot->call('getWebhookInfo')['result'] ?? [];
        echo 'Webhook configured: ' . (!empty($info['url']) ? 'yes' : 'no') . "\n";
        echo 'URL matches this site: ' . (($info['url'] ?? '') === $config['site_url'] . '/api/telegram-webhook.php' ? 'yes' : 'no') . "\n";
        echo 'Pending updates: ' . (int) ($info['pending_update_count'] ?? 0) . "\n";
        echo 'Last delivery error (Unix time; 0=none): ' . (int) ($info['last_error_date'] ?? 0) . "\n";
    }
    if ($command === 'disable') {
        $bot->call('deleteWebhook', ['drop_pending_updates' => false]);
        echo "Webhook disabled; pending updates preserved.\n";
    }
} catch (Throwable $error) {
    // Details intentionally exclude API responses and secrets.
    fwrite(STDERR, "Telegram setup failed. Check private config, PHP cURL/sodium, permissions, network and command prerequisites in TELEGRAM_UA.md.\n");
    exit(1);
}
