#!/usr/bin/env python3
"""Package the integrated site, keep SSH keys/config outside delivery roots."""
from pathlib import Path
import shutil
import hashlib
import json
import zipfile

root=Path('/workspace/releases/Emplivo_Wellness_2026-11-12')
public=root/'www'
checks={}
for f in public.rglob('*'):
    if f.is_file():
        assert f.name not in ['config.php','emplivo_ed25519'] and 'deploy-keys' not in f.parts
        checks['www/'+f.relative_to(public).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
(root/'CHECKSUMS.json').write_text(json.dumps(checks,indent=2)+'\n')
(root/'INSTALL_UA.md').write_text('''# Emplivo Wellness — оформлення з погодженої концепції

Пакет для чинного PHP-хостингу https://www.emplivo.com.ua/.
Це інтегрований сайт, не папка дизайн-прототипу. На домен пакет ще не завантажено.

## Встановлення

1. Збережіть резервну копію чинної публічної папки www поза www.
2. Завантажте ZIP у каталог домену поруч із www і розпакуйте із заміною файлів.
3. Має бути www/index.html, не www/www/index.html.
4. Збережіть emplivo-private/config.php поруч із www, а також чинні .htaccess
   і .user.ini. Секретів, приватних SSH-ключів і конфігурації у ZIP немає.
5. Публічні файли — 644, папки — 755. ZIP містить ці права.
6. Відкрийте /, /en/, /jobs/, /employers/, /jobs/spa-therapist/ та /contact/.
   Оновіть кеш через Ctrl+F5; номер Emplivo: +380 (67) 777 80 60.
7. Перевірте пошук, фільтри, збереження й ДЕМО-відгук. Демо-заявки не передаються
   в базу. Загальна анкета до Emplivo — реальна; надсилайте її лише з цим наміром.
8. Видаліть ZIP із хостингу після перевірки.

## Що застосовано

Молочно-шавлієва палітра, Cormorant Garamond/Inter, атмосферні ілюстрації,
нові головна, каталог, роботодавчий лендинг і UA/EN-версії. Раніше підготовлені
професійні й контентні SEO-сторінки збережені та узгоджені за палітрою.
Основні сторінки мають статичний HTML, canonical і hreflang; sitemap оновлено.

Вигадані вакансії та роботодавці залишаються позначеними ДЕМО. Їхня оплата не є
ринковою статистикою. Реальні відгуки/кейси й JobPosting не вигадуються.

Загальна анкета працює через чинний PHP API; успіх показується лише після
підтвердження збереження. Повтор після збою зберігає submissionId. Пробний
відгук на демо-вакансію залишається локальним. Бриф роботодавця готує лист,
який користувач надсилає сам; консультація не бронюється автоматично.
Кабінети й alerts позначені як локальні демонстрації. Автентифікація, розсилка,
CMS, ATS та автоматичний календар потребують окремих інтеграцій.

Перевірено локально: 64 HTML-сторінки, 1162 внутрішні посилання, 44 sitemap URL,
desktop/mobile, UK/EN, форма з контрольованими відповідями API та idempotency.
Реальних тестових записів у робочу базу не створювали.

Для відкату відновіть попередню публічну папку з резервної копії.
''',encoding='utf-8')
for f in root.rglob('*'):f.chmod(0o755 if f.is_dir() else 0o644)
root.chmod(0o755)
output=Path('/workspace/releases/emplivo-wellness-site.zip')
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(root.rglob('*')):z.write(f,f.relative_to(root))
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    assert all(((i.external_attr>>16)&0o777)==(0o755 if i.is_dir() else 0o644) for i in z.infolist())
    assert not any('deploy-keys' in n or n.endswith('config.php') for n in z.namelist())
    for name,digest in checks.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest

# Update the current local website and source checkout only after checks passed.
for target in [Path('/workspace/emplivo-local/www'),Path('/workspace/Emplivo')]:
    shutil.copytree(public,target,dirs_exist_ok=True)
print('Packaged and applied locally:',output,'public files:',len(checks),'bytes:',output.stat().st_size)
