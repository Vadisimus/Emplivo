#!/usr/bin/env python3
"""Check public release routes, internal links, JSON-LD and demo isolation."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin, unquote
import urllib.request
import urllib.error
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8082'

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=set();self.links=[];self.schemas=[];self.h1=0;self.canon=[];self.noindex=False;self.jsonld=False;self.buffer='';self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, 'Duplicate HTML id: '+a['id']
            self.ids.add(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='h1':self.h1+=1
        if tag=='link' and a.get('rel')=='canonical':self.canon.append(a.get('href'))
        if tag=='meta' and a.get('name')=='robots' and 'noindex' in a.get('content',''):self.noindex=True
        if tag=='script' and a.get('type')=='application/ld+json':self.jsonld=True;self.buffer=''
    def handle_data(self,data):
        if self.jsonld:self.buffer+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.jsonld:self.schemas.append(json.loads(self.buffer));self.jsonld=False

docs={}
for f in ROOT.rglob('index.html'):
    if '.git' in f.parts:continue
    route='/'+f.relative_to(ROOT).as_posix().removesuffix('index.html')
    text=f.read_text();doc=Document(text)
    assert doc.h1==1,(route,'expected one h1')
    assert len(doc.canon)==1 and doc.canon[0]=='https://www.emplivo.com.ua'+route,(route,doc.canon)
    assert not any(s in text for s in ['Помічник кухаря','Kitchen Helper','kitchen-helper-ua-001','+380631395033','+380 63 139 50 33']),route
    assert '+380677778060' in text or '+380 (67) 777 80 60' in text,route
    assert doc.schemas,route
    if '/demo-' in route:
        assert doc.noindex,route
        assert 'JobPosting' not in text and 'AggregateRating' not in text,route
    with urllib.request.urlopen(BASE+route,timeout=5) as r:assert r.status==200,route
    docs[route]=doc

link_count=0
for route,doc in docs.items():
    for link in doc.links:
        u=urlsplit(urljoin('https://www.emplivo.com.ua'+route,link))
        if u.scheme not in ('http','https') or u.netloc!='www.emplivo.com.ua':continue
        dest=u.path or '/'
        assert dest in docs,(route,'broken internal link',link)
        if u.fragment:assert unquote(u.fragment) in docs[dest].ids,(route,'missing fragment',link)
        link_count+=1

sitemap=ET.parse(ROOT/'sitemap.xml')
locs=[e.text for e in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(locs)==len(set(locs))
for loc in locs:
    path=urlsplit(loc).path
    assert path in docs and not docs[path].noindex,(loc,'bad sitemap entry')
assert all('/demo-' not in loc for loc in locs)

for asset in ['styles.css','modern.css','seo.css','seo.js','app.js','translations.js','jobs-data.js']:
    with urllib.request.urlopen(BASE+'/'+asset,timeout=5) as r:assert r.status==200
try:urllib.request.urlopen(BASE+'/api/applications.php',timeout=5)
except urllib.error.HTTPError as e:assert e.code==405 and 'message' in json.loads(e.read())
else:raise AssertionError('API must reject GET')

# Local PHP rejects demo roles before loading credentials or calling any upstream service.
data=b'--boundary\r\nContent-Disposition: form-data; name="role"\r\n\r\ndemo-spa-01\r\n--boundary--\r\n'
req=urllib.request.Request(BASE+'/api/applications.php',data=data,headers={'Content-Type':'multipart/form-data; boundary=boundary'})
try:urllib.request.urlopen(req,timeout=5)
except urllib.error.HTTPError as e:assert e.code==422 and 'message' in json.loads(e.read())
else:raise AssertionError('Demo role must never be forwarded')
print(f'PASS: {len(docs)} pages, {link_count} internal links, {len(locs)} sitemap entries, JSON-LD, phone, assets, API GET and demo guard')
