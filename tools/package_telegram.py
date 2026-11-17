#!/usr/bin/env python3
"""Build a PHP hosting add-on from an explicit list of non-secret source files."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
FILES=[
    'api/telegram-webhook.php', 'api/lib/TelegramBot.php', 'api/lib/TelegramConfig.php',
    'tools/telegram_admin.php', 'tools/TelegramPrivateConfig.php', 'tools/telegram_init.sh',
    'telegram-config.js', 'config/telegram.example.php', 'TELEGRAM_UA.md',
]
output=ROOT/'downloads/emplivo-telegram-setup.zip'
output.parent.mkdir(exist_ok=True)
with ZipFile(output,'w',ZIP_DEFLATED) as archive:
    for name in FILES:
        assert not name.startswith('/') and '..' not in Path(name).parts
        info=ZipInfo(name, (2026,11,17,0,0,0))
        info.create_system=3
        info.external_attr=(0o100644<<16)
        info.compress_type=ZIP_DEFLATED
        archive.writestr(info,(ROOT/name).read_bytes())
with ZipFile(output) as archive:
    assert archive.testzip() is None
    assert archive.namelist()==FILES
    for name in FILES:
        assert archive.read(name)==(ROOT/name).read_bytes()
    assert not any('emplivo-private/' in name or name.endswith('/telegram.php') for name in archive.namelist())
print('Verified hosting package:',output.relative_to(ROOT),'files:',len(FILES),'bytes:',output.stat().st_size)
