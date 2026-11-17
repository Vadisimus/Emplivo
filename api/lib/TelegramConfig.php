<?php
declare(strict_types=1);

namespace Emplivo;

final class TelegramConfigException extends \RuntimeException {}

/** Load a private PHP array without allowing malformed files to print secrets. */
final class TelegramConfig
{
    public static function load(string $path): array
    {
        if (!is_readable($path) || !is_file($path) || filesize($path) > 65536) {
            throw new TelegramConfigException('Private PHP configuration required');
        }
        $source = file_get_contents($path);
        if (!is_string($source) || !preg_match('/\A<\?php(?:\s|$)/D', $source)) {
            throw new TelegramConfigException('Configuration must start with a PHP opening tag');
        }
        try {
            // Tokenizer is optional on shared PHP hosting; buffering below also
            // protects installations where only the PHP parser is available.
            if (function_exists('token_get_all')) {
                foreach (token_get_all($source, TOKEN_PARSE) as $token) {
                    if (is_array($token) && in_array($token[0], [T_INLINE_HTML, T_ECHO, T_PRINT, T_EXIT], true)) {
                        throw new TelegramConfigException('Configuration must only return an array');
                    }
                }
            }
        } catch (\Throwable $error) {
            // Parser errors can include source fragments; never propagate their messages.
            throw new TelegramConfigException('Invalid private PHP configuration');
        }
        $level = ob_get_level();
        ob_start(static fn (string $output): string => '');
        set_error_handler(static function (): never {
            throw new TelegramConfigException('Private configuration warning');
        });
        try {
            $config = require $path;
            if (!is_array($config) || ob_get_level() !== $level + 1 || ob_get_length() !== 0) {
                throw new TelegramConfigException('Configuration must return an array without output');
            }
            return $config;
        } catch (\Throwable $error) {
            throw new TelegramConfigException('Invalid private PHP configuration');
        } finally {
            restore_error_handler();
            while (ob_get_level() > $level) { ob_end_clean(); }
        }
    }
}
