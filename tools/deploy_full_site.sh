#!/usr/bin/env bash
# Install a checked public release in place; private config/state stay beside www.
set -Eeuo pipefail
umask 077
release_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source_dir="$release_root/site"
target=${1:-/home/emplivo/emplivo.com.ua/www}
backup_dir=''
applied=0
existing=()
added=()
files=()

fail() { printf '%s\n' "$*" >&2; return 1; }
rollback() {
    local code=$1 line=$2
    trap - ERR INT TERM
    set +e
    printf 'DEPLOY_FAILED: step at line %s\n' "$line" >&2
    if [[ $applied == 1 ]]; then
        for rel in "${added[@]}"; do rm -f -- "$target/$rel"; done
        if [[ -s "$backup_dir/restore-files.txt" ]]; then
            if ! tar -xzpf "$backup_dir/www-before.tar.gz" -C "$target" --verbatim-files-from -T "$backup_dir/restore-files.txt"; then
                printf 'ROLLBACK_NEEDS_ATTENTION: %s\n' "$backup_dir" >&2
                exit 2
            fi
        fi
        printf 'DEPLOY_ROLLED_BACK; backup: %s\n' "$backup_dir" >&2
    else
        printf 'Public files were not changed.\n' >&2
    fi
    exit "$code"
}
trap 'rollback "$?" "$LINENO"' ERR
trap 'rollback 130 "$LINENO"' INT
trap 'rollback 143 "$LINENO"' TERM

for tool in sha256sum tar install curl php flock mktemp sed grep du df awk; do
    command -v "$tool" >/dev/null || fail "Required command missing: $tool"
