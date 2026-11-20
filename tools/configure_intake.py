#!/usr/bin/env python3
"""Write the public Worker origin and Turnstile site key used by Emplivo forms."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def configure(root, origin, site_key):
    url = urlsplit(origin)
    if (url.scheme != 'https' or not url.hostname or url.port not in (None, 443)
            or url.path not in ('', '/') or url.username or url.password or url.query or url.fragment):
        raise ValueError('Use an HTTPS origin without credentials, path, query or fragment.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{6,80}', site_key):
        raise ValueError('Enter the public Turnstile site key.')
    content = {'workerOrigin': f'https://{url.netloc}', 'siteKey': site_key}
    config = root / 'intake-config.mjs'
    config.write_text('export const intakeConfig = ' + json.dumps(content, indent=2) + ';\n', encoding='utf-8')
    manifest = root / 'CHECKSUMS.json'
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if config.name in data.get('files', {}):
            data['files'][config.name] = sha256(config.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-origin', required=True)
    parser.add_argument('--site-key', required=True)
    args = parser.parse_args()
    try:
        configure(Path(__file__).resolve().parents[1], args.worker_origin, args.site_key)
    except ValueError as error:
        parser.error(str(error))
