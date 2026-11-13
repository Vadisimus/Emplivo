const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const origin='https://vadisimus.github.io';
const prefix='/Emplivo/';
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2','.xml':'application/xml','.json':'application/json'};
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const errors=[],missing=[];let posts=0;
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.route('**/*',async route=>{
   const req=route.request();const url=new URL(req.url());
   if(req.method()!=='GET'){posts++;await route.abort();return;}
   if(url.origin!==origin||!url.pathname.startsWith(prefix)){missing.push(req.url());await route.abort();return;}
   let file=path.join(root,decodeURIComponent(url.pathname.slice(prefix.length)));
   if(!file.startsWith(root+path.sep)&&file!==root)throw Error('Path escaped fixture root');
   if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
   if(!fs.existsSync(file)){missing.push(req.url());await route.fulfill({status:404,body:'Not found'});return;}
   await route.fulfill({status:200,contentType:types[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
  });
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.goto(origin+prefix);await p.evaluate(()=>document.fonts.ready);
  assert.match(await p.locator('h1').textContent(),/Таланти/);
  assert.equal(await p.locator('#header-navigation a').first().getAttribute('href'),prefix+'jobs/');
  assert.equal(await p.locator('link[rel=canonical]').getAttribute('href'),'https://www.emplivo.com.ua/');
  await p.locator('#hero-search button').click();await p.waitForURL('**/Emplivo/jobs/');
  assert.equal(await p.locator('#catalog-list .job-card').count(),6);
  await p.locator('[data-filter=sector][value=spa]').check();assert.equal(await p.locator('#catalog-list .job-card').count(),2);
  await p.locator('#catalog-list .save-button').first().click();await p.reload();assert.equal(await p.locator('#catalog-list .save-button').first().getAttribute('aria-pressed'),'true');
  await p.locator('#catalog-list [data-action=details]').first().click();await p.locator('#dialog [data-action=apply]').click();
  const fill=async()=>{await p.locator('[name=name]').fill('Demo Candidate');await p.locator('[name=email]').fill('candidate@example.test');await p.locator('[name=phone]').fill('+380671234567');await p.locator('#application-form [type=submit]').click();};
  await fill();await p.locator('#application-form [type=submit]').click();await p.locator('[name=consent]').check();await p.locator('#application-form [type=submit]').click();assert.match(await p.locator('.success-panel').textContent(),/Демо-відгук/);assert.equal(posts,0);await p.keyboard.press('Escape');
  await p.goto(origin+prefix+'#application');
  assert.match(await p.locator('.application-notice').textContent(),/через email/);await fill();
  assert.equal(await p.locator('#cv-upload').count(),0);
  assert.match(await p.locator('#application-form').textContent(),/Прикріпіть PDF/);
  await p.locator('#application-form [type=submit]').click();await p.locator('[name=consent]').check();await p.locator('#application-form [type=submit]').click();
  assert.match(await p.locator('#dialog-title').textContent(),/Лист підготовлено/);
  assert.match(await p.locator('#dialog').textContent(),/Анкету ще не надіслано/);
  assert.equal(await p.locator('#dialog a[href^="mailto:hr@emplivo.com.ua"]').count(),1);assert.equal(posts,0);await p.keyboard.press('Escape');
  await p.goto(origin+prefix+'en/jobs/');assert.equal(await p.locator('html').getAttribute('lang'),'en');assert.equal(await p.locator('#catalog-list .job-card').count(),6);
  assert.equal(await p.locator('#header-navigation a').first().getAttribute('href'),prefix+'en/jobs/');
  assert.equal(await p.locator('link[rel=canonical]').getAttribute('href'),'https://www.emplivo.com.ua/en/jobs/');
  await p.goto(origin+prefix+'jobs/spa-therapist/');assert.match(await p.locator('h1').textContent(),/SPA-терапевти/);
  await p.locator('.seo-language').click();await p.waitForURL('**/Emplivo/en/jobs/spa-therapist/');assert.equal(await p.locator('html').getAttribute('lang'),'en');
  await p.setViewportSize({width:390,height:844});await p.goto(origin+prefix+'jobs/');assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await p.locator('[data-action=filters]').click();assert.equal(await p.locator('#filter-panel').isVisible(),true);
  assert.deepEqual(errors,[]);assert.deepEqual(missing,[]);assert.equal(posts,0);
  console.log('PASS: GitHub Pages project paths, all requested assets, UK/EN routes, search/filter/save, demo zero-POST, honest email-only general application, mobile layout.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
