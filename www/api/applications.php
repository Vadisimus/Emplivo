<?php
declare(strict_types=1);

// Emplivo gateway for PHP 8.3+. The private config sits beside www, never inside it.
ini_set('display_errors', '0');
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function respond(array $data, int $status): never
{
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}

function cvError(string $message, int $status = 422): never
{
    respond(['message' => 'Перевірте позначені поля.', 'errors' => ['cv' => $message]], $status);
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    respond(['message' => 'Цей спосіб надсилання не підтримується.'], 405);
}

$limit = 6 * 1024 * 1024;
if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > $limit) {
    cvError('Файл завеликий. Максимальний розмір резюме — 5 МБ.', 413);
}
if (!str_starts_with(strtolower($_SERVER['CONTENT_TYPE'] ?? ''), 'multipart/form-data;')) {
    respond(['message' => 'Неправильний формат заявки. Оновіть сторінку.'], 415);
}

try {
    $configPath = dirname(__DIR__, 2) . '/emplivo-private/config.php';
    if (!is_readable($configPath)) {
        respond(['message' => 'Надсилання тимчасово недоступне. Спробуйте пізніше.'], 503);
    }
    $config = require $configPath;
    $supabase = rtrim((string) ($config['supabase_url'] ?? ''), '/');
    $token = (string) ($config['api_token'] ?? '');
    if (!preg_match('~^https://[a-z0-9]+\.supabase\.co$~D', $supabase)
        || !preg_match('/^[a-f0-9]{64}$/D', $token) || !extension_loaded('curl')) {
        respond(['message' => 'Надсилання тимчасово недоступне. Спробуйте пізніше.'], 503);
    }

    // A normal browser sends Origin on a form POST. Never grant cross-origin writes.
    $host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
    if (!preg_match('/^[a-z0-9.-]+(?::[0-9]{1,5})?$/D', $host)) {
        respond(['message' => 'Відкрийте форму на сайті Emplivo та повторіть надсилання.'], 403);
    }
    $secure = !empty($_SERVER['HTTPS']) && strtolower((string) $_SERVER['HTTPS']) !== 'off';
    $secure = $secure || (string) ($_SERVER['SERVER_PORT'] ?? '') === '443';
    $origins = $config['allowed_origins'] ?? [];
    if (!$origins) {
        $origins = [($secure ? 'https://' : 'http://') . $host];
    }
    $origin = strtolower((string) ($_SERVER['HTTP_ORIGIN'] ?? ''));
    if (!in_array($origin, $origins, true)
        || strtolower((string) ($_SERVER['HTTP_SEC_FETCH_SITE'] ?? '')) === 'cross-site') {
        respond(['message' => 'Відкрийте форму на сайті Emplivo та повторіть надсилання.'], 403);
    }

    // Whitelist fields; PHP arrays cannot be smuggled into the upstream form.
    $fields = [];
    foreach (['submissionId', 'fullName', 'phone', 'email', 'role', 'destination', 'experience', 'consent'] as $key) {
        $value = $_POST[$key] ?? '';
        if (!is_string($value)) {
            respond(['message' => 'Неправильний формат заявки. Оновіть сторінку.'], 400);
        }
        $fields[$key] = $value;
    }
    $id = $fields['submissionId'];
    if (!preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/iD', $id)) {
        respond(['message' => 'Оновіть сторінку та повторіть надсилання.'], 400);
    }

    if (isset($_FILES['cv'])) {
        $file = $_FILES['cv'];
        if (!is_array($file) || !isset($file['error']) || !is_int($file['error'])) {
            cvError('Додайте один файл резюме у форматі PDF або DOCX.');
        }
        $error = $file['error'];
        if (in_array($error, [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true)) {
            cvError('Резюме завелике — максимум 5 МБ.', 413);
        }
        if ($error !== UPLOAD_ERR_OK && $error !== UPLOAD_ERR_NO_FILE) {
            cvError('Не вдалося завантажити резюме. Виберіть файл і повторіть надсилання.');
        }
        if ($error === UPLOAD_ERR_OK) {
            $path = (string) ($file['tmp_name'] ?? '');
            if (!is_uploaded_file($path)) {
                cvError('Не вдалося прочитати резюме. Виберіть файл повторно.');
            }
            $size = filesize($path);
            if ($size === false || $size > 5 * 1024 * 1024) {
                cvError('Резюме завелике — максимум 5 МБ.', 413);
            }
            if ($size === 0) {
                cvError('Файл резюме порожній. Виберіть інший файл або видаліть вкладення.');
            }
            if ($size > 0) {
                $name = basename(str_replace('\\', '/', (string) ($file['name'] ?? '')));
                $name = str_replace(["\r", "\n", "\0"], '', $name);
                $ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));
                if (!in_array($ext, ['pdf', 'docx'], true)) {
                    cvError('Додайте резюме у форматі PDF або DOCX.');
                }
                $signature = file_get_contents($path, false, null, 0, 5);
                if (($ext === 'pdf' && $signature !== '%PDF-')
                    || ($ext === 'docx' && !str_starts_with((string) $signature, "PK\x03\x04"))) {
                    cvError('Вміст файлу не відповідає формату PDF або DOCX.');
                }
                $mime = $ext === 'pdf' ? 'application/pdf'
                    : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
                $fields['cv'] = new CURLFile($path, $mime, $name);
            }
        }
    }

    $curl = curl_init($supabase . '/functions/v1/emplivo-application');
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $fields,
        CURLOPT_HTTPHEADER => ['X-Emplivo-Token: ' . $token, 'Accept: application/json', 'Expect:'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 20,
        CURLOPT_TIMEOUT => 25,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
    ]);
    $body = curl_exec($curl);
    $status = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    $curlError = curl_errno($curl);
    curl_close($curl);
    if ($body === false || $curlError !== 0) {
        error_log('Emplivo upstream transport error: ' . $curlError);
        respond(['message' => 'Звʼязок перервався. Дані залишилися у формі. Повторіть надсилання — дубль заявки не створиться.'], 503);
    }
    $result = json_decode($body, true);
    if ($status >= 200 && $status < 300 && is_array($result)
        && ($result['ok'] ?? false) === true && ($result['id'] ?? '') === $id) {
        respond(['ok' => true, 'id' => $id], 200);
    }
    if (in_array($status, [400, 409, 413, 415, 422], true) && is_array($result)
        && is_string($result['message'] ?? null)) {
        $response = ['message' => $result['message']];
        if (is_array($result['errors'] ?? null)) {
            $response['errors'] = $result['errors'];
        }
        respond($response, $status);
    }
    error_log('Emplivo upstream unexpected response: HTTP ' . $status);
    respond(['message' => 'Не вдалося підтвердити збереження. Дані залишилися у формі — повторіть надсилання.'], 503);
} catch (Throwable $error) {
    error_log('Emplivo gateway failed: ' . get_class($error));
    respond(['message' => 'Надсилання тимчасово недоступне. Дані залишилися у формі. Спробуйте пізніше.'], 503);
}
