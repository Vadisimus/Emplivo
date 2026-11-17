#!/usr/bin/env python3
"""Regression tests for malformed private files and hidden terminal token input."""
from pathlib import Path
from tempfile import TemporaryDirectory
import errno
import json
import os
import pty
import select
import shutil
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
PHP=os.environ.get('EMPLIVO_PHP','php')
# Synthetic format-valid fixture, never a live BotFather token.
FAKE='123456789:'+'TEST_ONLY_FAKE_'*3
with TemporaryDirectory(prefix='emplivo-secret-io-') as tmp:
    root=Path(tmp);web=root/'www';private=root/'emplivo-private'
    shutil.copytree(ROOT/'api',web/'api')
    (web/'tools').mkdir()
    private.mkdir(mode=0o700)
    for name in ['telegram_admin.php','TelegramPrivateConfig.php','telegram_init.sh']:
        shutil.copy2(ROOT/'tools'/name,web/'tools'/name)
    (web/'telegram-config.js').write_text('window.EMPLIVO_TELEGRAM = Object.freeze('+json.dumps({
        'groupUrl':'https://t.me/+AbCdeFGhIjKlmN01','botUsername':'Emplivobot','botEnabled':False,
    })+');')
    path=private/'telegram.php'
    cases=[
        "'bot_token' => '"+FAKE+"',",
        "<?php echo '"+FAKE+"'; return [];",
        "<?php var_dump('"+FAKE+"'); return [];",
        "<?php trigger_error('"+FAKE+"'); return [];",
        "<?php return ['bot_token'=>'"+FAKE+"' BROKEN];",
        "<?php return []; ?>"+FAKE,
    ]
    for source in cases:
        path.write_text(source)
        result=subprocess.run([PHP,str(web/'tools/telegram_admin.php'),'prepare'],capture_output=True,timeout=8)
        assert result.returncode==1, 'Malformed private configuration accepted'
        assert FAKE.encode() not in result.stdout+result.stderr, 'Secret printed by setup command'
    # A token-only text file is repaired without evaluating or printing that text.
    path.write_text(cases[0])
    env=os.environ.copy();env['EMPLIVO_TELEGRAM_TOKEN']=FAKE
    result=subprocess.run([PHP,str(web/'tools/telegram_admin.php'),'init'],env=env,capture_output=True,timeout=8)
    assert result.returncode==0, 'Private initialization failed'
    assert FAKE.encode() not in result.stdout+result.stderr
    assert path.read_text().startswith('<?php\n') and 'Emplivobot' in path.read_text()
    assert path.stat().st_mode & 0o777 == 0o600
    # Use a real controlling terminal: read -s must keep the token out of the transcript.
    pid,fd=pty.fork()
    if pid==0:
        os.chdir(web)
        os.environ.pop('EMPLIVO_TELEGRAM_TOKEN',None)
        os.environ['EMPLIVO_PHP']=PHP
        os.execvp('bash',['bash',str(web/'tools/telegram_init.sh')])
    captured=b'';sent=False;status=None
    deadline=time.monotonic()+10
    try:
        while time.monotonic()<deadline:
            readable,_,_=select.select([fd],[],[],.1)
            if readable:
                try:chunk=os.read(fd,65536)
                except OSError as e:
                    if e.errno==errno.EIO:break
                    raise
                if not chunk:break
                captured+=chunk
            if not sent and 'натисніть Enter: '.encode() in captured:
                os.write(fd,FAKE.encode()+b'\n');sent=True
        _,status=os.waitpid(pid,os.WNOHANG)
        if status==0:
            # waitpid returns pid=0 while alive; completed success also has status=0.
            try:
                remaining,completed=os.waitpid(pid,os.WNOHANG)
                if remaining==pid:status=completed
                elif remaining==0:raise AssertionError('Hidden terminal input timed out')
            except ChildProcessError:pass
        assert sent and os.waitstatus_to_exitcode(status)==0, 'Hidden initialization failed'
        assert FAKE.encode() not in captured, 'Token appeared in terminal transcript'
        assert 'Налаштування підготовлено'.encode() in captured
    finally:
        os.close(fd)
        try:
            remaining,_=os.waitpid(pid,os.WNOHANG)
            if remaining==0:
                os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)
        except ChildProcessError:pass
    print('PASS: malformed/printing/warning private configs rejected without secret output; private initialization and real terminal hidden input. No Telegram calls.')
