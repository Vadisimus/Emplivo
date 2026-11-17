#!/usr/bin/env bash
# Read a BotFather token from the terminal without echo, arguments or shell history.
set +x
set -euo pipefail
emplivo_setup_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
emplivo_php_bin=${EMPLIVO_PHP:-php}
trap 'unset EMPLIVO_TELEGRAM_TOKEN' EXIT
IFS= read -r -s -p 'Вставте НОВИЙ токен BotFather і натисніть Enter: ' EMPLIVO_TELEGRAM_TOKEN </dev/tty
printf '\n' >/dev/tty
export EMPLIVO_TELEGRAM_TOKEN
"$emplivo_php_bin" "$emplivo_setup_root/tools/telegram_admin.php" init
