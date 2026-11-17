const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const origin='https://vadisimus.github.io';
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
  for(const fixture of [null,{groupUrl:'https://t.me/EmplivoGroupExample',botUsername:'EmplivoApplyExampleBot'},{groupUrl:'https://evil.example/t.me/group',botUsername:'badbot?token=secret'}]){
   const context=await browser.newContext({viewport:{width:390,height:844}});
   const errors=[],missing=[];
   await context.route('**/*',async route=>{
    const u=new URL(route.request().url());
    assert.equal(route.request().method(),'GET');
    assert.equal(u.origin,origin,'No external requests or Telegram messages during tests');
    assert(u.pathname.startsWith('/Emplivo/'));
    if(fixture&&u.pathname.endsWith('/telegram-config.js')){
     await route.fulfill({contentType:'application/javascript',body:'window.EMPLIVO_TELEGRAM='+JSON.stringify(fixture)});return;
    }
    let file=path.resolve(root,decodeURIComponent(u.pathname.slice('/Emplivo/'.length)));
    assert(file===root||file.startsWith(root+path.sep));
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file)){missing.push(u.pathname);await route.fulfill({status:404,body:'Missing'});return;}
    await route.fulfill({contentType:types[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
   });
   const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
   const valid=fixture?.botUsername==='EmplivoApplyExampleBot';
   for(const route of ['', 'en/', 'jobs/spa-therapist/', 'en/jobs/spa-therapist/']){
    await p.goto(origin+'/Emplivo/'+route);
    const footer=p.locator('footer');
    assert.equal(await footer.locator('a[href="https://t.me/EmplivoGroupExample"]').count(),valid?1:0);
    assert.equal(await footer.locator('a[href="https://t.me/EmplivoApplyExampleBot?start=apply"]').count(),valid?1:0);
    if(valid){
     const link=footer.locator('a[href*="?start=apply"]');
     assert.match(await link.textContent(),route.startsWith('en/')?/Apply/:/Анкета/);
     assert.equal(await link.getAttribute('rel'),'noopener noreferrer');
     if(route==='')assert.equal(await p.locator('.cta-panel a[data-telegram=bot]').count(),1);
    }
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No mobile overflow');
   }
   assert.deepEqual(errors,[]);assert.deepEqual(missing,[]);
   await context.close();
  }
  console.log('PASS: empty/valid/malicious public config, UK/EN core and editorial links, mobile layout, project paths; no external requests.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
