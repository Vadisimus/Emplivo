#!/usr/bin/env python3
"""Test the complete installer with real backups and deterministic HTTP/Bot fixtures."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import hashlib
import os
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PHP=os.environ.get('EMPLIVO_PHP','php')
PACKAGE=ROOT/'downloads/emplivo-full-php-site.zip'

with TemporaryDirectory(prefix='emplivo-hosting-deploy-') as tmp:
    base=Path(tmp)
    for case in ['success','http_failure','stale_locale','bot_failure','tampered_payload','destination_symlink','public_private_folder']:
        home=base/case;target=home/'www';release=home/'release';binpath=home/'bin'
        target.mkdir(parents=True);binpath.mkdir()
        with ZipFile(PACKAGE) as z:z.extractall(release)
        (target/'index.html').write_text('ORIGINAL SITE')
        (target/'.htaccess').write_text('# Original host directives\nOptions -Indexes\n')
        (target/'.user.ini').write_text('; Original PHP settings\n')
        (target/'uploads').mkdir();(target/'uploads/keep.txt').write_text('USER UPLOAD')
        private=home/'emplivo-private';private.mkdir(mode=0o700)
        marker='SYNTHETIC_PRIVATE_VALUE_DO_NOT_PRINT'
        (private/'telegram.php').write_text(marker)
        (private/'config.php').write_text("<?php return ['supabase_url'=>'https://example123.supabase.co','api_token'=>str_repeat('a',64)];")
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in private.iterdir()}
        php_stub=binpath/'php'
        php_stub.write_text('''#!/usr/bin/env python3
import os,sys,subprocess
if len(sys.argv)>2 and sys.argv[1].endswith('/tools/telegram_admin.php') and sys.argv[2]=='webhook-check':
 print('Endpoint GET: HTTP=405; cURL=0; PHP handler=yes')
 print('Endpoint POST: HTTP=200; cURL=0; PHP handler=yes')
 print('Web PHP: 8.5.12')
 print('Web curl: OK')
 print('Web sodium: '+('FAIL' if os.environ['EMPLIVO_TEST_CASE']=='bot_failure' else 'OK'))
 print('Web state_writable: OK')
 sys.exit(0)
sys.exit(subprocess.call([os.environ['EMPLIVO_REAL_PHP'],*sys.argv[1:]]))
''');php_stub.chmod(0o755)
        curl_stub=binpath/'curl'
        curl_stub.write_text('''#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit
import os,sys
args=sys.argv[1:]
if os.environ['EMPLIVO_TEST_CASE']=='http_failure':sys.exit(22)
url=next(x for x in args if x.startswith('https://'))
rel=urlsplit(url).path.lstrip('/')
root=Path(os.environ['EMPLIVO_TEST_TARGET'])
file=root/rel
if file.is_dir():file=file/'index.html'
if '-o' in args:
 dest=Path(args[args.index('-o')+1])
 if os.environ['EMPLIVO_TEST_CASE']=='stale_locale' and rel=='ru/jobs/':dest.write_text('OLD CATALOG')
 else:dest.write_bytes(file.read_bytes())
''');curl_stub.chmod(0o755)
        if case=='tampered_payload':(release/'site/index.html').write_text('TAMPERED')
        if case=='destination_symlink':
            external=home/'external';external.mkdir();(target/'assets').symlink_to(external,target_is_directory=True)
        if case=='public_private_folder':(target/'emplivo-private').mkdir()
        env=os.environ.copy();env.update(PATH=str(binpath)+os.pathsep+env['PATH'],EMPLIVO_REAL_PHP=PHP,EMPLIVO_TEST_CASE=case,EMPLIVO_TEST_TARGET=str(target))
        result=subprocess.run(['bash',str(release/'deploy.sh'),str(target)],env=env,capture_output=True,timeout=25)
        output=(result.stdout+result.stderr).decode()
        assert marker not in output, 'Private contents disclosed in installer output'
        assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in private.iterdir()}, 'Private configuration changed'
        assert (target/'.user.ini').read_text()=='; Original PHP settings\n'
        assert (target/'uploads/keep.txt').read_text()=='USER UPLOAD'
        if case=='success':
            assert result.returncode==0 and 'DEPLOY_OK' in output, 'Successful installer path failed: '+output[-1200:]
            assert (target/'index.html').read_bytes()==(release/'site/index.html').read_bytes()
            assert 'lang="ru"' in (target/'ru/jobs/index.html').read_text()
            assert 'data-employer-apply' in (target/'ru/vacancies/ever-tech-product-engineer/index.html').read_text()
            assert 'id="vacancy-brief"' in (target/'ru/submit-vacancy/index.html').read_text()
            assert '# Original host directives' in (target/'.htaccess').read_text()
            assert 'DirectoryIndex index.html index.php' in (target/'.htaccess').read_text()
            assert not (target/'www').exists() and not (target/'emplivo-private').exists()
            backups=list((home/'deploy-backups').glob('*/www-before.tar.gz'))
            assert len(backups)==1 and backups[0].stat().st_mode & 0o777==0o600
            with tarfile.open(backups[0]) as tar:assert tar.extractfile('./index.html').read()==b'ORIGINAL SITE'
        else:
            assert result.returncode!=0, 'Expected installer failure was accepted: '+case
            assert (target/'index.html').read_text()=='ORIGINAL SITE', 'Original homepage not restored'
            assert (target/'.htaccess').read_text()=='# Original host directives\nOptions -Indexes\n', 'Original hosting directives not restored'
            if case in ['http_failure','stale_locale','bot_failure']:
                assert 'DEPLOY_ROLLED_BACK' in output, 'Failure did not roll back: '+output[-1200:]
                assert not (target/'telegram-config.js').exists(), 'New file retained after rollback'
            else:assert 'Public files were not changed.' in output
        print('PASS:',case)
print('PASS: full package, private configuration/uploads preservation, complete backup, website/Bot rollback, payload integrity and symlink guards. No real hosting requests.')
