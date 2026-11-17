#!/usr/bin/env python3
"""Configure public Telegram links. Bot tokens are never accepted by this tool."""
from pathlib import Path
from urllib.parse import urlsplit
from html import escape
import argparse
import json
import re

ROOT=Path(__file__).resolve().parents[1]

def validate(group, bot):
    u=urlsplit(group)
    if u.scheme!='https' or u.netloc!='t.me' or u.query or u.fragment or not re.fullmatch(r'/[A-Za-z][A-Za-z0-9_]{4,31}/?',u.path):
        raise ValueError('Use the public https://t.me/group_username address')
    bot=bot.removeprefix('@')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{4,31}',bot) or not bot.lower().endswith('bot'):
        raise ValueError('Use a Telegram bot username ending in bot, without a token')
    return group.rstrip('/'),bot

def install_scripts(root=ROOT):
    count=0
    for page in root.rglob('index.html'):
        if '.git' in page.parts:continue
        prefix='../'*len(page.relative_to(root).parent.parts) or './'
        text=page.read_text()
        if 'telegram-config.js' not in text:
            tags=f'<script defer src="{prefix}telegram-config.js?v=20261117"></script><script defer src="{prefix}telegram.js?v=20261117"></script>'
            # Load configuration before the main app or editorial enhancements.
            m=re.search(r'<script\b[^>]*\bsrc=',text)
            pos=m.start() if m else text.index('</head>')
            text=text[:pos]+tags+'\n'+text[pos:]
            page.write_text(text);count+=1
    return count

def write_links(group,bot):
    group,bot=validate(group,bot)
    (ROOT/'telegram-config.js').write_text('// Public addresses only. Never put a BotFather token here.\nwindow.EMPLIVO_TELEGRAM = Object.freeze('+json.dumps({'groupUrl':group,'botUsername':bot},ensure_ascii=False,indent=2)+');\n')
    # Keep useful links in pre-rendered HTML, including without JavaScript.
    for page in ROOT.rglob('index.html'):
        if '.git' in page.parts:continue
        text=page.read_text();en=page.relative_to(ROOT).parts[0]=='en'
        items=[(group,'Telegram job group' if en else 'Група вакансій у Telegram'),('https://t.me/'+bot+'?start=apply','Apply with the Telegram bot' if en else 'Анкета через Telegram-бота')]
        block='<nav class="telegram-static-links" aria-label="Telegram">'+''.join('<a href="'+escape(url,quote=True)+'" target="_blank" rel="noopener noreferrer">'+label+'</a>' for url,label in items)+'</nav>'
        text=re.sub(r'<nav class="telegram-static-links"[^>]*>.*?</nav>','',text,flags=re.S)
        text=text.replace('</footer>',block+'</footer>',1)
        page.write_text(text)
    print('Configured public Telegram addresses:',group,'@'+bot)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--group-url');p.add_argument('--bot-username');p.add_argument('--install-only',action='store_true');args=p.parse_args()
    print('Installed Telegram scripts on pages:',install_scripts())
    if not args.install_only:
        if not args.group_url or not args.bot_username:p.error('--group-url and --bot-username are required; do not supply a token')
        write_links(args.group_url,args.bot_username)
