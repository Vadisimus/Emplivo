#!/usr/bin/env python3
"""Package a committed public website and a rollback-capable hosting installer."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import argparse
import hashlib
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES={'about','api','assets','blog','candidates','cases','contact','demo-account','demo-employer-dashboard','demo-employers','demo-jobs','employers','en','insights','jobs','locations','privacy','ru','salary-guide','submit-vacancy','vacancies'}
OPERATIONS={'tools/telegram_admin.php','tools/TelegramPrivateConfig.php','tools/TelegramWebhookCheck.php','tools/telegram_init.sh','config/telegram.example.php'}

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def public(name):
    p=PurePosixPath(name)
    return name in OPERATIONS or p.parts[0] in DIRECTORIES or (len(p.parts)==1 and (p.suffix in {'.html','.css','.js','.xml'} or name in {'.nojekyll','robots.txt','TELEGRAM_UA.md'}))

def web_checks(payload):
    checks=[]
    for lang,prefix in [('uk',''),('en','en/'),('ru','ru/')]:
        for route in ('','jobs/','employers/','privacy/','contact/'):
            page=payload[prefix+route+'index.html'].decode()
            assert f'<html lang="{lang}"' in page, prefix+route
            # Requiring the application asset version distinguishes a stale copy from this release.
            bundle=re.search(r'vacancies-data\.js\?v=[a-f0-9]+',page)
            marker=bundle[0] if bundle else f'https://www.emplivo.com.ua/{prefix}{route}'
            checks.append((f'/{prefix}{route}', marker))
        page=payload[f'{prefix}submit-vacancy/index.html'].decode()
        assert f'<html lang="{lang}"' in page and 'id="vacancy-brief"' in page
        checks.append((f'/{prefix}submit-vacancy/', 'id="vacancy-brief"'))
    detail_pages=[name for name in sorted(payload) if re.fullmatch(r'(?:en/|ru/)?vacancies/[^/]+/index\.html',name)]
    assert detail_pages, 'No vacancy detail pages found'
    for name in detail_pages:
        route='/'+name.removesuffix('index.html')
        canonical=f'href="https://www.emplivo.com.ua{route}"'
        assert canonical in payload[name].decode(), name
        checks.append((route,canonical))
    checks.append(('/localization-ru.js','window.EMPLIVO_RU = '))
    return ''.join(f'{route}\t{marker}\n' for route,marker in checks)

def build(ref,output):
    revision=git('rev-parse',ref).decode().strip()
    names=git('ls-tree','-r','--name-only',revision).decode().splitlines()
    payload={name:git('show',f'{revision}:{name}') for name in names if public(name)}
    pages=[n for n in payload if n.endswith('/index.html') or n=='index.html']
    assert '"botEnabled": true' in payload['telegram-config.js'].decode()
    assert not any(set(PurePosixPath(n).parts)&{'www','emplivo-private','telegram-state','downloads','.git','deploy-keys'} for n in payload)
    assert not any(PurePosixPath(n).name in {'telegram.php','config.php'} for n in payload)
    manifest=''.join(hashlib.sha256(data).hexdigest()+'  site/'+name+'\n' for name,data in sorted(payload.items()))
    files={'site/'+name:data for name,data in payload.items()}
    files['manifest.sha256']=manifest.encode()
    files['http-checks.tsv']=web_checks(payload).encode()
    files['source-revision.txt']=(revision+'\n').encode()
    files['deploy.sh']=(ROOT/'tools/deploy_full_site.sh').read_bytes()
    files['INSTALL_FULL_SITE_UA.md']=(ROOT/'docs/PHP_HOSTING_DEPLOY_UA.md').read_bytes()
    output.parent.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).timetuple()[:6]
    with ZipFile(output,'w',ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):
            info=ZipInfo(name,stamp);info.create_system=3
            info.external_attr=((0o100644 if name.startswith('site/') else 0o100600)<<16)
            info.compress_type=ZIP_DEFLATED
            archive.writestr(info,data)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        for name,data in files.items():assert archive.read(name)==data
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    Path(str(output)+'.sha256').write_text(digest+'  '+output.name+'\n')
    print('Prepared source:',revision,'public files:',len(payload),'HTML pages:',len(pages),'bytes:',output.stat().st_size)
    print('SHA256:',digest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-ref',default='HEAD');p.add_argument('--output',type=Path,default=ROOT/'downloads/emplivo-full-php-site.zip')
    args=p.parse_args();build(args.source_ref,args.output)