done
[[ $target == /* && $(basename -- "$target") == www && -d $target && ! -L $target ]] || fail 'Expected an existing absolute www directory.'
parent=$(cd -- "$target/.." && pwd -P)
target="$parent/www"
[[ $release_root != "$target" && $release_root != "$target/"* ]] || fail 'Extract the release outside www.'
[[ -d $source_dir && -f $source_dir/index.html && -f $release_root/manifest.sha256 && -f $release_root/source-revision.txt && -s $release_root/http-checks.tsv ]] || fail 'Release is incomplete.'
frontend=0
if [[ -s $release_root/frontend-assets.sha256 ]]; then
    frontend=1
fi
[[ ! -L $target/.htaccess && ! -L $parent/deploy-backups ]] || fail 'Symlinked .htaccess/backup directory requires manual review.'
[[ ! -e $target/emplivo-private && ! -L $target/emplivo-private && ! -e $target/telegram-state && ! -L $target/telegram-state ]] || fail 'Private config/state found inside www; review its location before publishing.'
exec 9>"$parent/.emplivo-deploy.lock"
flock -n 9 || fail 'Another deployment is running.'

while IFS= read -r line; do
    [[ $line =~ ^[a-f0-9]{64}\ \ site/([A-Za-z0-9_./-]+)$ ]] || fail 'Invalid release manifest.'
    rel=${BASH_REMATCH[1]}
    [[ $rel != /* && ! $rel =~ (^|/)\.\.(/|$) && $rel != . && $rel != */ ]] || fail 'Unsafe release path.'
    [[ $rel != emplivo-private/* && $rel != telegram-state/* && $rel != .git/* && $rel != www/* ]] || fail 'Private/nested root in release.'
    if [[ $frontend == 1 && ! $rel =~ ^([A-Za-z0-9_/-]*index\.html|wellness\.(css|js)|seo\.css|vacancies\.css|localization-ru\.js|assets/workplace-hero(-small)?\.webp)$ ]]; then
        fail "Unexpected file in design update: $rel"
    fi
    [[ -f $source_dir/$rel && ! -L $source_dir/$rel ]] || fail 'Payload file missing or symlinked.'
    cursor=$target
    IFS=/ read -r -a components <<< "$rel"
    for component in "${components[@]}"; do
        cursor="$cursor/$component"
        [[ ! -L $cursor ]] || fail "Destination symlink requires manual review: $rel"
    done
    [[ ! -d $target/$rel ]] || fail "Destination is a directory: $rel"
    files+=("$rel")
    if [[ -e $target/$rel ]]; then existing+=("./$rel"); else added+=("$rel"); fi
done < "$release_root/manifest.sha256"
[[ ${#files[@]} -gt 70 ]] || fail 'Unexpectedly small website release.'
(cd -- "$release_root" && sha256sum -c manifest.sha256 >/dev/null)
if [[ $frontend == 0 ]]; then
    for rel in "${files[@]}"; do
        if [[ $rel == *.php ]]; then php -l "$source_dir/$rel" >/dev/null; fi
    done
    [[ -r $parent/emplivo-private/telegram.php ]] || fail 'Existing private Telegram config not found; no files changed.'
    general_status=$(php -r '
require $argv[1] . "/api/lib/TelegramConfig.php";
$path=$argv[2] . "/emplivo-private/config.php";
if (!is_file($path)) { echo "NOT_CONFIGURED"; exit; }
try {
 $c=\Emplivo\TelegramConfig::load($path);
 $ok=preg_match("~^https://[a-z0-9]+\\.supabase\\.co$~D",rtrim((string)($c["supabase_url"]??""),"/"))
  && preg_match("/^[a-f0-9]{64}$/D",(string)($c["api_token"]??""));
 echo $ok ? "CONFIGURED" : "NOT_CONFIGURED";
} catch (Throwable $e) { fwrite(STDERR,"Private site config has an invalid PHP format; contents hidden.\n"); exit(1); }
' "$source_dir" "$parent")
fi
size_kb=$(du -sk "$target" | awk '{print $1}')
free_kb=$(df -Pk "$parent" | awk 'NR==2 {print $4}')
[[ $size_kb =~ ^[0-9]+$ && $free_kb =~ ^[0-9]+$ ]] || fail 'Cannot determine backup disk space.'
(( free_kb > size_kb + 32768 )) || fail 'Not enough free disk space for a safe backup.'
mkdir -p -- "$parent/deploy-backups"
chmod 700 "$parent/deploy-backups"
backup_dir=$(mktemp -d "$parent/deploy-backups/full-site-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
printf '%s\n' "${existing[@]}" > "$backup_dir/restore-files.txt"
tar -czpf "$backup_dir/www-before.tar.gz" -C "$target" .
tar -tzf "$backup_dir/www-before.tar.gz" >/dev/null
printf 'Backup created: %s\n' "$backup_dir/www-before.tar.gz"

# Keep all existing hosting directives; select the new static homepage first.
if [[ $frontend == 0 ]]; then
    for name in config.php telegram.php; do
        if [[ -f $parent/emplivo-private/$name ]]; then sha256sum "$parent/emplivo-private/$name" >> "$backup_dir/private-before.sha256"; fi
    done
    if [[ -e $target/.htaccess ]]; then
        printf './.htaccess\n' >> "$backup_dir/restore-files.txt"
        sed '/^# BEGIN EMPLIVO STATIC ENTRY$/,/^# END EMPLIVO STATIC ENTRY$/d' "$target/.htaccess" > "$backup_dir/new-htaccess"
    else
        added+=(.htaccess)
        : > "$backup_dir/new-htaccess"
    fi
    cat >> "$backup_dir/new-htaccess" <<'HTACCESS'

# BEGIN EMPLIVO STATIC ENTRY
DirectoryIndex disabled
DirectoryIndex index.html index.php
# END EMPLIVO STATIC ENTRY
HTACCESS
fi
applied=1
for rel in "${files[@]}"; do
    destination_dir=$(dirname -- "$target/$rel")
    if [[ ! -d $destination_dir ]]; then install -d -m 755 -- "$destination_dir"; fi
    install -m 644 -- "$source_dir/$rel" "$target/$rel"
done
if [[ $frontend == 0 ]]; then
    install -m 644 -- "$backup_dir/new-htaccess" "$target/.htaccess"
    for name in config.php telegram.php; do
        if [[ -f $parent/emplivo-private/$name ]]; then sha256sum "$parent/emplivo-private/$name" >> "$backup_dir/private-after.sha256"; fi
    done
    cmp -s "$backup_dir/private-before.sha256" "$backup_dir/private-after.sha256" || fail 'Private configuration changed during deployment.'
fi

counter=0
query=''
if [[ $frontend == 1 ]]; then
    query="?emplivo_design=$(date +%s)"
fi
while IFS=$'\t' read -r route expected; do
    [[ $route =~ ^/[A-Za-z0-9_./-]*$ && $route != //* && -n $expected ]] || fail 'Invalid web check in the package.'
    counter=$((counter+1))
    body="$backup_dir/http-page-$counter.body"
    curl -fsSL --proto '=https' --proto-redir '=https' --max-redirs 3 --connect-timeout 8 --max-time 20 "https://www.emplivo.com.ua$route$query" -o "$body" || fail "Page request failed: $route"
    grep -Fq -- "$expected" "$body" || fail "New page not served at: $route"
done < "$release_root/http-checks.tsv"
grep -Fq 'https://t.me/Emplivobot?start=apply' "$backup_dir/http-page-1.body" || fail 'Telegram application link missing from homepage.'
if [[ $frontend == 1 ]]; then
    while IFS=' ' read -r expected rel; do
        [[ $expected =~ ^[a-f0-9]{64}$ && $rel =~ ^(wellness\.(css|js)|seo\.css|vacancies\.css|localization-ru\.js|assets/workplace-hero(-small)?\.webp)$ ]] || fail 'Invalid design asset check.'
        body="$backup_dir/http-design-asset.body"
        curl -fsSL --proto '=https' --proto-redir '=https' --max-redirs 3 --connect-timeout 8 --max-time 20 "https://www.emplivo.com.ua/$rel$query" -o "$body" || fail "Asset request failed: $rel"
        actual=$(sha256sum "$body")
        [[ ${actual%% *} == "$expected" ]] || fail "Updated asset not served at: /$rel"
    done < "$release_root/frontend-assets.sha256"
    trap - ERR INT TERM
    printf '\nDEPLOY_OK\nSource: %s\nSite: https://www.emplivo.com.ua/\nBackup: %s\nWebsite routes verified: %s\n' "$(cat "$release_root/source-revision.txt")" "$backup_dir/www-before.tar.gz" "$counter"
    exit 0
fi
curl -fsSL --proto '=https' --proto-redir '=https' --max-redirs 3 --connect-timeout 8 --max-time 20 https://www.emplivo.com.ua/telegram-config.js -o "$backup_dir/http-telegram-config.body"
grep -Eq '"botEnabled"[[:space:]]*:[[:space:]]*true' "$backup_dir/http-telegram-config.body" || fail 'Public bot configuration not active.'
curl -fsSL --proto '=https' --proto-redir '=https' --max-redirs 3 --connect-timeout 8 --max-time 20 https://www.emplivo.com.ua/assets/wellness-atlas.png -o "$backup_dir/http-hero.body"
php "$target/tools/telegram_admin.php" webhook-check > "$backup_dir/webhook-check.txt" 2>&1
grep -Fq 'Endpoint GET: HTTP=405; cURL=0; PHP handler=yes' "$backup_dir/webhook-check.txt" || fail 'Webhook GET check failed.'
grep -Fq 'Endpoint POST: HTTP=200; cURL=0; PHP handler=yes' "$backup_dir/webhook-check.txt" || fail 'Authenticated webhook check failed.'
grep -Fq 'Web curl: OK' "$backup_dir/webhook-check.txt" || fail 'Web cURL unavailable.'
grep -Fq 'Web sodium: OK' "$backup_dir/webhook-check.txt" || fail 'Web Sodium unavailable.'
grep -Fq 'Web state_writable: OK' "$backup_dir/webhook-check.txt" || fail 'Bot state not writable.'
trap - ERR INT TERM
printf '\nDEPLOY_OK\nSource: %s\nSite: https://www.emplivo.com.ua/\nBackup: %s\nGeneral application backend: %s\n' "$(cat "$release_root/source-revision.txt")" "$backup_dir/www-before.tar.gz" "$general_status"
printf 'Website routes verified: %s\n' "$counter"
grep -E '^(Endpoint|Web )' "$backup_dir/webhook-check.txt"
if [[ $general_status != CONFIGURED ]]; then
    printf 'General CV form needs its existing private Supabase configuration. Telegram applications are configured separately.\n'
fi
