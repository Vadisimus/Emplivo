const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base='http://127.0.0.1:8085';
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],headless:true});
 const errors=[],external=[];let posts=0;const ids=[];
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  context.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))external.push(r.url());});
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.route('**/api/applications.php',async route=>{
   assert.equal(route.request().method(),'POST');const body=route.request().postData();
   const id=body.match(/name="submissionId"\r\n\r\n([^\r]+)/)?.[1];assert(id);ids.push(id);posts++;
   assert(!body.includes('demo-spa-01'));
   await route.fulfill({status:posts===1?503:200,contentType:'application/json',body:JSON.stringify(posts===1?{message:'Simulated outage'}:{ok:true,id})});
  });
  await p.goto(base+'/');
  assert.match(await p.locator('h1').textContent(),/Таланти/);
  assert.equal(await p.locator('#header-navigation a').first().getAttribute('href'),'/jobs/');
  await p.locator('#hero-query').fill('тренер');await p.locator('#hero-search button').click();
  await p.waitForURL('**/jobs/?**');assert.equal(await p.locator('#catalog-list .job-card').count(),2);
  await p.locator('[data-action=reset-filters]').first().click();
  await p.locator('[data-filter=sector][value=spa]').check();assert.equal(await p.locator('#catalog-list .job-card').count(),2);
  await p.locator('#catalog-list .save-button').first().click();await p.reload();assert.equal(await p.locator('#catalog-list .save-button').first().getAttribute('aria-pressed'),'true');
  await p.locator('#catalog-list [data-action=details]').first().click();await p.locator('#dialog [data-action=apply]').click();
  const contacts=async()=>{await p.locator('[name=name]').fill('Test Candidate');await p.locator('[name=email]').fill('candidate@example.test');await p.locator('[name=phone]').fill('+380671234567');await p.locator('#application-form [type=submit]').click();await p.locator('#application-form [type=submit]').click();await p.locator('[name=consent]').check();};
  await contacts();await p.locator('#application-form [type=submit]').click();assert.match(await p.locator('.success-panel').textContent(),/Демо-відгук/);assert.equal(posts,0);
  await p.keyboard.press('Escape');
  await p.goto(base+'/#application');assert.equal(await p.locator('.application-notice').count(),1);await contacts();
  await p.locator('#application-form [type=submit]').click();await p.locator('#application-error').waitFor({state:'visible'});await p.waitForFunction(()=>!document.querySelector('#application-form [type=submit]').disabled);
  await p.locator('#application-form [type=submit]').click();await p.locator('.success-panel').waitFor({state:'visible'});
  assert.match(await p.locator('.success-panel').textContent(),/Анкету збережено|анкету збережено/);
  assert(!/демонстрація/.test(await p.locator('#dialog-title').textContent()));assert.equal(posts,2);assert.equal(ids[0],ids[1]);
  assert(!await p.evaluate(()=>JSON.stringify(localStorage).includes('candidate@example.test')));
  await p.keyboard.press('Escape');
  await p.goto(base+'/employers/');await p.locator('#main [data-action=brief]').click();
  await p.locator('[name=company]').fill('Example employer');await p.locator('[name=location]').fill('Kyiv');await p.locator('#brief-form [type=submit]').click();
  await p.locator('[name=role]').fill('Spa therapist');await p.locator('[name=start]').fill('Next month');await p.locator('#brief-form [type=submit]').click();
  await p.locator('[name=name]').fill('Test employer');await p.locator('[name=email]').fill('employer@example.test');await p.locator('#brief-form [type=checkbox]').check();await p.locator('#brief-form [type=submit]').click();
  assert.match(await p.locator('#dialog').textContent(),/не надсилає лист автоматично/);assert.equal(await p.locator('#dialog a[href^="mailto:"]').count(),1);await p.keyboard.press('Escape');
  for(const width of [360,390,768,1440]){await p.setViewportSize({width,height:900});for(const route of ['/','/jobs/','/employers/','/about/','/en/','/jobs/spa-therapist/']){await p.goto(base+route);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),route+' at '+width);}}
  await p.goto(base+'/en/');assert.equal(await p.locator('html').getAttribute('lang'),'en');assert.match(await p.locator('h1').textContent(),/People/);assert.equal(await p.locator('#header-navigation a').first().getAttribute('href'),'/en/jobs/');
  const nojs=await browser.newContext({javaScriptEnabled:false});const stat=await nojs.newPage();await stat.goto(base+'/jobs/');assert.equal(await stat.locator('#catalog-list .job-card').count(),6);assert.equal(await stat.locator('link[rel=canonical]').getAttribute('href'),'https://www.emplivo.com.ua/jobs/');await nojs.close();
  await p.setViewportSize({width:1440,height:1000});await p.goto(base+'/');await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:'/workspace/reports/wellness-release-desktop.png',animations:'disabled'});
  await p.setViewportSize({width:390,height:844});await p.goto(base+'/jobs/');await p.screenshot({path:'/workspace/reports/wellness-release-mobile.png',animations:'disabled'});
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('PASS: public routes, live search/filters/saves, demo zero POST, real general application mocked success+retry, idempotency, mailto brief, UK/EN, static no-JS catalogue, 360/390/768/1440 layouts. No production application writes.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
