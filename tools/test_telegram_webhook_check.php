<?php
declare(strict_types=1);

require_once __DIR__ . '/TelegramWebhookCheck.php';
function webhookCheck(bool $value, string $reason): void { if (!$value) { throw new RuntimeException($reason); } }
$marker = 'SYNTHETIC_PRIVATE_MARKER';
webhookCheck(\Emplivo\TelegramWebhookCheck::deliveryFailure('Wrong response from the webhook: 403 Forbidden ' . $marker) === 'HTTP 403', 'HTTP failure classified without raw response');
webhookCheck(\Emplivo\TelegramWebhookCheck::deliveryFailure('SSL error: ' . $marker) === 'TLS/certificate failure', 'TLS failure classified');
webhookCheck(!str_contains(\Emplivo\TelegramWebhookCheck::deliveryFailure($marker), $marker), 'Unknown errors hidden');
$calls = [];
$rows = \Emplivo\TelegramWebhookCheck::probe(['site_url' => 'https://www.emplivo.com.ua', 'webhook_secret' => $marker],
    function (string $url, string $method, string $secret) use (&$calls, $marker): array {
        $calls[] = $method;
        webhookCheck($url === 'https://www.emplivo.com.ua/api/telegram-webhook.php', 'Only the configured endpoint is probed');
        webhookCheck($secret === ($method === 'POST' ? $marker : ''), 'Secret sent only on authenticated POST');
        if ($method === 'GET') {
            return ['status' => 301, 'curl' => 0, 'handler' => false, 'redirect' => 'https://emplivo.com.ua/api/telegram-webhook.php', 'body' => $marker];
        }
        return ['status' => 200, 'curl' => 0, 'handler' => true, 'body' => json_encode([
            'probe' => 'emplivo-webhook', 'php' => $marker, 'bot_token' => $marker,
            'checks' => ['curl' => $marker, 'sodium' => true, 'state_writable' => false],
        ])];
    });
webhookCheck($calls === ['GET', 'POST'], 'Exactly two non-message probes');
webhookCheck($rows[0]['redirect_to'] === 'apex host', 'Known redirect classified');
webhookCheck(!isset($rows[1]['php']) && !isset($rows[1]['checks']['curl']), 'Untrusted runtime text excluded');
webhookCheck($rows[1]['checks'] === ['sodium' => true, 'state_writable' => false], 'Only boolean health checks retained');
webhookCheck(!str_contains(json_encode($rows), $marker), 'No secret, response body or arbitrary text in report');
try {
    \Emplivo\TelegramWebhookCheck::probe(['site_url' => 'https://evil.example', 'webhook_secret' => $marker], fn () => []);
    throw new LogicException('Unexpected destination accepted');
} catch (RuntimeException $expected) { /* Destination allowlist enforced. */ }
echo "PASS: safe delivery error classification, fixed endpoint probes, secret isolation, redirect/runtime filtering and destination allowlist. No network calls.\n";
