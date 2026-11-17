<?php
declare(strict_types=1);

namespace Emplivo;

/** CLI-only setup helpers. They never print or contact Telegram with a token. */
final class TelegramPrivateConfig
{
    public static function save(string $path, array $config, string $webroot): void
    {
        $parent = realpath(dirname($path));
        $public = realpath($webroot);
        if ($parent === false || $public === false || is_link($path) || is_link(dirname($path))
            || $parent === $public || str_starts_with($parent, $public . '/')) {
            throw new \RuntimeException('Private configuration must be outside webroot');
        }
        if (!chmod($parent, 0700)) { throw new \RuntimeException('Cannot secure private directory'); }
        $temporary = tempnam($parent, '.telegram-config-');
        $body = "<?php\n// Private Telegram settings. Never publish this file.\nreturn " . var_export($config, true) . ";\n";
        if ($temporary === false || !chmod($temporary, 0600)
            || file_put_contents($temporary, $body) !== strlen($body) || !rename($temporary, $path)) {
            if (is_string($temporary) && is_file($temporary)) { unlink($temporary); }
            throw new \RuntimeException('Cannot save private configuration');
        }
    }

    public static function prepare(string $path, string $webroot): array
    {
        if (!extension_loaded('sodium') || !is_readable($path)) {
            throw new \RuntimeException('Private configuration and Sodium required');
        }
        $config = require $path;
        if (!is_array($config) || !preg_match('/^[0-9]{6,20}:[A-Za-z0-9_-]{30,80}$/D', (string) ($config['bot_token'] ?? ''))) {
            throw new \RuntimeException('Set the bot token in private configuration first');
        }
        $source = file_get_contents($webroot . '/telegram-config.js');
        if (!is_string($source) || !preg_match('/Object\.freeze\(\s*(\{.*?\})\s*\)/s', $source, $match)) {
            throw new \RuntimeException('Public Telegram configuration missing');
        }
        $public = json_decode($match[1], true, 16, JSON_THROW_ON_ERROR);
        $defaults = [
            'bot_username' => (string) ($public['botUsername'] ?? ''),
            'group_url' => (string) ($public['groupUrl'] ?? ''),
            'site_url' => 'https://www.emplivo.com.ua',
            'state_dir' => dirname(dirname($path)) . '/telegram-state',
        ];
        foreach ($defaults as $key => $value) {
            if (!isset($config[$key]) || $config[$key] === '') { $config[$key] = $value; }
        }
        if (empty($config['webhook_secret'])) { $config['webhook_secret'] = bin2hex(random_bytes(32)); }
        if (empty($config['state_key'])) { $config['state_key'] = base64_encode(random_bytes(SODIUM_CRYPTO_SECRETBOX_KEYBYTES)); }
        // Validate without any network calls; the real recipient is identified separately.
        $validation = $config;
        if (empty($validation['admin_chat_id'])) { $validation['admin_chat_id'] = '1'; }
        new TelegramBot($validation, static function (): array { throw new \LogicException('Setup must not contact Telegram'); });
        self::save($path, $config, $webroot);
        return $config;
    }
}
