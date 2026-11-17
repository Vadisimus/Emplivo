<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/api/lib/TelegramBot.php';
function check(bool $value, string $label): void { if (!$value) { throw new RuntimeException($label); } }
$dir = sys_get_temp_dir() . '/emplivo-telegram-test-' . bin2hex(random_bytes(6));
$config = [
    'state_key' => base64_encode(random_bytes(32)), 'state_dir' => $dir,
    'admin_chat_id' => '999888777', 'bot_token' => '123456789:' . str_repeat('x', 35),
    'webhook_secret' => str_repeat('test_secret_', 4), 'group_url' => 'https://t.me/EmplivoGroupExample',
    'site_url' => 'https://www.emplivo.com.ua',
];
$calls = []; $failAdmin = false; $failReceipt = false;
$transport = function (string $method, array $payload) use (&$calls, &$failAdmin, &$failReceipt): array {
    check($method === 'sendMessage', 'Only mocked sendMessage expected');
    if ($failAdmin && $payload['chat_id'] === 999888777) { $failAdmin = false; throw new RuntimeException('simulated outage'); }
    if ($failReceipt && $payload['chat_id'] === 1234567 && str_contains($payload['text'], 'передано в особистий')) { $failReceipt = false; throw new RuntimeException('simulated receipt failure'); }
    $calls[] = $payload;
    return ['ok' => true, 'result' => ['message_id' => count($calls)]];
};
$sequence = 0;
$message = function (string $text, string $type = 'private') use (&$sequence): array {
    return ['update_id' => ++$sequence, 'message' => ['chat' => ['id' => 1234567, 'type' => $type], 'from' => ['id' => 1234567, 'is_bot' => false], 'text' => $text]];
};
$last = function () use (&$calls): string { return $calls[array_key_last($calls)]['text']; };
try {
    $bad = $config; $bad['admin_chat_id'] = '-1001234567';
    try { new \Emplivo\TelegramBot($bad, $transport); throw new LogicException('Negative group ID accepted'); }
    catch (RuntimeException $expected) { check(!($expected instanceof LogicException), 'Group destination rejected'); }
    $bot = new \Emplivo\TelegramBot($config, $transport);
    $inviteConfig = $config; $inviteConfig['group_url'] = 'https://t.me/+AbCdeFGhIjKlmN01';
    new \Emplivo\TelegramBot($inviteConfig, $transport);
    $bot->handle($message('/apply', 'supergroup'));
    check($calls === [], 'No replies or application data in groups');
    $bot->handle($message('/apply'));
    check(str_contains($last(), 'Погоджуюсь'), 'Consent required');
    $bot->handle($message('Test Name'));
    check(str_contains($last(), 'потрібна згода'), 'Cannot skip consent');
    foreach (['Погоджуюсь', 'Тестовий Кандидат', 'not-a-contact'] as $text) { $bot->handle($message($text)); }
    check(str_contains($last(), 'Перевірте email'), 'Invalid contact rejected');
    foreach (['+380 (67) 777-80-60', 'SPA-терапевт', 'Київ', 'Навчання та практика масажу.'] as $text) { $bot->handle($message($text)); }
    check(str_contains($last(), 'Перевірте анкету'), 'Review before transmission');
    check(count(array_filter($calls, fn ($c) => $c['chat_id'] === 999888777)) === 0, 'Nothing sent before confirmation');
    $files = glob($dir . '/*.bin');
    check(count($files) === 1, 'One encrypted session');
    $encrypted = file_get_contents($files[0]);
    check(!str_contains($encrypted, 'Кандидат') && !str_contains($encrypted, '7778060'), 'No plaintext PII in state');
    check((fileperms($files[0]) & 0777) === 0600 && (fileperms($dir) & 0777) === 0700, 'Private state permissions');
    $submit = $message('Надіслати заявку'); $failAdmin = true;
    try { $bot->handle($submit); throw new LogicException('Expected transport failure'); }
    catch (RuntimeException $expected) { check(!($expected instanceof LogicException), 'Transport failure propagates'); }
    check(!str_contains($last(), 'передано в особистий'), 'No false success after failed admin delivery');
    $failReceipt = true;
    try { $bot->handle($submit); throw new LogicException('Expected receipt failure'); }
    catch (RuntimeException $expected) { check(!($expected instanceof LogicException), 'Receipt failure propagates'); }
    check(count(array_filter($calls, fn ($c) => $c['chat_id'] === 999888777)) === 1, 'One accepted notification');
    $bot->handle($submit);
    check(str_contains($last(), 'передано в особистий'), 'Receipt sent after admin acknowledgment');
    $count = count($calls); $bot->handle($submit);
    check(count($calls) === $count, 'Repeated update acknowledged without repeated messages');
    check(count(array_filter($calls, fn ($c) => $c['chat_id'] === 999888777)) === 1, 'Receipt retry does not resend admin notification');
    foreach (['/apply', 'Погоджуюсь', 'Чернетка', '/cancel'] as $text) { $bot->handle($message($text)); }
    check(str_contains($last(), 'Чернетку анкети видалено'), 'Draft cancellation');
    $key = base64_decode($config['state_key']); $data = file_get_contents($files[0]);
    $state = json_decode(sodium_crypto_secretbox_open(substr($data, 24), substr($data, 0, 24), $key), true);
    check($state['draft'] === [], 'Canceled draft removed from encrypted record');
    $state['updated'] = time() - 90000; $nonce = random_bytes(24);
    file_put_contents($files[0], $nonce . sodium_crypto_secretbox(json_encode($state), $nonce, $key));
    check($bot->cleanup() === 1 && count(glob($dir . '/*.bin')) === 0, 'Expired state removed');
    echo "PASS: private chats, consent, validation, encrypted state, failed delivery, receipt retries, duplicate updates, cancellation, retention. No Telegram network requests.\n";
} finally {
    foreach (glob($dir . '/*') ?: [] as $path) { unlink($path); }
    foreach (glob($dir . '/.*') ?: [] as $path) { if (is_file($path)) { unlink($path); } }
    if (is_dir($dir)) { rmdir($dir); }
}
