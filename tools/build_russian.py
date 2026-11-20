#!/usr/bin/env python3
"""Build Russian editorial pages, localized static shells and language links."""
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://www.emplivo.com.ua'
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
LANGUAGES = {'uk': ('UA', 'Українська', ''), 'en': ('EN', 'English', 'en/'), 'ru': ('RU', 'Русский', 'ru/')}
SKIP_GENERATED = {'vacancies', 'submit-vacancy'}
ALTERNATE = r'<link\b(?=[^>]*\brel="alternate")(?=[^>]*\bhreflang=)[^>]*>\s*'
CORE_SWITCH = r'<button class="language"[^>]*>.*?</button>|<nav class="language-options"[^>]*>.*?</nav>'
SEO_SWITCH = r'<div class="seo-language-options"[^>]*>.*?</div>|<a class="seo-language"[^>]*>.*?</a>'
LOCALE_SCRIPT = r'<script defer src="[^"]*localization-ru\.js"></script>\s*'


def translation_dictionary(root):
    combined = {}
    for name in ('editorial-ru.json', 'wellness-ru.json'):
        combined.update(json.loads((root / 'content' / name).read_text(encoding='utf-8')))
    for en, ru in list(combined.items()):
        for splitter in (r'<[^>]+>', r' • ', r' · '):
            left, right = re.split(splitter, en), re.split(splitter, ru)
            if len(left) == len(right) > 1:
                for key, value in zip(left, right):
                    if key.strip() and value.strip():
                        combined.setdefault(key.strip(), value.strip())
    return combined


def localized_text(text, words):
    if not text.strip():
        return text
    key = ' '.join(text.split())
    result = words.get(key)
    if result is None and ' — ' in key:
        parts = key.split(' — ')
        translated = [words.get(part, part) for part in parts]
        if translated != parts:
            result = ' — '.join(translated)
    return text[:len(text)-len(text.lstrip())] + result + text[len(text.rstrip()):] if result is not None else text


