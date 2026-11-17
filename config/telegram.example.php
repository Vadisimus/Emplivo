<?php
// TEMPLATE ONLY. Copy outside www to ../emplivo-private/telegram.php (0600).
// Fill secrets there. Never commit the completed file or paste a token in chat.
return [
    'bot_token' => '',
    'bot_username' => '',   // Public @username, verified against getMe at registration.
    'webhook_secret' => '', // 32+ random characters: bin2hex(random_bytes(32))
    'state_key' => '',      // base64_encode(random_bytes(SODIUM_CRYPTO_SECRETBOX_KEYBYTES))
    'admin_chat_id' => '',  // Positive ID of the manager's PRIVATE chat, never a group.
    'group_url' => '',      // https://t.me/your_public_group
    'site_url' => 'https://www.emplivo.com.ua',
    'state_dir' => dirname(__DIR__) . '/telegram-state', // Change to absolute path OUTSIDE www.
];
