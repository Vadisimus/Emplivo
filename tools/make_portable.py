#!/usr/bin/env python3
"""Make the pre-rendered site work at / and under a GitHub Pages project path."""
from pathlib import Path
import re
import sys

def make_portable(root):
    root=Path(root).resolve()
    app_path=root/'wellness.js'
    app=app_path.read_text()
    if 'const SITE_BASE =' not in app:
        app=app.replace("  const PUBLIC = document.documentElement.dataset.mode === 'public';", "  const PUBLIC = document.documentElement.dataset.mode === 'public';\n  const SITE_BASE = new URL('.', document.currentScript.src).pathname;\n  const EMAIL_ONLY = PUBLIC && location.hostname.endsWith('.github.io');")
        app=app.replace("=> '/' + (locale === 'en'", "=> SITE_BASE + (locale === 'en'")
        app=app.replace("  const read =", "  const productionURL = (name, locale = language) => 'https://www.emplivo.com.ua/' + (locale === 'en' ? 'en/' : '') + (routePaths[name] ?? '');\n  const read =",1)
        old="const path = location.pathname.replace(/^\\/en\\//,'/').replace(/^\\//,'').replace(/index\\.html$/,'');"
        new="const localPath = location.pathname.startsWith(SITE_BASE) ? location.pathname.slice(SITE_BASE.length) : location.pathname.replace(/^\\//,''); const path = localPath.replace(/^en\\//,'').replace(/index\\.html$/,'');"
        assert old in app,'Route normalisation changed; review portable patch'
        app=app.replace(old,new)
        app=app.replace("$('#system-link').href = '/' +", "$('#system-link').href = SITE_BASE +")
        app=app.replace('href="/${language', 'href="${SITE_BASE}${language')
        app=app.replace('href="/assets/', 'href="${SITE_BASE}assets/').replace('src="/assets/','src="${SITE_BASE}assets/')
        app=app.replace("'https://www.emplivo.com.ua'+publicPath(page)","productionURL(page)")
        app=app.replace("'https://www.emplivo.com.ua'+publicPath(page,'uk')","productionURL(page,'uk')")
        app=app.replace("'https://www.emplivo.com.ua'+publicPath(page,'en')","productionURL(page,'en')")
        app=app.replace("fetch('/api/applications.php'", "fetch(SITE_BASE+'api/applications.php'")
        # A static host cannot save an application or accept a CV. Prepare email,
        # with a copy fallback, instead of submitting to an unavailable PHP URL.
        app=app.replace("const real = PUBLIC && !j;", "const real = PUBLIC && !j;\n    const emailOnly = real && EMAIL_ONLY;")
        app=app.replace("    if(a.step===2) body=", "    if(emailOnly && a.step===1) body=body.replace(/<label class=\"upload\">[\\s\\S]*?<\\/label><p class=\"form-error\" id=\"file-error\" hidden><\\/p>/, `<p class=\"application-notice\">${t('На GitHub Pages резюме не завантажується. Прикріпіть PDF або DOCX до листа у своїй поштовій програмі.','GitHub Pages cannot receive CV uploads. Attach your PDF or DOCX to the email in your mail app.')}</p>`);\n    if(a.step===2) body=")
        app=app.replace("real?t('Надіслати загальну анкету','Submit general application')", "real?(emailOnly?t('Підготувати лист','Prepare email'):t('Надіслати загальну анкету','Submit general application'))")
        old_notice="${real ? t('Реальне звернення: після надсилання анкета потрапить команді Emplivo. Це не відгук на вигадану вакансію.','Real enquiry: submitting sends your application to Emplivo. This is not an application for a fictional job.')"
        new_notice="${real ? (emailOnly ? t('Ця версія працює через email. Форма підготує лист, який ви надішлете самостійно; дані не зберігаються на GitHub Pages.','This version works by email. The form prepares a message for you to send; data is not saved on GitHub Pages.') : t('Реальне звернення: після надсилання анкета потрапить команді Emplivo. Це не відгук на вигадану вакансію.','Real enquiry: submitting sends your application to Emplivo. This is not an application for a fictional job.'))"
        assert old_notice in app,'General application notice changed'
        app=app.replace(old_notice,new_notice)
        app=app.replace("    const a=application;if(!a||a.submitting)return;", "    const a=application;if(!a||a.submitting)return;\n    if(EMAIL_ONLY){prepareGeneralEmail();return;}")
        marker='  function prepareBriefEmail(){'
        assert marker in app
        app=app.replace(marker,r'''
  function prepareGeneralEmail(){
    const a=application;if(!a)return;
    const body=[t('Загальна анкета Emplivo','Emplivo general application'),a.name,a.email,a.phone,a.city,a.experience,'',t('Резюме додається до листа окремо, за бажанням.','A CV can be attached separately to this email.')].filter(Boolean).join('\n');
    const href='mailto:hr@emplivo.com.ua?subject='+encodeURIComponent('Emplivo — '+t('загальна анкета','general application'))+'&body='+encodeURIComponent(body);
    application=null;
    openDialog(t('Лист підготовлено','Your email is ready'),`<p class="dialog-subtitle">${t('Анкету ще не надіслано. Відкрийте поштову програму або скопіюйте текст у лист на hr@emplivo.com.ua. За бажанням прикріпіть резюме вручну.','Your application has not been sent. Open your email app or copy this text into a message to hr@emplivo.com.ua. Attach your CV manually if you wish.')}</p><a class="button button-primary" href="${escape(href)}" target="_blank" rel="noopener noreferrer">${t('Відкрити поштову програму','Open email app')}</a><label class="field" style="margin-top:20px"><span>${t('Текст для копіювання','Text to copy')}</span><textarea rows="10" readonly>${escape(body)}</textarea></label>`,true);
  }
''' + marker)
        app_path.write_text(app)

    count=0
    for html in root.rglob('*.html'):
        if '.git' in html.parts:continue
        prefix='../'*len(html.relative_to(root).parent.parts) or './'
        original=html.read_text()
        text=re.sub(r'\b(href|src|action)=("|\')/(?!/)([^"\']*)\2',lambda m:m[1]+'='+m[2]+prefix+m[3]+m[2],original)
        text=re.sub(r'(?i)(content=["\'][^"\']*url=)/(?!/)',lambda m:m[1]+prefix,text)
        if text!=original:html.write_text(text);count+=1
    for css in root.glob('*.css'):
        text=css.read_text();updated=re.sub(r'url\((["\']?)/(?!/)',r'url(\1',text)
        if updated!=text:css.write_text(updated)
    (root/'.nojekyll').write_text('')
    print('Portable root/project-path navigation enabled; HTML files updated:',count)

if __name__=='__main__':make_portable(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
