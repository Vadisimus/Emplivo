const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const origin='https://vadisimus.github.io';
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
  const sandbox={window:{}};
  vm.runInNewContext(fs.readFileSync(path.join(root,'telegram-config.js'),'utf8'),sandbox);
  const saved=sandbox.window.EMPLIVO_TELEGRAM;
  const fixtures=[
   {config:null,group:saved.groupUrl,bot:saved.botEnabled?saved.botUsername:''},
   {config:{groupUrl:'',botUsername:'',botEnabled:false},group:'',bot:''},
   {config:{groupUrl:'https://t.me/EmplivoGroupExample',botUsername:'EmplivoApplyExampleBot',botEnabled:true},group:'https://t.me/EmplivoGroupExample',bot:'EmplivoApplyExampleBot'},
   {config:{groupUrl:'https://t.me/+AbCdeFGhIjKlmN01',botUsername:'EmplivoApplyExampleBot',botEnabled:true},group:'https://t.me/+AbCdeFGhIjKlmN01',bot:'EmplivoApplyExampleBot'},
   {config:{groupUrl:'https://t.me/+AbCdeFGhIjKlmN01',botUsername:'EmplivoApplyExampleBot',botEnabled:false},group:'https://t.me/+AbCdeFGhIjKlmN01',bot:''},
   {config:{groupUrl:'https://t.me/EmplivoGroupExample',botUsername:'EmplivoApplyExampleBot'},group:'https://t.me/EmplivoGroupExample',bot:''},
   {config:{groupUrl:'https://evil.example/t.me/group',botUsername:'badbot?token=secret',botEnabled:true},group:'',bot:''},
  ];
  for(const fixture of fixtures){
   const context=await browser.newContext({viewport:{width:390,height:844}});
   const errors=[],missing=[];
   await context.route('**/*',async route=>{
    const u=new URL(route.request().url());
    assert.equal(route.request().method(),'GET');
    assert.equal(u.origin,origin,'No external requests or Telegram messages during tests');
    assert(u.pathname.startsWith('/Emplivo/'));
    if(fixture.config&&u.pathname.endsWith('/telegram-config.js')){
     await route.fulfill({contentType:'application/javascript',body:'window.EMPLIVO_TELEGRAM='+JSON.stringify(fixture.config)});return;
    }
    let file=path.resolve(root,decodeURIComponent(u.pathname.slice('/Emplivo/'.length)));
    assert(file===root||file.startsWith(root+path.sep));
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file)){missing.push(u.pathname);await route.fulfill({status:404,body:'Missing'});return;}
    let body=fs.readFileSync(file);
    if(fixture.config&&path.extname(file)==='.html')body=body.toString().replace(/<nav class="telegram-static-links"[^>]*>[\s\S]*?<\/nav>/g,'');
    await route.fulfill({contentType:types[path.extname(file)]||'application/octet-stream',body});
   });
   const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
   for(const route of ['', 'en/', 'jobs/spa-therapist/', 'en/jobs/spa-therapist/']){
    await p.goto(origin+'/Emplivo/'+route);
    const footer=p.locator('footer');
    const groupLinks=footer.locator('a[href^="https://t.me/"]:not([href*="?start="])');
    assert.equal(await groupLinks.count(),fixture.group?1:0);
    if(fixture.group)assert.equal(await groupLinks.getAttribute('href'),fixture.group);
    assert.equal(await footer.locator('a[href*="?start=apply"]').count(),fixture.bot?1:0);
    assert.equal(await p.locator('.cta-panel a[data-telegram=bot]').count(),fixture.bot&&!route.includes('jobs/')?1:0);
    if(fixture.bot){
     const link=footer.locator('a[href*="?start=apply"]');
     assert.match(await link.textContent(),route.startsWith('en/')?/Apply/:/Анкета/);
     assert.equal(await link.getAttribute('rel'),'noopener noreferrer');
     assert.equal(await link.getAttribute('href'),'https://t.me/'+fixture.bot+'?start=apply');
    }
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No mobile overflow');
   }
   assert.deepEqual(errors,[]);assert.deepEqual(missing,[]);
   await context.close();
  }
  console.log('PASS: configured group, invite/public addresses, inactive/active bot, malicious config, UK/EN core and editorial links, mobile layout and project paths; no external requests.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
