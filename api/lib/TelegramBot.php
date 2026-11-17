<?php
declare(strict_types=1);

namespace Emplivo;

final class TelegramTransportException extends \RuntimeException
{
    public function __construct(
        public readonly int $curlCode,
        public readonly int $httpStatus,
        public readonly int $apiCode,
        public readonly int $retryAfter = 0,
    ) { parent::__construct('Telegram transport failed'); }
}

/** Private-chat intake only. No applications or contacts are sent to a group. */
final class TelegramBot
{
    private array $config;
    private \Closure $transport;
    private string $key;

    public function __construct(array $config, ?\Closure $transport = null)
    {
        $key = base64_decode((string) ($config['state_key'] ?? ''), true);
        if (!extension_loaded('sodium') || $key === false || strlen($key) !== SODIUM_CRYPTO_SECRETBOX_KEYBYTES
            || !preg_match('/^[1-9][0-9]{0,15}$/D', (string) ($config['admin_chat_id'] ?? ''))
            || !preg_match('/^[0-9]{6,20}:[A-Za-z0-9_-]{30,80}$/D', (string) ($config['bot_token'] ?? ''))
            || !preg_match('/^[A-Za-z0-9_-]{32,256}$/D', (string) ($config['webhook_secret'] ?? ''))
            || !preg_match('~^https://t\.me/(?:[A-Za-z][A-Za-z0-9_]{4,31}|\+[A-Za-z0-9_-]{16,64})$~D', (string) ($config['group_url'] ?? ''))
            || !in_array($config['site_url'] ?? '', ['https://www.emplivo.com.ua', 'https://emplivo.com.ua', 'https://vadisimus.github.io/Emplivo'], true)) {
            throw new \RuntimeException('Telegram configuration incomplete');
        }
        $dir = (string) ($config['state_dir'] ?? '');
        if (!str_starts_with($dir, '/') || is_link($dir)) {
            throw new \RuntimeException('Private state directory required');
        }
        if (!is_dir($dir) && !mkdir($dir, 0700, true) && !is_dir($dir)) {
            throw new \RuntimeException('Cannot create private state directory');
        }
        $resolved = realpath($dir);
        $webroot = realpath(dirname(__DIR__, 2));
        if ($resolved === false || $webroot === false || $resolved === $webroot || str_starts_with($resolved, $webroot . '/')) {
            throw new \RuntimeException('State must be outside webroot');
        }
        if (!chmod($dir, 0700)) {
            throw new \RuntimeException('Cannot secure state directory');
        }
        $this->config = $config;
        $this->key = $key;
        $this->transport = $transport ?? function (string $method, array $payload): array {
            if (!extension_loaded('curl') || !in_array($method, ['sendMessage', 'getMe', 'getUpdates', 'setWebhook', 'getWebhookInfo', 'deleteWebhook', 'setMyCommands'], true)) {
                throw new \RuntimeException('Telegram transport unavailable');
            }
            $curl = curl_init('https://api.telegram.org/bot' . $this->config['bot_token'] . '/' . $method);
            curl_setopt_array($curl, [
                // Bot API parameters are always a JSON object, including getMe {}.
                CURLOPT_POST => true, CURLOPT_POSTFIELDS => json_encode((object) $payload, JSON_THROW_ON_ERROR),
                CURLOPT_HTTPHEADER => ['Content-Type: application/json'], CURLOPT_RETURNTRANSFER => true,
                CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_TIMEOUT => 7, CURLOPT_FOLLOWLOCATION => false,
                CURLOPT_PROTOCOLS => CURLPROTO_HTTPS, CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
            ]);
            $body = curl_exec($curl);
            $status = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
            $curlCode = curl_errno($curl);
            curl_close($curl);
            $result = is_string($body) ? json_decode($body, true) : null;
            if ($curlCode !== 0 || $status !== 200 || !is_array($result) || ($result['ok'] ?? false) !== true) {
                // Never log the request URL, token, contact data or Telegram response body.
                throw new TelegramTransportException($curlCode, $status,
                    (int) ($result['error_code'] ?? 0), (int) ($result['parameters']['retry_after'] ?? 0));
            }
            return $result;
        };
    }

