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
DIRECTORIES={'about','api','apply','assets','blog','candidates','cases','contact','demo-account','demo-employer-dashboard','demo-employers','demo-jobs','employers','en','insights','jobs','locations','privacy','ru','salary-guide','saved','submit-vacancy','vacancies'}
OPERATIONS={'tools/telegram_admin.php','tools/TelegramPrivateConfig.php','tools/TelegramWebhookCheck.php','tools/telegram_init.sh','config/telegram.example.php'}

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def public(name):
    p=PurePosixPath(name)
    return name in OPERATIONS or p.parts[0] in DIRECTORIES or (len(p.parts)==1 and (p.suffix in {'.html','.css','.js','.mjs','.xml'} or name in {'.nojekyll','robots.txt','TELEGRAM_UA.md'}))

def web_checks(payload,frontend=False):
    checks=[]
    modern = 'design.css' in payload

    def style_marker(page):
        match=re.search(r'(?:design|wellness|seo)\.css\?v=[A-Za-z0-9]+',page)
        assert match, 'Stylesheet version is missing'
        return match[0]

    for lang,prefix in [('uk',''),('en','en/'),('ru','ru/')]:
        routes = ('','jobs/','employers/','privacy/','contact/')
        if modern:
            routes += ('apply/','saved/')
        for route in routes:
            page=payload[prefix+route+'index.html'].decode()
            assert f'<html lang="{lang}"' in page, prefix+route
            # Requiring the application asset version distinguishes a stale copy from this release.
            bundle=re.search(r'vacancies-data\.js\?v=[a-f0-9]+',page)
            marker=bundle[0] if bundle else f'https://www.emplivo.com.ua/{prefix}{route}'
            checks.append((f'/{prefix}{route}', style_marker(page) if frontend or modern else marker))
        page=payload[f'{prefix}submit-vacancy/index.html'].decode()
        form_marker = 'data-intake="employer"' if modern else 'id="vacancy-brief"'
        assert f'<html lang="{lang}"' in page and form_marker in page
        checks.append((f'/{prefix}submit-vacancy/', style_marker(page) if frontend else form_marker))
    detail_pages=[name for name in sorted(payload) if re.fullmatch(r'(?:en/|ru/)?vacancies/[^/]+/index\.html',name)]
    for name in detail_pages:
        route='/'+name.removesuffix('index.html')
        canonical=f'href="https://www.emplivo.com.ua{route}"'
        assert canonical in payload[name].decode(), name
        checks.append((route,style_marker(payload[name].decode()) if frontend or modern else canonical))
    if modern:
        checks.extend([('/intake.mjs','cf-turnstile-response'),('/navigation.mjs','mountNavigation')])
    else:
        checks.append(('/localization-ru.js','window.EMPLIVO_RU = '))
    return ''.join(f'{route}\t{marker}\n' for route,marker in checks)

def build(ref,output,frontend=False):
    revision=git('rev-parse',ref).decode().strip()
    if frontend:
        # Use the verified design in the working copy and preserve server-side files.
        assets=('design.css','navigation.mjs','jobs.mjs','intake.mjs','intake-config.mjs',
                'assets/mark.svg','assets/recruitment-preview.jpg','assets/workplace-hero.webp','assets/workplace-hero-small.webp')
        names=git('ls-files','--','index.html','*/index.html').decode().splitlines()
        payload={name:(ROOT/name).read_bytes() for name in (*names,*assets) if public(name)}
    else:
        names=git('ls-tree','-r','--name-only',revision).decode().splitlines()
        payload={name:git('show',f'{revision}:{name}') for name in names if public(name)}
        assert '"botEnabled": true' in payload['telegram-config.js'].decode()
    pages=[n for n in payload if n.endswith('/index.html') or n=='index.html']
    assert not any(set(PurePosixPath(n).parts)&{'www','emplivo-private','telegram-state','downloads','.git','deploy-keys'} for n in payload)
    assert not any(PurePosixPath(n).name in {'telegram.php','config.php'} for n in payload)
    manifest=''.join(hashlib.sha256(data).hexdigest()+'  site/'+name+'\n' for name,data in sorted(payload.items()))
    files={'site/'+name:data for name,data in payload.items()}
    files['manifest.sha256']=manifest.encode()
    files['http-checks.tsv']=web_checks(payload,frontend).encode()
    source=f'design {hashlib.sha256(manifest.encode()).hexdigest()[:16]}' if frontend else revision
    files['source-revision.txt']=(source+'\n').encode()
    files['deploy.sh']=(ROOT/'tools/deploy_full_site.sh').read_bytes()
    if frontend:
        files['frontend-assets.sha256']=''.join(
            f'{hashlib.sha256(payload[name]).hexdigest()}  {name}\n' for name in assets
        ).encode()
    else:
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
    print('Prepared source:',source,'public files:',len(payload),'HTML pages:',len(pages),'bytes:',output.stat().st_size)
    print('SHA256:',digest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-ref',default='HEAD');p.add_argument('--output',type=Path,default=ROOT/'downloads/emplivo-full-php-site.zip')
    p.add_argument('--frontend',action='store_true',help='Package the current public design for the existing PHP site.')
    args=p.parse_args()
    if args.frontend and args.output == ROOT/'downloads/emplivo-full-php-site.zip':
        p.error('--frontend needs a separate --output path')
    build(args.source_ref,args.output,args.frontend)
