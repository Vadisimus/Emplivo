#!/usr/bin/env python3
"""Package only reviewed public files; never include private config or credentials."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/workspace/releases')
NAME='Emplivo_SEO_Demo_2026-11-12'
STAGE=OUT/NAME
OUT.mkdir(exist_ok=True)
if STAGE.exists():shutil.rmtree(STAGE)
public=[f.relative_to(ROOT) for f in ROOT.rglob('index.html') if '.git' not in f.parts]
public += [Path(p) for p in ['styles.css','modern.css','seo.css','translations.js','app.js','seo.js','jobs-data.js','api/applications.php','robots.txt','sitemap.xml']]
# Keep old designs links useful without carrying legacy deployment documents.
redirect=STAGE/'www/designs.html';redirect.parent.mkdir(parents=True)
redirect.write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url=/"><title>Emplivo</title><a href="/">Emplivo</a></html>')
checks={}
for rel in public:
    assert not any(p in rel.parts for p in ['.git','emplivo-private']) and rel.name!='config.php'
    source=ROOT/rel;dest=STAGE/'www'/rel
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    dest.chmod(0o644)
    checks['www/'+rel.as_posix()]=hashlib.sha256(dest.read_bytes()).hexdigest()
checks['www/designs.html']=hashlib.sha256(redirect.read_bytes()).hexdigest()
(STAGE/'CHECKSUMS.json').write_text(json.dumps(checks,indent=2)+'\n')
(STAGE/'INSTALL_UA.md').write_text('''# Оновлення Emplivo — 12.11.2026

Цей пакет підготовлено для https://www.emplivo.com.ua/ на чинному PHP-хостингу.
Він не містить приватної конфігурації, паролів або ключів. На хостинг його ще не завантажено.

1. Збережіть резервну копію чинної папки www поза публічною папкою.
2. Відкрийте каталог домену на один рівень вище www.
3. Завантажте цей ZIP у каталог домену й розпакуйте із заміною файлів www.
   Не розпаковуйте всередині www, щоб не отримати www/www.
4. Збережіть чинні emplivo-private/config.php, www/.htaccess і www/.user.ini.
   Приватна папка має залишатися поруч із www, не всередині неї.
5. Документація й CHECKSUMS.json мають залишатися поза www.
6. Перевірте сайт через HTTPS з оновленням кешу: /, /en/, /jobs/spa-therapist/,
   /demo-employers/, /contact/, /sitemap.xml. Перевірте телефон +380 (67) 777 80 60.
7. Перевірте пошук, фільтри, збереження та пробний відгук на ДЕМО-вакансію.
   Він не повинен надсилати дані у базу. Загальна анкета залишається реальною;
   не надсилайте її лише для демонстрації без окремого наміру.
8. Видаліть ZIP із хостингу після завантаження та перевірки.

Якщо сайт повертає 403: перевірте, що файл знаходиться саме у www/index.html,
а не www/www/index.html. Для публічних файлів встановіть права 644, для публічних
папок — 755. Цей ZIP уже містить такі права; файловий менеджер має зберегти їх
після розпакування. Права приватної конфігурації цим кроком не змінюйте.

Усі шість вакансій і три роботодавці є вигаданими та позначені ДЕМО.
Числа в них не є ринковими зарплатами. Демо-сторінки мають noindex,
не включені в sitemap і не містять JobPosting-розмітки.

Автоматичні email-сповіщення, особисті кабінети, автоматичне бронювання,
публікація вакансій роботодавцями та підтверджені відгуки потребують окремого
бекенду, даних та інтеграцій. Контактна форма лише готує лист і не підтверджує запис.

Для відкату відновіть попередню публічну папку з резервної копії;
приватна конфігурація цим оновленням не змінюється.
''',encoding='utf-8')
archive=OUT/(NAME+'.zip')
# Shared hosting may honour Unix permissions stored in ZIP metadata. Public
# files must be readable by the web server, irrespective of the cloud umask.
for item in STAGE.rglob('*'):
    item.chmod(0o755 if item.is_dir() else 0o644)
STAGE.chmod(0o755)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(STAGE.rglob('*')):
        z.write(f,f.relative_to(STAGE))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert not any('emplivo-private' in n or n.endswith('config.php') for n in z.namelist())
    assert all(((i.external_attr >> 16) & 0o777) == (0o755 if i.is_dir() else 0o644) for i in z.infolist())
    for rel,digest in checks.items():assert hashlib.sha256(z.read(rel)).hexdigest()==digest

# Update the established local PHP document root without touching private config.
local=Path('/workspace/emplivo-local/www')
backup=OUT/'Emplivo_public_before_SEO_2026-11-12.tar.gz'
if local.exists() and not backup.exists():
    with tarfile.open(backup,'w:gz') as t:t.add(local,arcname='www')
shutil.copytree(STAGE/'www',local,dirs_exist_ok=True)
local.chmod(0o755)
print(f'Package: {archive}')
print(f'Public files: {len(checks)}; ZIP and SHA256 verified; local document root updated; private config untouched')