class LocaleHTML(HTMLParser):
    def __init__(self, route, routes, words):
        super().__init__(convert_charrefs=True)
        self.route, self.routes, self.words = route, routes, words
        self.output = []
        self.raw = ''
        self.raw_type = ''

    def link(self, value):
        if not value or value.startswith(('#', 'mailto:', 'tel:')):
            return value
        target = urlsplit(urljoin(f'{SITE}/en/{self.route}', value))
        if target.netloc != urlsplit(SITE).netloc or not target.path.startswith('/en/'):
            return value
        route = target.path.removeprefix('/en/')
        if route not in self.routes:
            return value
        path = '/' + posixpath.join('ru', route)
        if value.startswith(('https://', 'http://')):
            return urlunsplit((target.scheme, target.netloc, path, target.query, target.fragment))
        relative = posixpath.relpath(path, '/ru/' + self.route) + '/'
        return urlunsplit(('', '', relative, target.query, target.fragment))

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag in ('script', 'style'):
            self.raw = tag
            self.raw_type = data.get('type', '')
        result = []
        for key, value in attrs:
            if value is not None:
                if (tag == 'html' and key == 'lang'):
                    value = 'ru'
                elif key in ('aria-label','placeholder','alt','title') or (tag == 'meta' and key == 'content' and data.get('name', data.get('property')) in ('description','og:title','og:description')):
                    value = localized_text(value, self.words)
                elif (tag in ('a','link') and key == 'href') or (tag == 'meta' and key == 'content' and data.get('property') == 'og:url'):
                    value = self.link(value)
                elif tag == 'form' and key == 'action':
                    value = self.link(value)
            result.append(' ' + key + ('="' + escape(value, quote=True) + '"' if value is not None else ''))
        self.output.append('<' + tag + ''.join(result) + '>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self.output.append(f'</{tag}>')
        if tag == self.raw:
            self.raw = self.raw_type = ''

    def handle_data(self, text):
        if self.raw == 'script' and self.raw_type == 'application/ld+json':
            def convert(value, key=None):
                if isinstance(value, dict):
                    return {k: convert(v, k) for k,v in value.items()}
                if isinstance(value, list):
                    return [convert(entry,key) for entry in value]
                if not isinstance(value, str):
                    return value
                if key == 'inLanguage':
                    return 'ru'
                if value.startswith(SITE):
                    return self.link(value)
                if key in ('name','headline','description'):
                    return localized_text(value,self.words)
                return value
            self.output.append(json.dumps(convert(json.loads(text)),ensure_ascii=False).replace('<','\\u003c'))
        elif self.raw:
            self.output.append(text)
        else:
            self.output.append(escape(localized_text(text,self.words), quote=False))

    def handle_comment(self, text):
        self.output.append(f'<!--{text}-->')

    def handle_decl(self, text):
        self.output.append(f'<!{text}>')


def locale_links(route, lang, core=False):
    depth = len((LANGUAGES[lang][2] + route).strip('/').split('/')) if LANGUAGES[lang][2] + route else 0
    base = '../' * depth or './'
    names = {'uk': 'Мова сайту', 'en': 'Website language', 'ru': 'Язык сайта'}
    links = []
    for code, (short, label, prefix) in LANGUAGES.items():
        css = 'language' if core else 'seo-language'
        current = ' aria-current="page"' if code == lang else ''
        links.append(f'<a class="{css}" lang="{code}" hreflang="{code}" aria-label="{label}"{current} href="{base}{prefix}{route}">{short}</a>')
    klass = 'language-options' if core else 'seo-language-options'
    tag = 'nav' if core else 'div'
    return f'<{tag} class="{klass}" aria-label="{names[lang]}">' + ''.join(links) + f'</{tag}>'


def apply_language_links(text, route, lang):
    core = 'data-mode="public"' in text
    alternatives = ''.join(f'<link rel="alternate" hreflang="{code}" href="{SITE}/{prefix}{route}">' for code, (_,_,prefix) in LANGUAGES.items())
    alternatives += f'<link rel="alternate" hreflang="x-default" href="{SITE}/{route}">\n'
    text = re.sub(ALTERNATE, '', text)
    text = text.replace('</head>', alternatives + '</head>', 1)
    text, count = re.subn(CORE_SWITCH if core else SEO_SWITCH, lambda _: locale_links(route, lang, core), text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f'Missing language navigation on {lang}/{route}')
    return text


def build(root=ROOT):
    words = translation_dictionary(root)
    routes = {}
    for page in (root / 'en').rglob('index.html'):
        rel = page.relative_to(root / 'en')
        if rel.parts[0] in SKIP_GENERATED:
            continue
        route = rel.as_posix().removesuffix('index.html')
        if (root / route / 'index.html').is_file():
            routes[route] = page
    (root / 'localization-ru.js').write_text(
        'window.EMPLIVO_RU = ' + json.dumps(words,ensure_ascii=False,indent=2) + ';\n', encoding='utf-8')
    for route, en_page in sorted(routes.items()):
        english = en_page.read_text(encoding='utf-8')
        parser = LocaleHTML(route, routes, words)
        parser.feed(english)
        localized = apply_language_links(''.join(parser.output), route, 'ru')
        if 'data-mode="public"' in localized:
            depth = len(('ru/' + route).strip('/').split('/'))
            tag = f'<script defer src="{"../"*depth}localization-ru.js"></script>\n'
            localized = re.sub(LOCALE_SCRIPT, '', localized)
            localized = re.sub(r'<script\b(?=[^>]*\bsrc="[^"]*wellness\.js\?)[^>]*>', lambda m: tag + m[0], localized, count=1)
        ru_page = root / 'ru' / route / 'index.html'
        ru_page.parent.mkdir(parents=True, exist_ok=True)
        ru_page.write_text(localized, encoding='utf-8')
        for lang, page in [('uk', root / route / 'index.html'), ('en', en_page)]:
            original = page.read_text(encoding='utf-8')
            updated = apply_language_links(original, route, lang)
            if updated != original:
                page.write_text(updated, encoding='utf-8')

    sitemap = root / 'sitemap.xml'
    ET.register_namespace('', NS)
    tree = ET.parse(sitemap)
    entries = tree.getroot()
    editorial_urls = {f'{SITE}/ru/{route}' for route in routes}
    for item in list(entries):
        if item.findtext(f'{{{NS}}}loc') in editorial_urls:
            entries.remove(item)
    for route in sorted(routes):
        if '/noindex' in route or 'noindex' in (root / 'ru' / route / 'index.html').read_text(encoding='utf-8').split('</head>',1)[0]:
            continue
        node = ET.SubElement(entries, f'{{{NS}}}url')
        ET.SubElement(node, f'{{{NS}}}loc').text = f'{SITE}/ru/{route}'
    ET.indent(tree, space='  ')
    tree.write(sitemap, encoding='utf-8', xml_declaration=True)
    print(f'Russian website pages generated: {len(routes)}')


if __name__ == '__main__':
    build()
