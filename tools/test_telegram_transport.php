<?php
declare(strict_types=1);

namespace Emplivo {
    // Namespace-local cURL fixtures intercept the real transport's calls.
    function curl_init(string $url): object { return (object) ['options' => []]; }
    function curl_setopt_array(object $handle, array $options): bool
    { $GLOBALS['emplivo_transport_options'] = $options; return true; }
    function curl_exec(object $handle): string|false { return $GLOBALS['emplivo_transport_fixture']['body']; }
    function curl_getinfo(object $handle, int $key): int { return $GLOBALS['emplivo_transport_fixture']['status']; }
    function curl_errno(object $handle): int { return $GLOBALS['emplivo_transport_fixture']['curl']; }
    function curl_close(object $handle): void {}
}

namespace {
    require_once dirname(__DIR__) . '/api/lib/TelegramBot.php';
    function transportCheck(bool $value, string $reason): void { if (!$value) { throw new RuntimeException($reason); } }
    $dir = sys_get_temp_dir() . '/emplivo-transport-' . bin2hex(random_bytes(6));
    $config = [
        'bot_token' => '123456789:' . str_repeat('TEST_ONLY_', 4), 'admin_chat_id' => '1234567',
        'state_key' => base64_encode(random_bytes(32)), 'webhook_secret' => str_repeat('test_secret_', 4),
        'group_url' => 'https://t.me/+AbCdeFGhIjKlmN01', 'site_url' => 'https://www.emplivo.com.ua', 'state_dir' => $dir,
    ];
    $GLOBALS['emplivo_transport_fixture'] = ['body' => '{"ok":true,"result":{}}', 'status' => 200, 'curl' => 0];
    try {
        $bot = new \Emplivo\TelegramBot($config);
        $bot->call('getMe');
        transportCheck($GLOBALS['emplivo_transport_options'][CURLOPT_POSTFIELDS] === '{}', 'Empty Bot API parameters must be a JSON object');
        $bot->call('getWebhookInfo');
        transportCheck(json_decode($GLOBALS['emplivo_transport_options'][CURLOPT_POSTFIELDS]) instanceof stdClass, 'Metadata request has an object root');
        $payload = ['chat_id' => 1234567, 'text' => 'Local fixture', 'reply_markup' => ['keyboard' => [[['text' => 'Cancel']]]]];
        $bot->call('sendMessage', $payload);
        transportCheck(json_decode($GLOBALS['emplivo_transport_options'][CURLOPT_POSTFIELDS], true) === $payload, 'Message fields and nested keyboard arrays preserved');
        $secret = 'SYNTHETIC_PRIVATE_RESPONSE_MARKER';
        foreach ([
            ['body' => json_encode(['ok' => false, 'error_code' => 401, 'description' => $secret]), 'status' => 401, 'curl' => 0, 'api' => 401, 'retry' => 0],
            ['body' => false, 'status' => 0, 'curl' => 28, 'api' => 0, 'retry' => 0],
            ['body' => json_encode(['ok' => false, 'error_code' => 429, 'description' => $secret, 'parameters' => ['retry_after' => 12]]), 'status' => 429, 'curl' => 0, 'api' => 429, 'retry' => 12],
        ] as $fixture) {
            $GLOBALS['emplivo_transport_fixture'] = $fixture;
            try { $bot->call('getMe'); throw new LogicException('Expected transport error'); }
            catch (\Emplivo\TelegramTransportException $error) {
                transportCheck($error->curlCode === $fixture['curl'] && $error->httpStatus === $fixture['status'] && $error->apiCode === $fixture['api'] && $error->retryAfter === $fixture['retry'], 'Safe transport codes preserved');
                transportCheck(!str_contains($error->getMessage(), $secret) && !str_contains($error->getMessage(), $config['bot_token']), 'Response text and token excluded from errors');
            }
        }
        echo "PASS: object-root Bot API JSON, nested message data, safe cURL/HTTP/API codes, retry timing and no response/token disclosure. All cURL calls mocked.\n";
    } finally { if (is_dir($dir)) { rmdir($dir); } }
}