    public function call(string $method, array $payload = []): array
    {
        return ($this->transport)($method, $payload);
    }

    private function save(string $path, array $state): void
    {
        $nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        $data = $nonce . sodium_crypto_secretbox(json_encode($state, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE), $nonce, $this->key);
        $tmp = tempnam($this->config['state_dir'], '.write-');
        if ($tmp === false || !chmod($tmp, 0600) || file_put_contents($tmp, $data) !== strlen($data) || !rename($tmp, $path)) {
            if (is_string($tmp) && is_file($tmp)) { unlink($tmp); }
            throw new \RuntimeException('Cannot save state');
        }
    }

    private function load(string $path): array
    {
        if (!is_file($path)) { return []; }
        $data = file_get_contents($path);
        if (!is_string($data) || strlen($data) < SODIUM_CRYPTO_SECRETBOX_NONCEBYTES + SODIUM_CRYPTO_SECRETBOX_MACBYTES) {
            throw new \RuntimeException('Invalid state');
        }
        $plain = sodium_crypto_secretbox_open(substr($data, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES), substr($data, 0, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES), $this->key);
        if ($plain === false) { throw new \RuntimeException('Invalid state key'); }
        return json_decode($plain, true, 32, JSON_THROW_ON_ERROR);
    }

    private function drain(array &$state, string $path): void
    {
        while ($state['outbox'] ?? []) {
            $this->call('sendMessage', $state['outbox'][0]);
            array_shift($state['outbox']);
            $this->save($path, $state);
        }
    }

