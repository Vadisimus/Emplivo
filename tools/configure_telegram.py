#!/usr/bin/env python3
"""Configure public Telegram links. Bot tokens are never accepted by this tool."""
from pathlib import Path
from urllib.parse import urlsplit
import argparse
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def validate(group, bot):
    u=urlsplit(group)
    if u.scheme!='https' or u.netloc!='t.me' or u.query or u.fragment or not re.fullmatch(r'/(?:[A-Za-z][A-Za-z0-9_]{4,31}|\+[A-Za-z0-9_-]{16,64})/?',u.path):
        raise ValueError('Use an https://t.me/group_username or https://t.me/+invite address')
    bot=bot.removeprefix('@')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{4,31}',bot) or not bot.lower().endswith('bot'):
        raise ValueError('Use a Telegram bot username ending in bot, without a token')
    return group.rstrip('/'),bot

def public_configuration(group, bot, enabled):
    group, bot = validate(group, bot)
    values = {'groupUrl': group, 'botUsername': bot, 'botEnabled': enabled}
    return ('// Public addresses only. Never put a BotFather token here.\n'
            'window.EMPLIVO_TELEGRAM = Object.freeze(' + json.dumps(values, indent=2) + ');\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group-url', required=True)
    parser.add_argument('--bot-username', required=True)
    parser.add_argument('--enable-bot', action='store_true')
    args = parser.parse_args()
    try:
        configuration = public_configuration(args.group_url, args.bot_username, args.enable_bot)
    except ValueError as error:
        parser.error(str(error))
    (ROOT / 'telegram-config.js').write_text(configuration, encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_vacancies.py')], check=True)
