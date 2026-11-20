#!/usr/bin/env python3
"""Write the public Worker origin and Turnstile site key used by Emplivo forms."""
import argparse
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
    (root / 'intake-config.mjs').write_text('export const intakeConfig = ' + json.dumps(content, indent=2) + ';\n',
                                           encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-origin', required=True)
    parser.add_argument('--site-key', required=True)
    args = parser.parse_args()
    try:
        configure(Path(__file__).resolve().parents[1], args.worker_origin, args.site_key)
    except ValueError as error:
        parser.error(str(error))