    public function handle(array $update): void
    {
        $message = $update['message'] ?? null;
        if (!is_int($update['update_id'] ?? null) || !is_array($message)
            || ($message['chat']['type'] ?? '') !== 'private'
            || !is_int($message['chat']['id'] ?? null) || $message['chat']['id'] < 1
            || ($message['from']['id'] ?? null) !== $message['chat']['id']
            || ($message['from']['is_bot'] ?? true)) { return; }
        $chat = $message['chat']['id'];
        $stem = $this->config['state_dir'] . '/' . hash_hmac('sha256', (string) $chat, $this->key);
        $lock = fopen($this->config['state_dir'] . '/.bot.lock', 'c');
        if ($lock === false) { throw new \RuntimeException('Cannot lock state'); }
        chmod($this->config['state_dir'] . '/.bot.lock', 0600);
        if (!flock($lock, LOCK_EX)) { fclose($lock); throw new \RuntimeException('Cannot lock state'); }
        try {
            $path = $stem . '.bin';
            $state = $this->load($path);
            // Drafts expire after one hour of inactivity; dedupe receipts last one day.
            if (($state['updated'] ?? 0) < time() - 3600) {
                $state['draft'] = [];
            }
            if (($state['updated'] ?? 0) < time() - 86400) { $state = []; }
            $this->drain($state, $path);
            if ($update['update_id'] <= ($state['last_update'] ?? -1)) { return; }
            $state['last_update'] = $update['update_id'];
            $state['updated'] = time();
            if (($state['rate_since'] ?? 0) < time() - 60) { $state['rate_since'] = time(); $state['rate_count'] = 0; }
            $state['rate_count'] = ($state['rate_count'] ?? 0) + 1;
            if ($state['rate_count'] > 20) { $this->save($path, $state); return; }
            $text = is_string($message['text'] ?? null) ? trim($message['text']) : '';
            // Strip control characters, leaving ordinary newlines. All outgoing text is plain text.
            $text = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $text) ?? '';
            if (strlen($text) > 6000) { $text = ''; }
            $reply = '';
            $buttons = [];
            $draft = $state['draft'] ?? [];
            $site = $this->config['site_url'];
            if ($text === '/id') {
                $reply = 'ID цього особистого чату: ' . $chat . '. Лише власник вносить свій ID у приватну конфігурацію.';
            } elseif (in_array($text, ['/cancel', 'Скасувати'], true)) {
                $draft = [];
                $reply = 'Чернетку анкети видалено. Раніше надіслані заявки можна видалити за запитом: hr@emplivo.com.ua. Нова анкета: /apply';
            } elseif ($text === '/jobs') {
                $reply = "Вакансії: {$this->config['group_url']}\nКаталог: {$site}/jobs/\nНа сайті є окремо позначені демонстраційні вакансії.";
            } elseif ($text === '/privacy') {
                $reply = $this->privacy();
            } elseif ($text === '/help') {
                $reply = '/apply — анкета кандидата' . "\n/jobs — вакансії\n/privacy — обробка даних\n/cancel — видалити чернетку\n/id — ID вашого чату\nПідтримка: hr@emplivo.com.ua";
            } elseif ($text === '/apply' || preg_match('/^\/start(?:\s+apply)?$/D', $text)) {
                $draft = ['step' => 'consent', 'reference' => strtoupper(bin2hex(random_bytes(5)))];
                $reply = "Вітаємо в Emplivo. Це загальна анкета кандидата, а не відгук на вигадану вакансію.\n\n" . $this->privacy() . "\n\nЩоб передати контакти та досвід команді Emplivo для підбору роботи, натисніть «Погоджуюсь».";
                $buttons = ['Погоджуюсь', 'Скасувати'];
            } elseif (str_starts_with($text, '/start')) {
                $reply = 'Emplivo: /apply — анкета кандидата, /jobs — вакансії. Для роботодавців: ' . $site . '/employers/';
            } elseif (($draft['step'] ?? '') === 'consent') {
                if ($text === 'Погоджуюсь') {
                    $draft['consented_at'] = gmdate('c'); $draft['step'] = 'name';
                    $reply = 'Як до вас звертатися? Введіть ім’я та прізвище (до 120 символів).';
                } else { $reply = 'Для початку потрібна згода. Або скасуйте анкету.'; $buttons = ['Погоджуюсь', 'Скасувати']; }
            } elseif (($draft['step'] ?? '') === 'name') {
                if ($this->length($text, 2, 120)) { $draft['name'] = $text; $draft['step'] = 'contact'; $reply = 'Введіть телефон із кодом країни (+380…) або email для зв’язку.'; }
                else { $reply = 'Введіть ім’я від 2 до 120 символів.'; }
            } elseif (($draft['step'] ?? '') === 'contact') {
                $phone = preg_replace('/[\s()\-]/', '', $text);
                if (strlen($text) <= 254 && (filter_var($text, FILTER_VALIDATE_EMAIL) || preg_match('/^\+[1-9][0-9]{7,14}$/D', $phone))) {
                    $draft['contact'] = filter_var($text, FILTER_VALIDATE_EMAIL) ? $text : $phone; $draft['step'] = 'role';
                    $reply = 'Яку посаду шукаєте? Наприклад: SPA-терапевт, персональний тренер або wellness-менеджер.';
                } else { $reply = 'Перевірте email або телефон у форматі +380671234567.'; }
            } elseif (($draft['step'] ?? '') === 'role') {
                if ($this->length($text, 2, 160)) { $draft['role'] = $text; $draft['step'] = 'city'; $reply = 'У якому місті або регіоні шукаєте роботу?'; }
                else { $reply = 'Вкажіть посаду від 2 до 160 символів.'; }
            } elseif (($draft['step'] ?? '') === 'city') {
                if ($this->length($text, 2, 120)) { $draft['city'] = $text; $draft['step'] = 'experience'; $reply = 'Коротко опишіть досвід і кваліфікацію (до 1000 символів). Не додавайте медичні, паспортні чи банківські дані. Файли бот поки не приймає.'; }
                else { $reply = 'Вкажіть місто від 2 до 120 символів.'; }
            } elseif (($draft['step'] ?? '') === 'experience') {
                if ($this->length($text, 2, 1000)) {
                    $draft['experience'] = $text; $draft['step'] = 'review';
                    $reply = "Перевірте анкету:\n" . $this->summary($draft) . "\n\nНатисніть «Надіслати заявку» для передачі менеджеру. Для виправлення почніть /apply заново.";
                    $buttons = ['Надіслати заявку', 'Скасувати'];
                } else { $reply = 'Додайте короткий опис досвіду від 2 до 1000 символів.'; }
            } elseif (($draft['step'] ?? '') === 'review') {
                if ($text === 'Надіслати заявку') {
                    $reference = $draft['reference'];
                    $state['outbox'][] = $this->payload((int) $this->config['admin_chat_id'],
                        "Заявка Telegram #{$reference}\n" . $this->summary($draft) . "\nЗгода: {$draft['consented_at']}\nЗв’язок у Telegram: tg://user?id={$chat}\nПерсональні дані: не пересилайте у публічну групу.");
                    $reply = "Заявку #{$reference} передано в особистий чат відповідального менеджера Emplivo. Це не гарантує працевлаштування. Для уточнень: hr@emplivo.com.ua. Вакансії: /jobs";
                    $draft = [];
                } else { $reply = 'Щоб завершити, натисніть «Надіслати заявку», або /cancel.'; $buttons = ['Надіслати заявку', 'Скасувати']; }
            } else {
                $reply = 'Анкета не розпочата або чернетка вже видалена. Почніть /apply. Вакансії: /jobs. Файли бот не приймає; резюме можна додати через сайт або надіслати на hr@emplivo.com.ua.';
            }
            if ($draft && !in_array($draft['step'] ?? '', ['consent', 'review'], true) && !$buttons) { $buttons = ['Скасувати']; }
            $state['draft'] = $draft;
            $state['outbox'][] = $this->payload($chat, $reply, $buttons);
            $this->save($path, $state);
            $this->drain($state, $path);
        } finally { flock($lock, LOCK_UN); fclose($lock); }
    }

    private function privacy(): string
    {
        return 'Оператор: ТОВ «ЕМПЛІВО», ЄДРПОУ 46615773. Анкета передається лише відповідальному менеджеру в особистий Telegram-чат, не в групу вакансій. Telegram також обробляє повідомлення за власною політикою: https://telegram.org/privacy. Незавершена чернетка доступна 1 годину; зашифровані серверні записи видаляються після 24 годин неактивності на найближчому щогодинному очищенні. Регламент для менеджера: видалити отриману анкету не пізніше 90 днів. Запити щодо доступу, виправлення, видалення або відкликання згоди: hr@emplivo.com.ua. Політика: ' . $this->config['site_url'] . '/privacy/';
    }

    public function cleanup(): int
    {
        $lock = fopen($this->config['state_dir'] . '/.bot.lock', 'c');
        if ($lock === false || !flock($lock, LOCK_EX)) { throw new \RuntimeException('Cannot lock state'); }
        chmod($this->config['state_dir'] . '/.bot.lock', 0600);
        $deleted = 0;
        try {
            foreach (glob($this->config['state_dir'] . '/*.bin') ?: [] as $path) {
                $state = $this->load($path);
                if (($state['updated'] ?? 0) < time() - 86400) {
                    if (!unlink($path)) { throw new \RuntimeException('Cannot expire state'); }
                    $deleted++;
                }
            }
            foreach (glob($this->config['state_dir'] . '/.write-*') ?: [] as $path) {
                if (filemtime($path) < time() - 3600) { unlink($path); }
            }
        } finally { flock($lock, LOCK_UN); fclose($lock); }
        return $deleted;
    }

    private function summary(array $draft): string
    {
        return "Ім’я: {$draft['name']}\nКонтакт: {$draft['contact']}\nПосада: {$draft['role']}\nМісто: {$draft['city']}\nДосвід: {$draft['experience']}";
    }

    private function length(string $text, int $min, int $max): bool
    {
        $length = preg_match_all('/./us', $text);
        return $length !== false && $length >= $min && $length <= $max && !str_starts_with($text, '/');
    }

    private function payload(int $chat, string $text, array $buttons = []): array
    {
        return ['chat_id' => $chat, 'text' => $text, 'link_preview_options' => ['is_disabled' => true],
            'reply_markup' => $buttons ? ['keyboard' => array_map(fn ($s) => [['text' => $s]], $buttons), 'resize_keyboard' => true, 'one_time_keyboard' => true]
                : ['remove_keyboard' => true]];
    }
}
