#!/usr/bin/env python3
"""Validate address handling and idempotent static page configuration."""
from pathlib import Path
from tempfile import TemporaryDirectory
import contextlib
import io
import configure_telegram as config

for group, bot in [
    ('https://evil.example/EmplivoGroup', 'ExampleBot'),
    ('https://t.me/EmplivoGroup?token=oops', 'ExampleBot'),
    ('https://t.me/EmplivoGroup', '123456789:NOT_A_USERNAME'),
    ('https://t.me/+short', 'ExampleBot'),
    ('https://web.telegram.org/k/#-123456789', 'ExampleBot'),
]:
    try:
        config.validate(group, bot)
    except ValueError:
        pass
    else:
        raise AssertionError('Unsafe public configuration accepted')

with TemporaryDirectory(prefix='emplivo-public-telegram-') as tmp:
    root=Path(tmp)
    for relative in ['index.html','en/index.html','jobs/spa-therapist/index.html','en/jobs/spa-therapist/index.html']:
        p=root/relative
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('<html><head><script defer src="/wellness.js"></script></head><body><footer></footer></body></html>')
    assert config.install_scripts(root)==4
    assert config.install_scripts(root)==0
    config.ROOT=root
    with contextlib.redirect_stdout(io.StringIO()):
        config.write_links('https://t.me/+AbCdeFGhIjKlmN01','@EmplivoApplyExampleBot')
    for p in root.rglob('index.html'):
        text=p.read_text()
        assert 'https://t.me/+AbCdeFGhIjKlmN01' in text
        assert '?start=apply' not in text, 'Unverified bot must stay inactive'
    with contextlib.redirect_stdout(io.StringIO()):
        config.write_links('https://t.me/EmplivoGroupExample','@EmplivoApplyExampleBot',True)
        before={p:p.read_text() for p in root.rglob('index.html')}
        config.write_links('https://t.me/EmplivoGroupExample','@EmplivoApplyExampleBot',True)
    for p,previous in before.items():
        text=p.read_text()
        assert text==previous, 'Public setup must be repeatable'
        assert text.count('class="telegram-static-links"')==1
        assert text.index('telegram-config.js')<text.index('telegram.js')<text.index('/wellness.js')
        assert 'EmplivoApplyExampleBot?start=apply' in text
        assert ('Apply with' in text)==(p.relative_to(root).parts[0]=='en')
        prefix='../'*len(p.relative_to(root).parent.parts) or './'
        assert f'src="{prefix}telegram-config.js' in text
print('PASS: public URL/username validation, static links, UK/EN labels, nested paths, repeated configuration.')
