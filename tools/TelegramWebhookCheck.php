<?php
declare(strict_types=1);

namespace Emplivo;

/** Operational probes: print only allowlisted metadata, never URLs, bodies or secrets. */
final class TelegramWebhookCheck
{
    public static function deliveryFailure(string $message): string
    {
        if ($message === '') { return 'none recorded'; }
        if (preg_match('/Wrong response from (?:the )?webhook:\s*([1-5][0-9]{2})/i', $message, $match)) {
            return 'HTTP ' . $match[1];
        }
        $lower = strtolower($message);
        foreach ([
            ['certificate', 'TLS/certificate failure'], ['ssl', 'TLS/certificate failure'],
            ['timed out', 'connection timeout'], ['timeout', 'connection timeout'],
            ['resolve', 'DNS resolution failure'], ['refused', 'connection refused'], ['reset', 'connection reset'],
        ] as [$needle, $label]) {
            if (str_contains($lower, $needle)) { return $label; }
        }
        return 'unclassified delivery failure; inspect endpoint probe';
    }

    public static function probe(array $config, ?\Closure $request = null): array
    {
        $site = $config['site_url'] ?? '';
        if (!in_array($site, ['https://www.emplivo.com.ua', 'https://emplivo.com.ua'], true)) {
            throw new \RuntimeException('PHP hosting endpoint required');
        }
        $url = $site . '/api/telegram-webhook.php';
        $request ??= static function (string $url, string $method, string $secret): array {
            $handler = false;
            $body = '';
            $curl = curl_init($url);
            $options = [
                CURLOPT_RETURNTRANSFER => false, CURLOPT_CONNECTTIMEOUT => 5, CURLOPT_TIMEOUT => 15,
                CURLOPT_FOLLOWLOCATION => false, CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
                CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
                CURLOPT_HEADERFUNCTION => static function ($curl, string $header) use (&$handler): int {
                    if (strtolower(trim($header)) === 'x-emplivo-telegram: 1') { $handler = true; }
                    return strlen($header);
                },
                CURLOPT_WRITEFUNCTION => static function ($curl, string $chunk) use (&$body): int {
                    if (strlen($body) + strlen($chunk) > 65536) { return 0; }
                    $body .= $chunk;
                    return strlen($chunk);
                },
            ];
            if ($method === 'POST') {
                $options[CURLOPT_POST] = true;
                $options[CURLOPT_POSTFIELDS] = '{"update_id":0,"emplivo_probe":true}';
                $options[CURLOPT_HTTPHEADER] = ['Content-Type: application/json', 'X-Telegram-Bot-Api-Secret-Token: ' . $secret];
            }
            curl_setopt_array($curl, $options);
            curl_exec($curl);
            $result = ['status' => (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE), 'curl' => curl_errno($curl),
                'handler' => $handler, 'redirect' => (string) curl_getinfo($curl, CURLINFO_REDIRECT_URL), 'body' => $body];
            curl_close($curl);
            return $result;
        };
        $rows = [];
        foreach (['GET', 'POST'] as $method) {
            $result = $request($url, $method, $method === 'POST' ? (string) $config['webhook_secret'] : '');
            $row = ['method' => $method, 'http' => (int) ($result['status'] ?? 0), 'curl' => (int) ($result['curl'] ?? 0),
                'handler' => ($result['handler'] ?? false) === true];
            $redirect = $result['redirect'] ?? '';
            if (in_array($redirect, ['https://www.emplivo.com.ua/api/telegram-webhook.php', 'https://emplivo.com.ua/api/telegram-webhook.php'], true)) {
                $row['redirect_to'] = str_contains($redirect, '://www.') ? 'www host' : 'apex host';
            }
            $decoded = json_decode((string) ($result['body'] ?? ''), true);
            if ($method === 'POST' && is_array($decoded) && ($decoded['probe'] ?? '') === 'emplivo-webhook') {
                $version = $decoded['php'] ?? '';
                if (is_string($version) && preg_match('/^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$/D', $version)) { $row['php'] = $version; }
                foreach (['curl', 'sodium', 'state_writable'] as $key) {
                    if (is_bool($decoded['checks'][$key] ?? null)) { $row['checks'][$key] = $decoded['checks'][$key]; }
                }
            }
            $rows[] = $row;
        }
        return $rows;
    }
}
