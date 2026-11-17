#!/usr/bin/env python3
"""Exercise HTTP guards on an isolated PHP server; no real Telegram calls."""
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import shutil
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PHP = os.environ.get('EMPLIVO_PHP', 'php')
SECRET_MARKER = b'TEST_PRIVATE_SECRET_DO_NOT_PRINT'
with TemporaryDirectory(prefix='emplivo-webhook-') as tmp:
    root = Path(tmp)
    public = root/'www'
    shutil.copytree(ROOT/'api', public/'api')
    private = root/'emplivo-private'
    private.mkdir(mode=0o700)
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    process = subprocess.Popen([PHP, '-S', f'127.0.0.1:{port}', '-t', str(public)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    def request(method='POST', data=b'{}', headers=None):
        req = Request(f'http://127.0.0.1:{port}/api/telegram-webhook.php', method=method, data=None if method=='GET' else data, headers=headers or {'Content-Type':'application/json'})
        try:
            with urlopen(req, timeout=3) as response:
                assert SECRET_MARKER not in response.read(), 'Private configuration leaked in HTTP response'
                return response.status
        except HTTPError as e:
            assert SECRET_MARKER not in e.read(), 'Private configuration leaked in HTTP error'
            return e.code
    try:
        for attempt in range(40):
            try:
                assert request('GET') == 405
                break
            except URLError:
                time.sleep(.1)
        else:
            raise AssertionError('PHP server unavailable')
        assert request() == 503, 'Missing configuration must fail closed'
        (private/'telegram.php').write_text("'bot_token' => '"+SECRET_MARKER.decode()+"',")
        assert request() == 503, 'Raw configuration must fail without disclosing its contents'
        secret = 'test_secret_'*4
        config = "<?php return ['bot_token'=>'123456789:"+'x'*35+"','webhook_secret'=>'"+secret+"','state_key'=>base64_encode(str_repeat('s',32)), 'admin_chat_id'=>'999888777','group_url'=>'https://t.me/EmplivoGroupExample','site_url'=>'https://www.emplivo.com.ua','state_dir'=>"+repr(str(root/'state'))+"];"
        (private/'telegram.php').write_text(config)
        assert request() == 403, 'Missing secret'
        headers={'Content-Type':'application/json','X-Telegram-Bot-Api-Secret-Token':secret}
        probe=json.dumps({'update_id':0,'emplivo_probe':True}).encode()
        assert request(data=probe)==403, 'Runtime probe requires the webhook secret'
        probe_request=Request(f'http://127.0.0.1:{port}/api/telegram-webhook.php',method='POST',data=probe,headers=headers)
        with urlopen(probe_request,timeout=3) as response:
            assert response.status==200
            assert response.headers.get('X-Emplivo-Telegram')=='1'
            body=response.read()
            result=json.loads(body)
            assert result['probe']=='emplivo-webhook'
            assert all(isinstance(result['checks'][key],bool) for key in ['curl','sodium','state_writable'])
            assert b'bot_token' not in body and secret.encode() not in body and SECRET_MARKER not in body
        assert request(data=b'bad json',headers=headers) == 400
        assert request(data=b'{}',headers=headers) == 400
        assert request(data=b'x'*65537,headers=headers) == 413
        assert request(headers={'Content-Type':'text/plain'}) == 415
        update={'update_id':1,'message':{'chat':{'id':-100123456,'type':'supergroup'},'from':{'id':1234567,'is_bot':False},'text':'/apply'}}
        assert request(data=json.dumps(update).encode(),headers=headers) == 200, 'Group messages ignored without external calls'
        print('PASS: POST/JSON guards, missing configuration, webhook authentication, malformed/oversized body, group isolation. No Telegram calls.')
    finally:
        process.terminate()
        process.wait(timeout=5)
