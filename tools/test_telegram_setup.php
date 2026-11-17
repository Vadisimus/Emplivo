<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/api/lib/TelegramBot.php';
require_once __DIR__ . '/TelegramPrivateConfig.php';
function setupCheck(bool $value, string $reason): void { if (!$value) { throw new RuntimeException($reason); } }
$base = sys_get_temp_dir() . '/emplivo-setup-test-' . bin2hex(random_bytes(6));
$web = $base . '/www'; $private = $base . '/emplivo-private';
mkdir($web, 0700, true); mkdir($private, 0700);
$path = $private . '/telegram.php';
$token = '123456789:' . str_repeat('test_only_', 4);
file_put_contents($web . '/telegram-config.js', 'window.EMPLIVO_TELEGRAM = Object.freeze(' . json_encode([
    'groupUrl' => 'https://t.me/+AbCdeFGhIjKlmN01', 'botUsername' => 'Emplivo_bot', 'botEnabled' => false,
]) . ');');
file_put_contents($path, '<?php return ' . var_export(['bot_token' => $token, 'admin_chat_id' => '', 'custom_setting' => 'keep'], true) . ';');
function removeSetupFixture(string $dir): void
{
    foreach (scandir($dir) as $entry) {
        if ($entry === '.' || $entry === '..') { continue; }
        $path = $dir . '/' . $entry;
        if (is_dir($path) && !is_link($path)) { removeSetupFixture($path); }
        else { unlink($path); }
    }
    rmdir($dir);
}
try {
    ob_start();
    $prepared = \Emplivo\TelegramPrivateConfig::prepare($path, $web);
    $output = ob_get_clean();
    setupCheck($output === '', 'No secrets or configuration printed');
    setupCheck($prepared['bot_token'] === $token && $prepared['custom_setting'] === 'keep', 'Token and existing settings preserved');
    setupCheck($prepared['admin_chat_id'] === '', 'Temporary validation ID must not become the real recipient');
    setupCheck($prepared['bot_username'] === 'Emplivo_bot' && $prepared['group_url'] === 'https://t.me/+AbCdeFGhIjKlmN01', 'Public addresses imported');
    setupCheck(strlen($prepared['webhook_secret']) === 64 && strlen(base64_decode($prepared['state_key'], true)) === 32, 'Private random secrets generated');
    setupCheck($prepared['state_dir'] === $base . '/telegram-state', 'State outside public webroot');
    clearstatcache();
    setupCheck((fileperms($path) & 0777) === 0600 && (fileperms($private) & 0777) === 0700, 'Private permissions enforced');
    setupCheck((require $path) === $prepared, 'Private configuration readable by PHP');
    $repeated = \Emplivo\TelegramPrivateConfig::prepare($path, $web);
    setupCheck($prepared === $repeated, 'Rerun does not rotate secrets or reset settings');
    $prepared['admin_chat_id'] = '987654321';
    \Emplivo\TelegramPrivateConfig::save($path, $prepared, $web);
    setupCheck((require $path)['admin_chat_id'] === '987654321', 'Manager ID persisted privately');
    try {
        \Emplivo\TelegramPrivateConfig::save($web . '/telegram.php', $prepared, $web);
        throw new LogicException('Public secret file accepted');
    } catch (RuntimeException $expected) { /* Private-only invariant. */ }
    setupCheck(!is_file($web . '/telegram.php'), 'No secret file in webroot');
    echo "PASS: token-only bootstrap, no secret output, preserved token/settings, stable random keys, private state/permissions, recipient persistence and webroot rejection. No Telegram calls.\n";
} finally { removeSetupFixture($base); }
