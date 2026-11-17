<?php
declare(strict_types=1);

ini_set('display_errors', '0');
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function telegramResponse(int $status): never
{
    http_response_code($status);
    echo json_encode(['ok' => $status === 200]);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { header('Allow: POST'); telegramResponse(405); }
if (!str_starts_with(strtolower($_SERVER['CONTENT_TYPE'] ?? ''), 'application/json')) { telegramResponse(415); }
if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 65536) { telegramResponse(413); }

try {
    $configPath = dirname(__DIR__, 2) . '/emplivo-private/telegram.php';
    if (!is_readable($configPath)) { telegramResponse(503); }
    require_once __DIR__ . '/lib/TelegramConfig.php';
    $config = \Emplivo\TelegramConfig::load($configPath);
    $secret = (string) ($config['webhook_secret'] ?? '');
    if (strlen($secret) < 32) { telegramResponse(503); }
    $provided = (string) ($_SERVER['HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'] ?? '');
    if (!hash_equals($secret, $provided)) { telegramResponse(403); }
    $body = file_get_contents('php://input', false, null, 0, 65537);
    if ($body === false || strlen($body) > 65536) { telegramResponse(413); }
    $update = json_decode($body, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($update) || !is_int($update['update_id'] ?? null)) { telegramResponse(400); }
    require_once __DIR__ . '/lib/TelegramBot.php';
    (new \Emplivo\TelegramBot($config))->handle($update);
    telegramResponse(200);
} catch (JsonException $error) {
    telegramResponse(400);
} catch (Throwable $error) {
    error_log('Emplivo Telegram webhook failed; inspect private configuration and connectivity.');
    telegramResponse(503);
}
